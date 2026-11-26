# Amazon Redshift and Data Warehouse Concepts

## Data Warehouse Concepts

A **data warehouse** is a central repository of **structured, historical** data from many sources (operational databases, logs, SaaS apps), optimized for **analytics and reporting** rather than day-to-day transactions.

| | **OLTP** (databases) | **OLAP** (data warehouse) |
|---|---|---|
| Purpose | Run the business: many small **reads/writes** | **Analyze** the business: few, **large, complex queries** |
| Data | **Current**, normalized | **Historical**, aggregated, denormalized |
| Storage | **Row-oriented** | **Column-oriented** |
| Typical query | `UPDATE orders SET ... WHERE id = 42` | `SELECT region, SUM(sales) ... GROUP BY region` over billions of rows |
| AWS | **RDS**, **Aurora**, **DynamoDB** | **Redshift** |

- **ETL** (Extract, Transform, Load): transform data **before** loading it into the warehouse (e.g. **AWS Glue**).
- **ELT**: load **raw** data first, transform **inside** the warehouse with SQL (common with Redshift).
- **Data warehouse** = structured, **schema-on-write**. **Data lake** = raw, any format, **schema-on-read** (S3). **Lakehouse** = both together (Redshift Spectrum, Athena + Lake Formation).
- **Data mart**: a smaller warehouse focused on **one team or subject** (e.g. finance).
- **Star schema**: a central **fact table** (measures: sales, clicks) surrounded by **dimension tables** (customer, product, date). The usual warehouse model.

### Why column-oriented storage?

Analytic queries read **a few columns across many rows**. Storing data **by column** means:
- Only the **needed columns** are read from disk (less I/O).
- Similar values sit together, so **compression** is far better.
- Scans and aggregations are much faster than with row storage.

## Amazon Redshift

**Amazon Redshift** is a fully managed, **petabyte-scale** data warehouse. It is **PostgreSQL-based** (use standard **SQL** with JDBC/ODBC and BI tools), uses **columnar storage**, **compression** and **massively parallel processing (MPP)**. It is built for **OLAP**, **not OLTP**.

```
 BI tools / SQL clients ──► [ Leader node ] ──► [ Compute node ] ──► slices (parallel)
 (QuickSight, Tableau)       parses, plans,     [ Compute node ] ──► slices
                             aggregates         [ Compute node ] ──► slices
                                                      │
                          S3 ◄── COPY / UNLOAD / Spectrum ──► data lake
```

### Architecture

| Component | Role |
|---|---|
| **Cluster** | One **leader node** plus one or more **compute nodes**. |
| **Leader node** | Receives queries, builds the **execution plan**, distributes work and **aggregates** results. Not billed separately (for 2+ node clusters). |
| **Compute nodes** | Store the data and run the query steps **in parallel**. Divided into **slices**. |
| **Node types** | **RA3** (managed storage on S3, scale compute and storage **independently**), **DC2** (local SSD, older, small datasets). |
| **Managed storage** | RA3 keeps hot data on local SSD and the rest in **S3**, automatically. |

#### Dense Storage vs Dense Compute

| | **Dense Storage (DS)** | **Dense Compute (DC)** | **RA3** (current) |
|---|---|---|---|
| Node types | `ds2` (legacy) | `dc2` (`dc1` is legacy) | `ra3` |
| Disk | Large **HDD** | Fast local **SSD** | Local **SSD** cache + **S3** managed storage |
| Optimized for | **Large** datasets at **low cost per TB** | **Performance**, **smaller** datasets (low latency) | **Both**: scale compute and storage **independently** |
| Capacity | Up to **petabytes** | Hundreds of GB up to a few TB per cluster, grows by adding nodes | Pay for storage **separately** |

- **Dense Storage** = lots of cheap disk, slower. **Dense Compute** = more CPU/RAM and SSD per TB, faster, but you must add **nodes** (and pay for compute) to store more data.
- **DS2** is **deprecated**: AWS recommends **RA3**. **DC2** is still available for small datasets (under about **1 TB**, where it can be cheaper).
- Exam rule of thumb: **large data, cost-sensitive** → dense storage / **RA3**. **Fast queries on smaller data** → dense compute. Need to **scale compute and storage separately** → **RA3**.

#### Single-node vs Multi-node

| | **Single-node** | **Multi-node** |
|---|---|---|
| Nodes | **1** node (**160 GB**) does both leader and compute work | **1 leader** + **2 to 128** compute nodes |
| Parallelism | Limited to the slices of one node | **MPP** across nodes: queries and loads run in parallel |
| Scaling | Resize to a bigger node type or to multi-node | Add or remove nodes (**elastic resize**) |
| Data protection | **No replication** of data between nodes | Data is **mirrored** to another compute node, so a node failure is tolerated |
| Leader node | Shared with compute | Separate, **not billed** extra |
| Multi-AZ | **No** | Yes, on **RA3** (2+ nodes) |
| Use for | **Dev, test, small datasets**, learning | **Production**, large data, high concurrency |

- Multi-node is the only option for production: it gives **performance** (parallel slices) and **resilience** (node failure recovery). **Single-node** has no data replication, so rely on **snapshots**.
- Don't confuse with **Multi-AZ**: multi-node is about nodes **inside one cluster** (and usually **one AZ**), Multi-AZ is about the cluster across **AZs**.

- **Single-AZ** by default: a cluster lives in **one AZ**. **Multi-AZ** is available for RA3 (high availability, automatic failover).
- A cluster runs in a **VPC**, supports **Enhanced VPC Routing** (COPY/UNLOAD traffic stays in your VPC).

### Redshift Serverless

- **No cluster to manage**: capacity is measured in **RPUs** (Redshift Processing Units) and **scales automatically**.
- **Pay per use** (per second of compute used, plus storage). Good for **unpredictable** or **intermittent** workloads.
- Provisioned clusters are cheaper for **steady, predictable** load (and support **Reserved Instances**).

### Loading and Unloading Data

| Method | Notes |
|---|---|
| **`COPY`** | Fastest way to **bulk load** from **S3** (also DynamoDB, EMR, EC2). Loads **in parallel**, so split into **multiple files** (a multiple of the number of slices). Prefer compressed files. |
| **`UNLOAD`** | Export query results to **S3**. |
| **Zero-ETL integration** | Near real-time replication from **Aurora**, **RDS** and **DynamoDB** into Redshift, with no pipeline to build. |
| **Streaming ingestion** | Load directly from **Kinesis Data Streams / Firehose** and **MSK**. |
| **Data sharing** | Share live data **between Redshift clusters** without copying it. |
| **AWS DMS / Glue** | Migrate or transform data on the way in. |

- Individual `INSERT` statements are **slow**. Use `COPY`.

### Redshift Spectrum

- Run SQL on **data in S3** **without loading it** into Redshift, and **join** it with tables in the cluster.
- Uses a **fleet of Spectrum nodes** outside your cluster, so it scales the scan independently.
- Uses the **Glue Data Catalog** (or Athena catalog) for table definitions. Formats: Parquet, ORC, CSV, JSON, Avro.
- **Spectrum vs Athena**: Spectrum extends an **existing Redshift** warehouse. **Athena** is standalone, serverless, no cluster.

### Performance Design

| Concept | What it does |
|---|---|
| **Distribution style** | How rows are spread across nodes: **AUTO**, **EVEN** (round robin), **KEY** (same key on the same node, good for joins), **ALL** (full copy on every node, for small dimension tables). |
| **Sort key** | Orders rows on disk so the engine can **skip blocks** (zone maps). Pick columns used in filters (e.g. date). |
| **Compression encoding** | Per-column encodings, applied automatically (`COPY` can choose). |
| **`VACUUM`** | Reclaims space and re-sorts rows after deletes and updates (auto vacuum runs in the background). |
| **`ANALYZE`** | Updates table statistics for the query planner (also automatic). |
| **Workload management (WLM)** | **Queues** and priorities so short queries are not stuck behind long ones. **Automatic WLM** is the default. |
| **Concurrency Scaling** | Adds **temporary extra clusters** automatically for bursts of concurrent queries. |
| **Materialized views** | Precomputed results for repeated queries. |
| **Result caching** | Identical queries return cached results instantly. |
| **Short query acceleration (SQA)** | Fast lane for short queries. |

### Availability, Backup and DR

- **Snapshots** are stored in **S3**. **Automatic** (about every **8 hours** or **5 GB** per node, default **1 day** retention, up to 35 days) and **manual** (kept until deleted).
- **Restore** a snapshot to a **new cluster**.
- **Cross-Region snapshot copy** for **disaster recovery** (can be **automated**, supports **KMS-encrypted** snapshots with a grant).
- **Multi-AZ** (RA3) for high availability. Without it, a cluster is **single-AZ**: use snapshots to recover in another AZ.
- **Elastic resize** (add or remove nodes in minutes) and **classic resize**. **Concurrency Scaling** for read bursts.

### Security

- **Encryption at rest**: **KMS** or **HSM**, for the cluster, snapshots and backups. **In transit**: **SSL/TLS**.
- **VPC**, **security groups**, optionally **not publicly accessible**.
- **IAM** for API access and **IAM roles attached to the cluster** (to let `COPY`/`UNLOAD`/Spectrum reach **S3**, Glue, etc.).
- **Database users and groups**, **column-level** and **row-level security**, **dynamic data masking**.
- **Audit logging** to **S3** (connection, user and activity logs), **CloudTrail** for API calls, **CloudWatch** for metrics.
- **Lake Formation** for centralized governance on the data lake.

### Other Features

- **Redshift ML**: create and use **SageMaker** models with SQL.
- **Federated queries**: query live **RDS/Aurora PostgreSQL and MySQL** from Redshift.
- **Redshift Query Editor v2**: browser-based SQL client.
- **Redshift Data API**: run SQL over **HTTPS** with no persistent connection or drivers (works well from **Lambda**).
- **Integrates with QuickSight** and other BI tools (JDBC/ODBC).

### Pricing

- Redshift is an **expensive** service compared with most AWS databases: you pay for **nodes running 24/7**, even when idle. **Pause** a provisioned cluster, use **Serverless** for intermittent load, buy **Reserved Instances** for steady load, and **delete** unused dev/test clusters (take a final snapshot).
- **Provisioned**: per **node-hour** (**Reserved Instances** for 1 or 3 years save a lot). **Serverless**: per **RPU-second**.
- **Managed storage** (RA3 / Serverless) per GB-month. **Spectrum** per **TB scanned**.
- **Backup storage** beyond the free allowance. **Concurrency Scaling** has free credits, then per-second billing.
- Data transfer **into** Redshift is free, **cross-Region** snapshot copy is charged.

## Cheat Sheet Additions

- **Load sources**: **S3**, **EMR**, **DynamoDB**, or multiple data sources on **remote hosts** (over SSH).
- Most common use case: **Business Intelligence** (BI) and reporting.
- **Billing**: per **hour** for each node, the **leader node is not billed** in a multi-node cluster.
- **Backups**: Redshift attempts to keep **3 copies** of your data: the **original**, a **replica on the compute nodes** and a **backup in S3**. Snapshots can be copied **asynchronously** to **another Region** (delivered to S3).
- **Retention**: backups default to **1 day**, up to **35 days**.
- **Storage layout**: similar (same-column) data is stored **sequentially on disk** for faster reads.
- **Empty table import**: when importing into an **empty table**, Redshift can **sample the data** to create a schema.
- **MPP** distributes both **queries and data** across all nodes.

## Redshift vs Other Analytics Services

| Service | Model | Use when |
|---|---|---|
| **Redshift** | **Data warehouse** (OLAP, SQL, cluster or serverless) | Complex, **repeated** analytics on **structured** data, BI dashboards, joins over large datasets |
| **Athena** | **Serverless** SQL on **S3** (per TB scanned) | **Ad hoc** queries on a data lake, logs (ALB, CloudTrail, VPC Flow) |
| **EMR** | Managed **Hadoop/Spark** clusters | Big data **processing**, custom frameworks, ML pipelines |
| **Glue** | Serverless **ETL** + **Data Catalog** | Transform and catalog data |
| **OpenSearch** | **Search** and log analytics | Full-text search, dashboards on logs |
| **RDS / Aurora** | **OLTP** | Transactional applications |
| **DynamoDB** | **NoSQL** key-value | Low latency at scale, not analytics |

## Exam Tips (SAA)

- "**Data warehouse**", "**analytics** / **BI** on **petabytes** of structured data", "**OLAP**", "complex SQL queries" → **Redshift**.
- "**OLTP**" / transactions → **RDS / Aurora**, **not** Redshift.
- "Query **S3 data** from Redshift **without loading**" → **Redshift Spectrum**.
- "**Ad hoc** SQL on S3, **serverless**, no cluster" → **Athena**.
- "**Bulk load** into Redshift fast" → **`COPY`** from **S3** (multiple files, parallel). Not row-by-row `INSERT`.
- "**Unpredictable / intermittent** workload, no management" → **Redshift Serverless**.
- "**Steady** workload, lower cost" → provisioned cluster + **Reserved Instances**.
- "**Disaster recovery**" → **snapshots** with **cross-Region copy** (Redshift is **single-AZ** unless **Multi-AZ** RA3).
- "Many **concurrent** queries slow down" → **Concurrency Scaling** (and **WLM**).
- "**Scale compute and storage independently**" → **RA3** nodes.
- "Near real-time analytics on **Aurora / DynamoDB** data without ETL" → **zero-ETL integration**.
- "**Share data** between clusters / accounts without copying" → **data sharing**.
- "Cluster needs to read **S3** during `COPY`" → attach an **IAM role** to the cluster.
- "**Encrypt** the warehouse" → **KMS** (or HSM). "**Audit** queries/connections" → **audit logging** to S3.
- "Run SQL from **Lambda** without managing connections" → **Redshift Data API**.
- "Dashboards" → **QuickSight** on Redshift.

Related: [S3](../S3/README.md), [Kinesis](../Kinesis/README.md), [IAM](../IAM/README.md), [CloudTrail](../CloudTrail/README.md), [CloudWatch](../CloudWatch/README.md), [OpenSearch](../OpenSearch/README.md).
