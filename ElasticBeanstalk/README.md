# AWS Elastic Beanstalk

**AWS Elastic Beanstalk** is a **PaaS** (Platform as a Service) that lets you **deploy and run web applications** without managing the infrastructure. You **upload your code** and Beanstalk automatically handles **provisioning, load balancing, auto scaling, health monitoring and deployment**.

It looks like a legacy service without too much maintenance and with a lot of legacy components. Seems not to be good to use it in production env.

```
Developer ──► code (zip / WAR / Docker) ──► Elastic Beanstalk
                                                │ creates and manages
                                                ▼
                         ┌─────────────── Environment ───────────────┐
   Users ──► ELB ──────► │  EC2 instances (Auto Scaling Group)       │ ──► RDS (optional)
                         │  + platform (Java, Python, Node, Docker…) │
                         └───────────────────────────────────────────┘
                              CloudWatch · S3 (code) · CloudFormation
```

- **Exam keyword**: "deploy a web app **quickly**, with **minimal infrastructure management**, but **keep control** of the underlying resources".
- **Developer-centric** view of the app. Under the hood it is **CloudFormation** creating **EC2, ASG, ELB, S3, CloudWatch**.
- The service itself is **free**. You pay only for the **underlying resources** (EC2, ELB, RDS, S3...).
- You keep **full control**: you can access the EC2 instances and tune the resources.

## Core Concepts

| Concept | What it is |
|---|---|
| **Application** | A **logical collection** of Beanstalk components (environments, versions, configurations). Like a folder. |
| **Application version** | A **specific, labeled iteration** of deployable code, stored in **S3**. |
| **Environment** | The **running infrastructure** where one application version is deployed. One version runs per environment. |
| **Environment tier** | **Web server** tier or **Worker** tier (see below). |
| **Platform** | OS + runtime + web server (Java, .NET, Node.js, PHP, Python, Ruby, Go, Docker...). |
| **Configuration** | Environment settings (instance type, scaling, env vars). Saved as **saved configurations**. |
| **`.ebextensions`** | Folder in the code with `.config` files (YAML/JSON) to **customize** resources and settings. |

## Environment Tiers

| | **Web server tier** | **Worker tier** |
|---|---|---|
| Purpose | Serves **HTTP requests** | Processes **background jobs** |
| Architecture | **ELB** + **Auto Scaling group** of EC2 | **SQS queue** + Auto Scaling group of EC2 |
| Trigger | Client requests | **Messages in SQS** (a **daemon** on each instance pulls and POSTs them to your app) |
| Scaling | Based on **CPU/network** etc. | Based on **queue length** |
| Use case | Websites, APIs | Video processing, report generation, **periodic tasks** (`cron.yaml`) |

- Typical decoupled pattern: **web tier** puts a message in **SQS**, **worker tier** processes it.

## Environment Types

These apply to the **web server tier**. The **environment type** is a **configuration choice**, not a different service.

```
Single instance                         Load balanced (HA)

 Users ──► Elastic IP                    Users ──► ELB
             │                                      │
        ┌────▼────┐                      ┌─────────┼─────────┐
        │  EC2    │                      ▼         ▼         ▼
        │ (1 AZ)  │                   EC2 (AZ-a) EC2 (AZ-b) EC2 (AZ-c)
        └─────────┘                      └── Auto Scaling group ──┘
```

| | **Single instance** | **Load balanced (HA)** |
|---|---|---|
| Architecture | **One EC2** + **Elastic IP** (an ASG of **min 1 / max 1** keeps it alive) | **ELB** + **Auto Scaling group** across **multiple AZs** |
| Load balancer | **None** | **ALB** (default), NLB or Classic |
| Scaling | **No** scale out (a single instance) | **Automatic** (min/max, scaling triggers) |
| Availability | **Low**: one AZ, a failure means downtime until it is replaced | **High**: survives instance or AZ failure |
| Cost | **Lowest** | Higher (ELB + several EC2) |
| Use case | **Dev / test**, low-traffic apps | **Production** |

- A **single instance** environment can be **upgraded** to **load balanced** (and back) by changing the environment configuration.
- **Single instance** does not support **rolling** deployments the same way (there is no spare capacity), so expect **brief downtime** on deploy.
- With **single instance**, the **public IP** is an **Elastic IP**. With **load balanced**, clients use the **ELB DNS name** (CNAME), so **Route 53 alias** is the recommended custom domain setup.

## Deployment Policies

| Policy | How it works | Downtime | Extra cost | Rollback |
|---|---|---|---|---|
| **All at once** | Deploys to **all instances** at the same time | **Yes** | None | Redeploy (slow) |
| **Rolling** | Deploys in **batches**. Capacity is **reduced** during deploy | No (reduced capacity) | None | Redeploy (slow) |
| **Rolling with additional batch** | Launches a **new batch first** to keep **full capacity** | No | **Small** | Redeploy (slow) |
| **Immutable** | Launches **new instances in a new temporary ASG**, then swaps | No | **High** (double capacity briefly) | **Fast** (terminate new ASG) |
| **Traffic splitting** | **Canary**: sends a **% of traffic** to the new version (immutable-style) | No | High | **Fast** |
| **Blue/Green** | Separate **new environment**, then **swap CNAMEs** | No | High (two environments) | **Fast** (swap back) |

- **Blue/Green is not built-in** as a deployment policy: you **clone the environment** and use **Swap Environment URLs** (manual, DNS-based, so not instant for clients with DNS caching).
- **Immutable** is the safest **in-place** option for production.
- **All at once** is the **fastest** and cheapest, but has **downtime**: good for dev.

## Supported Platforms

| Language / runtime | Platform details |
|---|---|
| **Java** | **Java SE** (JAR) and **Tomcat** (WAR) |
| **.NET** | **.NET on Windows Server** (IIS) and **.NET Core on Linux** |
| **Node.js** | Runs on **Amazon Linux**, with **nginx** as proxy |
| **PHP** | Apache + PHP |
| **Python** | **Gunicorn** / WSGI (Django, Flask) |
| **Ruby** | **Puma** / Passenger |
| **Go** | Compiled binary behind nginx |
| **Docker** | **Single container** or **multi-container** (the latter uses **ECS** under the hood) |
| **Custom platform** | Build your own AMI with **Packer** for anything not listed |

- Platforms run on **Amazon Linux** (or **Windows Server** for classic .NET). Beanstalk publishes **platform versions** and retires old ones, so use a **supported** version.
- Anything not natively supported can usually be run with the **Docker** platform or a **custom platform**.
- **Exam tip**: if the language isn't in the list (e.g. Rust, C++) → **Docker** (or a custom platform).

## Database Considerations

- You can create an **RDS** instance **inside** the Beanstalk environment, but then its **lifecycle is tied** to the environment: **deleting the environment deletes the database**.
- For **production**, create RDS **outside** Beanstalk and pass the **connection string** through **environment variables**.
- Decoupling the DB is also needed for **Blue/Green** deployments.

## Other Features

| Feature | Details |
|---|---|
| **Managed platform updates** | Automatic **minor/patch** updates in a **maintenance window** |
| **Health monitoring** | **Basic** and **Enhanced** health reporting (Green/Yellow/Red/Grey) |
| **Logs** | Request logs, **stream to CloudWatch Logs** or **S3** |
| **Environment variables** | Configure app settings without code changes |
| **Elastic Beanstalk CLI (`eb`)** | `eb init`, `eb create`, `eb deploy`, `eb status`, `eb terminate` |
| **Custom domain / HTTPS** | Via **Route 53** and **ACM** certificate on the **ELB** |
| **Lifecycle policy** | Limits the number of **old application versions** stored in S3 |

## CLI Example

```bash
# Initialize the app in the current folder
eb init my-app --platform python-3.11 --region eu-north-1

# Create a load balanced environment
eb create my-env --elb-type application

# Deploy a new version
eb deploy

# Check status and health
eb status
eb health

# Swap two environments (blue/green)
eb swap my-env-blue --destination_name my-env-green

# Delete the environment (and its resources)
eb terminate my-env
```

## Elastic Beanstalk vs Similar Services

| | **Elastic Beanstalk** | **CloudFormation** | **Lambda** | **ECS / EKS** | **OpsWorks** | **App Runner** |
|---|---|---|---|---|---|---|
| Model | **PaaS** for web apps | **IaC**, you define all resources | **Serverless** functions | **Container** orchestration | **Chef/Puppet** config management | Fully managed **containers/source** |
| Control | Medium (managed, but you can tune) | Full | Low (code only) | High | High | Low |
| Servers | **EC2 managed for you** | Whatever you define | **No servers** | Fargate or EC2 | EC2 | No servers visible |
| Best for | **Developers** who want a **quick deploy** | Repeatable infrastructure | Event-driven, short tasks | Microservices | Existing Chef/Puppet code | Simple web apps/APIs |

## Exam Tips

- "Deploy an app **without managing infrastructure**, but **keep control** of EC2" → **Elastic Beanstalk**.
- "**Developer** wants to upload code and let AWS handle **scaling, load balancing, health**" → **Elastic Beanstalk**.
- Beanstalk is **PaaS**. It is **not serverless**: it still uses **EC2** (you pay for them).
- "**Background processing** with a queue" → **Worker tier** (**SQS** based).
- "**Zero downtime** and **fast rollback**" → **Immutable**, **Traffic splitting** or **Blue/Green** (swap URLs).
- "**Lowest cost** and **fastest** deploy, downtime acceptable" → **All at once**.
- "Keep **full capacity** during deploy" → **Rolling with additional batch** (or Immutable).
- **Database in the environment** is **deleted with it**. For production, **decouple RDS** from Beanstalk.
- "**Customize** the environment (install packages, create resources)" → **`.ebextensions`**.
- Beanstalk uses **CloudFormation** under the hood, so resources are visible there.
- Beanstalk is **regional**, and the application code lives in an **S3** bucket.
- Need to run **Docker** with little effort → Beanstalk **Docker platform** (or **App Runner / ECS** for more container-focused setups).
