# Amazon Athena

**Amazon Athena** is a **serverless, interactive query service** that lets you run standard **SQL** directly on data stored in **S3**, with **no infrastructure to manage** and **no loading** of data. It is built on **Presto/Trino** (SQL engine) and **Apache Hive** (DDL), and queries are **schema-on-read**.

```
 S3 (CSV, JSON, Parquet, ORC, Avro, logs)
        ▲                           │ table definitions
        │ read (scan)               ▼
   [ Athena ] ◄──────────── Glue Data Catalog
        ▲
        │ SQL (console, JDBC/ODBC, API, SDK)
   Analysts, QuickSight, apps
        │
        └──► query results written to an S3 results bucket
```

- **Serverless**: nothing to provision, scales automatically, queries run in parallel.
- **Pay per query**: about **$5 per TB of data scanned** (failed queries and DDL are free, canceled queries are charged for data scanned).
- **Data stays in S3**: Athena only reads it. Nothing is copied into a warehouse.
- Query results are stored in an **S3 bucket** you choose (the **query result location**).

## Supported Data Formats

| Format | Type | Notes |
|---|---|---|
| **CSV, TSV, JSON** | Row-based, text | Easy, but **expensive** to scan (reads everything) |
| **Avro** | Row-based, binary | Good for **schema evolution** |
| **Parquet** | **Columnar**, binary | **Best** for analytics: reads only needed columns, compressed |
| **ORC** | **Columnar**, binary | Similar to Parquet, optimized for Hive |
| **Apache logs, CloudTrail, ALB, VPC Flow Logs** | Logs | Via built-in SerDes / ready-made table templates |
| **Compression** | gzip, Snappy, LZO, ZSTD, bzip2 | Reduces the amount scanned |

## Tables and the Data Catalog

- A table in Athena is **only metadata** (location in S3, columns, format). The data is **not** moved.
- Metadata is stored in the **AWS Glue Data Catalog** (the same catalog used by **Glue**, **EMR**, **Redshift Spectrum** and **Lake Formation**).
- Create tables with `CREATE EXTERNAL TABLE ...` (Hive DDL), a **Glue crawler** (auto-discovers schema), or the console wizard.
- **Dropping** a table deletes only the **metadata**, not the S3 data.

## SerDe (Serializer / Deserializer)

**SerDe** is a library that tells a system **how to read and write a data format**: it **deserializes** raw bytes (a CSV line, a JSON document) into **rows and columns**, and **serializes** rows back into bytes. It comes from **Apache Hive**, and is used by Hive, EMR, Glue and Athena. The SerDe is what makes **schema-on-read** possible: the files stay raw in S3, and the SerDe interprets them at query time.

### SerDe in Athena

- Athena uses SerDes to read S3 files. You pick one in the table DDL with `ROW FORMAT SERDE '...'` (or `STORED AS PARQUET`, which picks the SerDe for you).
- Athena is **read-oriented**: it **deserializes** when querying. It only serializes when writing results (`CTAS`, `INSERT`, `UNLOAD`).

| Format | SerDe |
|---|---|
| **CSV / TSV** | `LazySimpleSerDe` (simple), `OpenCSVSerde` (handles **quotes** and **escapes**, all columns read as **strings**) |
| **JSON** | `OpenX JsonSerDe` (common), `Hive JsonSerDe` |
| **Parquet** | `ParquetHiveSerDe` |
| **ORC** | `OrcSerde` |
| **Avro** | `AvroSerDe` |
| **Text logs** (Apache, ALB, etc.) | `RegexSerDe` (parses lines with a **regex**), `Grok SerDe` |
| **CloudTrail** | `CloudTrailSerde` |

- Pick the **wrong SerDe** and queries return **nulls, shifted columns or errors**.
- **Custom** SerDes are not supported in Athena. Use a built-in one or **convert** the data (e.g. to Parquet with **CTAS**).

## Cost and Performance Optimization

The bill depends on **data scanned**, so reduce what each query reads:

| Technique | Why it helps |
|---|---|
| Use **columnar formats** (**Parquet / ORC**) | Reads only the **columns** the query needs. Up to ~**90%** cheaper than CSV. |
| **Compress** data | Less data scanned and transferred. |
| **Partition** data (e.g. `year=2026/month=11/day=27/`) | Queries filtering on partition keys read only **matching prefixes**. Use `MSCK REPAIR TABLE` or **partition projection** to register partitions. |
| **Bucket** data | Groups rows by a column to speed up joins/filters. |
| **Larger files** (128 MB+) | Avoid the **many small files** problem (overhead per file). |
| `SELECT` only **needed columns** | Avoid `SELECT *`. Use `LIMIT` carefully (it does not always reduce the scan). |
| **CTAS** (`CREATE TABLE AS SELECT`) | Convert data to Parquet/partitioned layout with a single query. |
| **Workgroups** with **per-query / per-workgroup data limits** | Cap cost, cancel runaway queries. |

## Key Features

### Workgroups

- Separate **teams, projects or workloads** (each with its own query settings, results location and **encryption**).
- Set **data usage controls** (limit data scanned per query or per period) and **CloudWatch alarms/SNS** notifications.
- Use **IAM** to restrict who can use which workgroup, and **cost allocation tags** to track spend.

### Federated Query

- Query **other data sources** (RDS, Aurora, DynamoDB, Redshift, DocumentDB, on-premises DBs, CloudWatch Logs, other clouds) **in place** with SQL, using **data source connectors**.
- Connectors run as **Lambda functions** (deployed from the **Serverless Application Repository**).
- Lets you **join** S3 data with relational/NoSQL data in a single query.

### Other Features

- **Athena for Apache Spark**: run interactive **Spark** (PySpark) notebooks, serverless.
- **UDFs** (user-defined functions) via **Lambda**, and **ML inference** with **SageMaker** models in SQL.
- **Query result reuse**: return cached results for identical queries (saves cost/time).
- **Prepared statements** and **named queries** for repeated SQL.
- **Iceberg, Hudi and Delta Lake** table support: **ACID** transactions, `INSERT/UPDATE/DELETE/MERGE`, **time travel** on S3 data.
- **Integrates with QuickSight** (dashboards), **Glue**, **Lake Formation**, **CloudTrail/CloudWatch**.

## Security

- **IAM** controls access to Athena **and** to the underlying S3 data (the user needs permission on both, plus the **Glue Data Catalog** and the **results bucket**).
- **Lake Formation** for **fine-grained** (database, table, **column, row, cell**) permissions.
- **Encryption**:
  - **At rest** in S3: **SSE-S3**, **SSE-KMS**, **CSE-KMS**. Also encrypts **query results** (set per workgroup).
  - **In transit**: **TLS**.
- **VPC endpoints (PrivateLink)** for private access to the Athena API.
- **CloudTrail** logs all Athena API calls (who ran which query).
- **Cross-account** access to S3 data via **bucket policies** plus IAM.

## Common Use Cases

- **Ad hoc analysis** of data in an S3 **data lake**.
- Querying **logs**: **ALB / ELB access logs**, **CloudTrail**, **VPC Flow Logs**, **S3 access logs**, **CloudFront** logs, **WAF** logs.
- **Business intelligence** with **QuickSight**.
- **Cost and usage analysis**: query **AWS Cost and Usage Reports (CUR)** with Athena.
- Run **queries on data** without setting up a cluster or ETL.

## Athena vs Other Analytics Services

| Service | Model | Use when |
|---|---|---|
| **Athena** | **Serverless** SQL on **S3**, pay per TB scanned | **Ad hoc**, infrequent queries, no setup, log analysis |
| **Redshift** | **Data warehouse** (cluster or serverless), data loaded in | **Complex, repeated** analytics, many joins, high concurrency, BI |
| **Redshift Spectrum** | Redshift querying **S3** | You already have Redshift and want to join S3 with warehouse tables |
| **EMR** | Managed **Hadoop/Spark** clusters | Heavy **processing**, custom frameworks |
| **Glue** | Serverless **ETL** + **Data Catalog** | Transform data and catalog it (Athena uses its catalog) |
| **OpenSearch** | **Search** and log analytics | Full-text search, real-time log dashboards |
| **QuickSight** | **BI** dashboards | Visualize Athena/Redshift results |

## Limits and Gotchas

- **Not** a transactional database (no OLTP). It is **OLAP**, query-based.
- **Query latency**: seconds to minutes, **not** for sub-second dashboards at scale.
- Default **query timeout** of **30 minutes** (DML), with soft limits on **concurrent queries** per account/Region.
- Many **small files** or **unpartitioned CSV/JSON** make queries **slow and expensive**.
- Athena needs a **results bucket**, and S3 costs (storage, GET requests) are billed separately.
- **Provisioned capacity** (DPUs) is available for **predictable, dedicated** query capacity (an alternative to on-demand per-TB pricing).

## Exam Tips (SAA)

- "**Serverless SQL** on **S3**", "**ad hoc** queries", "**no infrastructure**" → **Athena**.
- "**Analyze ALB / CloudTrail / VPC Flow / S3 access logs** stored in S3" → **Athena**.
- "**Reduce Athena cost**" → **Parquet/ORC (columnar)**, **compression**, **partitioning**, larger files.
- "Query **S3 and a relational/NoSQL database** in one SQL query" → **Athena Federated Query**.
- "**Control cost / limit data scanned** per team" → **Workgroups** with data usage limits.
- "**Catalog** of S3 data / schema discovery" → **Glue Data Catalog** and **crawler**.
- "**Column / row level** security on the data lake" → **Lake Formation**.
- "**Dashboards** on S3 data" → **Athena + QuickSight**.
- "**Complex, frequent** queries with heavy joins / data warehouse" → **Redshift** (not Athena).
- "Query S3 from an **existing Redshift** cluster" → **Redshift Spectrum**.

Related: [S3](../S3/README.md), [Redshift](../Redshift/README.md), [Kinesis](../Kinesis/README.md), [IAM](../IAM/README.md), [CloudTrail](../CloudTrail/README.md), [OpenSearch](../OpenSearch/README.md).
