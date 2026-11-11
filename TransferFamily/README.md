# AWS Transfer Family (SFTP, FTPS, FTP, AS2)

**AWS Transfer Family** is a fully managed service to transfer files **into and out of S3 or EFS** using the standard file-transfer protocols your partners and legacy tools already use. No servers to run: you keep your existing clients and workflows and just change the endpoint.

## Supported Protocols

| Protocol | Port | Security | Notes |
|---|---|---|---|
| **SFTP** (SSH File Transfer Protocol) | 22 | Encrypted over SSH | Most common. Not the same as FTPS |
| **FTPS** (FTP over TLS) | 21 + data ports | Encrypted with TLS (needs a certificate from ACM) | |
| **FTP** | 21 | **Not encrypted** | **VPC-internal only** (cannot be public) |
| **AS2** (Applicability Statement 2) | 443 | Signed + encrypted messages | B2B / EDI documents (supply chain, healthcare) |

## Storage Backends

- **Amazon S3** (most common) or **Amazon EFS**.
- Users see a normal folder structure; files are stored as S3 objects / EFS files.
- Each user is mapped to a **home directory** (a bucket/prefix or EFS path) and an **IAM role** that defines what they may access.

## Endpoint Types

| Type | Access | Notes |
|---|---|---|
| **Public** | Internet, AWS-managed IPs | Simplest. IPs can change |
| **VPC (internet-facing)** | Elastic IPs + **security groups** | Fixed IPs for partner **allow-lists** |
| **VPC (internal)** | Private only (Direct Connect / VPN / peering) | Required for FTP; needs access from on-prem or other VPCs |

> Need a **static IP** for firewall allow-listing → VPC endpoint with Elastic IPs.
> Custom domain → **Route 53** record (or a third-party DNS) pointing to the endpoint.

## Authentication

| Method | Use |
|---|---|
| **Service managed** | Users and SSH public keys stored in Transfer Family (SFTP only) |
| **AWS Directory Service** | Microsoft AD / AD Connector credentials (SFTP, FTPS, FTP) |
| **Custom identity provider** | Your own IdP via **Lambda** or **API Gateway** (LDAP, Okta, Cognito, etc.). Works with all protocols |

## Key Features

- **Fully managed, highly available, multi-AZ**, scales automatically.
- **Pay per hour per enabled protocol endpoint + per GB transferred** (so delete unused servers).
- **Managed workflows**: post-upload steps (copy, tag, decrypt, delete, custom Lambda) for processing, virus scanning, etc.
- **Logging** to CloudWatch Logs; actions in CloudTrail.
- **Encryption**: in transit (SFTP/FTPS/AS2), at rest with S3/EFS **SSE** (KMS).
- **Event integration**: S3 events / EventBridge to trigger processing after upload.
- **Scope-down policies** and **logical directories** to restrict each user to their own folder.

## Typical Architecture

```
Partner (SFTP client) → Transfer Family endpoint → S3 bucket / EFS
                                  │                     │
                    IAM role + home dir per user   S3 event → Lambda / workflow
```

## Transfer Family vs Alternatives

| Need | Use |
|---|---|
| Partners/legacy tools must use **SFTP/FTPS/FTP** into S3/EFS | **Transfer Family** |
| Scheduled bulk sync on-prem ↔ AWS (NFS/SMB) | **DataSync** |
| Cloud-backed file shares for on-prem apps | **Storage Gateway** |
| Huge offline migration | [Snow Family](../SnowFamily/README.md) |
| Your own app uploading over HTTPS | S3 API / pre-signed URLs |
| Run your own SFTP server | EC2 + EBS/EFS (you manage it, **not** the exam answer if "managed" is required) |

## Exam Tips

- "**SFTP/FTPS/FTP** access to **S3 or EFS**, **no server management**" → **AWS Transfer Family**.
- "**Fixed IP** so a partner can allow-list" → **VPC endpoint with Elastic IP** (+ security group).
- **FTP is unencrypted** and only available **inside a VPC**.
- Backends are **S3 and EFS only** (not EBS, not FSx).
- "Use existing **Active Directory** / **LDAP** credentials" → Directory Service or **custom identity provider** (Lambda/API Gateway).
- "**EDI / B2B** documents" → **AS2**.
- It is billed **per hour while the server is running**, even with no traffic.

Related: [S3](../S3/README.md), [EBS and EFS in Depth](../EC2/ebs-efs.md), [Snow Family](../SnowFamily/README.md), [Route 53](../Route53/README.md).
