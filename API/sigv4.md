# AWS Request Signing & Signature Version 4 (SigV4)

Exam notes on how every AWS API request is **authenticated**: what is signed, what travels over the wire, and the numbers/traps that show up in SAA questions.

## What SigV4 is and why it exists

**AWS Signature Version 4** is the protocol that authenticates requests to AWS APIs. The client signs the request with its credentials; AWS recomputes the signature and compares.

- **Identity** — proves the caller holds the secret access key.
- **Integrity** — a hash of the request is signed, so any tampering in transit invalidates it.
- **Replay protection** — requests carry a timestamp and must reach AWS within **~5 minutes**; presigned URLs add an explicit expiry.
- The **secret access key is never sent**. It is used to *derive* a signing key and sign; only the resulting signature travels.
- SDKs and the CLI sign automatically — hand-rolled SigV4 is only needed when no SDK exists for the language.

## The signing process (4 steps)

1. **Canonical request** — normalized request: HTTP method, canonical URI, sorted query string, lowercased/trimmed canonical headers, `SignedHeaders` list, and the **SHA-256 hash of the payload**.
2. **String to sign** — `AWS4-HMAC-SHA256` + timestamp (`YYYYMMDDTHHMMSSZ`) + **credential scope** (`date/region/service/aws4_request`) + SHA-256 of the canonical request.
3. **Derive the signing key** — HMAC-SHA256 chain, scoped to **one day, one region, one service**:

```text
kDate    = HMAC-SHA256("AWS4" + SecretAccessKey, "20261022")
kRegion  = HMAC-SHA256(kDate,    "eu-north-1")
kService = HMAC-SHA256(kRegion,  "s3")
kSigning = HMAC-SHA256(kService, "aws4_request")
```

4. **Sign** — `Signature = HMAC-SHA256(kSigning, StringToSign)`, sent in the `Authorization` header (or in the query string for presigned URLs).

```http
Authorization: AWS4-HMAC-SHA256
  Credential=AKIAIOSFODNN7EXAMPLE/20261022/eu-north-1/s3/aws4_request,
  SignedHeaders=host;x-amz-content-sha256;x-amz-date,
  Signature=fe5f80f77d5fa3beca038a248ff027d0445342fe2855ddc963176630326f1024
```

**Credential scope is the exam point:** the same request signed for `us-east-1` is invalid in `eu-north-1`, and an `s3` signature is invalid for `ec2`. Global services use their conventional scope (`us-east-1` for IAM/Route 53/global STS).

## Authentication methods: header vs query string

| | **Authorization header** | **Query string (presigned URL)** |
|---|---|---|
| Typical use | CLI, SDKs, normal API calls | Share a link to a private S3 object |
| Expiry mechanism | Timestamp + ~5 min window | `X-Amz-Expires` (explicit seconds) |
| Where auth lives | Header (not cached, not loggable in URLs) | URL parameters — **anyone holding the URL can use it** (bearer token) |
| Temporary creds | `X-Amz-Security-Token` header | `X-Amz-Security-Token` query parameter |

A SigV4 presigned URL carries `X-Amz-Algorithm`, `X-Amz-Credential`, `X-Amz-Date`, `X-Amz-Expires`, `X-Amz-SignedHeaders`, `X-Amz-Signature` (and `X-Amz-Security-Token` for temporary credentials).

## Presigned URL limits (S3, memorized numbers)

| Signer | Maximum validity |
|---|---|
| **IAM user** credentials (SigV4) | **7 days** (604800 s) — CLI/SDK cap |
| **S3 console** | **1 minute to 12 hours** |
| **Temporary credentials** (STS/role/EC2 instance profile) | **Never longer than the credential** — the URL dies when the session dies, even if you asked for longer |
| Revoked/deactivated credential | URL stops working immediately |

- The URL only grants what the **signer** was allowed to do — if the signer lacks `s3:GetObject`, the URL fails; if the permission is revoked, it fails too.
- Enforce a maximum age with the bucket policy condition **`s3:signatureAge`** (milliseconds), e.g. deny presigned requests older than 10 minutes.
- Restrict where a URL can be used with `aws:SourceIp` / `aws:SourceVpc(e)` — the URL itself is a bearer token, so short expiry + network restrictions are the controls.

## Temporary credentials

- Add the **session token** to the request (`X-Amz-Security-Token` header/query parameter) and include it in `SignedHeaders` — missing it produces auth errors even with correct keys.
- Presigned URLs created with temporary credentials inherit the **session's** lifetime (AssumeRole default 1 h, EC2 instance profile ~6 h) — the "URL expired early" FAQ in a nutshell.

## Payload signing

- The payload hash (`x-amz-content-sha256`) binds the body to the signature.
- **`UNSIGNED-PAYLOAD`** — skip hashing the body (S3 over **HTTPS** and presigned URLs): cheaper for large uploads, but the body is then not integrity-protected by the signature.
- **`STREAMING-AWS4-HMAC-SHA256-PAYLOAD`** — chunked/streaming uploads: each chunk is signed, so S3 can verify data as it arrives.
- **SigV4a** is the asymmetric variant that signs for **multiple regions** — used by **S3 Multi-Region Access Points**; SDK/CLI switch automatically. Not something you configure for classic regional APIs.

## Common errors and what they mean

| Error | Likely cause |
|---|---|
| `SignatureDoesNotMatch` | Wrong secret key, **clock skew**, modified signed header/query, wrong region/service in scope, mismatched presigned URL |
| `RequestTimeTooSkewed` / `RequestExpired` | System clock off by more than the allowed window — sync with NTP |
| `ExpiredToken` | Temporary credentials expired — re-assume the role and sign again |
| `AccessDenied` with a presigned URL | Signer lacks the permission, or bucket policy explicitly denies |
| `403` on an unsigned request to a private resource | No signature at all — sign it, or make the object public (not recommended) |

## Exam traps

- **The secret key never travels** — only the signature. "Send the secret key over HTTPS" is the wrong answer.
- **Signature is scoped** to date/region/service — a valid signature cannot be replayed against another region or service.
- **5-minute window** for header-signed requests; presigned URLs use `X-Amz-Expires` instead.
- **Presigned URL ≠ CloudFront signed URL**: S3 presigned URLs use SigV4 (access key + secret); **CloudFront** signed URLs/cookies use **CloudFront key groups (RSA)**. For private CloudFront content, the answer is CloudFront signed URLs/cookies, not an S3 presigned URL.
- **SigV4 vs SigV2**: SigV2 is legacy (and unsupported in some regions); SigV4 is the default. Presigned SigV2 URLs support only MD5 checksums, SigV4 supports the modern checksum algorithms.
- **`--no-sign-request`** means *anonymous*, not "unsigned payload" — it only works on public resources.
- Presigned URLs are **bearer tokens**: whoever has the link has the access until expiry — never put one in a public repo or log.
- **S3 Multi-Region Access Points** automatically use **SigV4a** in SDK/CLI — you don't hand-select it.
- Changing a **signed header** (e.g. adding `x-amz-acl` without re-signing) breaks the signature; proxied headers can too.

## Exam mapping

| Question phrasing | Answer |
|---|---|
| Custom app gets `SignatureDoesNotMatch` calling AWS | Use the **SDK/CLI**; check clock, region, session token and signed headers |
| Give a user temporary download access to one private object | **S3 presigned URL (SigV4)** with a short expiry |
| Presigned URL must die in ≤ 1 hour | `--expires-in 3600` (`X-Amz-Expires`) or `s3:signatureAge` bucket-policy condition |
| Presigned URL stopped working before its expiry | Signed with **temporary credentials** that expired/rotated |
| Request works in one region, fails in another | Signature **credential scope** (date/region/service) |
| Streaming upload of unknown size to S3 | Chunked SigV4 (`STREAMING-AWS4-HMAC-SHA256-PAYLOAD`) |
| Private content through CloudFront | **CloudFront signed URL/cookie** (key group), not an S3 presigned URL |
| Multi-region S3 access point | **SigV4a** (automatic in SDK/CLI) |
| Protect against replayed requests | Timestamp + 5-minute window; short presigned expiry |

## Quick commands

```bash
# Generate a SigV4 presigned URL (max 7 days with IAM user credentials)
aws s3 presign s3://my-bucket/report.pdf --expires-in 3600

# Anonymous request (public bucket only) — NOT the same as unsigned-payload
aws s3 cp s3://public-bucket/file.txt . --no-sign-request

# Confirm which identity your signature represents
aws sts get-caller-identity

# Inspect the canonical request/string-to-sign when debugging (SDK/CLI --debug)
aws s3api get-object --bucket my-bucket --key report.pdf out.pdf --debug
```

```python
# boto3: presigned GET
import boto3
s3 = boto3.client("s3", region_name="eu-north-1")
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": "my-bucket", "Key": "report.pdf"},
    ExpiresIn=3600,
)
```

## References

- SigV4 overview: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv.html
- Signature elements: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-signing-elements.html
- Presigned URLs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
- S3 SigV4 conditions (`s3:signatureAge`): https://docs.aws.amazon.com/AmazonS3/latest/API/bucket-policy-s3-sigv4-conditions.html
- Troubleshooting SigV4: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-troubleshooting.html
- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY
