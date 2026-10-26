# S3 Lifecycle (exam focus)

An **S3 Lifecycle configuration** is a set of rules on a bucket that tells S3 to **move objects to cheaper storage classes** (transitions) and/or **delete them** (expiration) automatically — no application code, no Lambda, no cron jobs. It is the standard answer to every *"reduce storage cost automatically"* exam question.

## The action types

| Action | What it does |
|---|---|
| **Transition** | Move an object to a colder storage class along a one-way **waterfall**: Standard → Standard-IA → Intelligent-Tiering → One Zone-IA → Glacier Instant Retrieval → Glacier Flexible Retrieval → Glacier Deep Archive. You can skip steps (e.g. Standard → Deep Archive directly) but never go up. One exception: **One Zone-IA cannot transition to Glacier Instant Retrieval** (only to Flexible Retrieval / Deep Archive). |
| **Expiration** | Delete the object (non-versioned bucket) or add a **delete marker** (versioned bucket) |
| **Expire current versions** | On versioned buckets: turns the current version into a noncurrent one via delete marker |
| **Permanently delete noncurrent versions** | Actually frees the storage of old versions — without this, versioned buckets grow forever |
| **Delete expired delete markers** | Removes stray zero-version delete markers ("expired object delete markers") |
| **Abort incomplete multipart upload** | Kill uploads that never finished (best practice: after **7 days**) — abandoned parts bill forever otherwise |

### Canonical example (the pattern you'll see in questions)

Logs that must stay one month, then get cheap, then die after a year:

- Transition **Standard → Standard-IA** after **30 days**
- Transition **Standard-IA → Glacier Flexible Retrieval** after **90 days**
- **Expire** after **365 days**
- **Abort incomplete multipart uploads** after **7 days**

## Rules you must know for the exam

1. **Rules apply retroactively.** When you add a lifecycle configuration, it covers **existing objects and new ones** — an "expire after 30 days" rule added today immediately queues every object already older than 30 days for deletion. (Think twice before adding expiration rules to a bucket with production data.)
2. **A bucket policy cannot stop lifecycle.** Even a policy that denies *everything* to *everybody* will not prevent lifecycle transitions or deletions — lifecycle is an S3-internal operation, not a request.
3. **Minimum storage durations** — leaving (or deleting) a storage class early incurs a **prorated charge** for the remainder:

   | Storage class | Minimum storage duration |
   |---|---|
   | S3 Standard-IA / One Zone-IA | **30 days** |
   | S3 Intelligent-Tiering | **none** (removed in 2021) |
   | S3 Glacier Instant Retrieval | **90 days** |
   | S3 Glacier Flexible Retrieval | **90 days** |
   | S3 Glacier Deep Archive | **180 days** |

   So "expire objects 10 days after they enter Standard-IA" still bills you 30 days of IA. And a single rule **cannot** chain transitions closer than the minimum duration (e.g. to Glacier IR at day 4 and Deep Archive at day 24 is illegal — Deep Archive must be ≥ day 94).
4. **30-day rule for IA transitions.** Lifecycle cannot move objects from Standard to **Standard-IA or One Zone-IA before they are 30 days old** — the classic exam trap ("transition to IA after 7 days" is not allowed; Glacier classes and Intelligent-Tiering have no such floor).
5. **Small objects don't transition by default.** Since **September 2024**, objects **< 128 KB** are never transitioned automatically (transition request cost would exceed the savings). Opt in with an **object size filter** (`ObjectSizeGreaterThan`) or the `x-amz-transition-default-minimum-object-size` header. Before Sept 2024 they *were* allowed to go straight to Glacier Flexible/Deep Archive.
6. **Asynchronous, and billing decouples from the action.** S3 queues transitions/expirations — actual execution can lag by **days or weeks**, and the timestamp is rounded to **midnight UTC the next day**. But **billing changes the moment the rule is satisfied**: after the expiration time you stop paying for storage even if the object is still there; after a transition date you start paying the destination class rate. **Exception:** Intelligent-Tiering — billing changes only after the physical transition completes.
7. **Transition costs exist:** no *retrieval* charge for lifecycle transitions, but each transition is a **transition request** (charged per object) plus **ingestion** into the destination class — another reason small objects are filtered out.
8. **Waterfall only.** You cannot transition "backwards" with lifecycle: Glacier Flexible Retrieval can only go to Deep Archive, Deep Archive is **one-way** (restore + copy to leave it). Going from archived classes back to Standard/IA requires restore → copy.
9. **Conflicting rules on the same day** — S3 applies a fixed precedence: **permanent deletion > transition > delete marker creation**; when both a Glacier Flexible and a Standard-IA transition are eligible, **Glacier Flexible wins**.
10. **Versioning interplay:**
   - Expiration on a versioned bucket only adds a **delete marker**; storage isn't freed until a rule **permanently deletes noncurrent versions**.
   - On a **non-versioned** bucket, expiration **permanently deletes** the object (irrecoverable).
   - Cleanup combo for versioned buckets: expire current + delete noncurrent versions + delete expired delete markers.
11. **Tag-based rules are re-checked at execution time.** Tags are evaluated daily; if the trigger tag was removed before the queued action ran, the action is aborted (removing a tag is a *race*, not a guaranteed cancel — remove it early, or wait for a Lifecycle Event Notification).
12. **Objects with `PENDING`/`FAILED` replication status** cannot be transitioned (on versioned/suspended buckets) — replication must settle first.

## Lifecycle × other features

- **Replication**: lifecycle-created delete markers are **not replicated** — apply the same rules on both buckets (see [Replication](replication.md)).
- **Consistency**: lifecycle expiration is unrelated to read consistency — a bucket is still [strongly consistent](data-consistency.md) while objects are queued for deletion.
- **Object Lock**: retention/holds govern what may be deleted; lifecycle can't override a retention period.
- **Encryption**: objects stay encrypted through transitions (SSE-KMS keys stay attached).
- **Monitoring**: **S3 Storage Lens** shows how much storage is *not* following lifecycle recommendations; lifecycle progress is visible via CloudWatch metrics and **Lifecycle Event Notifications**.
- **Directory buckets (S3 Express One Zone)** support only a subset — check current limits before assuming rules apply.

## Exam checklist

- "Automatically move logs to IA after 30 days, archive after 90, delete after 1 year" → **lifecycle transition + expiration rules** (no code).
- "Clean up incomplete/abandoned multipart uploads" → **abort incomplete multipart upload after 7 days**.
- "Objects are still there after the expiration date" → that's **normal** (asynchronous, days/weeks delay) — but **billing already stopped**.
- "Bucket policy denies everything but objects keep disappearing" → **lifecycle cannot be blocked by bucket policy**.
- "Old versions are piling up costs with versioning on" → add rules for **noncurrent versions + expired delete markers**.
- "Delete 7 days after entering IA but the bill shows 30 days" → **minimum storage duration** charge.
- "Transition isn't happening for our tiny files" → **< 128 KB default no-transition behavior** (post Sept 2024).
- "Move objects to Standard-IA after 7 days" → **not allowed**: IA / One Zone-IA transitions need objects ≥ **30 days** old (use Intelligent-Tiering or a Glacier class if you need it sooner).

## References

- AWS docs — [Managing the lifecycle of objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- AWS docs — [Transitioning objects using S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html)
- AWS docs — [Expiring objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html)
- AWS docs — [Examples of S3 Lifecycle configurations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-examples.html)
- AWS docs — [Troubleshooting S3 Lifecycle issues](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-lifecycle.html)

← Back to the [S3 overview](README.md)
