# Amazon CloudFront

**Amazon CloudFront** is AWS's **Content Delivery Network (CDN)**. It caches and delivers your content from a global network of **edge locations** close to users, reducing latency and load on the origin.

Related notes: [S3](../S3/README.md), [Global Accelerator](../GlobalAccelerator/README.md), [Route 53](../Route53/README.md), [Elastic Load Balancing](../EC2/elastic-load-balancing.md).

## What Is a CDN

A **Content Delivery Network** is a geographically distributed set of servers (**edge servers / PoPs**) that **cache copies of content** near users.

- Without a CDN: every user request travels to the **origin** (single region), so far users see high latency and the origin takes all the load.
- With a CDN: the first request fetches from the origin and is **cached** at the edge; later requests nearby are served from the cache (**cache hit**).
- Benefits: **lower latency**, **less origin load**, **better scalability** for traffic spikes, **DDoS absorption**, lower data transfer cost from the origin.

## How CloudFront Works

1. User requests `https://dxxxx.cloudfront.net/image.png` (or your own domain).
2. DNS routes the user to the **nearest edge location**.
3. **Cache hit**: the edge returns the object immediately.
4. **Cache miss**: the edge asks the next layer (optionally a **Regional Edge Cache**), then the **origin**, returns the object and **caches** it for the TTL.

```
User → Edge location → Regional Edge Cache → Origin (S3 / ALB / EC2 / custom HTTP)
         (cache hit returns here)
```

- **Edge locations**: hundreds of PoPs worldwide (more than 400).
- **Regional Edge Caches**: larger caches between edges and the origin, for less popular content.
- CloudFront is a **global service** (the distribution is not tied to a region).
- Supports **HTTP/HTTPS**, **HTTP/2, HTTP/3**, **WebSocket**, and IPv6.

## Main Concepts

| Concept | Meaning |
|---|---|
| **Distribution** | The CloudFront configuration; gets a `*.cloudfront.net` domain name |
| **Origin** | Where the content comes from: **S3 bucket**, **ALB/ELB**, **EC2**, API Gateway, MediaStore/MediaPackage, or **any custom HTTP server** (even on-premises) |
| **Behavior** | Rules per **path pattern** (`/images/*`, `/api/*`): which origin, allowed methods, cache policy, viewer protocol, function associations |
| **Cache policy** | What forms the **cache key** (headers, cookies, query strings) and the **TTLs** |
| **Origin request policy** | What extra values are forwarded to the origin **without** being part of the cache key |
| **Response headers policy** | Add CORS and security headers (HSTS, etc.) |
| **Origin group** | Primary + secondary origin for **failover** |
| **Price class** | Limit the edge locations used to reduce cost |

## Origins

- **S3 origin**: use **Origin Access Control (OAC)** so the bucket stays **private** and only CloudFront can read it (OAC replaces the legacy **OAI**; OAC supports SSE-KMS and all regions). Add a bucket policy allowing the `cloudfront.amazonaws.com` service principal with the distribution ARN as condition.
- **S3 static website endpoint**: treated as a **custom origin** (HTTP only, no OAC).
- **ALB / EC2 origin**: the ALB or instance must be **publicly reachable**; allow the **CloudFront managed prefix list** in the security group, and use a **custom header** secret to prove traffic came from CloudFront. (Or use a **VPC origin** to keep the ALB/EC2 in a private subnet.)
- **Custom origin**: any HTTP(S) server, including on-premises.
- **Origin Shield**: an extra centralized caching layer in front of the origin to improve cache hit ratio and cut origin load further (extra cost).
- **Origin failover**: origin group switches to the secondary on 4xx/5xx or timeout (high availability).

## Caching

- Objects stay in cache until the **TTL** expires (default 24 hours, min/max configurable) or until invalidated.
- **Cache key**: by default the URL path/host; add headers, cookies, query strings **only if needed** (more values = lower hit ratio).
- Respects `Cache-Control` / `Expires` headers from the origin, bounded by min/max/default TTL.
- **Cache invalidation**: force removal before TTL expires (for example `/*` or `/images/logo.png`). First 1,000 paths per month free, then paid. Alternative: **versioned file names** (`app.v2.js`), which is free and preferred.
- Aim for a high **cache hit ratio** (check CloudWatch / cache statistics).
- Dynamic content can use **TTL 0** and still benefit from the AWS backbone and persistent connections.

## Security

- **HTTPS**: viewer protocol policy (HTTP and HTTPS / redirect HTTP to HTTPS / HTTPS only); also HTTPS between CloudFront and the origin.
- **Certificates**: custom domain (**alternate domain name / CNAME**) needs an **ACM certificate in `us-east-1`** (N. Virginia). Free cert for `*.cloudfront.net`.
- **AWS WAF** integration (block SQLi, XSS, rate limit, bot control) at the edge.
- **AWS Shield Standard** is included free (DDoS layers 3/4); **Shield Advanced** optional.
- **Geo restriction**: allow list or block list of countries.
- **Signed URLs / Signed cookies**: restrict access to **paid or private content**.
  - **Signed URL**: one file per URL (for example a download, or clients that don't support cookies).
  - **Signed cookie**: access to **multiple files** (for example a whole video library or a site section).
  - Use **trusted key groups** (recommended, no root user needed); the old method used CloudFront key pairs of the root account.
- **Field-level encryption**: encrypt specific POST fields (for example credit card) at the edge with a public key; only the app with the private key can decrypt.
- **Origin Access Control** keeps S3 private; **custom headers** or **prefix lists** protect ALB origins.

### Signed URL (CloudFront) vs S3 Pre-signed URL

| | CloudFront signed URL | S3 pre-signed URL |
|---|---|---|
| Scope | Any origin (S3, HTTP) | **S3 only** |
| Signed with | CloudFront key pair (trusted key group) | IAM credentials of the signer |
| Features | Caching, WAF, geo, custom domain, path wildcards | Direct S3 access with signer's permissions |

## Edge Compute

| | **CloudFront Functions** | **Lambda@Edge** |
|---|---|---|
| Runtime | JavaScript (lightweight) | Node.js, Python |
| Triggers | **Viewer request / response** only | Viewer **and origin** request / response |
| Max duration | Under 1 ms | 5 s (viewer), 30 s (origin) |
| Scale | Millions of requests per second | Thousands per second |
| Network / file / body access | No | Yes (network calls, request body) |
| Cost | Cheaper (about 1/6) | More expensive |
| Use cases | URL rewrites, redirects, header manipulation, cache key normalization, simple auth (JWT check) | Heavy logic, A/B testing, call external services, SEO, image resizing |

## Lambda@Edge in Detail

**Lambda@Edge** lets you run Lambda functions (Node.js or Python) at CloudFront locations, to customize requests and responses close to the user, with no servers to manage.

### The 4 Trigger Points

```
Viewer ──(1) Viewer request──▶ CloudFront cache ──(3) Origin request──▶ Origin
Viewer ◀─(4) Viewer response── CloudFront cache ◀─(2) Origin response── Origin
```

| Trigger | Runs when | Runs on cache hit? | Typical use |
|---|---|---|---|
| **Viewer request** | Every request, before the cache lookup | Yes | Authentication, redirects, URL rewrite, A/B testing |
| **Origin request** | Cache **miss**, before calling the origin | No | Choose origin dynamically, modify request to origin, add auth headers |
| **Origin response** | Origin replied, before caching | No | Change headers before the object is cached, generate custom errors |
| **Viewer response** | Before returning to the viewer (hit or miss) | Yes | Add security headers, cookies |

- Origin triggers run **only on cache miss**, so they are cheaper and the result is **cached**. Viewer triggers run on **every** request.
- A function can **generate a response itself** (for example a redirect or a 403) without ever contacting the origin.

### Limits and Requirements

| | Viewer triggers | Origin triggers |
|---|---|---|
| Max execution time | **5 seconds** | **30 seconds** |
| Max memory | 128 MB | Up to 10,240 MB |
| Max function package size | 1 MB | 50 MB (zipped) |
| Max response size generated | 40 KB | 1 MB |

- Must be created in **`us-east-1`** (N. Virginia); CloudFront **replicates** it to edge locations worldwide.
- Must use a **numbered version** (not `$LATEST`) and the function needs an **IAM role** trusted by both `lambda.amazonaws.com` and `edgelambda.amazonaws.com`.
- **No VPC access**, no Lambda layers, no environment variables, no containers, no provisioned concurrency; x86 only.
- Runs in a **regional edge cache**, not in every edge PoP. Logs go to **CloudWatch Logs in the region closest to where it ran**.
- Billed per request and per duration (more expensive than CloudFront Functions); no free tier.

### Use Cases

- **Authentication / authorization** (validate JWT or cookies, redirect to login).
- **A/B testing** and **dynamic content** by cookie, country, or device header.
- **Dynamic origin selection** (route to different origins by header or path).
- **SEO**: serve pre-rendered pages to bots; **SSR** for web apps at the edge.
- **Image resizing / transformation** on demand.
- **Custom error pages** or calling an **external API** (network calls are allowed).
- **Bot mitigation** and adding **security headers**.

### Lambda@Edge vs Regular Lambda

| | Lambda | Lambda@Edge |
|---|---|---|
| Runs in | A single **region** | **CloudFront edge** (replicated from us-east-1) |
| Triggered by | Many AWS services | **CloudFront events** only |
| VPC, layers, env vars | Supported | **Not supported** |
| Limits | Up to 15 min, 10 GB | 5 s / 30 s, see above |

## Other Features

- **Custom error pages** and caching of error responses (error caching minimum TTL).
- **Default root object** (for example `index.html`).
- **Compression** (gzip, Brotli) at the edge.
- **Real-time logs** (to Kinesis Data Streams), **standard access logs** (to S3), and CloudWatch metrics.
- **Streaming / media**: video on demand, live streaming with MediaPackage; supports HLS, DASH.
- **Dedicated static IPs** are not provided by default (IPs change). Use Global Accelerator if you need static IPs.
- **Upload acceleration**: PUT/POST can be forwarded to the origin through edge locations (a distribution can accept uploads).
- **Continuous deployment** (staging distribution) for safe config changes.

## Pricing Notes

- Pay for **data transfer out** to the internet (per GB, cheaper at higher volume and by region) and **number of requests** (HTTP/HTTPS).
- **Data transfer from an AWS origin (S3, ALB, EC2) to CloudFront is free.**
- Free tier: 1 TB data out and 10 million requests per month (always free).
- **Price classes**: All (best performance), 200 (excludes the most expensive regions), 100 (cheapest regions only).
- Invalidations beyond the free quota and Lambda@Edge / Functions are charged extra.

## CloudFront vs S3 Cross-Region Replication

| | CloudFront | S3 CRR |
|---|---|---|
| Purpose | Global **cached** delivery, **read-only**, TTL based | **Replicate** a bucket to another region, near real-time |
| Content | Cached at **edge** (many locations) | Files stored in the **destination region** (must configure per region) |
| Best for | Static content available everywhere | Dynamic content needed with low latency in few regions, DR |

## CloudFront vs Global Accelerator

| | CloudFront | Global Accelerator |
|---|---|---|
| Caching | **Yes** (edge cache) | **No** |
| Protocols | HTTP/HTTPS, WebSocket | Any **TCP/UDP** |
| IPs | Changing | **2 static anycast IPs** |
| Use for | Cacheable web content, video, APIs | Gaming, IoT, VoIP, static IP, fast failover |

See [Global Accelerator](../GlobalAccelerator/README.md) for details.

## Typical Architectures

```
Static website:   User → CloudFront (+ WAF) → S3 (private, OAC)
Dynamic app:      User → CloudFront → ALB → ASG of EC2
Mixed:            /static/* → S3 origin      /api/* → ALB origin   (two behaviors)
Custom domain:    Route 53 alias record → CloudFront distribution (+ ACM cert in us-east-1)
```

## Exam Tips

- "Reduce latency for **global users**, **cache** static content at the edge" → **CloudFront**.
- "Keep the S3 bucket **private** but served only via CloudFront" → **Origin Access Control (OAC)** (legacy: OAI).
- "Restrict content to **paying users** / temporary access" → **signed URLs** (single file) or **signed cookies** (many files).
- "Restrict by **country**" → CloudFront **geo restriction** (or Route 53 geolocation for DNS-level routing).
- "Protect from web exploits / DDoS at the edge" → **AWS WAF** + **Shield** on CloudFront.
- "Custom domain with HTTPS on CloudFront" → **ACM certificate in us-east-1**.
- "Update content **immediately**" → **invalidation** (or versioned object names).
- "Lightweight header/URL manipulation at massive scale and lowest cost" → **CloudFront Functions**; "needs network calls or origin-level triggers" → **Lambda@Edge**.
- Lambda@Edge: **create in us-east-1**, 4 triggers (viewer/origin x request/response); **origin triggers run only on cache miss**, viewer triggers on every request.
- "Run code at the edge that **changes which origin** is used, or **calls external services**" → **Lambda@Edge** (CloudFront Functions can't).
- "Origin **high availability**" → **origin group** (failover).
- "**Static IPs** or **non-HTTP** traffic" → **Global Accelerator**, not CloudFront.
- "Encrypt **specific form fields** end to end" → **field-level encryption**.
- "Different origins per path (`/api` vs `/static`)" → multiple **behaviors** in one distribution.
- CloudFront is **global**, and is **not** the same as S3 Cross-Region Replication (CDN cache vs real copies).
- Data transfer **from S3/ALB/EC2 to CloudFront is free**; cost comes from CloudFront to the internet.
