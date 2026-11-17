# Amazon SNS (Simple Notification Service)

**Amazon SNS** is a fully managed **publish/subscribe (pub/sub)** messaging service. A producer sends a message **once** to a **topic**, and SNS **pushes** it to **many subscribers** at the same time. It decouples applications and is also used to send notifications to people (email, SMS, mobile push).

## Pub/Sub Concepts (intro)

In the **point-to-point** model (e.g. a queue like **SQS**), a producer sends a message to one queue and **one consumer** processes it. This couples the producer to a specific consumer's pace and address.

In the **pub/sub** model:

```
                         ┌─► Subscriber A (email)
Publisher ──► Topic ─────┼─► Subscriber B (SQS queue)
 (producer)   (channel)  ├─► Subscriber C (Lambda)
                         └─► Subscriber D (HTTP endpoint)
```

- **Publisher**: sends events to a topic. It **does not know** who the subscribers are.
- **Topic**: a logical channel that receives messages and fans them out.
- **Subscriber**: registers interest in a topic and receives **every message** published to it (optionally filtered).
- **Fan-out**: one message → many receivers, in parallel.
- **Loose coupling**: add or remove subscribers without changing the publisher.
- **Push vs pull**: SNS **pushes** to subscribers. SQS is **pull**-based (consumers poll).

## Core Concepts

| Concept | What it is |
|---|---|
| **Topic** | The channel messages are published to. Has an **ARN** and an access policy. |
| **Publisher** | Any app or AWS service that calls `Publish` (or sends events natively). |
| **Subscription** | Connects an **endpoint** to a topic using a protocol. Must be **confirmed** for some protocols (email, HTTP/S). |
| **Message** | Up to **256 KB** (up to **2GB** with special Java/Python libraries), with optional **message attributes** (metadata). |

## Subscriber Types (Endpoints)

- **Amazon SQS** queues
- **AWS Lambda** functions
- **Kinesis Data Firehose** (to S3, Redshift, OpenSearch, etc.)
- **HTTP / HTTPS** endpoints (webhooks)
- **Email** / **Email-JSON**
- **SMS** text messages
- **Mobile push** notifications (APNs, FCM, ADM...) via platform applications

## Topic Types

| | **Standard** | **FIFO** |
|---|---|---|
| Throughput | Nearly **unlimited** | High, but limited (per topic) |
| Ordering | **Best-effort** | **Strict**, per message group |
| Duplicates | **At-least-once** delivery (possible duplicates) | **Exactly-once** (deduplication) |
| Subscribers | All types | **SQS** queues (FIFO and standard) and others (e.g. Lambda, Firehose, HTTPS) |

## Key Features

- **Message filtering**: a **filter policy** on each subscription delivers only the messages whose attributes (or body) match.
- **Fan-out pattern**: SNS topic → **multiple SQS queues**, each processed independently and durably.
- **Delivery retries** with a **delivery policy**, plus a **dead-letter queue (DLQ)** (an SQS queue) per subscription for undeliverable messages.
- **Message archiving and replay** (FIFO topics).
- **Raw message delivery** to skip the SNS JSON wrapper for SQS and HTTP endpoints.
- **Cross-account** access through topic policies; **cross-Region** delivery to SQS/Lambda.
- **Message data protection**: detect and mask sensitive data.

## Security

- **Encryption in transit** (HTTPS) and **at rest** with **KMS** (server-side encryption).
- **IAM policies** control who can publish or subscribe.
- **SNS access policy** (resource-based) allows other accounts and AWS services (e.g. S3, CloudWatch) to publish.
- **VPC endpoints** (PrivateLink) to publish without traversing the internet.

## Common Integrations (Publishers)

Many AWS services publish to SNS directly: **CloudWatch Alarms**, **S3 event notifications**, **Auto Scaling** events, **CloudFormation**, **AWS Budgets**, **DynamoDB**, **RDS events**, **EventBridge** rules (as a target), and more.

## Common Patterns

- **Fan-out**: S3 event or app → **SNS topic** → multiple **SQS queues** / Lambdas (e.g. thumbnails, metadata, analytics all triggered by one upload).
- **Alerting**: CloudWatch alarm → SNS → email / SMS / Slack (via Lambda or AWS Chatbot).
- **Application-to-person (A2P)**: SMS and mobile push to end users.
- **Event-driven microservices**: services publish domain events; others subscribe.

## SNS vs SQS vs EventBridge vs Kinesis

| | **SNS** | **SQS** | **EventBridge** | **Kinesis Data Streams** |
|---|---|---|---|---|
| Model | **Pub/sub, push** | **Queue, pull** | Event bus, rules, **push** | **Stream**, pull, ordered shards |
| Consumers | Many (fan-out) | One consumer per message | Many targets by rule | Many, each reads the stream |
| Persistence | **No** (no storage; retries only) | Yes (up to **14 days**) | No | Yes (24 h to **365 days**), replayable |
| Best for | Notifications, fan-out | Decoupling, buffering | Routing events (SaaS, AWS, custom), schedules | Real-time ordered data streaming |

## Exam Tips

- "**Fan-out**", one message to **many** subscribers → **SNS** (often **SNS + SQS**).
- "Send **email / SMS / mobile push** notifications" → **SNS**.
- "**React to a CloudWatch alarm**" → alarm action → **SNS**.
- "Decouple, **buffer**, consumers pull at their own pace" → **SQS**. SNS does **not** store messages.
- "Need **ordering** and **deduplication** with fan-out" → **SNS FIFO + SQS FIFO**.
- "Subscribers want only **some** messages" → **subscription filter policy**.
- "Failed deliveries" → **DLQ** on the subscription.
- Message size limit **256 KB**; larger payloads → store in **S3** and send a reference.

Related: [S3](../S3/README.md), [IAM](../IAM/README.md), [API](../API/README.md).
