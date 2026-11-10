# Amazon Route 53

Notes on **Amazon Route 53**, AWS's highly available, scalable **DNS** service, **domain registrar** and **health-checking** service, refined for the **SAA-C03** exam. The name comes from DNS port **53**.

Related notes: [Elastic Load Balancing](../EC2/elastic-load-balancing.md), [Auto Scaling Groups](../EC2/auto-scaling-groups.md), [VPC](../VPC/README.md).

## What Route 53 Does

1. **Domain registration**: buy and renew domain names (also transfer them in).
2. **DNS hosting**: hosted zones hold the records that answer DNS queries.
3. **Traffic routing**: routing policies decide *which* answer to return (latency, weighted, failover...).
4. **Health checks**: monitor endpoints and stop returning unhealthy ones.

Key facts:

- **Global service** (not tied to a region), with a **100% availability SLA**. It is the only AWS service with that SLA.
- Authoritative DNS: you control the records.
- Uses **anycast** across a global network of edge locations.
- Pricing: per hosted zone per month, per million queries, per health check. **Alias queries to AWS resources are free.**

## DNS Refresher

| Term | Meaning |
|---|---|
| **Domain name** | Human-readable name, for example `example.com` |
| **FQDN** | Fully qualified name, for example `www.api.example.com.` |
| **TLD** | Top-level domain: `.com`, `.org`, `.io` |
| **SLD / apex** | `example.com`, the root of your zone (also "zone apex" or "naked domain") |
| **Name server (NS)** | Server that answers queries for a zone |
| **Registrar** | Company where the domain is registered (Route 53, GoDaddy...) |
| **Zone file** | The collection of records for a domain |
| **Resolver** | Recursive DNS server that does lookups for clients (ISP, `8.8.8.8`, VPC resolver) |
| **TTL** | How long (seconds) resolvers cache an answer |

Resolution flow: client → recursive resolver → **root** → **TLD** (`.com`) → **authoritative** name server (Route 53) → answer is cached for the TTL.

## Record Types

Record sets are a collection of records which determine where to send traffic.

| Type | Maps | Example |
|---|---|---|
| **A** | Name → IPv4 | `app.example.com → 203.0.113.10` |
| **AAAA** | Name → IPv6 | |
| **CNAME** | Name → another name | `www → app.example.com` |
| **NS** | Delegates a zone to name servers | The 4 NS records of your hosted zone |
| **SOA** | Zone metadata (primary NS, serial, refresh) | Created automatically |
| **MX** | Mail servers (with priority) | |
| **TXT** | Free text (SPF, DKIM, domain verification) | |
| **CAA** | Which CAs may issue certificates | |
| **SRV** | Service host and port | |
| **PTR** | IP → name (reverse DNS) | |
| **DS** | DNSSEC delegation signer | |

A record contains: **name**, **type**, **value(s)**, **TTL**, and optionally a **routing policy**.

### CNAME vs Alias (very common exam topic)

| | CNAME | Alias |
|---|---|---|
| Points to | Any DNS name | **AWS resource** only |
| **Zone apex** (`example.com`) | **Not allowed** | **Allowed** |
| Cost | Standard query charge | **Free** for queries to AWS resources |
| Health | No | Can use **Evaluate Target Health** |
| Record type shown | CNAME | **A or AAAA** (it is a Route 53 extension) |
| TTL | You set it | Set by Route 53 (inherited from the target) |

Alias targets: **ELB**, **CloudFront**, **API Gateway**, **Elastic Beanstalk**, **S3 static website endpoint**, **VPC interface endpoints**, **Global Accelerator**, another record **in the same hosted zone**.
**Cannot** alias to an **EC2 instance DNS name** (use an A record with the IP or Elastic IP).

Rule of thumb: pointing at an AWS resource → **Alias**. Pointing at a non-AWS name → CNAME (not at the apex).

## Hosted Zones

A container for the records of one domain.

| | Public hosted zone | Private hosted zone |
|---|---|---|
| Answers | Queries from the **internet** | Queries from **associated VPCs** only |
| Use | Public websites and APIs | Internal names such as `db.internal.example.com` |
| Setup | Update the registrar's NS records to the zone's 4 NS | Associate one or more VPCs (even cross-account/region) |

- Cost: about **$0.50 per hosted zone per month** (first 25), plus queries.
- A new public hosted zone gets **4 NS records**. If the domain is registered elsewhere, copy them to the registrar.
- Private zones need VPC settings **`enableDnsHostnames`** and **`enableDnsSupport`** set to true.
- A private and a public zone with the same name enable **split-horizon DNS** (different answers inside and outside).
- Deleting a hosted zone and recreating it gives **new NS records**. Update the registrar.

## TTL

- **High TTL** (for example 24 h): fewer queries, cheaper, but changes propagate slowly.
- **Low TTL** (for example 60 s): fast changes and failover, more queries.
- Lower the TTL **before** a planned migration, then raise it again afterwards.
- Alias records have no configurable TTL.

## Routing Policies

| Policy | What it does | Health checks? | Typical use |
|---|---|---|---|
| **Simple** | Returns one record (or several values in random order, client picks) | No | One resource, no logic |
| **Weighted** | Split traffic by weights (0 to 255). Weight 0 = no traffic | Yes | A/B tests, canary/blue-green, gradual migration |
| **Latency-based** | Sends users to the REGION with the **lowest latency** | Yes | Global apps with multi-region deployments |
| **Failover** | **Active-passive**: primary, then secondary when primary is unhealthy | **Required** on primary | Disaster recovery |
| **Geolocation** | By the user's **location** (continent, country, US state) | Yes | Localisation, content restrictions, legal/compliance. Needs a **default** record |
| **Geoproximity** | By **distance** to resources, with a **bias** to shift traffic. Needs **Traffic Flow** | Yes | Shift load toward/away from a region |
| **IP-based** | By the client's **CIDR** (IP ranges you define) | Yes | Route known ISPs/corporate networks to specific endpoints |
| **Multivalue answer** | Up to **8 healthy** records returned at random | Yes | Cheap client-side load balancing. **Not a substitute for ELB** |

Key distinctions:

- **Latency ≠ Geolocation**: latency = *fastest* region, geolocation = *where the user is* (rules, not speed).
- **Geolocation ≠ Geoproximity**: geolocation uses fixed political regions; geoproximity uses distance and a tunable bias.
- **Multivalue ≠ Simple**: multivalue returns only **healthy** records and supports health checks.
- Weighted, latency, failover, geo, multivalue etc. need a unique **Set Identifier** per record.
- **Traffic Flow** is a visual editor (very expensive) for building complex routing trees, versioned as **traffic policies**.

## Health Checks

Route 53 health checkers (in many regions) probe endpoints and mark them healthy/unhealthy.

| Type | Monitors |
|---|---|
| **Endpoint** | An IP or domain over HTTP, HTTPS or TCP (optionally string matching in the first 5120 bytes of the response) |
| **Calculated** | Combines other health checks with AND / OR / "at least N of" |
| **CloudWatch alarm** | The state of an alarm. Use this for **private resources** and custom metrics |

- About **15 global checkers**; interval 30 s (standard) or 10 s (fast, extra cost); default threshold 3 failures.
- Healthy when **> 18%** of checkers report healthy.
- Checkers come from **public IPs**: you must allow them in the firewall/security group.
- Route 53 health checkers **cannot reach private resources** (inside a VPC). Create a **CloudWatch alarm** on a metric and have the health check watch the alarm.
- Health checks can trigger **SNS** notifications via CloudWatch alarms.
- An **alias record with Evaluate Target Health** uses the target's own health (for example an ELB) without a separate health check.

## Failover Pattern

```
primary   (Failover=PRIMARY)   → ALB in eu-west-1, linked health check
secondary (Failover=SECONDARY) → static S3 website or ALB in another region
```

When the primary's health check fails, Route 53 starts answering with the secondary.

## Domain Registration and Transfers

- Register and auto-renew domains in Route 53, or register elsewhere and **only use Route 53 for DNS** (change NS at the registrar).
- Registrar and DNS host are independent: you can register in Route 53 and host DNS elsewhere, or the reverse.
- **Domain transfer** needs an authorisation code, the domain unlocked and older than 60 days. Registration takes up to a few days.
- Enable **transfer lock** and **auto-renew** to prevent loss of the domain.

## DNSSEC

- Protects against **DNS spoofing and cache poisoning** by signing records.
- Route 53 supports **DNSSEC signing** for public hosted zones using a **KMS asymmetric key** (must be in **us-east-1**, ECC_NIST_P256).
- Establish the chain of trust by adding a **DS record** at the parent (registrar/TLD).
- Route 53 can also act as a **DNSSEC-enabled registrar**.

## Route 53 Resolver (Hybrid DNS)

The VPC DNS resolver (the **`.2`** address, `169.254.169.253`) answers queries inside a VPC automatically. For **hybrid** setups:

| Endpoint | Direction | Use |
|---|---|---|
| **Inbound endpoint** | On-premises → AWS | On-prem servers resolve **private hosted zone** names in AWS |
| **Outbound endpoint** | AWS → on-premises | VPC instances resolve **on-prem** names, via **forwarding rules** |

- Endpoints are ENIs in your VPC (at least 2 AZs for HA), traffic goes over **VPN or Direct Connect**.
- **Resolver rules** (forward or system) can be shared across accounts with **AWS RAM**.
- **Resolver DNS Firewall**: allow/block outbound DNS queries from VPCs by domain lists (data exfiltration protection).
- **Query logging**: public zone queries and Resolver queries can go to CloudWatch Logs, S3 or Kinesis Data Firehose.

## Route 53 Application Recovery Controller (ARC)

- Helps with **multi-region / multi-AZ failover** for application recovery.
- **Readiness checks**, **routing controls** (on/off switches that shift traffic via health checks), **safety rules** to prevent bad failovers.
- Also hosts **zonal shift** (move traffic away from an impaired AZ).

### Zonal Shift

Temporarily moves a load balancer's traffic **away from one AZ** to the healthy AZs, so a single-AZ problem (bad deploy, power or network issue) doesn't hurt users.

- Supported on **ALB and NLB** (originally only with cross-zone load balancing disabled; check current docs for cross-zone limits), and on **EKS** and **Auto Scaling groups** (the ASG won't launch into the shifted AZ).
- Works by **stopping the LB from sending new traffic to targets in that AZ**. Existing connections drain; no change to your instances.
- **Temporary**: you set an expiry from **1 minute up to 3 days**, and can extend or cancel it.
- **Manual** (console/CLI/API, you start the shift) or **zonal autoshift**: AWS shifts traffic **automatically** when it detects an AZ impairment, and runs periodic **practice runs** to check you can survive losing an AZ.
- Needs **enough capacity in the other AZs** to absorb the traffic, otherwise the shift can cause overload.
- No extra cost.

**Exam tip:** "Quickly shift traffic away from an impaired AZ without changing DNS or infrastructure" → **zonal shift**.

## Common Architectures

**Website on ALB:** `www.example.com` → Alias A → ALB (+ Evaluate Target Health).

**Static site at the apex:** `example.com` → Alias A → CloudFront distribution (or S3 website endpoint).

**Multi-region active-active:** Latency records → one ALB per region, each with health checks.

**DR active-passive:** Failover records → primary region ALB, secondary static site or standby region.

**Internal service names:** Private hosted zone `corp.internal` associated with the VPCs, records like `db.corp.internal` → RDS endpoint (CNAME).

**Hybrid:** Resolver inbound + outbound endpoints over VPN/Direct Connect.

## Exam Tips

- "Map the **zone apex** to an ELB/CloudFront" → **Alias** record (CNAME is not allowed at the apex).
- "Cheapest way to point a name at an AWS resource" → **Alias** (no query charge).
- "Route users to the **lowest latency** region" → **Latency** policy.
- "Route by **country/continent**, legal restrictions, localised content" → **Geolocation** (add a default record).
- "Shift traffic toward a region using a **bias**" → **Geoproximity** (Traffic Flow).
- "Gradually send 10% of traffic to a new version" → **Weighted**.
- "Active-passive disaster recovery" → **Failover** + health check.
- "Return only healthy IPs, up to 8" → **Multivalue answer**. It does **not** replace a load balancer.
- "Route by the client's IP range / ISP" → **IP-based**.
- Health check for a **private** resource → **CloudWatch alarm** health check.
- Resolve names between **on-premises and a VPC** → Route 53 **Resolver inbound/outbound endpoints**.
- Internal-only names inside a VPC → **private hosted zone** (VPC DNS support and hostnames enabled).
- Block malicious domain lookups from the VPC → **Route 53 Resolver DNS Firewall**.
- Public DNS integrity → **DNSSEC** (KMS key in **us-east-1**).
- Domain registered at another registrar → create a hosted zone and update the registrar's **NS records**.
- Route 53 is **global** and has a **100% SLA**.
