# Amazon AppFlow

**Amazon AppFlow** is a fully managed **integration service** that securely moves data between **SaaS applications** (Salesforce, SAP, Zendesk, Slack, ServiceNow, Google Analytics...) and **AWS services** (S3, Redshift...) **in a few clicks, without writing code**.

## Purpose

Companies keep a lot of business data in SaaS tools. Getting it into AWS for analytics, ML or backup usually means writing and maintaining custom API scripts: authentication, pagination, rate limits, retries, schema changes. AppFlow replaces that **custom glue code** with managed, configurable **flows**.

Typical use cases:

- Load **Salesforce** opportunities/accounts into **S3 / Redshift** for analytics and BI (QuickSight).
- Back up SaaS data to **S3** (data lake).
- Push enriched data **back into a SaaS app** (e.g. S3 → Salesforce).
- Move data **between SaaS apps** (e.g. Salesforce → Snowflake).
- Feed events from SaaS apps to **EventBridge** for event-driven workflows.

## Sources and Destinations

| Side | Examples |
|---|---|
| **Sources** | Salesforce, SAP (OData), ServiceNow, Zendesk, Slack, Marketo, Google Analytics, Datadog, Dynatrace, Infor Nexus, Veeva, **S3**, 50+ connectors |
| **Destinations** | **Amazon S3**, **Redshift**, **EventBridge**, Lookout for Metrics, Salesforce, Snowflake, Zendesk, Marketo, Upsolver... |
| **Custom connectors** | Build your own with the **Custom Connector SDK** for any API |

## How It Works

```
SaaS app (Salesforce, SAP, Zendesk...) ──► AppFlow flow ──► S3 / Redshift / EventBridge / SaaS
          (source connector)        (map, filter, validate, transform)
```

A **flow** defines source, destination, field mapping and **trigger**:

| Trigger | Meaning |
|---|---|
| **On demand** | Run manually |
| **Scheduled** | Every N minutes/hours/days; can transfer **only new/changed records** (incremental) |
| **Event** | Runs in response to a SaaS **event** (e.g. Salesforce change data capture) |

Transformations (no code): **field mapping**, **filtering**, **validation**, **masking**, **merging/truncating** fields, partitioning and aggregating files in S3 (CSV, JSON, Parquet).

## Security

- Data **encrypted in transit** (TLS) and **at rest** (AWS KMS, AWS-managed or customer-managed key).
- **AWS PrivateLink**: for supported SaaS apps (e.g. Salesforce, Snowflake), data stays on the **AWS network**, not the public internet.
- SaaS credentials stored securely (OAuth tokens in **Secrets Manager**); IAM controls who can manage flows.

## Pricing

- Pay **per flow run** plus **per GB of data processed**. No upfront cost, no infrastructure.

## AppFlow vs Similar Services

| Need | Service |
|---|---|
| **SaaS app ↔ AWS** data transfer, no code | **AppFlow** |
| Complex ETL / transformations on data already in AWS | **AWS Glue** |
| Migrate **databases** | **DMS** |
| Copy **files** from on-prem NFS/SMB to S3/EFS/FSx | **DataSync** |
| SFTP/FTPS/FTP file exchange with partners into S3/EFS | **Transfer Family** |
| Real-time streaming data | **Kinesis** |
| Event routing (incl. some SaaS partners) | **EventBridge** |

## Exam Tips

- "**Transfer data from Salesforce / SAP / Zendesk / Slack (SaaS) to S3 or Redshift**" → **AppFlow**.
- "**Without writing code** / **no custom integration**" with SaaS apps → **AppFlow**.
- "SaaS data must **not traverse the public internet**" → AppFlow with **PrivateLink**.
- AppFlow is **bi-directional** (SaaS → AWS and AWS → SaaS) and supports **scheduled, event and on-demand** flows.
- Heavy transformations after loading → combine with **Glue**; analytics → **Redshift / Athena / QuickSight**.

Related: [S3](../../S3/README.md), [DataSync](../DataSync/README.md), [DMS](../DMS/README.md), [Transfer Family](../TransferFamily/README.md).
