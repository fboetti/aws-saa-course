# Gateways in AWS VPC — Overview

A **gateway** is the VPC's door to something **outside the subnet or outside the VPC**.
Subnets by themselves only talk to each other through the `local` route; to reach the
internet, another VPC, on-premises or an AWS service privately, traffic needs a gateway,
and a **[route table](../route-tables/README.md) entry** pointing to it.

```
                        ┌────────────── VPC ──────────────┐
 Internet ◄──── IGW ◄───┤ public subnet                   │
                        │   NAT GW ◄── private subnet     │
 On-prem  ◄── VGW/TGW ◄─┤                                 │
 Other VPC ◄─ PCX/TGW ◄─┤   gateway endpoint ◄── S3/DDB    │
                        └─────────────────────────────────┘
```

**Purpose:** connect, translate addresses (NAT), and control the path of traffic leaving or
entering the VPC. A gateway moves traffic; it does not filter it (SGs/NACLs do).

## Main Types

### Internet access

| Gateway | Purpose | Key points |
|---|---|---|
| **Internet Gateway (IGW)** | Two-way internet access for resources with a public IP | One per VPC; free; horizontally scaled and highly available; does the public ↔ private IP mapping. Route `0.0.0.0/0 → igw` makes a subnet public |
| **NAT Gateway** | **Outbound-only** IPv4 internet for private subnets | Lives in a **public subnet** with an Elastic IP; managed, scales up to 100 Gbps; zonal, so deploy **one per AZ**; billed per hour + per GB. A *private* NAT GW translates between overlapping private networks |
| **Egress-only IGW** | **Outbound-only IPv6** | Stateful, free; the IPv6 counterpart to a NAT gateway (IPv6 has no NAT) |
| *NAT instance* | Legacy self-managed EC2 NAT | Disable source/dest check; cheap but a single point of failure |

### Private connectivity to AWS services

| Gateway | Purpose | Key points |
|---|---|---|
| **Gateway VPC endpoint** | Private access to **S3** and **DynamoDB** | Route table entry via a prefix list; **free**; no ENI; Regional |
| **Interface endpoint (PrivateLink)** | Private access to most other AWS services and partner/own services | ENI with a private IP in your subnet; paid per hour + GB; no route entry, resolved through DNS |
| **Gateway Load Balancer endpoint** | Send traffic through third-party appliances (firewall, IDS) | Used in route tables to steer traffic via GWLB |

### Hybrid and multi-VPC connectivity

| Gateway | Purpose | Key points |
|---|---|---|
| **Virtual Private Gateway (VGW)** | VPN / Direct Connect endpoint on the **AWS side of one VPC** | One per VPC; pairs with a **Customer Gateway** (the on-premises device); supports route propagation |
| **Customer Gateway (CGW)** | AWS object describing **your** on-premises VPN device | Public IP + BGP ASN; lives on your side |
| **Transit Gateway (TGW)** | **Regional hub** for many VPCs, VPNs and Direct Connect | Transitive routing; own route tables for segmentation; paid per attachment + GB; can peer across Regions |
| **Direct Connect Gateway** | Reach VPCs in **many Regions/accounts** from one Direct Connect link | Global; connects private/transit VIFs to VGWs or TGWs |
| **VPC peering connection** (`pcx-`) | Direct private link between two VPCs | Not a physical gateway, but a route target; **not transitive**; no overlapping CIDRs |
| **Client VPN endpoint** | Managed OpenVPN access for remote users | Associates with subnets; not the same as Site-to-Site VPN |

### Other gateway names you may meet

| Name | What it is |
|---|---|
| **API Gateway** | Managed API front door (REST/HTTP/WebSocket) — an app-layer service, **not** a VPC gateway |
| **Storage Gateway** | Hybrid storage appliance (file, volume, tape) exposing S3/EBS to on-premises — not a network gateway |
| **Carrier / Local gateways** | Wavelength and Outposts connectivity to carrier networks / local network |

## Which Gateway? (quick map)

| Need | Gateway |
|---|---|
| Public subnet reachable from the internet | **Internet Gateway** |
| Private instances need to download updates, no inbound | **NAT Gateway** |
| IPv6 instances: outbound only | **Egress-only IGW** |
| Private, free access to S3 / DynamoDB | **Gateway endpoint** |
| Private access to other AWS services or SaaS | **Interface endpoint (PrivateLink)** |
| Encrypted IPsec tunnel from the office to one VPC | **VGW + Customer Gateway** |
| Many VPCs + on-premises, transitive | **Transit Gateway** |
| Dedicated private line, many Regions | **Direct Connect + DX Gateway** |
| Two VPCs, simple, non-transitive | **VPC peering** |
| Force traffic through a third-party firewall | **GWLB endpoint** |

## Exam Reminders

- Every gateway except interface endpoints and `local` needs a **route table entry**.
- IGW and egress-only IGW: **free**. NAT, TGW, interface endpoints, Direct Connect: **paid**.
- **NAT Gateway goes in a public subnet** and is zonal; **IGW** is attached to the VPC.
- **VPC peering is not transitive**; **Transit Gateway** is.
- **Gateway endpoints are only for S3 and DynamoDB**; everything else uses interface endpoints.
- A VPC has at most **one IGW** and **one VGW**.

## References

- AWS docs — Connect your VPC to other networks: https://docs.aws.amazon.com/vpc/latest/userguide/extend-intro.html
- AWS docs — Internet gateways: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
- AWS docs — NAT gateways: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
- Related notes: [VPC overview](../README.md), [Route Tables](../route-tables/README.md), [VPC Networking fundamentals](../networking/README.md), [Security Groups](../security-groups/README.md), [Network ACLs](../nacl/README.md)
