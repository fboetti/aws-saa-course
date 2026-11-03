# IAM Identities: Root, Users, Groups and Roles

## Root user

Created with the account; signs in with the **email + password** and has **unrestricted** access that **cannot be limited by IAM policies** (SCPs *can* restrict the root of a *member* account).

Best practice: enable **MFA**, delete/never create access keys, don't use for daily work, store credentials in a safe.

**Tasks that require root** (classic exam list):

- Change account settings (account name, email, root password, root access keys)
- Close the AWS account
- Change or cancel the AWS Support plan
- Restore IAM user permissions (when the last admin locked themselves out)
- Activate IAM access to the Billing console
- Enable MFA Delete on an S3 bucket (root of the bucket-owning account)
- Edit or delete an S3 bucket policy that denies all principals
- Register as a seller in the Reserved Instance Marketplace
- Configure an S3 bucket to enable MFA delete / sign up for GovCloud

## IAM users

An identity for **one person or application** with long-term credentials.

| Credential | Use |
|---|---|
| Console password | Sign in to the Management Console |
| Access keys (`AKIA…`) | CLI / SDK / API (max **2** per user) |
| MFA device | Second factor |
| SSH public keys / Git credentials | CodeCommit |

- Start with **no permissions** (implicit deny).
- Up to **5,000 users** per account (quota); **10 groups** per user.
- Prefer federation / Identity Center for humans; keep IAM users for edge cases (break-glass admin, third-party tools that cannot assume roles).

## IAM groups

A **collection of users** to attach permissions to in bulk.

- A group is **not an identity** — it cannot be a `Principal` in a policy and cannot be assumed.
- **No nesting** (groups cannot contain groups).
- A user can belong to **several** groups (up to 10); permissions are the **union**.
- Users need not belong to any group.
- Default quota: 300 groups per account.

## IAM roles

An identity with **permissions but no long-term credentials**. Anyone/anything trusted can **assume** it and receives **temporary credentials** from STS.

Two policy types make a role work:

| Policy | Question it answers |
|---|---|
| **Trust policy** (a resource-based policy on the role) | *Who* may assume this role? |
| **Permissions policy** | *What* may the role do once assumed? |

Example trust policy letting EC2 assume the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

### Who can assume a role

- AWS services (EC2, Lambda, ECS tasks, …) — **service roles**
- IAM users/roles in the **same** account
- Principals from **another** account (cross-account)
- Federated users (SAML 2.0, OIDC / web identity)

### Role flavours

| Type | Notes |
|---|---|
| **Service role** | Role a service assumes on your behalf (Lambda execution role, CodePipeline role) |
| **Service-linked role** | Predefined by the service, trust policy fixed, you can't edit permissions (e.g. `AWSServiceRoleForElasticLoadBalancing`); deleted via the service |
| **Instance profile** | Container that passes a role to an EC2 instance; console creates it automatically, CLI/CFN need it explicit |
| **Cross-account role** | Trust policy names the other account; both sides need permission |
| **Federated role** | Trust names a SAML/OIDC provider |

### Assuming a role

- API: `sts:AssumeRole` (also `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`).
- Returns `AccessKeyId`, `SecretAccessKey`, `SessionToken` valid **15 min – 12 h** (default 1 h; role-chaining capped at **1 h**).
- When you assume a role you **give up** your original permissions for that session and get the role's.
- Details: [AWS STS](../API/sts.md).

### EC2 and instance profiles

```
EC2 instance → instance profile → IAM role → temporary creds via IMDS (169.254.169.254)
```

- One role per instance profile; the credentials are rotated automatically.
- Use **IMDSv2** (session-token based) to blunt SSRF attacks.
- Never store access keys on the instance.

## Cross-account access: two ways

| Method | How | Caller keeps own permissions? |
|---|---|---|
| **Assume a role** in the target account | Trust policy + `sts:AssumeRole` permission on caller | No (uses role's) |
| **Resource-based policy** (S3, SQS, SNS, KMS, Lambda…) | Policy names the other account's principal | **Yes** |

## Exam traps

- Groups can't be nested and can't be principals.
- Roles don't have passwords or permanent keys.
- "Application on EC2 needs S3 access" → **instance profile role**, not keys.
- Service-linked roles can't be edited; you only delete them when the service no longer uses them.
- Root user cannot be restricted by IAM policies.
