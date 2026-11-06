# Auto Scaling and Elastic Load Balancing

## Auto Scaling Groups (ASG)

An ASG maintains a fleet of EC2 instances: **min / desired / max** capacity across multiple AZs.

- Replaces unhealthy instances (EC2 status checks or ELB health checks).
- Free: pay only for the resources it launches.
- Uses a **Launch Template** (AMI, type, SGs, key, user data, IAM role, EBS, Spot/On-Demand mix). Launch Configurations are deprecated.
- Spans subnets in multiple AZs → high availability.
- Integrates with ELB target groups.

### Scaling Policies

| Policy | How it works |
|---|---|
| **Target tracking** | Keep a metric at a target (e.g. average CPU 50%). Simplest |
| **Step scaling** | Different adjustments depending on alarm breach size |
| **Simple scaling** | One alarm, one action, then cooldown |
| **Scheduled** | Known patterns (e.g. every Monday 9am) |
| **Predictive** | ML forecast from history |

- Common metrics: CPU, network in/out, `ALBRequestCountPerTarget`, custom CloudWatch metrics (e.g. queue depth in SQS).
- **Cooldown** (default 300 s) prevents thrashing; **instance warm-up** for new instances.
- **Scale-in protection**, **lifecycle hooks** (pause at launch/terminate to run custom actions), **instance refresh** (rolling AMI updates), **warm pools** for faster scale-out.
- Termination policy default: balance AZs, then oldest launch template/config, then closest to next billing hour.

## Elastic Load Balancing (ELB)

Distributes traffic across targets in multiple AZs; managed, highly available, performs **health checks**.

| Type | Layer | Protocols | Notes |
|---|---|---|---|
| **Application (ALB)** | 7 | HTTP, HTTPS, gRPC, WebSocket | Path/host/header/query routing, Lambda/IP/instance targets, OIDC/Cognito auth, WAF; fixed DNS name |
| **Network (NLB)** | 4 | TCP, UDP, TLS | Millions of req/s, ultra-low latency, **static IP / Elastic IP per AZ**, PrivateLink |
| **Gateway (GWLB)** | 3 | GENEVE (6081) | Route traffic through third-party virtual appliances (firewalls, IDS) |
| **Classic (CLB)** | 4/7 | Legacy | Deprecated |

### Features

- **Target groups**: instances, IPs, Lambda, ALB (for NLB).
- **Cross-zone load balancing**: ALB on by default (free); NLB/GWLB off by default (inter-AZ charges when on).
- **Sticky sessions**: cookie-based affinity (duration-based or application cookie).
- **Connection draining / deregistration delay** (default 300 s).
- **SSL/TLS termination** with ACM certificates; **SNI** for multiple certs on one listener.
- **Client IP**: ALB passes it in `X-Forwarded-For`; NLB preserves source IP.
- Security: SG on ALB; instances' SG allows traffic **from the ALB SG** only.

## Typical 3-Tier Pattern

Route 53 → ALB (public subnets) → ASG of EC2 (private subnets) → RDS Multi-AZ (data subnets).

## Exam Tips

- "Route by URL path / host" → ALB.
- "Static IP, extreme performance, TCP/UDP" → NLB.
- "Inspect traffic with third-party appliance" → GWLB.
- "Scale on queue backlog" → ASG with custom SQS-based metric.
- "Self-healing, high availability" → ASG across ≥2 AZs behind ELB.
