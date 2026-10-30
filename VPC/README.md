# Amazon VPC — Theoretical Overview

Notes on **Amazon Virtual Private Cloud (VPC)**, the networking layer everything else in AWS runs on. Follows the VPC section of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=63222s) (section starts around **12:19:52**, right after the AWS API chapter), refined for the **SAA-C03** exam.

| Note | Read it for |
|---|---|
| **This page** | The whole VPC map: addressing, internet access, security layers, hybrid/multi-VPC connectivity, exam facts |
| [VPC Networking](networking/README.md) | Fundamentals first: CIDR maths, subnets, route tables, the IGW and how a packet actually flows |
| [Default VPC](default-vpc/README.md) | The VPC AWS builds for you: its CIDR, what gets created, why it exists, how to recreate it |
| [Network ACLs](nacl/README.md) | The stateless subnet firewall: rule ordering, ephemeral ports, default vs custom, SG vs NACL, exam traps |
| [VPC Sharing with AWS RAM](vpc-sharing/README.md) | Letting other accounts launch into your subnets — who owns, controls and pays for what |

## What is a VPC?

A **VPC** is a **logically isolated virtual network** inside **one AWS region**. You choose its IP range (CIDR block), carve it into **subnets** (one AZ each), decide where traffic goes with **route tables** and **gateways**, and filter it with **security groups** and **network ACLs**.

It is your traditional data-centre network rebuilt in software — the pieces map almost one to one:

| On-premises | In a VPC |
|---|---|
| Private address plan | VPC **CIDR block** (e.g. `10.0.0.0/16`) |
| VLAN / network segment | **Subnet** (pinned to one AZ) |
| Router + routing table | Implicit **VPC router** + **route tables** |
| Edge router to the ISP | **Internet Gateway** |
| NAT box / proxy for outbound traffic | **NAT Gateway** |
| Host firewall | **Security group** (stateful, per ENI) |
| Perimeter ACL on a switch/router | **Network ACL** (stateless, per subnet) |
| Network card | **ENI** (Elastic Network Interface) |
| Leased line / IPsec VPN to a branch | **Direct Connect** / **Site-to-Site VPN** |

```
AWS account / region
└── VPC 10.0.0.0/16                          logically isolated network
     ├── Availability Zone A
     │    ├── public subnet  10.0.1.0/24      route 0.0.0.0/0 -> igw
     │    └── private subnet 10.0.11.0/24     route 0.0.0.0/0 -> nat-gw-a
     ├── Availability Zone B
     │    ├── public subnet  10.0.2.0/24      route 0.0.0.0/0 -> igw
     │    └── private subnet 10.0.12.0/24     route 0.0.0.0/0 -> nat-gw-b
     └── AZ C ...
```

The three scopes to keep straight — most "can I do X?" exam questions reduce to them:

| Object | Scope |
|---|---|
| VPC, Internet Gateway, route table, security group, NACL, gateway endpoint, Transit Gateway | **Region** |
| Subnet, ENI, NAT Gateway, interface endpoint ENI, EC2 instance, EBS volume | **One AZ** |
| Elastic IP | **Region** (attaches to any ENI in that region) |

## Key Features and Quotas

- **Region specific** — a VPC never spans regions. Cross-region connectivity is **VPC peering** (inter-region supported), **Transit Gateway peering**, or VPN/Direct Connect.
- **Default VPC in every region** — pre-built and ready to use (`172.31.0.0/16`, one public `/20` per AZ). Custom VPCs start empty. See [Default VPC](default-vpc/README.md).
- **Subnets are AZ-scoped** — high availability means **one subnet per tier per AZ**.
- **DNS attributes** — `enableDnsSupport` (the Amazon DNS resolver answers queries) and `enableDnsHostnames` (instances get DNS names such as `ip-10-0-1-5.eu-north-1.compute.internal` / public DNS names). Both are **on in the default VPC**; in a custom VPC only `enableDnsSupport` is on by default — **`enableDnsHostnames` is off**. Private hosted zones in Route 53 and interface-endpoint private DNS need **both** on.

| Quota | Default | Adjustable |
|---|---|---|
| VPCs per region | **5** | Yes |
| Subnets per VPC | **200** | Yes |
| IPv4 CIDR blocks per VPC (primary + secondary) | **5** | Yes, up to 50 |
| IPv6 CIDR blocks per VPC | **5** | Yes, up to 50 |
| IPv4 CIDR size (VPC and subnet) | **/16 – /28** | No |
| Internet gateways per VPC | **1** | No |
| Elastic IPs per region | **5** | Yes |
| Security groups per ENI | **5** | Yes, up to 16 |
| Inbound / outbound rules per security group | **60 / 60** | Yes |
| Rules per NACL (each direction) | **20** | Yes, up to 40 |
| Active peering connections per VPC | **50** | Yes, up to 125 |

### What VPC costs

| Free | Paid |
|---|---|
| VPC, subnets, route tables, NACLs, security groups | **NAT Gateway** — per hour **+ per GB processed** |
| Internet Gateway, egress-only IGW | **Interface endpoints** — per hour per AZ + per GB |
| **Gateway endpoints** (S3, DynamoDB) | **Transit Gateway** — per attachment-hour + per GB |
| VPC peering connection (no hourly fee) | **Site-to-Site VPN** (~0.05 USD/hour per connection), **Client VPN** |
| Virtual private gateway object | **Direct Connect** — port-hours + data transfer out |
| AWS RAM resource shares | **Public IPv4 addresses** (incl. Elastic IPs), ~0.005 USD/hour each, attached or not |
| Same-AZ traffic over private IPs | **Data transfer**: inter-AZ (each direction), inter-region, internet egress, cross-region peering |

Cost levers the exam loves: **gateway endpoint instead of NAT for S3/DynamoDB traffic**, **keep chatty traffic in one AZ**, **peering instead of TGW for a handful of VPCs**, **release unused public IPv4/EIPs**.

## IP Addressing

Address planning is the first design decision and the hardest to undo.

- **Use RFC 1918 private ranges**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` (`100.64.0.0/10` is also accepted). AWS lets you use publicly routable ranges, but traffic to the *real* owners of those addresses would then never leave your VPC.
- **CIDR size**: VPC and subnets between **/16** (65,536 addresses) and **/28** (16 addresses).
- **5 reserved addresses per subnet** — in `10.0.1.0/24`: `.0` network, `.1` VPC router, `.2` Amazon DNS, `.3` reserved for future use, `.255` broadcast (VPCs do not support broadcast, AWS reserves it anyway). So a `/24` has **251** usable, a `/28` only **11**.
- **Never overlap** with on-premises networks, other VPCs or anything you may later peer/VPN with. Overlap cannot be fixed by routing — you re-IP, use **PrivateLink**, or a **private NAT Gateway**. **VPC IPAM** helps plan and allocate across accounts.
- **Growing**: subnets **cannot be resized**; a VPC can get **secondary CIDR blocks** (up to 5 total, adjustable to 50) and you create new subnets in them. The primary CIDR cannot be changed.
- **IPv6**: a VPC gets a **/56** (Amazon-provided, or your own via BYOIP/IPAM), each subnet a **/64**. IPv6 addresses are **globally unique and public** — "private" for IPv6 means *no inbound route*, which is what an **egress-only Internet Gateway** gives you. IPv4 cannot be disabled on a VPC (it always has an IPv4 CIDR), but you can create **IPv6-only subnets**.

| Address type | Survives stop/start? | Notes |
|---|---|---|
| **Private IPv4** | Yes (kept until the ENI is deleted) | Primary private IP of an instance never changes |
| **Auto-assigned public IPv4** | **No** — a new one after stop/start | From the subnet setting `MapPublicIpOnLaunch` or the launch option; cannot be moved |
| **Elastic IP** | Yes | Static, regional, remappable to another instance/ENI; billed like any public IPv4 |
| **IPv6** | Yes | Public, globally unique |

## Subnets and Route Tables

Full walkthrough with packet flow: [VPC Networking](networking/README.md). The essentials:

- You launch into a **subnet**, not a VPC. A subnet is a slice of the VPC CIDR in **exactly one AZ**.
- **"Public" or "private" is not a setting** — it is a consequence of the subnet's **route table**:
  - **public subnet** → route `0.0.0.0/0 → igw-…` (and instances need a public IPv4/EIP),
  - **private subnet** → no IGW route; typically `0.0.0.0/0 → nat-…` for outbound only,
  - **isolated subnet** → no default route at all (databases, internal-only workloads; reach AWS services through endpoints).
- Every subnet is associated with **exactly one route table**; a route table can serve many subnets. Subnets without an explicit association use the **main route table** — keep the main table private and give public subnets an explicit custom table, so a newly created subnet is never public by accident.
- The **local route** (VPC CIDR → `local`) is always there and **cannot be deleted**: every subnet can route to every other subnet in the VPC (SGs/NACLs still filter).
- **Longest prefix match wins**: `10.0.1.0/24` beats `10.0.0.0/16` beats `0.0.0.0/0`.
- Route targets: `igw-` internet, `nat-` NAT Gateway, `eni-` appliance/NAT instance, `pcx-` peering, `tgw-` Transit Gateway, `vgw-` VPN gateway, `vpce-` gateway endpoint (via a **prefix list** `pl-…`), `eigw-` egress-only IGW.

### Multi-tier reference design

```
                     Internet
                        |
                      [IGW]
                        |
  public subnets   ALB, NAT GW (one per AZ), bastion       0.0.0.0/0 -> igw
                        |
  private subnets  EC2 / ECS / Lambda (app tier)           0.0.0.0/0 -> nat (same AZ)
                        |
  isolated subnets RDS / ElastiCache (data tier)           local only (+ endpoints)
```

Repeat each tier in **at least two AZs**. Security groups chain the tiers: ALB SG ← internet on 443, app SG ← **ALB SG**, DB SG ← **app SG**.

## Internet Access

### Internet Gateway (IGW)

- **One per VPC**, created and then **attached** (two steps). Horizontally scaled, redundant, **no bandwidth limit, free**.
- Does **1:1 NAT** between an instance's private IPv4 and its public IPv4/EIP; for IPv6 it just routes (addresses are already public).
- Is **not a firewall** — SGs and NACLs still decide.
- A subnet reaches the internet only when **all three** hold: IGW attached + `0.0.0.0/0 → igw` route + public IPv4/EIP on the instance.

### NAT Gateway vs NAT Instance

Private instances still need *outbound* internet (patches, package repos, external APIs) while staying unreachable from outside. NAT does **source NAT** — many private IPs behind one public IP — and only allows return traffic of connections started from inside.

| | **NAT Gateway** | **NAT Instance** (legacy) |
|---|---|---|
| Managed by | AWS | You (EC2 + AMI + patching) |
| Placement | **Public subnet**, with an **Elastic IP** | Public subnet, with public IP/EIP |
| Availability | Redundant **inside one AZ** → deploy **one per AZ** | Single instance; HA is DIY (scripts, ASG) |
| Bandwidth | Scales automatically, **5 → 100 Gbps** | Limited by instance type |
| Security groups | **Cannot** be attached (NACLs still apply) | Yes |
| Extra config | None | **Disable source/destination check** |
| Port forwarding / bastion | No | Possible |
| Cost | Per hour + **per GB processed** | EC2 instance cost; cheaper at very low volume |

Rule of thumb: **"managed, highly available, scales" → NAT Gateway**; **"cheapest, low traffic, single point of failure acceptable" → NAT instance**.

- Each private subnet should route to the **NAT Gateway in its own AZ**: if the AZ hosting a single NAT fails, every other AZ loses internet, and cross-AZ NAT traffic also costs inter-AZ data transfer.
- A **private NAT Gateway** (no EIP, cannot reach the internet) translates traffic between networks with **overlapping CIDRs** — e.g. VPC ↔ on-premises via TGW.
- NAT Gateways handle **IPv4 only**. For IPv6 outbound-only use an **egress-only Internet Gateway** (stateful, free).
- Newer option: a **regional NAT Gateway** mode that spans AZs automatically. The classic exam model is still the zonal "one per AZ" design.

### Reaching instances without exposing them

| Option | How it works | Exam signal |
|---|---|---|
| **Bastion host** | Hardened EC2 in a public subnet; SSH/RDP to it, then hop to private instances | "jump box", allow SSH **only from the corporate IP** in the bastion SG |
| **SSM Session Manager** | Agent on the instance calls out to Systems Manager; no inbound ports, no keys, sessions logged | "no open ports / no bastion / audit sessions" |
| **EC2 Instance Connect Endpoint** | Endpoint in the VPC tunnels SSH/RDP to private instances | "SSH to private instance without public IP or bastion" |

## Security: Security Groups and NACLs

Two independent layers. Traffic must pass **both**.

### Security Groups (SG)

- **Stateful**: return traffic of an allowed flow is allowed automatically, in either direction.
- **Allow rules only** — no deny. Whatever is not allowed is dropped.
- Attached to **ENIs** (so to instances, RDS, Lambda in VPC, ALBs, interface endpoints…); up to 5 SGs per ENI, rules are the **union** of all of them.
- **All rules are evaluated** together — no ordering.
- A **new SG**: no inbound rules (deny all inbound), allow all outbound. The **default SG** of each VPC additionally allows inbound **from members of the same SG**.
- Sources can be CIDRs, **prefix lists**, or **other security groups** — referencing an SG ("allow 3306 from `sg-app`") is the clean way to chain tiers and survives IP changes. Works across peered VPCs in the same region.
- Changes apply **immediately**. SGs are **VPC-scoped** (can't be used in another VPC, except through [VPC sharing](vpc-sharing/README.md)).

### Network ACLs (NACL)

- **Stateless**: each direction is checked separately, so return traffic must be allowed explicitly — typically **ephemeral ports 1024–65535** (Linux uses 32768–60999, Windows 49152–65535; the exam answer is 1024–65535).
- Applied at the **subnet** boundary — affects every resource in it. Each subnet has **exactly one** NACL; one NACL can cover many subnets.
- **Allow and deny** rules, numbered **1–32766**, evaluated **lowest number first, first match wins**; the final `*` rule denies everything else. Leave gaps (100, 200…) to insert rules later.
- **Default NACL** allows all in and out. A **custom NACL** denies all until you add rules.
- Traffic between instances in the **same subnet** does not cross the NACL.
- The tool for **blocking a specific IP or range** — security groups cannot deny.

### Security Group vs NACL

| | **Security Group** | **NACL** |
|---|---|---|
| Level | ENI / instance | Subnet |
| State | **Stateful** | **Stateless** |
| Rules | Allow only | Allow **and** deny |
| Evaluation | All rules, union | Numbered order, first match |
| Return traffic | Automatic | Must be allowed (ephemeral ports) |
| Default (new) | Inbound none, outbound all | Default NACL: all allowed; custom NACL: all denied |
| Typical use | Tier-to-tier access, least privilege | Subnet guardrails, **blocking IPs** |

Evaluation order: **inbound** → NACL (subnet) → SG (ENI) → instance; **outbound** → SG → NACL.

### Beyond SG/NACL

- **AWS Network Firewall** — managed stateful firewall/IPS with domain filtering, deployed in its own subnets; you steer traffic to it through route tables. Answer for "inspect/filter all traffic leaving the VPC" or "block outbound access to specific domains".
- **Gateway Load Balancer (GWLB)** — inserts fleets of **third-party virtual appliances** (firewalls, IDS) transparently into the traffic path (GENEVE, port 6081), reached through **GWLB endpoints**.
- **AWS WAF** protects L7 (ALB, API Gateway, CloudFront) — it is not a VPC feature, but often appears as the alternative answer.

## ENI and Elastic IP

- **ENI** — virtual network card: primary private IPv4, optional secondary IPs, public IP/EIP, IPv6, MAC address, security groups, source/dest-check flag. **AZ-bound**. The primary ENI (`eth0`) cannot be detached; a **secondary ENI can be moved** to another instance in the same AZ — keeping its IPs and MAC — which is a classic low-cost failover/licensing pattern.
- **Elastic IP** — static public IPv4 owned by your account in one region. Remap it to a standby instance to fail over without DNS changes. Billed hourly like every public IPv4; default limit 5 per region. Prefer DNS/load balancers over EIPs when possible.

## Connecting VPCs and Networks

### VPC Peering

- **Private one-to-one link** between two VPCs — same or different **account** and **region**. Traffic stays on the AWS backbone, no single point of failure, no bandwidth bottleneck.
- **Not transitive**: A↔B and B↔C does **not** give A↔C. N VPCs fully meshed = N(N−1)/2 connections.
- **No edge-to-edge routing**: A cannot use B's IGW, NAT Gateway, VPN, Direct Connect or gateway endpoint.
- **CIDRs must not overlap.**
- One side requests, the other **accepts**; then add **routes in both route tables** (`pcx-…`) and open SGs/NACLs on both sides.
- No hourly fee; data transfer is billed (cross-AZ and cross-region rates). Best for **a few VPCs**.

### VPC Sharing (AWS RAM)

- Shares **subnets**, not the VPC, with accounts in the **same AWS Organization** and **same region**. Default VPC subnets cannot be shared.
- **Owner** keeps the network (routes, NACLs, IGW, NAT, TGW attachment, endpoints) and pays for it; **participants** launch and pay for their own resources and their own SGs/ENIs.
- It is not connectivity between VPCs — it puts multiple accounts **into one VPC**. Details: [VPC Sharing with AWS RAM](vpc-sharing/README.md).

### Transit Gateway (TGW)

- **Regional hub-and-spoke router** for thousands of VPCs, Site-to-Site VPNs and Direct Connect gateways — across accounts (shared via **RAM**).
- **Transitive routing**: every spoke reaches every other through the hub — this is what peering lacks.
- **TGW route tables** segment traffic (prod / dev / shared services) and centralize **egress** (one NAT VPC) or **inspection** (Network Firewall / GWLB VPC).
- **Inter-region TGW peering** connects hubs in different regions over the AWS backbone.
- Supports **ECMP over multiple VPN tunnels** to scale VPN bandwidth, and **IP multicast** (the only native multicast option).
- Paid per attachment-hour and per GB — more expensive than peering for two or three VPCs.

### VPC Endpoints and PrivateLink

Endpoints let VPC resources reach AWS services **privately**, without IGW, NAT or public IPs.

| | **Gateway endpoint** | **Interface endpoint** (PrivateLink) |
|---|---|---|
| Services | **S3 and DynamoDB** only | 100+ AWS services (S3 and DynamoDB included), your own and SaaS services |
| Mechanism | **Route table** entry: service **prefix list** → `vpce-…` | **ENI** with a private IP in each chosen subnet/AZ |
| Security | **Endpoint policy** (+ bucket policy `aws:sourceVpce`) | Endpoint policy **+ security group** on the ENI |
| DNS | Service's normal public name; routing does the magic | **Private DNS**: the service's name resolves to the ENI IPs |
| Reachable from on-premises / peered VPC / other region | **No** — only from inside its own VPC | **Yes** — over DX/VPN, peering, TGW |
| Cost | **Free** | Per hour per AZ + per GB |

- **Private S3/DynamoDB access from inside the VPC, cheapest** → **gateway endpoint** (also removes NAT data-processing charges).
- **S3 access from on-premises over Direct Connect/VPN** → **S3 interface endpoint**.
- **PrivateLink for your own services**: the provider puts a **Network Load Balancer** (or GWLB) in front of the service and creates an **endpoint service**; consumers create interface endpoints in their VPCs. One-directional (consumer → provider), **works with overlapping CIDRs**, no peering, no route changes — the answer for "expose one service to hundreds of VPCs/customers".
- **Gateway Load Balancer endpoint** is the third endpoint type, used to send traffic to inspection appliances.

### Site-to-Site VPN

- **IPsec tunnels over the internet** between a **Customer Gateway** (your device/software, described to AWS by its public IP) and a **Virtual Private Gateway** (one per VPC) or a **Transit Gateway**.
- Every connection has **two tunnels** terminating in different AZs — configure both for HA.
- Routing: **static** or **dynamic (BGP)**; enable **route propagation** in the subnet route tables to learn on-prem routes.
- About **1.25 Gbps per tunnel**; scale with **ECMP on a Transit Gateway** across multiple tunnels/connections.
- **Accelerated VPN** (TGW only) enters the AWS network at the nearest edge via Global Accelerator.
- **VPN CloudHub**: several branch sites connect to one VGW and can reach each other (hub-and-spoke over VPN).
- Set up in minutes, encrypted, but latency/throughput depend on the internet.

**AWS Client VPN** is a different product: a managed **OpenVPN-based** endpoint for individual **users/laptops** to reach the VPC (and on-prem through it).

### AWS Direct Connect (DX)

- **Dedicated private connection** from your data centre to an AWS Direct Connect location, then to AWS — bypasses the internet: **consistent latency, high bandwidth**, lower data-transfer-out rates.
- **Dedicated connections**: 1, 10, 100 or 400 Gbps ports. **Hosted connections** (via partners): 50 Mbps up to 25 Gbps. **LAG** bundles several links.
- **Virtual interfaces (VIFs)**: **private VIF** → VPCs (via VGW or DX gateway), **public VIF** → public AWS endpoints (S3, DynamoDB…) over the private link, **transit VIF** → Transit Gateway via DX gateway.
- **Direct Connect gateway**: one DX connection reaches VPCs in **many regions/accounts** (global object).
- **Not encrypted by default** — use **MACsec** (L2, on 10/100/400 Gbps dedicated ports) or a **Site-to-Site VPN over a public VIF / transit VIF**.
- Provisioning takes **weeks to months** — use a VPN meanwhile and keep it as **backup**.
- Resilience: **high** = two connections at **two DX locations**; **maximum** = two connections at each of two locations. A single DX connection is a single point of failure.

### Choosing the connectivity option

| Need | Choose |
|---|---|
| 2–3 VPCs, simple, cheapest | **VPC peering** |
| Many VPCs / accounts / on-prem, transitive, segmentation | **Transit Gateway** |
| Several accounts in **one** network managed centrally | **VPC sharing (RAM)** |
| Expose a single service privately, overlapping CIDRs OK | **PrivateLink** (NLB + endpoint service) |
| Private access to S3/DynamoDB from the VPC | **Gateway endpoint** |
| Private access to other AWS services, or S3 from on-prem | **Interface endpoint** |
| On-prem link fast to set up, encrypted, internet-based | **Site-to-Site VPN** |
| On-prem link with consistent latency / high bandwidth | **Direct Connect** (+ VPN backup) |
| Remote employees to the VPC | **Client VPN** |

## Monitoring and Troubleshooting

- **VPC Flow Logs** — metadata of IP traffic (source/destination IP and port, protocol, bytes, `ACCEPT`/`REJECT`) at **VPC, subnet or ENI** level, delivered to **CloudWatch Logs, S3 or Kinesis Data Firehose**. Not real-time (aggregation window up to ~10 minutes), **no packet contents**. Not captured: traffic to the Amazon DNS resolver, instance metadata (`169.254.169.254`), Amazon Time Sync, DHCP. Query them with **Athena** (S3) or CloudWatch Logs Insights.
  - Reading a rejection: inbound `ACCEPT` but the response `REJECT` → a **NACL** is blocking the return (SGs are stateful and would have allowed it).
- **Traffic Mirroring** — copies **actual packets** from an ENI to an inspection target (IDS, packet analysis).
- **Reachability Analyzer** — static analysis of whether a path between two resources *would* work and which component blocks it; **sends no packets**.
- **Network Access Analyzer** — finds unintended access paths (e.g. "is any database reachable from the internet?").
- **Route 53 Resolver endpoints** — **inbound** (on-prem resolves AWS private names) and **outbound** (VPC resolves on-prem names via forwarding rules) for hybrid DNS. **DHCP option sets** set custom DNS servers / domain names for a VPC.

## Topics Covered in the Course

| Topic | What to take away |
|---|---|
| **Key features / quotas** | Region specific, default VPC, 5 VPCs/region, 200 subnets/VPC, 5 IPv4/IPv6 CIDR blocks, DNS hostnames attribute, free vs paid. |
| **VPC fundamentals** | Region/AZ scope, CIDR planning, default vs custom VPC, default subnets. |
| **Subnets** | Public vs private by route, 5 reserved IPs, one AZ per subnet. |
| **Internet Gateway** | Create + attach, public IP requirement, `0.0.0.0/0` route. |
| **Route tables** | Main vs custom, subnet associations, local route, longest prefix match. |
| **Security groups** | Stateful, allow-only, SG references, default deny inbound. |
| **Network ACLs** | Stateless, ordered allow/deny, ephemeral ports. |
| **NAT** | NAT Gateway vs NAT instance, public subnet + EIP, one per AZ. |
| **VPC peering** | 1:1, not transitive, no edge-to-edge, no overlapping CIDRs, routes on both sides. |
| **VPC sharing (AWS RAM)** | Share subnets, not VPCs; same Organization and region; owner controls the network. |
| **VPC endpoints** | Gateway (S3/DynamoDB, free) vs interface (PrivateLink, paid, ENI + DNS). |
| **VPC Flow Logs** | What is captured, destinations, troubleshooting SG vs NACL. |
| **Site-to-Site VPN** | IPsec over the internet, CGW ↔ VGW/TGW, two tunnels. |
| **Direct Connect** | Dedicated links, VIFs, DX gateway, encryption caveat, VPN backup. |
| **Hands-on** | Build a VPC: subnets, IGW, route tables, SG/NACL, EC2, bastion, NAT. |

## Exam Info (SAA-C03)

### Exam Facts

| Item | Detail |
|---|---|
| Questions | **65** (multiple choice and multiple response); 15 are unscored |
| Time | **130 minutes** |
| Passing score | **720 / 1000** (scaled) |
| Cost | **150 USD** |
| Validity | 3 years |
| Delivery | Pearson VUE test centre or online proctored |

### Domain Weighting

| Domain | Weight |
|---|---|
| 1. Design **Secure** Architectures | **30%** |
| 2. Design **Resilient** Architectures | **26%** |
| 3. Design **High-Performing** Architectures | **24%** |
| 4. Design **Cost-Optimized** Architectures | **20%** |

VPC appears in **every domain**: security (SG/NACL, private subnets, endpoints, Network Firewall), resilience (multi-AZ subnets, NAT per AZ, DX + VPN), performance (DX, TGW, placement in one AZ) and cost (gateway endpoint vs NAT, peering vs TGW, public IPv4 charges, inter-AZ traffic).

### High-Yield Facts

- A subnet lives in **exactly one AZ**; multi-AZ means multiple subnets.
- **5 IPs reserved** per subnet: `.0` network, `.1` router, `.2` DNS, `.3` future, last = broadcast.
- VPC/subnet CIDR **/16 to /28**; use **RFC 1918** ranges; **no overlaps** if you will ever connect networks.
- Quotas: **5 VPCs/region, 200 subnets/VPC, 5 CIDR blocks/VPC, 1 IGW/VPC, 5 EIPs/region** (all adjustable except IGW and CIDR size).
- **Local route cannot be deleted**; **longest prefix match** wins.
- **Public subnet = route to IGW**, plus public IPv4/EIP on the instance.
- **Custom VPCs have `enableDnsHostnames` off**; the default VPC has DNS hostnames and support on.
- **SGs are stateful and allow-only; NACLs are stateless, ordered, allow + deny** — asked constantly.
- To **block an IP**, use a **NACL deny**.
- **NACL return traffic** needs **ephemeral ports 1024–65535**.
- **NAT Gateway**: public subnet + EIP, **one per AZ**, IPv4 only, no SGs. **NAT instance**: disable **source/destination check**.
- **Egress-only IGW** = outbound-only **IPv6**.
- **Peering**: not transitive, no edge-to-edge routing, no overlapping CIDRs, works cross-account and cross-region.
- **Transit Gateway**: transitive hub for VPCs + VPN + DX; route tables for segmentation; ECMP for VPN bandwidth; multicast.
- **Gateway endpoints** (S3/DynamoDB) are **free** and VPC-local; **interface endpoints** cost money but work from on-prem/peered VPCs.
- **PrivateLink** = NLB + endpoint service; one-way; tolerates overlapping CIDRs.
- **VPN**: two tunnels, ~1.25 Gbps per tunnel, encrypted, quick. **DX**: dedicated, not encrypted by default, weeks to provision.
- **VPC Flow Logs**: metadata only, not real-time, to CloudWatch Logs / S3 / Firehose.
- **Reachability Analyzer** sends no traffic.
- **Every public IPv4 address is billed**, including EIPs in use.

### Scenario → Answer

| Requirement | Answer |
|---|---|
| Private subnet instances need OS updates, no inbound internet | **NAT Gateway** in a public subnet (one per AZ for HA) |
| Private IPv6 instances need outbound-only internet | **Egress-only Internet Gateway** |
| Cheapest private access to S3 from a VPC; also cut NAT costs | **Gateway VPC endpoint** |
| Access S3 privately **from on-premises** over DX/VPN | **S3 interface endpoint** |
| Private access to a service that is not S3/DynamoDB (SQS, KMS, Secrets Manager…) | **Interface endpoint (PrivateLink)** |
| Restrict a bucket to traffic from one VPC endpoint | Bucket policy with **`aws:sourceVpce`** |
| Expose an internal service to many VPCs/customers, CIDRs overlap | **PrivateLink** (NLB + endpoint service) |
| Two VPCs in different regions need private connectivity | **Inter-region VPC peering** |
| Dozens of VPCs and on-premises networks, any-to-any routing | **Transit Gateway** |
| VPC A peered to B needs B's NAT Gateway / VPN | **Not possible** (no edge-to-edge) — use TGW or own NAT |
| Block one malicious IP for a whole subnet | **NACL deny rule** |
| Only the web tier may reach the database | **DB SG allows inbound from the web-tier SG** |
| Return traffic is dropped although the SG allows it | **NACL** missing **ephemeral port** rule |
| Admin access to private instances, no open inbound ports, audited | **SSM Session Manager** |
| Consistent, high-bandwidth private link to a data centre | **Direct Connect** |
| Encrypted link needed this week; DX will take months | **Site-to-Site VPN** now, then DX with VPN as backup |
| Encrypt traffic over Direct Connect | **MACsec** or **VPN over DX** |
| One DX connection must reach VPCs in several regions | **Direct Connect gateway** |
| VPN throughput above a single tunnel's limit | **Transit Gateway + ECMP** over multiple tunnels |
| Remote employees need access to the VPC | **AWS Client VPN** |
| Central network team owns the VPC; many accounts deploy into it | **VPC sharing via AWS RAM** |
| Share subnets with another region or outside the Organization | **Not supported** — use peering/TGW or separate VPCs |
| Instances get no DNS names / private hosted zone not resolving | Enable **`enableDnsHostnames` + `enableDnsSupport`** |
| On-prem servers must resolve AWS private DNS names | **Route 53 Resolver inbound endpoint** |
| Inspect and filter all traffic leaving the VPCs (domain filtering) | **AWS Network Firewall** (often with TGW, centralized) |
| Insert third-party firewall appliances transparently | **Gateway Load Balancer** |
| Find out why instance A cannot reach B, without sending traffic | **Reachability Analyzer** |
| Capture full packets for an IDS | **Traffic Mirroring** |
| VPC is running out of IPs | Add a **secondary CIDR** and new subnets (subnets can't be resized) |
| Static public IP that can move to a standby instance | **Elastic IP** |

### Exam Traps

- **"Public subnet" is defined by routes, not by name** — and instances also need a public IPv4/EIP. Auto-assign public IP alone does not make a subnet public either.
- **Attaching an IGW changes no routes.** You still add `0.0.0.0/0 → igw`.
- **A single NAT Gateway is an AZ single point of failure.** One per AZ, each private subnet routed to its own AZ's NAT.
- **NAT Gateway lives in a public subnet** — putting it in a private subnet breaks outbound internet.
- **Peering does not chain**, and you **cannot borrow a peer's IGW/NAT/VPN/DX** (no edge-to-edge).
- **Overlapping CIDRs** break peering, VPN and TGW routing — fix with re-IP, PrivateLink or a private NAT Gateway.
- **SGs cannot deny**; **NACLs are stateless** — forget the ephemeral ports and responses vanish.
- **The default SG is not wide open**: inbound only from itself. **The default NACL is** wide open; a **custom NACL** denies everything.
- **Gateway endpoints do not work from on-prem, peered VPCs or other regions.** Interface endpoints do.
- **Gateway endpoints are free; interface endpoints are not.** Peering has no hourly fee but its data transfer is billed.
- **Direct Connect is not encrypted** and a single connection is not resilient — pair it with a VPN or a second DX location.
- **VPN bandwidth is per tunnel (~1.25 Gbps)**; adding tunnels to a VGW does not aggregate — use TGW + ECMP.
- **Flow logs** are not real-time and do not contain payloads; they do not log DNS-resolver or metadata traffic.
- **The default VPC is convenient but not production-grade**: every subnet is public and auto-assigns public IPs.
- **Custom VPCs ship with DNS hostnames off.**
- **The primary CIDR is permanent** and subnets cannot be resized — plan for growth.
- **IPv6 addresses are public**: block inbound with an egress-only IGW and SGs, not with "private" ranges.
- **Every public IPv4 is billed**, even an EIP attached to a running instance.

### Study Checklist

- [ ] Draw a 3-tier, 2-AZ VPC from scratch: CIDR → subnets per AZ → IGW → route tables → NAT per AZ → SGs chained by reference.
- [ ] Compute usable IPs for `/24`, `/20`, `/28` and name the 5 reserved addresses.
- [ ] Explain SG vs NACL (state, rules, order, scope) without notes.
- [ ] Explain why a private subnet needs a NAT Gateway, where it lives and why one per AZ.
- [ ] Compare peering, Transit Gateway, VPC sharing and PrivateLink for a given topology.
- [ ] Compare gateway vs interface endpoints on cost, DNS, reachability and services.
- [ ] Compare Site-to-Site VPN and Direct Connect on speed, cost, encryption, setup time and resilience.
- [ ] Read a flow log record and say whether an SG or a NACL blocked the traffic.
- [ ] List the bastion alternatives (Session Manager, EC2 Instance Connect Endpoint).
- [ ] Know the SAA-C03 domain weights and the 720/1000 passing score.

## Useful CLI Commands

```bash
# VPCs and their CIDR blocks
aws ec2 describe-vpcs --query "Vpcs[].[VpcId,CidrBlock,IsDefault]" --output table

# DNS attributes of a VPC (one attribute per call)
aws ec2 describe-vpc-attribute --vpc-id vpc-0123456789abcdef0 --attribute enableDnsHostnames
aws ec2 describe-vpc-attribute --vpc-id vpc-0123456789abcdef0 --attribute enableDnsSupport

# Turn DNS hostnames on in a custom VPC
aws ec2 modify-vpc-attribute --vpc-id vpc-0123456789abcdef0 --enable-dns-hostnames '{"Value":true}'

# Subnets with AZ and public-IP setting
aws ec2 describe-subnets \
  --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]" --output table

# Route tables, their subnet associations and routes
aws ec2 describe-route-tables \
  --query "RouteTables[].[RouteTableId,VpcId,Associations[].SubnetId,Routes[].DestinationCidrBlock]" --output json

# Security groups and inbound rules
aws ec2 describe-security-groups \
  --query "SecurityGroups[].[GroupName,GroupId,IpPermissions]" --output json

# Network ACLs and their entries
aws ec2 describe-network-acls \
  --query "NetworkAcls[].[NetworkAclId,IsDefault,Entries[].[RuleNumber,Egress,RuleAction,CidrBlock]]" --output json

# NAT gateways and their state
aws ec2 describe-nat-gateways \
  --query "NatGateways[].[NatGatewayId,State,SubnetId]" --output table

# VPC peering connections
aws ec2 describe-vpc-peering-connections \
  --query "VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code]" --output table

# VPC endpoints
aws ec2 describe-vpc-endpoints \
  --query "VpcEndpoints[].[VpcEndpointId,VpcEndpointType,ServiceName]" --output table

# Flow logs configured in the region
aws ec2 describe-flow-logs \
  --query "FlowLogs[].[FlowLogId,ResourceId,TrafficType,LogDestinationType]" --output table

# RAM resource shares available to this account (shared subnets, etc.)
aws ram get-resource-shares --resource-owner OTHER-ACCOUNTS --output table

# Subnets owned by another account (OwnerId != your account)
aws ec2 describe-subnets \
  --query "Subnets[].[SubnetId,OwnerId,VpcId,CidrBlock,AvailabilityZone]" --output table
```

## References

- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=63222s
- ExamPro SAA-C03 cheat sheet: https://www.exampro.co/saa-c03 (source of the key features / quota list)
- AWS VPC quotas: https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html
- AWS VPC documentation: https://docs.aws.amazon.com/vpc/
- VPC pricing: https://aws.amazon.com/vpc/pricing/
- AWS whitepaper — Building a Scalable and Secure Multi-VPC AWS Network Infrastructure: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html
- SAA-C03 exam guide: https://aws.amazon.com/certification/certified-solutions-architect-associate/
- Related notes in this repo: [VPC Networking fundamentals](networking/README.md), [Default VPC](default-vpc/README.md), [Network ACLs](nacl/README.md), [VPC Sharing with AWS RAM](vpc-sharing/README.md), [AWS Global Infrastructure](../concepts/README.md), [Availability Zones](../concepts/availability-zones/README.md), [Resilience patterns](../concepts/resilience/README.md)
