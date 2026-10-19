# Amazon S3 — Theoretical Overview

Notes on S3 buckets and their properties, following the course video
([freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=18393s) — S3 section starts at **5:06:32**).

## What is S3?

**Amazon Simple Storage Service (S3)** is AWS's object storage service. You store data as **objects** inside **buckets** — think of a bucket as a top-level container (like a filesystem root) and objects as files living under a *key* (their full path/name inside the bucket).

Key characteristics:

- **Object storage, not file storage**: there is no real directory tree. Keys are flat strings like `images/2026/photo.jpg`; the `/` characters just *look* like folders in the console.
- **Regional service**: a bucket is created in a specific AWS region and its name must be unique **globally** across all AWS accounts.
- **Virtually unlimited scale**: no maximum bucket size; you pay for what you store plus requests and data transfer.
- **Designed for 99.999999999% (eleven nines) durability** and 99.99% availability (Standard), because objects are stored redundantly across multiple devices in a minimum of three Availability Zones.

## Buckets and Objects

| Concept | Details |
|---|---|
| **Bucket** | Container for objects. Must follow strict, **globally unique** naming rules (they become part of a public DNS name — see [Bucket Naming Rules](#bucket-naming-rules)). Cannot be renamed after creation. |
| **Object** | The unit of storage: data + metadata + key. Max object size is **5 TB**. Objects are the **data payload**; buckets are the infrastructure around them — see the [Object Overview](objects.md). |
| **Key** | The full path/name of the object, e.g. `photos/2026/cat.png`. Keys can contain slashes to simulate folders, but S3 has no real hierarchy. |
| **Version ID** | If versioning is enabled, every object gets a unique version ID; "folders" and current versions coexist. |
| **Metadata** | Custom key/value pairs set on upload, plus system metadata (content type, ETag, last modified). |

## Bucket Naming Rules

Because every object is addressable with a URL (`https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>`), the bucket name is part of a public DNS name — so it must be **unique across all AWS accounts and all regions**, and it must be DNS-compatible.

The full rules (allowed characters, reserved prefixes/suffixes, IP-address and adjacent-dot restrictions, examples) are in a dedicated document: **[Bucket Naming Rules](bucket-naming-rules.md)**.

## Bucket Types

S3 has **two types of buckets**:

- **General purpose buckets** — the original type, with a *flat* namespace. What the console shows as "folders" are just key prefixes: a folder you create is a real **0-byte object** whose key ends with `/`, and "moving" an object into a folder only changes its **key** (S3 implements it as copy + delete — no data relocation in a hierarchy, because there is none).
- **Directory buckets** — introduced in 2023 together with the **S3 Express One Zone** storage class: a true hierarchical (directory) namespace in a single AZ, with consistent single-digit millisecond latency.

The full comparison (names, supported features, endpoints) is in a dedicated document: **[Bucket Types](bucket-types.md)**.

## Storage Classes

S3 offers several storage classes to trade cost against access speed (trade Retrieval Time, Accessibility, Durability). All except **Glacier Instant Retrieval** are for data that is *infrequently* accessed:

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

**Frequent vs. infrequent access** is decided by how often you expect to read the data; **retrieval time** is decided by how quickly you need it back. You can also add **provisioned throughput** (capacity units) when you need to sustain high GET/PUT rates beyond your account's baseline.

The full deep dive — durability, availability, data redundancy, retrieval times, throughput/scalability, use cases and pricing (storage, requests, retrieval fees, minimum durations) for **every** storage class — is in **[Storage Classes Deep Dive](storage-classes.md)**.

S3 Outposts has its own storage class.

## Bucket Properties / Features

### Versioning

- Keeps every version of every object (including an edit marker `null` for the first upload).
- States: **Off → Enabled** (once suspended, it can only be *suspended*, never fully off again).
- Deleting a versioned object just adds a **delete marker**; the object is recoverable by removing the marker or deleting a specific version.
- **MFA Delete** can be enabled so that changing versioning or permanently deleting versions requires an MFA device — extra protection against accidental/malicious deletion.
- Versioning is a prerequisite for **Cross-Region Replication (CRR)** and **Same-Region Replication (SRR)**.

### Replication

- **CRR**: copies objects to a bucket in another region (compliance, lower-latency access, disaster recovery).
- **SRR**: copies objects to another bucket in the same region (log aggregation, keeping prod/test in sync).
- Replication is **asynchronous** and applies only to **new** objects created after replication is configured (existing objects are not copied unless you run a backfill/batch replication).
- Requires versioning on both source and destination buckets.

### Lifecycle Rules

Rules that automate object transitions over time, e.g.:

- Move to **Standard-IA** after 30 days, **Glacier** after 90 days, **Deep Archive** after 365 days.
- **Expire (delete)** old versions or incomplete multipart uploads after N days.
- Works together with versioning (can clean up old versions and delete markers).

### Encryption

S3 supports four encryption options:

1. **SSE-S3** — Amazon S3 manages the keys (`aws:kms` not needed); each object encrypted with a unique key, keys themselves encrypted. Use header `x-amz-server-side-encryption: AES256`.
2. **SSE-KMS** — Keys managed by AWS **KMS** (AWS-managed or your own CMK); gives you key usage audit trail via CloudTrail and per-key permissions.
3. **SSE-C** — You supply and manage the keys; AWS stores and uses them but never manages them for you.
4. **Client-side encryption** — You encrypt the data *before* uploading it with your own library and keys; S3 only ever stores ciphertext.

You can enforce encryption with a **bucket policy** that rejects any `PutObject` without a server-side encryption header, or enable **"Default encryption"** on the bucket so every new object is encrypted automatically. *(Note: since January 2023 S3 encrypts all new objects by default with SSE-S3 unless otherwise specified.)*

### Access Control

Multiple layers, used together:

- **IAM policies** — identity-based, attached to users/roles (most common).
- **Bucket policies** — resource-based policies attached directly to the bucket; can allow/deny cross-account or public access.
- **ACLs** — legacy, object/bucket-level grant lists (mostly deprecated; new buckets have ACLs disabled by default).
- **Block Public Access (BPA)** — four safety settings (block public ACLs, ignore public ACLs, block public bucket policies, restrict public bucket policies) that lock a bucket down; enabled by default on new buckets.
- **Pre-signed URLs** — temporary, signed URLs you generate with your credentials to grant time-limited access to a specific object without making it public.
- **Access Points** — named endpoints with their own policies, useful when many applications share one bucket.

### Static Website Hosting

- S3 can serve a static website directly: set an **index document** (e.g. `index.html`) and optional **error document**.
- The website endpoint is public HTTP (not HTTPS on the bucket endpoint itself — for HTTPS, put **CloudFront** in front).
- Combines with bucket policies to allow `s3:GetObject` for everyone.
- Note: **Cross-Origin Resource Sharing (CORS)** must be configured on the bucket if the site loads its assets from a different domain.

### Event Notifications

Buckets can emit events when things happen, delivered to:

- **Lambda functions** (e.g. process an image on upload)
- **SNS topics**
- **SQS queues**
- **EventBridge** (which can also route to dozens of other AWS services)

Events include `ObjectCreated`, `ObjectRemoved`, `ObjectRestore` (Glacier), etc. This is the backbone of many serverless data pipelines.

### Other Notable Features

- **Multipart upload** — required for files >5 GB, recommended above ~100 MB; parallelizes upload and allows resuming.
- **Transfer acceleration** — upload over CloudFront edge locations for long-distance transfers.
- **S3 Batch Operations** — apply an action (copy, tag, restore, modify ACLs) to billions of objects with a single job.
- **S3 Inventory** — periodic list of all objects and metadata for audit/analysis.
- **Requester Pays** — the requester (not the bucket owner) pays data transfer and request costs.
- **Object Lock** — WORM (write-once-read-many) protection for compliance; cannot be deleted or overwritten for a retention period. Requires versioning.
- **Tagging** — key/value tags on buckets and objects, useful for cost allocation and lifecycle policies.

## Limits and Quotas (exam-relevant)

The full restrictions list lives in **[Bucket Restrictions and Limitations](bucket-restrictions-and-limitations.md)**. The highlights:

- Bucket names: **globally unique**, with strict naming rules — see [Bucket Naming Rules](bucket-naming-rules.md).
- **Single-region by default** — a bucket lives in one region; cross-region access is just cross-region data transfer (or use replication/Cross-Region Access Points).
- Maximum object size: **5 TB**; multipart upload recommended above 100 MB (required above 5 GB).
- **100 buckets** per account by default, raisable to 1,000 on request.
- Deleting a bucket requires it to be **empty** first (no objects or versions).
- Versioning, Object Lock and replication need to be considered *before* uploading data — many settings can't be applied retroactively in a meaningful way.

## Cost Drivers

1. **Storage** — per GB-month, depends on storage class.
2. **Requests** — per 1,000 PUT/GET/LIST/COPY requests (GET is cheaper than PUT).
3. **Data transfer** — data transferred *out* to the internet (per GB), between regions, or out to CloudFront (often free).
4. **Retrieval fees** — for Glacier classes (except Glacier IR) and Standard-IA/One Zone-IA.
5. **Management features** — replication, inventory, analytics, etc.

## Security Checklist (SAA exam focus)

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
- `iac/pulumi/` — minimal S3 bucket provisioned with Pulumi (Python); see its [README](iac/pulumi/README.md).
- `iac/cdk/` — the same infrastructure defined with AWS CDK (Python); see its [README](iac/cdk/README.md).

Companion theory docs, linked from this overview:

- [Bucket Naming Rules](bucket-naming-rules.md) — URL/DNS uniqueness, allowed characters, reserved prefixes and suffixes.
- [Request Styles](request-styles.md) — virtual hosted-style vs path-style URLs: formats, TLS/dots gotchas, and the path-style deprecation.
- [Bucket Types](bucket-types.md) — general purpose (flat) vs directory buckets, zero-byte folder objects, S3 Express One Zone.
- [Storage Classes Deep Dive](storage-classes.md) — durability, availability, redundancy, retrieval times, throughput and per-class pricing for all eight storage classes.
- [Object Overview](objects.md) — objects as data vs infrastructure: ETags, checksums, prefixes, metadata, tags, Object Lock, versioning.
- [Bucket Restrictions and Limitations](bucket-restrictions-and-limitations.md) — bucket quotas, object size limits, what "high availability" applies to.

## References

- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=18393s (S3 from 5:06:32)
- ExamPro SAA-C03 cheat sheet: https://www.exampro.com/ssa-c03 (source of the restrictions list)
- AWS S3 documentation: https://docs.aws.amazon.com/s3/
- S3 storage classes: https://aws.amazon.com/s3/storage-classes/
