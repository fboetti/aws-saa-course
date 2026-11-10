# AWS Global Accelerator

**AWS Global Accelerator** gives your application **two static anycast IP addresses** and routes user traffic over the **AWS global network** to the best healthy endpoint, improving performance and availability for global users.

Related notes: [Route 53](../Route53/README.md), [Elastic Load Balancing](../EC2/elastic-load-balancing.md), [VPC](../VPC/README.md).

## The Problem It Solves

Without it, users reach your app over the public internet: many hops, variable latency, and DNS caching slows failover. With Global Accelerator, users enter the AWS network at the **nearest edge location** and travel on the AWS backbone to your region.

## How It Works

1. You create an **accelerator**. AWS assigns **2 static anycast IPv4 addresses** (optionally dual-stack with 2 IPv6, or **bring your own IP** range via BYOIP). They don't change for the life of the accelerator.
2. The IPs are advertised from **edge locations worldwide**; a user's traffic is routed to the **closest edge**.
3. From the edge, traffic goes over the **AWS global network** to a healthy endpoint in the closest/best region.
4. Health checks detect failures and shift traffic in **seconds** (no DNS TTL wait).

## Components

| Component | Meaning |
|---|---|
| **Accelerator** | The resource with the 2 static IPs and a DNS name |
| **Listener** | Port(s) and protocol (**TCP** or **UDP**) it accepts. Optional client affinity (source IP) |
| **Endpoint group** | One per **region**. Has a **traffic dial** (0 to 100%) and health check settings |
| **Endpoint** | **ALB, NLB, EC2 instance, or Elastic IP**, with optional **weight** |

- **Traffic dial**: percentage of traffic sent to a region's endpoint group (for example 0% for maintenance, or gradually increase for a new region).
- **Endpoint weights** (0 to 255): split traffic between endpoints in a group.
- **Client IP preservation**: supported for ALB, EC2 and (with config) NLB endpoints.
- Endpoints can be **internet-facing or internal**; internal ALB/NLB reachable through the accelerator are supported too.
- **Custom routing accelerator**: map users deterministically to a **specific EC2 instance and port** (for example game sessions or VoIP) in a VPC subnet.

## Global Accelerator vs CloudFront

| | Global Accelerator | CloudFront |
|---|---|---|
| Purpose | Accelerate **any TCP/UDP** app via the AWS backbone | **Cache and deliver** web content at the edge |
| Caching | **No** | **Yes** |
| Protocols | TCP, UDP | HTTP/HTTPS, WebSocket |
| Good for | Gaming, IoT, VoIP, **static IPs**, non-HTTP, fast regional failover | Websites, video, static and dynamic content |
| Entry | 2 static anycast IPs | DNS name (changing IPs) |

Both use the AWS global network and edge locations, and both integrate with **AWS Shield** and DDoS protection.

## Global Accelerator vs Route 53

| | Global Accelerator | Route 53 |
|---|---|---|
| Mechanism | **Network-level** anycast routing | **DNS** answers |
| Failover speed | **Seconds**, no client caching issue | Depends on **TTL** and resolver caching |
| IPs | **Static**, stable (whitelistable) | Return the targets' own IPs |
| Extras | Traffic dial, weights | Many routing policies (geo, latency, weighted...) |

Use Route 53 *and* Global Accelerator together: a Route 53 alias record can point at the accelerator.

## Benefits

- **Static IPs**: easy firewall whitelisting, no DNS dependency.
- **Better performance**: up to about **60%** improvement vs the public internet (AWS figure), lower jitter.
- **Fast failover** across regions and AZs with health checks.
- **Security**: DDoS protection with **AWS Shield Standard** (Advanced optional); private endpoints stay in your VPC.
- Works with **single-region** apps too (static IPs and edge entry).

## Pricing Notes

- Hourly fee per accelerator plus a **Data Transfer-Premium (DT-Premium)** fee per GB, based on the direction with the higher volume.
- No charge for the endpoints themselves beyond their normal costs.

## Typical Architecture

```
Users worldwide
   └─ 2 static anycast IPs (Global Accelerator)
        ├─ eu-west-1: endpoint group (dial 50%) → ALB → ASG
        └─ us-east-1: endpoint group (dial 50%) → ALB → ASG
```

## Exam Tips

- "Need **static IPs** for a global app / clients must whitelist IPs" → **Global Accelerator** (or NLB for a single region).
- "**Non-HTTP** (TCP/UDP) global app: gaming, IoT, VoIP" → **Global Accelerator**.
- "**Fast regional failover** without waiting for DNS TTL" → **Global Accelerator**.
- "**Cache** content at the edge / reduce load on origin" → **CloudFront**, not Global Accelerator.
- "Shift a percentage of traffic between regions" → **traffic dial** (or weights).
- "Static IPs **and** path-based routing" → Global Accelerator → ALB (or NLB → ALB).
- Global Accelerator is a **global** service; endpoints are **regional** (ALB, NLB, EC2, Elastic IP).
