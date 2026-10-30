# VPC Sharing with AWS RAM — Exam Notes

**AWS Resource Access Manager (AWS RAM)** is the service that lets one AWS account share
supported resources with other accounts, organizational units (OUs) or an entire AWS
Organization.

**VPC sharing** is the RAM feature that shares **subnets** from one VPC with other
accounts. The VPC itself is **never shared** — the owner keeps the VPC, subnets, route
tables, gateways and network ACLs, while participants launch their own resources into the
shared subnets.

RAM is broader than VPC sharing: it also shares resource types such as Transit Gateways,
Route 53 Resolver rules and License Manager configurations. For the exam, the VPC use
case is **subnet sharing**.

```
AWS Organization
├── Account A — VPC owner / network team
│   └── VPC 10.0.0.0/16
│       ├── subnet 10.0.1.0/24  ── RAM resource share ──> Account B
│       ├── subnet 10.0.2.0/24  ── RAM resource share ──> Account C
│       ├── route tables, NACLs, IGW, NAT, TGW attachment  (owner-managed)
│       └── VPC endpoints, flow logs, DHCP options          (owner-managed)
│
├── Account B — participant
│   └── EC2, RDS, Lambda, ELB ... launched into Account A's shared subnet
│
└── Account C — participant
    └── its own resources in the same shared VPC
```

Participants do **not** get their own copy of the VPC. They see Account A's VPC and
subnets in their VPC console, marked with the owner's account ID. Resources from
different accounts share the same VPC network and implicit `local` routing.

### Mental model: two planes, two owners

VPC sharing separates **who owns the network** from **who owns what runs on it**:

| Plane | Owned by | Contains |
|---|---|---|
| **Network plane** | VPC owner | VPC, subnets, CIDRs, route tables, NACLs, IGW, NAT, TGW attachment, endpoints, flow logs on subnets |
| **Workload plane** | Each participant | Instances, databases, functions, load balancers, **their** ENIs and security groups |

Consequences that explain almost every exam question:

- **Routing is shared, filtering is per account.** Everything in the VPC can route to
  everything else through `local`; isolation between participants comes only from
  **security groups**, **NACLs** (owner-managed) and **subnet placement**.
- **Cross-account SG referencing works** inside a shared VPC: a participant's SG rule can
  allow traffic from `111122223333/sg-0abc…` in another account.
- **IAM and billing stay per account** — that is the "account isolation" half of the
  benefit; the network is the "centralized" half.
- Compared with **peering/TGW**, there is nothing to connect: the accounts are already in
  the same VPC, so there are no extra routes, attachments or per-GB TGW charges.

## Why Use VPC Sharing?

- **Centralized network management** — a network/security team owns the VPC, CIDR plan,
  route tables, NAT, IGW, endpoints and NACLs. Application teams deploy into shared
  subnets without managing the network.
- **Fewer VPCs** — instead of one VPC per account, many accounts use the same VPC. This
  reduces VPC sprawl and CIDR-overlap problems.
- **Cost sharing** — the owner runs shared NAT gateways, interface endpoints, Transit
  Gateway attachments and public IPv4 addresses; participants avoid duplicating them.
- **Account isolation with shared networking** — each account keeps its own IAM, billing,
  budgets and resource ownership, while using the same network.
- **High interconnectivity** — resources in the same VPC can talk to each other through
  the `local` route without peering, TGW or extra routes.

> VPC sharing is intended for accounts **inside the same trust boundary**. If you need
> strong isolation between business units, use separate VPCs with peering, Transit
> Gateway or PrivateLink instead.

## Design Best Practices

- **Use dedicated subnets per participant** (usually one per AZ) instead of putting every
  account in the same subnet. This limits the blast radius and prevents one account from
  exhausting all free IPs.
- Keep **shared infrastructure subnets** for NAT gateways, interface endpoints, firewalls
  and other central services **unshared** and owner-only.
- Use **AZ IDs**, not AZ names, when coordinating placement across accounts.
- Use separate accounts for **billing and IAM isolation**, and the shared VPC for
  **network centralization**.
- Restrict who can create resource shares with **SCPs** (see Governance below).
- Not every AWS service supports shared subnets. EC2, RDS/Aurora, Lambda, ECS/EKS, ELB,
  Redshift, EMR, OpenSearch, EFS and MSK are supported; check the current list before
  designing around a less common service.

## Governance and Security

- Enabling RAM sharing is an **organization-level** decision. Once enabled, any account
  with the right RAM permissions may be able to create shares unless you restrict it.
- Use **SCPs** to allow only the network account to call `ram:CreateResourceShare` and
  `ram:AssociateResourceShare`, or deny `ram:*` in accounts that should never share.
- Participants' **IAM policies and SCPs still apply** to the resources they launch.
- Sharing is for the **same trust boundary**. A shared subnet is not a security boundary
  between participants — use security groups, NACLs, separate subnets or separate VPCs
  when you need isolation.
- The VPC owner can see participant ENIs and security groups but cannot modify them;
  participants cannot see each other's resources.

### What sharing does and does not expose

Sharing a subnet does **not** share the resources living in it. Each account sees only
its own workload plane, plus the owner's network plane:

| Resource | Owner sees | Participant sees |
|---|---|---|
| Shared subnets / VPC | Yes (owns them) | Yes (marked with owner's account ID) |
| **Security groups** | Own SGs **and** participants' SGs (read-only) | Own SGs only — never the owner's, unless the owner shares them via RAM |
| **EC2 instances** | Own only — participants' instances are **not** visible or manageable | Own only — not the owner's, not other participants' |
| ENIs | Own **and** participants' ENIs (read-only) | Own only |

- Visibility comes from **account ownership of the resource**, not from a cross-account
  IAM role. The owner needs no role in the participant account to see its ENIs and SGs;
  and assuming a role in a participant account gives you that account's view, not an
  extended view of the shared VPC.
- To act on a participant's instances, the owner would need real access to that account
  (e.g. a cross-account role) — VPC sharing itself grants none.

## Prerequisites

| Requirement | Detail |
|---|---|
| **Same AWS Organization** | Owner and participants must be accounts in the **same AWS Organization** |
| **RAM sharing enabled** | Enable resource sharing with AWS Organizations — this must be done from the **organization management account** |
| **Resource share** | The owner creates a RAM resource share containing the subnet ARNs |
| **Same region** | The subnets and the resource share must be in the **same region** |
| **Non-default subnets** | You **cannot share subnets in a default VPC** |
| **Owner account** | Only the VPC owner can share the subnets |
| **Permissions** | Participants still need IAM permissions; their SCPs and IAM policies still apply |

VPC subnet sharing **does not support accounts outside your organization**. AWS RAM can
share some other resource types with external accounts via an invitation, but **VPC
subnets are organization-only**.

## How It Works

1. The **owner** creates the VPC, subnets and shared network services (IGW, NAT, route
   tables, NACLs, endpoints, TGW attachment).
2. The **owner** creates an AWS RAM **resource share**, adds one or more **subnet ARNs**,
   and selects the principals (accounts, OUs or the whole organization).
3. **Participants** see the shared subnets in the VPC console and launch resources into
   them.
4. The **owner** keeps managing the network; participants manage **their own** resources.
5. The **owner** can unshare a subnet at any time.

There is **no transitive sharing**: a participant cannot re-share a subnet that was
shared with it.

## Owner vs Participant Permissions

| Capability | VPC owner | Participant |
|---|---|---|
| Create/modify VPC, subnets, route tables, NACLs, IGW, NAT, TGW attachments | **Yes** | **No** (describe only) |
| Create security groups | Yes | **Yes** — their own SGs |
| Use the VPC's **default security group** | Yes | **No** — it belongs to the owner |
| Use a non-default SG owned by the owner | Yes | Only if the owner **shares the SG via RAM** |
| Create ENIs | Yes | **Yes** — their own ENIs |
| Create VPC Flow Logs | Subnet and any ENI | **Only ENIs they own** |
| Create/describe/modify/delete VPC endpoints | **Yes** | **No** — even describe is denied |
| Launch EC2/RDS/Redshift/Lambda/ELB/etc. | Yes | **Yes** |
| View/modify another account's resources | Owner sees participant ENIs/SGs but cannot modify them | **No** |
| Delete the shared subnet or VPC | Only after participants remove their resources | **No** |
| Re-share the subnet | N/A | **No** |
| See VPC/resource tags | Yes | **No** — tags are not shared |

Additional participant restrictions from the AWS docs:

- Cannot create, delete **or describe** NAT gateways in the shared subnet.
- Cannot create, attach or delete internet gateways / egress-only internet gateways.
- Cannot create, delete or replace network ACLs.
- Cannot create, delete or associate route tables.
- Cannot attach a Transit Gateway to the shared VPC — only the owner can.
- Cannot modify the shared subnet or VPC attributes.
- Cannot **create, describe, modify or delete VPC endpoints** in subnets shared with
  them — only AWS service-managed endpoints can appear in a shared subnet.
- Can create security groups and reference other security groups by
  `account-number/security-group-id`.
- Can create flow logs for **its own ENIs**, but not for the shared subnet.

## Billing: Who Pays for What?

This split is a favourite exam question.

| Cost | Who pays |
|---|---|
| **NAT gateway** hourly + data processing | **VPC owner** |
| **Transit Gateway** attachment + data processing | **VPC owner** |
| **Virtual private gateway**, **VPC endpoints** (gateway and interface) and **AWS PrivateLink** | **VPC owner** |
| **Public IPv4 addresses** used in the shared VPC | **VPC owner** |
| **EC2, RDS, Redshift, Lambda** and other participant resources | **Participant** |
| Participant **inter-AZ data transfer**, peering, IGW and DX gateway data transfer | **Participant** |
| Data transfer **within the same AZ** | **Free**, regardless of account ownership |
| **AWS RAM itself** | **Free** — no charge for resource shares |

## Quotas

| Quota | Default | Adjustable |
|---|---|---|
| Participant accounts per VPC | **100** | Yes |
| Subnets shared with one account | **100** | Yes |
| Standard VPC quotas (5 VPCs, 200 subnets, etc.) | Apply normally | Yes |
| Elastic IPs per region | **5** | Yes — applies to shared VPCs too |

- Participant resources count against the **participant's** quotas, not the owner's.
- The shared VPC and subnets count against the **owner's** VPC/subnet quotas.

## VPC Sharing vs Peering vs Transit Gateway vs PrivateLink

| Requirement | Best fit |
|---|---|
| Multiple accounts must place resources in the **same VPC/subnets** | **VPC sharing (AWS RAM)** |
| Central network team owns the network, app teams own their resources | **VPC sharing (AWS RAM)** |
| Two **separate VPCs** need private connectivity | **VPC peering** |
| Many VPCs + on-premises need any-to-any routing | **Transit Gateway** |
| Expose one service privately to other VPCs/accounts | **PrivateLink** |
| Share the VPC object itself | **Not possible** — share subnets |
| Share subnets across regions | **Not possible** — use peering/TGW |
| Share subnets with an account outside your organization | **Not supported** for VPC sharing |
| Isolate untrusted business units | **Separate VPCs**, not shared subnets |

Key distinction: **RAM sharing is not connectivity.** Peering and TGW connect separate
VPCs; VPC sharing puts resources from multiple accounts into **one** VPC.

## Exam Facts (SAA-C03)

| Fact | Detail |
|---|---|
| **Service** | AWS Resource Access Manager (AWS RAM) |
| **What is shared** | **Subnets**, not the VPC |
| **Who can participate** | Accounts in the **same AWS Organization** |
| **Region scope** | **Same region** as the subnets |
| **Default VPC** | Its subnets **cannot** be shared |
| **Transitive sharing** | **No** — participants cannot re-share |
| **Network control** | **Owner** owns VPC, subnets, routes, NACLs, IGW, NAT, TGW attachment |
| **Resource ownership** | **Participant** owns its EC2/RDS/Lambda/etc. |
| **Billing** | Owner pays network infrastructure/public IPv4; participant pays its resources and data transfer |
| **Revocation** | Existing participant resources keep running; no new resources can be created |
| **AZ mapping** | Use **AZ IDs**, not AZ names, across accounts |
| **Security groups** | Participants create their own; owner SGs only if shared via RAM; default SG cannot be used by participants |
| **VPC endpoints** | Owner-managed; participants cannot create, describe, modify or delete them |
| **Tags** | Not shared with participants |
| **Cost of RAM** | **Free** |
| **Quotas** | 100 participant accounts per VPC, 100 subnets per account |

## Commands

```bash
# 1. Organization management account only: enable sharing in Organizations
aws ram enable-sharing-with-aws-organization --region eu-north-1

# 2. Owner: create a resource share with one subnet and one participant account
OWNER=111122223333
REGION=eu-north-1
SUBNET_ARN="arn:aws:ec2:$REGION:$OWNER:subnet/subnet-0123456789abcdef0"

aws ram create-resource-share \
  --name shared-prod-subnets \
  --resource-arns "$SUBNET_ARN" \
  --principals 444455556666 \
  --region "$REGION"

# Share with an OU or the whole organization instead of one account:
#   --principals arn:aws:organizations::111122223333:ou/o-abc123/ou-abcd-12345678
#   --principals arn:aws:organizations::111122223333:organization/o-abc123

# 3. Owner: add another subnet to an existing resource share
aws ram associate-resource-share \
  --resource-share-arn arn:aws:ram:eu-north-1:111122223333:resource-share/rs-0123456789abcdef0 \
  --resource-arns "arn:aws:ec2:$REGION:$OWNER:subnet/subnet-..." \
  --region "$REGION"

# 4. Participant: find shares and shared subnets
aws ram get-resource-shares \
  --resource-owner OTHER-ACCOUNTS \
  --region eu-north-1

aws ec2 describe-subnets \
  --region eu-north-1 \
  --query "Subnets[].[SubnetId,OwnerId,VpcId,CidrBlock,AvailabilityZone]" \
  --output table

# 5. Owner: see principals and resources in the share
aws ram list-principals \
  --resource-owner SELF \
  --resource-share-arns arn:aws:ram:eu-north-1:111122223333:resource-share/rs-... \
  --region eu-north-1

aws ram list-resources \
  --resource-owner SELF \
  --resource-share-arns arn:aws:ram:eu-north-1:111122223333:resource-share/rs-... \
  --region eu-north-1

# 6. Owner: unshare a subnet
aws ram disassociate-resource-share \
  --resource-share-arn arn:aws:ram:eu-north-1:111122223333:resource-share/rs-... \
  --resource-arns "$SUBNET_ARN" \
  --region eu-north-1
```

> The resource share is **regional**. For subnets in three regions, create three
> resource shares (or use one share per region).

## Exam Scenarios

| Requirement | Answer |
|---|---|
| A central network account owns the VPC; 40 application accounts must deploy into it | **VPC sharing via AWS RAM** |
| Reduce duplicate NAT gateway and interface-endpoint costs across accounts | **Share subnets**; owner runs shared NAT/endpoints |
| Applications need implicit same-VPC routing and high interconnectivity | **VPC sharing** |
| Two separate VPCs with non-overlapping CIDRs need private connectivity | **VPC peering** |
| 30 VPCs and on-premises need any-to-any routing | **Transit Gateway** |
| Share subnets with an account outside the AWS Organization | **Not supported** for VPC sharing |
| Share the same subnets with accounts in three regions | **Not possible** — share per region or use peering/TGW |
| Share subnets from the default VPC | **Not possible** — create a custom VPC |
| Participant wants to change a route table or NACL | **Cannot** — the VPC owner manages the network |
| Participant wants to use the owner's security group | Owner must **share the SG via RAM**, or participant creates its own |
| Participant needs internet egress | Owner provides the **NAT/IGW route**; participant cannot create a NAT gateway |
| Participant needs a private S3 endpoint | **Owner creates the VPC endpoint**; participants cannot |
| Owner unshares a subnet while participant resources are running | Resources **keep running**; no new resources; owner cannot delete the subnet until they are gone |
| Owner wants to delete the shared VPC | Participants must delete their resources first |
| Who pays for public IPv4 addresses in the shared VPC? | **The VPC owner** |
| Who pays for the participant's EC2 instances? | **The participant** |
| How do accounts agree on which AZ is which? | Compare **AZ IDs** (`use1-az1`), not AZ names |

## Exam Traps

- **"VPC sharing" shares subnets, not the VPC.** You cannot share a VPC object, and
  participants cannot modify the VPC.
- **Same organization only.** VPC subnet sharing does not work with external accounts.
- **Same region only.** A resource share cannot contain subnets from another region.
- **No default VPC subnets.** You cannot share subnets in a default VPC.
- **No transitive sharing.** A participant cannot re-share a subnet shared with it.
- **Sharing is not peering.** Peering/TGW connect separate VPCs; RAM puts resources into
  one VPC.
- **Owner keeps network control.** Participants cannot create or modify route tables,
  NACLs, IGWs, NAT gateways or TGW attachments.
- **Participants can create SGs and ENIs**, and can create flow logs for their own ENIs,
  but not for the shared subnet.
- **The default SG belongs to the owner.** Participants cannot launch instances with it.
- **VPC endpoints are owner-managed.** Participants cannot create, describe, modify or
  delete them in a shared subnet.
- **Owner SGs are not automatically usable.** They must be shared via RAM; otherwise the
  participant creates its own SG.
- **Billing is split.** Owner pays NAT/TGW/endpoints/public IPv4; participants pay their
  instances and their data transfer.
- **Unsharing does not terminate resources.** Existing participant resources continue to
  run; new launches are blocked; the owner cannot delete the subnet until the resources
  are gone.
- **Tags are not shared.** Participants do not see the VPC's tags or the tags on the
  owner's resources.
- **AZ names are account-specific.** Use AZ IDs when coordinating placement across
  accounts.
- **RAM is free**, but the resources and data transfer are not.
- **Resource shares are regional.** Do not assume one share covers every region.
- **Participant resources count against participant quotas**, including security groups
  and ENIs.
- **VPC sharing is for the same trust boundary.** For isolation, use separate VPCs and
  private connectivity.

## Study Checklist

- [ ] Explain the difference between AWS RAM, VPC sharing, VPC peering and Transit
      Gateway.
- [ ] State the prerequisites: same organization, same region, RAM enabled, resource
      share.
- [ ] Draw the owner/participant model and say who owns which resources.
- [ ] List what participants **can** create and what they **cannot** modify.
- [ ] Explain why participants cannot create NAT gateways or VPC endpoints.
- [ ] Explain the billing split between owner and participant.
- [ ] Explain what happens when the owner unshares a subnet with running resources.
- [ ] Explain why default VPC subnets cannot be shared.
- [ ] Explain why AZ IDs matter across accounts.
- [ ] Recite the two main quotas: 100 participant accounts per VPC and 100 subnets per
      account.

## References

- AWS docs — Share your VPC subnets with other accounts: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-sharing.html
- AWS docs — Shared subnet prerequisites: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-share-prerequisites.html
- AWS docs — Owner and participant permissions: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-share-limitations.html
- AWS docs — Billing for shared subnets: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-share-billing.html
- AWS docs — Working with shared subnets: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-sharing-share-subnet-working-with.html
- AWS docs — Services that support shared subnets: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-sharing-service-behavior.html
- AWS docs — What is AWS RAM: https://docs.aws.amazon.com/ram/latest/userguide/what-is.html
- AWS docs — VPC quotas (subnet sharing): https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html
- Related notes: [VPC overview](../README.md), [Default VPC](../default-vpc/README.md), [VPC networking](../networking/README.md), [Availability Zones](../../concepts/availability-zones/README.md)
