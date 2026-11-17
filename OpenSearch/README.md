# Amazon OpenSearch Service

**Amazon OpenSearch Service** is a managed service for deploying, operating and scaling **OpenSearch** (the open-source fork of **Elasticsearch** and Kibana) clusters. It is used for **search**, **log analytics**, **real-time application monitoring** and **clickstream analytics**. It is the successor of Amazon Elasticsearch Service.

## Purpose

- **Full-text search** with relevance scoring, fuzzy matching, autocomplete, faceting (e.g. product search, site search).
- **Log and event analytics**: ingest logs, metrics and traces, then search and visualize them.
- **Partial matching and complex queries** on any field (unlike DynamoDB, which is key-based).
- **Vector search / k-NN** for semantic search and generative-AI (RAG) workloads.
- Visualization through **OpenSearch Dashboards** (the Kibana equivalent).

## Core Concepts

| Concept | What it is |
|---|---|
| **Domain** | An OpenSearch cluster: the nodes, storage and settings you configure. |
| **Index** | A collection of **documents** (JSON), similar to a table. |
| **Shard** | An index is split into **primary shards**, each with optional **replica shards** for HA and read throughput. |
| **Data nodes** | Store data and run queries. |
| **Dedicated master (cluster manager) nodes** | Manage cluster state; recommended **3** for production. |
| **UltraWarm / Cold storage** | Cheaper tiers for infrequently accessed data, backed by **S3**. |

## Deployment Options

| Option | Notes |
|---|---|
| **Managed cluster** | You choose instance types, node count, EBS storage. Runs in **1–3 AZs**. |
| **OpenSearch Serverless** | No clusters to manage: capacity scales automatically (measured in **OCUs**). Collections of type search, time series or vector search. |

## High Availability and Scaling

- **Multi-AZ** (up to 3 AZs) with replica shards placed in different AZs; **Multi-AZ with Standby** for 99.99% availability.
- Scale vertically (bigger instances) or horizontally (more data nodes); storage on **EBS** (or instance store for some types).
- **Automated snapshots** to S3 (hourly, kept 14 days); manual snapshots for longer retention.

## Data Ingestion

```
Kinesis Data Streams ─► Kinesis Data Firehose ─► OpenSearch
CloudWatch Logs ─► subscription filter ─► Lambda / Firehose ─► OpenSearch
DynamoDB Streams ─► Lambda ─► OpenSearch
S3 / other sources ─► OpenSearch Ingestion (managed Data Prepper) ─► OpenSearch
Logstash / Beats / OpenSearch API ─► OpenSearch
```

- **Firehose** can deliver directly to OpenSearch, with S3 as a backup for failed or all documents.
- **OpenSearch Ingestion** is the managed, serverless pipeline (based on Data Prepper).
- **Zero-ETL integrations** exist from DynamoDB and others.

## Security

- **IAM** identity-based and **resource-based (domain access) policies**; request signing with SigV4.
- **Fine-grained access control**: index-, document- and field-level security, with an internal user database or IAM / SAML / **Cognito** (for Dashboards login).
- **Encryption at rest** (KMS) and **in transit** (TLS); node-to-node encryption.
- **Network**: deploy in a **VPC** (private, accessed via security groups, VPN or bastion) or use a **public endpoint**. You cannot switch between VPC and public later.

## Common Architecture Patterns

- **DynamoDB + OpenSearch**: DynamoDB is the system of record (fast key lookups); a **DynamoDB Stream → Lambda** keeps OpenSearch in sync for **search**. Search first, then fetch the item by key.
- **Log analytics**: CloudWatch Logs → Firehose / Lambda → OpenSearch → Dashboards.
- **Streaming**: Kinesis Data Streams → Firehose → OpenSearch (near real-time).
- **Generative AI**: documents embedded with **Bedrock** and stored as vectors in OpenSearch for retrieval (RAG).

## OpenSearch vs Other Services

| Need | Service |
|---|---|
| Free-text search, partial matches, log analytics | **OpenSearch** |
| Key-value lookups, single-digit ms at any scale | **DynamoDB** |
| SQL analytics on a data warehouse | **Redshift** |
| Ad-hoc SQL on S3 data | **Athena** |
| Relational OLTP | **RDS / Aurora** |
| Simple log search in AWS | **CloudWatch Logs Insights** |

## Exam Tips

- "**Search** / full-text search / **partial matching** / analytics on logs" → **OpenSearch Service**.
- "Search on top of **DynamoDB** data" → **DynamoDB Streams + Lambda → OpenSearch**.
- "Load streaming data into OpenSearch" → **Kinesis Data Firehose** (or Data Streams + Lambda).
- "Analyze **CloudWatch Logs** in near real time with Kibana-like dashboards" → CloudWatch Logs subscription → OpenSearch.
- "No cluster management" → **OpenSearch Serverless**.
- Not a database for transactions: it is a **search and analytics engine**, usually fed from another source of truth.
- Cluster is **not serverless by default**: you size instances and shards, and it runs in a **VPC or public endpoint**.

Related: [S3](../S3/README.md), [IAM](../IAM/README.md), [VPC](../VPC/README.md).
