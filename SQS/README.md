# Amazon SQS (Simple Queue Service)

**Amazon SQS** is a fully managed **message queue** service. Producers **send** messages to a queue, the queue **stores them durably**, and consumers **poll (pull)** them and process them at their own pace. It is the classic way to **decouple** and **buffer** between application components. It was one of the first AWS services (2004). There are no servers to manage, it scales automatically, and you pay per request.

```
Producer(s) ──► [ SQS Queue ] ◄── poll ── Consumer(s)
                 (stores msgs)             (process, then DELETE)
```

- **Point-to-point**: each message is processed by **one consumer** (contrast with SNS pub/sub fan-out).
- **Pull-based**: consumers call `ReceiveMessage`. SQS does not push (except through integrations such as the Lambda event source mapping, which polls for you).
- **Persistent**: messages are stored (default **4 days**, up to **14 days**) until a consumer **deletes** them.

## Core Concepts

| Concept | What it is |
|---|---|
| **Queue** | The container for messages. Has a URL, an ARN and an access policy. |
| **Producer** | Calls `SendMessage` / `SendMessageBatch` (up to **10** messages per batch). |
| **Consumer** | Calls `ReceiveMessage` (up to **10** messages per call), processes, then `DeleteMessage`. |
| **Message** | Up to **1 MiB** (1 KiB minimum, up to 2GB with ad-hoc-libraries) of text (JSON, XML, plain text) plus up to **10 message attributes** (metadata). |
| **Message ID / Receipt handle** | The ID identifies the message. The **receipt handle** is returned on each receive and is required to **delete** it or change its visibility. |
| **Visibility timeout** | Time a message stays **hidden** from other consumers after being received. |

## Queue Types

| | **Standard** | **FIFO** |
|---|---|---|
| Throughput | Nearly **unlimited** | **300 msg/s** per API action (**3,000** with batching). **High throughput mode** goes higher. |
| Ordering | **Best-effort** | **Strict**, per **message group** |
| Delivery | **At-least-once** (duplicates possible) | **Exactly-once processing** (deduplication) |
| Naming | Any | Name must end in **`.fifo`** |
| `MessageGroupId` | **Not needed** | **Required** on every message (defines the ordering scope) |
| `MessageDeduplicationId` | **Not needed** (no deduplication, so consumers must be **idempotent**) | **Required** on every message, unless **content-based deduplication** is enabled on the queue. **5-minute** window |
| Parallelism | Unlimited consumers, any message to any consumer | Parallel **across** groups only. **One consumer at a time per group** |
| Per-message delay | Supported (`DelaySeconds`) | **Not** supported (queue-level delay only) |
| SNS fan-out | Can subscribe to **standard** and **FIFO** topics | Can subscribe **only** to a **FIFO** topic (SNS FIFO + SQS FIFO) |
| Lambda trigger | Batches, high concurrency | One concurrent batch **per message group** |
| Price | Lower | Higher per request |
| Use for | Most workloads, max scale | Order and no-duplicate guarantees (orders, financial transactions, commands) |

- **`MessageGroupId`** (FIFO only, **required** on every `SendMessage`; sending without it fails): messages with the same group ID are delivered **in order** and are processed by **one consumer at a time**. Different groups can be processed **in parallel**. Standard queues don't need it.
- **`MessageDeduplicationId`** (FIFO only, **required** unless content-based deduplication is on; standard queues don't need it): messages with the same ID within the **5-minute** deduplication interval are accepted but **not delivered again**. If you enable **content-based deduplication** on the queue (SHA-256 of the body), SQS generates the ID for you and you can omit it. An explicit ID overrides the generated one.
- You **cannot convert** a standard queue to FIFO (or the reverse). Create a new queue and migrate.
- **Choosing**: need **maximum throughput** and can tolerate **occasional duplicates / out-of-order** delivery → **Standard**. Need **strict order** and **no duplicates**, and throughput limits are acceptable → **FIFO**.
- A FIFO queue with a **single message group ID** is fully ordered but processed by **one consumer** at a time, so use **many group IDs** (e.g. per customer or order) to scale.

## Message Metadata

Besides the **body**, a message carries metadata at three levels.

**1. Identifiers** (returned by SQS)

| Field | Purpose |
|---|---|
| **`MessageId`** | Unique ID assigned by SQS on send. Stays the same on every receive. |
| **`ReceiptHandle`** | Returned **per receive** (changes each time). Needed for `DeleteMessage` and `ChangeMessageVisibility`. |
| **`MD5OfBody`** | Checksum to verify the body was not corrupted in transit. |

**2. Message attributes** (custom, set by the **producer**)

- Structured **name / type / value** metadata sent **next to** the body, so consumers can route or filter **without parsing the body**.
- Up to **10 attributes** per message. Types: **String**, **Number**, **Binary** (optionally with a custom label, e.g. `Number.int`).
- They **count toward the message size limit**. Names are case-sensitive and can't start with `AWS.` or `Amazon.`.
- Consumers must **ask for them**: `ReceiveMessage` returns attributes only if you pass `MessageAttributeNames` (a name, a prefix like `Order.*`, or `All`). SQS also returns an **MD5 of the attributes** for validation.
- **SNS to SQS**: SNS message attributes are mapped to SQS message attributes when **raw message delivery** is on. Otherwise they sit inside the SNS JSON wrapper.
- Attributes are **not** used by SQS for filtering. There is no server-side filter, unlike SNS filter policies.

**3. System attributes** (set by **SQS**, read-only)

Returned by `ReceiveMessage` when requested with `MessageSystemAttributeNames` (or `All`):

| Attribute | Meaning |
|---|---|
| **`SenderId`** | IAM user/role ID (or account) of the sender. |
| **`SentTimestamp`** | When the message was sent (epoch ms). |
| **`ApproximateReceiveCount`** | Times the message was received. Compare with `maxReceiveCount` to spot **retries** heading to the DLQ. |
| **`ApproximateFirstReceiveTimestamp`** | First time it was received. |
| **`MessageGroupId`**, **`MessageDeduplicationId`**, **`SequenceNumber`** | **FIFO** only. Sequence number is assigned by SQS and increases per group. |
| **`DeadLetterQueueSourceArn`** | On messages in a DLQ: the source queue they came from. |
| **`AWSTraceHeader`** | **X-Ray** trace context. The one system attribute a **producer can set**, for end-to-end tracing. |

- **Queue attributes** are a different thing: settings on the queue itself (`VisibilityTimeout`, `MessageRetentionPeriod`, `RedrivePolicy`, etc.), read with `GetQueueAttributes`.
- **Tags** are queue-level labels (cost allocation, ABAC), not message metadata.

## Visibility Timeout

When a consumer receives a message, SQS does **not** remove it. It hides it for the **visibility timeout**, and the consumer must **delete** it when done.

```
t=0   Consumer A receives msg ──► msg invisible to others (30 s default)
t<30  A finishes ──► DeleteMessage ──► gone
t>30  A is too slow/crashed ──► msg becomes visible again ──► Consumer B receives it (duplicate processing!)
```

- Default **30 seconds**, range **0 s to 12 hours**.
- Too **low**: messages are processed more than once. Too **high**: failed messages take a long time to be retried.
- This is why **standard queues need idempotent consumers**. Visibility timeout reduces duplicates but does **not** guarantee exactly-once on a standard queue.

### Where it can be set

| Level | How | Scope |
|---|---|---|
| **Queue** | `VisibilityTimeout` queue attribute | Default for all messages. Changing it does **not** affect messages already in flight. |
| **Receive call** | `VisibilityTimeout` parameter on `ReceiveMessage` | Overrides the queue value for the messages returned by that call. |
| **Single message** | `ChangeMessageVisibility` (or `...Batch`) with the **receipt handle** | Resets the timer for that message. |

- `ChangeMessageVisibility` sets the new timeout **counting from the moment of the call**, it does not add to the time left.
- The **total** time a message can stay invisible is capped at **12 hours** from its first receive. You can't extend beyond that.
- Setting it to **0** makes the message **visible immediately** (a way to give it back without waiting, e.g. when a consumer can't process it).

### Heartbeat pattern (long or unpredictable jobs)

Instead of one huge timeout, use a short timeout and **extend while working**:

```
receive msg (timeout 60 s)
  ├─ every ~30 s: ChangeMessageVisibility(+60 s)   ◄── "heartbeat"
  └─ done ──► DeleteMessage
worker crashes ──► heartbeats stop ──► msg reappears after <= 60 s (fast retry)
```

### Related behavior

- A message **received but not deleted** counts as **in flight** (`ApproximateNumberOfMessagesNotVisible`). Limits: **120,000** in flight for standard, **20,000** for FIFO.
- **FIFO**: while a message of a group is in flight, **later messages of the same group are not delivered**, so a slow or failing message **blocks its group**.
- Each receive increases `ApproximateReceiveCount`. After **`maxReceiveCount`** receives without a delete, the message goes to the **DLQ**. Visibility timeout expiry is what makes the retries happen.
- **Lambda** event source mapping: set the queue's visibility timeout to **at least 6x the function timeout** (plus any batching window), or messages reappear while the function is still running.
- Visibility timeout is **not** the same as a **delay queue** (hides a message **before** its first receive) or **retention** (how long it lives in the queue).

## Delay Queues

A **delay queue** hides each **new** message from consumers for a set time **after it is sent**.

- **`DelaySeconds`** queue attribute: **0 (default) to 15 minutes (900 s)**. Applies to every message sent to the queue.
- **Per-message delay**: see [Message Timers](#message-timers). **FIFO** supports only the **queue-level** delay.
- Changing the queue delay affects **new** messages only. Messages already in the queue keep their old delay (standard queues).
- Use for: giving a downstream system time to be ready, scheduling a follow-up shortly after an event, or a short retry back-off.
- **Not** a scheduler for hours or days. For that use **EventBridge Scheduler** or **Step Functions** (Wait state).

### Message Timers

A **message timer** is a **per-message delay**: the `DelaySeconds` parameter on `SendMessage` (or on each entry of `SendMessageBatch`).

- Range **0 to 900 s (15 min)**, same as the queue delay.
- **Overrides** the queue's `DelaySeconds` for that message (a timer of 0 means no delay even if the queue has one).
- **Standard queues only**. On a **FIFO** queue a per-message timer is **not supported** (the request fails). Use the queue-level delay instead.
- Different messages in the same queue can have **different** delays.

| | **Delay queue** | **Visibility timeout** |
|---|---|---|
| Hides the message | **Before** its first receive (after send) | **After** each receive (until deleted) |
| Max | **15 min** | **12 hours** |
| Purpose | Postpone processing | Give the consumer time to finish, then retry |

## Polling: Short vs Long

| | **Short polling** | **Long polling** |
|---|---|---|
| `WaitTimeSeconds` | **0** | **1 to 20** |
| Behavior | Returns **immediately**, even with an empty result (samples a subset of servers) | **Waits** until a message arrives or the timeout expires (queries all servers) |
| Cost / latency | More empty responses, more cost | **Fewer empty responses**, lower cost, lower latency |

- **Long polling is recommended**. Enable it per queue (`ReceiveMessageWaitTimeSeconds`) or per request.
- **Default is short polling** (queue wait time **0**). A `WaitTimeSeconds` on the `ReceiveMessage` call **overrides** the queue setting.
- **Short polling** can return an **empty response even when messages exist** (only a sample of servers is queried), so a tight loop wastes requests and money.
- **Long polling** returns **as soon as a message is available**, so it does not add latency. It returns empty only after the full wait (max **20 s**).
- Make sure the client's **HTTP timeout** is longer than the wait time (e.g. > 20 s).
- Long polling also reduces **false empty responses**, and fewer calls means a lower bill (SQS is billed **per request**).

## Key Settings

| Setting | Default | Range |
|---|---|---|
| **Message retention period** | **4 days** | 60 s to **14 days** |
| **Visibility timeout** | 30 s | 0 s to 12 h |
| **Delivery delay** (queue) | 0 | 0 to **15 min** |
| **Message size** | | up to **1 MiB** |
| **Receive wait time** (long polling) | 0 | 0 to 20 s |

- **Delay queue**: see [Delay Queues](#delay-queues).
- **Large payloads** (over 1 MiB): store the body in **S3** and send a **reference**. The **SQS Extended Client Library** (Java / Python) does this, for messages up to **2 GB**.
- **Purge queue** deletes all messages (takes up to 60 s). Deleting a queue is separate.

## Dead-Letter Queues (DLQ)

A **DLQ** is another SQS queue that receives messages that **could not be processed successfully**.

- Set a **redrive policy** on the source queue: the **DLQ ARN** and **`maxReceiveCount`**. When a message is received more than that many times without being deleted, SQS moves it to the DLQ.
- The DLQ must be the **same type** as the source (standard to standard, FIFO to FIFO), in the **same account and Region**.
- Set a **longer retention** on the DLQ than on the source queue. The retention clock keeps the **original enqueue time**.
- **DLQ redrive**: move messages **back** to the source queue (or another queue) after fixing the bug, from the console or with `StartMessageMoveTask`.
- Set CloudWatch alarms on the DLQ's `ApproximateNumberOfMessagesVisible`.

## Security

- **Encryption at rest**: **SSE-SQS** (SQS-owned keys, **on by default**) or **SSE-KMS** (your own KMS key, with audit via CloudTrail). Encryption in transit with **HTTPS**.
- **IAM policies** control who can send / receive / delete.
- **SQS access policy** (resource-based) allows **cross-account** access and lets **AWS services** (SNS, S3, EventBridge) send messages to the queue.
- **VPC endpoints** (PrivateLink, interface endpoint) to reach SQS without the internet.

## ABAC (Attribute-Based Access Control)

SQS supports **ABAC**: authorize access using **tags** on queues and on principals instead of listing queue ARNs in every policy. See [IAM ABAC](../IAM/abac.md) for the general model.

- **Tag the queue** (`TagQueue`, or `Tags` at `CreateQueue`), e.g. `Project=Blue`, and **tag the principal** (IAM user/role, or a session tag) with the same key.
- A single policy then grants access to **every queue whose tag matches** the caller's tag. New queues need only a tag, not a policy edit.

```json
{
  "Effect": "Allow",
  "Action": ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"],
  "Resource": "arn:aws:sqs:*:*:*",
  "Condition": {
    "StringEquals": { "aws:ResourceTag/Project": "${aws:PrincipalTag/Project}" }
  }
}
```

| Condition key | Use in SQS |
|---|---|
| `aws:ResourceTag/key` | Tag on the **queue** being accessed |
| `aws:PrincipalTag/key` | Tag on the **caller** (user, role or session tag) |
| `aws:RequestTag/key` | Tag passed in `CreateQueue` / `TagQueue` (force tags at creation) |
| `aws:TagKeys` | Which tag keys the request may set (restrict who can add or change tags) |

- **Govern the tags**: anyone allowed `sqs:TagQueue` / `sqs:UntagQueue` can change their own access, so restrict those actions (for example with `aws:TagKeys` or `aws:RequestTag`).
- Works **alongside** the queue's resource-based access policy and IAM policies (same evaluation logic: explicit deny wins).
- Tags are for **access control and cost allocation** only, not part of the message. `sqs:ListQueues` can't be filtered by resource tag (it has no specific queue resource).

## Temporary Queues

**Temporary queues** are lightweight **virtual queues** for short-lived messaging, mainly the **request / response** pattern, provided by the **Temporary Queue Client** (a client-side library for **Java**).

```
Requester ──► [ request queue ] ──► Responder
    ▲                                   │
    └──── [ temp reply queue ] ◄────────┘   (one per requester)
```

- Many **virtual queues** are multiplexed on **one real "host" queue**. The client tags each message with its target virtual queue and routes it to the right consumer.
- **No cost or latency of creating real queues**: creating or deleting a virtual queue makes **no SQS API call**, so thousands of short-lived reply queues are cheap.
- **Idle** virtual queues are cleaned up automatically (including when the app crashes).
- Use for: RPC-style calls over SQS where each requester needs its own reply queue.
- It is a **client library feature**, not a separate SQS queue type.

## Common Integrations

| Integration | How it works |
|---|---|
| **SNS to SQS (fan-out)** | One topic, many queues. Needs a queue policy that allows the topic to `SendMessage`. |
| **S3 event notifications** | S3 sends events (e.g. `ObjectCreated`) to a queue. Needs a queue policy for S3. |
| **EventBridge** | Queue as a rule target. |
| **Lambda** | **Event source mapping** polls the queue and invokes the function with **batches**. Failed batches return to the queue (use **partial batch response** to report only the failed messages) and end up in the DLQ. |
| **Auto Scaling group** | Scale consumers (EC2) on the **backlog per instance** (queue depth ÷ number of instances), published as a **CloudWatch custom metric**. |
| **EC2 / ECS / containers** | Workers poll the queue. |

## Common Patterns

- **Decoupling / buffering**: a web tier writes to SQS, a worker tier processes asynchronously. A traffic spike fills the queue instead of overloading the backend.
- **Work queue with auto scaling**: ASG scales the workers on `ApproximateNumberOfMessagesVisible` (backlog per instance).
- **Fan-out**: **SNS + SQS**, each queue processed independently and durably.
- **Request / response**: with the **Temporary Queue Client** (virtual queues) for lightweight reply queues.
- **Order processing**: **FIFO** queue with the order ID as the message group.

## Useful CloudWatch Metrics

- **`ApproximateNumberOfMessagesVisible`**: the backlog, used for scaling and alarms.
- **`ApproximateNumberOfMessagesNotVisible`**: in flight (received, not yet deleted).
- **`ApproximateAgeOfOldestMessage`**: detects stuck or slow consumers.
- **`NumberOfMessagesSent` / `Received` / `Deleted`**.

## SQS vs SNS vs Kinesis Data Streams

| | **SQS** | **SNS** | **Kinesis Data Streams** |
|---|---|---|---|
| Model | **Queue, pull** | **Pub/sub, push** | **Stream**, pull |
| Consumers | **One** consumer per message (competing consumers) | **Many** subscribers get every message | **Many**, each reads the full stream |
| Persistence | Until **deleted** (max 14 days) | **None** | 24 h to **365 days**, **replayable** |
| Ordering | FIFO queues (per message group) | FIFO topics | Per **shard / partition key** |
| Scaling | Automatic, no capacity to manage | Automatic | Shards (provisioned or on-demand) |

## Exam Tips

- "**Decouple** components", "**buffer** traffic spikes", "**asynchronous** processing" → **SQS**.
- "**Fan-out**" → **SNS + SQS** (SNS pushes to many queues).
- "Messages must be processed **in order**" or "**exactly once**" → **SQS FIFO** (message group ID / deduplication ID).
- "Messages are processed **twice**" → visibility timeout too short, or the consumer is not **idempotent** (standard queue = at-least-once).
- "Processing takes longer than the visibility timeout" → **`ChangeMessageVisibility`** (heartbeat) or increase the timeout. Max **12 hours**.
- "Lambda + SQS, messages processed twice" → queue visibility timeout **>= 6x** the function timeout.
- "Reduce **empty receives** / lower cost / lower latency" → **long polling** (up to **20 s**).
- "Messages that **keep failing**" → **DLQ** with `maxReceiveCount`. Set the DLQ retention **longer** than the source.
- "Grant access to queues by **tag** / scale permissions without editing policies" → **ABAC** with queue **tags** (`aws:ResourceTag` = `aws:PrincipalTag`).
- "**Scale** consumers based on load" → ASG with a CloudWatch alarm on **queue length / backlog per instance**.
- "Message larger than the limit" → **S3** + **Extended Client Library** (up to 2 GB).
- "Pass **metadata** without parsing the body" → **message attributes** (max 10, count toward size). "How many times was it retried?" → **`ApproximateReceiveCount`**.
- "**Delay** delivery of new messages" → **delay queue** (up to 15 min). "Different delay **per message**" → **message timer** (standard queues only).
- "Needs **multiple consumers** each getting a copy, or **replay**" → not SQS: **SNS** (copies) or **Kinesis** (replay).
- Retention: default **4 days**, max **14 days**. SQS has **no limit** on the number of messages stored.

Related: [SNS](../SNS/README.md), [S3](../S3/README.md), [IAM](../IAM/README.md), [EC2](../EC2/README.md).
