# AWS CloudTrail

**AWS CloudTrail** records **API calls and account activity** across your AWS account: **who** did **what**, **when**, **from where**, and **on which resource**. It is the **audit and governance** service. Calls made from the Console, CLI, SDKs and other AWS services are all captured. It is **enabled by default** (event history) and is **regional**, with **multi-Region** and **organization** trails to aggregate.

```
 Console / CLI / SDK / AWS service ──► API call ──► CloudTrail ──┬─► Event history (90 days, free)
                                                                 ├─► Trail ──► S3 (long term) ──► Athena
                                                                 │        └──► CloudWatch Logs (alarms, Insights)
                                                                 ├─► EventBridge (react in near real time)
                                                                 └─► CloudTrail Lake (SQL queries)
```

- **CloudTrail** = *who did what* (audit). **CloudWatch** = *how it performs* (metrics, logs). **Config** = *what it looked like* (configuration history).
- CloudTrail records **API activity**, not what happens **inside** your instances or apps (use CloudWatch Logs for that).

## Event Types

| Type | What it records | Default |
|---|---|---|
| **Management events** | **Control-plane** operations on resources: `RunInstances`, `CreateBucket`, `CreateUser`, `AttachRolePolicy`, console sign-ins. Split into **read** and **write** events. | **On** |
| **Data events** | **Data-plane**, high-volume operations: **S3 object-level** (`GetObject`, `PutObject`, `DeleteObject`), **Lambda invoke**, **DynamoDB item** access and more. | **Off** (extra cost) |
| **Insights events** | **Unusual activity** detected from the normal baseline (spikes in API calls or error rates). | **Off** (extra cost) |
| **Network activity events** | API calls made **through VPC endpoints**, to detect unexpected data access paths. | **Off** |

## Where Events Go

| Destination | Notes |
|---|---|
| **Event history** | Last **90 days** of **management events**, **searchable** and **free**, per Region. Cannot be extended, can't include data events. |
| **Trail → S3** | For **long-term** storage (beyond 90 days). Logs are JSON, **gzip**, delivered typically within about **5 to 15 minutes**. Encrypted with **SSE-S3** by default or **KMS**. Analyze with **Athena**. |
| **Trail → CloudWatch Logs** | Query with **Logs Insights**, and use **metric filters** + **alarms** (e.g. alarm on root login). |
| **EventBridge** | React to API calls (see below). |
| **CloudTrail Lake** | Managed **event data store**: query events with **SQL**, keep up to **7 years** (paid). |

### Trails

- A **trail** is a configuration that **delivers events to S3** (and optionally CloudWatch Logs).
- **Single-Region** or **multi-Region** (recommended: one trail covers **all Regions**, including new ones).
- **Organization trail**: created in the management account, logs **all accounts** in an AWS Organization.
- **Global service events** (IAM, STS, CloudFront) are logged as management events and included in a multi-Region trail.
- **Log file integrity validation**: hourly **digest files** signed (SHA-256 with RSA) to **detect tampering** or deletion of logs.
- Protect the bucket: **bucket policy**, **MFA Delete**, **Object Lock**, a **separate security account**.

## Anatomy of a CloudTrail Record

```json
{
  "eventVersion": "1.09",
  "eventTime": "2026-11-21T10:15:30Z",
  "eventSource": "ec2.amazonaws.com",
  "eventName": "TerminateInstances",
  "awsRegion": "eu-north-1",
  "sourceIPAddress": "203.0.113.10",
  "userIdentity": { "type": "IAMUser", "arn": "arn:aws:iam::111122223333:user/alice" },
  "requestParameters": { "instancesSet": { "items": [{ "instanceId": "i-0abc123" }] } },
  "errorCode": null,
  "readOnly": false
}
```

| Field | Meaning |
|---|---|
| **`userIdentity`** | **Who**: IAM user, assumed role, root, AWS service, federated user. |
| **`eventTime`** | **When** (UTC). |
| **`eventSource` / `eventName`** | **Which service and API** was called. |
| **`awsRegion` / `sourceIPAddress`** | **Where** it was called from. |
| **`requestParameters` / `responseElements`** | **What** was sent and returned. |
| **`errorCode` / `errorMessage`** | Present when the call **failed** (e.g. `AccessDenied`). |
| **`readOnly`** | `true` for read calls, `false` for write calls. |

## CloudTrail + EventBridge: Event Patterns

An **event pattern** is the **JSON filter** of an EventBridge rule. Its structure **mirrors the event** and only the fields you list are matched. Every **API call recorded by CloudTrail** becomes an event, so you can **react to any API call** (e.g. someone creates an IAM user, a security group opens port 22, an S3 bucket is deleted).

- **`detail-type`** is `"AWS API Call via CloudTrail"` and **`source`** is the service (`aws.ec2`, `aws.iam`, `aws.s3`).
- The CloudTrail record sits under **`detail`**, so you match on `detail.eventName`, `detail.eventSource`, `detail.userIdentity.type`...
- **Management events** reach the **default bus** without a trail you create. **Data events** (e.g. S3 `PutObject`) **require a trail** that logs them.

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": ["TerminateInstances"]
  }
}
```

### Pattern matching rules

- **Values are always in an array**. Several values in one field = **OR**. Several fields = **AND**.
- **Absent fields are ignored** (not matched against).

| Operator | Example | Matches |
|---|---|---|
| **Exact** | `"state": ["running", "stopped"]` | Either value. |
| **Prefix** | `"eventName": [{"prefix": "Delete"}]` | `DeleteBucket`, `DeleteUser`... |
| **Suffix** | `"key": [{"suffix": ".png"}]` | Names ending with `.png`. |
| **Equals ignore case** | `[{"equals-ignore-case": "alice"}]` | `Alice`, `ALICE`. |
| **Wildcard** | `[{"wildcard": "*/dev/*"}]` | Simple `*` patterns. |
| **Anything-but** | `"type": [{"anything-but": ["Root"]}]` | Everything **except** the listed values. |
| **Numeric** | `"size": [{"numeric": [">", 100, "<=", 500]}]` | Number ranges. |
| **Exists** | `"errorCode": [{"exists": true}]` | Field present (e.g. **failed** calls). Use `false` for absent. |
| **CIDR** | `"sourceIPAddress": [{"cidr": "10.0.0.0/8"}]` | IP in range. |
| **`$or`** | `"$or": [{...}, {...}]` | **OR across different fields**. |

```json
{
  "source": ["aws.signin"],
  "detail-type": ["AWS Console Sign In via CloudTrail"],
  "detail": { "userIdentity": { "type": ["Root"] } }
}
```

- Patterns are **case-sensitive** (except `equals-ignore-case`) and match **content only**, not transformations.
- **Test** a pattern against a sample event in the console (**Test event pattern**) or with `aws events test-event-pattern`.
- Targets then act: **SNS** alert, **Lambda** remediation, **SSM Automation**, **Step Functions**.

## Security and Cost

- **Cost**: **one copy of management events per Region is free** in event history and the first trail. **Additional trails**, **data events**, **Insights** and **Lake** are **paid**.
- **Access**: IAM controls who can view and manage trails. Restrict **S3 bucket** and **KMS key** access. Use an **organization trail** so member accounts **can't disable** it.
- **Alert on tampering**: `StopLogging`, `DeleteTrail`, `UpdateTrail` should trigger an alarm.

## Exam Tips (SAA)

- **Who deleted / changed this resource?** → **CloudTrail**.
- **Keep audit logs beyond 90 days** → **trail to S3** (query with **Athena**), or **CloudTrail Lake**.
- **Log S3 object access or Lambda invocations** → enable **data events** (off by default).
- **Detect unusual API activity** → **Insights events**.
- **Prove logs weren't modified** → **log file integrity validation**.
- **All accounts and Regions in one place** → **organization trail**, **multi-Region**.
- **React to an API call** (e.g. root login, security group change) → **EventBridge rule** with a **CloudTrail event pattern**.
- **Alarm on API activity** → CloudTrail → **CloudWatch Logs** → **metric filter** → **alarm**.
- **CloudTrail vs Config vs CloudWatch**: API history vs **configuration history and compliance** vs **performance metrics and logs**.
