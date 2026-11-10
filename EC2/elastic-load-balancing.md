# Elastic Load Balancing (ELB)

A Load Balancer is physical hardware or virtual software that accepts incoming traffic and then distributes the traffic to multiple targets, by balancing the load
via different rules. 

**Elastic Load Balancing** is a SUITE of load balancers (ALB, NLB, GWLB, CLB) that distributes incoming traffic across multiple targets (EC2 instances, containers, IPs, Lambda) in one or more AZs. It is a **managed, regional, highly available** service that scales automatically and runs **health checks** so traffic only goes to healthy targets.

Why use it:

- Single entry point (one DNS name) in front of many servers.
- **High availability** across AZs and **fault tolerance** (unhealthy targets are skipped).
- Works with [Auto Scaling Groups](auto-scaling-groups.md) for elasticity.
- Offloads **TLS termination**, authentication and (with ALB) WAF integration.
- Decouples the client from the number and IPs of backend servers.

## Types at a Glance

| Type | Layer | Protocols | Best for |
|---|---|---|---|
| **Application (ALB)** | 7 | HTTP, HTTPS, gRPC, WebSocket | Web apps, microservices, content-based routing |
| **Network (NLB)** | 4 | TCP, UDP, TLS, TCP_UDP | Extreme performance, static IPs, non-HTTP protocols |
| **Gateway (GWLB)** | 3 (+4) | IP, GENEVE (port 6081) | Third-party virtual appliances (firewall, IDS/IPS, DPI) |
| **Classic (CLB)** | 4 and 7 | HTTP/S, TCP, SSL | Legacy EC2-Classic era. **Deprecated**, migrate away |

## Application Load Balancer (ALB)

- Layer 7, Understands HTTP: routes on **path**, **host header**, **HTTP header**, **query string**, **HTTP method** and **source IP**.
- Listener **rules** (priority-ordered) with actions: forward, redirect (HTTP → HTTPS), fixed response, authenticate (OIDC, Cognito).
- Targets: **instances, IP addresses** (including on-premises via VPN/Direct Connect), **Lambda**. Multiple target groups per ALB, so one ALB can serve many microservices.
- Supports **HTTP/2**, **WebSocket**, **gRPC**, and **weighted target groups** (blue/green and canary).
- Client IP is in the **`X-Forwarded-For`** header (also `X-Forwarded-Proto`, `X-Forwarded-Port`). The target sees the ALB's private IP as the source.
- Integrates with **AWS WAF**, **Cognito**, **ACM**, **CloudWatch**, and is a valid **CloudFront** origin.
- Gets a **fixed DNS name** only; IPs change. For static IPs use NLB, or put **Global Accelerator** in front, or NLB → ALB targets.
- Must span **≥ 2 AZs** (one subnet per AZ).

## Network Load Balancer (NLB)

- Layer 4, handles **millions of requests per second** at **ultra-low latency**, and sudden spiky traffic.
- **One static IP per AZ**, and you can attach an **Elastic IP** per AZ. Good when clients must whitelist IPs.
- **Preserves the client source IP** (for instance targets) with no `X-Forwarded-For` needed.
- Protocols: TCP, UDP, TLS (termination with ACM certs), TCP_UDP.
- Targets: instances, IPs, and an **ALB** (to combine static IPs with L7 routing).
- Backbone of **AWS PrivateLink** (VPC endpoint services).
- Supports **security groups** (since 2023). Health checks can be TCP, HTTP or HTTPS.
- Not in the free tier; billed per hour and per **LCU/NLCU**.

## Gateway Load Balancer (GWLB)

- Combines a **transparent network gateway** (single entry/exit for all traffic) and a **load balancer** that spreads traffic across a fleet of **virtual appliances**.
- Uses the **GENEVE protocol on UDP 6081** to wrap packets and keep original source/destination.
- Typical flow: route table → **GWLB endpoint** (GWLBE) → GWLB → appliance → back to GWLB → destination.
- Use for: firewalls, intrusion detection/prevention, deep packet inspection, payload manipulation. Often from AWS Marketplace partners.
- Target groups: instances or IPs.

## Core Concepts

| Concept | Meaning |
|---|---|
| **Listener** | Process that checks for connection requests on a protocol and port (for example HTTPS:443) and applies rules |
| **Rule** | Condition(s) + action, evaluated by priority (ALB). A default rule catches the rest |
| **Target group** | Set of targets plus protocol/port and health check settings. A target can be in several groups |
| **Target** | Instance, IP, Lambda function, or ALB |
| **Health check** | Probe (protocol, path, port, interval, timeout, healthy/unhealthy thresholds, success codes) that decides if a target gets traffic |
| **Scheme** | **Internet-facing** (public subnets, public IPs) or **internal** (private IPs only, for backend tiers) |
| **Node** | The load balancer's network interface in each enabled AZ |

- Target group **target types**: `instance` (by ID), `ip` (any private IP, including on-premises or peered VPCs), `lambda`, `alb`.
- An unhealthy target is not removed from the group, only skipped until it passes checks again.
- If **all** targets are unhealthy, ALB/NLB use **fail-open** and send traffic to all targets anyway.

## Cross-Zone Load Balancing

Each LB node normally sends traffic only to targets in its own AZ. **Cross-zone** lets every node spread requests across targets in **all enabled AZs**, which evens out load when AZs have unequal target counts.

| Type | Default | Inter-AZ data charge |
|---|---|---|
| **ALB** | **On** (can be disabled per target group) | No charge |
| **NLB** | Off | Charged when enabled |
| **GWLB** | Off | Charged when enabled |
| **CLB** | Off in API/CLI, on in console | No charge |

## Security Groups and Networking

- ALB (and now NLB) use **security groups**. Pattern: LB SG allows 80/443 from the internet, **instance SG allows traffic only from the LB SG**.
- Instances can sit in **private subnets**; only the LB nodes need public subnets for an internet-facing scheme.
- The LB needs a subnet in each AZ you enable, with enough free IPs (min /27 recommended).
- Targets must allow health check traffic from the LB.

## TLS/SSL

- **SSL/TLS termination** at the LB using certificates from **ACM** (or IAM / imported). Backend traffic can be HTTP or re-encrypted (HTTPS).
- **SNI (Server Name Indication)**: multiple certificates and domains on **one listener** (ALB, NLB). Not supported on CLB.
- **Security policies** define allowed TLS versions and ciphers.
- NLB can pass TLS through untouched (TCP listener) for end-to-end encryption, or terminate with a TLS listener.
- ALB **mutual TLS (mTLS)** is supported for client certificate authentication.

## Sticky Sessions (Session Affinity)

Keep a client on the same target.

- **Duration-based cookie**: LB generates `AWSALB` (ALB) or `AWSELB` (CLB). Duration from 1 second to 7 days.
- **Application-based cookie**: custom cookie set by the app, or LB-generated `AWSALBAPP`.
- Works with ALB, NLB (source-IP based) and CLB. Can cause **uneven load**; prefer storing sessions externally (**ElastiCache**, **DynamoDB**) for stateless servers.

## Connection Draining (Deregistration Delay)

- When a target is deregistered or unhealthy, in-flight requests get time to finish before the target is removed.
- Default **300 s**, range 0 to 3600 s. Set low for short requests, higher for long uploads.
- Called **connection draining** on CLB, **deregistration delay** on ALB/NLB/GWLB.

## Other Features

- **Slow start mode** (ALB): ramp up traffic to a new target gradually.
- **Load balancing algorithms** (ALB): round robin (default), least outstanding requests. NLB uses flow hash.
- **Access logs** to S3 (off by default), **request tracing** (`X-Amzn-Trace-Id`), **CloudWatch metrics**, **CloudTrail** for API calls.
- **Deletion protection**, **idle timeout** (ALB default 60 s), **HTTP desync mitigation**.
- **Zonal shift** (ARC): move traffic away from an impaired AZ.
- **IPv6 / dual-stack** support (ALB, NLB).
- **Lambda** as an ALB target: serverless HTTP backends.

## Choosing a Load Balancer

```
Need to inspect/route by URL, host, headers, or use Lambda/WAF/Cognito? → ALB
Need TCP/UDP, static/Elastic IP, source IP preserved, extreme throughput? → NLB
Need to insert a firewall / IDS appliance transparently? → GWLB
Need static IPs AND path routing? → NLB → ALB, or Global Accelerator → ALB
```

## Typical Architecture

```
Route 53 (alias record) → internet-facing ALB (public subnets, 2+ AZs)
        └─ target group → ASG of EC2 (private subnets)
                              └─ RDS Multi-AZ (data subnets)
```

Use an **alias record** in Route 53 pointing to the LB DNS name (free, works at the zone apex), not a CNAME.

## Exam Tips

- "Route by URL path or hostname", "microservices", "HTTP/HTTPS", "WAF", "Cognito auth" → **ALB**.
- "Static IP / Elastic IP", "TCP/UDP", "millions of req/s", "ultra-low latency", "PrivateLink" → **NLB**.
- "Third-party firewall / IDS inspect all traffic", "GENEVE" → **GWLB**.
- Backend needs the real client IP:
  - behind ALB → read **`X-Forwarded-For`**;
  - behind NLB → source IP is preserved.
- Clients must whitelist the LB's IPs → **NLB** (or Global Accelerator). ALB IPs change.
- Uneven traffic across AZs with different target counts → enable **cross-zone** (default on only for ALB).
- Several HTTPS domains on one LB → **SNI** with multiple ACM certificates.
- Users lose their session after being sent to a different instance → **sticky sessions**, or better, externalise session state.
- Remove an instance without dropping requests → **connection draining** (deregistration delay).
- Instance should only accept traffic from the LB → SG rule that references the **LB's security group**.
- Instances are "healthy" in EC2 but the app is down, and ASG does not replace them → enable **ELB health checks** in the ASG.
- ELB is **regional**; for multi-region failover use Route 53 or Global Accelerator.
- **Classic Load Balancer** is deprecated: the answer is rarely CLB.
