# Default VPC — Exam Notes

The **default VPC** is the VPC AWS builds for you in every region so you can launch
internet-reachable resources without designing a network first. It is not a special kind
of VPC — it is a normal VPC with the `IsDefault` flag set to `true` and a pre-built set
of subnets, routes and gateways.

```
Region eu-north-1
└── default VPC  172.31.0.0/16              IsDefault = true
    ├── default subnet  172.31.0.0/20       AZ #1   public, auto-assign public IPv4
    ├── default subnet  172.31.16.0/20      AZ #2   public, auto-assign public IPv4
    ├── default subnet  172.31.32.0/20      AZ #3   public, auto-assign public IPv4
    ├── internet gateway (attached)
    ├── main route table
    │   ├── 172.31.0.0/16 -> local
    │   └── 0.0.0.0/0     -> igw-...
    ├── default security group  (same-SG inbound, all outbound)
    ├── default network ACL     (allow all)
    └── default DHCP options set
```

The CIDR-to-AZ mapping is account-specific; the order above is only an example.

## What AWS Creates

When AWS creates a default VPC, it creates **all of the following** for you:

| Component | What you get |
|---|---|
| **VPC** | `172.31.0.0/16` (65,536 IPv4 addresses), `IsDefault = true` |
| **Default subnets** | One **/20** subnet in each Availability Zone — `172.31.0.0/20`, `172.31.16.0/20`, `172.31.32.0/20`, … |
| **Internet gateway** | Created and **attached** to the VPC |
| **Main route table** | `172.31.0.0/16 -> local` and `0.0.0.0/0 -> internet gateway` |
| **Default security group** | Inbound from **the same security group**, all outbound allowed |
| **Default network ACL** | Allows **all** inbound and outbound traffic |
| **DHCP options** | The account's **default DHCP options set** is associated |
| **DNS** | DNS resolution and DNS hostnames are enabled |

Each default subnet:

- is **`DefaultForAz = true`**,
- is **`MapPublicIpOnLaunch = true`** (instances get a public IPv4 automatically),
- has **4,091 usable IPs** after the 5 reserved addresses,
- is **public** because it uses the main route table with `0.0.0.0/0 -> igw`.

> The default VPC is **IPv4-only when created**. It has **no IPv6 CIDR**, no NAT
> gateway, no private subnet, no VPN, no peering and no VPC endpoints. You can add
> those later, but they are not part of the default setup.

### Reading the design

Every design choice in the default VPC optimizes for **"works on the first try"**, and
each one is a trade-off you would usually reverse in production:

| Choice | Why it helps a beginner | Why production avoids it |
|---|---|---|
| `172.31.0.0/16` — the largest allowed block, inside RFC 1918 `172.16.0.0/12` | Never runs out of addresses | Same CIDR in **every account and region** → peering, VPN and TGW overlap |
| One `/20` per AZ, all in the main route table | Any AZ works, multi-AZ placement is trivial | No public/private split, no tiering |
| `0.0.0.0/0 -> igw` in the **main** table | Every subnet, even a new one, is public | A forgotten subnet is internet-routable by default |
| `MapPublicIpOnLaunch = true` | Instances are reachable without extra steps | Every instance gets a (billed) public IPv4 |
| Default NACL allows all | No stateless-rule surprises | No subnet-level guardrail |
| Default SG: same-SG inbound only | Safe-ish starting point | Still needs explicit rules; easy to over-open |

## Why Does It Exist?

The default VPC is an **onboarding and convenience feature**, not a production
reference architecture. It exists so that a new account can:

1. **Launch an EC2 instance immediately** with a public IP and working internet access —
   no VPC, subnet, route table, IGW or DNS setup required.
2. **Use services that expect a VPC and subnets** without building one first — the AWS
   docs explicitly mention **Elastic Load Balancing, Amazon RDS and Amazon EMR**.
3. **Run simple public workloads** such as a blog or a basic website.
4. **Migrate away from EC2-Classic** — the default VPC was the easy path from the old
   flat EC2-Classic network to VPC networking. EC2-Classic was retired in 2022–2023,
   but the default VPC remains as the "just works" starting point.

Exam framing: the default VPC is the answer when the question says **"get started
quickly"**, **"launch a public instance with minimal setup"** or **"no networking
configuration"**. It is **not** the answer for a secure, isolated, production-grade
multi-tier design.

## Default VPC vs Custom VPC

| | **Default VPC** | **Custom VPC** |
|---|---|---|
| Created | Automatically, one per region | By you |
| CIDR | Fixed `172.31.0.0/16` | You choose `/16`–`/28` |
| Subnets | One `/20` per AZ, public by default | None — you design them |
| Internet gateway | Already attached | You create and attach it |
| Default route | `0.0.0.0/0 -> IGW` already present | You add it |
| DNS support (`enableDnsSupport`) | **Enabled** | **Enabled** by default |
| DNS hostnames (`enableDnsHostnames`) | **Enabled** | **Disabled** by default |
| Auto-assign public IPv4 | **Enabled** on default subnets | Your choice per subnet |
| Default SG / NACL | Present (same as any VPC) | Present (same as any VPC) |
| `IsDefault` flag | `true` | `false` — **cannot be promoted** |
| Typical use | Labs, tutorials, quick public instances | Production, private subnets, compliance |

> Every VPC — default or custom — comes with a **default security group**, a
> **default network ACL** and a **main route table**. Those are not unique to the
> default VPC. The difference is the pre-built **subnets, IGW, route and public-IP
> settings**.

## Exam Facts (SAA-C03)

| Fact | Detail |
|---|---|
| **Scope** | One default VPC **per region per account**; it does not span regions |
| **CIDR** | Always **`172.31.0.0/16`** |
| **Subnets** | One **`/20`** default subnet **per AZ** |
| **Routing** | Main route table sends **`0.0.0.0/0` to the IGW** |
| **Public IPs** | Default subnets **auto-assign public IPv4** |
| **DNS** | `enableDnsSupport` and `enableDnsHostnames` are **on** |
| **Quota** | Counts toward the **5 VPCs per region** default quota |
| **Cost** | The default VPC itself is **free**; resources and public IPv4 addresses are billed |
| **Deletion** | You **can** delete it, but dependencies must be removed first |
| **Restore** | You **cannot restore** the old default VPC; you can only create a new one |
| **Recreation** | `aws ec2 create-default-vpc` — **no parameters** |
| **Promotion** | You **cannot mark a custom VPC as default** |
| **Second default VPC** | **Not allowed** in the same region |
| **Default subnets** | You can delete them and recreate them individually with `create-default-subnet` |
| **IPv6** | Not included at creation; attach an IPv6 CIDR later if needed |

### Numbers worth memorizing

- `172.31.0.0/16` — the default VPC CIDR.
- `/20` — the size of each default subnet.
- **4,091** — usable IPs in a default subnet (`4,096 - 5 reserved`).
- **5** — default VPC quota per region; the default VPC counts as one.
- **3** — typical number of AZs (and therefore default subnets) in a region.

## Commands

### Find the default VPC

```bash
# Current region: is there a default VPC?
aws ec2 describe-vpcs \
  --filters Name=is-default,Values=true \
  --query "Vpcs[].[VpcId,CidrBlock,IsDefault]" \
  --output table

# Same check in every region (None = no default VPC in that region)
for region in $(aws ec2 describe-regions --query "Regions[].RegionName" --output text); do
  printf '%-20s ' "$region"
  aws ec2 describe-vpcs \
    --region "$region" \
    --filters Name=is-default,Values=true \
    --query "Vpcs[0].VpcId" \
    --output text
done
```

### Inspect its components

```bash
VPC_ID=$(aws ec2 describe-vpcs \
  --filters Name=is-default,Values=true \
  --query "Vpcs[0].VpcId" --output text)

# Default subnets: one per AZ, public IP auto-assign on
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone,DefaultForAz,MapPublicIpOnLaunch]" \
  --output table

# Main route table: local + 0.0.0.0/0 -> igw
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "RouteTables[].[RouteTableId,Routes[].[DestinationCidrBlock,GatewayId]]" \
  --output json

# IGW attached to the VPC
aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --query "InternetGateways[].[InternetGatewayId,Attachments[0].State]" \
  --output table

# DNS attributes
aws ec2 describe-vpc-attribute --vpc-id "$VPC_ID" --attribute enableDnsHostnames
aws ec2 describe-vpc-attribute --vpc-id "$VPC_ID" --attribute enableDnsSupport
```

### Recreate the default VPC

The whole command is:

```bash
aws ec2 create-default-vpc --region eu-north-1
```

Example output:

```json
{
  "Vpc": {
    "VpcId": "vpc-0123456789abcdef0",
    "CidrBlock": "172.31.0.0/16",
    "IsDefault": true,
    "State": "pending"
  }
}
```

Rules for recreation:

- It works **only if the region has no default VPC**.
- It takes **no CIDR, subnet, AZ or tag parameters** — AWS decides everything.
- It always uses **`172.31.0.0/16`** and creates a **`/20` subnet per AZ**.
- It creates a **new VPC ID and new subnet IDs**; it does **not** restore instances,
  data, load balancers, EIP associations or anything else you had inside the old one.
- The new default subnets **may map to different AZs** than the old ones (e.g. the
  `172.31.0.0/20` subnet may move from `eu-north-1a` to `eu-north-1b`).
- If a default VPC already exists, the call fails — there can be only one per region.
- You can check permissions without creating anything with `--dry-run`.

Safe "create only if missing" snippet:

```bash
REGION=eu-north-1

COUNT=$(aws ec2 describe-vpcs \
  --region "$REGION" \
  --filters Name=is-default,Values=true \
  --query "length(Vpcs)" --output text)

if [ "$COUNT" -eq 0 ]; then
  aws ec2 create-default-vpc --region "$REGION"
else
  echo "A default VPC already exists in $REGION; not recreating."
fi
```

Console equivalent: **VPC console → Your VPCs → Actions → Create default VPC**.

### Recreate a single default subnet

If only one default subnet was deleted, you do not need to rebuild the whole VPC:

```bash
aws ec2 create-default-subnet \
  --availability-zone eu-north-1a \
  --region eu-north-1
```

Rules:

- It creates a **`/20`** in the **next available contiguous space** of the default VPC.
- You **cannot choose the CIDR**.
- There can be **only one default subnet per AZ**.
- It can only be created in the **default VPC**, not a custom one.
- A **new AZ added to a region later** may not get a default subnet automatically.
- If there is not enough space left in the VPC, the call fails; add a secondary CIDR
  first.

### Delete the default VPC

There is **no `delete-default-vpc` command**. It is deleted like any other VPC with
`delete-vpc`, after its dependencies are removed:

```bash
# High-level order — do not run blindly:
# 1. terminate instances / delete load balancers, NAT gateways, endpoints, etc.
# 2. detach and delete the internet gateway
# 3. delete the default subnets
# 4. delete the VPC
aws ec2 delete-vpc --vpc-id "$VPC_ID" --region eu-north-1

# 5. recreate the default VPC if you still need it
aws ec2 create-default-vpc --region eu-north-1
```

You do **not** need to delete the **default security group**, **main route table** or
**default network ACL** — AWS removes them with the VPC. You **do** need to remove
resources that hold ENIs (instances, load balancers, NAT gateways, interface endpoints)
and detach/delete the IGW first.

> Destructive action: deleting the default VPC removes the network and every resource
> still inside it. Dependent resources (instances, load balancers, subnets, etc.) must
> be deleted first; the console shows the dependency list before deletion. Prefer the
> console for the delete step if you are unsure.

## Exam Scenarios

| Requirement | Answer |
|---|---|
| Launch a public EC2 instance immediately with no VPC setup | Use the **default VPC** and one of its default subnets |
| A default VPC was deleted in a region — restore it exactly as before | **Not possible**; `create-default-vpc` builds a **new** VPC with new IDs/AZ mapping |
| Only one default subnet was deleted | `aws ec2 create-default-subnet --availability-zone <az>` |
| The company wants its custom VPC to become the default VPC | **Not possible** — the default flag cannot be moved |
| Create a second default VPC in the same region | **Not possible** — one per region |
| The default VPC has no private subnets or NAT gateway | **Add** private subnets + NAT, or build a custom VPC |
| Production workload must be isolated and not publicly reachable | Use a **custom VPC** with private subnets, NAT/endpoints and least-privilege SGs |
| Security baseline: remove default VPCs from every region | Delete the default VPC per region; deny recreation with an SCP on `ec2:CreateDefaultVpc` |
| Why do RDS/ELB resources show `172.31.0.0/16`? | They were created in the **default VPC** |
| Cannot delete the default VPC | It still has **dependent resources** (ENIs, instances, LBs, NAT, endpoints) or an attached IGW |
| Need IPv6 in the default VPC | Associate an **IPv6 CIDR** with the VPC; it is not there at creation |
| Stop default subnets from auto-assigning public IPs | Modify the subnet attribute `map-public-ip-on-launch` to `false` |
| Default VPC overlaps an on-premises/peered network | Its primary CIDR is fixed `172.31.0.0/16`; use a **custom VPC** with a non-overlapping CIDR |

## Exam Traps

- **Default VPC ≠ default subnet ≠ default SG ≠ default NACL.** You can delete a
  default subnet and the VPC is still the default VPC. Every VPC has a default SG and
  a default NACL, not just the default VPC.
- **The default VPC is public by default, but the default SG is not open to the
  internet.** Its inbound rule only allows traffic from **resources in the same SG**.
  You still need an SG rule that allows internet traffic (and a public IP + IGW route)
  before an instance is reachable from outside.
- **Auto-assign public IPv4 alone does not make a subnet public.** The subnet still
  needs a route table with `0.0.0.0/0 -> igw`.
- **The default VPC is not highly available just because it has subnets in every AZ.**
  An application is only multi-AZ if you actually place resources in multiple AZs and
  put a load balancer in front.
- **The default VPC has no NAT gateway and no private subnet.** All default subnets are
  public. For private workloads, add subnets/NAT or use a custom VPC.
- **The default VPC is free; deleting it saves nothing by itself.** You pay for
  instances, public IPv4 addresses, EIPs, data transfer, etc.
- **Recreating does not restore the old VPC.** New VPC ID, new subnet IDs, possibly
  different AZ mapping, and no data.
- **You cannot create a default VPC with your own CIDR or choose its subnets.**
  `create-default-vpc` has no input parameters.
- **You cannot promote a custom VPC to default**, and you cannot have two default VPCs
  in one region.
- **`create-default-subnet` cannot pick a CIDR** and cannot be used in a custom VPC.
- **Deleting the default VPC does not delete custom VPCs** or default VPCs in other
  regions.
- **Each account has its own default VPC per region**; an AWS Organization does not
  share one.
- **The default VPC counts against the 5-VPC regional quota.** If you are at the limit,
  recreating it needs a free slot.
- **The default VPC's primary CIDR cannot be changed**, which is why `172.31.0.0/16`
  often breaks peering with corporate networks. You can add secondary CIDRs, but the
  primary stays.
- **Some landing zones remove it.** AWS Control Tower Account Factory can delete the
  default VPC in governed regions (or create accounts without one). The standard exam
  model still assumes one default VPC per region unless it has been removed.
- **IAM nuance:** the components created by `CreateDefaultVpc` are created by AWS on
  your behalf. Denying `ec2:CreateInternetGateway` does not stop the default VPC's IGW
  from being created; deny `ec2:CreateDefaultVpc` if you want to block recreation.
- **IaC nuance:** CloudFormation cannot create a *default* VPC (there is no `IsDefault`
  input); Terraform's `aws_default_vpc` can adopt an existing one or create it. Treat
  the default VPC as an account baseline rather than a normal IaC resource.

## Study Checklist

- [ ] Draw the default VPC from memory: CIDR, `/20` per AZ, IGW, main route, default
      SG/NACL, DNS, public IP setting.
- [ ] Say why it exists and name three services that can use it.
- [ ] Recite `aws ec2 create-default-vpc` and explain why it has no parameters.
- [ ] Explain the difference between recreating a **default VPC** and a **default
      subnet**.
- [ ] Explain why a deleted default VPC cannot be restored exactly.
- [ ] Explain why the default VPC is not a production/security baseline.
- [ ] List the dependencies that prevent deleting a VPC.
- [ ] Explain what happens to `172.31.0.0/16` if it overlaps an on-premises network.
- [ ] Know that default SG/NACL/main route table exist in **every** VPC.

## References

- AWS docs — Default VPCs: https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html
- AWS docs — Default VPC components: https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc-components.html
- AWS docs — Work with your default VPC and default subnets: https://docs.aws.amazon.com/vpc/latest/userguide/work-with-default-vpc.html
- AWS CLI — `create-default-vpc`: https://docs.aws.amazon.com/cli/latest/reference/ec2/create-default-vpc.html
- AWS CLI — `create-default-subnet`: https://docs.aws.amazon.com/cli/latest/reference/ec2/create-default-subnet.html
- AWS docs — Delete a VPC: https://docs.aws.amazon.com/vpc/latest/userguide/delete-vpc.html
- Related notes: [VPC overview](../README.md), [VPC networking](../networking/README.md), [Availability Zones](../../concepts/availability-zones/README.md), [Resilience patterns](../../concepts/resilience/README.md)
