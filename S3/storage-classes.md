# S3 Storage Classes — Deep Dive

Every object in S3 lives in **exactly one storage class**. If you don't specify one on upload, S3 assigns **S3 Standard**. You can set the class per object (`x-amz-storage-class` header on `PutObject`) or automate moves with **lifecycle transitions** — a transition is a server-side copy + delete, not an in-place mutation.

This document goes class by class through the properties that matter: **durability, availability, data redundancy, retrieval time, throughput/scalability, use cases and pricing**. The overview table lives in the [S3 README](README.md#storage-classes).

> Prices are **us-east-1 (N. Virginia) list prices, checked October 2026** — other regions differ, and AWS changes prices (S3 Express was cut by ~31–85% in April 2025). Always verify at [aws.amazon.com/s3/pricing](https://aws.amazon.com/s3/pricing).

## Key Terms

| Term | Meaning |
|---|---|
| **Durability** | Probability that an object is *lost* in a year. S3 is designed for **99.999999999% (eleven 9s)** — i.e. expected loss of 1 object per 10¹¹ stored over a year. A *design target*, not a guarantee about your particular object. |
| **Availability** | Percentage of time the object can actually be *retrieved* over a year (99.99%, 99.9%, 99.5%…). This is what changes between multi-AZ and single-AZ classes. |
| **Data redundancy** | *Where* copies live: synchronously across ≥3 Availability Zones, across devices in one AZ, etc. Redundancy is what *delivers* durability and availability. |
| **Retrieval time** | How fast a `GET` returns data: milliseconds (instant classes) vs minutes/hours (archived classes — a **restore** is required first). |
| **Retrieval fee** | Per-GB charge paid when you *read* data back, on top of the GET request charge. Standard and Intelligent-Tiering have **none**. |
| **Minimum storage duration** | If you delete/overwrite/transition an object before N days, S3 still bills you for the remainder (pro-rated). |
| **Minimum billable object size** | Objects smaller than this are billed as if they were this size (128 KB for the IA and Glacier IR classes). |

## Comparison Tables

### Architecture (durability / availability / redundancy)

| Storage class | Durability | Availability | AZs | Redundancy model |
|---|---|---|---|---|
| **S3 Standard** | 99.999999999% | 99.99% | ≥3 | Sync copies across ≥3 AZs |
| **S3 Standard-IA** | 99.999999999% | 99.9% | ≥3 | Sync copies across ≥3 AZs |
| **S3 Intelligent-Tiering** | 99.999999999% | 99.9% | ≥3 | Sync copies across ≥3 AZs |
| **S3 One Zone-IA** | 99.999999999% | **99.5%** | **1** | Multiple devices in a single AZ |
| **S3 Express One Zone** | 99.999999999% | 99.95% | **1** | Multiple devices in a single AZ (directory bucket) |
| **S3 Glacier Instant Retrieval** | 99.999999999% | 99.9% | ≥3 | Sync copies across ≥3 AZs |
| **S3 Glacier Flexible Retrieval** | 99.999999999% | 99.99%¹ | ≥3 | Sync copies across ≥3 AZs |
| **S3 Glacier Deep Archive** | 99.999999999% | 99.99%¹ | ≥3 | Sync copies across ≥3 AZs |

¹ Availability applies **after** the object has been restored — while archived, it isn't retrievable at all.
All classes except **One Zone-IA** and **Express One Zone** are resilient to the loss of an entire AZ. *(Legacy `REDUCED_REDUNDANCY` — 99.9% durability, "annual expected loss of 0.01% of objects" — exists but AWS explicitly says not to use it.)*

### Access & billing

| Storage class | Retrieval time | Retrieval fee (per GB) | Min duration | Min billable size | Storage (per GB-mo) | Write req. (per 1k) | Read req. (per 1k) |
|---|---|---|---|---|---|---|---|
| **S3 Standard** | milliseconds | **none** | none | none | $0.023² | $0.005 | $0.0004 |
| **S3 Standard-IA** | milliseconds | $0.01 | 30 days | 128 KB | $0.0125 | $0.01 | $0.001 |
| **S3 Intelligent-Tiering** | ms (auto tiers) | **none**³ | none | none⁴ | $0.023 / $0.0125 / $0.004 / $0.0036 / $0.00099⁵ | $0.005 | $0.0004 |
| **S3 One Zone-IA** | milliseconds | $0.01 | 30 days | 128 KB | $0.01 | $0.01 | $0.001 |
| **S3 Express One Zone** | single-digit ms | none (small data charge on requests)⁶ | none | none | $0.11 | $0.00113 | $0.00003 |
| **S3 Glacier Instant Retrieval** | milliseconds | $0.03 | 90 days | 128 KB | $0.004 | $0.02 | $0.01 |
| **S3 Glacier Flexible Retrieval** | 1 min – 12 h (restore) | $0.03 expedited / $0.01 standard / **free bulk** | 90 days | 40 KB metadata⁷ | $0.0036 | $0.03 | $0.0004⁸ |
| **S3 Glacier Deep Archive** | 12 h (standard) / 48 h (bulk) | $0.02 standard / $0.0025 bulk | **180 days** | 40 KB metadata⁷ | $0.00099 | $0.05 | $0.0004⁸ |

² Tiered: $0.023 (first 50 TB) → $0.022 (next 450 TB) → $0.021 (over 500 TB); the Intelligent-Tiering Frequent tier follows the same tiers.
³ Standard and bulk restores are free across **all five** IT tiers; expedited retrievals from the optional Archive Access tier are charged.
⁴ Objects <128 KB are **not monitored**, stay in the Frequent tier forever, and pay no monitoring fee.
⁵ IT tiers: Frequent $0.023 / Infrequent $0.0125 / Archive Instant $0.004 (automatic) + Archive $0.0036 / Deep Archive $0.00099 (optional) — plus **$0.0025 per 1,000 objects/month** monitoring fee for objects >128 KB.
⁶ Express adds a small per-GB data component to requests (≈$0.0032/GB written, ≈$0.0006/GB read).
⁷ Glacier FR/DA have no *object* minimum, but each archived object carries **40 KB of metadata**: 8 KB billed at S3 Standard rate + 32 KB at the class rate (keeps LIST/Inventory working in real time).
⁸ GETs on **restored** copies — the restored copy is stored (and billed) at **S3 Standard rates** for the restore duration you choose.

**Common to all classes:** inbound data transfer is free; `DELETE`/`CANCEL` requests are free; `LIST` is always charged at the S3 Standard write rate ($0.005/1k) regardless of class; data out to the internet is $0.09/GB (first 100 GB/month free); out to **CloudFront is free**. And every class shares the same **11-nines durability** design target — you never trade durability for price, only availability, latency and access cost.

---

## 1. S3 Standard — the default

The benchmark class; everything else is a trade-off against it.

- **Durability**: 99.999999999%. **Availability**: 99.99% (highest together with Glacier FR/DA).
- **Data redundancy**: object copied synchronously across a minimum of **3 Availability Zones**, on multiple devices — survives AZ loss and disasters.
- **Retrieval time**: milliseconds, on-demand, no restore.
- **Throughput / scalability**: automatically scales to sustained **3,500 write / 5,500 read requests per second per prefix**; add more prefixes to scale further (no limit on prefix count). Multipart upload for large objects; Transfer Acceleration available.
- **Use cases**: anything accessed **more than once a month** — websites, dynamic apps, active content, big data/analytics input, the "primary copy" of data you can't afford to wait for.
- **Pricing model** (the only class with *no* extra fees of any kind):
  - **Storage per GB-month**, tiered: $0.023 / $0.022 / $0.021.
  - **Per requests**: $0.005 per 1k writes (PUT/COPY/POST/LIST), $0.0004 per 1k reads.
  - **No retrieval fee, no minimum storage duration, no minimum object size.**

## 2. S3 Standard-IA (Infrequent Access)

"Same as Standard, but cheaper to hold and more expensive to touch."

- **Durability**: 11 nines; **Availability**: 99.9% (one nine less than Standard — same multi-AZ design, priced lower).
- **Data redundancy**: identical to Standard — sync copies across **≥3 AZs**, resilient to AZ loss. Use it for the *primary* copy of data that can't be re-created.
- **Retrieval time**: milliseconds — but every GB retrieved costs **$0.01**, which is the whole point of the class.
- **Throughput / scalability**: same per-prefix scaling as Standard (3,500 w / 5,500 r per second per prefix).
- **Use cases**: backups, old records, secondary datasets accessed **about once a month** that still need instant reads; typically fed by a lifecycle rule from Standard.
- **Pricing**: $0.0125/GB-month (≈46% cheaper than Standard) + requests $0.01 write / $0.001 read per 1k (2–2.5× Standard) + **$0.01/GB retrieval** + lifecycle **transition-in $0.01 per 1k objects**. Minimums: **30 days** storage, **128 KB** per object.
- **Cost trap**: the class only wins if access is rare. Each extra read costs 25× a Standard GET in request+retrieval terms; accessed weekly, it can end up *more* expensive than Standard.

## 3. S3 One Zone-IA

"The cheap copy — one AZ only."

- **Durability**: 11 nines (same design target — data is still spread over multiple devices). **Availability**: **99.5%** — the lowest of all classes.
- **Data redundancy**: stored in a **single Availability Zone** — *not* resilient to AZ loss (flood, earthquake, AZ-level outage). 20% cheaper than Standard-IA precisely because of this.
- **Retrieval time**: milliseconds, with the same **$0.01/GB** retrieval fee.
- **Throughput / scalability**: same per-prefix scaling as Standard.
- **Use cases**: data you can **re-create** if the AZ dies (regenerable datasets, build artifacts), **replication targets** (e.g. CRR copies of a Standard original), secondary copies, data-residency/isolation workloads in Local Zones. Never your only copy of irreplaceable data.
- **Pricing**: $0.01/GB-month, requests $0.01 write / $0.001 read per 1k, retrieval $0.01/GB, transition-in $0.01/1k. Minimums: **30 days**, **128 KB**.

## 4. S3 Intelligent-Tiering

"The one class that optimizes itself — no rules, no guessing."

- **Durability**: 11 nines; **Availability**: 99.9%; **Redundancy**: ≥3 AZs — identical architecture to Standard, so access performance is identical too.
- **Access tiers** (automatic, per object, no performance impact):
  | Tier | Moves after | Storage/GB-mo | Access |
  |---|---|---|---|
  | Frequent Access | upload/transition | $0.023 | milliseconds |
  | Infrequent Access | 30 days untouched | $0.0125 | milliseconds |
  | Archive Instant Access | 90 days untouched | $0.004 | milliseconds |
  | Archive Access *(opt-in)* | 90+ days untouched | $0.0036 | restore, minutes–hours |
  | Deep Archive Access *(opt-in)* | 180+ days untouched | $0.00099 | restore, 12–48 h |
- **Retrieval time**: milliseconds for the three automatic tiers, **with no retrieval fees** (standard/bulk restores free on all five tiers). Only the two optional archive tiers need a `RestoreObject`.
- **Throughput / scalability**: same as Standard; caveat — per-object monitoring makes it a poor fit for **billions of tiny objects** (and objects <128 KB can't tier at all: they sit in Frequent forever at Standard prices).
- **Use cases**: **unknown or changing access patterns** — data lakes, user-generated content, mixed archives, anything you'd otherwise over-engineer with lifecycle rules. Migrating "stuff I might need" is the canonical answer.
- **Pricing**: per-GB-month of whichever tier the object sits in + **monitoring & automation fee $0.0025 per 1,000 objects/month** (>128 KB) + Standard-rate requests ($0.005/$0.0004 per 1k) + transition-in $0.01/1k. **No minimum duration, no minimum object size, no retrieval fees.**

## 5. S3 Express One Zone

"The fast one — a different bucket type entirely."

- **Durability**: 11 nines. **Availability**: 99.95% (single-AZ, but priced and engineered for it). **Redundancy**: multiple devices inside the **one AZ you choose** — pairs with compute in the same AZ for data locality.
- **Retrieval time**: **single-digit milliseconds, consistently** (up to 10× faster than Standard's typical 20–100 ms first byte). Requires **[directory buckets](bucket-types.md)** — a true directory namespace with **zonal endpoints** (`<bucket>--<az-id>--x-s3.s3express-<az-id>.<region>.amazonaws.com`), virtual-hosted style only, session-based auth (`CreateSession`).
- **Throughput / scalability**: purpose-built for sustained high request rates with *predictable* latency (Standard's strength is scale, Express's is *consistency*); supports `RenameObject`, and its request prices are far below Standard's (storage is far above).
- **Use cases**: latency-sensitive workloads — real-time analytics, ML training/inference, ad-tech bidding, financial trading, interactive dashboards, pick-heavy pipelines.
- **Pricing**: storage **$0.11/GB-month** (~5× Standard — you pay for speed), requests **$0.00113/1k writes, $0.00003/1k reads** (after the April 2025 cut) plus a small per-GB data component (≈$0.0032 written, ≈$0.0006 read). No minimums, no retrieval fee, no lifecycle transitions (a directory bucket only holds Express objects).

## 6. S3 Glacier Instant Retrieval

"Archive pricing, Standard access." For data read rarely (about once per quarter) that must still be available immediately.

> Like the other two Glacier classes, this is an **S3 storage class**, not a separate service: objects live in your normal bucket, no vault required.

- **Durability**: 11 nines. **Availability**: 99.9%. **Redundancy**: **≥3 AZs** — same protection as Standard.
- **Retrieval time**: **milliseconds** — no restore needed, the object is immediately readable, but each GB read costs **$0.03**.
- **Throughput / scalability**: standard S3 request-rate scaling (3,500 w / 5,500 r per prefix), high-throughput reads like Standard.
- **Use cases**: long-lived data **accessed about once a quarter** that must respond instantly when touched — medical imaging, media/photo archives, broadcast footage, compliance records.
- **Pricing**: **$0.004/GB-month** (83% cheaper than Standard) + requests $0.02 write / $0.01 read per 1k (the most expensive reads of any instant class) + **retrieval $0.03/GB** + transition-in $0.02/1k. Minimums: **90 days**, **128 KB**.
- **Rule of thumb**: if you never pay the retrieval fee (≤ quarterly access), it's a bargain; read it monthly and Standard wins.

## 7. S3 Glacier Flexible Retrieval (formerly S3 Glacier)

"Cheapest to hold, slow (but free in bulk) to get back."

- **Durability**: 11 nines. **Availability**: 99.99% *after restore*. **Redundancy**: ≥3 AZs.
- **Retrieval time**: objects are **archived — not readable until restored**:
  | Option | Time | Data cost/GB |
  |---|---|---|
  | Expedited | 1–5 minutes | $0.03 |
  | Standard | 3–5 hours | $0.01 |
  | **Bulk** | 5–12 hours | **free** |
  Restore requests are billed per 1,000 (bulk restores: requests free too). The restored **copy is stored at S3 Standard rates** for the duration you pick, on top of the still-charged archive storage.
- **Throughput / scalability**: bulk restores are throughput-optimized and free — the standard pattern for large backfills. For guaranteed fast access, buy **provisioned capacity units** (≥3 expedited retrievals every 5 min, up to **150 MB/s** of retrieval throughput each, per month).
- **Use cases**: archives accessed **once or twice a year** where retrieval sometimes must happen in minutes — backups, log archives, research data, DR copies.
- **Pricing**: **$0.0036/GB-month** + write requests **$0.03/1k** (10× Standard — design for *few, large* objects) + free bulk retrieval / paid expedited & standard + transition-in **$0.03/1k**. Minimum duration **90 days**; no object minimum, but the **40 KB per-object metadata** overhead (8 KB Standard rate + 32 KB FR rate). Because of the per-object overhead and request prices, archive **fewer, larger objects** (e.g. tar/zip many small files together) rather than millions of small ones.

## 8. S3 Glacier Deep Archive

"The cheapest storage AWS sells — tape replacement."

- **Durability**: 11 nines. **Availability**: 99.99% *after restore*. **Redundancy**: ≥3 AZs.
- **Retrieval time**: restore required; **Standard: 12 hours ($0.02/GB)**, **Bulk: 48 hours ($0.0025/GB)** — no expedited option. Same "restored copy billed at Standard rates" rule.
- **Throughput / scalability**: built for bulk restores of entire datasets, not latency; huge write-request cost per object favors large, consolidated archives.
- **Use cases**: data retained **7–10+ years**, regulatory/compliance retention, records accessed **less than once a year**, tape-library archives migrating off magnetic tape.
- **Pricing**: **$0.00099/GB-month** (≈$1/TB/month — 23× cheaper than Standard) + write requests **$0.05/1k** (the most expensive in S3) + reads $0.0004/1k after restore + transition-in **$0.05/1k** (10M objects → **$500 just to move them in**). Minimum duration **180 days** — deleting early still bills the pro-rated remainder; 40 KB metadata overhead like Glacier FR.

> **Lineage — the old Glacier vault service**: Flexible Retrieval and Deep Archive descend from **Amazon Glacier** (launched 2012), a *separate* service whose containers were **vaults** — not buckets — with their own API, vault access policies and **Vault Lock** (WORM), where every upload was an *archive* that stayed unreadable until restored. AWS then exposed the same storage inside S3 as storage classes (the class called "S3 Glacier", plus Deep Archive in 2019), and in the **November 2021 reorganization** renamed the class to **S3 Glacier Flexible Retrieval** and launched **Glacier Instant Retrieval** alongside it. The original vault-based service still exists separately (AWS stopped onboarding new customers to it in 2025). The DNA shows in both classes: restore-before-read, the **expedited/standard/bulk** tiers and per-archive billing. Exam hint: "vault" wording (vaults, Vault Lock, vault access policies) points at the **standalone Glacier service**, while Flexible Retrieval and Deep Archive are ordinary S3 objects in your bucket that merely need a `RestoreObject` first.

---

## Pricing Mechanics Common to Every Class

1. **Storage** — per GB-month of actual data (tiered for Standard/IT Frequent).
2. **Requests** — per 1,000; writes cost far more than reads, and write prices **rise sharply** for colder classes ($0.005 Standard → $0.05 Deep Archive).
3. **Retrieval** — per GB read back, only on IA/One Zone-IA/Glacier classes (and restore tiers); **Standard, Intelligent-Tiering and (nearly) Express have none**.
4. **Minimum storage durations** — 30 days (IA classes) / 90 days (Glacier IR, FR) / 180 days (Deep Archive): early delete, overwrite or transition ⇒ pro-rated charge for the remainder.
5. **Minimum billable size** — 128 KB for Standard-IA, One Zone-IA, Glacier IR (tiny-object math changes drastically).
6. **Lifecycle transitions (ingest)** — per 1,000 objects moved *into* a class: **$0.01** (IA, IT), **$0.02** (Glacier IR), **$0.03** (Glacier FR), **$0.05** (Deep Archive). Object *count*, not size, drives this.
7. **Monitoring** — Intelligent-Tiering only: $0.0025 per 1,000 objects/month (>128 KB).
8. **Data transfer** — out to internet $0.09/GB after 100 GB/month free; free inbound; free to CloudFront; **VPC gateway endpoint** access to S3 is free of data-processing charges.

**Worked example (why object count matters):** 10 M small objects (50 KB each) in Deep Archive = 500 GB × $0.00099 ≈ **$0.50/month of storage**. On top of that, the 40 KB metadata overhead per object adds 80 GB at Standard rates (≈ $1.84) + 320 GB at Deep Archive rates (≈ $0.32) **every month** — already 4× the data itself. And getting them in costs **$500 once**, whether by lifecycle transition ($0.05 per 1k objects) or by direct PUT ($0.05 per 1k writes). Fixed per-object costs, not bytes, dominate cold-storage migrations of tiny files — which is also why lifecycle no longer transitions objects < 128 KB by default. Bundle small files into larger archives first.

## Throughput & Scalability (all classes)

- S3 **automatically scales** request rates — no pre-provisioning, no quota requests.
- Documented sustained rates **per prefix**: **3,500** PUT/COPY/POST/DELETE and **5,500** GET/HEAD requests/second. There is **no limit on the number of prefixes**, so throughput scales linearly with them: 10 prefixes read in parallel ≈ 55,000 GET/s. Key names no longer need random hashes (that was pre-2018 advice) — any distinct prefixes work, e.g. by date or tenant.
- **Multipart upload**: required >5 GB, recommended >100 MB — parallel parts raise effective throughput and allow resume.
- **Transfer Acceleration**: uploads via CloudFront edge locations (virtual-hosted endpoint, extra cost).
- **Archive restores**: bulk = free & throughput-optimized; provisioned capacity units buy expedited throughput (150 MB/s each).
- **Express One Zone**: optimizes *latency consistency* rather than raw request count; colocating compute in the same AZ removes cross-AZ transfer too.

## Exam Takeaways

- **Durability is always 11 nines** — you pay for *availability, latency and access*, never durability.
- **Standard vs Standard-IA**: both multi-AZ, ms access; Standard = no fees at all, IA = cheaper storage but $0.01/GB retrieval + 30-day/128 KB minimums. Use IA for access ≤ ~once/month.
- **One Zone-IA**: single AZ, **99.5% availability**, cheapest "real" class at $0.01/GB — only for **re-creatable** data or replication targets.
- **Intelligent-Tiering**: pay a monitoring fee, **never a retrieval fee** — the answer for "unknown/changing access patterns".
- **Glacier Instant Retrieval**: ms access at $0.004/GB but $0.03/GB per read, 90-day minimum — quarterly-access data.
- **Glacier Flexible Retrieval**: restore first (1–5 min expedited to 12 h bulk); **bulk retrieval is free** — the usual "cheap archive with occasional needs" answer.
- **Glacier Deep Archive**: cheapest ($0.00099/GB), **12–48 h**, **180-day minimum**, $0.05/1k writes — compliance/7–10-year retention.
- **Express One Zone**: single-digit ms, single AZ, ~5× the storage price — latency-sensitive analytics/ML, not general storage.
- Watch **minimum durations and transition fees**: they are the classic exam "gotcha" (delete an archive at day 30 ⇒ still pay to day 180).
- Retrieval **time** vs retrieval **price** are independent: IR is fast *and* charges per GB; bulk Glacier is slow *and* free.

## References

- Storage classes overview (AWS docs): https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
- S3 pricing (official, per region): https://aws.amazon.com/s3/pricing/
- S3 storage classes (product page): https://aws.amazon.com/s3/storage-classes/
- Understanding S3 Glacier storage classes: https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html
- S3 Intelligent-Tiering deep dive: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
- Scaling request rates (prefixes): https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html

← Back to the [S3 overview](README.md)
