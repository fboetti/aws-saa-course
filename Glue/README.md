# AWS Glue

**AWS Glue** is a fully managed, serverless **ETL (extract, transform, load)** and data integration service. It discovers, prepares, and moves data between sources so it's ready for analytics, ML, and application development.

## Core components

- **Glue Data Catalog**: A central metadata repository. It holds table definitions, schemas, and partitions. Athena, Redshift Spectrum, EMR, and Lake Formation all use it. It's Hive metastore compatible.
- **Crawlers**: These scan data stores such as S3, RDS, DynamoDB, and JDBC sources. They infer schemas and create or update tables in the Data Catalog. You can run them on a schedule.
- **ETL jobs**: These run Apache Spark (Python or Scala), Python shell, or Ray code. Glue provisions and scales the compute, and you pay only while jobs run (billed per DPU-hour).
- **Glue Studio**: A visual, drag-and-drop editor for building ETL jobs. It generates code for you.
- **Glue DataBrew**: A no-code visual tool for data cleaning and normalization, with 250+ prebuilt transformations.
- **Glue Workflows and Triggers**: These orchestrate multi-step pipelines. Triggers can be scheduled, on-demand, or event-based.
- **Glue Data Quality**: Defines rules (DQDL) to validate data.
- **Glue Schema Registry**: Enforces and versions schemas for streaming data (Kafka, Kinesis).
- **Job bookmarks**: Track already-processed data so jobs handle only new data on each run.

## Typical flow

1. A crawler scans raw data in S3 and populates the Data Catalog.
2. A Glue job reads the cataloged data, transforms it (clean, join, convert to Parquet or ORC, partition), and writes it to a target such as S3 or Redshift.
3. Athena, Redshift Spectrum, or QuickSight query the result.

## Key features

- **Serverless**: No infrastructure to manage.
- **Streaming ETL**: Reads from Kinesis, Kafka, or MSK using Spark Structured Streaming.
- **DynamicFrame**: A Glue abstraction over Spark DataFrames that handles messy or schema-inconsistent data.
- **Connectors**: Built-in support for S3, RDS, Redshift, DynamoDB, JDBC, MongoDB, Snowflake, and more.
- **Security**: IAM roles, KMS encryption, VPC connections, and Lake Formation integration.

## Exam tips (SAA)

- If a question asks for a **serverless ETL** service, the answer is usually **Glue**. If it asks for a managed Hadoop/Spark cluster you control, the answer is EMR.
- **Convert CSV or JSON to Parquet or ORC** to cut Athena query cost and improve performance. Glue is the standard answer.
- **Data Catalog** is the metadata layer for a data lake. Athena queries need table definitions, and Glue provides them.
- **Crawlers** are the answer for automatic schema discovery.
- **Job bookmarks** are the answer for incremental processing, so you don't reprocess old data.
- Glue is not for real-time sub-second processing. Use Kinesis or Lambda for that. Glue streaming is micro-batch.
- Glue jobs run in a **VPC** through connections. S3 access from a private subnet needs a VPC endpoint.
- Glue works with **Lake Formation** for fine-grained access control on the data lake.

## Comparison

| Need | Service |
|---|---|
| Serverless ETL and catalog | **Glue** |
| Full control of Spark/Hadoop clusters | EMR |
| Ad hoc SQL on S3 | Athena (uses the Glue Catalog) |
| Data warehouse | Redshift |
| Simple event-driven transforms | Lambda |
