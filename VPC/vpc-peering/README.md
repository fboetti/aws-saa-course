# VPC Peering — Exam Notes

A **VPC peering connection** (`pcx-…`) is a **private, one-to-one network link between two
VPCs**. Instances talk using **private IPs** as if on the same network. Traffic stays on the
**AWS backbone** (never the public internet) and is not a gateway, VPN or separate appliance:
no single point of failure and no bandwidth bottleneck.

```
 VPC A 10.0.0.0/16 <───── pcx-123 ─────> VPC B 10.1.0.0/16
   route: 10.1.0.0/16 -> pcx-123          route: 10.0.0.0/16 -> pcx-123
```

## Scope

- **Same account or different accounts.**
- **Same Region or different Regions** (inter-Region peering; encrypted, on the AWS backbone, never the internet).
- Works for **IPv4 and IPv6**.

## How to set it up

1. **Requester** VPC creates the peering request, naming the accepter VPC ID, account and Region.
2. **Accepter** VPC owner **accepts** it (same-account requests still need acceptance; inter-Region/cross-account too). Pending requests **expire after 7 days**.
3. Add **routes in both VPCs' route tables**: destination = peer CIDR, target = `pcx-…`.
4. Open **security groups** and **NACLs** on both sides for the peer CIDR (or, same Region, the peer's SG).
5. Optional: enable **DNS resolution** over the peering so the peer's public DNS name resolves to the **private IP**.

> Peering alone does nothing: routes on **both** sides + SG/NACL rules are required. Forgetting
> the second route table is the classic failure.

## Rules and limitations (heavily tested)

| Rule | Detail |
|---|---|
| **No overlapping CIDRs** | Primary or secondary CIDR blocks must not overlap, or the peering cannot be created |
| **Not transitive** | A↔B and B↔C does **not** give A↔C. Create A↔C, or use **Transit Gateway** |
| **No edge-to-edge routing** | A cannot use B's **IGW, NAT Gateway, VPN, Direct Connect or gateway endpoint (S3/DynamoDB)** to reach outside |
| **One peering per VPC pair** | No duplicate connections between the same two VPCs |
| **Full mesh grows fast** | N VPCs fully meshed = **N(N-1)/2** connections |
| **SG referencing** | A peer's SG can be referenced as a source only in the **same Region** (not inter-Region) |
| **No fee for the connection** | Only data transfer is billed (cross-AZ and cross-Region rates); same-AZ traffic is free |
| **Subnet-level routing** | You can route only specific subnets/CIDRs via the peering, not the whole VPC |

## Peering vs the alternatives

| Need | Best choice |
|---|---|
| 2-3 VPCs, simplest and cheapest | **VPC peering** |
| Many VPCs, transitive, + on-prem | **Transit Gateway** |
| Expose one service one-way, overlapping CIDRs | **PrivateLink** |
| L7 service-to-service with IAM auth | **VPC Lattice** |
| Put many accounts into one network | **VPC sharing (RAM)** |

## Exam tips

- **"Connect two VPCs privately, lowest cost/simplest"** -> **VPC peering**.
- **"Not transitive"** appears in many questions: for a hub, answer **Transit Gateway**.
- **Overlapping CIDRs** -> peering fails; use **PrivateLink** (or Lattice, or NAT/private NAT).
- **Cross-account or cross-Region** is supported by peering.
- **Updated routes on both sides** is the fix when instances cannot reach each other over a peering.
- A peered VPC **cannot reach the internet or on-prem through the other VPC's** IGW/NAT/VPN/DX.
- **Gateway endpoint to S3** in VPC B is **not** reachable from VPC A over the peering.
- On-prem -> VPC A -> peered VPC B through a VPN/DX is **not allowed** (no edge-to-edge).
- Peering has **no bandwidth limit** of its own and no single point of failure.

## Sample questions

1. *Instances in a peered VPC cannot ping each other although the peering is active.* ->
   Missing **routes** in one/both route tables, or **SG/NACL** rules blocking the peer CIDR.
2. *VPC A is peered with B, and B is peered with C. Can A talk to C?* -> **No**, not transitive.
   Peer A with C or use Transit Gateway.
3. *A company needs private connectivity between VPCs in two accounts with overlapping
   CIDRs.* -> Peering is impossible; use **PrivateLink**.
4. *A VPC wants to use a peered VPC's NAT Gateway for internet access.* -> **Not supported**
   (no edge-to-edge routing); deploy a NAT in the VPC.
5. *50 VPCs must be connected with transitive routing.* -> **Transit Gateway** (a full mesh
   would need 1,225 peerings).

## References

- VPC peering docs: https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html
- Peering limitations: https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html
- Related notes: [VPC overview](../README.md), [Transit Gateway](../transit-gateway/README.md), [VPC Endpoints / PrivateLink](../vpc-endpoints/README.md), [VPC Lattice](../vpc-lattice/README.md), [VPC Sharing with AWS RAM](../vpc-sharing/README.md), [Route Tables](../route-tables/README.md), [Security Groups](../security-groups/README.md)
