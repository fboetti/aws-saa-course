# Amazon MemoryDB

**Amazon MemoryDB** (formerly *MemoryDB for Redis*) is a **durable, in-memory database** that is compatible with **Valkey** and **Redis OSS**. Unlike a cache, it is meant to be used as a **primary database**: it keeps the whole dataset in memory for **microsecond reads** and **single-digit millisecond writes**, and stores every write in a **Multi-AZ transaction log** so no data is lost.

```
App ──► MemoryDB primary ──► write to Multi-AZ transaction log (durable) ──► ack
    └─► reads from primary / replicas (in memory, microsecond latency)
```

## Key Features

- **Redis / Valkey compatible**: use the same clients, commands and data structures (strings, lists, sets, **sorted sets**, hashes, streams, geospatial, pub/sub).
- **Durability**: data is written to a **Multi-AZ transaction log** before the write is acknowledged, so nothing is lost on failover or node restart.
- **Multi-AZ** with **automatic failover**: a replica is promoted if the primary fails, with no data loss.
- **Sharding**: data is partitioned across up to **500 shards**, each with a primary and up to **5 replicas**, to scale reads and writes.
- **Snapshots**: automated and manual snapshots stored in **S3**, restorable into a new cluster.
- **Vector search**: store and query vectors, for example for semantic search or generative AI workloads.
- Fully managed: provisioning, patching, failure detection and recovery.

## Architecture

| Component | Notes |
|---|---|
| **Cluster** | One or more **shards**. |
| **Shard** | One **primary** (reads and writes) and up to 5 **replicas** (reads, failover targets). |
| **Node** | An in-memory instance of the chosen node type. |
| **Multi-AZ transaction log** | Durable log that all writes go through. Replicas and restarted nodes recover from it. |

## Security

- Runs **inside a VPC**, controlled by **security groups** (default port **6379**).
- **Encryption at rest** (KMS) and **in transit** (TLS).
- **ACLs** (users and access strings) and **IAM authentication**.
- **IAM** policies control the **management API** (create, modify and delete clusters).

## Monitoring

- **CloudWatch** metrics such as `CPUUtilization`, `DatabaseMemoryUsagePercentage`, `Evictions`, `ReplicationLag`, `CurrConnections`.

## MemoryDB vs ElastiCache

| | **MemoryDB** | **ElastiCache (Redis / Valkey)** |
|---|---|---|
| Purpose | **Primary database** | **Cache** (can also be a data store) |
| Durability | **Multi-AZ transaction log**, no data loss | Optional snapshots, **data can be lost** on failover |
| Write latency | Single-digit ms (log write) | Lower (in-memory only) |
| Read latency | Microseconds | Microseconds |
| Failover | Automatic, **no data loss** | Automatic, may lose recent writes |
| Cost | Higher | Lower |
| Memcached support | No | Yes |

## MemoryDB vs Other Services

| | **MemoryDB** | **DynamoDB** | **DAX** |
|---|---|---|---|
| Type | In-memory, Redis-compatible DB | Serverless NoSQL (disk, SSD) | In-memory cache for DynamoDB |
| Latency | Microsecond reads | Single-digit ms | Microsecond reads |
| Best for | Redis API, rich data structures, durability | Key-value at any scale | Accelerating DynamoDB reads |

## Common Use Cases

- **Microservices and web apps** that need a fast **durable** store using the Redis API.
- **Gaming**: leaderboards (sorted sets), player sessions and state.
- **Real-time** applications: streaming, messaging, IoT, financial data.
- **Session store** and shopping carts that must **not be lost**.
- **Vector search** for generative AI and recommendations.

## Exam Tips

- **Redis-compatible, durable, in-memory primary database** → **MemoryDB**.
- **Redis cache to offload a database, data loss acceptable** → **ElastiCache**.
- **Microsecond reads and no data loss on failover** → **MemoryDB** (Multi-AZ transaction log).
- **Cache for DynamoDB with no code changes** → **DAX**.
- **Simple multi-threaded cache** → ElastiCache for **Memcached** (MemoryDB does not support it).
- **MemoryDB is not publicly accessible** → clients must run in the same VPC (or connected to it).
