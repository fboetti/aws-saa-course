# S3 — Bucket Restrictions and Limitations

Notes from the course cheat sheet ([exampro.co/saa-c03](https://www.exampro.co/saa-c03)):

- You can by default create **100 buckets** per account.
- You can create a service request to increase the limit to **1,000 buckets** (and further via AWS Support).
- You need to **empty a bucket first** before you can delete it (no objects — and no leftover versions or delete markers if versioning is enabled).
- **No max bucket size** and no limit to the number of objects in a bucket.
- Files (objects) can be between **0 and 5 TB**.
- Files larger than **100 MB** should use **multi-part upload** (mandatory above 5 GB).
- **S3 for AWS Outposts** has its own limits (capacity of the on-premises outpost device).
- **Get, Put, List, and Delete operations are designed for high availability** — these are the everyday data-plane operations.
- **Create, Delete or configuration operations should be run less often** — these are control-plane operations; hammering them (e.g. in tight loops from application code) can lead to throttling, since buckets are a limited resource.

## Exam-relevant extras

- A bucket is **single-region**: data never leaves the region unless you copy it or set up replication.
- Bucket names are **globally unique** — see [Bucket Naming Rules](bucket-naming-rules.md).
- Versioning, Object Lock and replication should be considered *before* uploading data — many settings can't be applied retroactively in a meaningful way.

← Back to the [S3 overview](README.md)
