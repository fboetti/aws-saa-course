# Amazon S3 — Theoretical Overview

Notes on S3 buckets and their properties, following the course video
([freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=18393s) — S3 section starts at **5:06:32**).

## What is S3?

**Amazon Simple Storage Service (S3)** is AWS's object storage service. You store data as **objects** inside **buckets** — think of a bucket as a top-level container (like a filesystem root) and objects as files living under a *key* (their full path/name inside the bucket).

Key characteristics:

- **Object storage, not file storage**: there is no real directory tree. Keys are flat strings like `images/2026/photo.jpg`; the `/` characters just *look* like folders in the console.
- **Regional service**: a bucket is created in a specific AWS region and its name must be unique **globally** across all AWS accounts.
- **Virtually unlimited scale**: no maximum bucket size; you pay for what you store plus requests and data transfer.
- **Strong read-after-write consistency**: since December 2020 every `PUT`, overwrite, `DELETE` and `LIST` is immediately visible to subsequent reads — see [Data Consistency](data-consistency.md).
- **Designed for 99.999999999% (eleven nines) durability** and 99.99% availability (Standard), because objects are stored redundantly across multiple devices in a minimum of three Availability Zones.

## Buckets and Objects

| Concept | Details |
|---|---|
| **Bucket** | Container for objects. Must follow strict, **globally unique** naming rules (they become part of a public DNS name — see [Bucket Naming Rules](#bucket-naming-rules)). Cannot be renamed after creation. |
| **Object** | The unit of storage: data + metadata + key. Max object size is **5 TB** in the exam material (raised to **50 TB** in December 2025). Objects are the **data payload**; buckets are the infrastructure around them — see the [Object Overview](objects.md). |
| **Key** | The full path/name of the object, e.g. `photos/2026/cat.png` (max 1,024 bytes). Keys can contain slashes to simulate folders, but S3 has no real hierarchy. |
| **Version ID** | If versioning is enabled, every new write gets a unique version ID; objects that existed before versioning was enabled have version ID `null`. |
| **Metadata** | Custom key/value pairs set on upload, plus system metadata (content type, ETag, last modified). |

## Bucket Naming Rules

Because every object is addressable with a URL (`https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>`), the bucket name is part of a public DNS name — so it must be **unique across all AWS accounts and all regions**, and it must be DNS-compatible.

The full rules (allowed characters, reserved prefixes/suffixes, IP-address and adjacent-dot restrictions, examples) are in a dedicated document: **[Bucket Naming Rules](bucket-naming-rules.md)**.

## Bucket Types

For the exam, two bucket types matter:

- **General purpose buckets** — the original type, with a *flat* namespace. What the console shows as "folders" are just key prefixes: a folder you create is a real **0-byte object** whose key ends with `/`, and "moving" an object into a folder only changes its **key** (S3 implements it as copy + delete — no data relocation in a hierarchy, because there is none).
- **Directory buckets** — introduced in 2023 together with the **S3 Express One Zone** storage class: a true hierarchical (directory) namespace in a single AZ, with consistent single-digit millisecond latency.

Newer, specialized types also exist — **table buckets** (S3 Tables, Apache Iceberg tables for analytics, Dec 2024) and **vector buckets** (S3 Vectors, for embeddings/AI search, 2025) — but they postdate the SAA-C03 content.

The full comparison (names, supported features, endpoints) is in a dedicated document: **[Bucket Types](bucket-types.md)**.

## Storage Classes

S3 offers several storage classes that trade **storage price** against **availability, retrieval time and access cost** — durability is the same 11 nines everywhere. Standard, Intelligent-Tiering and Express One Zone suit frequently accessed data; the IA and Glacier classes are for data read rarely:

| Storage Class | Retrieval time | Use case |
|---|---|---|
| **S3 Standard** | milliseconds | Frequently accessed data, general purpose, ≥3 AZs |
| **S3 Intelligent-Tiering** | milliseconds | Unknown/changing access patterns — objects are auto-moved between tiers based on usage |
| **S3 Express One Zone** | single-digit milliseconds | High-performance, latency-sensitive workloads; requires a [directory bucket](bucket-types.md), single AZ |
| **S3 Standard-Infrequent Access (S3 Standard-IA)** | milliseconds | Less frequent access, but you need fast retrieval; lower storage, per-GB retrieval fee |
| **S3 One Zone-Infrequent Access** | milliseconds | Infrequently accessed, *recreatable* data stored in a single AZ (cheaper, less durable) |
| **S3 Glacier Instant Retrieval** | milliseconds | Long-lived archive with *occasional* immediate reads (e.g. quarterly media access); cheapest with instant access |
| **S3 Glacier Flexible Retrieval** (formerly Glacier) | minutes to hours | Archive with rarely needed retrieval; free bulk restores of 3–5 hours |
| **S3 Glacier Deep Archive** | hours | Longest-term retention, cheapest storage; 12–48 hours retrieval |

**Frequent vs. infrequent access** is decided by how often you expect to read the data; **retrieval time** is decided by how quickly you need it back. Request throughput needs no provisioning — S3 scales automatically per prefix. The only "provisioned capacity" in S3 is for **Glacier Flexible Retrieval expedited restores**, to guarantee they are accepted.

The full deep dive — durability, availability, data redundancy, retrieval times, throughput/scalability, use cases and pricing (storage, requests, retrieval fees, minimum durations) for **every** storage class — is in **[Storage Classes Deep Dive](storage-classes.md)**.

S3 Outposts has its own storage class.

## Bucket Properties / Features

### Versioning

- Keeps every version of every object; objects uploaded before versioning was enabled keep version ID `null`.
- States: **Unversioned** (default) → **Enabled** ↔ **Suspended**. Once enabled, a bucket can never return to unversioned — only be suspended, which stops creating new versions but keeps the existing ones.
- Deleting a versioned object just adds a **delete marker**; the object is recoverable by removing the marker or deleting a specific version.
- **MFA Delete** can be enabled so that changing versioning or permanently deleting versions requires an MFA device — extra protection against accidental/malicious deletion.
- Versioning is a prerequisite for **Cross-Region Replication (CRR)** and **Same-Region Replication (SRR)**.

### Replication

- **CRR**: copies objects to a bucket in another region (compliance, lower-latency access, disaster recovery).
- **SRR**: copies objects to another bucket in the same region (log aggregation, keeping prod/test in sync).
- Replication is **asynchronous** and applies only to **new** objects created after replication is configured (existing objects are not copied unless you run a backfill/batch replication).
- Requires versioning on both source and destination buckets.

The full deep dive — what is/isn't replicated, delete-marker rules, cross-account setup, Replication Time Control (RTC) and S3 Batch Replication — is in **[S3 Object Replication](replication.md)**.

### Lifecycle Rules

Rules that automate object transitions over time, e.g.:

- Move to **Standard-IA** after 30 days, **Glacier** after 90 days, **Deep Archive** after 365 days.
- **Expire (delete)** old versions or incomplete multipart uploads after N days.
- Works together with versioning (can clean up old versions and delete markers).

The full treatment — action types, minimum storage durations, the 128 KB transition default, billing vs execution delays, precedence rules and versioning interplay — is in **[S3 Lifecycle](lifecycle.md)**.

### Encryption

S3 supports four server-side options plus client-side encryption:

1. **SSE-S3** — Amazon S3 manages the keys; each object is encrypted with a unique key (AES-256), itself encrypted with a regularly rotated root key. Header `x-amz-server-side-encryption: AES256`. The default.
2. **SSE-KMS** — keys in AWS **KMS** (the AWS managed key `aws/s3` or your own **customer managed key**); adds a CloudTrail audit trail of key usage and per-key permissions. Header `aws:kms`. Enable **S3 Bucket Keys** to cut KMS request costs.
3. **DSSE-KMS** — *dual-layer* server-side encryption: S3 applies **two independent layers** of AES-256 encryption with KMS keys, for standards that require two layers (e.g. CNSSP 15). Header `aws:kms:dsse`.
4. **SSE-C** — you supply the key with **every request** (HTTPS only); S3 uses it to encrypt/decrypt and then discards it — it stores only a salted HMAC to validate future requests. Lose the key, lose the data.
5. **Client-side encryption** — you encrypt the data *before* uploading it with your own library and keys; S3 only ever stores ciphertext.

You can enforce encryption with a **bucket policy** that rejects any `PutObject` without a server-side encryption header, or enable **"Default encryption"** on the bucket so every new object is encrypted automatically. *(Note: since January 2023 S3 encrypts all new objects by default with SSE-S3 unless otherwise specified.)*

### Access Control

Multiple layers, used together:

- **IAM policies** — identity-based, attached to users/roles (most common).
- **Bucket policies** — resource-based policies attached directly to the bucket; can allow/deny cross-account or public access.
- **ACLs** — legacy, object/bucket-level grant lists (mostly deprecated; new buckets have ACLs disabled by default).
- **Block Public Access (BPA)** — four safety settings (block public ACLs, ignore public ACLs, block public bucket policies, restrict public bucket policies) that lock a bucket down; enabled by default on new buckets.
- **Pre-signed URLs** — temporary, signed URLs you generate with your credentials to grant time-limited access to a specific object without making it public.
- **Access Points** — named endpoints with their own policies, useful when many applications share one bucket.
- **Object Lambda Access Points** — run a Lambda on the *output* of GET/HEAD/LIST requests, so each consumer gets a transformed view (anonymized, filtered, resized) of the same stored object — no derivative copies. (Still a valid exam answer, though AWS closed the feature to new customers in 2025.)

### Static Website Hosting

- S3 can serve a static website directly: set an **index document** (e.g. `index.html`) and optional **error document**.
- The website endpoint is public HTTP (not HTTPS on the bucket endpoint itself — for HTTPS, put **CloudFront** in front).
- Making it public takes two steps: **turn off Block Public Access** for the bucket, then add a bucket policy allowing `s3:GetObject` to everyone. The better pattern keeps the bucket private behind **CloudFront + Origin Access Control (OAC)**.
- Website endpoint format: `http://<bucket>.s3-website-<region>.amazonaws.com` (or `s3-website.<region>` in newer regions) — different from the REST endpoint, and it returns HTML error pages and supports redirects.
- Note: **Cross-Origin Resource Sharing (CORS)** must be configured on the bucket if the site loads its assets from a different domain.

### Event Notifications

Buckets can emit events when things happen, delivered to:

- **Lambda functions** (e.g. process an image on upload)
- **SNS topics**
- **SQS queues**
- **EventBridge** (which can also route to dozens of other AWS services)

Events include `ObjectCreated`, `ObjectRemoved`, `ObjectRestore` (Glacier), etc. This is the backbone of many serverless data pipelines — the broader service landscape around S3 is in **[S3 × AWS Services](integrations.md)**.

### Mountpoint for Amazon S3

**Mountpoint for Amazon S3** is an open-source file client (Linux, FUSE + AWS CRT) that mounts a bucket as a **local file system**, translating file operations into S3 API calls — so legacy/file-based applications get S3's elastic storage and throughput through a file interface.

- Reads: **sequential and random**, up to the maximum object size; writes: **create new files sequentially only** — it **cannot modify existing files** or delete directories, and there are **no symlinks, no file locking, no full POSIX**.
- Designed for **read-heavy, many-instance workloads**: ML training, genomics, rendering, autonomous-vehicle simulation, ETL over TB–PB data lakes; repeated reads can be **cached** on instance storage/memory/EBS.
- Each file = one object key (`Data/x.csv` → directory `Data`, file `x.csv`). No filesystem charge — you pay normal **S3 requests + data transfer** (Mountpoint itself is free/open source).
- **Not a shared file system**: many readers + one sequential writer is the sweet spot; if you need locking/POSIX permissions AWS points you to **FSx for Lustre with a data repository association** to the bucket.

**Exam mapping (file storage decision):**

| Requirement | Answer |
|---|---|
| High-throughput file-style reads of a huge S3 data lake from Linux, no locking needed | **Mountpoint for Amazon S3** |
| Shared POSIX file system, concurrent read/write, multi-AZ, Linux/NFS | **Amazon EFS** |
| HPC / machine-learning workloads needing full POSIX, blazing throughput, S3-linked repo | **Amazon FSx for Lustre** |
| Windows file shares / AD integration, SMB | **Amazon FSx for Windows File Server** |
| On-premises apps needing file/byte access to S3-like storage with local caching | **AWS Storage Gateway (File Gateway)** |

"Applications must keep using `open()`/`read()` on Linux against an S3 dataset, but don't need locking" → **Mountpoint for S3**; "they *do* need locking/POSIX" → **FSx for Lustre** (AWS's own answer in the docs).

### Requester Pays

With **Requester Pays** buckets, the **person who downloads the data pays for it** — the classic answer to *"the bucket owner is tired of paying egress for everyone else's downloads"*:

- The bucket owner flips `RequestPaymentConfiguration` → `Payer = Requester` (bucket-level only, **never per object**). **Storage costs always stay with the bucket owner**; the requester pays the **requests + data download (egress)**.
- **Use case**: sharing huge datasets — reference data, geospatial data, web-crawl data, genomics — with third parties who should bear their own download costs.
- **Every request must be authenticated and must opt in**: the requester sends the **`x-amz-request-payer: requester`** header (or `RequestPayer` query parameter; `--request-payer requester` in the CLI; include it in **pre-signed URLs** too). The response then carries `x-amz-request-charged: requester`.
- **No header → `403 Access Denied` — and the *bucket owner* pays for that failed request.** Same if authentication fails or the request is anonymous. An assumed IAM role means **the role's account** is charged.

**Unsupported / hard limits (exam traps):**

- **Anonymous access is impossible** — which also means **Requester Pays buckets do not work with static website hosting**: any request through the website endpoint returns **403**.
- Not supported: SOAP, BitTorrent, and using the bucket as (or logging to) an end-user logging target.
- **Glacier restores**: requester pays only the restore *request*; the **bucket owner** pays the retrieval charges.

**Exam mapping:** "share a large dataset; consumers (not the owner) should pay download costs" → **Requester Pays**. "Public/anonymous website must stay free for visitors" → **not** Requester Pays (the owner pays; **CloudFront + OAC** in front of the bucket lowers the cost, since S3 → CloudFront transfer is free and CloudFront egress is cheaper and cached). "Consumers need only *temporary, fine-grained* access" → [pre-signed URLs](#access-control) rather than a billing switch.

### Other Notable Features

- **Multipart upload** — required for files >5 GB (the single-PUT limit), recommended above ~100 MB; up to **10,000 parts** of 5 MB–5 GB each, uploaded in parallel and retried individually. Incomplete uploads keep billing until aborted (lifecycle rule).
- **Byte-range fetches** — the read-side counterpart: GET ranges of an object in parallel to speed up downloads or read only part of a file.
- **Transfer Acceleration** — uploads enter the AWS network at the nearest **CloudFront edge location** and ride the AWS backbone to the bucket; for long-distance transfers, extra cost, endpoint `<bucket>.s3-accelerate.amazonaws.com`.
- **S3 Batch Operations** — apply an action (copy, tag, restore, modify ACLs) to billions of objects with a single job.
- **S3 Inventory** — periodic list of all objects and metadata for audit/analysis.
- **Requester Pays** — the requester (not the bucket owner) pays data transfer and request costs — see [Requester Pays](#requester-pays).
- **Object Lock** — WORM (write-once-read-many) protection for compliance; cannot be deleted or overwritten for a retention period. Requires versioning (and can now be enabled on existing buckets too).
- **Tagging** — key/value tags on buckets and objects, useful for cost allocation and lifecycle policies.

## Limits and Quotas (exam-relevant)

The full restrictions list lives in **[Bucket Restrictions and Limitations](bucket-restrictions-and-limitations.md)**. The highlights:

- Bucket names: **globally unique**, with strict naming rules — see [Bucket Naming Rules](bucket-naming-rules.md).
- **Single-region by default** — a bucket lives in one region; cross-region access is just cross-region data transfer (or use replication/Cross-Region Access Points).
- Maximum object size: **5 TB** (exam number; 50 TB since Dec 2025); single PUT max **5 GB**; multipart upload recommended above 100 MB (required above 5 GB).
- **10,000 general purpose buckets** per account by default since Nov 2024, raisable up to 1 million (older material and exam questions say **100**, raisable to 1,000).
- Deleting a bucket requires it to be **empty** first (no objects or versions).
- Versioning, Object Lock and replication need to be considered *before* uploading data — many settings can't be applied retroactively in a meaningful way.

## Cost Drivers

1. **Storage** — per GB-month, depends on storage class.
2. **Requests** — per 1,000 PUT/GET/LIST/COPY requests (GET is cheaper than PUT).
3. **Data transfer** — data transferred *out* to the internet (per GB), between regions, or out to CloudFront (often free).
4. **Retrieval fees** — per GB read back from Standard-IA, One Zone-IA and all Glacier classes (Glacier IR included — $0.03/GB; only Flexible Retrieval *bulk* restores are free). Standard and Intelligent-Tiering have none.
5. **Management features** — replication, inventory, analytics, etc.

## Security Checklist (SAA exam focus)

The full treatment of every control below — how the layers combine and how they map to exam questions — is in **[S3 Security Overview](security.md)**.

- Encrypt everything (SSE-S3 for simple, SSE-KMS when you need key control/auditing).
- Enable **Block Public Access** unless the bucket is intentionally public.
- Use **bucket policies** with `aws:SecureTransport` to deny non-HTTPS requests.
- Use **versioning + MFA Delete + replication** for critical data.
- Use **Object Lock** for compliance workloads.
- Log all access with **CloudTrail** data events and **S3 server access logging**.
- Prefer **VPC Gateway Endpoints** for S3 access from VPCs (free, keeps traffic off the internet).

## Repository Layout

Hands-on material for this section lives alongside these notes:

- `s3-bash-scripts/` — AWS CLI scripts exercising bucket operations.
- `sdk/` — boto3 (Python SDK) examples.
- [`bucket-policy/`](bucket-policy/readme.md) — grant another IAM user access with a bucket policy.
- [`metadata/`](metadata/readme.md) — upload an object with user-defined metadata.
- [`encryption/`](encryption/readme.md) — server-side encryption with SSE-S3 and SSE-KMS.
- [`encryption-client-side/`](encryption-client-side/readme.md) — encrypt locally, upload only ciphertext.
- [`iac/`](iac/README.md) — the same bucket provisioned with CloudFormation, Terraform, Pulumi and AWS CDK.

Companion theory docs, linked from this overview:

- [Bucket Naming Rules](bucket-naming-rules.md) — URL/DNS uniqueness, allowed characters, reserved prefixes and suffixes.
- [Request Styles](request-styles.md) — virtual hosted-style vs path-style URLs: formats, TLS/dots gotchas, and the path-style deprecation.
- [Bucket Types](bucket-types.md) — general purpose (flat) vs directory buckets, zero-byte folder objects, S3 Express One Zone.
- [Storage Classes Deep Dive](storage-classes.md) — durability, availability, redundancy, retrieval times, throughput and per-class pricing for all eight storage classes.
- [Object Overview](objects.md) — objects as data vs infrastructure: ETags, checksums, prefixes, metadata, tags, Object Lock, versioning.
- [Data Consistency](data-consistency.md) — strong read-after-write consistency since Dec 2020, what is still eventually consistent (replication, notifications) and conditional writes.
- [S3 Object Replication](replication.md) — CRR vs SRR, prerequisites, what is/isn't replicated, delete markers, Replication Time Control, Batch Replication.
- [S3 Lifecycle](lifecycle.md) — transitions and expirations, minimum storage durations, small-object default, billing vs execution delays, versioning cleanup.
- [S3 × AWS Services](integrations.md) — interoperability: Athena, Glue, EMR, Spectrum, Firehose, Lambda/SageMaker, Macie/GuardDuty/AWS Backup, Transfer Family.
- [Bucket Restrictions and Limitations](bucket-restrictions-and-limitations.md) — bucket quotas, object size limits, what "high availability" applies to.
- [S3 Security Overview](security.md) — bucket policies, ACLs, Object Ownership, Block Public Access, Access Analyzer, access points/Access Grants/Object Lambda, PrivateLink/CORS, encryption (in transit, server- and client-side), versioning/MFA Delete, tags, compliance and infrastructure security.

## References

- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=18393s (S3 from 5:06:32)
- ExamPro SAA-C03 cheat sheet: https://www.exampro.co/saa-c03 (source of the restrictions list)
- AWS S3 documentation: https://docs.aws.amazon.com/s3/
- S3 storage classes: https://aws.amazon.com/s3/storage-classes/
