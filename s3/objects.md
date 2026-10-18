# S3 Object Overview

## Objects are DATA, not infrastructure

An **object** is the unit of data storage in S3: the actual bytes you upload, plus the metadata that describes them. **Buckets are infrastructure** — they are the containers and configuration surface (policies, encryption defaults, lifecycle rules); **objects are the data payload itself**. Consequences of this mental model:

- There is no "edit" operation on an object: its content is **immutable**. To change it you upload a *new* full version (under the same key or a new one) — never a partial, in-place update.
- A single object can be anywhere from **0 bytes to 5 TB** (multipart upload required above 5 GB).
- Object operations (PutObject, GetObject…) are the *data plane*; bucket operations (CreateBucket, PutBucketPolicy…) are the *control plane* — see [Bucket Restrictions](bucket-restrictions-and-limitations.md).
- Terraform/Pulumi can detect the change of data in an object file (like txt, thanks to ETag change): CloudFormation hasn't a construct to detect this change.

## Anatomy of an object

| Part | Description |
|---|---|
| **Key** | The object's name/full path, e.g. `photos/2026/cat.png`. Flat namespace in general purpose buckets. |
| **Data** | The bytes themselves (text, images, video, backups…). |
| **Version ID** | Unique ID of this version (if versioning is enabled on the bucket). |
| **ETag** | An entity tag — a unique identifier/checksum of the object's content (see below). |
| **Checksum** | Optional additional integrity checksums (CRC32, CRC32C, SHA-1, SHA-256). |
| **Metadata** | System-managed (content type, size, last modified) plus custom key/value pairs. |
| **Tags** | Optional key/value labels (max 10) for access control, lifecycle and cost allocation. |
| **Storage class** | Which tier the object lives in (Standard, IA, Glacier…). |

## ETags

The **ETag** (entity tag) is an opaque unique identifier that Amazon S3 assigns to each version of an object. Key facts:

- For a **single-part upload**, the ETag is (usually) the **MD5 hex digest of the object's content** — so two identical files uploaded directly get the same ETag.
- For a **multipart upload**, the ETag is **NOT** the MD5 of the whole file: it's a hash combining the MD5s of the individual parts, with a `-N` suffix indicating the number of parts (e.g. `d41d8cd98f00b204e9800998ecf8427e-3`).
- When the object is encrypted with **SSE-KMS**, or stored in a **directory bucket** (S3 Express One Zone), the ETag is a **random string**, not an MD5 — never use it to verify content in those cases.
- ETags are used for **conditional requests**: `If-Match` / `If-None-Match` on GET/PUT (optimistic locking, cache validation, avoiding overwrites) and for **Range GETs** to verify the partial content.
- The ETag **changes when the object changes** (a new version gets a new ETag), so it doubles as a cheap "did this change?" indicator.

## Checksums

Because ETags are unreliable for verification (multipart, KMS encryption, directory buckets), S3 supports **additional checksums** computed over the *entire* object:

- Algorithms: **CRC32** (default when the SDK computes one), **CRC32C**, **SHA-1**, **SHA-256**.
- Unlike the ETag, a checksum is **consistent regardless of upload method** — multipart, copy or encryption don't change it — which makes it the right tool for **end-to-end data integrity validation**.
- You can supply the checksum on upload, or let the SDK calculate and send it; the value is stored and returned with GET/HEAD.
- Existing objects can be backfilled with **S3 Batch Operations** (a checksum-repair job), and checksums are also validated automatically during multipart completion and replication.
- Choose **CRC32C** for fast integrity checks and **SHA-256** when a compliance standard requires a cryptographic hash.

## Prefixes

A **prefix** is simply a string that represents the beginning part of an object key — `photos/2026/` is a prefix for all keys starting with that string. In the flat namespace of general purpose buckets, prefixes are how "folders" are simulated (see [Bucket Types](bucket-types.md)). They matter beyond organization:

- **Performance**: S3 request rate scales horizontally *per prefix* — you can sustain ~**3,500 PUT/COPY/POST/DELETE** and ~**5,500 GET/HEAD requests per second per prefix**. Spreading traffic over **at least 15 prefixes** avoids `503 Slow Down` errors (randomize key names inside a prefix if you can't create more prefixes).
- **Scoping**: lifecycle rules, replication rules and IAM/bucket policies can all be restricted to a prefix, so one bucket can host several independent applications safely.
- **Listing**: `ListObjectsV2` with a `Delimiter` (`/`) groups keys by prefix, which is how the console renders the folder tree.

The limit of an object key is 1024 bytes/characters.

## Metadata

Every object carries metadata, in two flavors:

- **System-defined**: `Content-Type`, `Cache-Control` (max-age=3600, must-revalidate, ecc), `Content-Disposition`, `Content-Encoding`, `Content-Language`, `Content-Length`, `Last-Modified`, `ETag`, storage class, encryption info — managed by S3, some of them can be modified by the user (e.g. Content-Type).
- **User-defined**: your own key/value pairs, sent as `x-amz-meta-*` headers, up to **2 KB** of custom metadata per object.

Important details:

- Metadata is **part of the object**: to change it you must issue a new **CopyObject** with the `REPLACE` metadata directive (or re-upload) — the key doesn't change, but a new object version is created and you pay for a copy request.
- Custom metadata is returned with every GET, and can be filtered on with `x-amz-meta-` conditions in IAM policies.
- Don't confuse **object tags** (below) with metadata: metadata travels with the object and describes it technically; tags are a management layer regarding CLOUD RESOURCES and you can add/remove independently. Metadata is about the CONTENT of the object.

## Tags

**Object tags** are key/value pairs (up to **10 per object**; keys ≤128 chars, values ≤256 chars) attached to an object for management purposes:

- Can be **added, changed or removed at any time** with `PutObjectTagging`/`DeleteObjectTagging` — no need to re-upload the data.
- Requires the `s3:PutObjectTagging` permission, and can be restricted per-tag via IAM conditions (`s3:RequestTag`, `s3:TagKeys`) — e.g. "only allow uploads tagged `environment=dev`".
- Drive **lifecycle rules** ("expire all objects tagged `temp=true` after 7 days") and **replication rules** ("replicate only tagged `critical`").
- Enable **cost allocation**: tag objects on ingestion and see exactly how much each project costs in Cost Explorer.
- Are used as filters in **S3 event notifications** (EventBridge).
- Not replicated automatically with the object unless replica modification sync is enabled — and **not supported in directory buckets**.

## Object Locking (WORM)

**S3 Object Lock** keeps objects from being deleted or overwritten for a fixed time or indefinitely (**Write Once Read Many**) — a common compliance requirement (SEC, FINRA, GDPR…):

- Must be enabled **when the bucket is created**, and it **requires versioning** — the lock applies to *object versions*.
- **Governance mode**: users with the `s3:BypassGovernanceRetention` permission (and MFA, if required) can bypass and shorten retention.
- **Compliance mode**: **nobody** — including the root account — can delete or overwrite a version before its retention expires. Irreversible.
- **Legal holds**: an extra, independent lock applied per version with no expiration date; released explicitly when the case is closed. Legal hold does not extend retention but blocks deletion while active.
- Retention periods can be extended (never shortened) on any locked version.
- Deleting an object with versioning just adds a delete marker — but the *version* itself cannot be removed until the retention expires, which is what makes Object Lock genuinely tamper-proof.

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
