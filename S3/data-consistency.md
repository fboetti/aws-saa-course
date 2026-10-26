# S3 Data Consistency

## The short version (exam focus)

Since **December 2020**, Amazon S3 provides **strong read-after-write consistency** for *all* requests — new `PUT`s, overwrites, `DELETE`s and `LIST`s — **automatically and at no extra cost**. If a request returns `200 OK`, any immediately following read (by any client, from any AZ in that region) sees the result of that write.

This is the single most common "gotcha" in S3 exam questions: older material (and pre-2020 questions) talks about **eventual consistency**, where a `GET`/`LIST` right after a `PUT` could return stale data and you had to build retry/verification logic. **That model no longer applies to general purpose buckets.**

## Before and after December 2020

| | Old model (eventual) | Current model (strong) |
|---|---|---|
| `GET` after `PUT` (new object) | Might return `404 Not Found` for a while | Immediately returns the new object |
| `GET` after overwrite | Might return the previous version | Immediately returns the new version |
| `GET` after `DELETE` | Might still return the object | Immediately returns `404` |
| `LIST` after `PUT`/`DELETE` | Could miss new keys / show deleted ones | Always reflects the latest state |
| Client-side mitigation | Retry loops, delays, version tracking | Nothing needed — it just works |

## What "strong consistency" covers

- **Write → read**: a `PUT` that succeeds is immediately visible to subsequent `GET`/`HEAD`/`LIST` requests.
- **Overwrite → read**: writing the same key again means every subsequent read gets the *latest* version (never an older one).
- **Delete → read/list**: a successful `DELETE` immediately removes the object from reads and listings.
- **No stale answers**: reads never return a value from before a completed write — there is no window in which an older version can reappear.
- **`LIST` is consistent**: `ListObjectsV2` results match the actual bucket state, including objects created or deleted just before the call.
- **Applies to every object in the bucket**, whatever its storage class, encryption, versioning or Object Lock settings — nothing needs to be reconfigured, and it costs nothing extra. Features that copy or report data *elsewhere* (replication, notifications, Inventory) are the exceptions listed below.
- **Applies across the region**: consistency is guaranteed across all Availability Zones of the bucket's region, for every client (console, CLI, SDK, applications).

## What is *still* eventually consistent (the nuance)

Strong consistency is **per bucket, per region**. Operations that propagate data *elsewhere* remain asynchronous:

| Feature | Consistency behavior |
|---|---|
| **Cross-Region / Same-Region Replication (CRR/SRR)** | **Asynchronous** — the replica appears in the destination bucket seconds later (typically). Reads in the destination can lag the source. |
| **S3 event notifications** | **At-least-once** delivery, *near* real-time — events can arrive slightly late and may be duplicated; consumers must be idempotent. |
| **S3 Batch Operations** | Jobs are processed asynchronously across billions of objects; each object changes when its task completes. |
| **Glacier restores** | Restore is an asynchronous job (minutes to hours depending on the retrieval tier). |
| **S3 Inventory** | A periodic snapshot — not real-time; new objects may not appear until the next report. |
| **Cache/CDN layers in front of S3** | CloudFront or browser caches hold objects until their TTL expires — S3 is consistent, the cache may not be. |
| **Multi-Region architectures** (replication, global tables-style designs) | Any cross-region read path is eventually consistent by construction. |

Directory buckets (**S3 Express One Zone**) have **always been strongly consistent** — they run in a single AZ with a synchronous directory namespace.

## Conditional writes: making concurrent updates safe

Strong consistency guarantees that *reads* see the latest data, but it does **not** stop two writers from racing each other. S3 offers **conditional writes** for that:

- `If-Match: <ETag>` — the write succeeds only if the object currently has that ETag (optimistic locking). If someone else wrote in between, you get **`412 Precondition Failed`** and can re-read and retry.
- `If-None-Match: *` — the write succeeds **only if the object does not exist**; otherwise `412`. This is the "create-if-absent" primitive that prevents the classic lost-update problem.

Since objects are **immutable** (see [Object Overview](objects.md)), the safe update pattern is: `GET` (grab ETag) → modify → conditional `PUT` with `If-Match`. With plain unconditional `PUT`s, the last writer silently wins.

## Design implications

- **No read-after-write retry logic** is needed for a single bucket in one region — a completed upload is immediately usable.
- **Do not use `LIST`-then-`GET` races as a guard**: rely on `GET` returning 404/200 truthfully instead.
- **Distributed systems in the exam**: S3 joins DynamoDB (strongly consistent reads available), Aurora (strongly consistent within the primary) on the "strong consistency" side; SQS/SNS (at-least-once), S3 *replication* and S3 *notifications* remain eventually/at-least-once consistent — question wording about "eventual consistency" for S3 itself is almost always a leftover from the pre-2020 model.
- **When a question insists on eventual consistency for S3**, check whether it actually means: replication, event delivery, or a multi-region setup — those are the only remaining cases.

## References

- AWS What's New — [Amazon S3 now delivers strong read-after-write consistency](https://aws.amazon.com/about-aws/whats-new/2020/12/amazon-s3-now-delivers-strong-read-after-write-consistency/)
- AWS docs — [Strong consistency](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel)
- AWS docs — [Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)
- AWS docs — [S3 event message delivery](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html)

← Back to the [S3 overview](README.md)
