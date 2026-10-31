# Network ACLs (NACLs) — Exam Notes

A **network ACL (NACL)** is a **stateless firewall at the subnet boundary**. It filters
every packet entering or leaving a subnet, using an ordered list of **allow and deny**
rules. It is the second filtering layer of a VPC, next to [security groups](../security-groups/README.md).

```
                     ┌──────────────── Subnet 10.0.1.0/24 ────────────────┐
 Internet / other    │   NACL (subnet edge)        SG (per ENI)           │
 subnets  ─────────> │ ─> inbound rules ──────> inbound rules ──> EC2     │
          <───────── │ <─ outbound rules <───── outbound rules <──        │
                     └────────────────────────────────────────────────────┘
```

## Purpose

- **Subnet-wide guardrail** — one rule set covers every resource in the subnet, including
  ones launched later by someone who forgot to configure a security group.
- **Explicitly deny** traffic — the only native VPC control that can block a specific IP
  or CIDR (security groups cannot deny).
- **Defense in depth** — an extra layer in front of the SGs, often owned by a network or
  security team while application teams own the SGs.
- **Coarse isolation between tiers** — e.g. the database subnet only accepts traffic from
  the app subnet's CIDR.

For fine-grained, tier-to-tier least privilege, security groups remain the main tool.

## How NACLs Work

| Property | Behaviour |
|---|---|
| **Scope** | A **subnet**. Each subnet has **exactly one** NACL; one NACL can be associated with **many** subnets |
| **State** | **Stateless** — inbound and outbound are checked independently; return traffic must be allowed explicitly |
| **Rules** | **Allow and deny**, separate inbound and outbound lists |
| **Evaluation** | Rules are numbered **1–32766**, evaluated **lowest number first**; the **first match wins** and evaluation stops |
| **Catch-all** | The final `*` rule denies everything not matched; it cannot be edited or removed |
| **Rule match on** | Protocol, port range, and source (inbound) / destination (outbound) **CIDR** — not security groups |
| **Quota** | **20** rules per direction (adjustable up to 40); **200** NACLs per VPC |
| **Propagation** | Changes apply **immediately** |
| **Cost** | Free |

### Default vs custom NACL

| | **Default NACL** | **Custom NACL** |
|---|---|---|
| Created | With the VPC (one per VPC) | By you |
| Inbound / outbound | **Allow all** | **Deny all** until you add rules |
| Subnet association | Every subnet without an explicit association | Only the subnets you associate |
| Deletable | No | Yes, once no subnet is associated |

Associating a subnet with a new NACL **replaces** its current association; the subnet
falls back to the default NACL if you delete the custom one.

### Rule numbering

```
 Rule #   Type         Protocol  Port range     Source / Dest      Allow/Deny
 100      HTTPS        TCP       443            0.0.0.0/0          ALLOW
 110      SSH          TCP       22             203.0.113.0/24     ALLOW
 120      Custom TCP   TCP       1024-65535     0.0.0.0/0          ALLOW   (return traffic)
 *        All          All       All            0.0.0.0/0          DENY
```

- Leave **gaps** (100, 110, 120…) so you can insert rules later.
- **Order matters.** A `DENY 198.51.100.7/32` must have a **lower number** than the
  `ALLOW 0.0.0.0/0` it should override, otherwise the allow matches first.

## Statelessness and Ephemeral Ports

A client connects *to* a well-known port (443) *from* a random **ephemeral port**. The
reply goes back to that ephemeral port, so the NACL on the client side must allow it.

```
 Web server in subnet (inbound HTTPS from the internet)
   Inbound  rule: allow TCP 443        (request)
   Outbound rule: allow TCP 1024-65535 (response to the client's ephemeral port)

 Instance in subnet calling an external API (outbound HTTPS)
   Outbound rule: allow TCP 443        (request)
   Inbound  rule: allow TCP 1024-65535 (response)
```

- Exam answer: **1024–65535**. In practice Linux uses 32768–60999, Windows 49152–65535,
  and NAT gateways 1024–65535.
- **Symptom of a missing ephemeral rule:** the SG allows the request, but connections hang
  or time out. In **VPC Flow Logs** the request shows `ACCEPT` and the response `REJECT`.

## Where the NACL Sits in the Packet Flow

- **Inbound:** NACL (subnet) → security group (ENI) → instance.
- **Outbound:** security group (ENI) → NACL (subnet) → out.
- Traffic between two instances in the **same subnet** never crosses the NACL; only the
  SGs apply. Traffic between **different subnets** crosses the NACL of **both** subnets.
- Traffic to/from the **VPC's own services** is not filtered by NACLs: DHCP, the Amazon
  DNS resolver (Route 53 Resolver), instance metadata (`169.254.169.254`), Amazon Time
  Sync, and the default-gateway/VPC router addresses.

## Security Group vs NACL

| | **Security group** | **NACL** |
|---|---|---|
| Level | ENI / instance | **Subnet** |
| State | **Stateful** | **Stateless** |
| Rules | **Allow only** | Allow **and deny** |
| Evaluation | All rules together | Numbered, **first match wins** |
| Return traffic | Automatic | Must be allowed explicitly |
| Source / destination | CIDR, prefix list, **another SG** | **CIDR only** |
| Default (new) | Inbound deny, outbound allow | Default NACL: allow all; custom: deny all |
| Applies to | Only resources the SG is attached to | **Everything** in the subnet |
| Typical use | Tier-to-tier access, least privilege | **Blocking IPs**, subnet guardrails |

## Exam Facts (SAA-C03)

- NACLs are **stateless** and **subnet-level**; SGs are **stateful** and **ENI-level**.
- NACLs support **deny** rules; SGs do not.
- Rules are evaluated in **ascending order**, **first match wins**.
- A subnet has **one** NACL; a NACL can serve **many** subnets.
- **Default NACL = allow all; custom NACL = deny all** until rules are added.
- **Block a specific IP/CIDR** (attacker, scanner, abusive client) → **NACL deny rule**.
- Return traffic needs **ephemeral ports 1024–65535**.
- NACLs cannot reference security groups — **CIDR blocks only**.
- NACLs are **free**, **regional** (VPC-scoped) and apply **immediately**.
- Debugging: **VPC Flow Logs** show `ACCEPT`/`REJECT`; inbound `ACCEPT` + response
  `REJECT` points at a **NACL**.
- Both layers must allow the traffic: a flow needs **NACL allow AND SG allow**.

### Scenario → Answer

| Scenario | Answer |
|---|---|
| Block one malicious IP from reaching the whole subnet | **NACL deny rule** with a low number |
| Security groups can't deny — how to block a CIDR range? | **NACL** |
| Requests reach the instance (SG allows) but responses never return | NACL missing **ephemeral port** outbound rule |
| Ensure no instance in a subnet can ever accept SSH, whatever its SG says | **NACL** deny TCP 22 inbound |
| Allow only the app tier to reach the database subnet | NACL on the DB subnet (CIDR-based) **plus** an SG referencing the app SG |
| Want a stateful, instance-level firewall | **Security group**, not NACL |
| Filtering by domain name, deep packet inspection or IPS | **AWS Network Firewall** (or WAF for HTTP), not NACL |
| Protect an ALB/CloudFront from web exploits (SQLi, XSS) | **AWS WAF** — NACLs only see IP/port/protocol |
| Newly created custom NACL, nothing works | Custom NACLs **deny all** — add allow rules both ways |
| Changed rules in a NACL — do instances need a restart? | No, applied **immediately** |

## Exam Traps

- **"Stateless" means two rules.** An allowed inbound 443 does **not** allow the
  response; you must also open ephemeral ports outbound.
- **Order beats intent.** A deny placed *after* a broader allow is never reached.
- **Default ≠ custom.** The default NACL allows everything; a brand new custom one
  denies everything.
- **One NACL per subnet.** Associating another replaces the first, not adds to it.
- **NACLs cannot filter by SG or by instance.** Only CIDR, protocol and ports.
- **Same-subnet traffic bypasses the NACL.** Don't use a NACL to isolate two instances in
  the same subnet — use SGs or separate subnets.
- **NACLs don't inspect content.** Domain/URL filtering → Network Firewall; HTTP attacks
  → WAF; DDoS → Shield.
- **Don't overuse NACLs.** AWS best practice is to keep SGs as the primary control and use
  NACLs sparingly for explicit denies and subnet-level guardrails.
- **Quotas bite.** 20 rules per direction by default; with a long deny list, summarise
  into CIDRs or use Network Firewall.
- **IPv6 needs its own rules.** IPv4 and IPv6 rules are separate entries; a `0.0.0.0/0`
  rule does not cover `::/0`.

## Commands

```bash
# All NACLs of a VPC with their associations
aws ec2 describe-network-acls \
  --filters Name=vpc-id,Values=vpc-0abc1234 \
  --query 'NetworkAcls[].{Id:NetworkAclId,Default:IsDefault,Subnets:Associations[].SubnetId}' \
  --output table

# Rules of one NACL, in evaluation order
aws ec2 describe-network-acls --network-acl-ids acl-0abc1234 \
  --query 'NetworkAcls[0].Entries[].[RuleNumber,Egress,Protocol,RuleAction,CidrBlock,PortRange]' \
  --output table

# Create a custom NACL (denies everything until rules are added)
aws ec2 create-network-acl --vpc-id vpc-0abc1234

# Allow HTTPS in (rule 100), ephemeral ports out (rule 100, --egress)
aws ec2 create-network-acl-entry --network-acl-id acl-0abc1234 \
  --rule-number 100 --protocol tcp --port-range From=443,To=443 \
  --cidr-block 0.0.0.0/0 --rule-action allow --ingress
aws ec2 create-network-acl-entry --network-acl-id acl-0abc1234 \
  --rule-number 100 --protocol tcp --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 --rule-action allow --egress

# Block one IP for the whole subnet (lower number than the allow rules)
aws ec2 create-network-acl-entry --network-acl-id acl-0abc1234 \
  --rule-number 50 --protocol -1 \
  --cidr-block 198.51.100.7/32 --rule-action deny --ingress

# Associate a subnet with the NACL (replaces its current one)
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-0abc1234 \
  --query 'NetworkAcls[0].Associations[?SubnetId==`subnet-0abc1234`].NetworkAclAssociationId'
aws ec2 replace-network-acl-association \
  --association-id aclassoc-0abc1234 --network-acl-id acl-0abc1234

# Change or delete a rule
aws ec2 replace-network-acl-entry --network-acl-id acl-0abc1234 \
  --rule-number 100 --protocol tcp --port-range From=443,To=443 \
  --cidr-block 10.0.0.0/8 --rule-action allow --ingress
aws ec2 delete-network-acl-entry --network-acl-id acl-0abc1234 --rule-number 50 --ingress
```

## Study Checklist

- [ ] Explain stateless vs stateful and what it means for return traffic.
- [ ] Say why `1024–65535` outbound is needed for a public web server.
- [ ] Order three rules so that a deny for one IP beats a broader allow.
- [ ] State what a default NACL and a custom NACL allow.
- [ ] Choose NACL vs SG vs Network Firewall vs WAF for a given requirement.
- [ ] Read a Flow Log with inbound `ACCEPT` and response `REJECT` and name the culprit.
- [ ] Recite the quotas: 20 rules per direction, 1–32766 numbering, one NACL per subnet.

## References

- AWS docs — Network ACLs: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html
- AWS docs — Network ACL rules and ephemeral ports: https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html
- AWS docs — Compare security groups and network ACLs: https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html#VPC_Security_Comparison
- Related notes: [VPC overview](../README.md), [VPC Networking fundamentals](../networking/README.md), [Default VPC](../default-vpc/README.md), [VPC Sharing](../vpc-sharing/README.md)
