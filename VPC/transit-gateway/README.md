# AWS Transit Gateway (TGW) — Exam Notes

A **Transit Gateway** is a **regional, managed hub-and-spoke router** that connects VPCs,
VPNs and Direct Connect gateways through one central point, with **transitive routing**.
It replaces the N(N-1)/2 mesh of VPC peering connections with N attachments.

```
 VPC A ─┐                           ┌─ Site-to-Site VPN ── On-premises
 VPC B ─┼── attachments ──> [ TGW ] ┼─ DX gateway (transit VIF) ── Data center
 VPC C ─┘   (route tables)          └─ TGW peering ── TGW in another Region
```

## Core concepts

| Concept | What it is |
|---|---|
| **Attachment** | A connection to the TGW: **VPC**, **VPN**, **Direct Connect gateway**, **TGW peering**, **Connect** (SD-WAN/GRE) |
| **TGW route table** | Controls routing between attachments. Each attachment has one **association** (which table it uses) and can **propagate** its routes into one or more tables |
| **Propagation vs static** | Propagation learns routes automatically (VPC CIDRs, BGP from VPN/DX); static routes are manual |
| **Blackhole route** | Drops traffic to a CIDR (isolation) |
| **Appliance mode** | Keeps both directions of a flow on the **same AZ** appliance (needed for stateful inspection) |

## How to set one up

1. Create the TGW (choose ASN, default route table association/propagation).
2. Create a **VPC attachment**, selecting **one subnet per AZ** to use (a TGW ENI is placed there).
3. **Update the VPC route tables**: destination = other VPC/on-prem CIDR, target = `tgw-…`.
4. Configure TGW route tables (association + propagation) for segmentation.
5. Share across accounts/Organization with **AWS RAM**.

> Both sides need routes: the **VPC route table** (to the TGW) **and** the **TGW route table**
> (to the attachment). Forgetting the VPC side is the classic failure.

## Key features and limits

- **Transitive routing**: A <-> TGW <-> B, which peering cannot do.
- **Scale**: thousands of attachments; up to **5,000 VPC attachments** per TGW.
- **Bandwidth**: up to **50 Gbps burst per VPC attachment** (per AZ); VPN tunnel is
  **1.25 Gbps**, but **ECMP** across tunnels multiplies it (TGW is the **only** service that supports ECMP for VPN).
- **Regional resource**; connect Regions with **inter-Region TGW peering** (AWS backbone, encrypted, **static routes only**).
- **IP multicast** support (the only native AWS multicast option).
- **Cross-account** via RAM; can attach VPCs in other accounts.
- Supports **IPv4 and IPv6**; **no overlapping CIDRs** between attached VPCs (routes would conflict).
- **Security groups of different VPCs cannot be referenced** across the TGW (use CIDRs); SG referencing works with peering in the same Region but not TGW.
- **Pricing**: per attachment-hour + per GB processed. More expensive than peering for 2-3 VPCs.

## Common architectures

| Pattern | Design |
|---|---|
| **Segmentation** | Separate TGW route tables (prod / dev / shared); propagate only the allowed attachments |
| **Centralized egress** | Spokes route `0.0.0.0/0` to TGW -> egress VPC with NAT Gateways + IGW |
| **Centralized inspection** | Traffic routed to a VPC with **Network Firewall** or **Gateway Load Balancer** appliances (appliance mode on) |
| **Shared services** | Common VPC (DNS, AD, tooling) reachable from all spokes |
| **Hybrid hub** | One **transit VIF** (via DX gateway) or one VPN to the TGW reaches all VPCs |
| **Multi-Region** | TGW in each Region, connected with TGW peering |

## TGW vs the alternatives

| | **TGW** | **VPC Peering** | **PrivateLink** | **VPC Lattice** |
|---|---|---|---|---|
| Model | Hub-and-spoke router | 1:1 link | One service, one-way | L7 service network |
| Transitive | **Yes** | No | n/a | n/a |
| Overlapping CIDRs | No | No | Yes | Yes |
| On-prem reach | **Yes** (VPN/DX) | No (no edge-to-edge) | Via DX/VPN | No |
| Cost | Attachment + GB | Free (data transfer only) | Hourly + GB | Service + GB + requests |
| Best for | **Many VPCs + on-prem** | **2-3 VPCs**, cheapest | Expose a service | Microservices |

## Exam tips

- **"Many VPCs (tens to thousands) + on-prem, simplify the network, transitive routing"** -> **Transit Gateway**.
- **Two or three VPCs, lowest cost** -> VPC peering, not TGW.
- **Scale VPN throughput beyond 1.25 Gbps** -> TGW + **ECMP** over multiple VPN tunnels.
- **One Direct Connect link to many VPCs** -> **transit VIF + DX gateway + TGW** (private VIF + DX gateway alone doesn't route between VPCs).
- **Multicast** -> Transit Gateway.
- **Isolate prod from dev while sharing a hub** -> separate **TGW route tables** (association/propagation).
- **Inspect all traffic centrally** -> TGW + inspection VPC (Network Firewall / GWLB) with **appliance mode**.
- **Connect VPCs in different Regions** -> **TGW peering** (or inter-Region VPC peering).
- **Overlapping CIDRs** -> TGW will not work for those VPCs; use **PrivateLink** or **VPC Lattice**.
- **Cross-account sharing** -> **RAM**.
- A TGW attachment needs a **subnet in each AZ** used; traffic only reaches AZs that have one.

## Sample questions

1. *A company has 40 VPCs in several accounts and an on-prem data center via VPN. They want
   a simple, scalable network without peering meshes.* -> **Transit Gateway**, shared with
   RAM, VPN attached.
2. *VPN throughput of a single tunnel (1.25 Gbps) is insufficient.* -> **TGW with ECMP**
   across multiple Site-to-Site VPN connections.
3. *Dev VPCs must reach shared services but never the prod VPCs.* -> Separate TGW route
   tables with selective propagation.
4. *Two VPCs need private connectivity at the lowest possible cost.* -> **VPC peering**.
5. *All outbound traffic from 20 VPCs must go through one set of NAT Gateways.* ->
   **Centralized egress** VPC reached through the TGW.

## References

- Transit Gateway docs: https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html
- Pricing: https://aws.amazon.com/transit-gateway/pricing/
- Whitepaper — Building a Scalable and Secure Multi-VPC AWS Network Infrastructure: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html
- Related notes: [VPC overview](../README.md), [Direct Connect](../direct-connect/README.md), [VPC Sharing with AWS RAM](../vpc-sharing/README.md), [VPC Lattice](../vpc-lattice/README.md), [VPC Endpoints / PrivateLink](../vpc-endpoints/README.md), [Route Tables](../route-tables/README.md)
