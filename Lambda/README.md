# AWS Lambda

**AWS Lambda** is a **serverless, event-driven compute** service. You upload **code** (a *function*), Lambda runs it **in response to events**, and you pay only for the **compute time used** (billed per **millisecond**). There are no servers to provision, patch or scale. Lambda handles the OS, runtime, scaling and high availability across multiple AZs.

```
Event source ──► [ Lambda function ] ──► Result / downstream service
(S3, SQS, API Gateway,   (runs in an execution
 EventBridge, ...)        environment, then freezes)
```

- **Event-driven**: a function runs when something **invokes** it (an API call, a queue message, a file upload, a schedule).
- **Stateless**: don't keep state in the function. Use S3, DynamoDB, EFS or ElastiCache.
- **Short-lived**: maximum run time is **15 minutes**.
- **Automatic scaling**: each concurrent request gets its own execution environment, from zero up to thousands.

## Core Concepts

| Concept | What it is |
|---|---|
| **Function** | Your code plus its configuration (runtime, memory, timeout, role, env vars). |
| **Runtime** | The language environment: Node.js, Python, Java, .NET, Ruby, **Go / Rust / C++ via `provided.al2023` (custom runtime)**. |
| **Handler** | The entry point Lambda calls with the **event** and a **context** object. |
| **Event** | A JSON document describing what triggered the function. |
| **Execution role** | The **IAM role** the function **assumes** to call other AWS services (and write logs). |
| **Resource-based policy** | Controls **who can invoke** the function (e.g. S3, API Gateway, another account). |
| **Execution environment** | The sandbox (a Firecracker micro-VM) that runs your code. It is **reused** for later invocations. |
| **Version / Alias** | An **immutable snapshot** of the function (`$LATEST` is mutable). An **alias** is a pointer to a version (`prod`) that can **split traffic** between two versions (canary). |
| **Layer** | A zip of **libraries or dependencies** shared across functions (up to **5 layers** per function). |
| **Architecture** | **x86_64** or **arm64 (Graviton)**. arm64 is cheaper and usually faster per dollar. |

## Limits to Remember

| Setting | Value |
|---|---|
| **Timeout** | Default **3 s**, max **15 min (900 s)** |
| **Memory** | **128 MB to 10,240 MB (10 GB)**, in 1 MB steps |
| **CPU** | **Not set directly.** It scales **with memory** (about **1 vCPU at 1,769 MB**, up to **6 vCPUs**) |
| **Ephemeral storage `/tmp`** | **512 MB** default, up to **10,240 MB** |
| **Deployment package (zip)** | **50 MB** zipped (direct upload), **250 MB** unzipped (including layers) |
| **Container image** | Up to **10 GB** (from **ECR**) |
| **Environment variables** | **4 KB** total |
| **Payload (synchronous)** | **6 MB** request and response |
| **Payload (asynchronous)** | **1 MB** (it was 256 KB before late 2025, so older material says 256 KB) |
| **Concurrency** | **1,000** concurrent executions per **Region** by default (**soft limit**, can be raised) |
| **Scaling rate** | Each function adds up to **1,000 new execution environments every 10 seconds** |

> Exam tip: **more than 15 minutes** → don't use Lambda. Use **ECS / Fargate**, **Batch** or **Step Functions**. Need **more CPU** → **raise memory**.

## Invocation Types

| Type | How it works | Examples | Errors |
|---|---|---|---|
| **Synchronous** | The caller **waits** for the response. | API Gateway, ALB, Function URL, CloudFront (Lambda@Edge), Cognito, SDK `RequestResponse` | **The caller** handles errors and retries. |
| **Asynchronous** | Lambda **queues** the event and returns `202` right away. | **S3**, **SNS**, **EventBridge**, CodeCommit, SDK `Event` | Lambda **retries twice** (3 attempts in total). Then the event goes to a **DLQ** or **destination**. |
| **Poll-based (event source mapping)** | Lambda **polls** the source and invokes your function with **batches**. | **SQS**, **Kinesis**, **DynamoDB Streams**, **MSK / Kafka**, Amazon MQ | Depends on the source (see below). |

- **Async** events can wait in Lambda's internal queue up to **6 hours** (max event age). Both the retry count (0 to 2) and the max age are configurable.
- Because of retries, functions must be **idempotent**.

### Event Source Mapping (poll-based)

An **event source mapping** is a Lambda resource that **reads** from a queue or stream and invokes your function. Lambda does the polling, **not** the source.

| Source | Behavior |
|---|---|
| **SQS (standard)** | Batches of up to **10,000** messages. On error the **whole batch** returns to the queue. Use **partial batch response** (`batchItemFailures`) to retry only failed messages. Unprocessed messages go to the queue's **DLQ** (set on the **queue**, not on the function). |
| **SQS (FIFO)** | One batch in flight **per message group**, so order is kept. |
| **Kinesis / DynamoDB Streams** | **One batch per shard** at a time (or more with *parallelization factor*, up to 10). On error Lambda **retries the batch until it succeeds or the data expires**, which **blocks the shard**. Limit this with max retries, max record age, **bisect batch on error** and an **on-failure destination**. |

> A DLQ on the **function** only covers **asynchronous** invocations. For SQS, configure the DLQ **on the queue**.

## Error Handling for Async Invocations

| Option | Purpose |
|---|---|
| **Dead-letter queue (DLQ)** | Failed events go to **SQS** or **SNS**. Older feature. |
| **Destinations** | Route the **result** of an async invocation: **on success** or **on failure** to **SQS, SNS, Lambda or EventBridge**. Newer, richer (includes the response and error details). **Preferred** over a DLQ. |

## Cold Starts and Execution Environment

Lifecycle: **Init** (download code, start runtime, run code **outside** the handler) → **Invoke** (run the handler) → **Shutdown**.

- A **cold start** is the **Init** of a **new** environment. A **warm start** reuses an existing one and skips Init.
- After an invocation, the environment is **frozen** and may be **reused**. Put **SDK clients and DB connections outside the handler** so warm calls reuse them. Anything in `/tmp` can survive between warm calls, but **never rely on it**.
- Cold starts are longer for **Java / .NET**, **large packages**, **VPC (much reduced today)** and **low memory** settings.
- Ways to cut them:
  - **Provisioned Concurrency**: keeps a set number of environments **pre-initialized**. Costs money even when idle. Can be scheduled with **Application Auto Scaling**.
  - **SnapStart**: caches a **snapshot** of the initialized environment. Available for **Java**, **Python** and **.NET**. Free for Java, with a cost for the others.
  - Smaller packages, lazy loading, **arm64**, more memory.

## Concurrency

**Concurrency** = number of requests being handled **at the same time**. Roughly `invocations per second × average duration (s)`.

| Setting | What it does |
|---|---|
| **Unreserved concurrency** | The shared pool of the account (min **100** is always left unreserved). |
| **Reserved concurrency** | **Guarantees** a function a share of the pool **and caps it** at that value. Free. Setting it to **0** **throttles everything** (a handy "off switch"). Also protects downstream resources such as an RDS database. |
| **Provisioned concurrency** | **Pre-warmed** environments to remove cold starts. **Paid**. |

- When the limit is reached, Lambda **throttles** (`429 TooManyRequestsException`). Sync callers get the error, async events are **retried**, and poll-based sources retry.

## Networking (VPC)

- By default a function runs in an **AWS-managed VPC** with **internet access** but **no access to your private resources**.
- To reach an **RDS** instance or other **private resources**, attach the function to **your VPC** (choose **subnets** and **security groups**). Lambda creates **Hyperplane ENIs** in them.
- A function **in a VPC** has **no internet access**, even in a public subnet (it never gets a public IP). It needs a **NAT Gateway** in a public subnet (private subnets with a route to it) to reach the internet, or **VPC endpoints** to reach AWS services privately.
- **RDS Proxy** is recommended for Lambda → RDS: many short-lived functions can **exhaust database connections**, and the proxy **pools** them.

## Function URL

- A built-in **HTTPS endpoint** for a function (`https://<id>.lambda-url.<region>.on.aws`), with no API Gateway needed.
- Auth: **`AWS_IAM`** (SigV4) or **`NONE`** (public). Supports **CORS** and **response streaming**.
- Choose **API Gateway** instead when you need **throttling, API keys, usage plans, request validation, caching, WAF, custom authorizers**.

## Security

- **Execution role** (what the function **can do**) vs **resource-based policy** (who **can invoke** it). Both matter for cross-service calls.
- Never hardcode secrets. Use **Secrets Manager** or **SSM Parameter Store**. Environment variables are **encrypted at rest** by default with a KMS key, and you can use a **customer managed key** and **encryption helpers** (encrypt in transit).
- **Code signing** (with AWS Signer) makes sure only trusted code is deployed.
- Logs go to **CloudWatch Logs** automatically (the role needs `AWSLambdaBasicExecutionRole`). Metrics: `Invocations`, `Errors`, `Throttles`, `Duration`, `ConcurrentExecutions`, `IteratorAge` (streams). **X-Ray** gives tracing.

## Pricing

You pay for:

1. **Requests**: per million invocations.
2. **Duration**: **GB-seconds** = memory allocated × run time (billed per **1 ms**). It now also includes the **Init** phase for most runtimes.
3. Extras: **Provisioned Concurrency**, **ephemeral storage** above 512 MB, **SnapStart**, data transfer.

- **Free tier (always free)**: **1 million requests** and **400,000 GB-seconds** per month.
- **Memory = cost and speed**. More memory means more CPU, so a function can finish **faster** and sometimes **cost less**. Use **AWS Lambda Power Tuning** to find the sweet spot.
- **arm64** costs about **20% less per GB-second** than x86.
- **Compute Savings Plans** can cover Lambda.

## Common Integrations and Use Cases

| Use case | Architecture |
|---|---|
| **Serverless REST API** | **API Gateway** (or Function URL / ALB) → Lambda → **DynamoDB** |
| **File processing** | **S3** `ObjectCreated` event → Lambda (thumbnails, ETL, virus scan) |
| **Queue worker** | **SQS** → Lambda (event source mapping) |
| **Stream processing** | **Kinesis / DynamoDB Streams** → Lambda |
| **Fan-out** | **SNS** → many Lambdas (and SQS queues) |
| **Scheduled jobs (cron)** | **EventBridge Scheduler / rule** → Lambda |
| **Reacting to AWS events** | **EventBridge** (e.g. EC2 state change, CloudTrail API call) → Lambda |
| **Orchestration** | **Step Functions** coordinating many Lambdas (retries, branching, waits up to a year) |
| **Edge logic** | **Lambda@Edge** / **CloudFront Functions** |

### Lambda@Edge vs CloudFront Functions

| | **CloudFront Functions** | **Lambda@Edge** |
|---|---|---|
| Runs at | **Edge locations** | **Regional edge caches** |
| Languages | **JavaScript** only | **Node.js** and **Python** |
| Max duration | **< 1 ms** | **5 s** (viewer events), **30 s** (origin events) |
| Triggers | Viewer request / response | Viewer **and** origin request / response |
| Network / file access | **No** | **Yes** |
| Use for | Header edits, URL rewrites, simple auth tokens | Heavy logic, calling other AWS services, body access |

## Instruction Set Architecture

Each function runs on one **instruction set architecture**, chosen in its configuration:

| | **x86_64** | **arm64** |
|---|---|---|
| Processor | Intel / AMD | **AWS Graviton2** |
| Default | **Yes** | No (opt in) |
| Price | Baseline | About **20% cheaper** per GB-second |
| Performance | Baseline | Often **better price-performance** (AWS cites up to ~19% better performance) |

- Set it **per function** (CLI/API: `--architectures arm64`). The default is **x86_64**.
- **Compiled code and native dependencies must match** the architecture: native libraries, **layers** and **container images** must be built for **arm64** or **x86_64** accordingly. Pure interpreted code (plain Python, Node.js, Java bytecode) usually runs on both **without changes**.
- A **layer** lists its **compatible architectures**. Use a layer built for the function's architecture.
- To migrate: rebuild dependencies for arm64, **test** (a canary alias helps), then switch. Note that **Lambda@Edge** supports **x86_64 only**.

> Exam tip: "Reduce Lambda cost with minimal effort" → switch to **arm64 (Graviton2)**, after checking dependencies are compatible.

## Versions, Aliases and ARNs

### Versions

- **`$LATEST`** is the **mutable** working copy. Every code or config change edits it.
- **Publishing** a version takes an **immutable snapshot** of the code **and** configuration (env vars, memory, timeout, layers). Versions are numbered **1, 2, 3...** and the numbers are **never reused**, even after deletion.
- A published version **cannot be changed**. To change it, edit `$LATEST` and publish a new one.
- Each version has its **own ARN**. Keep in mind that **resource-based policies, concurrency settings and triggers** are not all shared between versions, so check them per version or alias.

### Aliases

- An **alias** is a **named pointer** to a version (e.g. `prod`, `dev`, `beta`), with its **own ARN**.
- You can **repoint** an alias to a different version without changing the callers. This is how you **deploy and roll back**.
- An alias can **split traffic between two versions** (weighted, e.g. 90% v1 / 10% v2) for **canary** releases. It can only point to **published versions**, **not** `$LATEST`. A weighted alias works only if both versions use the same **execution role**, the same **DLQ** setting and are **not** `$LATEST`.
- Event sources (S3, API Gateway, SNS...) can target the **alias ARN**, so promoting a new version needs **no change to the trigger**.
- Works with **CodeDeploy** for **canary / linear** shifting, with automatic rollback on CloudWatch alarms.
- **Provisioned Concurrency** is configured on a **version or alias**, **not** on `$LATEST`.

### Qualified vs Unqualified ARN

| | ARN | Resolves to |
|---|---|---|
| **Unqualified** | `arn:aws:lambda:eu-north-1:123456789012:function:my-func` | **`$LATEST`** |
| **Qualified (version)** | `...:function:my-func:3` | That **exact version** |
| **Qualified (alias)** | `...:function:my-func:prod` | Whatever version the alias **currently points to** |
| **Qualified (`$LATEST`)** | `...:function:my-func:$LATEST` | `$LATEST` (same as unqualified) |

- A **qualified ARN** ends with a **version number or alias name** (the **qualifier**). An **unqualified ARN** has **none**.
- Invoking the unqualified ARN always runs **`$LATEST`**, which can **change under you** at any time.
- **Provisioned Concurrency** can't be set on an unqualified ARN (or `$LATEST`). Use a **version or alias**.
- A version number and an alias name can't be confused: alias names **cannot be purely numeric**.

> Exam tip: "Deploy a new version with **gradual traffic shifting** and **no change to callers**" → **alias with weights** (+ **CodeDeploy**). "Pin a trigger to stable code" → **qualified ARN** (alias, not `$LATEST`).

## Deployment

- **Zip** (code up to the limits above, with dependencies via **layers**) or **container image** (up to **10 GB**, pulled from **ECR**, must implement the Lambda runtime API).
- Tooling: **AWS SAM**, **CDK**, **CloudFormation**, **Terraform**, Serverless Framework.
- Use **versions + aliases** with **CodeDeploy** for **canary / linear** rollouts and automatic rollback.

## When NOT to Use Lambda

- Runs **longer than 15 minutes** (use **ECS/Fargate**, **Batch**, **EC2**).
- Needs **persistent connections, local state**, or very **steady high load** (a container or EC2 can be cheaper).
- Needs specialized hardware (e.g. **GPUs**) or full OS control.
- Needs **consistent ultra-low latency** with no tolerance for cold starts (unless using Provisioned Concurrency / SnapStart).

## Exam Cheat Sheet

| If the question says... | Think... |
|---|---|
| "Serverless", "run code without managing servers" | **Lambda** |
| "Run longer than 15 minutes" | **Fargate / Batch / Step Functions** |
| "Cold starts hurting latency" | **Provisioned Concurrency** or **SnapStart** |
| "Limit a function so it doesn't overwhelm the database" | **Reserved concurrency** (and **RDS Proxy**) |
| "Lambda can't reach the internet from a VPC" | **NAT Gateway** (or VPC endpoint) |
| "Lambda needs to access RDS" | Put it **in the VPC** + **RDS Proxy** |
| "Failed async events must not be lost" | **DLQ** or **on-failure destination** |
| "SQS failures should go to a DLQ" | DLQ on the **queue**, not on the function |
| "Share libraries across functions" | **Layers** |
| "Gradual deployment / traffic shifting" | **Alias** weights + **CodeDeploy** |
| "Run code at CloudFront edge, tiny and fast" | **CloudFront Functions** (**Lambda@Edge** for heavier logic) |
| "Need more CPU" | Increase **memory** |
| "Need more than 512 MB temp space" | Raise **ephemeral storage** (up to 10 GB) or use **EFS** |
| "Shared persistent file system" | Mount **EFS** (requires VPC) |
| "Quick HTTPS endpoint, no API Gateway" | **Function URL** |
