# S3 Security Overview

Security in S3 is **layered**: no single setting protects a bucket, several controls overlap and *stack*, and for the SAA exam you are usually asked which layer the question is really about (identity? network? data at rest? data in transit? compliance?).

## Table of contents

- [General introduction](#general-introduction)
- [Bucket policies](#bucket-policies)
- [ACLs](#acls)
- [Object Ownership](#object-ownership)
- [Block Public Access](#block-public-access)
- [IAM Access Analyzer for S3](#iam-access-analyzer-for-s3)
- **[Access Points](#access-points)** / **[Object Lambda Access Points](#object-lambda-access-points)**
- [Access Grants](#access-grants)
- [PrivateLink for Amazon S3](#privatelink-for-amazon-s3)
- [Internetwork traffic privacy](#internetwork-traffic-privacy)
- [CORS](#cors)
- [In-transit encryption](#in-transit-encryption)
- [Server-side encryption](#server-side-encryption)
- [Client-side encryption](#client-side-encryption)
- [Versioning](#versioning)
- [MFA Delete](#mfa-delete)
- [Object tags](#object-tags)
- [Compliance validation](#compliance-validation)
- [Infrastructure security](#infrastructure-security)
- [How the layers fit together](#how-the-layers-fit-together)
- [Exam cheat sheet](#exam-cheat-sheet)

---

## General introduction

**Amazon S3** is a regional, multi-tenant object store: data lives in buckets, addressed by bucket name + object key, and is reachable over the network through REST endpoints. That has three consequences that drive every security feature:

1. **Access is always network access.** Whoever can reach the endpoint and present valid credentials can attempt a request. So S3 security = *authentication/authorization* (who) + *transport/network* (how the request travels) + *encryption* (what's stored) + *governance* (how it's kept that way).
2. **The bucket is the security boundary.** Almost every control (policy, ACLs, Block Public Access, CORS, default encryption, versioning, logging) is configured at **bucket** level and only secondarily at **object** level.
3. **Defaults are now secure.** New buckets get **ACLs disabled** (Object Ownership = *bucket owner enforced*) and **Block Public Access enabled** — and since January 2023 every new object is encrypted at rest by default (SSE-S3). Most "make it public" exam traps require someone to *deliberately turn these off*.

A useful mental model is the request path. A request to S3 passes through, in order:

```
client → TLS (in-transit encryption) → endpoint (public / VPC endpoint / PrivateLink)
       → Block Public Access        → authentication (SigV4: IAM / resource policy)
       → authorization evaluation (explicit Deny > Allow; IAM + bucket policy + ACL + session policies)
       → default encryption (at rest) → object stored / returned
```

Each stage below maps to one or more of the topics in this document.

---

## Bucket policies

A **bucket policy** is a **resource-based policy** attached to the bucket (and optionally its objects). It is plain JSON in the IAM policy language and is managed with `PutBucketPolicy` / `GetBucketPolicy`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"],
      "Condition": { "Bool": { "aws:SecureTransport": "false" } }
    }
  ]
}
```

Key properties:

| Aspect | Detail |
|---|---|
| **Scope** | The bucket ARN (`arn:aws:s3:::bucket`) and/or object ARNs (`arn:aws:s3:::bucket/key-or/prefix/*`) — so a single statement can cover many objects. |
| **Principals** | Any principal: the account's own identities, **another AWS account**, an AWS service (`Principal: { "Service": "cloudtrail.amazonaws.com" }`), or `*` (everyone = "public"). |
| **Size limit** | Bucket policies are limited to **20 KB** (keep them for coarse, cross-account and deny rules). |
| **Evaluation** | An explicit **`Deny` always wins** over any `Allow` (from any policy, anywhere). Otherwise: identity policy **OR** resource policy can allow; for **cross-account** access *both* the identity policy in the caller's account and the bucket policy must allow. |
| **Conditions** | Rich keys: `aws:SecureTransport`, `aws:TLSVersion`, `aws:SourceIp`, `aws:SourceArn`/`aws:SourceAccount` (confused-deputy protection), `aws:PrincipalOrgID`, `aws:SourceVpc`/`aws:SourceVpce`, `s3:prefix`, `s3:x-amz-acl`, `s3:ResourceTag`/`aws:RequestTag`. |
| **Not for** | Granting a *principal* broad rights — that's an IAM policy. Bucket policies say *what may happen to this resource*; IAM policies say *what this identity may do*. |

Typical exam uses:

- **Enforce HTTPS** — deny when `aws:SecureTransport` is `false`.
- **Enforce encryption** — deny `s3:PutObject` when `Null: {"s3:x-amz-server-side-encryption": "true"}` or when the value is not the required one.
- **Cross-account sharing** — allow a specific account ARN; remember the *other* side needs an identity policy too (unless it's the bucket-owner-full-control pattern / access point policy).
- **Service access** — allow CloudTrail, Config, backup services via `Principal.Service` + `SourceArn`/`SourceAccount`.
- **Restrict by source** — VPC-only (`aws:SourceVpc`/`aws:SourceVpce`), IP ranges, or organization (`aws:PrincipalOrgID`).
- **Deny deletion** — deny `s3:DeleteBucket` to protect critical buckets.

> Exam pattern: "users must not be able to access the bucket over HTTP" → bucket policy + `aws:SecureTransport`. "Applications must encrypt on upload" → bucket policy condition (belt) **and/or** default encryption (braces).

---

## ACLs

**Access Control Lists** are the *legacy* authorization mechanism: a list of **grants** (grantee + permission) stored on the bucket or on an individual object.

- Grantees are **canonical user IDs, AWS e-mail/groups (legacy), or predefined groups** (`AllUsers` = anyone on the internet, `AuthenticatedUsers` = any AWS authenticated user). ACLs **cannot reference IAM users/roles by name** — only those coarse grantees — which is why they were replaced by policies.
- Permissions are limited to `READ`, `WRITE`, `READ_ACP`, `WRITE_ACP`, `FULL_CONTROL`.
- **Bucket ACL** governs the bucket itself (e.g. allow `Write` to upload into the bucket); **object ACL** governs that one object.
- ACLs are evaluated **in addition to** IAM/bucket policies, but policies win: an ACL can only *grant*, and an explicit `Deny` anywhere (bucket policy, IAM policy, session policy) blocks the request regardless of what the ACL says.
- **Object Ownership = bucket owner enforced** (the default since April 2023) **disables ACLs entirely** — all objects belong to the bucket owner, and any request that tries to set/modify an ACL fails.
- **Directory buckets (S3 Express One Zone) never support ACLs.**
- If you must migrate an ACL-based workload: use **S3 Batch Operations** to rewrite grants, or simply disable ACLs and move to bucket policies.
- When **Block Public Access** is on, ACLs that would make things public are rejected (`BlockPublicAcls`) or silently ignored (`IgnorePublicAcls`).

**Verdict (exam):** ACLs = **avoid**. Prefer bucket policies / IAM policies / access points. If a question mentions ACLs alongside a modern control, the modern control is usually the answer — *unless* the question explicitly says "legacy ACL-based application" or "object-level permissions for a specific object uploaded by another account".

---

## Object Ownership

**Object Ownership** is the bucket-level setting that decides *who owns objects* and *whether ACLs are used at all*. Console → bucket → Permissions → Object Ownership:

| Setting | ACLs | Ownership of objects | Notes |
|---|---|---|---|
| **Bucket owner enforced** (default for new buckets) | **Disabled** | Always the **bucket owner**, regardless of who uploaded | Recommended; removes the whole "someone else uploaded it, now the bucket owner can't read it" class of problems. |
| **Bucket owner preferred** | Enabled | Bucket owner, *if* the uploader grants `FULL_CONTROL` to it (ACL `bucket-owner-full-control`) | Legacy cooperative mode for cross-account uploads. |
| **Object writer** | Enabled | The **object uploader** | Original S3 behaviour; needed only when the uploader must retain control of its own objects. |

Why it matters for security:

- It is the **master switch for ACLs** — "ACLs disabled" and "Object Ownership: bucket owner enforced" are the same statement.
- It removes cross-account ownership confusion (a shared bucket where the bucket owner gets `AccessDenied` on objects written by another account).
- **Directory buckets only support bucket owner enforced.**
- It is one of the defaults that make "accidental public exposure via ACL" impossible on new buckets.

---

## Block Public Access

**S3 Block Public Access (BPA)** is a set of four **guardrails that override any policy or ACL** that would make a bucket or its objects public:

| Setting | Effect |
|---|---|
| **Block public ACLs** | Rejects requests that try to attach an ACL with public access (`public-read`/`public-read-write`) to a bucket or object. |
| **Ignore public ACLs** | Treats all existing public ACLs as private — they are not evaluated. |
| **Block public bucket policies** | Rejects (`PutBucketPolicy`) any bucket policy that contains a statement granting public access. |
| **Restrict public buckets** | Ignores existing public bucket-policy statements: access to such buckets is limited to AWS service principals and authorized users **within the account**. |

- Can be set **per bucket** and **per account**. **Account-level settings always win** — if the account blocks, you cannot re-enable it on an individual bucket.
- New buckets get **all four enabled**; accounts created since April 2023 have the account-level settings on by default.
- "Public" here means a principal that is not an AWS-account principal (`Principal: *` combined with anonymous access, or ACL grantees `AllUsers`/`AuthenticatedUsers`).
- It **does not** replace authorization: it only neutralizes *public* grants. Cross-account grants, VPC endpoint restrictions, IAM etc. still apply normally.
- Turning BPA **off** is a deliberate act — the console warns you. For a static website you typically disable it *and* explicitly allow `s3:GetObject` for everyone — that's the intended exception.
- Access points have their own BPA configuration too (and account-level BPA applies to them).

**Typical exam question:** "The bucket was exposed publicly — how do you guarantee it can never happen again?" → enable **Block Public Access at the account level** (plus `BlockPublicPolicy`), not just fix the policy.

---

## IAM Access Analyzer for S3

**IAM Access Analyzer** (an IAM feature, no extra charge) continuously reviews S3 buckets and flags **external access** — access granted to anyone *outside* the bucket's account:

- Detects buckets shared with **other AWS accounts**, **public** buckets (policy- or ACL-based), and access granted to AWS services/roles outside the account.
- Produces **findings** in the console/API listing *who* has access and *which statement* grants it; findings can be **archived** (with an expiry, e.g. 90 days) when the access is intended.
- **One-click remediation**: from a finding you can review the policy and enable Block Public Access / remove the statement.
- Analyzes both **bucket policies and ACLs**, and complements Access Analyzer's other features — notably **policy generation**, which builds a least-privilege IAM policy for S3 from observed CloudTrail activity.
- Works across **all buckets in the account (all regions)** — this is the tool for "find every bucket that is not private" audits; pair it with **S3 Storage Lens** (security metrics, `buckets with public access` etc.), **AWS Config** (`s3-bucket-public-read-prohibited`, `s3-bucket-public-write-prohibited`, `s3-bucket-level-public-access-prohibited`, `s3-default-encryption-enabled`) and **Amazon Macie** (sensitive-data discovery in buckets).

**Exam mapping:** "identify buckets that are shared externally / publicly accessible" → **IAM Access Analyzer for S3**. "Automated sensitive-data discovery" → **Macie**. "Conformance checks in AWS" → **Config**.

---

## Access Points

An **S3 access point** is a **named endpoint with its own resource policy**, attached to a bucket. Instead of one bucket policy that must describe every application sharing the bucket, each application gets its own access point (and its own policy) pointing at the same bucket.

- ARN format: `arn:aws:s3:us-east-1:111122223333:accesspoint/my-app` — requests use the access point hostname `my-app.s3.us-east-1.amazonaws.com`.
- **Up to 10,000 access points per account per Region** — designed for many applications/teams on one bucket (the "bucket policy is too big / too coarse" problem).
- Policies are attached to the access point ARN and can scope access to **prefixes/objects**, restrict by VPC, by principal, etc.
- **Cross-account access point policies** are a common pattern: the *resource* side is expressed once via the access point; the caller still needs an identity policy naming the access point ARN.
- **Network scope**: access points can be **internet-facing** or **VPC-only**. A **VPC-only access point** simply refuses requests that do not arrive from the VPC (or via its endpoint) — network-level restriction without any bucket-policy plumbing.
- Access points inherit the bucket's **Block Public Access**; a public access point is impossible when BPA is on. They also support per-access-point BPA settings.
- **Not for** the "single global endpoint" case: every access point is regional; a bucket policy is still needed for bucket-wide rules (e.g. deny non-TLS, deny deletes).
- **Directory buckets** use a special flavour: **S3 Express Zone Mount access points** (mount an S3 Express filesystem e.g. for EFS/File Cache use cases).
- **S3 Multi-Region Access Points** give a *single* hostname fronting buckets in multiple regions, with cross-region replication underneath — for global applications (read locality / failover).

**Exam mapping:** "many applications share one bucket with different permissions / policy is too large" → **access points**. "Global app, single endpoint across regions" → **Multi-Region Access Point**. "Bucket must only be reachable from the VPC" → VPC-only access point (or a gateway-endpoint `aws:SourceVpce` condition).

---

## Object Lambda Access Points

An **S3 Object Lambda Access Point** runs an **AWS Lambda function on the *output* of read requests**, so every caller receives a **transformed version of the object** while the stored object stays untouched.

- It intercepts standard **GET, HEAD and LIST** requests made through it: S3 fetches the original object, invokes your Lambda, and the client receives what the Lambda returns. **Writes are not transformed**, and Object Lambda is **not supported on directory buckets**.
- Built from three pieces: the **Object Lambda Access Point** itself, a normal **supporting S3 access point** (the underlying data source), and the **Lambda function + configuration** saying which actions (`GetObject`, `HeadObject`, `ListObjects…`) it applies to.
- The Lambda reads the original via a **pre-signed URL** in the event payload and sends the result back with the **`s3-object-lambda:WriteGetObjectResponse`** API (the execution role needs `s3-object-lambda:WriteGetObjectResponse`; the managed policy `AmazonS3ObjectLambdaExecutionRolePolicy` covers it).
- The application just swaps the bucket name for the **Object Lambda Access Point ARN** — no change to the stored data.

**Typical uses (exam triggers):**

- **Anonymize / redact data on read** — production data returned *anonymized* (e.g. PII scrubbed) for a specific consumer; AWS ships prebuilt Lambdas in the **Serverless Application Repository** for PII detection/redaction and decompression.
- **One master dataset, many views** — filter by tenant/role, different schemas or formats per consumer, **without creating and maintaining derivative copies** of the same objects.
- **On-the-fly image resizing / thumbnails**, decompression, format conversion.

**Trade-offs:** every read pays **Lambda cost + added latency**, so it is a *transformation* tool, not a caching/backup one; permissions must be granted across all pieces (Object Lambda AP policy, supporting access point policy, Lambda role). Context keys such as `s3-object-lambda:TlsVersion` and `s3-object-lambda:AuthType` can be used in its resource policy.

**Exam mapping:** "different consumers need *different representations* of the same objects (anonymized, filtered, resized) without duplicating the data" → **S3 Object Lambda Access Point**.

---

## Access Grants

**S3 Access Grants** manage *data access for large numbers of identities* — it maps a **grantee** (an IAM Identity Center user/group, an Active Directory user/group, or an IAM role) to an **S3 location** (bucket, prefix or access point) with **read/write** permission, issuing **temporary credentials through AWS STS**.

- Terminology: **Access Grants instance** (one per region, optionally registered with IAM Identity Center / AD) → **registered locations** (the actual S3 prefix or access point ARN) → **grants** (grantee × location × permission).
- The **grantor** is the entity that owns the data (e.g. the data platform team); **grantees** are IAM Identity Center users/groups, Active Directory identities, or IAM roles — the role may live in **another AWS account**, so cross-account data sharing works without editing the bucket policy.
- Permissions are enforced at the *prefix* level and are evaluated **in addition to** the bucket/IAM permissions — the bucket owner must still allow the Access Grants service role to act.
- Use case: a **data lake with hundreds/thousands of users** — writing per-user bucket policies or ACLs does not scale; Access Grants gives self-service, auditable, least-privilege, *temporary* credentials.
- Audit via **CloudTrail** (grant create/update/delete + credential vending) and console visibility of who has access to what.
- Successor to the "give everyone `s3:*` in the data-lake bucket policy" pattern; complements **access points** (which scale *policies*, Access Grants scales *identities*).

**Exam mapping:** "grant access to a prefix to thousands of IAM Identity Center users / AD groups with least privilege and temporary credentials" → **Access Grants**. "Give one application its own scoped permission on a shared bucket" → **access point**.

---

## PrivateLink for Amazon S3

S3 can be reached privately in two ways, and the exam loves to contrast them:

| | **Gateway endpoint** | **Interface endpoint (PrivateLink)** |
|---|---|---|
| How | Route table entry: traffic to the S3 prefix list stays on the AWS network | ENI with a private IP in your subnet + private DNS name for S3 |
| Cost | **Free** | Hourly + per-GB data-processing charges |
| Reach | VPC only (via route tables) | VPC, **VPN, Direct Connect, other VPCs/peered accounts** (anywhere that can reach the ENI) |
| Policy | Endpoint policy (route-table scoped) | Endpoint policy **+ private DNS**; can restrict to specific buckets/actions |
| Typical use | Default for EC2 in a VPC talking to S3 | Hybrid/on-premises or cross-account apps that must never leave the AWS network, or when you need endpoint-level restrictions |

**PrivateLink specifics for S3:**

- Creates an **interface endpoint** in your VPC endpoints' subnets; enable **private DNS** and applications resolve `bucket.s3.region.amazonaws.com` to the private ENI — *no code change*.
- The **endpoint policy** is another resource-policy layer: e.g. "this endpoint may only `GetObject` from bucket X" — useful to stop a compromised instance in that VPC from exfiltrating other buckets.
- Combined with a bucket policy condition `aws:SourceVpce` / `aws:SourceVpc`, you get **"this bucket is only reachable from my VPC"** — a classic SAA answer.
- Works with **on-premises via Direct Connect/VPN** (the endpoint is reachable over the private network), which a gateway endpoint alone does not cover from on-prem.
- Traffic still traverses TLS; PrivateLink is about *where the packets go*, encryption is a separate layer.
- VPC endpoint policies and S3 Block Public Access both still apply.

**Exam mapping:** "keep S3 traffic off the internet, free, from EC2 in a VPC" → **gateway endpoint**. "Private connectivity from on-prem/hybrid, or per-endpoint restrictions, cross-account private access" → **interface endpoint / PrivateLink**.

---

## Internetwork traffic privacy

"Internetwork traffic privacy" = making sure the *path* between client and S3 never exposes data or credentials, whether the path crosses the public internet or not.

- **Every S3 request can be sent over HTTPS.** S3's regional, dualstack and FIPS endpoints all support TLS; only the **static-website endpoints are HTTP-only** (put **CloudFront** in front for HTTPS on a website).
- **Endpoints:**
  - Regional (virtual-hosted): `https://bucket.s3.us-east-1.amazonaws.com/key`
  - Dualstack (IPv6): `https://bucket.s3.dualstack.us-east-1.amazonaws.com/key`
  - FIPS: `https://bucket.s3-fips.us-east-1.amazonaws.com/key` (regulated workloads)
  - Path-style (legacy): `https://s3.us-east-1.amazonaws.com/bucket/key` — being deprecated for new buckets.
- **Keep traffic on AWS networks**: VPC **gateway endpoints** (free), **PrivateLink** interface endpoints, **AWS Direct Connect**, **Site-to-Site VPN** — none of these rely on the public internet.
- **Make HTTPS mandatory** with the `aws:SecureTransport` condition (see [Bucket policies](#bucket-policies)) and optionally enforce a minimum TLS version (`aws:TLSVersion` ≥ 1.2).
- **Signatures**: all requests use **AWS SigV4** over TLS — credentials never travel in cleartext; presigned URLs are time-limited and also TLS-based.
- **Logging/verification**: `aws:SourceIp`, `aws:SourceVpc(e)`, **S3 server access logs** and **CloudTrail data events** tell you where requests came from.
- S3 is a *service*, not a server you SSH into — there's no management plane to protect beyond the API itself (see [Infrastructure security](#infrastructure-security)).

**Exam mapping:** "traffic must never leave the private network / must not traverse the internet" → gateway endpoint or Direct Connect. "Must not accept non-HTTPS requests" → bucket policy `aws:SecureTransport`. "IPv6" → dualstack endpoint. "Regulated environment requiring validated crypto endpoints" → FIPS endpoint.

---

## CORS

**Cross-Origin Resource Sharing (CORS)** is a *browser* mechanism: a page at `https://app.example.com` that fetches an object from `https://bucket.s3.amazonaws.com/photo.jpg` is making a **cross-origin request**, and the browser blocks reading the response unless the *bucket* (the resource origin) explicitly allows it.

CORS config can be passed as JSON or XML (AWS console only accepts JSON).

- Configured on the bucket with `PutBucketCors`, as a set of rules:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://app.example.com"],
      "AllowedMethods": ["GET", "PUT", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-version-id", "Content-Length"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

- **Preflight**: for non-simple methods/headers the browser first sends an `OPTIONS` request; S3 answers it from the CORS configuration. `MaxAgeSeconds` caches that answer.
- `ExposeHeaders` makes response headers readable by JS (`ETag` is the classic one needed for uploads/conditional requests).
- **CORS is not authorization.** It does not make a bucket private or public — it only controls what *browsers* do with responses. A private bucket still needs IAM/policy + a presigned URL/Cognito for the underlying GET; a public bucket still needs CORS configured for the browser to read the objects from another origin.
- Common symptoms: works with `curl`, fails in the browser → missing CORS. `Access-Control-Allow-Origin` missing/wrong → `AllowedOrigins`. `PUT` failing with CORS error → preflight `AllowedMethods`/`AllowedHeaders` (e.g. `x-amz-server-side-encryption` not allowed).
- Cross-origin **uploads** (browser PUT) and **S3 static website hosting** are the main use cases; also applies when assets are served from a bucket but the app runs elsewhere.
- Bucket-level only (one configuration per bucket) — with multiple apps, consider separate prefixes + CloudFront behaviors or separate buckets.

**Exam mapping:** "the static site loads images/scripts from another bucket and the browser blocks them" → configure **CORS** on the source bucket (do not confuse with the bucket policy that grants `GetObject` — you usually need **both**: policy for authorization, CORS for the browser).

---

## In-transit encryption

Protecting data **while it moves** — i.e. TLS/SSL between client and S3.

- S3 supports **TLS 1.2+** on its service endpoints; requests over HTTPS are encrypted end-to-end between your client and the S3 front end.
- **Enforce it**: bucket policy with `Bool: { "aws:SecureTransport": "false" }` → `Deny`, and optionally `NumericLessThan: { "aws:TLSVersion": "1.2" }`.
- The **static website endpoint is HTTP only** → for HTTPS use **CloudFront** (which also gives you TLS 1.2+ minimum protocol version, custom certs and OAC).
- Data also stays encrypted **inside** the AWS network between AZs/devices, but that's at-rest/in-network encryption managed by S3.
- VPC endpoints/PrivateLink/Direct Connect reduce exposure to internet-path attacks but **do not replace TLS** — encrypt anyway (defense in depth; a compromised instance could otherwise sniff).
- Combined with **S3 Server Access Logging** / **CloudTrail data events** (`aws:SecureTransport` appears in event records) you can *audit* whether requests used HTTPS.

---

## Server-side encryption

**Server-side encryption (SSE)** = S3 encrypts data **at rest on its own infrastructure**, transparently; you never handle plaintext after upload. Since **January 2023 every new object is encrypted by default** (SSE-S3) even if you specify nothing.

| | **SSE-S3** | **SSE-KMS** | **SSE-C** |
|---|---|---|---|
| Key management | **Amazon S3** | **AWS KMS** (AWS-managed key `aws/s3` or **your own CMK**) | **You** (bring your own key, sent with each request) |
| Header | `x-amz-server-side-encryption: AES256` | `x-amz-server-side-encryption: aws:kms` (+ `x-amz-server-side-encryption-kms-key-id`) | `x-amz-server-side-encryption-customer-algorithm: AES256` + key + SHA-256 of key |
| Key storage by AWS | Yes (keys are rotated/managed for you) | KMS holds the key material | **Never** — key is used in memory only |
| Auditing | Standard S3 logging | **CloudTrail key-usage events**, per-key IAM/kms policy granularity, key disable & scheduled deletion | None (S3 has no key record) |
| Extra cost | Included | **KMS requests per PUT/GET** (mitigate with **S3 Bucket Keys**) | Included |
| ETag | MD5 (usual) | Random (not MD5) | Not a reliable MD5 of the plaintext |
| Best for | Default, simple compliance | Key-level control, audit trail, separation of duties, compliance | Keys must never be stored/seen by AWS |

Notes:


- **Server-side Encryption** only encrypts THE CONTENT of an object, not its metadata.
- **Default encryption** on the bucket sets the encryption for all new/overwrite objects (SSE-S3 or SSE-KMS); a **bucket policy** can *require* it by denying `PutObject` without the right header.
- **SSE-C** requests must use **HTTPS**, and you must supply the **identical key on every GET** — losing the key means losing the data (AWS explicitly can't recover it).
- **S3 Bucket Keys**: for SSE-KMS, a bucket-level key is used to derive per-object keys — reduces KMS calls (and cost) by up to ~99%, with the same audit properties.
- **DSSE-KMS**: it's SSE-KMS, with the INCLUSION OF CLIENT-SIDE ENCRYPTION.
Data in encrypted twice and the client-side key comes from KMS.
- Encryption is **transparent**: SDKs/CLI/consoles just work; there is nothing to change in applications for SSE-S3/SSE-KMS.
- Keys are encrypted with **FIPS 140-2/140-3 validated** hardware modules (S3 uses validated cryptographic modules for SSE-S3).
- SSE protects **at rest** only — pair it with [in-transit encryption](#in-transit-encryption).

---

## Client-side encryption

**Client-side encryption (CSE)** = *you* encrypt the data **before uploading**; S3 only ever stores ciphertext, and AWS never has the key or the plaintext.

- Implemented with an **S3 encryption client** (AWS SDKs: Python/Java/.NET/JS `S3EncryptionClient`), not with a header. Two modes:
  - **CSE-KMS**: the client calls **KMS** to generate/decrypt a data key (`GenerateDataKey`/`Decrypt`) — key management and audit stay in KMS, plaintext key only in client memory.
  - **CSE-C (customer-provided)**: you generate and store the key yourself; AWS is not involved at all.
- Uses **envelope encryption**: a random data key encrypts the object (AES-GCM, which also provides **integrity/authentication**), the data key itself is stored encrypted in the object's metadata (`x-amz-meta-...`).
- Because the ciphertext is opaque to S3: **server-side features that must read data don't apply** — e.g. S3 cannot re-encrypt, cannot compute meaningful ETags/checksums on plaintext, and **the console/`SelectObjectContent` can't process** the content; you must decrypt client-side.
- Loss of the key (or of the KMS permission) = permanent data loss; plan key rotation, backup and recovery (a **replicated** object stays ciphertext — replication does not help if keys are gone).
- Choose CSE when **regulation requires that AWS never holds the key/plaintext** or for data where the encryption must be verifiable end-to-end; otherwise SSE-KMS is simpler and cheaper.
- **Note:** AWS has deprecated the *legacy* encryption clients (JS v2 etc.) — use the current **AWS Encryption SDK / S3 CSE client**, which supports AES-GCM and multiple recipients.

**Rule of thumb:** *server-side* = "S3 encrypts it for you" (easy, default). *Client-side* = "nobody but me can ever see it" (maximum control, maximum responsibility).

---

## Versioning

**Versioning** keeps **every version of every object** (including delete markers), which turns it into a security/resilience control, not just a feature:

- **Protection against deletion and overwrite**: an accidental or malicious `DeleteObject` only creates a **delete marker** — the previous version survives and can be restored by removing the marker. Permanent destruction requires deleting a *specific version* (and MFA, if [MFA Delete](#mfa-delete) is on).
- **Protection against ransomware/overwrite**: `PutObject` creates a *new version*; the old bytes are still there. This is why versioning is the first line of defence in the "bucket was wiped" scenario.
- **Prerequisite** for **Cross-Region/Same-Region Replication**, **S3 Object Lock** (WORM) and **lifecycle cleanup of old versions**.
- Costs: all versions consume storage — add **lifecycle rules** to expire noncurrent versions / delete markers after N days.
- States: *Off → Enabled*; once **suspended** it can be re-enabled but never fully "off" again, and existing versions remain.
- With versioning, "delete" means one of three things: remove a delete marker (restore), delete a specific version (permanent, needs extra privileges), or lifecycle-expire it.

**Exam mapping:** "protect against accidental deletion / application overwrite / object-lock / replication" → **enable versioning** (before uploading data — it cannot be applied retroactively to already-deleted data).

---

## MFA Delete

**MFA Delete** adds a **multi-factor authentication requirement** to the most dangerous versioned operations — so a leaked access key alone cannot destroy history.

- Only works on a bucket with **versioning enabled** — MFA Delete is configured together with versioning.
- Requires the **MFA device serial number + current code** in the API call for:
  1. **Permanently deleting an object version** (`DeleteObjectVersion`), and
  2. **Changing the bucket's versioning state** (suspend/re-enable, `PutBucketVersioning`).
- Must be **enabled via API/CLI using the account root credentials** (not with an IAM user; the console doesn't manage it) — `aws s3api put-bucket-versioning --mfa "arn:aws:iam::...:mfa/xxx 123456"`. Root can therefore also disable it, so protect the root account (MFA on root, hardware keys, no access keys).
- Configuration persists across suspensions: if versioning is suspended and re-enabled, MFA Delete stays on.
- Does **not** protect reads or ordinary `DeleteObject` (which just adds a delete marker) — it protects *irreversible* actions and the versioning switch itself.
- Best combined with: versioning + **Object Lock (Compliance mode)** for true WORM, restrictive IAM (only a break-glass role may call `s3:DeleteObjectVersion`), CloudTrail alarming on those calls.

**Exam mapping:** "add a second factor before versions can be permanently deleted / versioning disabled" → **MFA Delete**. "Regulatory WORM that *nobody* (not even root) can bypass" → **Object Lock – Compliance mode** (MFA Delete can be turned off by root; Compliance mode cannot).

---

## Object tags

**Tags** are pairs of key/value metadata attached to a **bucket or an object** (max **10 tags per object**, key ≤128 chars, value ≤256 chars, case-sensitive, no `aws:` prefix).

Security-relevant uses:

- **Attribute-based access control (ABAC)**: bucket policies and IAM policies can condition on `s3:ResourceTag` ("only if `classification=public`") and `aws:RequestTag`/`s3:Tagging` (you may only *set* tags from an allowed set). The combination is how you build "a user may only read objects tagged with their team".
- **Data classification / governance**: tag objects with `pii`, `retention`, `confidentiality` and then have policies, lifecycle rules and audits act on those tags.
- **Lifecycle rules**: expire/transition *tagged* objects (e.g. delete all `temp=true` objects after 7 days — a cheap data-hygiene/security control).
- **Cost allocation**: **bucket-level** tags can be activated as **cost allocation tags** so S3 spend is broken down per bucket/project in the bill.
- **Audit/traceability**: tags appear in CloudTrail (for tagging calls), S3 Inventory and Storage Lens — "which objects belong to project X?".
- **Tags live outside the object's data**: they are stored separately, returned on GET/HEAD (`x-amz-tagging`) or with the `?tagging` sub-resource, and set via the `x-amz-tagging` header / `PutObjectTagging`.
- Tags are **version-specific**: in a versioned bucket each version carries its own tag set, and tagging operations (`PutObjectTagging`/`DeleteObjectTagging`) act on an existing version **without creating a new one** (only a `PUT` of a new object makes a new version). Without a version ID, they act on the current version; pass a version ID (`s3:PutObjectVersionTagging`) to tag a specific older version.
- Tags **survive copies** only if you pass them (`x-amz-tagging-directive: COPY` is default on CopyObject) — and they are **not** automatically applied on replication unless configured.

---

## Compliance validation

Compliance in S3 is mostly *"which audited controls does the service satisfy"*, plus the features you add on top.

- **Programs S3 complies with** (verify current scope in AWS Artifact): **PCI DSS**, **SOC 1/2/3**, **ISO 9001, 27001, 27017, 27018**, **HIPAA eligible** (sign a **BAA** with AWS), **FedRAMP**, **MTCS**, **IRAP**, **ENS**, **OSPAR**, **CISF**, **GxP (EU/US)**, **21 CFR Part 11 (EU/US)**, **CSA STAR**, **FIPS 140-2/140-3 validated** cryptographic modules for encryption at rest/in transit.
- Get the reports/agreements from **AWS Artifact** (no email/auditor needed): SOC reports, ISO certificates, the HIPAA BAA, PCI Attestation of Compliance.
- **AWS shared responsibility**: AWS certifies the *infrastructure and service*; **you** configure access, encryption, logging and retention correctly. Using a compliant service does not make *your data* compliant by default.
- Features that support compliance workloads:
  - **S3 Object Lock** — WORM, retention modes **Governance** (privileged roles can override) vs **Compliance** (nobody, including root, can delete/overwrite before expiry); **legal hold**. Requires versioning.
  - **Versioning** + **MFA Delete** — recoverability and irreversible-deletion protection.
  - **Replication (CRR)** — regional residency / DR for retention requirements.
  - **Object tags & lifecycle** — retention classification and auto-expiry.
  - **Server-side encryption** (SSE-KMS with customer-managed keys for key custody), **CloudTrail data events**, **S3 server access logs**, **S3 Inventory** — audit evidence.
  - **Data residency**: choose the bucket region; keep data in-region (also helped by CRR policies limiting destinations).
- For regulated data: **encrypt** (SSE-KMS/FIPS), **lock** (Object Lock), **log** (CloudTrail + access logs), **restrict** (BPA + endpoint/bucket policies), **prove** (Artifact reports + Config rules).

**Exam mapping:** "must not be deletable/overwriteable for 7 years, even by an admin" → **Object Lock – Compliance mode**. "Audited evidence of S3 controls" → **AWS Artifact**. "Which controls do *we* still own?" → shared responsibility model.

---

## Infrastructure security

Controls around the **physical and network infrastructure** that hosts S3 — the layer you don't configure, but should be able to argue about in the exam:

- **Physical/data-centre security**: AWS-managed data centres with 24/7 security, layered access, environmental controls; customers have **no direct access** to the infrastructure — S3 is API-only (no SSH, no instance to patch, no storage media to touch). You also can't inspect where physically an object lives beyond the region/AZ redundancy model.
- **Redundancy & isolation**: objects are stored across a **minimum of 3 AZs** in the region; multi-tenant isolation is handled by AWS; AZs are fault-isolated power/cooling/network zones.
- **Network layer**: requests traverse the AWS global network; you control exposure with **VPC gateway endpoints**, **PrivateLink interface endpoints**, **Direct Connect/VPN**, bucket policies with `aws:SourceVpc(e)`/`aws:SourceIp`, and **internet-facing vs VPC-only access points**.
- **DDoS**: **AWS Shield Standard** protects all AWS customers automatically against common layer 3/4 attacks on S3 endpoints; **Shield Advanced** for enhanced support/SLAs; **AWS WAF** applies to *CloudFront/API Gateway/ALB* in front of S3 (not to S3 endpoints directly) — so for a public bucket use **CloudFront + WAF + Shield Advanced**.
- **Observability & detection**:
  - **S3 server access logging** — per-request logs (who, what, when, response).
  - **CloudTrail** — management events always; **data events** (GetObject/PutObject) must be explicitly enabled (cost consideration) → they power **CloudTrail Lake**, event selectors and alerts.
  - **Amazon GuardDuty S3 Protection** — ML-based detection of anomalous S3 data events (e.g. unusual `GetObject` patterns, deletion sprees).
  - **AWS Config** — conformance rules for public access, encryption, versioning.
  - **Amazon Macie** — sensitive-data discovery/classification in buckets.
  - **S3 Storage Lens** — organization-wide security metrics (public buckets, unencrypted buckets, replication lag) and best-practice checks.
- **Vulnerability/patching & access to hardware** are entirely AWS's responsibility (shared responsibility model) — patching the S3 control plane, hardening hosts, securing data centres.
- **Account-level hardening** is part of infrastructure security too: **account-level Block Public Access**, no root access keys, SCPs to deny `s3:PutBucketPolicy` outside approved patterns, permission boundaries for roles that can modify bucket policies.

---

## How the layers fit together

A single "make my bucket secure" baseline combines almost every topic above:

1. **Defaults**: Object Ownership = *bucket owner enforced* (ACLs off) + **Block Public Access** on, at **account** level.
2. **Identity**: least-privilege IAM policies; **access points** when several apps share the bucket; **Access Grants** when humans (Identity Center/AD) need scoped, temporary access.
3. **Resource policies**: a bucket policy that (a) denies non-HTTPS (`aws:SecureTransport`), (b) denies unencrypted uploads, (c) restricts source VPC/endpoint/IP/org, (d) denies `DeleteBucket`/versioning changes for normal roles.
4. **Network**: **gateway endpoint** (free, VPC) or **PrivateLink** (hybrid/cross-account), VPC-only access points for strict isolation.
5. **Data at rest**: default encryption **SSE-S3** (simple) or **SSE-KMS with a customer-managed key + Bucket Key** (audited, key-controlled); **client-side** where AWS must never see plaintext.
6. **Data in transit**: HTTPS everywhere; CloudFront for website endpoints; minimum TLS version in the policy.
7. **Integrity/retention**: **versioning** + **MFA Delete** (+ **Object Lock** for WORM) + lifecycle rules for old versions.
8. **Detection/evidence**: CloudTrail data events, S3 access logs, GuardDuty S3 Protection, Macie, Storage Lens, Config rules, **IAM Access Analyzer for S3** for external-sharing findings.
9. **Browser apps**: **CORS** rules for the exact origins/methods (never `*` in production for sensitive buckets).

---

## Exam cheat sheet

| Requirement | Go-to service/feature |
|---|---|
| Deny HTTP / enforce TLS | Bucket policy `aws:SecureTransport` |
| Enforce encryption on upload | Bucket policy condition **or** default encryption |
| Find publicly/externally shared buckets | **IAM Access Analyzer for S3** |
| Discover PII in buckets | **Amazon Macie** |
| Compliance/conformance rules in-account | **AWS Config** |
| Prove/attest service compliance | **AWS Artifact** |
| Make public access impossible | **Block Public Access** (account level) |
| ACLs legacy / object ownership issues | **Object Ownership – bucket owner enforced** |
| Many apps, one bucket, separate permissions | **Access points** (Multi-Region AP for global) |
| Thousands of human users, temporary, prefix-scoped | **Access Grants** |
| Free private S3 from a VPC | **Gateway endpoint** |
| Private S3 from on-prem / cross-account / per-endpoint policy | **PrivateLink (interface endpoint)** |
| Browser cross-origin access to objects | **CORS** on the bucket |
| Prevent accidental/malicious overwrite or delete | **Versioning** (+ lifecycle) |
| Second factor to purge versions / disable versioning | **MFA Delete** |
| Irreversible WORM retention, even for root | **Object Lock – Compliance mode** |
| ABAC / classification-driven policies | **Object tags** |
| Key control + audit of key usage | **SSE-KMS** (customer-managed key, CloudTrail) |
| AWS must never see the data | **Client-side encryption** |
| Keep S3 off the public internet, IPv6, FIPS endpoints | dualstack/FIPS endpoints, VPC endpoints |
| DDoS on S3/website | **Shield (Standard/Advanced)** + CloudFront + WAF |

---

## References

- S3 security docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security.html
- Block Public Access: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
- Bucket policies: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html
- IAM Access Analyzer: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
- Access points: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-points.html
- S3 Access Grants: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-grants.html
- Encryption: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingServerSideEncryption.html
- Compliance programs: https://aws.amazon.com/compliance/programs/
- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=18393s (S3 from 5:06:32)
