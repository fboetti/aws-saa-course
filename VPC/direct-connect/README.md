# AWS Direct Connect (DX) — Exam Notes

**AWS Direct Connect** is a **dedicated, private network link** between your data centre
(or office) and AWS. Traffic travels over a physical fibre connection instead of the public
internet, so you get **consistent latency, high bandwidth** and, for large volumes,
**lower data-transfer-out costs** than internet or VPN.

```
 On-premises            Direct Connect location (colo)               AWS Region
 ┌─────────────┐       ┌───────────────────────────────┐        ┌──────────────────┐
 │ Customer    │─fibre─│ Customer/partner  │  AWS DX   │─AWS────│ VPC (private VIF)│
 │ router      │       │ router (cage)     │  router   │ backbone│ S3 (public VIF)  │
 └─────────────┘       └───────────────────────────────┘        │ TGW (transit VIF)│
                                                                 └──────────────────┘
```

## Purpose

- **Consistent, predictable** network performance for hybrid workloads.
- **High throughput** (1–400 Gbps) for data migration, backups and analytics.
- **Lower egress cost** than data transfer out over the internet.
- **Private connectivity** to VPCs and to public AWS services without internet exposure.
- Meets compliance needs that forbid public-internet transport (but see encryption below).

## Core Components

| Component | What it is |
|---|---|
| **DX location** | A colocation facility where AWS has routers; you or a partner reach it |
| **Connection** | The physical port/link at a DX location |
| **Dedicated connection** | Your own port: **1, 10, 100 or 400 Gbps**, ordered from AWS |
| **Hosted connection** | Capacity sold by an **AWS Direct Connect Partner**: from **50 Mbps** up to **25 Gbps**, faster to get |
| **LAG** | Link Aggregation Group: bundle up to **4** same-speed connections into one logical link |
| **Virtual interface (VIF)** | A VLAN + BGP session over the connection that reaches a specific destination |
| **Direct Connect gateway** | **Global** object that connects a DX connection to VPCs/TGWs in **multiple Regions and accounts** |

## Virtual Interfaces (VIFs)

| VIF | Reaches | Via | Notes |
|---|---|---|---|
| **Private VIF** | **VPC** private IPs | VGW (one VPC) or **DX gateway** (many VPCs) | Most common |
| **Public VIF** | AWS **public** endpoints (S3, DynamoDB, public IPs) — **not** the internet | AWS public prefixes via BGP | Needs public IP addresses (your own or AWS-provided) |
| **Transit VIF** | **Transit Gateway** | DX gateway + TGW | The way to reach many VPCs from one VIF |

- A **VIF is a VLAN** on the connection (802.1Q) with a **BGP** session; BGP is mandatory.
- You can have **many VIFs** on one connection (different destinations or accounts).
- A VIF can be **hosted** in another AWS account — it reaches that account's resources.

## Connectivity Paths

```
 Private VIF ──> VGW ─────────────> ONE VPC (same Region)
 Private VIF ──> DX gateway ──────> VGWs of MANY VPCs (any Region, any account)
 Transit VIF ──> DX gateway ──────> TGW ──> MANY VPCs (+ inter-VPC routing)
 Public VIF ──────────────────────> S3, DynamoDB, other AWS public endpoints
```

- A **DX gateway** is global, but it **does not route between VPCs** it connects to (it is
  not a hub); for VPC-to-VPC use **Transit Gateway** or peering.
- On-premises site to on-premises site **through AWS** is not what a normal VIF does;
  the feature for that is **SiteLink** (private VIFs/transit VIFs, DX location to DX location).

## Security: Not Encrypted by Default

DX is **private**, not **encrypted**. For encryption:

| Option | Layer | Notes |
|---|---|---|
| **MACsec** | L2 (point-to-point) | On 10/100/400 Gbps **dedicated** connections |
| **Site-to-Site VPN over DX** | L3 (IPsec) | VPN terminated through a **public VIF** or a **transit VIF** (accelerated/private IP VPN) |
| Application-level TLS | L4+ | Always possible |

## Resilience

| Level | Design |
|---|---|
| Development / non-critical | **One** connection — single point of failure |
| **High resiliency** | **Two** connections at **two different DX locations** |
| **Maximum resiliency** | **Four** connections: **two at each of two locations** (separate devices) |
| Cheap backup | **Site-to-Site VPN** as failover to DX |

- A single DX connection (or a single location) is **never** highly available.
- Failover between DX and VPN is controlled by **BGP**: DX routes are preferred over VPN
  for the same prefix.
- **BFD** (Bidirectional Forwarding Detection) speeds up failure detection.

## Lead Time and Cost

- **Provisioning takes weeks to months** (cross-connect, circuit, LOA-CFA letter). Hosted
  connections are faster. Plan a **VPN as an interim link**.
- **Cost = port-hours + data transfer out** (DTO over DX is cheaper than over the
  internet). **Data transfer in is free.**
- No encryption, no managed SLA for the customer-side circuit: the cross-connect and the
  last mile from your site to the DX location are **your** responsibility.

## Direct Connect vs Site-to-Site VPN

| | **Direct Connect** | **Site-to-Site VPN** |
|---|---|---|
| Path | Dedicated private fibre | **Internet** (IPsec tunnels) |
| Encryption | **No** by default (MACsec/VPN add it) | **Yes** (IPsec) |
| Bandwidth | 50 Mbps – 400 Gbps | ~**1.25 Gbps per tunnel** |
| Latency | Consistent, low | Variable (internet) |
| Setup time | **Weeks – months** | **Minutes** |
| Cost | Port fees + DTO | Per connection-hour + DTO |
| Best as | Primary hybrid link | Quick start, backup, encrypted overlay |

## Exam Facts (SAA-C03)

- DX = **dedicated private link**, **not over the internet**, **not encrypted by default**.
- **Lower and predictable latency**, higher bandwidth, **lower DTO** cost than the internet.
- Takes **weeks to months** to provision → **VPN as a stopgap/backup**.
- **Dedicated**: 1/10/100/400 Gbps. **Hosted**: 50 Mbps–25 Gbps via partner.
- **VIF types**: private (VPC), public (AWS public services), transit (Transit Gateway).
- **DX gateway** = access **many VPCs across Regions/accounts** from one connection.
- **Resilient**: two locations, two connections each for maximum; VPN as cheap backup.
- **Encrypt** with **MACsec** or **IPsec VPN over DX**.
- **BGP** is required; DX routes beat VPN routes when prefixes are equal.
- **Data transfer in is free**; DTO is billed at a reduced rate.
- A DX connection is tied to **one DX location**; the location maps to a **Region**, but the
  DX gateway lets you reach other Regions.
- **Link Aggregation Group (LAG)** = more bandwidth/redundancy at a single location.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| Consistent latency for a hybrid app, regulatory ban on internet transit | **Direct Connect** |
| Need connectivity next week, can't wait for DX | **Site-to-Site VPN** |
| DX as primary, cheap backup if it fails | **Site-to-Site VPN** failover |
| One DX link must reach VPCs in several Regions | **Direct Connect gateway** |
| One DX link must reach dozens of VPCs with routing between them | **Transit VIF + Transit Gateway** |
| Private link must also be encrypted | **MACsec** or **VPN over DX** |
| Access S3 from on-premises privately over DX | **Public VIF** (or interface endpoint via private VIF) |
| Highest resiliency | **Two DX locations, two connections each** |
| Move many TB of data to AWS | **DX** (steady) or **Snow family** (one-off, offline) |
| Need bandwidth below 1 Gbps | **Hosted connection** (50 Mbps and up) |
| Reduce egress cost for steady bulk traffic | **Direct Connect** |
| Individual remote users need access | **Client VPN**, not DX |

## Exam Traps

- **"Private" ≠ "encrypted".** DX needs MACsec or an IPsec VPN for encryption.
- **A single DX connection is a single point of failure**, even if AWS runs the far end.
- **DX is not instant.** Questions with an urgent deadline point to VPN.
- **Public VIF doesn't give internet access** — only AWS public service endpoints.
- **DX gateway ≠ transit router.** It doesn't route between the VPCs attached to it.
- **Data transfer IN is free**; the savings are on data **out**.
- **A VPN backup uses the internet** and has lower bandwidth; expect reduced throughput on
  failover.
- **Wrong tool for users.** Laptops/remote workers → Client VPN; sites → DX or VPN.
- **Overlapping CIDRs** between on-premises and VPCs break routing; plan addressing first.
- **DX gateway and TGW are different layers**: DX gateway links VIFs to VGW/TGW, the TGW
  routes among VPCs.

## Commands

```bash
# List DX locations and connections
aws directconnect describe-locations
aws directconnect describe-connections

# Order a dedicated connection (needs LOA-CFA, then a cross-connect at the colo)
aws directconnect create-connection --location EqDC2 \
  --bandwidth 1Gbps --connection-name office-dx

# Create a DX gateway and associate it with a VGW or TGW
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name dxgw-main --amazon-side-asn 64512
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id dxgw-0abc1234 --gateway-id vgw-0abc1234

# Create a private virtual interface
aws directconnect create-private-virtual-interface --connection-id dxcon-0abc1234 \
  --new-private-virtual-interface \
  virtualInterfaceName=private-vif,vlan=101,asn=65000,directConnectGatewayId=dxgw-0abc1234

# Check VIF and BGP status
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[].[virtualInterfaceName,virtualInterfaceType,virtualInterfaceState,bgpPeers[0].bgpStatus]' \
  --output table
```

## Study Checklist

- [ ] Explain why DX gives consistent latency and lower DTO costs than the internet.
- [ ] Name the three VIF types and what each reaches.
- [ ] Describe the role of the DX gateway and what it does **not** do.
- [ ] Design a maximum-resiliency DX setup and a DX + VPN backup.
- [ ] Say how to encrypt DX traffic (MACsec, VPN over DX).
- [ ] Choose between DX, Site-to-Site VPN, Client VPN and Snow family.
- [ ] Recall the speeds: dedicated 1/10/100/400 Gbps, hosted 50 Mbps–25 Gbps.

## References

- AWS docs — What is Direct Connect: https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html
- AWS docs — Direct Connect resiliency recommendations: https://aws.amazon.com/directconnect/resiliency-recommendation/
- AWS docs — Direct Connect gateways: https://docs.aws.amazon.com/directconnect/latest/UserGuide/direct-connect-gateways.html
- Related notes: [VPC overview](../README.md#aws-direct-connect-dx), [Gateways](../gateways/README.md), [Route Tables](../route-tables/README.md), [VPC Networking fundamentals](../networking/README.md)
