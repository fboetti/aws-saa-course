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

## Subscription Protocols (Endpoints)

| Protocol | Endpoint | Notes |
|---|---|---|
| **sqs** | SQS queue (standard or FIFO) | Needs a queue policy allowing the topic to `SendMessage`. Same or cross-account / cross-Region. Most common fan-out target. |
| **lambda** | Lambda function | Invoked **asynchronously**. Needs a resource-based permission for SNS. |
| **firehose** | Kinesis Data Firehose stream | Deliver to S3, Redshift, OpenSearch, Splunk, etc. Needs an IAM role for SNS. |
| **http** / **https** | Web endpoint (webhook) | Must **confirm** the subscription (`SubscribeURL` in a `SubscriptionConfirmation` message). HTTPS is preferred. |
| **email** | Email address | Plain-text. Recipient must **confirm** via link. |
| **email-json** | Email address | Same, but the body is the **JSON** SNS payload. |
| **sms** | Phone number | A2P text messages. Subject to spending limits and opt-out rules. |
| **application** | Mobile push platform endpoint | APNs, FCM, ADM, etc. via a **platform application**. |

- **Auto-confirmed**: SQS, Lambda and Firehose in the **same account** (when subscribed by an authorized principal). **Manual confirmation**: email, email-json, HTTP/S.
- **FIFO topics** support: SQS (FIFO/standard), Lambda, Firehose and HTTPS. They do **not** support email, SMS or mobile push.
- Each subscription can have its own **filter policy**, **DLQ**, **delivery policy** and **raw message delivery** setting.

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

## Application as Subscriber (Mobile Push)

The **application** protocol delivers a message to a **mobile app** installed on a device as a **push notification**, through a platform notification service.

```
Publisher ──► SNS Topic ──► Platform application ──► APNs / FCM / ADM ──► Device (app)
```

- **Platform application**: an SNS object that represents your app on one **push notification service (PNS)**, holding the **credentials** for it.
  - **APNs** (Apple iOS/macOS), **FCM** (Google Firebase, Android and others), **ADM** (Amazon Device Messaging), **Baidu**, **WNS** (Windows), **MPNS**.
- **Platform endpoint**: one per **device token** (a specific app install) under a platform application. SNS creates it via `CreatePlatformEndpoint` when the app registers its token.
- **Flow**: the app registers with the PNS and gets a **device token** → your backend creates a **platform endpoint** in SNS → subscribe the endpoint (protocol `application`) to a topic, **or** publish **directly** to the endpoint.
- **Direct publish** (one device) vs **topic publish** (broadcast to many devices and other subscriber types at once).
- **Message format**: use `MessageStructure: json` to send a **different payload per platform** (keys like `APNS`, `GCM`/`FCM`, `ADM`, plus `default`).
- **Tokens expire or get uninstalled**: SNS marks the endpoint **disabled** when the PNS reports it invalid. Clean up or re-enable endpoints with the refreshed token.
- Can also use **SNS delivery status logging** (CloudWatch Logs) to track push success and failure.
- **Not available on FIFO topics.**
- **Related, not the same**: **SMS** and **email** are other person-facing endpoints that do not need a platform application.

## Subscription Filter Policy

By default every subscriber receives **every message**. A **filter policy** is a **JSON** document attached to a **subscription** (not the topic) so SNS delivers only matching messages. Non-matching messages are simply **not delivered** to that subscriber (no cost to the others).

- **Filter policy scope**:
  - `MessageAttributes` (default): matches the message **attributes** set by the publisher.
  - `MessageBody`: matches fields in the **JSON body** (supports nested keys).
- A message must match **all** keys (**AND**); the values listed for one key are **OR**.
- **Operators**: exact string/number match, `prefix`, `suffix`, `anything-but`, `numeric` (`>`, `<`, `=`, ranges), `exists` (true/false), `equals-ignore-case`, and `$or` across keys.
- A subscription **without** a filter policy receives everything.

```json
{
  "store": ["example_corp"],
  "event": [{"anything-but": "order_cancelled"}],
  "price_usd": [{"numeric": [">=", 100]}],
  "customer_interests": ["rugby", "football"]
}
```

Example: one **orders** topic, with `order_placed` → billing queue, `order_cancelled` → refund Lambda, and everything → audit queue. The publisher sends once and does not need to know who consumes what.

## Delivery Policy (Retries)

A **delivery policy** defines how SNS **retries** failed deliveries to a subscriber. It can be set at the **topic** level (default for all its HTTP/S subscriptions) and **overridden per subscription**.

- **Applies to HTTP/S endpoints only** for customizable policies. For **SQS, Lambda and Firehose** (AWS-managed endpoints), SNS uses its own **fixed retry policy** (many retries over up to **23 days**, not configurable). **Email / SMS / mobile push** use their own provider-side behavior.
- **A delivery is considered failed** when the endpoint is unreachable or returns a non-2xx status. **Client-side errors** (e.g. endpoint deleted, permission denied) are **not retried**.
- **Retry phases** (in order):
  1. **Immediate retry**: `numNoDelayRetries` (retries with no wait).
  2. **Pre-backoff**: `numMinDelayRetries` retries, `minDelayTarget` seconds apart.
  3. **Backoff**: `numRetries` total with delay growing from `minDelayTarget` to `maxDelayTarget`, following a **backoff function**: `linear`, `arithmetic`, `geometric` or `exponential`.
  4. **Post-backoff**: `numMaxDelayRetries` retries, `maxDelayTarget` seconds apart.
- **Throttling**: `maxReceivesPerSecond` caps the delivery rate to a subscriber (set in the topic's `defaultThrottlePolicy`) to avoid overwhelming it.
- **After retries are exhausted** the message is **dropped**, unless the subscription has a **DLQ** (an SQS queue), which then receives it for later analysis or redrive. Add a DLQ to avoid losing messages.
- **Delivery status logging**: log success and failure per protocol to **CloudWatch Logs** (needs an IAM role) for troubleshooting.

```json
{
  "healthyRetryPolicy": {
    "minDelayTarget": 1,
    "maxDelayTarget": 60,
    "numRetries": 50,
    "numNoDelayRetries": 3,
    "numMinDelayRetries": 2,
    "numMaxDelayRetries": 35,
    "backoffFunction": "exponential"
  },
  "throttlePolicy": { "maxReceivesPerSecond": 10 }
}
```

## Dead-Letter Queue (DLQ)

A **DLQ** is an **SQS queue** that captures messages SNS **could not deliver** to a subscriber, so they are not lost and can be analyzed or reprocessed.

- **Configured per subscription** (not per topic) through a **redrive policy** (`RedrivePolicy` with the DLQ ARN). Each subscription can have its own DLQ, or share one.
- A message goes to the DLQ when **delivery fails after all retries** are exhausted (see the delivery policy), or immediately on **non-retryable client errors** (e.g. Lambda function or SQS queue deleted, permission denied).
- **Same account and Region** as the subscription, and the DLQ type must match the topic: **FIFO topic → FIFO DLQ**, **standard topic → standard DLQ**.
- The DLQ needs a **queue policy** allowing `sns.amazonaws.com` to `sqs:SendMessage` (conditioned on the subscription/topic ARN).
- Messages keep their **message attributes**, plus error details such as `ERROR_CODE` and `ERROR_MESSAGE`, to help debugging.
- Works for **all protocols** that deliver to AWS-managed endpoints (SQS, Lambda, Firehose) and HTTP/S. It is **not** used for email, SMS or mobile push failures.
- **Monitor** the DLQ with a **CloudWatch alarm** on `ApproximateNumberOfMessagesVisible` (or `NumberOfNotificationsFailed` on the topic), then **fix the cause** and **redrive** the messages (SQS DLQ redrive to source/another queue, or reprocess with Lambda).
- **Not to be confused** with an SQS queue's own DLQ, which captures messages a **consumer** failed to process. The SNS DLQ captures **delivery** failures from SNS to the subscriber.
- Set the DLQ **retention** long enough (up to **14 days**) to investigate, and **encrypt** it with KMS if messages are sensitive.

## Raw Message Delivery

By default SNS wraps every message in a **JSON envelope** (metadata + your payload as a string). With **raw message delivery** enabled on a subscription, SNS delivers **only the original message body**, with no wrapper.

```json
// Default (wrapped)
{
  "Type": "Notification",
  "MessageId": "22b80b92-...",
  "TopicArn": "arn:aws:sns:us-east-1:123456789012:orders",
  "Subject": "New order",
  "Message": "{\"orderId\": 42}",
  "Timestamp": "2026-11-18T10:00:00.000Z",
  "SignatureVersion": "1",
  "Signature": "...",
  "MessageAttributes": { ... }
}

// Raw message delivery
{"orderId": 42}
```

- **Per subscription** setting (`RawMessageDelivery = true`), **disabled by default**.
- Supported on **SQS**, **HTTP/S** and **Firehose** subscriptions. **Not** applicable to Lambda, email, SMS or mobile push.
- **Message attributes** are not lost: for SQS they become **SQS message attributes**, for HTTP/S they are sent as **headers** (`x-amz-sns-rawdelivery`, etc.).
- **Why use it**: consumers get the original payload directly, with no unwrapping or parsing, which is handy when the same message is also sent to non-SNS consumers or when the consumer expects a specific format. It also slightly reduces message size.
- **Trade-off**: you lose envelope fields such as `MessageId`, `Timestamp`, `Subject` and the **signature** (so no signature verification for HTTP/S endpoints).
- Combines with **filter policies** (filtering is done before delivery, so it still works on the attributes).

## Message Data Protection

**Message data protection** lets SNS **inspect messages in transit** through a topic and act on **sensitive data** (PII, PHI, financial data, credentials) using a **data protection policy** (JSON) attached to the **topic**. It is a managed, no-code alternative to scanning payloads in your own code.

- **Detects** sensitive data with **managed data identifiers** (e.g. names, email addresses, phone numbers, credit card numbers, SSNs, AWS secret access keys, health IDs) and **custom data identifiers** (your own **regex**).
- **Operations** (what to do when data is found):
  - **Audit**: report the **findings** (counts, no data) to a destination: **CloudWatch Logs**, **S3** or **Kinesis Data Firehose**. Can sample a percentage of messages.
  - **Deny**: **block** the message from being published (`Publish`) or from being delivered to subscribers (`Deliver`).
  - **De-identify**: **mask** (replace with `*`) or **redact** (remove) the data before delivery.
- **Direction**: policy statements apply on **inbound** (publish) and/or **outbound** (delivery) traffic. Outbound can be targeted at specific **principals** or protocols, so for example internal subscribers see full data while others get masked data.
- Applies to **standard topics** only (not FIFO) and is configured **per topic**.
- Complements **KMS encryption** (protects data at rest) and **IAM / topic policies** (control access). It controls the **content** of messages.

```json
{
  "Name": "__example_data_protection_policy",
  "Version": "2021-06-01",
  "Statement": [{
    "DataDirection": "Inbound",
    "Principal": ["*"],
    "DataIdentifier": ["arn:aws:dataprotection::aws:data-identifier/CreditCardNumber"],
    "Operation": { "Deny": {} }
  }]
}
```

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
- "**Push notification** to iOS / Android devices" → SNS **application** protocol with a **platform application** (APNs, FCM).
- "**React to a CloudWatch alarm**" → alarm action → **SNS**.
- "Decouple, **buffer**, consumers pull at their own pace" → **SQS**. SNS does **not** store messages.
- "Need **ordering** and **deduplication** with fan-out" → **SNS FIFO + SQS FIFO**.
- "Subscribers want only **some** messages" → **subscription filter policy**.
- "Failed deliveries" → **DLQ** on the subscription (an **SQS** queue, set with a **redrive policy**, same account/Region, FIFO ↔ FIFO).
- "Customize **retries / backoff** or **throttle** delivery to an HTTP endpoint" → **delivery policy**.
- "Detect / **mask** / **block** **PII** (credit cards, SSNs) in messages" → **SNS message data protection** policy.
- "Consumer receives the SNS **JSON wrapper** and wants the **original payload**" → enable **raw message delivery** on the subscription.
- Message size limit **256 KB**; larger payloads → store in **S3** and send a reference.

Related: [S3](../S3/README.md), [IAM](../IAM/README.md), [API](../API/README.md).
