# Security Groups — Exam Notes

A **security group (SG)** is a **stateful, allow-only firewall attached to an ENI**. It is
the main VPC traffic control: it decides what can reach (inbound) and leave (outbound) a
resource such as an EC2 instance, RDS database, ALB or Lambda function in a VPC. The other
filtering layer is the [NACL](../nacl/README.md).

```
                     ┌──────────────── Subnet 10.0.1.0/24 ────────────────┐
 Internet / other    │   NACL (subnet edge)        SG (per ENI)           │
 subnets  ─────────> │ ─> inbound rules ──────> inbound rules ──> EC2     │
          <───────── │ <─ outbound rules <───── outbound rules <──        │
                     └────────────────────────────────────────────────────┘
```

## How Security Groups Work

| Property | Behaviour |
|---|---|
| **Scope** | An **ENI** (so an instance, RDS, ALB, interface endpoint, Lambda-in-VPC…); the SG itself belongs to a **VPC** |
| **State** | **Stateful** — a reply to an allowed request is allowed automatically, in both directions |
| **Rules** | **Allow only** — there is no deny rule; anything not allowed is dropped |
| **Evaluation** | **All rules are evaluated together**, no ordering or priority |
| **Source / destination** | CIDR (IPv4/IPv6), **prefix list**, or **another security group** |
| **Default (new SG)** | **No inbound rules** (deny all), **all outbound allowed** |
| **Multiple SGs** | Up to **5 per ENI** (adjustable to 16); the effective rules are the **union** |
| **Quota** | **60** inbound + **60** outbound rules per SG; **2,500** SGs per Region (can have up to 10k)|
| **Propagation** | Changes apply **immediately**, no restart; existing tracked connections are not cut |
| **Cost** | Free |

### Default security group

Every VPC has one **default SG** that cannot be deleted:

- **Inbound:** allow all traffic **from members of the same SG**.
- **Outbound:** allow all.
- Instances launched without an explicit SG get this one.

### Rule anatomy

```
 Inbound
 Type    Protocol  Port   Source              Purpose
 HTTPS   TCP       443    0.0.0.0/0           public web traffic
 SSH     TCP       22     203.0.113.10/32     admin from the office IP only
 MySQL   TCP       3306   sg-0app1234         only members of the app SG
```

- A rule is defined by **protocol + port range + source** (inbound) or **destination**
  (outbound).
- Inbound rules have a **source**; outbound rules have a **destination**.
- Descriptions are optional but recommended.

## Referencing Other Security Groups

Instead of an IP range, a rule can name another SG as the source. Every ENI **in** that SG
is allowed, whatever its IP.

```
 Internet ──443──> [ALB SG] ──8080──> [App SG] ──3306──> [DB SG]
                    src: 0.0.0.0/0     src: ALB SG       src: App SG
```

- Survives scaling, replacement and IP changes — no CIDR to maintain.
- Works across **peered VPCs in the same Region** (and across accounts, by `account/sg-id`).
- The rule matches the **private IPs** of the members; it does **not** pull in the SG's own
  rules.
- A rule referencing its **own SG** allows members to talk to each other (the default SG
  does this).

## Stateful Behaviour and Connection Tracking

- If an inbound request is allowed, the response leaves **regardless of outbound rules**.
  If an outbound request is allowed, the response returns **regardless of inbound rules**.
- No need to open **ephemeral ports** — that is a NACL concern.
- Tracked connections survive rule removal until they close; **untracked** flows (e.g. a
  rule open to `0.0.0.0/0` on all ports with a matching all-ports rule the other way) are
  re-evaluated per packet, so removing the rule cuts them immediately.

## Traffic Security Groups Don't Filter

Not blocked by an SG, regardless of rules: DHCP, the Amazon DNS resolver, instance
metadata (`169.254.169.254`), Amazon Time Sync, the VPC router, and Windows license
activation. They are also outside what a NACL filters.

## Security Group vs NACL

| | **Security group** | **NACL** |
|---|---|---|
| Level | ENI / instance | **Subnet** |
| Association | **Many SGs per ENI** (up to 5, union of rules) | **One NACL per subnet** (one NACL can serve many subnets) |
| State | **Stateful** | **Stateless** |
| Rules | **Allow only** | Allow **and deny** |
| Evaluation | **All rules together**, no order | **Numbered 1–32766, first match wins** |
| Return traffic | Automatic | Must be allowed explicitly (**ephemeral ports 1024–65535**) |
| Source / destination | CIDR, prefix list, **another SG** | **CIDR only** |
| Default (new) | Inbound **deny**, outbound **allow** | Default NACL: **allow all**; custom NACL: **deny all** |
| Applies to | Only resources the SG is attached to | **Everything** in the subnet |
| Same-subnet traffic | **Filtered** (SG applies to both ENIs) | **Not seen** — never crosses the subnet edge |
| Quotas | 60 in + 60 out rules per SG, 5 SGs per ENI | 20 rules per direction (up to 40), 200 NACLs per VPC |
| Blocking an IP | **Impossible** | **Yes** — deny rule with a low number |
| Ownership | Usually the **application team** | Usually the **network / security team** |
| Typical use | Tier-to-tier least privilege | **Blocking IPs**, subnet guardrails |
| Troubleshooting sign | Everything times out | Request `ACCEPT`, response `REJECT` in Flow Logs |

### Stateful (SG) vs Stateless (NACL)

**Stateful** = the firewall remembers connections. When a request is allowed, it records
the flow and lets the reply through without checking any rule.
**Stateless** = no memory. Every packet is checked on its own against the rules, in each
direction, as if it were the first.

Example: a client on the internet opens HTTPS to a web server in the subnet.

```
 SECURITY GROUP (stateful)                NACL (stateless)

 client ──443──> inbound rule? ALLOW      client ──443──> inbound rule 100? ALLOW
        <───────  reply passes            <──────────── outbound rule? needed!
                  automatically                         must allow TCP 1024-65535
                  (outbound not checked)                (client's ephemeral port)
```

| | **Stateful — security group** | **Stateless — NACL** |
|---|---|---|
| Remembers connections | **Yes** (connection tracking) | **No** |
| Rules needed for a request/response | **One** (the direction that starts the flow) | **Two** (request direction + return direction) |
| Return traffic | Allowed automatically | Checked against the opposite-direction rules |
| Ephemeral ports | Not a concern | Must be opened: **1024–65535** |
| Outbound rules for replies | Not consulted | **Required** |
| Typical misconfiguration | Forgetting an inbound rule (nothing gets in) | Forgetting the return rule (**request arrives, reply dropped**) |
| Flow Logs symptom | Whole connection times out | Request `ACCEPT`, response `REJECT` |
| Rule count for a web server | 1 inbound (443) | 1 inbound (443) + 1 outbound (1024–65535) |

- Inbound-initiated flow (client → server): SG needs **inbound 443**; NACL needs **inbound
  443 + outbound 1024–65535**.
- Outbound-initiated flow (server → external API): SG needs **outbound 443** (open by
  default); NACL needs **outbound 443 + inbound 1024–65535**.
- Stateful tracking is per connection, so the SG reply is allowed even if the outbound
  rules are empty or the inbound rule is later removed for a connection already tracked.

### Packet order

- **Inbound:** NACL (subnet) → **SG** (ENI) → instance.
- **Outbound:** instance → **SG** (ENI) → NACL (subnet).
- A flow needs **NACL allow AND SG allow**; either layer alone can drop it.

### Which one is it? (quick tells)

| Clue in the question | Pick |
|---|---|
| "Deny", "block", "blacklist" an IP or CIDR | **NACL** |
| "Stateful", "instance level", "attached to the instance" | **SG** |
| "Subnet level", "all instances in the subnet", "rule numbers" | **NACL** |
| "Allow traffic only from the web tier / another group" | **SG** (reference the SG) |
| "Ephemeral ports", "return traffic must be allowed" | **NACL** |
| "Least privilege between tiers" | **SG** |
| "Additional layer / defense in depth" | **SG + NACL** |

## Exam Facts (SAA-C03)

- SGs are **stateful** and **ENI-level**; NACLs are **stateless** and **subnet-level**.
- SGs support **allow rules only** — they **cannot deny**. To block an IP use a **NACL**.
- **New SG: no inbound, all outbound.** Default SG: inbound from itself, all outbound.
- **All rules are evaluated**; there is no rule order.
- An ENI can have **up to 5 SGs** and the rules are combined (union).
- A rule's source can be a **CIDR, a prefix list or another SG**.
- **Chain tiers by SG reference** (ALB → app → DB), not by IP ranges.
- SGs are **Region/VPC-scoped** — usable only in their own VPC (and peered VPCs in the same
  Region for references). In a [shared VPC](../vpc-sharing/README.md), participants create and manage their own SGs; they can't see or edit other accounts' SGs.
- Changes are **immediate**; no instance restart.
- SGs are **free**.
- You can change the SGs of a **running** instance; you can't remove the last one (it falls
  back to the default SG).
- Timeouts vs refusals: a blocked connection **times out** (SG drops silently); a
  **"connection refused"** means traffic got through and nothing listens on the port.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| Web servers must accept HTTPS from anyone | Inbound **TCP 443 from 0.0.0.0/0** (and `::/0` for IPv6) |
| Only the web tier may reach the database | DB SG inbound 3306, **source = web SG** |
| Allow SSH only from the corporate network | Inbound TCP 22 from the **office CIDR** |
| Block one IP address from an instance | **NACL deny** — SG can't deny |
| Source IPs of the app tier change constantly (Auto Scaling) | **Reference the SG**, not a CIDR |
| Many rules share the same CIDRs across SGs | **Managed prefix list** |
| Remote admin without opening port 22 | **SSM Session Manager** (no inbound rules) |
| Instances in the same SG cannot talk to each other | Add a rule with **the SG itself as source** (new SGs don't allow it) |
| Need a stateful firewall for one instance | **Security group** |
| Need to block a domain name or inspect packets | **AWS Network Firewall**, not SG |
| Protect against SQLi / XSS | **AWS WAF** on ALB/CloudFront |
| Lambda in a VPC can't reach the internet | Check subnet route (**NAT**), not just the SG; SG outbound too |
| Can SG rules be changed without restarting? | Yes, **immediately** |

## Exam Traps

- **SGs cannot deny.** Any "block this IP/range" answer with an SG rule is wrong.
- **Stateful ≠ everything open.** A new SG blocks all inbound; only replies to allowed
  connections are free.
- **Outbound is open by default.** Tightening outbound is a hardening step, not required
  for replies.
- **No priority.** Two conflicting rules can't exist — rules only allow, so any match wins.
- **SG references use private IPs.** Traffic that reaches the target via its **public** or
  Elastic IP is not matched by an SG-source rule.
- **Per-VPC.** An SG from VPC A can't be attached in VPC B (no cross-VPC use except peering
  references and VPC sharing).
- **The default SG self-reference** means resources in the default SG can talk to each other
  but nothing external can reach them.
- **Don't open 0.0.0.0/0 on SSH/RDP.** Typical "most secure" answer: restrict to a known
  CIDR, or use SSM Session Manager / EC2 Instance Connect Endpoint.
- **SGs filter ports, not content.** Use WAF/Network Firewall for application-layer
  filtering.
- **IPv6 is separate.** `0.0.0.0/0` doesn't cover `::/0`.
- **Both layers apply.** Traffic needs **NACL allow AND SG allow**.

## Commands

```bash
# Create an SG in a VPC (no inbound, all outbound)
aws ec2 create-security-group --group-name web-sg \
  --description "Web tier" --vpc-id vpc-0abc1234

# Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress --group-id sg-0web1234 \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Allow MySQL from another SG (tier chaining)
aws ec2 authorize-security-group-ingress --group-id sg-0db1234 \
  --protocol tcp --port 3306 --source-group sg-0app1234

# Inspect the rules of an SG
aws ec2 describe-security-group-rules --filters Name=group-id,Values=sg-0web1234 \
  --query 'SecurityGroupRules[].[IsEgress,IpProtocol,FromPort,ToPort,CidrIpv4,ReferencedGroupInfo.GroupId]' \
  --output table

# Remove a rule
aws ec2 revoke-security-group-ingress --group-id sg-0web1234 \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Replace the SGs of an instance
aws ec2 modify-instance-attribute --instance-id i-0abc1234 \
  --groups sg-0web1234 sg-0admin1234

# Delete an SG (fails if still attached or referenced by another SG)
aws ec2 delete-security-group --group-id sg-0web1234
```

## Study Checklist

- [ ] Explain stateful vs stateless and why SGs need no ephemeral-port rule.
- [ ] Say what a brand new SG allows inbound and outbound, and what the default SG allows.
- [ ] Design ALB → app → DB SGs using SG references.
- [ ] Choose SG vs NACL vs Network Firewall vs WAF for a requirement.
- [ ] Explain why an SG can't block an IP, and what to use instead.
- [ ] Recall the limits: 5 SGs per ENI, 60 rules per direction, immediate effect.
- [ ] Differentiate "timed out" (filtered) from "connection refused" (reached, no listener).

## References

- AWS docs — Security groups: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
- AWS docs — Security group rules: https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html
- AWS docs — Compare security groups and network ACLs: https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html#VPC_Security_Comparison
- Related notes: [VPC overview](../README.md), [Network ACLs](../nacl/README.md), [VPC Networking fundamentals](../networking/README.md), [Default VPC](../default-vpc/README.md), [VPC Sharing](../vpc-sharing/README.md)
