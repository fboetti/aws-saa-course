# Amazon VPC Lattice — Exam Notes

**VPC Lattice** is a fully managed **application-layer (L7) networking service** that
connects, secures and monitors **service-to-service** communication across **VPCs and
accounts**, without VPC peering, Transit Gateway, PrivateLink or a service mesh sidecar.

```
 Client (VPC A) ──> Service network ──> Service (HTTP/HTTPS/gRPC) ──> Target group (VPC B)
                    auth policy + SG       listener + rules            EC2 / ECS / EKS / Lambda / ALB / IP
```

## Core components

| Component | What it is |
|---|---|
| **Service** | An application (like a microservice) with a DNS name, **listeners** (HTTP, HTTPS, gRPC) and **rules** |
| **Target group** | The compute that serves requests: **EC2 / ASG, ECS, EKS (pods), Lambda, ALB, IP addresses** |
| **Service network** | Logical boundary that groups services; **VPCs and services are associated** with it |
| **Auth policy** | **IAM resource policy** on a service or service network; authenticates with **SigV4** |
| **Access logs / monitoring** | To **S3, CloudWatch Logs, Kinesis Data Firehose**; metrics in CloudWatch |

## How it works

1. Create **services** (listener + rules + target groups).
2. Create a **service network** and associate the services.
3. **Associate client VPCs** with the service network (optionally with a security group).
4. Clients resolve the service's DNS name (link-local range `169.254.171.0/24` / `fd00:ec2::/32`) and Lattice routes to targets.
5. Share across accounts with **AWS RAM** (share the service or service network).

## Key features

- **Works with overlapping CIDRs** — no IP routing between VPCs, so no CIDR planning.
- **No transitive-peering/route-table headaches**: no peering, TGW or route changes.
- **Layer 7 routing**: path/header/method rules, **weighted routing** (blue/green, canary).
- **Auth**: IAM auth policies + SigV4, plus SG on the VPC association; **TLS** supported (ACM certificates, custom domains).
- **Mixed compute** behind one service: EC2, containers and Lambda together.
- **Cross-account and cross-VPC** via RAM; **same Region** only.
- **Observability** built in: access logs and CloudWatch metrics.
- Pricing: per service/hour + per GB + per request.

## VPC Lattice vs other connectivity options

| | **VPC Lattice** | **VPC Peering** | **Transit Gateway** | **PrivateLink** | **App Mesh (retiring)** |
|---|---|---|---|---|---|
| Layer | **L7** (HTTP/HTTPS/gRPC) | L3 | L3 | L4 (TCP/TLS) | L7 (sidecar proxy) |
| Overlapping CIDRs | **Yes** | No | No | **Yes** | n/a |
| Direction | Any client -> service | Full mesh of IPs | Full IP routing | **One-way** consumer -> provider | Service to service |
| Auth / per-request policy | **IAM auth policy** | SG / NACL only | SG / NACL only | Endpoint policy, SG | mTLS |
| Operational effort | Low (managed) | Low, but routes | Medium | Low-medium (NLB + endpoints) | Higher (sidecars) |
| Best for | **Microservices** across VPCs/accounts | A few VPCs, any protocol | Many VPCs/on-prem hub | Expose **one service** privately | Containers only |

## Exam tips

- **"Connect microservices across many VPCs/accounts, overlapping CIDRs, without
  managing peering/TGW/sidecars, with centralized auth"** -> **VPC Lattice**.
- **IAM-based, per-service authorization (SigV4) at the network layer** -> Lattice **auth policies**.
- **Expose a single service to other VPCs, one-way, TCP** -> **PrivateLink**, not Lattice.
- **Full IP connectivity / many VPCs + on-prem** -> **Transit Gateway**; Lattice is app-layer only, not general IP routing.
- Lattice handles **HTTP/HTTPS/gRPC**; non-HTTP TCP workloads (databases, custom protocols) are not its fit.
- **Weighted/path-based routing** for canary or blue/green between services -> Lattice rules.
- Targets can be **Lambda** and **ALB**, so it fits serverless and mixed estates.
- **Same Region** only; use **RAM** to share across accounts.
- Not the same as **ALB**: an ALB is one load balancer inside a VPC; Lattice is a cross-VPC service network.

## Sample questions

1. *Dozens of microservices in different VPCs and accounts with overlapping CIDRs must
   call each other, with IAM-based authorization and minimal operational overhead.* ->
   **VPC Lattice** service network, shared with RAM.
2. *A provider wants to expose one internal TCP service to customer VPCs privately.* ->
   **PrivateLink** (NLB + endpoint service).
3. *Route 10% of traffic to a new version of a service across VPCs.* -> Lattice
   **weighted target groups** in a listener rule.
4. *Hub connectivity for 50 VPCs plus on-premises over Direct Connect.* ->
   **Transit Gateway** (not Lattice).

## References

- VPC Lattice docs: https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html
- VPC Lattice pricing: https://aws.amazon.com/vpc/lattice/pricing/
- Related notes: [VPC overview](../README.md), [VPC Endpoints / PrivateLink](../vpc-endpoints/README.md), [VPC Sharing with AWS RAM](../vpc-sharing/README.md), [Security Groups](../security-groups/README.md)
