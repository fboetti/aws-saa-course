# EC2 Security

## Security Groups (SG)

- **Virtual firewall at the ENI level**; allow rules only (no deny).
- **Stateful**: return traffic automatically allowed.
- Default SG: inbound denied, outbound all allowed.
- Rules reference **CIDR, other SGs, or prefix lists**; referencing an SG avoids hardcoded IPs.
- Many SGs per instance (rules are unioned); many instances per SG.
- Scoped to a **VPC/region**.
- Timeouts → SG issue; "connection refused" → application issue.

Classic ports: **22** SSH, **3389** RDP, **80** HTTP, **443** HTTPS, **21** FTP, **3306** MySQL, **5432** PostgreSQL.

### SG vs NACL

| | Security Group | NACL |
|---|---|---|
| Level | Instance (ENI) | Subnet |
| State | Stateful | Stateless |
| Rules | Allow only | Allow and deny, ordered |
| Evaluation | All rules | Lowest number first |

## Key Pairs

- Public key stored on the instance; private key (`.pem`/`.ppk`) kept by you. Used for SSH and Windows password decryption.
- Lost key: stop instance → detach root volume → fix `authorized_keys` on a rescue instance, or use SSM.

## Access Methods

- **SSH** (22), **RDP** (3389).
- **EC2 Instance Connect**: browser SSH, pushes a temporary key; needs port 22 open from AWS ranges.
- **Session Manager (SSM)**: no inbound ports, no key pair, no bastion; IAM-controlled, logged to CloudWatch/S3. Needs SSM Agent + instance role `AmazonSSMManagedInstanceCore` + network path to SSM endpoints.
- **Bastion host** in a public subnet (legacy approach).

Switch to the default user (e.g. after a Session Manager login, which starts as `ssm-user`):

```bash
sudo su - ec2-user
```

The `-` gives a full login shell (home directory, `ec2-user` environment). Default usernames: `ec2-user` (Amazon Linux), `ubuntu` (Ubuntu), `admin` (Debian), `ec2-user` or `centos` (RHEL/CentOS variants).

## IAM Roles for EC2

- Attach an **instance profile** (role) → temporary credentials via instance metadata. **Never** store access keys on instances.
- See [IAM identities](../IAM/identities.md).

## Other Security Features

- **EBS encryption** (KMS), **Nitro Enclaves** (isolated compute for sensitive data).
- **AWS Systems Manager**: Patch Manager, Run Command, State Manager, Parameter Store.
- **Amazon Inspector**: vulnerability scanning of instances.
- **GuardDuty**: threat detection (e.g. crypto mining, unusual API calls).
- **CloudTrail** logs EC2 API calls; **VPC Flow Logs** capture traffic metadata.
- Compliance isolation: Dedicated Hosts/Instances.

## Shared Responsibility

AWS: hardware, hypervisor, facilities. You: guest OS patches, firewall (SG), IAM, data, app security.

## Exam Tips

- "Allow only the web tier to talk to DB" → DB SG allows source = web SG.
- "Access instances without opening ports/bastion" → SSM Session Manager.
- "App on EC2 must call S3" → IAM role, not access keys.
