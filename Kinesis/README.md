# Amazon Kinesis

**Amazon Kinesis** is a family of managed services for **collecting, processing and analyzing real-time streaming data** (application logs, clickstreams, IoT telemetry, metrics, video).

```
Producers ──► [ Kinesis Data Streams ] ──► Consumers (Lambda / Flink / KCL apps)
                                      └──► Firehose ──► S3 / Redshift / OpenSearch
```

## The Four Services

| Service | Purpose |
|---|---|
| **Kinesis Data Streams (KDS)** | Low-latency ingest of streaming data at scale, with custom consumers and replay. |
| **Amazon Data Firehose** (formerly Kinesis Data Firehose) | Fully managed delivery of streaming data to destinations, with no consumer code. |
| **Managed Service for Apache Flink** (formerly Kinesis Data Analytics) | Real-time analytics with Apache Flink (or legacy SQL). |
| **Kinesis Video Streams** | Ingest and process video, audio and other time-serialized device data. |

## Kinesis Data Streams (KDS)

- Data is split across **shards**. Each shard provides up to **1 MB/s or 1,000 records/s** in, and **2 MB/s** out.
- Each record has a **partition key**, which is hashed to pick the shard. A poorly distributed key causes **hot shards**.
- Records are **ordered per shard**. Maximum record size is **1 MB**.
- **Retention**: 24 hours by default, extendable up to **365 days**. Records can be **replayed**.
- Multiple consumers can read the same data (unlike SQS).

### Capacity Modes

| Mode | Notes |
|---|---|
| **Provisioned** | You choose the shard count and **split / merge** shards to resize. |
| **On-demand** | Scales automatically, with no shard management. Pay per throughput. |

### Producers and Consumers

| Producers | Consumers |
|---|---|
| **AWS SDK** (`PutRecord`, `PutRecords`) | **Lambda** (event source mapping) |
| **KPL** (Kinesis Producer Library): batching, retries, aggregation | **KCL** (Kinesis Client Library): checkpointing in DynamoDB, shard coordination |
| **Kinesis Agent** (installed on servers, tails log files) | **Managed Service for Apache Flink** |
| Third-party tools and AWS services (e.g. CloudWatch Logs subscription, IoT Core) | **Firehose** |

### Kinesis Producer Library (KPL)

The KPL is a library that makes high-throughput writing to a stream more efficient than calling the SDK directly. It is **built for Java**: it runs a native C++ child process that the Java API wraps, so it is **hard to use if you are not familiar with Java** (other languages have to talk to that process through a more awkward interface, and the SDK is usually the easier choice).

- **Aggregation**: packs many small user records into one Kinesis record to use each shard's 1,000 records/s limit better.
- **Batching**: sends several records in one `PutRecords` call.
- **Automatic retries** on failed writes, plus CloudWatch metrics.
- **Adds latency**: records wait in a buffer (`RecordMaxBufferedTime`, 100 ms by default). If you need the lowest latency, use the SDK instead.
- **Consumers must deaggregate**: use the **KCL** (which handles it) or the KPL deaggregation module. A plain SDK consumer sees the packed records.

### Shared vs Enhanced Fan-Out

| | **Shared (classic)** | **Enhanced fan-out (EFO)** |
|---|---|---|
| Throughput | **2 MB/s per shard**, shared by all consumers | **2 MB/s per shard per consumer** |
| Model | Pull (`GetRecords`) | **Push** over HTTP/2 (`SubscribeToShard`) |
| Latency | ~200 ms | ~70 ms |
| Use when | Few consumers, cost-sensitive | Many consumers needing full throughput |

## Amazon Data Firehose

Firehose is similar to Data Streams (both ingest streaming data from producers), but it is **simpler and less customizable**. It trades control for convenience: there are no shards to size, no consumers to write and no scaling to manage. You pick a destination and AWS delivers the data. In exchange, you lose custom consumers, replay, per-record ordering control and storage, and you accept near-real-time latency because of buffering.

- **Serverless** and fully managed. It loads streaming data into destinations without writing consumer code.
- **Destinations**: **S3**, **Redshift** (via an S3 `COPY`), **OpenSearch**, **Splunk**, HTTP endpoints, and partners (Datadog, MongoDB, New Relic and others).
- **Near-real-time**: it **buffers** by size or time (a minimum of about 60 seconds, with a zero-buffer option available for some destinations).
- Optional **Lambda transformation**, **format conversion** (JSON to **Parquet / ORC**) and **compression** (GZIP, Snappy and others).
- Can use a **Kinesis Data Stream** as its source, or accept direct `PutRecord` calls.
- **No storage and no replay**. Failed records can be backed up to an S3 bucket.

## Managed Service for Apache Flink

- Runs **real-time analytics** on streams: filtering, aggregations, sliding and tumbling windows, anomaly detection.
- Reads from **KDS** or **MSK**. Writes to KDS, Firehose, S3 and others.
- Fully managed: it provisions the compute and handles scaling and checkpointing.
- Older SQL-based applications are legacy. Use **Flink** for new work.

## Kinesis Video Streams

- Ingests **video, audio and other time-serialized data** from cameras and devices.
- Used for **ML / analytics** (for example with **Rekognition Video**), **playback** (HLS / DASH) and **WebRTC** two-way streaming.
- Data is stored and encrypted, with configurable retention.

## KDS vs Firehose

| | **Data Streams** | **Firehose** |
|---|---|---|
| Management | You manage shards (or use on-demand) | Fully managed |
| Latency | ~200 ms (~70 ms with enhanced fan-out) | Near-real-time (buffered) |
| Custom consumers | **Yes** | **No** (delivers to destinations) |
| Replay | **Yes** | **No** |
| Storage | 1 to 365 days | None |
| Scaling | Manual (provisioned) or automatic (on-demand) | Automatic |

## KDS vs SQS vs SNS

| | **Kinesis Data Streams** | **SQS** | **SNS** |
|---|---|---|---|
| Model | Stream | Queue | Pub/sub |
| Multiple consumers on same data | **Yes** | No (one consumer per message) | Yes (fan-out) |
| Ordering | Per shard | FIFO queues only | FIFO topics only |
| Replay | **Yes** | No (deleted after processing) | No |
| Retention | Up to 365 days | Up to 14 days | None |
| Scaling | Shards | Automatic | Automatic |

## Security

- **Encryption in transit** (HTTPS) and **at rest** (**KMS**, server-side encryption you enable on the stream).
- **IAM** policies control access to streams and consumers.
- **VPC endpoints** (interface) for private access without traversing the internet.
- **CloudTrail** logs API calls.

## Common Architecture Patterns

- **Real-time log / clickstream ingestion**: `Producers → KDS → Lambda / Flink`, with a Firehose branch to S3 for long-term storage.
- **Streaming ETL to a data lake**: `KDS → Firehose (Lambda transform, Parquet) → S3 → Athena`.
- **Search and observability**: `CloudWatch Logs → Firehose → OpenSearch`.
- **IoT telemetry**: `IoT Core → KDS → Flink → dashboards / alerts`.

## Useful CloudWatch Metrics

| Metric | Meaning |
|---|---|
| `WriteProvisionedThroughputExceeded` | Producers are throttled (too much data or a hot shard). |
| `ReadProvisionedThroughputExceeded` | Consumers are throttled. |
| `GetRecords.IteratorAgeMilliseconds` | How far consumers lag behind. A growing value means consumers are falling behind. |
| `IncomingBytes` / `IncomingRecords` | Producer volume. |

## Exam Tips

- **Real-time streaming, custom processing, ordering, replay** → **Data Streams**.
- **Load streaming data into S3 / Redshift / OpenSearch with minimal management** → **Firehose**.
- **Real-time SQL or Flink analytics on streams** → **Managed Service for Apache Flink**.
- **Video streams from cameras** → **Kinesis Video Streams**.
- **Hot shard** → choose a better partition key, or split the shard.
- **`ProvisionedThroughputExceededException`** → add shards (or use on-demand), spread the partition key more evenly, and use **exponential backoff** (see [API/exponential-backoff.md](../API/exponential-backoff.md)).
- **Many consumers needing full throughput each** → **enhanced fan-out**.
- **Ordered, replayable, multi-consumer** → **KDS**. **Decoupling and work queues** → **SQS**.
- **Firehose is near-real-time, not real-time**, because of its buffer.
- **Order within a shard is guaranteed**. To keep related records in order, use the **same partition key**.
- **Lambda consuming KDS** processes **one batch per shard** at a time by default. A failing batch **blocks the shard** until it succeeds or expires, so configure retries, bisect-on-error and an **on-failure destination**.
