# S3 Bucket Types — General Purpose vs Directory Buckets

S3 has **two types of buckets**, introduced at re:Invent 2023:

1. **General purpose buckets** — the original bucket type, with the classic *flat* namespace.
2. **Directory buckets** — the new bucket type, used exclusively with the **S3 Express One Zone** storage class.

The bucket type is chosen at creation time and **cannot be changed afterwards**.

## General Purpose Buckets (flat hierarchy)

General purpose buckets are what the course mostly refers to when it says "S3 bucket". They:

- Use a **flat key namespace** — there is no real directory tree, just keys like `photos/2026/cat.png`.
- Support **every storage class** *except* S3 Express One Zone (Standard, IA tiers, Intelligent-Tiering, all Glacier classes…).
- Store data redundantly across a **minimum of three Availability Zones** (regional service).
- Have names in the **global namespace** (globally unique across all accounts/regions — see [Bucket Naming Rules](bucket-naming-rules.md)).

### Folders are zero-byte objects

Because the hierarchy is flat, what the console shows as "folders" are actually **prefixes inside object keys** — and a folder you create in the console is a real object of **0 bytes** whose key ends with a `/`:

```
photos/                    ← actual object, 0 bytes, key = "photos/"
photos/2026/               ← actual object, 0 bytes, key = "photos/2026/"
photos/2026/cat.png        ← actual object, 340 KB, key = "photos/2026/cat.png"
```

S3 does not create or manage these marker objects automatically — uploading `photos/2026/cat.png` alone would make the console *display* the folders even though no marker objects exist. They exist mainly so the folder can be shared/empty and still show up.

### Moving an object = renaming its key

Since there are no real locations to move between, "moving" an object into a folder is **nothing but a change of its key** — the data itself doesn't need to go anywhere. Under the hood S3 implements a move (or a rename) as **CopyObject + DeleteObject**: a new object with the new key is created and the old one is deleted. Consequences worth remembering for the exam:

- A "move" is actually a **new object**: its ETag changes, and with versioning enabled you end up with new versions (the old one gets a delete marker).
- A move across storage classes/buckets is also just a copy — so it may incur **retrieval fees** (e.g. from Glacier) and is a billable `PUT` request.
- A **lifecycle rule can change an object's "location"** by transitioning it to another storage class — again, only its metadata/storage class changes, the key stays the same.

## Directory Buckets (S3 Express One Zone)

Directory buckets are the bucket type behind the **S3 Express One Zone** storage class — the first S3 storage class designed for **consistent single-digit millisecond latency**. Unlike the flat namespace of general purpose buckets, directory buckets organize objects into a **real hierarchical namespace**, like a file system:

- Keys are stored in **directories**, not prefixes. When you upload `dir1/dir2/file1.txt`, the directories `dir1/` and `dir2/` are **created automatically** by S3 and are **deleted automatically when they become empty** (after a delete or an aborted multipart upload) — no zero-byte marker objects needed.
- `/` is the only allowed delimiter, and `ListObjectsV2` doesn't return keys in lexicographical order.
- No prefix limits; each directory scales horizontally and can handle the bucket's full request rate (up to **2,000,000 GET / 200,000 PUT TPS per bucket**), so there's no need to randomize key prefixes for performance.
- Data is stored redundantly on multiple devices, but in a **single Availability Zone** — designed for **99.95% availability** within that AZ. During AZ creation you must acknowledge that an AZ outage can mean data unavailability or loss.
- You pick the AZ to **co-locate storage with your compute** (EC2/EKS/ECS) for the fastest possible access. Also supported in **AWS Local Zones**.
- **S3 Express One Zone is only available in directory buckets** — you can't store Express objects in a general purpose bucket, and a directory bucket can only hold Express One Zone objects.

### Naming

Directory bucket names must be **unique only within the chosen AZ**, and must include a mandatory suffix with the zone ID:

```
bucket-base-name--usw2-az1--x-s3
\______base______/ \__zone__/
```

- 3–63 characters, only lowercase letters, numbers and hyphens (**no dots**).
- Must end with `--<zone-id>--x-s3` (added automatically by the console; you must include it when using an API).
- The same reserved prefixes as general purpose buckets (`xn--`, `sthree-`, `amzn-s3-demo-`) and reserved suffixes (`-s3alias`, `--ol-s3`, `.mrap`).

### Not supported in directory buckets

Many well-known S3 features simply don't exist for directory buckets — a frequent exam trap:

- **Versioning**, **replication**, **Object Lock**, **MFA delete**
- **ACLs** (always disabled; access is defined by policies only) and **Block Public Access is always on** and can't be relaxed
- **Lifecycle transition actions**, **S3 Select**, **Object tags**
- **S3 Event Notifications**, **Storage Lens**, **Requester Pays**, **Access Grants**
- **Static website hosting**, **Transfer Acceleration**, **Multi-Region Access Points**, **Object Lambda**, **PrivateLink for S3**
- **SSE-C** and **DSSE-KMS** — encryption is **SSE-S3 by default**, with optional **SSE-KMS using a single customer managed key per bucket** (bucket keys always enabled)
- `s3 sync` in the CLI (use `s3 cp --recursive` instead)

Endpoints are different too: bucket management (CreateBucket, DeleteBucket…) goes through **Regional endpoints** (`s3express-control.<region>.amazonaws.com`), while object operations use **Zonal endpoints** that include the AZ (`s3express-usw2-az1.us-west-2.amazonaws.com`) and require a `CreateSession` IAM call first.

## Comparison Table

| | **General purpose bucket** | **Directory bucket** |
|---|---|---|
| Namespace | **Flat** (prefixes simulate folders; folders = 0-byte objects) | **Hierarchical** (real directories, auto-created/removed) |
| Storage classes | All except S3 Express One Zone | **S3 Express One Zone only** |
| Redundancy | ≥3 Availability Zones | Single AZ (multiple devices) |
| Latency | milliseconds | **consistent single-digit milliseconds** |
| Availability design | 99.99% | 99.95% within the AZ |
| Name uniqueness | **Global** namespace | Within the AZ only |
| Name format | free-form (see naming rules) | `base--zone-id--x-s3` |
| Versioning / replication / Object Lock | yes | no |
| Event notifications | yes | no |
| ACLs | legacy, off by default | never supported |
| Static website hosting | yes | no |
| Typical use case | general purpose, archives, static sites, backups | latency-sensitive, high-throughput workloads (real-time analytics, ML training, media processing, high-frequency data pipelines) |

## Which one should you pick?

- **General purpose bucket** — recommended for *most* use cases and access patterns; it's the default answer unless a question explicitly mentions latency sensitivity, high request rates with consistent performance, or S3 Express One Zone.
- **Directory bucket** — only when your application is performance-critical and benefits from single-digit millisecond, consistent latency and you want to co-locate storage and compute in one AZ (at the cost of single-AZ resilience).

## References

- AWS docs — [Differences for directory buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-differences.html)
- AWS docs — [Directory bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-naming-rules.html)
- AWS blog — [S3 Express One Zone supports KMS with customer managed keys](https://aws.amazon.com/blogs/aws/amazon-s3-express-one-zone-now-supports-aws-kms-with-customer-managed-keys/)

← Back to the [S3 overview](README.md)
