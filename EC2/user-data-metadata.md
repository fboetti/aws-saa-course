# User Data and Instance Metadata

## User Data

- Script/cloud-init config passed at launch to **bootstrap** an instance (install packages, start services, pull code). Can be a bash scriptp or a yaml file.
- Runs **once at first boot** by default, as **root**. Can be configured to run on every boot (cloud-init settings / `#cloud-boothook`).
- Limit **16 KB** (raw, before base64).
- Editable only when the instance is **stopped**; take effect on next boot if set to rerun.
- Visible via metadata (`/latest/user-data`) → **never put secrets** in it.

```bash
#!/bin/bash
dnf update -y
dnf install -y httpd
systemctl enable --now httpd
echo "Hello from $(hostname -f)" > /var/www/html/index.html
```

Long user data slows launch → prefer a **pre-baked AMI** for heavy setup.

## Instance Metadata Service (IMDS)

- Available **inside** the instance at `http://169.254.169.254/latest/meta-data/` (IPv6: `fd00:ec2::254`).
- Provides: instance ID, type, AMI ID, AZ, local/public IPs, security groups, IAM role credentials (`iam/security-credentials/<role>`), tags (if enabled), user data.
- Not encrypted, no auth beyond local access; **not** metadata about the instance's own data/OS.

### IMDSv1 vs IMDSv2

| | IMDSv1 | IMDSv2 |
|---|---|---|
| Method | Simple GET | Session token (PUT then GET with header) |
| SSRF protection | Weak | Strong (token required, hop limit 1) |

```bash
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id
```

- **Enforce IMDSv2** (`HttpTokens=required`) via launch template/account default. Containers may need hop limit 2.

## Tags

- Key/value labels for cost allocation, automation, ABAC ([ABAC](../IAM/abac.md)).
- Can be exposed in IMDS if enabled.

## Exam Tips

- "Run a script at first launch" → user data.
- "Instance needs to know its own IP/AZ" → metadata endpoint.
- "Reduce SSRF credential theft risk" → require IMDSv2.
