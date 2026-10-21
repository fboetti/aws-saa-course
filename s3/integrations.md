# S3 × AWS Services — Interoperability (exam focus)

S3 is AWS's **central data hub**: nearly every AWS service can *write objects to* S3 (landing zone) or *read from* S3 (source of truth). The pattern "store everything in S3, then attach the right service" is behind most data-lake exam questions.

## Decision table (trigger phrase → service)

| The question says… | Answer |
|---|---|
| "Run SQL queries directly on files in S3, serverless, no loading" | **Amazon Athena** |
| "Crawl/ETL/catalog the data, create the schema for the lake" | **AWS Glue** (Data Catalog) |
| "Visualize/query results for business users" | **Amazon QuickSight** |
| "Query S3 from inside Redshift without copying data" | **Redshift Spectrum** (external schema) |
| "ETL Hadoop/Spark jobs at scale over S3" | **Amazon EMR** (S3A connector) |
| "Deliver streaming/near-real-time data into S3" | **Kinesis Data Firehose** |
| "Do something whenever an object is created/deleted" | **Lambda / EventBridge** (event notifications) |
| "Machine-learning training data / model artifacts" | **Amazon SageMaker** (S3 is the default input/output channel) |
| "Classify/scan objects for PII or sensitive data" | **Amazon Macie** |
| "Audit who read/wrote objects" | **CloudTrail data events** + S3 server access logging |
| "Detect compromised/anomalous bucket activity" | **GuardDuty S3 Protection** |
| "Back up the bucket itself, immutably" | **AWS Backup** (+ Vault Lock) |
| "Load files from S3 into Redshift" | **Redshift COPY** command |
| "Stream SaaS/CRM data into S3" | **Amazon AppFlow** |
| "Serve objects globally through a CDN" | **CloudFront** (S3 origin, OAC/OAI) |
| "Let FTP/SFTP clients read/write a bucket" | **AWS Transfer Family** |

## Analytics and query layer

- **Amazon Athena** — serverless SQL over S3 objects (CSV, JSON, Parquet, ORC, Avro); nothing to provision, **pay per data scanned**. Exam lever: switch to **columnar formats + partitioning** (e.g. by date) to cut query cost dramatically; query results are written to an S3 bucket of your choice. Schema comes from the **Glue Data Catalog**.
- **AWS Glue** — serverless **ETL** plus **crawlers** that infer schemas and register tables in the Data Catalog; jobs read from and write to S3. The Data Catalog is the shared metadata layer for **Athena, EMR, Redshift Spectrum** (governed centrally via **Lake Formation** permissions).
- **Amazon EMR** (Hadoop/Spark/Hive) — uses **S3 as durable storage** (via the `s3a` connector) instead of HDFS: compute and storage scale independently, clusters can be ephemeral. Hive/Spark metadata in Glue/Hive Metastore.
- **Amazon Redshift Spectrum** — `CREATE EXTERNAL SCHEMA` → query S3 **in place** (no `COPY` first), billed per byte scanned; combine external tables with internal Redshift tables.
- **Amazon QuickSight** — dashboards on top of Athena/S3.
- **S3 Select / Glacier Select** — push a SQL *expression* into a GET so **S3 filters the object server-side**: only matching bytes leave S3 (cheaper/faster partial reads of one object — different job from Athena, which queries across many).

## Streaming and ingestion

- **Kinesis Data Firehose** — the "load stream into S3" answer: buffers (e.g. 60 s–15 min), optionally **transforms with Lambda**, converts format (e.g. to Parquet) and delivers to S3 **near real time** — no consumers to manage.
- **Kinesis Data Streams / IoT** — for custom consumers (e.g. Lambda) that write batches of objects.
- **Amazon AppFlow** — pulls Salesforce/Zendesk/SaaS data into S3 (and pushes out), no glue code.
- **AWS Database Migration Service (DMS)** — can use **S3 as a source or target**, handy for landing database extracts in the lake.
- **EventBridge** — S3 events routed to **200+ AWS services** (beyond the classic Lambda/SNS/SQS targets), with filtering rules.

## Compute and event-driven processing

- **Lambda + event notifications** (`ObjectCreated`, `ObjectRemoved`, `ObjectRestore`…) → **Object Lambda transforms**, thumbnail generation, validation, indexing pipelines. Events carry **object metadata, not the payload** (size limits apply), so Lambda fetches the data itself.
- **ECS/EKS/EC2** read/write through the SDK; **Step Functions** orchestrates multi-step document pipelines over S3.

## Machine learning

- **SageMaker**: training data and model artifacts live in S3 — S3 is the recommended **input channel** and the default output location.
- **Rekognition / Textract / Comprehend**: batch APIs take **S3 input/output locations** directly, so TB-scale media/documents never move through your code.

## Security, governance, compliance integrations

- **CloudTrail data events** — object-level logging (`GetObject`, `PutObject`): *who touched which object* (costly at high volume → usually on for sensitive buckets via advanced event selectors).
- **S3 server access logging** — request-level logs for the bucket itself.
- **Amazon Macie** — automated **sensitive-data discovery** (PII) across buckets.
- **GuardDuty S3 Protection** — anomaly detection on CloudTrail data events for buckets.
- **AWS Config** rules (`s3-default-encryption-enabled`, public-access checks) + **IAM Access Analyzer** for sharing/public exposure.
- **AWS Backup** — centralized, cross-account/cross-region backups of S3; **Vault Lock** gives WORM immutability (ransomware/compliance), complementing in-bucket [Object Lock](objects.md#object-locking-worm).

## Non-AWS / legacy interop (brief)

- **CloudFront** fronts S3 for global delivery (free-ish origin traffic, HTTPS, caching, OAC/OBA).
- **AWS Transfer Family** speaks **SFTP/FTPS/FTP** to partners who can't do REST — the bucket stays the storage.
- For S3-*compatible* third-party storage/clients (MinIO, rclone, custom endpoints) the same SDK/API works with a custom `endpoint` — see the [references](#references).

## Exam checklist

- Data lake in S3 = **Glue catalog → Athena (query) → QuickSight (visualize)**; add **Lake Formation** when the question is *permissions across analytics services*.
- "Reduce Athena cost" → **columnar formats (Parquet/ORC) + partitioning** (it bills per byte scanned).
- "Streaming landing zone with transformation, no infrastructure" → **Firehose (+ Lambda)**.
- "Don't copy the data into Redshift" → **Spectrum**; "get it *into* Redshift" → **COPY**.
- Event-driven → **S3 events to Lambda/EventBridge**; hybrid/legacy producers/consumers → **Storage Gateway, DataSync, Transfer Family, Snow** (covered elsewhere in the course).
- "Who accessed this object?" → **CloudTrail data events** (not server access logs — those are bucket-request level).

## References

- AWS docs — [Using Amazon S3 with AWS services](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-using-service.html)
- AWS docs — [Querying your data lake with Athena](https://docs.aws.amazon.com/athena/latest/ug/getting-started.html)
- AWS docs — [Amazon S3 event notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html)
- AWS docs — [What is AWS Glue?](https://docs.aws.amazon.com/glue/latest/dg/what-is-glue.html)
- AWS re:Post/AWS blogs — [S3 Select](https://aws.amazon.com/blogs/aws/s3-select/)

← Back to the [S3 overview](README.md)
