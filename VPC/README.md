# Amazon VPC — Theoretical Overview

Notes on **Amazon Virtual Private Cloud (VPC)**, the networking layer everything else in AWS runs on. Follows the VPC section of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=63222s) (section starts around **12:19:52**, right after the AWS API chapter).

## What is a VPC?

A **VPC** is a **logically isolated virtual network** inside one AWS region. You choose its IP range (CIDR block), carve it into **subnets**, decide how traffic enters and leaves through **route tables** and **gateways**, and control who can talk to whom with **security groups** and **network ACLs**.

Think of it as your own traditional data-centre network — routers, switches, subnets, firewalls — but defined in software and running on AWS infrastructure.

Key characteristics:

- **Region specific**: a VPC lives in exactly one region and does **not** span regions. To connect networks in different regions you use VPC peering (cross-region peering is supported), Transit Gateway or a VPN/Direct Connect.
- **Account- and region-scoped**: each account gets a **default VPC** per region; you can create additional custom VPCs (up to **5 per region** by default).
- **Defined by CIDR**: primary IPv4 block between **/16 and /28** (65,536 down to 16 addresses). Up to **5 IPv4 CIDR blocks** per VPC (adjustable to 50) plus up to **5 IPv6 /56 CIDR blocks** (also adjustable to 50).
- **Subnets are AZ-scoped**: a subnet belongs to exactly one Availability Zone and cannot span AZs. Multi-AZ designs need one subnet per AZ (up to **200 subnets per VPC**).
- **VPCs themselves are free**: the core building blocks (VPC, subnets, route tables, NACLs, security groups, internet gateways, peering) cost nothing — see [Key Features](#key-features-and-quotas) for what does.
- **The default VPC** is pre-built for convenience: CIDR `172.31.0.0/16`, one `/20` public subnet per AZ, an Internet Gateway, a main route table and permissive default SG/NACL. Custom VPCs start empty.
- **DNS hostnames**: a VPC attribute (`enableDnsHostnames`) decides whether instances get domain-name addresses (`ip-10-0-1-5.eu-north-1.compute.internal`); it is enabled on the default VPC and **disabled by default on custom VPCs**.

```
AWS account / region
└── VPC 10.0.0.0/16                          logically isolated network
     ├── Availability Zone A
     │    ├── public subnet  10.0.1.0/24      route 0.0.0.0/0 -> igw
     │    └── private subnet 10.0.11.0/24     route 0.0.0.0/0 -> nat-gw-a
     ├── Availability Zone B
     │    ├── public subnet  10.0.2.0/24
     │    └── private subnet 10.0.12.0/24     route 0.0.0.0/0 -> nat-gw-b
     └── AZ C ...
```

## Key Features and Quotas

The generic VPC features from the course slide, plus the numbers worth memorizing for the exam:

- **VPCs are region specific** — they do not span regions. **VPC Peering** (including cross-region peering) is what connects VPCs across regions.
- **Up to 5 VPCs per region** by default (adjustable).
- **Every region comes with a default VPC.**
- **Up to 200 subnets per VPC.**
- **Up to 5 IPv4 CIDR blocks per VPC** (adjustable to 50).
- **Up to 5 IPv6 CIDR blocks per VPC** (adjustable to 50).
- **DNS hostnames** — the `enableDnsHostnames` VPC attribute controls whether an instance receives a domain-name address; the companion `enableDnsSupport` must also be true for DNS resolution inside the VPC. Both are **on** in the default VPC and **off** in a custom VPC — you usually want to turn them on.

| Quota | Default | Adjustable |
|---|---|---|
| VPCs per region | **5** | Yes |
| Subnets per VPC | **200** | Yes |
| IPv4 CIDR blocks per VPC | **5** | Yes, up to 50 |
| IPv6 CIDR blocks per VPC | **5** | Yes, up to 50 |
| Primary IPv4 CIDR size | **/16 – /28** | No |

### What VPC costs

**Most components cost nothing:**

- VPCs, subnets, route tables, NACLs, security groups, internet gateways
- **VPC peering** (no hourly charge — but data transferred **across regions** through a peering connection is billed)

**Some things cost money:**

- **NAT Gateway** — hourly + per-GB processed
- **VPC endpoints** — interface endpoints only (hourly per AZ + per GB); **gateway endpoints are free**
- **Site-to-Site VPN connections** (~0.05 USD/hour) and **Client VPN**; the virtual private gateway object itself is free
- **AWS Direct Connect** (port hours + port speed)
- **IPv4 addresses** — every public IPv4 address (including **Elastic IPs**) is billed hourly, even when attached to a running instance

## Core Building Blocks

| Component | What it does |
|---|---|
| **VPC** | The isolated network and its CIDR range. |
| **Subnet** | A slice of the VPC CIDR in **one AZ**; public or private is decided by its route table. |
| **Route table** | Rules (`destination → target`) deciding where traffic goes; the main table is the default for subnets. |
| **Internet Gateway (IGW)** | Attached to the VPC; enables IPv4/IPv6 internet access for resources with public addresses. |
| **NAT Gateway / NAT instance** | Lets **private** subnets reach the internet outbound, without allowing inbound connections. |
| **Security Group (SG)** | **Stateful**, allow-only firewall at the **ENI/instance** level. |
| **Network ACL (NACL)** | **Stateless**, allow+deny firewall at the **subnet** level, evaluated in numbered order. |
| **Elastic Network Interface (ENI)** | Virtual NIC: private IPs, MAC, security groups; can be moved between instances. |
| **Elastic IP (EIP)** | Static public IPv4 address you can detach and re-attach. |
| **VPC endpoint** | Private path to supported AWS services (S3, DynamoDB, and many more) without the internet. |

### CIDR and Subnets

Planning the address space is the first design decision: it must not overlap with other VPCs, on-premises networks or the networks you might later peer with.

- **5 IP addresses are reserved in every subnet**: the network address, the VPC router, the DNS resolver, a future-use address, and the broadcast address. A `/24` therefore gives **251 usable** addresses, not 256.
- A **public subnet** has a route to an **Internet Gateway** and resources need a public IPv4/EIP (or IPv6) to be reachable.
- A **private subnet** has no direct IGW route — typically `0.0.0.0/0 → NAT Gateway` for outbound-only access.
- Subnets **cannot be resized**; you create new ones. You *can* add secondary CIDR blocks to a VPC — up to **5 blocks per VPC** (adjustable to 50) — which is how you grow without rebuilding.
- **IPv6** uses a **/56 block per VPC** (also up to 5 blocks, adjustable to 50); each subnet gets a /64. For outbound-only IPv6 use an **egress-only Internet Gateway** instead of a NAT Gateway.
- **Overlapping CIDRs** block VPC peering and VPN routing. AWS IPAM or careful planning avoids this.

### Route Tables

A route table is a list of destinations and targets. Every VPC has a **main route table**; subnets without an explicit association use it.

- The **local route** (`10.0.0.0/16 → local`) is always present and cannot be deleted — it lets subnets in the VPC talk to each other.
- **Longest prefix match wins**: a `/24` route beats a `/16` route beats `0.0.0.0/0`.
- Common targets: `igw-…` (internet), `nat-…` (NAT Gateway), `eni-…` (appliance/firewall), `pcx-…` (peering), `tgw-…` (Transit Gateway), `vpce-…` (gateway endpoint), `vgw-…` (VPN).
- To make a subnet public: associate a route table with `0.0.0.0/0 → igw` **and** give the instance a public IP/EIP. The route alone is not enough.
- Route tables are **associated with subnets**, so different subnets in the same VPC can have different egress paths.

### Internet Gateway

- **One per VPC**, horizontally scaled, redundant and highly available — no bandwidth bottleneck and no hourly charge.
- Performs NAT for instances that have a **public IPv4** address, and is required for IPv6 internet access.
- It is **not** a firewall; security groups and NACLs still apply.

### NAT: Gateway vs Instance

Private subnets need outbound internet access for patches, package installs and API calls. Two options:

| | **NAT Gateway** | **NAT Instance** |
|---|---|---|
| Managed by | AWS | You (an EC2 instance) |
| Availability | One per AZ; deploy one per AZ for HA | Single instance unless you build HA yourself |
| Scaling | Automatic, up to ~100 Gbps | Depends on instance type |
| Cost | Hourly + per-GB processed | EC2 instance + data transfer; can be cheaper at low volume |
| Setup | Place in a **public subnet** with an **EIP** | Disable **source/destination check**, manage SG and AMI |
| Security groups | Not applicable | Applies to the instance |
| Bastion / inbound | No | Possible (a NAT instance can double as a bastion) |
| IPv6 | Not used — use **egress-only IGW** | Not used |

Exam rule of thumb: **"managed, highly available, scales" → NAT Gateway**; **"cheapest possible, low traffic, can tolerate a single point of failure" → NAT instance**.

A **private NAT Gateway** has no EIP and is used to translate traffic between overlapping networks (e.g. on-prem → VPC) or for outbound traffic from a private subnet to another VPC/on-prem.

### Security Groups

- **Stateful**: if inbound traffic is allowed, the response is automatically allowed back out (and vice versa). No ephemeral-port rules needed.
- **Allow rules only** — there is no explicit deny. Anything not allowed is dropped.
- Applied at the **ENI / instance** level; one instance can have multiple SGs.
- **All rules are evaluated together** before a decision (unlike NACLs, which stop at the first match).
- Default: **deny all inbound**, **allow all outbound**. A new SG therefore blocks everything inbound until you add rules.
- Rules can reference **another security group** (e.g. "allow 3306 from the web-tier SG") instead of IP ranges — this is the cleanest way to chain tiers.
- Changes apply **immediately** to all associated resources.

### Network ACLs

- **Stateless**: return traffic must be explicitly allowed in the opposite direction, including **ephemeral ports 1024–65535**.
- Applied at the **subnet** level, so it affects every resource in that subnet.
- **Allow and deny** rules, evaluated in **numbered order** — the first match wins, so order matters.
- Separate **inbound** and **outbound** rule sets.
- The **default NACL** allows all traffic. A **custom NACL** denies all traffic until you add rules.
- Use it when you need to **block a specific IP/range** — security groups cannot do that.

### Security Group vs NACL

| | **Security Group** | **NACL** |
|---|---|---|
| Level | Instance / ENI | Subnet |
| State | **Stateful** | **Stateless** |
| Rule types | Allow only | Allow **and** deny |
| Evaluation | All rules | First match, in order |
| Return traffic | Automatically allowed | Must be explicitly allowed |
| Typical use | Tier-to-tier access control | Broad subnet guardrails, IP blocking |

## Connecting VPCs and Networks

### VPC Peering

- **One-to-one** connection between two VPCs (same or different region/account).
- Traffic stays on the AWS backbone; no single point of failure or bandwidth bottleneck.
- **No transitive routing**: if A peers with B and B peers with C, A cannot reach C through B. You need a full mesh or Transit Gateway.
- **CIDRs must not overlap**.
- You must add routes in **both** VPCs and allow traffic in SGs/NACLs on both sides.
- Cheapest option for a small number of VPCs; becomes unmanageable as the mesh grows.

### Transit Gateway (TGW)

- A **regional hub-and-spoke router** that connects many VPCs, VPNs and Direct Connect gateways.
- Supports **transitive routing**, so a full mesh of peerings is not needed.
- Attachments: VPCs, Site-to-Site VPN, Direct Connect gateway, TGW peering (cross-region).
- Has its own **route tables**, which let you segment networks (prod/dev/security) and centralize inspection.
- The standard answer for **"many VPCs + on-premises, centralized connectivity"**.

### VPC Endpoints and PrivateLink

Endpoints let resources reach AWS services **privately**, without an Internet Gateway or NAT Gateway.

| | **Gateway endpoint** | **Interface endpoint** |
|---|---|---|
| Supported services | **S3 and DynamoDB** only | Most AWS services and SaaS (via PrivateLink) |
| How it works | A route-table target (`vpce-…`) | An **ENI** in your subnet with a private IP |
| Security groups | Not on the endpoint (instance SGs still apply) | Used on the endpoint ENI |
| Cost | **Free** | Hourly per AZ + per-GB processed |
| DNS | Uses the service's public DNS name | Private DNS name resolves to the endpoint ENI |
| From on-premises | **No** | **Yes**, over Direct Connect/VPN (with Route 53 Resolver) |
| From another region | **No** | **Yes**, over VPC peering or Transit Gateway |

- **Gateway endpoints** are the cost-optimal answer for **private S3/DynamoDB access** from inside the VPC. They **do not** work from on-premises or from another region — use an interface endpoint for those.
- **Interface endpoints / PrivateLink** are the answer for **everything else**, for **overlapping CIDRs**, for **on-premises/other-region access**, and for consuming **third-party SaaS** privately.
- **Endpoint policies** restrict which resources/actions the endpoint can reach (e.g. only one bucket).

### Site-to-Site VPN

- **IPsec tunnel over the public internet** between your network and AWS (Virtual Private Gateway or Transit Gateway).
- Each connection has **two tunnels** for redundancy; one tunnel alone is not highly available.
- Up to **~1.25 Gbps per tunnel**; use **ECMP** with multiple tunnels/TGW to scale beyond that.
- Quick to set up (minutes/hours), encrypted, but latency and throughput depend on the internet.
- Common pattern: **Direct Connect as primary + VPN as backup**.

### AWS Direct Connect (DX)

- A **dedicated private fibre connection** from your data centre to an AWS Direct Connect location.
- **1, 10 or 100 Gbps** dedicated ports (hosted connections go lower); can use **LAG** to bundle links.
- **VIFs**: private VIF (to a VPC via VGW), public VIF (to public AWS services), transit VIF (to a Direct Connect gateway / TGW).
- **Not encrypted by default** — add **MACsec** or run a **Site-to-Site VPN over DX** when encryption is required.
- Takes **weeks to months** to provision; use VPN as a backup during/alongside it.
- The answer for **"consistent low latency, high bandwidth, private connectivity to AWS"**.

### Other Networking Pieces

- **Egress-only Internet Gateway** — outbound-only IPv6 (the IPv6 counterpart of NAT).
- **VPC sharing (AWS RAM)** — a VPC owner shares subnets with other accounts; participants launch resources in the shared subnets but cannot modify the VPC.
- **DHCP option sets** — custom DNS/domain names for instances.
- **VPC DNS attributes** — `enableDnsHostnames` (instances get domain-name addresses) and `enableDnsSupport` (VPC DNS resolver answers queries); both required for DNS-based service discovery. The default VPC has them on, custom VPCs start with both off.
- **Route 53 Resolver** — inbound/outbound DNS endpoints to resolve names between on-premises and AWS.
- **VPC Flow Logs** — capture IP traffic metadata at VPC/subnet/ENI level; deliver to CloudWatch Logs, S3 or Firehose. Useful for troubleshooting and security analysis, but **not real-time** and not a packet capture.
- **Traffic Mirroring** — copy actual packets from an ENI for deep inspection.
- **Reachability Analyzer** — static analysis of whether a path *would* work; it sends **no packets**.
- **Network Access Analyzer** — finds unintended network access paths.

## Topics Covered in the Course

The VPC chapter of the course walks through the pieces above, roughly in this order:

| Topic | What to take away |
|---|---|
| **Key features / quotas** | Region specific, default VPC, 5 VPCs per region, 200 subnets per VPC, 5 IPv4/IPv6 CIDR blocks, DNS hostnames attribute, what is free vs paid. |
| **VPC fundamentals** | Region/AZ scope, CIDR planning, default vs custom VPC, default subnets. |
| **Subnets** | Public vs private, the 5 reserved IPs, one AZ per subnet. |
| **Internet Gateway** | Attaching an IGW, public IP requirement, route to `0.0.0.0/0`. |
| **Route tables** | Main vs custom tables, subnet associations, longest prefix match. |
| **Security groups** | Stateful, allow-only, SG references, default deny inbound. |
| **Network ACLs** | Stateless, ordered allow/deny, ephemeral ports. |
| **NAT** | NAT Gateway vs NAT instance, placement in a public subnet, HA per AZ. |
| **VPC peering** | 1:1, no transitive routing, no overlapping CIDRs, routes on both sides. |
| **VPC endpoints** | Gateway (S3/DynamoDB) vs interface (PrivateLink), cost and DNS. |
| **VPC Flow Logs** | What is captured, where logs go, how to troubleshoot. |
| **Site-to-Site VPN** | IPsec over the internet, two tunnels, VGW/TGW. |
| **Direct Connect** | Dedicated links, VIFs, latency/bandwidth, encryption caveat. |
| **VPC follow-along / hands-on** | Build a VPC from scratch: subnets, IGW, route tables, SG/NACL, EC2, bastion, NAT. |

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

VPC questions appear in **all four domains** — security (SG/NACL/endpoints), resilience (multi-AZ subnets, VPN backup), performance (DX, TGW, placement) and cost (gateway endpoints vs NAT, peering vs TGW).

### High-Yield Facts

- A subnet lives in **exactly one AZ**; multi-AZ means multiple subnets.
- **5 IPs are reserved** per subnet (network, router, DNS, future use, broadcast).
- **Default quotas**: 5 VPCs per region, 200 subnets per VPC, 5 IPv4 and 5 IPv6 CIDR blocks per VPC (all adjustable; CIDR blocks up to 50).
- The **local route** in a route table cannot be deleted.
- **Custom VPCs have `enableDnsHostnames` and `enableDnsSupport` off** — the default VPC has both on.
- **1 Internet Gateway per VPC**; it is highly available and free.
- **Free**: VPCs, subnets, route tables, NACLs, security groups, internet gateways, VPC peering. **Paid**: NAT Gateway, interface endpoints, VPN connections, Direct Connect, public IPv4/Elastic IPs.
- **Security groups are stateful; NACLs are stateless** — this is asked constantly.
- **Security groups cannot deny**; use a **NACL** to block an IP.
- **NACLs need ephemeral ports 1024–65535** allowed for return traffic.
- **NAT Gateway is AZ-scoped**: one per AZ for high availability.
- **NAT Gateway needs a public subnet and an EIP**; NAT instance needs **source/destination check disabled**.
- **VPC peering is not transitive** and requires **non-overlapping CIDRs**.
- **Transit Gateway** is the hub for many VPCs/VPNs/DX and supports transitive routing.
- **Gateway endpoints** (S3/DynamoDB) are **free**; interface endpoints cost per hour and per GB.
- **Direct Connect is not encrypted** by default; use VPN over DX or MACsec.
- **Site-to-Site VPN has two tunnels**; one tunnel is not HA.
- **VPC Flow Logs** do not capture packet contents and are not real-time.
- **Reachability Analyzer** checks configuration without sending traffic.
- **Egress-only IGW** is for outbound-only IPv6; NAT Gateway is IPv4.

### Scenario → Answer

| Requirement | Answer |
|---|---|
| Private subnet instances need OS updates, no inbound internet | **NAT Gateway** in a public subnet |
| Cheapest private access to S3 from a VPC | **Gateway VPC endpoint** |
| Private access to a service that is not S3/DynamoDB | **Interface endpoint (PrivateLink)** |
| Two VPCs in different regions need low-latency private connectivity | **Inter-Region VPC peering** |
| Dozens of VPCs and on-premises networks need any-to-any routing | **Transit Gateway** |
| Block one specific malicious IP for a whole subnet | **Network ACL deny rule** |
| Allow only the web tier to reach the database tier | **Security group referencing another security group** |
| Dedicated, consistent connection to AWS from a data centre | **Direct Connect** |
| Quick encrypted connection over the internet while DX is provisioned | **Site-to-Site VPN** (then DX + VPN backup) |
| Encrypt traffic over Direct Connect | **VPN over DX** or **MACsec** |
| Outbound-only IPv6 internet access | **Egress-only Internet Gateway** |
| Give another account its own resources inside your VPC | **VPC sharing via AWS RAM** |
| Instances need domain-name addresses / DNS resolution fails | **Enable `enableDnsHostnames` + `enableDnsSupport`** on the VPC |
| Many VPCs need to reach the same S3 bucket cheaply | **Gateway endpoint per VPC** (or central egress design) |
| Centralized traffic inspection between VPCs | **Transit Gateway + Network Firewall / Gateway Load Balancer** |

### Exam Traps

- **"Public subnet" is defined by routes, not by name.** A subnet with `0.0.0.0/0 → igw` still needs public IPs/EIPs for its instances.
- **A NAT Gateway in one AZ does not protect against that AZ failing.** Deploy one per AZ and give each private subnet a route to the NAT in its own AZ.
- **Peering does not chain.** A→B and B→C does not give A→C; use TGW.
- **Overlapping CIDRs** break peering/VPN/TGW routing — re-IP, use PrivateLink, or use a private NAT Gateway.
- **Security group changes are immediate**, NACL changes too, but **flow logs** and **CloudTrail** are not real-time.
- **Gateway endpoints are regional** and tied to the VPC's route tables; **interface endpoints are per-AZ ENIs**.
- **Direct Connect alone is not encrypted** and is not a complete DR strategy — pair it with a VPN.
- **VPN throughput is per tunnel (~1.25 Gbps)**, not per connection; aggregate with TGW/ECMP or multiple connections.
- **Default VPC is convenient but not production-grade**: permissive default SG/NACL and public subnets by default.
- **Custom VPCs ship with DNS hostnames/support disabled** — instances get no domain name until you enable the VPC attributes.
- **Not everything in a VPC is free**: gateway endpoints are, interface endpoints are not; peering has no hourly fee but cross-region peering data transfer does.
- **EIPs are regional and limited** (5 per region by default); releasing unused ones avoids charges.

### Study Checklist

- [ ] Draw a VPC from scratch: CIDR → subnets per AZ → IGW → route tables → SG/NACL → EC2 → NAT.
- [ ] Explain the difference between SG and NACL without notes.
- [ ] Explain why a private subnet needs a NAT Gateway and where it must live.
- [ ] Compare peering, Transit Gateway and PrivateLink for a given topology.
- [ ] Compare gateway vs interface endpoints on cost, DNS and supported services.
- [ ] Compare Site-to-Site VPN and Direct Connect on speed, cost, encryption and setup time.
- [ ] Read a flow log line and say whether SG or NACL likely blocked the traffic.
- [ ] Know the SAA-C03 domain weights and the 720/1000 passing score.

## Useful CLI Commands

```bash
# VPCs and their CIDR blocks
aws ec2 describe-vpcs --query "Vpcs[].[VpcId,CidrBlock,IsDefault]" --output table

# DNS hostnames / DNS support attributes of a VPC
aws ec2 describe-vpc-attributes --vpc-id vpc-0123456789abcdef0 \
  --query "VpcAttributes[].[Attribute,Value]" --output table

# Subnets with AZ and public-IP setting
aws ec2 describe-subnets \
  --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]" --output table

# Route tables and their routes
aws ec2 describe-route-tables \
  --query "RouteTables[].[RouteTableId,VpcId,Routes[].DestinationCidrBlock]" --output table

# Security groups and inbound rules
aws ec2 describe-security-groups \
  --query "SecurityGroups[].[GroupName,GroupId,IpPermissions]" --output json

# NAT gateways and their state
aws ec2 describe-nat-gateways \
  --query "NatGateways[].[NatGatewayId,State,SubnetId]" --output table

# VPC peering connections
aws ec2 describe-vpc-peering-connections \
  --query "VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code]" --output table

# VPC endpoints
aws ec2 describe-vpc-endpoints \
  --query "VpcEndpoints[].[VpcEndpointId,VpcEndpointType,ServiceName]" --output table
```

## References

- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=63222s 
- ExamPro SAA-C03 cheat sheet: https://www.exampro.com/ssa-c03 (source of the key features / quota list)
- AWS VPC quotas: https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html
- AWS VPC documentation: https://docs.aws.amazon.com/vpc/
- VPC pricing: https://aws.amazon.com/vpc/pricing/
- SAA-C03 exam guide: https://aws.amazon.com/certification/certified-solutions-architect-associate/
- Related notes in this repo: [AWS Global Infrastructure](../concepts/README.md), [Availability Zones](../concepts/availability-zones/README.md), [Resilience patterns](../concepts/resilience/README.md)
