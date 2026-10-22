# S3 Request Styles — Virtual Hosted-Style vs Path-Style

Every S3 request has to say *which bucket* it is talking to. There are two ways to encode that into a URL: put the bucket name in the **hostname** (virtual hosted-style) or put it in the **URL path** (path-style). Same bucket, same key, same result — only the shape of the URL changes.

```
Virtual hosted-style                                Path-style
--------------------                                ----------
https://my-bucket.s3.us-west-2.amazonaws.com/images/logo.png
        \_______/ \______________________/ \______________/
          bucket           endpoint                key

https://s3.us-west-2.amazonaws.com/my-bucket/images/logo.png
                          \_______/ \_____/ \______________/
                           endpoint bucket           key
```

## The Two Formats

| | Virtual hosted-style | Path-style |
|---|---|---|
| **URL format** | `https://<bucket-name>.s3.<region>.amazonaws.com/<key>` | `https://s3.<region>.amazonaws.com/<bucket-name>/<key>` |
| **Example** | `https://my-bucket.s3.us-west-2.amazonaws.com/images/logo.png` | `https://s3.us-west-2.amazonaws.com/my-bucket/images/logo.png` |
| **Bucket in** | the DNS hostname (as a subdomain) | the first component of the path |
| **HTTP `Host` header** | `my-bucket.s3.us-west-2.amazonaws.com` | `s3.us-west-2.amazonaws.com` |
| **How S3 finds the bucket** | parses it out of the `Host` header | parses it out of the request URI |
| **Status** | ✅ recommended, current default of AWS SDKs/CLI | ⚠️ deprecated — works today, will be discontinued (see [Deprecation Status](#deprecation-status--path-style-is-being-phased-out)) |

Both are plain REST requests to the same endpoint — the bucket simply gets "carved out" of the domain in the first case. A request can also specify the bucket via the HTTP `Host` header directly (HTTP 1.0, or any request where you control the headers), which is effectively how the virtual hosted-style works under the hood.

> ⚠️ **Path-style is on its way out.** It still works in all commercial Regions today, but AWS formally announced its retirement (see [Deprecation Status](#deprecation-status--path-style-is-being-phased-out)) — new work should always use virtual hosted-style.

There is also a **legacy global endpoint** without a region (`https://<bucket>.s3.amazonaws.com` / `https://s3.amazonaws.com/<bucket>`), which defaults to **US East (N. Virginia)**. For path-style requests it only works in `us-east-1` — any other region answers **301 Permanent Redirect** to the correct regional endpoint. For virtual hosted-style it may answer 307, or **400 Bad Request** outright for regions launched after March 20, 2019. Always prefer the **regional endpoint** (`s3.<region>.amazonaws.com`).

## Key Differences

### 1. DNS and bucket names

- **Virtual hosted-style**: the bucket name becomes a subdomain of `s3.<region>.amazonaws.com`, which is exactly why bucket names must be **globally unique and DNS-compatible** — see [Bucket Naming Rules](bucket-naming-rules.md).
- **Path-style**: the bucket name never touches DNS. (S3 buckets are globally unique regardless — the naming rule exists because of the virtual hosted-style URL shape, not the other way round.)

### 2. HTTPS and dots in bucket names (the big gotcha)

The wildcard certificate AWS presents for the endpoint only covers **one** label before `s3`:

- `*.s3.us-west-2.amazonaws.com` matches `my-bucket.s3.us-west-2.amazonaws.com` ✅
- It does **not** match `my.assets.s3.us-west-2.amazonaws.com` ❌ — a dotted bucket name inserts two labels, so HTTPS fails with a certificate hostname mismatch.

So with **virtual hosted-style + HTTPS, bucket names must not contain dots**. Workarounds, in order of preference:

1. Don't use dots in bucket names (or use hyphens instead).
2. Serve the bucket under **your own domain** via a CNAME/alias to the virtual hosted-style endpoint, with a certificate for *your* domain.
3. Path-style requests — but see the deprecation note below.

This is also why **CNAME/custom-domain URLs** exist: `images.example.com` → `images.example.com.s3.us-west-2.amazonaws.com`, and the bucket name must exactly match the hostname you register.

### 3. Browsers and same-origin

AWS explicitly recommends **avoiding path-style URLs for browser-hosted website content** — the bucket moving between "path segments" and "origins" confuses the browser same-origin security model. For websites, use the **S3 website endpoint** or **CloudFront** instead (see [Static Website Hosting](README.md#static-website-hosting)).

### 4. Features that only accept one style

| Feature | Style |
|---|---|
| **Transfer Acceleration** (`<bucket>.s3-accelerate.amazonaws.com`) | virtual hosted only |
| **S3 Access Points** (alias becomes the hostname) | virtual hosted only |
| **Directory buckets / S3 Express One Zone** | virtual hosted only — path-style is not supported |
| **Dualstack (IPv6)** endpoints (`s3.dualstack.<region>`) | both styles supported — see [Dualstack Endpoints](#dualstack-endpoints-ipv6) |
| **IP-address endpoints / local emulators** (LocalStack, moto, `--endpoint-url http://127.0.0.1:4566`) | path-style — you can't put a bucket in a hostname that has no DNS name |
| **S3-compatible third-party services** (MinIO, Ceph RGW, Wasabi, Backblaze B2…) | often path-style by default, since their endpoints aren't `*.amazonaws.com` |

### 5. Request signing

SigV4 signatures include the **`Host` header**. A request signed for one style cannot be replayed with the other — you must re-sign if you change styles. This matters when writing your own URL-rewriting proxies or presigned URLs.

## Dualstack Endpoints (IPv6)

**Dual-stack endpoints** are a variant of the regional endpoint that serves traffic over **both IPv4 and IPv6** — the hostname simply has `dualstack` inserted after `s3`. They work with **either request style**, exactly like the standard regional endpoint:

```
Virtual hosted-style:  https://my-bucket.s3.dualstack.us-west-2.amazonaws.com/images/logo.png
Path-style:            https://s3.dualstack.us-west-2.amazonaws.com/my-bucket/images/logo.png
```

- When you call a dual-stack endpoint, DNS resolves the name to an **IPv6 or IPv4 address** and the request works identically — same API, same performance, no code changes besides the endpoint hostname.
- **No additional charges** for accessing S3 over IPv6 (data transfer pricing still applies as usual).
- FIPS variants also exist (`s3-fips.dualstack.<region>.amazonaws.com`).
- Transfer Acceleration has a dual-stack form too: `<bucket>.s3-accelerate.dualstack.amazonaws.com`.
- Use case: **IPv6-only clients/VPCs** (or dual-stack networks avoiding NAT64 for S3 traffic), and any environment that must reach S3 over IPv6.
- Careful: when using S3 through a VPC **gateway endpoint**, adding dualstack changes how traffic egresses — a gateway endpoint is IPv4-based, so verify your routing before switching.

Since dual-stack endpoints exist for both styles, switching to IPv6 never forces you off virtual hosted-style (or onto path-style).

## Deprecation Status — path-style is being phased out

**Path-style requests are officially deprecated and will be discontinued** — treat them as legacy even where they still work.

Timeline:

- **May 2019** — AWS announces path-style will be retired; buckets created after **September 30, 2020** would support virtual hosted-style only.
- **Sept 2020** — after customer pushback, AWS **delays** the deprecation with no new date, but keeps the goal: *"the path-style naming convention is being retired in favor of virtual-hosted style"*.
- **2022/2023** — delayed again; the AWS docs keep the standing notice: *"Currently, Amazon S3 supports both virtual-hosted–style and path-style URL access in all AWS Regions. **However, path-style URLs will be discontinued in the future.**"*
- **As of October 2026** — no hard end date has been announced and path-style still answers in all commercial Regions, so it is **not yet fully removed**; but it is formally on the way out, with parts already gone:
  - **Directory buckets (S3 Express One Zone)** already support **virtual hosted-style only** — path-style is effectively *already* discontinued there.
  - The **legacy global path-style endpoint** (`https://s3.amazonaws.com/<bucket>`) only works in `us-east-1`; everywhere else it already fails with **301/400**.

Practical consequence: **never build anything new on path-style**. Use virtual hosted-style (the AWS SDK/CLI default), and keep path-style only where nothing else works (IP/localhost endpoints, S3-compatible third-party tools). To find legacy callers in your account, check **S3 server access logs** (`Host Header` field) or **CloudTrail data events** (`host` element of `requestParameters`).

## Choosing the Style in Tooling

**AWS CLI** — `~/.aws/config`:

```ini
[default]
s3 =
    addressing_style = virtual   # virtual | path | auto
```

**boto3 (Python SDK)**:

```python
import boto3
from botocore.config import Config

s3 = boto3.client("s3", config=Config(s3={"addressing_style": "virtual"}))
```

- `virtual` — always virtual hosted-style (AWS default behavior in practice).
- `path` — always path-style (needed for IP/localhost endpoints and many S3-compatible services).
- `auto` — virtual hosted-style, falling back to path-style when the endpoint can't carry a bucket subdomain (IP address, custom endpoint).

## Exam Takeaways

- **Virtual hosted-style is the modern default**: bucket in the hostname, `https://<bucket>.s3.<region>.amazonaws.com/<key>`.
- **Path-style** puts the bucket in the path: `https://s3.<region>.amazonaws.com/<bucket>/<key>` — it **works today but is officially deprecated and will be discontinued** (with no announced end date); directory buckets already reject it.
- Bucket names are **globally unique and DNS-compatible because they become subdomains** in virtual hosted-style URLs.
- **Dots in bucket names break HTTPS** with virtual hosted-style (wildcard certificate covers only one label) — avoid dots, or use a custom domain.
- Transfer Acceleration, Access Points and **directory buckets (S3 Express One Zone)** use virtual hosted-style only.
- **Dual-stack endpoints** (`<bucket>.s3.dualstack.<region>.amazonaws.com` / `s3.dualstack.<region>.amazonaws.com/<bucket>`) add **IPv6** support to both request styles, at no extra cost.
- For websites served to browsers, don't use path-style URLs — use the website endpoint or CloudFront.

## References

- Virtual hosting of general purpose buckets (AWS docs): https://docs.aws.amazon.com/AmazonS3/latest/userguide/VirtualHosting.html
- Amazon S3 Path Deprecation Plan – The Rest of the Story: https://aws.amazon.com/blogs/aws/amazon-s3-path-deprecation-plan-the-rest-of-the-story/
- Update to Amazon S3 Path Deprecation Plan: https://aws.amazon.com/blogs/storage/update-to-amazon-s3-path-deprecation-plan
- S3 endpoints and quotas: https://docs.aws.amazon.com/general/latest/gr/s3.html
- Using Amazon S3 dual-stack endpoints: https://docs.aws.amazon.com/AmazonS3/latest/userguide/dual-stack-endpoints.html
- Making requests to Amazon S3 over IPv6: https://docs.aws.amazon.com/AmazonS3/latest/developerguide/ipv6-access.html

← Back to the [S3 overview](README.md)
