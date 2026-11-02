# Bastion Host / Jump Box — Exam Notes

A **bastion host** (a.k.a. **jump box**) is a hardened EC2 instance in a **public subnet**
that is the single, controlled entry point for administering instances in **private
subnets** over SSH (Linux, port 22) or RDP (Windows, port 3389).

```
 Admin ──SSH──> Bastion (public subnet, public IP/EIP) ──SSH──> Private EC2 (no public IP)
        internet                 IGW                      private IP, VPC-local route
```

## How it works

1. Launch an EC2 instance in a **public subnet** (route `0.0.0.0/0 -> igw`) with a public
   IPv4 / **Elastic IP**.
2. **Bastion SG:** inbound 22 (or 3389) **only from the admin / corporate CIDR** — never `0.0.0.0/0`.
3. **Private instance SG:** inbound 22 **with the bastion's security group as source**
   (SG reference), not a CIDR.
4. Connect to the bastion, then hop to the private instance's **private IP**.
5. Use **SSH agent forwarding** (`ssh -A`) or **ProxyJump** (`ssh -J bastion private`) so the
   private key is **never stored on the bastion**.

```bash
# One command through the bastion; key stays on your machine
ssh -J ec2-user@BASTION_PUBLIC_IP ec2-user@PRIVATE_IP
```

## Hardening checklist

- Restrict the source IP range in the SG; no other open ports.
- Minimal AMI, patched, no extra software; disable password auth (keys only).
- Log sessions (CloudWatch Logs agent) and enable CloudTrail.
- Optionally an **Auto Scaling group (min=max=1)** so it self-heals, with an **EIP**
  re-associated via user data.
- For HA across AZs: one bastion per AZ behind a **Network Load Balancer** (TCP 22), or an ASG
  spanning two public subnets.
- Use **IAM roles**, not stored credentials, on the bastion.
- Stop it when not needed (cost) — or avoid it entirely (see below).

## Modern alternatives (often the "better" exam answer)

| Option | How it works | Pick it when the question says |
|---|---|---|
| **SSM Session Manager** | SSM Agent calls out to Systems Manager; **no inbound ports, no keys, no public IP**; IAM-controlled; sessions logged to S3/CloudWatch | "no open ports", "no bastion", "audit/log every session", "least operational overhead" |
| **EC2 Instance Connect Endpoint** | Endpoint in the VPC tunnels SSH/RDP to private instances; IAM-controlled, CloudTrail-logged | "SSH to private instance **without a public IP or bastion**" |
| **EC2 Instance Connect** | Pushes a temporary (60 s) public key to the instance via the API | "temporary keys", "no long-lived SSH keys" |
| **Site-to-Site VPN / Direct Connect** | Admins reach private IPs directly over the private link | "admins on-premises already connected to the VPC" |
| **AWS Client VPN** | Remote users get a VPN into the VPC | "remote admins need private access" |

SSM Session Manager needs: SSM Agent (preinstalled on Amazon Linux/Windows AMIs), an
**instance profile** with `AmazonSSMManagedInstanceCore`, and outbound HTTPS to SSM — via
NAT **or** the interface endpoints `ssm`, `ssmmessages`, `ec2messages` (fully private VPC).

## Bastion vs NAT — do not confuse them

| | **Bastion host** | **NAT Gateway / instance** |
|---|---|---|
| Direction | **Inbound** admin access to private instances | **Outbound** internet access from private instances |
| Protocol | SSH / RDP | Any outbound IPv4 |
| Lives in | Public subnet | Public subnet |
| Needs | Public IP/EIP, restrictive SG | EIP, route in private route table |

## Exam tips

- **"Securely administer private instances"** with a classic design -> bastion in a public
  subnet; SG allows SSH **only from the corporate IP**.
- Private instance SG should reference the **bastion SG** as source, not `0.0.0.0/0`.
- **Fewest open ports / no bastion / no SSH keys / auditing** -> **SSM Session Manager**.
- **No public IP and no bastion, via the VPC** -> **EC2 Instance Connect Endpoint**.
- A bastion is **not** a NAT: it does not give private instances internet access.
- Bastion in a **private** subnet is a trap — it needs a public IP and an IGW route.
- Keep keys off the bastion: **agent forwarding / ProxyJump**.
- HA bastion: **ASG across 2 AZs** (+ NLB); a single bastion is a single point of failure.
- A NACL on the public subnet must allow inbound 22 **and** outbound **ephemeral ports**
  (1024-65535) since NACLs are stateless; SGs are stateful.

## Sample questions

1. *A company's EC2 instances in private subnets must be administered via SSH. Security
   requires that no inbound ports be open to the internet and every session be logged. What
   should the architect do?* -> **SSM Session Manager** (not a bastion).
2. *Admins need SSH to private instances only from the office (203.0.113.0/24). Which
   design?* -> Bastion in a public subnet, SG inbound 22 from `203.0.113.0/24`; private SG
   inbound 22 from the bastion SG.
3. *Which is the most cost-effective way to SSH into a private instance with no bastion and
   no public IP?* -> **EC2 Instance Connect Endpoint**.
4. *The bastion must survive an AZ failure.* -> Bastions in two AZs (ASG across public
   subnets) behind an NLB.

## References

- Bastion on AWS (Quick Start / blog): https://aws.amazon.com/solutions/implementations/linux-bastion/
- Session Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html
- EC2 Instance Connect Endpoint: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-with-ec2-instance-connect-endpoint.html
- Related notes: [VPC overview](../README.md), [Security Groups](../security-groups/README.md), [Network ACLs](../nacl/README.md), [Gateways (NAT/IGW)](../gateways/README.md), [VPC Endpoints](../vpc-endpoints/README.md)
