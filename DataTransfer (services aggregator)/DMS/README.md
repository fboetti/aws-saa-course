# AWS DMS (Database Migration Service)

**AWS Database Migration Service (DMS)** is a managed service to **migrate databases to AWS** quickly and securely. The **source database stays operational** during the migration, minimizing downtime. DMS can also be used for **continuous replication** after (or instead of) a one-time migration.

## How It Works

```
Source DB ──► Source Endpoint ──► Replication Instance (EC2, runs the task) ──► Target Endpoint ──► Target DB
```

| Component | Description |
|---|---|
| **Replication instance** | An EC2 instance managed by DMS that runs the migration tasks. Pick the size based on data volume and the number of tasks. Can be **Multi-AZ** for high availability |
| **Endpoints** | Connection details (host, credentials) for the source and target |
| **Replication task** | Defines what to migrate (tables, schemas, filters, transformations) and the migration type |
| **DMS Serverless** | Automatically provisions and scales capacity, so you don't manage the replication instance |

## Migration Types

| Type | Description |
|---|---|
| **Full load** | One-time copy of the existing data |
| **Full load + CDC** | Copy existing data, then keep applying ongoing changes (**Change Data Capture**). Near-zero downtime |
| **CDC only** | Replicate only ongoing changes (data was already loaded another way) |

## Supported Sources and Targets

- **Sources**: Oracle, SQL Server, MySQL, MariaDB, PostgreSQL, MongoDB, SAP ASE, Db2, Amazon RDS/Aurora, S3, DocumentDB, and more (on-prem, EC2, or RDS).
- **Targets**: RDS, Aurora, Redshift, DynamoDB, S3, DocumentDB, Neptune, OpenSearch, Kinesis Data Streams, Kafka (MSK), and more.

### Homogeneous vs Heterogeneous

| Type | Example | Tools |
|---|---|---|
| **Homogeneous** (same engine) | Oracle → RDS Oracle, MySQL → Aurora MySQL | DMS alone (or native tools) |
| **Heterogeneous** (different engine) | Oracle → Aurora PostgreSQL, SQL Server → MySQL | **AWS SCT** (Schema Conversion Tool) converts schema and code, **then DMS** moves the data |

> **DMS moves the data; it does not convert the schema.** For different engines, use **SCT** first (tables, indexes, stored procedures, functions). DMS Schema Conversion is the managed version of this capability.
> **SCT is not needed** for homogeneous migrations or when the target is S3 / DynamoDB-style data stores with no schema conversion.

## Key Features

- **Minimal downtime** with CDC: the source stays live while the target catches up, then you cut over.
- **Multi-AZ replication instance** for failover (data is synced to a standby).
- **Continuous replication** for DR, reporting, or feeding a data lake (e.g. RDS → S3, DB → Kinesis).
- **Table mappings and transformations**: filter, rename, or drop columns/tables.
- **Data validation** to confirm source and target match.
- **Encryption** in transit (SSL/TLS) and at rest (KMS).
- **Monitoring** with CloudWatch, plus CloudTrail for API calls.
- Pricing: pay for the **replication instance hours** (or DCUs for Serverless) and storage. The migration itself has no license fee, and some DMS usage is free for limited periods.

## Connectivity

- Source and target can be on-prem, EC2, or RDS. The replication instance needs network access to both.
- Use **Direct Connect** or **Site-to-Site VPN** for on-prem sources, and **security groups** and VPC placement to restrict access.
- Either the source **or** the target must be on AWS (DMS doesn't migrate on-prem to on-prem).

## DMS vs Other Services

| Need | Use |
|---|---|
| Migrate a **database** with minimal downtime | **DMS** |
| **Convert schema** between different engines | **SCT** (+ DMS for data) |
| Bulk **files** from NFS/SMB to S3/EFS | [DataSync](../DataSync/README.md) |
| Huge offline data movement | [Snow Family](../SnowFamily/README.md) |
| Track migration progress across many servers/apps | [Migration Hub](../../MigrationHub/README.md) |
| Restore from backup into the same engine | Native tools / RDS snapshots |

## Exam Tips

- "Migrate a **database** to AWS with **minimal downtime**, source stays running" → **DMS** (full load + **CDC**).
- "**Different** database engines" → **SCT + DMS**. "**Same** engine" → DMS only.
- "**Continuous replication**" to another DB, S3, or Kinesis → DMS with CDC.
- "**High availability** for the migration" → **Multi-AZ** replication instance.
- Runs on a **replication instance (EC2)**, so size it appropriately, or use **DMS Serverless**.
- Always one side must be **on AWS**.
- DMS is for **databases**; **DataSync** is for **files**.

Related: [DataSync](../DataSync/README.md), [Snow Family](../SnowFamily/README.md), [Migration Hub](../../MigrationHub/README.md), [Transfer Family](../TransferFamily/README.md).
