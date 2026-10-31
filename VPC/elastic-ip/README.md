# Elastic IP (EIP) — Exam Notes

An **Elastic IP** is a **static public IPv4 address** allocated to your AWS account. It
stays yours until you release it and can be remapped between instances or network
interfaces, so the public address no longer depends on a single instance.

## Quick Facts

| Property | Behaviour |
|---|---|
| **Type** | Public **IPv4** only (IPv6 addresses are already static and public) |
| **Scope** | **Regional** — usable on any ENI in the Region, not across Regions |
| **Ownership** | Yours until **released**; survives instance **stop/start** and termination |
| **Attached to** | An **ENI** (usually via an instance); one EIP per **private IP** of the ENI |
| **Remapping** | Move it to another instance/ENI in seconds → fast failover without DNS changes |
| **Source** | Amazon's pool, your own range (**BYOIP**) or a customer-owned pool (Outposts) |
| **Default quota** | **5 per Region** (adjustable) |
| **Cost** | Billed **hourly like every public IPv4**, whether attached or not (idle ones included) |

## IPv6: No Elastic IPs Needed

EIPs are an **IPv4-only** concept, because public IPv4 addresses are scarce and an
instance's public address is mapped (1:1 NAT by the IGW) to its private one.

- Every IPv6 address in a VPC is **globally unique and public** (Amazon gives the VPC a
  /56, each subnet a /64), so an instance **already has a public address** without any
  NAT or mapping.
- An IPv6 address **stays with the ENI** (it survives stop/start) — it behaves like an
  always-static address, so there is nothing to allocate, associate or release.
- No per-address charge, no 5-per-Region quota.
- Whether the address is reachable is decided by **routing and filtering**, not by the
  address itself: `::/0 → igw` for two-way access, `::/0 → egress-only IGW` for
  outbound-only, plus SG/NACL rules for IPv6.
- For a **fixed IPv6 for failover**, move the ENI (or use your own IPv6 range via BYOIP).

### AWS support for IPv6

- **Dual-stack model:** a VPC always keeps its IPv4 CIDR and can add an IPv6 one (**/56**,
  Amazon-provided or BYOIP); each subnet gets a **/64**. Subnets can be **dual-stack** or
  **IPv6-only**.
- **Network layer:** IPv6 has its own routes (`::/0`) and its own SG and NACL rules.
  Internet access goes through the **IGW** (two-way) or the **egress-only IGW** (outbound
  only). **NAT Gateway is IPv4-only**; **NAT64/DNS64** lets IPv6-only workloads reach IPv4
  services.
- **Services:** EC2, ALB/NLB, CloudFront, Route 53 (`AAAA` records), S3, VPC endpoints,
  Transit Gateway, peering, Direct Connect and Site-to-Site VPN support IPv6, though
  support varies per service and Region — check before relying on it.
- **Exam angle:** IPv4 cannot be disabled in a VPC; IPv6 addresses are public, so use the
  egress-only IGW to prevent inbound; "running out of IPv4 addresses" points to **adding
  an IPv6 CIDR / IPv6-only subnets**.

## Public IP Types Compared

| | **Auto-assigned public IPv4** | **Elastic IP** |
|---|---|---|
| Survives **stop/start** | **No** — new address | **Yes** |
| Remappable | No | **Yes** |
| Released when | Instance stops/terminates | You release it |
| Typical use | Throwaway or default public access | Whitelisted IP, failover, fixed identity |

- Associating an EIP with an instance **replaces** its auto-assigned public IP, which is
  lost for good.
- An instance with only an EIP keeps it across stop/start; a **reboot** never changes any IP.

## Common Uses

- A **fixed public IP** that clients or partners **whitelist** in their firewall.
- **Failover**: re-associate the EIP to a standby instance (or a standby ENI).
- **NAT Gateway**: needs an EIP for its public address (a private NAT Gateway does not).
- Public-facing resources behind a fixed address when DNS or a load balancer is not an
  option.

## Elastic IP vs Alternatives

| Need | Better than an EIP |
|---|---|
| Stable name for users | **Route 53 / DNS** pointing at an ALB or CloudFront |
| Scale across several instances | **ALB / NLB** (NLB can take one EIP per AZ) |
| Global static anycast IPs | **AWS Global Accelerator** |
| Private access, no public IP | **SSM Session Manager**, VPC endpoints, NAT Gateway |
| IPv6 | Not needed: addresses are already globally unique and stable on the ENI |

## Exam Facts (SAA-C03)

- EIP = **static, public, IPv4, Regional**. **IPv6 has no EIPs** (every address is globally unique).
- Survives **stop/start**; auto-assigned public IPs do **not**.
- **Remappable** → "failover without changing DNS".
- **Charged for all public IPv4**, in use or not → **release unused EIPs**.
- **5 EIPs per Region** by default; can be increased.
- Not transferable between **Regions**; transferable between **accounts** in the same Region.
- A **NAT Gateway** needs an EIP; an **IGW** is still required for internet access.
- To be reachable from the internet an instance needs **IGW + route + public IPv4/EIP**.
- An EIP on an instance in a **private subnet** (no IGW route) does not give internet access.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| A partner needs a fixed IP to whitelist | **Elastic IP** |
| Public IP changes after every stop/start | Use an **Elastic IP** |
| Fail over to a standby instance keeping the same public IP | **Re-associate the EIP** (or move a secondary ENI) |
| Bills for unattached IPs | **Release** unused EIPs |
| Fixed global IP addresses for a multi-Region app | **Global Accelerator**, not EIPs |
| Bring existing public IPs into AWS | **BYOIP** |
| Do IPv6 instances need Elastic IPs? | **No** — addresses are already globally unique and public |
| Need many static IPs per instance | Multiple ENIs/private IPs, each with an EIP |
| Resilient outbound traffic with a fixed source IP | **NAT Gateway** with an EIP (per AZ) |

## Exam Traps

- **An EIP alone doesn't give internet access** — the subnet needs an IGW route.
- **Idle EIPs cost money**; running instances with EIPs are billed too (since public IPv4
  charging began).
- **Association replaces the auto-assigned public IP**; you can't get it back.
- **Regional, not AZ-bound** — unlike the ENI, the EIP can follow an instance to another AZ.
- **One EIP per private IP**: an extra EIP needs a secondary private IP or another ENI.
- **No EIPs for IPv6**: addresses are globally unique, public and stable on the ENI; use the egress-only IGW to keep them outbound-only.
- **EIPs are not Region-portable**; use Global Accelerator for multi-Region static IPs.
- **Prefer DNS/load balancers**; AWS recommends avoiding EIPs where possible.

## Commands

```bash
# Allocate an EIP (from the Amazon pool)
aws ec2 allocate-address --domain vpc

# Associate it with an instance (or --network-interface-id)
aws ec2 associate-address --allocation-id eipalloc-0abc1234 --instance-id i-0abc1234

# Re-associate to a standby instance (failover)
aws ec2 associate-address --allocation-id eipalloc-0abc1234 \
  --instance-id i-0def5678 --allow-reassociation

# List EIPs and spot the unused ones (no AssociationId)
aws ec2 describe-addresses \
  --query 'Addresses[].[PublicIp,AllocationId,InstanceId,AssociationId]' --output table

# Disassociate and release
aws ec2 disassociate-address --association-id eipassoc-0abc1234
aws ec2 release-address --allocation-id eipalloc-0abc1234
```

## Study Checklist

- [ ] Contrast auto-assigned public IP vs Elastic IP across stop/start.
- [ ] Explain EIP failover and the alternative with a secondary ENI.
- [ ] State why NAT Gateways need an EIP.
- [ ] Say when to use DNS, ALB/NLB or Global Accelerator instead.
- [ ] Explain why IPv6 needs no Elastic IPs.
- [ ] Remember the cost rule: all public IPv4 addresses are billed.

## References

- AWS docs — Elastic IP addresses: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html
- AWS docs — Public IPv4 address charge: https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/
- Related notes: [VPC overview](../README.md), [Gateways](../gateways/README.md), [VPC Networking fundamentals](../networking/README.md), [Route Tables](../route-tables/README.md)
