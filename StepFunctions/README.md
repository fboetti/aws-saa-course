# AWS Step Functions

**AWS Step Functions** is a **serverless orchestration service** that lets you build **workflows** (state machines) coordinating multiple AWS services (Lambda, ECS, Batch, SNS, SQS, DynamoDB, Glue...) with **visual design**, **built-in error handling, retries and state tracking**. You define *what happens, in which order, and what to do on failure*; Step Functions runs it.

```
Start ─► [ Task: Validate (Lambda) ] ─► < Choice: valid? >
                                           │ yes                 │ no
                                           ▼                     ▼
                              [ Task: Charge (Lambda) ]     [ Fail ]
                                           │  (Retry / Catch)
                                           ▼
                              [ Parallel: Ship + Email ] ─► End
```

- Workflows are written in **Amazon States Language (ASL)**, a **JSON** definition, usually designed in **Workflow Studio** (drag and drop).
- **Serverless**: no servers to manage, scales automatically, pay per use.
- The exam keyword is "**orchestrate** multiple services/Lambdas **with retries, branching, parallelism, human approval**" (avoid chaining Lambdas by hand).

## Core Concepts

| Concept | What it is |
|---|---|
| **State machine** | The **workflow definition** (ASL JSON). |
| **Execution** | One **run** of a state machine, with its own input, output and history. |
| **State** | A **step** in the workflow. |
| **Transition** | The move from one state to the next. |
| **Task** | A state that **does work** (calls a service or an activity). |
| **Activity** | Work done by a **worker outside AWS Step Functions** (any server) that **polls** for tasks. |
| **Input / Output** | JSON passed between states, filtered with `InputPath`, `Parameters`, `ResultSelector`, `ResultPath`, `OutputPath`. |

## State Types

| State | Purpose |
|---|---|
| **Task** | Do work: invoke a **Lambda**, start an **ECS/Fargate** task, run a **Glue** job, call **SNS/SQS/DynamoDB**, and so on. |
| **Choice** | **Branching** (if / else) based on input values. |
| **Parallel** | Run **branches at the same time**, then wait for all. |
| **Map** | **Iterate** over an array and run the same steps on each item. **Distributed Map** handles **massive scale** (up to 10,000 parallel child executions, items from **S3**). |
| **Wait** | **Delay** for a time or until a timestamp. |
| **Pass** | Pass input to output, optionally **transform/inject data**. |
| **Succeed / Fail** | **Stop** the execution successfully or with an error. |

### Task State

A **Task** state is the one that **does the actual work**: it calls a **Lambda function**, another **AWS service** (ECS, Batch, Glue, SNS, SQS, DynamoDB...) through an **integration**, an **HTTP endpoint**, or an **Activity** worker.

- The target is set in `Resource` (e.g. `arn:aws:states:::lambda:invoke`, `arn:aws:states:::sns:publish`, or `arn:aws:states:::aws-sdk:...` for any SDK call).
- The **integration pattern** is chosen by the ARN suffix: none (**Request Response**), `.sync` (**wait for the job**), `.waitForTaskToken` (**wait for callback**).
- Supports **`Retry`**, **`Catch`**, **`TimeoutSeconds`** and **`HeartbeatSeconds`**.
- Needs **IAM permissions** on the state machine's **execution role** for the service it calls.

```json
"SendAlert": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Parameters": { "TopicArn": "arn:aws:sns:eu-north-1:123456789012:alerts", "Message": "Done" },
  "TimeoutSeconds": 30,
  "End": true
}
```

### Pass State

A **Pass** state **does no work and calls no service**. It simply takes its input and **passes it to the output**, optionally **modifying it** on the way.

- **Inject fixed data** with `Result` (placed where `ResultPath` says), or **reshape** the JSON with `Parameters`.
- Useful to **build/test a workflow** before the real tasks exist (a **placeholder / mock**), to **debug** the data flow, or to **add or rename fields** between two states.
- **No cost beyond the transition** (no Lambda needed for simple JSON manipulation).
- Can be the last state of a branch with `"End": true`.

```json
"AddDefaults": {
  "Type": "Pass",
  "Result": { "currency": "EUR", "retries": 0 },
  "ResultPath": "$.defaults",
  "Next": "Charge"
}
```

## Input and Output Processing

Every state receives **JSON input** and produces **JSON output**. The output of one state becomes the **input of the next**. The first state gets the **execution input** (from `StartExecution`).

```
Input ─► InputPath ─► Parameters ─► [ state work ] ─► ResultSelector ─► ResultPath ─► OutputPath ─► Output
```

| Field | What it does |
|---|---|
| **`InputPath`** | **Filters** the raw input, keeping only the part the state needs (default `$`, everything). |
| **`Parameters`** | **Builds** the payload sent to the task. Keys ending in `.$` take values from the input via **JSONPath** (e.g. `"id.$": "$.orderId"`). |
| **`ResultSelector`** | **Reshapes** the task result before it is used (pick only some fields). |
| **`ResultPath`** | **Where to put the result** inside the original input (e.g. `$.charge`). `null` **discards** the result and keeps the input. Default `$` **replaces** the input. |
| **`OutputPath`** | **Filters** what is passed to the next state. |

- **Context object** (`$$`) gives metadata about the execution (e.g. `$$.Execution.Id`, `$$.State.Name`).
- **Intrinsic functions** (`States.Format`, `States.JsonToString`, `States.Array`, `States.MathAdd`...) manipulate data **without a Lambda**.
- Newer **JSONata** query language (`Arguments`, `Output`, `Assign`) and **variables** (`Assign`) can replace the path fields above and **store values** for later states.
- **Size limit**: **256 KB** per state input/output. For larger data, store it in **S3** and pass the **reference** (key/ARN).

## Workflow Types: Standard vs Express

| | **Standard** | **Express** |
|---|---|---|
| Max duration | **Up to 1 year** | **5 minutes** |
| Execution semantics | **Exactly-once** | **At-least-once** (async) / at-most-once (sync) |
| Start rate | ~2,000/s | **100,000+/s** |
| History | Kept in service (visible in console / API, 90 days) | Only in **CloudWatch Logs** |
| Pricing | Per **state transition** | Per **number of executions + duration + memory** |
| Best for | **Long-running, auditable, non-idempotent** workflows (order processing, ML pipelines, human approval) | **High-volume, short** event processing (IoT ingestion, streaming data, mobile backends) |

- **Standard** supports the **`.waitForTaskToken`** pattern and **Activities**. Express does **not**.
- Express can run **synchronously** (caller waits, e.g. from API Gateway) or **asynchronously**.

## Service Integration Patterns

| Pattern | Behavior |
|---|---|
| **Request Response** (default) | Call the service and **move on** as soon as the HTTP response arrives. |
| **Run a Job (`.sync`)** | **Wait until the job completes** (ECS, Batch, Glue, EMR, CodeBuild...). |
| **Wait for Callback (`.waitForTaskToken`)** | Pause until an external system returns a **task token** (`SendTaskSuccess` / `SendTaskFailure`). Used for **human approval** and **long external processes**. |

- **Optimized integrations** (~220 services via **AWS SDK integrations**, over **10,000 API actions**): call almost any AWS API **without a Lambda glue function**.
- Can also call **HTTP endpoints** (third-party APIs) through **HTTP Task**.

## Error Handling

- **Retry**: retry a failed state with `ErrorEquals`, `IntervalSeconds`, `MaxAttempts`, `BackoffRate` (**exponential backoff**).
- **Catch**: on error, **route to a fallback state** (cleanup, notify, compensate).
- Predefined errors: `States.ALL`, `States.Timeout`, `States.TaskFailed`, `States.Permissions`...
- **`TimeoutSeconds`** and **`HeartbeatSeconds`** detect stuck tasks.
- Implements the **Saga pattern** (compensating transactions) for distributed workflows.

## Triggers and Integrations

- **Start an execution** from: **API Gateway**, **EventBridge** (rules and Scheduler), **Lambda / SDK** (`StartExecution`), **CLI**, console, or **another state machine**.
- **Targets** from the workflow: Lambda, ECS/Fargate, Batch, Glue, EMR, SageMaker, SNS, SQS, DynamoDB, EventBridge, CodeBuild, Athena, Bedrock and more.
- **Nested workflows**: a state machine can **start another** (sync or async).

## Security and Monitoring

- **IAM execution role**: Step Functions assumes it to call the integrated services (**least privilege** per service used).
- **Resource policies / IAM** control who can start executions.
- **CloudWatch** metrics and logs, **X-Ray** tracing, **CloudTrail** for API calls, **EventBridge** events on execution status change.
- Encryption at rest with AWS-owned or **customer managed KMS key**. Supports **VPC interface endpoints** (PrivateLink).

## Pricing

- **Standard**: per **state transition** (first **4,000 free/month**).
- **Express**: per **request count** and **duration x memory**.
- Plus the cost of the services the workflow calls.

## CLI Example

```bash
# Create a state machine from an ASL definition
aws stepfunctions create-state-machine --name OrderFlow \
  --definition file://order.asl.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsRole \
  --type STANDARD

# Start an execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:eu-north-1:123456789012:stateMachine:OrderFlow \
  --input '{"orderId":"42"}'
```

Minimal ASL with retry and catch:

```json
{
  "StartAt": "Charge",
  "States": {
    "Charge": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": { "FunctionName": "ChargeFn", "Payload.$": "$" },
      "Retry": [{ "ErrorEquals": ["States.TaskFailed"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2 }],
      "Catch": [{ "ErrorEquals": ["States.ALL"], "Next": "NotifyFailure" }],
      "Next": "Done"
    },
    "NotifyFailure": { "Type": "Task", "Resource": "arn:aws:states:::sns:publish",
      "Parameters": { "TopicArn": "arn:aws:sns:eu-north-1:123456789012:alerts", "Message": "Charge failed" },
      "End": true },
    "Done": { "Type": "Succeed" }
  }
}
```

## Step Functions vs Similar Services

| | **Step Functions** | **SQS** | **SNS** | **EventBridge** | **Amazon MWAA (Airflow)** | **SWF** |
|---|---|---|---|---|---|---|
| Purpose | **Orchestrate** steps with state | **Queue** / decouple | **Pub/sub** fan-out | **Event bus**, routing | Data pipeline **scheduling** (Python DAGs) | Legacy orchestration |
| Coordination | **Central** (state machine) | None | None | **Choreography** | DAG | Decider code |
| Visual / managed | Yes | No | No | No | Partial | No |

- **Orchestration** (Step Functions, one brain controls the flow) vs **choreography** (EventBridge/SNS, services react to events).
- **SWF** is **legacy**: new workloads should use **Step Functions**.

## Exam Tips

- "**Coordinate multiple Lambdas/services** with **retries, branching, parallel steps**, serverless" → **Step Functions**.
- "**Human approval** / wait for an external process" → **`.waitForTaskToken`** (Standard).
- "Workflow runs **up to a year**, **exactly-once**" → **Standard**. "**High volume, under 5 min**" → **Express**.
- "**Process millions of S3 objects** in parallel" → **Distributed Map**.
- "Replace a **legacy SWF** or hand-coded Lambda chain" → Step Functions.
- Lambda max is **15 minutes**, so **longer or multi-step** flows need Step Functions.
- Decouple producer/consumer with buffering → **SQS**. Fan-out notifications → **SNS**. Ordered, stateful, error-handled flow → **Step Functions**.
