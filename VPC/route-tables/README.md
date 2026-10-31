# Route Tables — Exam Notes

A **route table** is a list of rules (**destination CIDR → target**) that tells the VPC
router where to send a packet leaving a subnet. It decides **where traffic goes**; security
groups and [NACLs](../nacl/README.md) decide **whether it is allowed**. The step-by-step
packet walk is in [VPC Networking](../networking/README.md#3-route-tables-destination--target);
this page is about the table itself and how it ties into every other VPC service.

```
 EC2 ──> SG (out) ──> subnet ──> ROUTE TABLE ──> target (igw / nat / pcx / tgw / vgw / vpce)
                                      │
                                      └─ NACL (out) is checked at the subnet edge as well
```

## How Route Tables Work

| Property | Behaviour |
|---|---|
| **Scope** | A **VPC** (Regional); the table lives in one VPC and is used by its subnets only |
| **Association** | Each subnet has **exactly one** route table; one table can serve **many** subnets |
| **Main route table** | Created with the VPC; used by every subnet **without an explicit association**. You can edit it and **replace** which table is main, but not delete it |
| **Custom route table** | Created by you; contains only the **local route** until you add more |
| **Local route** | `VPC CIDR → local`; automatic, **cannot be deleted or changed**; one per CIDR block (incl. secondary CIDRs and IPv6) |
| **Selection** | **Longest prefix match** wins; the order of rows is irrelevant |
| **Quota** | **200** route tables per VPC; **50** non-propagated routes per table (adjustable to 1,000); **100** BGP-propagated routes |
| **Propagation** | Changes apply **immediately** |
| **Cost** | Free |

- A subnet is **public** only because its table has `0.0.0.0/0 → igw-…`; private if not.
  See [Subnets and Route Tables](../README.md#subnets-and-route-tables).
- Route tables filter **nothing**: a route to a target does not mean the traffic is
  allowed — SG and NACL still apply.

## Route Targets

| Target | Prefix | Typical route | Notes |
|---|---|---|---|
| Local | `local` | `10.0.0.0/16 → local` | Always present; VPC-internal traffic |
| Internet Gateway | `igw-` | `0.0.0.0/0 → igw-…` | Public IPv4/EIP also needed |
| Egress-only IGW | `eigw-` | `::/0 → eigw-…` | **IPv6 outbound only** |
| NAT Gateway | `nat-` | `0.0.0.0/0 → nat-…` | Placed in a **public** subnet; IPv4 outbound for private subnets |
| VPC peering | `pcx-` | `10.9.0.0/16 → pcx-…` | **Both** sides need a route; not transitive |
| Transit Gateway | `tgw-` | `10.0.0.0/8 → tgw-…` | Hub for VPCs, VPN, Direct Connect |
| Virtual private gateway | `vgw-` | `192.168.0.0/16 → vgw-…` | VPN / Direct Connect to on-premises; supports **propagation** |
| Gateway endpoint | `vpce-` | `pl-… (S3 / DynamoDB) → vpce-…` | Route via **prefix list**; free |
| Network interface | `eni-` | `0.0.0.0/0 → eni-…` | Appliance / NAT instance / firewall |
| Gateway Load Balancer endpoint | `vpce-` | `0.0.0.0/0 → vpce-…` | Steer traffic through third-party appliances |
| Carrier / Outposts / Local gateways | `cagw-` `lgw-` | | Wavelength and Outposts, rarely exam-relevant |

Interface endpoints (PrivateLink) need **no route**: they are ENIs with a private IP in the
subnet, reached through the `local` route and DNS.

## Route Priority

When several routes could match a destination:

1. **Longest prefix** (most specific CIDR) wins.
2. If prefixes are equal: **local** → **static** routes → **propagated** routes. Among
   propagated routes: **Direct Connect** > **VPN static** > **VPN BGP**.
3. A route that points to a **deleted or unavailable target** becomes a **blackhole** and
   drops traffic; it never falls back to a broader route automatically.

The local route is the most specific route for the VPC CIDR, so intra-VPC traffic stays
local. The only exception is a route **more specific** than the local one that targets a
network interface or Gateway Load Balancer endpoint (used to inspect intra-VPC traffic).

## Route Table Associations

| Type | Used for |
|---|---|
| **Subnet association** | Normal case: this table controls the subnet's **outbound** routing |
| **Main (implicit) association** | Subnet with no explicit association |
| **Gateway association (edge association)** | Attach a table to an **IGW** or **VGW** to route **incoming** traffic (e.g. send ingress traffic through a firewall appliance first) |

A subnet cannot have two tables. To change a subnet's behaviour you **replace** its
association — and an explicit association with a custom table overrides the main table.

## Relationship With Other VPC Services

### Internet Gateway
- Route `0.0.0.0/0 → igw` makes the subnet public. The IGW also does the 1:1 NAT between
  private and public IPv4 — a public IP alone without the route is useless.
- One IGW per VPC; it has no bandwidth limit and no availability concern.

### NAT Gateway
- The NAT gateway sits in a **public subnet**; private subnets point their default route to
  it: `0.0.0.0/0 → nat-…`. The NAT subnet's own table must have `0.0.0.0/0 → igw`.
- **Per-AZ NAT** + one private table **per AZ** = resilient design; a single NAT is an AZ
  single point of failure.

### VPC Peering
- Peering needs a route in **both** VPCs' tables (each pointing to `pcx-…`). The accepter
  must also add its route; no routes means no traffic even though the connection is active.
- **Not transitive**: A↔B and B↔C does not give A↔C. CIDRs must **not overlap**.
- Edge-to-edge routing (via the peer's IGW, VPN or endpoint) is **not** supported.

### Transit Gateway
- VPC tables point the remote CIDRs to `tgw-…`; the TGW has **its own route tables**
  (association + propagation) to segment prod / dev / shared services.
- Needed for transitive routing between many VPCs and on-premises.

### VPN / Direct Connect
- Enable **route propagation** on the subnet tables: the VGW (or TGW) injects the
  on-premises prefixes learned via **BGP**, so no static entries are needed.
- Static VPN needs routes entered manually on the on-premises side and VGW.

### Gateway and Interface Endpoints
- **Gateway endpoint (S3, DynamoDB):** adds a route (`prefix list → vpce-…`) to the
  tables you select — free. Without the association, traffic goes via NAT/internet.
- **Interface endpoint:** no route table involvement; an ENI with a private IP. DNS resolves
  the service name to that IP.

### Egress-only Internet Gateway
- `::/0 → eigw-…` lets IPv6 instances start connections out while blocking inbound — the
  IPv6 equivalent of a NAT gateway.

### Network Firewall / Gateway Load Balancer
- Traffic is steered **through** an inspection endpoint with route-table entries: an IGW
  edge table sends incoming traffic to the firewall subnet, and the workload table sends
  outgoing traffic to it.

### Shared VPCs (RAM)
- The VPC **owner** manages route tables; participants launch into shared subnets but
  **cannot** modify routes (see [VPC Sharing](../vpc-sharing/README.md)).

### Security Groups and NACLs
- The route table picks the next hop; the **SG** (ENI) and **NACL** (subnet) then allow or
  drop. A missing route and a blocking SG look the same from the client: a **timeout**.
- Typical debugging order: **route table → NACL → SG → OS firewall**.

## Exam Facts (SAA-C03)

- A subnet is associated with **one** route table; a table can have **many** subnets.
- **Main route table** is used by subnets with no explicit association — keep it **private**.
- The **local route cannot be deleted**.
- **Longest prefix match** decides; `0.0.0.0/0` is the default route.
- **Public subnet = route to an IGW** (plus a public IP/EIP on the instance).
- Private subnet outbound: `0.0.0.0/0 → NAT gateway` (NAT in a public subnet). IPv6 outbound:
  `::/0 → egress-only IGW`.
- Peering and VPN/DX/TGW all need **routes on every involved side**.
- VPC peering is **not transitive**; use **Transit Gateway** for hub-and-spoke.
- **Route propagation** automatically installs VPN/DX routes from a VGW.
- **Gateway endpoints** (S3, DynamoDB) work through **route table entries** — interface
  endpoints do not.
- A route table in a VPC **cannot** route to another VPC without a peering/TGW/VPN target.
- **Edge association** on an IGW/VGW route table lets you inspect inbound traffic.
- Route tables are **Regional-VPC objects**, free, and changes are **immediate**.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| Make a subnet public | Route `0.0.0.0/0 → igw` in its table (+ public IP) |
| Private instances need to download patches, no inbound | `0.0.0.0/0 → NAT gateway` in the private table |
| New subnet accidentally became public | It used a **main table with an IGW route** — keep the main table private |
| Two VPCs connected by peering still can't talk | Add routes in **both** tables (and SG/NACL) |
| A↔B and B↔C peered, A can't reach C | Peering isn't transitive → **Transit Gateway** or direct A↔C peering |
| On-premises routes must appear automatically | Enable **route propagation** (VGW) |
| Private S3 access without NAT or internet | **Gateway endpoint** + route table entry |
| IPv6 instances must reach out but not be reachable | `::/0 → egress-only IGW` |
| Force all outbound traffic through a firewall | Route `0.0.0.0/0` to the **firewall / GWLB endpoint** |
| NAT gateway deleted, private subnets lose internet | The `nat-…` route is now a **blackhole** — update it |
| Subnet in AZ-B uses a NAT in AZ-A | Cross-AZ cost + failure coupling → **one NAT and one table per AZ** |
| Which table does a subnet with no association use? | The **main** route table |

## Exam Traps

- **Routes ≠ permission.** A route to the IGW does not open anything: SG and NACL must still
  allow it, and the instance needs a public IP.
- **Main table is a trap door.** If the IGW route is in the main table, *every* unassociated
  subnet — including new ones — is public.
- **One table per subnet**, never two. Re-associating replaces the old one.
- **Both sides of a peering need routes**, not just the requester.
- **Overlapping CIDRs** can't be peered or sensibly routed.
- **Blackholes are silent.** Deleting a NAT, peering or TGW attachment leaves a stale route
  that drops traffic.
- **The local route wins in the VPC CIDR.** You can't point the VPC CIDR itself at a
  gateway; only a more specific route to an ENI / GWLB endpoint can divert intra-VPC traffic.
- **NAT gateway in a private subnet** has no internet route and does nothing.
- **Gateway endpoint ≠ interface endpoint:** only the first uses route tables.
- **Propagated routes lose to static** ones with the same prefix.
- **IPv6 is separate:** `0.0.0.0/0` doesn't cover `::/0`.

## Commands

```bash
# Tables of a VPC with their routes and associated subnets
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-0abc1234 \
  --query 'RouteTables[].{Id:RouteTableId,Main:Associations[?Main].Main|[0],Subnets:Associations[].SubnetId,Routes:Routes[].[DestinationCidrBlock,GatewayId,NatGatewayId,State]}'

# Create a custom table and add routes
aws ec2 create-route-table --vpc-id vpc-0abc1234
aws ec2 create-route --route-table-id rtb-0pub1234 \
  --destination-cidr-block 0.0.0.0/0 --gateway-id igw-0abc1234
aws ec2 create-route --route-table-id rtb-0priv1234 \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id nat-0abc1234

# Associate a subnet (replaces the current association) and replace a route
aws ec2 associate-route-table --route-table-id rtb-0pub1234 --subnet-id subnet-0abc1234
aws ec2 replace-route --route-table-id rtb-0priv1234 \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id nat-0def5678

# Peering and VGW propagation
aws ec2 create-route --route-table-id rtb-0priv1234 \
  --destination-cidr-block 10.9.0.0/16 --vpc-peering-connection-id pcx-0abc1234
aws ec2 enable-vgw-route-propagation --route-table-id rtb-0priv1234 --gateway-id vgw-0abc1234

# Find blackhole routes
aws ec2 describe-route-tables \
  --query 'RouteTables[].Routes[?State==`blackhole`]'

# Cleanup: disassociate, delete route, delete table (not the main table)
aws ec2 disassociate-route-table --association-id rtbassoc-0abc1234
aws ec2 delete-route --route-table-id rtb-0pub1234 --destination-cidr-block 0.0.0.0/0
aws ec2 delete-route-table --route-table-id rtb-0pub1234
```

## Study Checklist

- [ ] Explain main vs custom tables and why the main one should stay private.
- [ ] Say how a subnet becomes public, private with NAT, or isolated.
- [ ] Apply longest-prefix-match to a 3-route table and pick the winning route.
- [ ] List the target prefixes (`igw`, `nat`, `pcx`, `tgw`, `vgw`, `vpce`, `eigw`, `eni`).
- [ ] Describe what routes a peering, a VPN, a gateway endpoint and a NAT each need.
- [ ] Say why peering isn't transitive and what to use instead.
- [ ] Debug "can't reach X": route → NACL → SG.
- [ ] Define blackhole routes and how to spot them.

## References

- AWS docs — Route tables: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html
- AWS docs — Route priority: https://docs.aws.amazon.com/vpc/latest/userguide/route-tables-priority.html
- AWS docs — Gateway route tables: https://docs.aws.amazon.com/vpc/latest/userguide/route-table-options.html
- Related notes: [VPC overview](../README.md), [VPC Networking fundamentals](../networking/README.md), [Network ACLs](../nacl/README.md), [Security Groups](../security-groups/README.md), [Default VPC](../default-vpc/README.md), [VPC Sharing](../vpc-sharing/README.md)
