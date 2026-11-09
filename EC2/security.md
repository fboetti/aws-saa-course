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

## EC2 Instance Connect

- Connects to an instance over SSH **without managing long-lived key pairs**. Console: select the instance → **Connect → EC2 Instance Connect** (browser terminal), or from a terminal: `aws ec2-instance-connect ssh --instance-id i-...`.
- How it works: on each connection it calls `SendSSHPublicKey`, which pushes a **temporary public key** to the instance metadata. The key is valid for **60 seconds**, so you must connect right away. The instance's SSH daemon fetches it through an `AuthorizedKeysCommand` helper.
- Supported on **Amazon Linux 2 / 2023 and Ubuntu** (the package is preinstalled on those AMIs). Other Linux distros need the `ec2-instance-connect` package installed. **Windows is not supported** (use RDP or SSM).
- Network requirements:
  - **Security group must allow inbound SSH (22)** from the source. For the browser console, that is the **AWS-published EC2_INSTANCE_CONNECT IP range** for the region (it can be looked up in `ip-ranges.json`).
  - The instance needs a **public IPv4** for the browser console. For private instances, use an **EC2 Instance Connect Endpoint** (below).
- Permissions are **IAM-based**: the user needs `ec2-instance-connect:SendSSHPublicKey`, which can be restricted by instance ID, tags and OS user. This gives per-user control and CloudTrail records of who connected.
- **EC2 Instance Connect Endpoint (EICE)**: an endpoint in your VPC subnet that lets you SSH/RDP to **private instances without a public IP, bastion host or internet gateway**. Connections are IAM-authorised and logged in CloudTrail. Use `aws ec2-instance-connect ssh --connection-type eice`.
- Compared with Session Manager: Instance Connect still needs **port 22 open** and an SSH-capable OS. Session Manager needs no inbound ports but needs the SSM Agent and an instance role.
- Troubleshooting "connection failed" in the console: wrong security group or NACL on port 22, no public IP, unsupported AMI, or wrong default username.

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
- "Browser SSH, no permanent keys to manage" → **EC2 Instance Connect**. "SSH to a private instance with no bastion/public IP" → **Instance Connect Endpoint**.
- "App on EC2 must call S3" → IAM role, not access keys.
