# S3 Object Overview

## Objects are DATA, not infrastructure

An **object** is the unit of data storage in S3: the actual bytes you upload, plus the metadata that describes them. **Buckets are infrastructure** — they are the containers and configuration surface (policies, encryption defaults, lifecycle rules); **objects are the data payload itself**. Consequences of this mental model:

- There is no "edit" operation on an object: its content is **immutable**. To change it you upload a *new* full version (under the same key or a new one) — never a partial, in-place update.
- A single object can be anywhere from **0 bytes to 5 TB** (exam number; 50 TB since Dec 2025). A single PUT is limited to 5 GB, so multipart upload is required above that.
- Object operations (PutObject, GetObject…) are the *data plane*; bucket operations (CreateBucket, PutBucketPolicy…) are the *control plane* — see [Bucket Restrictions](bucket-restrictions-and-limitations.md).
- IaC tools treat objects differently: Terraform (`aws_s3_object` with `etag = filemd5(...)`) and Pulumi (`BucketObject`) manage individual objects and re-upload when the file's hash changes. **CloudFormation has no resource type for S3 objects** — you need a custom resource, or CDK's `BucketDeployment` (which uses one under the hood).

## Anatomy of an object

| Part | Description |
|---|---|
| **Key** | The object's name/full path, e.g. `photos/2026/cat.png`. Flat namespace in general purpose buckets. |
| **Data** | The bytes themselves (text, images, video, backups…). |
| **Version ID** | Unique ID of this version (if versioning is enabled on the bucket). |
| **ETag** | An entity tag — a unique identifier/checksum of the object's content (see below). |
| **Checksum** | Integrity checksum (CRC64NVME, CRC32, CRC32C, SHA-1, SHA-256). |
| **Metadata** | System-managed (content type, size, last modified) plus custom key/value pairs. |
| **Tags** | Optional key/value labels (max 10) for access control, lifecycle and cost allocation. |
| **Storage class** | Which tier the object lives in (Standard, IA, Glacier…). |

## ETags

The **ETag** (entity tag) is an opaque unique identifier that Amazon S3 assigns to each version of an object. Key facts:

- For a **single-part upload**, the ETag is (usually) the **MD5 hex digest of the object's content** — so two identical files uploaded directly get the same ETag.
- For a **multipart upload**, the ETag is **NOT** the MD5 of the whole file: it's a hash combining the MD5s of the individual parts, with a `-N` suffix indicating the number of parts (e.g. `d41d8cd98f00b204e9800998ecf8427e-3`).
- When the object is encrypted with **SSE-KMS**, **DSSE-KMS** or **SSE-C**, or stored in a **directory bucket** (S3 Express One Zone), the ETag is **not** an MD5 of the data — never use it to verify content in those cases.
- ETags are used for **conditional requests**: `If-Match` / `If-None-Match` on GET/PUT (optimistic locking, cache validation, avoiding overwrites) and `If-Range` on range GETs (resume a download only if the object hasn't changed).
- The ETag **changes when the object changes** (a new version gets a new ETag), so it doubles as a cheap "did this change?" indicator.

## Checksums

Because ETags are unreliable for verification (multipart, KMS encryption, directory buckets), S3 supports **checksums** that are computed on the data itself:

- Algorithms: **CRC64NVME**, **CRC32**, **CRC32C**, **SHA-1**, **SHA-256**. Since December 2024 current SDKs send a CRC checksum on every upload by default, and S3 adds a CRC64NVME checksum to new objects that arrive without one.
- Checksums are **independent of encryption** (computed on the plaintext data), which makes them the right tool for **end-to-end data integrity validation**.
- Multipart uploads have two checksum types: **full object** (one checksum of the whole file — CRC algorithms only — comparable to a checksum you compute locally) and **composite** (a checksum of the part checksums, shown with a `-N` suffix, like the multipart ETag).
- You can supply the checksum on upload, or let the SDK calculate and send it; S3 validates it on arrival, stores it and returns it with GET/HEAD (`ChecksumMode=ENABLED`).
- Objects uploaded without a checksum can get one by **copying them in place** (e.g. at scale with S3 Batch Operations).
- Choose a **CRC** algorithm for fast integrity checks and **SHA-256** when a compliance standard requires a cryptographic hash.

## Prefixes

A **prefix** is simply a string that represents the beginning part of an object key — `photos/2026/` is a prefix for all keys starting with that string. In the flat namespace of general purpose buckets, prefixes are how "folders" are simulated (see [Bucket Types](bucket-types.md)). They matter beyond organization:

- **Performance**: S3 request rate scales horizontally *per prefix* — you can sustain ~**3,500 PUT/COPY/POST/DELETE** and ~**5,500 GET/HEAD requests per second per prefix**, and there's no limit on the number of prefixes, so throughput scales with them (10 prefixes ≈ 55,000 GET/s). Hitting the limit returns `503 Slow Down` (retry with backoff while S3 scales). Randomizing key names is no longer needed — that advice predates 2018.
- **Scoping**: lifecycle rules, replication rules and IAM/bucket policies can all be restricted to a prefix, so one bucket can host several independent applications safely.
- **Listing**: `ListObjectsV2` with a `Delimiter` (`/`) groups keys by prefix, which is how the console renders the folder tree.

An object key can be at most **1,024 bytes** of UTF-8 — bytes, not characters, so non-ASCII characters use up more of the limit.

## Metadata

Every object carries metadata, in two flavors:

- **System-defined**: `Content-Type`, `Cache-Control` (e.g. `max-age=3600, must-revalidate`), `Content-Disposition`, `Content-Encoding`, `Content-Language`, `Content-Length`, `Last-Modified`, `ETag`, storage class, encryption info. Some are controlled only by S3 (`Content-Length`, `Last-Modified`, `ETag`); others you set yourself (e.g. `Content-Type`, `Cache-Control`).
- **User-defined**: your own key/value pairs, sent as `x-amz-meta-*` headers, up to **2 KB** of custom metadata per object.

Important details:

- Metadata is **part of the object**: to change it you must issue a new **CopyObject** with the `REPLACE` metadata directive (or re-upload) — the key doesn't change, but a new object version is created and you pay for a copy request.
- Custom metadata is returned as `x-amz-meta-*` headers with every GET/HEAD. S3 cannot search by metadata itself — to query it at scale, use **S3 Inventory** or **S3 Metadata** (metadata tables queryable with Athena).
- Don't confuse **object tags** (below) with metadata: **metadata describes the content** and is fixed with the object; **tags are a management layer** (access control, lifecycle, replication filters) that you can add or remove at any time without touching the data.

## Tags

**Object tags** are key/value pairs (up to **10 per object**; keys ≤128 chars, values ≤256 chars) attached to an object for management purposes:

- Can be **added, changed or removed at any time** with `PutObjectTagging`/`DeleteObjectTagging` — no need to re-upload the data.
- Requires the `s3:PutObjectTagging` permission, and policies can condition on tags: `s3:ExistingObjectTag/<key>` (tags already on the object — "only read objects tagged `team=blue`") and `s3:RequestObjectTag/<key>` / `s3:RequestObjectTagKeys` (tags sent with the request — "only allow uploads tagged `environment=dev`").
- Drive **lifecycle rules** ("expire all objects tagged `temp=true` after 7 days") and **replication rules** ("replicate only tagged `critical`").
- **Not for cost allocation**: object tags do not appear in the bill. Cost allocation works with **bucket** tags (activated as cost allocation tags); for per-prefix/per-object usage, use **S3 Storage Lens** or **S3 Inventory**.
- Are **replicated by default** along with the object; **not supported in directory buckets**.

## Object Locking (WORM)

**S3 Object Lock** keeps objects from being deleted or overwritten for a fixed time or indefinitely (**Write Once Read Many**) — a common compliance requirement (SEC, FINRA, GDPR…):

- **Requires versioning** — the lock applies to *object versions*. Originally it could only be enabled at bucket creation; since late 2023 it can also be enabled on an **existing** versioned bucket. Once enabled it cannot be disabled.
- Retention can be set **per object version** (`x-amz-object-lock-mode`, `x-amz-object-lock-retain-until-date`) or as a **default retention** on the bucket that applies to every new object.
- **Governance mode**: users with the `s3:BypassGovernanceRetention` permission (and MFA, if required) can bypass and shorten retention.
- **Compliance mode**: **nobody** — including the root account — can delete or overwrite a version before its retention expires. Irreversible.
- **Legal holds**: an extra, independent lock applied per version with no expiration date; released explicitly when the case is closed. Legal hold does not extend retention but blocks deletion while active.
- Retention periods can be extended (never shortened) on any locked version.
- Deleting an object with versioning just adds a delete marker — but the *version* itself cannot be removed until the retention expires, which is what makes Object Lock genuinely tamper-proof.

Object Lock can be managed from the console as well as from the CLI/SDK (e.g. `aws s3api put-object --object-lock-mode COMPLIANCE --object-lock-retain-until-date …`). Compliance mode is irreversible, so test it with Governance mode or short retention periods first.

## Versioning

Versioning turns every write into a **new version** instead of an overwrite — the backbone of object-level durability and recovery:

- Each version has its own **Version ID** and **ETag**; the "current" version is the one without a delete marker.
- Deleting an object adds a **delete marker** (recoverable by deleting the marker); permanently deleting requires targeting a specific **Version ID**.
- Lifecycle rules clean up **noncurrent versions** and stray delete markers — otherwise every edit forever consumes storage.
- Prerequisite for **replication** (CRR/SRR) and **Object Lock**; **MFA Delete** adds a second factor for permanent deletions.
- Full details in the [Versioning section](README.md#versioning) of the overview.

## References

- AWS docs — [Object properties](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-properties.html)
- AWS docs — [Adding checksums to objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html)
- AWS docs — [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- AWS docs — [Organizing objects using prefixes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html)

← Back to the [S3 overview](README.md)
