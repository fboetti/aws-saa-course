# S3 Object Replication (exam focus)

**S3 Replication** asynchronously copies objects from a **source bucket** to one or more **destination buckets**. It is configured *only on the source bucket* (via the replication configuration + an IAM role), and the destination needs no rule of its own — just to satisfy the prerequisites.

## The two types

| | **CRR** — Cross-Region Replication | **SRR** — Same-Region Replication |
|---|---|---|
| Destination | Bucket in a **different region** | Bucket in the **same region** |
| Typical exam triggers | Compliance (data must live in another jurisdiction), **disaster recovery**, lower-latency access for geographically distant users | **Log aggregation**, keeping **prod ↔ test/dev in sync**, multi-tenant isolation, keeping two buckets in sync in one region |
| Cost | Cross-region data transfer charges apply | No cross-region transfer; cheap |
| Latency | Asynchronous — usually seconds, most objects within 15 minutes, **no guarantee** unless you add [RTC](#s3-replication-time-control-rtc) | Same |

Both support **cross-account** replication (destination owned by a different AWS account).

## Prerequisites (always the answer to "why isn't my replication working?")

1. **Versioning must be enabled on BOTH source and destination buckets.** This is the #1 exam fact about replication.
2. An **IAM role** that S3 assumes, allowed to read from the source (`s3:GetReplicationConfiguration`, `s3:ListBucket`, `s3:GetObjectVersionForReplication`, `s3:GetObjectVersionAcl`, `s3:GetObjectVersionTagging`) and write to the destination (`s3:ReplicateObject`, `s3:ReplicateDelete`, `s3:ReplicateTags`) — plus `kms:Decrypt`/`kms:Encrypt` on the keys when objects use SSE-KMS.
3. For **cross-account** destinations: a **bucket policy** on the destination allowing the source account/role to write.
4. The bucket owner must be able to **read the objects** (object ownership/ACLs) — otherwise those objects are skipped.

## What IS and ISN'T replicated (exam gold)

### Replicated by default

- Objects **created after** the replication configuration was added.
- Unencrypted objects and objects encrypted with **SSE-S3** or **SSE-C**.
- Objects encrypted with **SSE-KMS or DSSE-KMS** — but **only if you opt in** on the rule (`SourceSelectionCriteria` → `SseKmsEncryptedObjects`) and name the destination key (`ReplicaKmsKeyID`); otherwise they are skipped.
- **Object tags**, metadata, **ACL updates** (unless you change replica ownership), and **Object Lock retention** (retention/hold travels with the replica — the destination bucket must have Object Lock enabled too).

### NOT replicated by default

| Case | Behavior |
|---|---|
| **Objects that already existed** before the rule was configured | Not copied — use **S3 Batch Replication** to backfill |
| **Permanently deleted versions** (DELETE with a Version ID) | **Not replicated** — the version survives in the destination on purpose: this protects against malicious/accidental deletion (great for DR) |
| **Delete markers** (normal DELETE without Version ID) | **Not replicated** in the current (V2, `Filter`-based) configuration — you must enable *delete marker replication*, and it isn't supported on tag-based rules. In legacy V1 configs (no `Filter`) delete markers **are** replicated |
| **Delete markers created by lifecycle actions** | Never replicated — apply the same lifecycle rules to both buckets instead |
| **Replicas of replicas** (A → B, then B → C) | B's replicas are not re-replicated to C automatically — use Batch Replication |
| Objects changed to a **new destination bucket** after reconfiguration | Not re-replicated automatically |
| Objects in **Glacier Flexible Retrieval, Glacier Deep Archive, Intelligent-Tiering Archive/Deep Archive Access** | Cannot be replicated until restored and moved to a retrievable storage class |
| **Tag-based rules**: objects tagged *after* upload | The tag must already be present **at `PutObject` time** for live replication; otherwise use Batch Replication |
| **Bucket-level configuration** (lifecycle, notifications, policies…) | Never copied — source and destination can (and often should) differ |

## S3 Replication Time Control (RTC)

Regular replication is asynchronous and best-effort. **RTC** makes it predictable and compliance-grade:

- Replicates **most objects in seconds**, and **99.99% of new objects within 15 minutes** by design.
- Backed by an **SLA: 99.9% of objects within 15 minutes** during a billing month (SLA excludes periods where S3 request-rate guidelines or the 1 Gbps replication transfer quota are exceeded).
- Enables **S3 Replication metrics** in CloudWatch (latency, pending operations/bytes) and **event notifications** when an object breaches the 15-minute threshold.
- Configured on the rule itself (`ReplicationTime` with `Time.Minutes: 15` — **15 is the only allowed value**); costs extra.
- RTC does **not** apply to Batch Replication, and delete-marker replication is outside the SLA.

**Exam pattern:** a question demands *"objects must appear in the DR region within a guaranteed, auditable time frame"* → the answer is **CRR + Replication Time Control**.

## S3 Batch Replication

On-demand job (via **S3 Batch Operations**) that:

- **Backfills existing objects** created before the replication rule existed.
- **Retries failed replications** (objects stuck in `FAILED` status).
- Works for objects tagged after upload (which live replication skipped) and for re-replicating to a changed destination.

A rule can be **disabled** (`Status: Disabled`) or removed; objects written meanwhile are not replicated later on their own — Batch Replication reconciles the gap.

## Two-way replication

For active-active setups (e.g. both regions accept writes behind a Multi-Region Access Point) you configure replication **in both directions** (A → B and B → A) and enable **replica modification sync**: metadata changes made on a *replica* (tags, ACLs, Object Lock settings) are replicated back to the source. Objects that are themselves replicas are not replicated back again, so there is no loop.

## Exam checklist

- **Versioning on source AND destination** — mandatory, both buckets.
- Replication is **asynchronous** (eventual) — **not a backup**, **not real-time**; add **RTC** for a 15-minute SLA.
- **Only new objects** are replicated — existing objects need **S3 Batch Replication**.
- **Permanent deletes are not replicated** → destination keeps the data (DR win); **delete markers need explicit opt-in** (V2 rules).
- **CRR** = compliance / DR / lower-latency distant users; **SRR** = log aggregation / prod-test sync / same-region multi-bucket sync.
- Replication needs an **IAM role**; cross-account also needs a **destination bucket policy**.
- Destination replica has the **same key** (and its own Version ID); you can specify a different **storage class** for the replica (e.g. replicate to Standard-IA to save cost).
- Check progress via `x-amz-replication-status` (`PENDING`/`COMPLETE`/`FAILED`) and CloudWatch **replication metrics**.
- Replication also underpins **[data consistency](data-consistency.md)** questions: the *destination* read is eventually consistent even though a single bucket is strongly consistent.

## References

- AWS docs — [Replicating objects within and across Regions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-what-is-isnot-replicated.html)
- AWS docs — [Replicating delete markers between buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-marker-replication.html)
- AWS docs — [Meeting compliance requirements with S3 Replication Time Control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-time-control.html)
- AWS docs — [Replicating existing objects (S3 Batch Replication)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-batch-replication-batch.html)
- AWS blog — [Announcing Amazon S3 Replication Time Control](https://aws.amazon.com/blogs/aws/amazon-s3-replication-time-control/)

← Back to the [S3 overview](README.md)
