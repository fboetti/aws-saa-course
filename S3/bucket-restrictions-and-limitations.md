# S3 — Bucket Restrictions and Limitations

Notes from the course cheat sheet ([exampro.co/saa-c03](https://www.exampro.co/saa-c03)), with current values where AWS has since changed them:

- **Bucket quota**: the cheat sheet says **100 buckets** per account by default, raisable to **1,000** with a service request — that is what older exam questions use. Since **November 2024** the default is **10,000 general purpose buckets** per account, raisable up to **1 million** via Service Quotas.
- You need to **empty a bucket first** before you can delete it (no objects — and no leftover versions or delete markers if versioning is enabled). For large buckets, an expiration **lifecycle rule** empties it for free.
- **No max bucket size** and no limit to the number of objects in a bucket.
- Objects can be between **0 bytes and 5 TB** (the exam number; AWS raised the maximum to **50 TB** in December 2025).
- A **single `PUT` uploads at most 5 GB**. Above that, **multipart upload** is mandatory; it is recommended from **100 MB**. Multipart allows up to **10,000 parts** of 5 MB–5 GB each.
- **S3 on Outposts** has its own limits (capacity of the on-premises Outpost) and its own storage class.
- **Get, Put, List and Delete operations are designed for high availability** — these are the everyday **data-plane** operations.
- **Create, Delete or configuration operations should be run less often** — these are **control-plane** operations (`CreateBucket`, `PutBucketPolicy`…). Don't call them in tight loops from application code: create buckets at deploy time, not per request or per user.

## Exam-relevant extras

- A bucket is **single-region**: data never leaves the region unless you copy it or set up replication.
- Bucket names are **globally unique** — see [Bucket Naming Rules](bucket-naming-rules.md).
- Versioning, Object Lock and replication should be considered *before* uploading data — replication only copies new objects (existing ones need Batch Replication), and versions do not exist for writes made before versioning was enabled.
- Request rates scale **per prefix**: 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD per second per prefix, with no limit on the number of prefixes.

← Back to the [S3 overview](README.md)
