# Amazon QLDB (Quantum Ledger Database)

**Amazon QLDB** is a fully managed **ledger database** that provides a **transparent, immutable and cryptographically verifiable** transaction log owned by a central trusted authority. It tracks every change to application data and keeps a complete, verifiable history.

> **Note:** AWS ended support for QLDB on **July 31, 2025**. It can no longer be used, and AWS recommends migrating ledger workloads to **Amazon Aurora PostgreSQL**. It still appears in older SAA course material and exam guides, so the concepts are worth knowing.

## Purpose

- Keep an **authoritative history** of changes that can never be altered or deleted.
- Prove with **cryptography** that data has not been tampered with.
- Typical use cases: **financial transactions** (bank ledgers, credits and debits), **supply chain** tracking, **insurance claims**, **vehicle registration** history, **HR records**.

## Core Concepts

| Concept | What it is |
|---|---|
| **Ledger** | The database. Contains tables and a **journal**. |
| **Journal** | **Append-only** log of every committed transaction. Entries are **never modified or deleted**. |
| **Hash chain** | Each journal block is hashed and linked to the previous one (**SHA-256**), so any change is detectable. |
| **Digest** | A hash representing the entire ledger history at a point in time. Used to **verify** a document revision. |
| **Tables / documents** | Data stored as **Amazon Ion** documents (a superset of JSON). Each change creates a new **revision**. |
| **Indexed storage** | Current and historical data you query with **PartiQL**. |

## Key Features

- **Immutable**: no update or delete of history. Updates append a new revision.
- **Cryptographically verifiable**: request a digest and a proof, then verify that a revision is intact.
- **Serverless**: automatic scaling, **no capacity to provision**.
- **ACID transactions** with **strong consistency** (serializable isolation).
- **SQL-like queries** with **PartiQL**.
- **Export** the journal to **S3** or **stream** it to **Kinesis Data Streams** for analytics and integration.
- **Highly available**: data replicated across multiple AZs in a Region.
- Encrypted at rest and in transit; access via **IAM**.

## QLDB vs Amazon Managed Blockchain

| | **QLDB** | **Managed Blockchain** |
|---|---|---|
| Ledger owner | **Central, trusted authority** | **Decentralized**: multiple parties |
| Consensus | Not needed (single owner) | Required (Hyperledger Fabric, Ethereum) |
| Performance | Higher throughput, simpler | Slower, more complex |
| Use when | One organization needs an **immutable audit log** | Multiple untrusting parties need **shared** records |

## QLDB vs Other Databases

| Need | Service |
|---|---|
| Immutable, verifiable history (centralized) | **QLDB** (now: Aurora PostgreSQL) |
| Decentralized, multi-party ledger | **Managed Blockchain** |
| General relational OLTP | **RDS / Aurora** |
| Key-value, millisecond latency | **DynamoDB** |
| Search / log analytics | **OpenSearch** |

## Exam Tips

- "**Immutable**, append-only, **cryptographically verifiable** ledger / audit trail, **central authority**" → **QLDB**.
- "**Decentralized**, multiple parties, no central authority" → **Managed Blockchain**, not QLDB.
- QLDB is **serverless**, **ACID**, and uses **PartiQL**; the journal can be exported to **S3** or streamed to **Kinesis**.
- Do not use a normal database or CloudTrail when the question stresses **tamper-proof, verifiable data history** for an application.

Related: [IAM](../IAM/README.md), [S3](../S3/README.md), [OpenSearch](../OpenSearch/README.md).
