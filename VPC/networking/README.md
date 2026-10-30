# VPC Networking — The Pieces and How Traffic Actually Flows

A fundamentals-first companion to the [full VPC notes](../README.md) (which are organised
for exam revision). This page answers one question: **when an instance inside a VPC sends
a packet, what decides where it goes?**

Four objects decide it: the **VPC** (the network and its address range), **subnets**
(AZ-pinned slices of it), **route tables** (the signposts) and the **Internet Gateway**
(the door to the public internet). Security groups and NACLs then decide whether the
packet is *allowed* to take that path.

```
   93.184.216.34 (internet)
            |
      [ igw-0123 ]              Internet Gateway, attached to the VPC
            |
 ===== VPC 10.0.0.0/16 ========================================  implicit VPC router
      |                                |
 AZ: eu-north-1a                   AZ: eu-north-1b
 10.0.0.0/20  (public)             10.0.16.0/20 (private)
 rtb-public (custom):              rtb-main (main table):
   10.0.0.0/16 -> local              10.0.0.0/16 -> local
   0.0.0.0/0   -> igw-0123           0.0.0.0/0   -> nat-0456 (lives in the public subnet)
      |                                |
  [ EC2, public IP ]               [ EC2, private IP only ]
```

## 0. CIDR in five minutes

Everything in a VPC is expressed in **CIDR notation**: `address/prefix`. The prefix says
how many leading bits are fixed (the network part); the rest are free (the hosts).

```
10.0.0.0/16   ->  first 16 bits fixed  ->  2^(32-16) = 65,536 addresses  10.0.0.0 – 10.0.255.255
10.0.1.0/24   ->  first 24 bits fixed  ->  2^(32-24) =    256 addresses  10.0.1.0 – 10.0.1.255
```

| Prefix | Addresses | Usable in a subnet (−5) | Typical use |
|---|---|---|---|
| `/16` | 65,536 | 65,531 | Whole VPC (largest allowed) |
| `/20` | 4,096 | 4,091 | Default VPC subnets, large subnets |
| `/24` | 256 | 251 | Common subnet size |
| `/26` | 64 | 59 | Small tier |
| `/28` | 16 | **11** | Smallest allowed (e.g. TGW attachment subnets) |

Mental shortcut: **every +1 on the prefix halves the block**. A `/16` splits into 16 ×
`/20` or 256 × `/24`.

Which ranges to use:

- **RFC 1918 private ranges**: `10.0.0.0/8`, `172.16.0.0/12` (172.16.x – 172.31.x),
  `192.168.0.0/16`. The default VPC's `172.31.0.0/16` sits inside `172.16.0.0/12`.
- AWS *accepts* publicly routable ranges, but then those addresses belong to someone else
  on the internet: your VPC routes them `local`, so you can never reach the real owners.
- Pick a range that **will not overlap** with on-premises or any VPC you may connect later
  — overlap cannot be routed around.

## 1. The VPC: a private network with an address range

A VPC is a logically isolated network in **one region**, defined by a primary CIDR block
between `/16` and `/28`. It comes with an implicit **VPC router** in every AZ — you never
see or manage it, but it is what applies the route tables.

- The router makes every subnet reachable from every other subnet in the VPC through the
  **local route**. Reachable is not the same as *allowed*: SGs and NACLs still filter.
- The primary CIDR **cannot be changed**. To grow, add **secondary CIDR blocks** (up to 5
  in total by default) and create new subnets in them.

## 2. Subnets: the slice you actually launch into

You never launch "into a VPC" — you launch into a **subnet**, and a subnet is pinned to
exactly **one AZ** (it cannot span AZs). It is a contiguous chunk of the VPC CIDR, e.g.
`10.0.0.0/20`, and subnets in one VPC cannot overlap each other.

**5 addresses are reserved** in every subnet. For `10.0.0.0/24`:

| Address | Reserved for |
|---|---|
| `10.0.0.0` | Network address |
| `10.0.0.1` | VPC router |
| `10.0.0.2` | Amazon-provided DNS (the resolver sits at VPC base + 2) |
| `10.0.0.3` | Reserved for future use |
| `10.0.0.255` | Broadcast (VPCs do not support broadcast; reserved anyway) |

So the first address you can give an instance is `.4`.

Subnet attributes worth knowing:

- **`MapPublicIpOnLaunch`** — auto-assign a public IPv4 to instances launched here. **On**
  in default subnets, **off** in subnets you create.
- **Public / private / isolated are not checkboxes.** There is no `isPublic` flag. A
  subnet is public or private purely because of **the route table it is associated with**
  (plus whether instances have public IPs). Rename it and nothing changes; change its
  route and its whole behaviour changes.
- Subnets **cannot be resized** — delete and recreate, or add a new one.

## 3. Route tables: destination → target

A route table is a list of rules, each with a **destination CIDR** and a **target**:

| Destination | Target | Meaning |
|---|---|---|
| `10.0.0.0/16` | `local` | inside the VPC (auto-created, **cannot be deleted**) |
| `0.0.0.0/0` | `igw-0123` | "everything else → the internet" |
| `0.0.0.0/0` | `nat-0456` | "everything else → the NAT Gateway" |
| `10.9.0.0/16` | `pcx-0abc` | "→ peered VPC" |
| `pl-…` (S3 prefix list) | `vpce-0def` | "→ S3 through a gateway endpoint" |
| `192.168.0.0/16` | `vgw-0789` | "→ on-premises through the VPN" |

How the decision is made:

- **Every subnet is associated with exactly one route table**; one table can serve many
  subnets. A new VPC has a single **main route table**, and any subnet without an explicit
  association silently uses it.
- **Longest prefix match wins**: for a packet to `10.0.1.7`, a `10.0.1.0/24` route beats
  `10.0.0.0/16`, which beats `0.0.0.0/0`.
- `0.0.0.0/0` is the **default route** — the fallback when nothing more specific matches.
  Pointing it at an IGW is what "sending traffic to the internet" means in a VPC. `::/0` is the IPV6 version.
- Route tables are associated with **subnets**, not with the VPC as a whole — that is how
  two subnets in the same VPC have different egress paths.
- **Best practice**: leave the main table **private** (local route only, or NAT) and give
  public subnets an explicit **custom** table with the IGW route. Then a subnet created
  later, and forgotten, is private by default instead of public by accident.

## 4. Internet Gateway: the edge of the VPC

The IGW is a virtual router that must be **created and then attached to the VPC** — two
separate API calls; an unattached IGW does nothing.

- **One per VPC** (and one VPC per IGW), horizontally scaled and redundant, **free**, no
  bandwidth limit.
- Performs **1:1 NAT**: it swaps the instance's private IPv4 for its **public IPv4 / EIP**
  on the way out, and back on the way in. The instance's OS only ever sees its private IP.
- It is **not a firewall**: SGs and NACLs still filter.
- For IPv6 it simply routes (IPv6 addresses are already public). For outbound-only IPv6
  use an *egress-only* Internet Gateway.

### The three conditions for internet access

A resource in a subnet reaches the internet only if **all** hold:

1. the VPC has an IGW **attached**,
2. the subnet's route table has **`0.0.0.0/0 → igw-…`**,
3. the resource has a **public IPv4 / Elastic IP** (or an IPv6 address).

Miss any one and traffic goes nowhere. On top of that, SG and NACL must allow it.

A **private subnet** has no IGW route. For outbound-only access it routes `0.0.0.0/0` to
a **NAT Gateway** that sits in a *public* subnet: the private instance → NAT (source NAT
to the NAT's EIP) → IGW → internet. Replies come back the same way; connections initiated
from the internet have nowhere to land.

## 5. Packet flow end to end

**Outbound** (instance `10.0.0.5` with public IP → `93.184.216.34:443`):

1. **Security group** on the ENI — outbound is allow-all by default → allowed. SGs are
   stateful, so the reply will be let back in automatically.
2. **NACL** of the subnet, *outbound* rules — stateless, numbered, first match → allowed.
3. **Route table** of the subnet: longest match is `0.0.0.0/0 → igw-0123`.
4. **IGW** rewrites source `10.0.0.5` to the public IP and forwards to the internet.
5. The **reply** arrives at the IGW, is mapped back to `10.0.0.5`, and must pass the NACL
   *inbound* rules — which need **ephemeral ports 1024–65535** allowed, because the reply
   targets the port the client picked. The SG lets it in without any rule (stateful).

**Inbound** (`93.184.216.34` → the instance's public IP on port 443):

1. **IGW** maps the public IP to the private IP — only possible if the instance **has** a
   public IP/EIP.
2. **NACL inbound**: port 443 must be allowed.
3. **Security group inbound**: port 443 must be allowed from the source.
4. The instance answers; the reply passes the SG automatically, but the **NACL outbound**
   rules must allow the client's **ephemeral port range**.

Order of evaluation: **inbound NACL → SG → instance**, **outbound SG → NACL**. To *block*
a specific IP, use a NACL deny — security groups cannot deny. Traffic between two
instances in the **same subnet** never crosses the NACL; the SGs still apply.

## 6. How this maps to the hands-on script

[`../vpc/create-vpc`](../vpc/create-vpc) builds a **minimal public network**: one VPC,
one IGW and **one** subnet routed to it — the left half of the diagram, without the
private subnet and NAT Gateway.

| Script step | Concept it creates |
|---|---|
| `create-vpc --cidr-block 172.1.0.0/16` | the network + implicit VPC router + **main route table**, default NACL, default SG |
| `create-internet-gateway` | the IGW object (does nothing yet) |
| `attach-internet-gateway` | binds the IGW to the VPC (condition 1) |
| `create-subnet --cidr-block 172.1.0.0/20` | a `/20` subnet (4,091 usable IPs); no `--availability-zone`, so AWS picks the AZ |
| `associate-route-table` with `RouteTables[0]` | the only table in the VPC *is* the main one, so this explicitly associates the subnet with the **main** route table |
| `create-route 0.0.0.0/0 → $IGW_ID` | condition 2 — *this* is what makes the subnet public |

Things to notice about the lab, all good exam material:

- **Attaching the IGW does not change any routing.** Without the explicit
  `0.0.0.0/0 → igw` route the subnet stays private.
- **The IGW route goes into the main route table**, so *every* future subnet in this VPC
  without its own association is public too. Fine for a lab; in a real design you would
  create a separate public route table and keep the main one private.
- **Condition 3 is still missing**: a subnet you create has `MapPublicIpOnLaunch = false`,
  so an instance launched there gets no public IP unless you pass
  `--associate-public-ip-address` or enable the subnet attribute
  (`aws ec2 modify-subnet-attribute --subnet-id … --map-public-ip-on-launch`).
- **`172.1.0.0/16` is not a private RFC 1918 range** — it is public address space (the
  private block is `172.16.0.0/12`). AWS allows it, but real hosts in `172.1.x.x` become
  unreachable from this VPC. Prefer `10.x.x.x` or `172.16–31.x.x` for anything beyond a lab.
- **DNS hostnames are off** in a custom VPC, so instances get no DNS names until you run
  `modify-vpc-attribute --enable-dns-hostnames`.
- [`../vpc/delete-vpc`](../vpc/delete-vpc) tears down in reverse dependency order: detach
  and delete the IGW, delete the subnet, delete the VPC. The main route table, default
  NACL and default SG go away with the VPC.

Practical gotchas when checking the result in the console:

- Every command passes `--region eu-north-1`; the console's region selector must show
  **Stockholm (eu-north-1)** too, or the VPC dashboard looks empty.
- Attachments and routes are **eventually consistent** — a few seconds can pass before the
  VPC's resource map reflects them.

## Commands

```bash
# Routes of every route table in a VPC (is 0.0.0.0/0 -> igw there? which subnets use it?)
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "RouteTables[].[RouteTableId,Associations[*].[Main,SubnetId],Routes[*].[DestinationCidrBlock,GatewayId]]" \
  --output json

# IGW and the VPC it is attached to (empty Attachments = created but not attached)
aws ec2 describe-internet-gateways \
  --filters "Name=tag:Name,Values=my-igw-fboetti" \
  --query "InternetGateways[*].[InternetGatewayId,Attachments[*].VpcId]" --output table

# Subnets: CIDR, AZ, free IPs and public-IP auto-assign
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone,AvailableIpAddressCount,MapPublicIpOnLaunch]" \
  --output table

# Make instances in the subnet get a public IPv4 automatically (condition 3)
aws ec2 modify-subnet-attribute --subnet-id "$SUBNET_ID" --map-public-ip-on-launch

# Give instances DNS hostnames (off by default in a custom VPC)
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames '{"Value":true}'
```

## Exam traps (short list — full list in [../README.md](../README.md))

- **"Public subnet" is defined by routes, not by name** — and the instance still needs a
  public IP/EIP.
- **Attaching an IGW ≠ routing to it.** Both are required.
- Route tables are associated with **subnets**; the **main table is the fallback** for
  subnets without an explicit association.
- The **local route cannot be deleted** — intra-VPC routing always works (filtering is
  up to SGs/NACLs).
- **Longest prefix match** decides between overlapping routes.
- **5 reserved IPs** per subnet: a `/24` gives 251, a `/28` gives 11.
- Subnets **cannot span AZs** or be resized; multi-AZ means one subnet per AZ.
- **NACLs are stateless**: allow ephemeral ports 1024–65535 for return traffic.
- The IGW is **not a firewall** and is **free**; NAT Gateways are neither.

## Related

- [Amazon VPC — Theoretical Overview](../README.md) — quotas, SG vs NACL, NAT, peering,
  TGW, endpoints, hybrid connectivity, exam notes.
- [Default VPC](../default-vpc/README.md) — the pre-built version of this network.
- [Availability Zones](../../concepts/availability-zones/README.md)
- [Resilience patterns](../../concepts/resilience/README.md)
- Scripts: [`../vpc/create-vpc`](../vpc/create-vpc), [`../vpc/delete-vpc`](../vpc/delete-vpc)
