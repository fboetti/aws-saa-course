# Amazon ElastiCache

**Amazon ElastiCache** is a managed **in-memory data store and cache** service. It provides sub-millisecond (microsecond for reads in some cases) latency and is used to **speed up applications and reduce load on databases**. AWS handles provisioning, patching, failure detection, recovery and backups.

```
App ──► ElastiCache (hit)  ──► response
    └─► miss ──► RDS / DynamoDB ──► write result to cache ──► response
```

## Engines

| Engine | Notes |
|---|---|
| **Valkey** | Open-source, Redis-compatible fork backed by AWS and the Linux Foundation. Usually the cheapest option. |
| **Redis OSS** | Rich data structures, persistence, replication, Multi-AZ, pub/sub. |
| **Memcached** | Simple key-value cache, multi-threaded, no persistence or replication. |

### Redis / Valkey vs Memcached

| | **Redis / Valkey** | **Memcached** |
|---|---|---|
| Data types | Strings, lists, sets, **sorted sets**, hashes, streams, geospatial | Strings only (simple key-value) |
| High availability | **Multi-AZ** with automatic failover | No |
| Replication | **Read replicas** | No |
| Persistence | **Yes** (snapshots / AOF, backup and restore) | **No** |
| Sharding | **Cluster mode** (up to 500 shards) | **Yes** (nodes, client-side partitioning) |
| Threading | Mostly single-threaded per node | **Multi-threaded** |
| Pub/sub | Yes | No |
| Auth | **Redis AUTH**, **IAM auth**, ACLs | **SASL** |

## Deployment Options

| Option | Notes |
|---|---|
| **Node-based cluster** | You choose node type and count. Supports **Multi-AZ**, replicas and reserved nodes. |
| **Serverless** | No capacity planning. Scales automatically, billed by data stored and ECPUs used. |

## Redis / Valkey Cluster Modes

| Mode | Behavior |
|---|---|
| **Cluster mode disabled** | **One shard**: 1 primary and up to **5 replicas**. Replicas scale reads, and the data must fit in one node. |
| **Cluster mode enabled** | **Multiple shards** (data is partitioned across them), each with a primary and replicas. Scales both reads and writes. |

- **Multi-AZ** with **automatic failover**: a replica is promoted if the primary fails.
- **Global Datastore**: cross-Region replication for low-latency reads and disaster recovery.

## Caching Strategies

| Strategy | How it works | Trade-off |
|---|---|---|
| **Lazy loading (cache-aside)** | Read from cache. On a miss, read from the DB and write to the cache. | Only requested data is cached, but a miss costs 3 trips and data can go **stale**. |
| **Write-through** | Write to the DB and the cache together. | Cache is never stale, but writes are slower and unread data fills the cache. |
| **TTL** | Each key expires after a time. | Limits staleness. Combine with the strategies above. |

- Cache **evictions** (memory full) and **TTL** keep memory under control. A high eviction count means the cache is too small, so scale up or out.

## Common Use Cases

- **Database caching**: offload frequent, read-heavy queries from RDS / Aurora / DynamoDB.
- **Session store**: keep user sessions in a central cache so the app stays **stateless** behind a load balancer.
- **Leaderboards and counters**: Redis **sorted sets** and atomic increments.
- **Real-time analytics, rate limiting, pub/sub messaging, job queues**.
- **Gaming, geospatial** queries (Redis geo commands).

## Security

- Runs **inside a VPC**. It is not publicly accessible, and access is controlled with **security groups** (port **6379** for Redis, **11211** for Memcached).
- **Encryption at rest** (KMS) and **in transit** (TLS).
- **Redis AUTH** (password / token), **RBAC / ACLs** and **IAM authentication** for Redis / Valkey. **SASL** for Memcached.
- **IAM** policies control the **management API** (create, modify and delete clusters). Access to the data itself uses AUTH / ACLs, or IAM authentication on Redis / Valkey.

## Backup and Monitoring

- **Redis / Valkey**: automated daily snapshots and manual snapshots, stored in S3. Restore into a new cluster. **Memcached has no backups.**
- **CloudWatch** metrics: `CPUUtilization`, `EngineCPUUtilization`, `DatabaseMemoryUsagePercentage`, `Evictions`, `CacheHits` / `CacheMisses`, `ReplicationLag`, `CurrConnections`.

## ElastiCache vs Similar Services

| | **ElastiCache** | **DynamoDB DAX** | **MemoryDB** |
|---|---|---|---|
| Purpose | General cache / data store | Cache **for DynamoDB only** | **Durable** primary database (Redis-compatible) |
| Durability | Optional (Redis snapshots) | Cache only | **Multi-AZ transaction log** |
| Code changes | Application manages cache logic | **None** (DAX-compatible SDK client) | Use as a database |

## Exam Tips

- **Reduce database load, speed up reads, in-memory cache** → **ElastiCache**.
- **Complex data types, persistence, replication, Multi-AZ, backups, pub/sub, sorted sets / leaderboards** → **Redis / Valkey**.
- **Simple, multi-threaded, horizontally scaled cache with no persistence** → **Memcached**.
- **Stateless app with shared sessions** → store sessions in **ElastiCache** (or DynamoDB).
- **Caching for DynamoDB with no application changes** → **DAX**, not ElastiCache.
- **Redis-compatible, durable primary database** → **MemoryDB**.
- **Stale data** → use **write-through** and/or a **TTL**.
- **Read-heavy RDS workload** → add a **cache** (or read replicas). The cache is faster and cheaper per read.
- **Cache is not publicly accessible** → the app must run in the same VPC (or connected to it).
