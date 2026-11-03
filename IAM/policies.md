# IAM Policies

A policy is a **JSON document** that defines permissions. It does nothing until attached to an identity or resource.

## Anatomy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadReports",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::reports-bucket",
        "arn:aws:s3:::reports-bucket/*"
      ],
      "Condition": {
        "IpAddress": { "aws:SourceIp": "203.0.113.0/24" }
      }
    }
  ]
}
```

| Element | Meaning |
|---|---|
| `Version` | Always `2012-10-17` (the current language version; `2008-10-17` lacks policy variables) |
| `Statement` | One or more statements |
| `Sid` | Optional statement ID |
| `Effect` | `Allow` or `Deny` |
| `Principal` / `NotPrincipal` | Who — **only in resource-based policies** (and trust policies) |
| `Action` / `NotAction` | API operations (`service:Operation`, wildcards allowed) |
| `Resource` / `NotResource` | ARNs the action applies to |
| `Condition` | Extra requirements (IP, MFA, time, tags, org, region…) |

Notes:

- Bucket-level actions (`s3:ListBucket`) target the bucket ARN; object-level (`s3:GetObject`) target `bucket/*` — a classic mistake.
- Identity-based policies **omit** `Principal` (it is implied); resource-based policies **require** it.
- `NotAction` with `Allow` does **not** deny the rest — it allows everything *except* the listed actions.

## Policy types

| Type | Attached to | Grants? | Purpose |
|---|---|---|---|
| **Identity-based** | User, group, role | Yes | What the identity can do |
| **Resource-based** | Resource | Yes | Who can use the resource (incl. cross-account) |
| **Permission boundary** | User or role | No (limits) | Maximum an identity can get |
| **SCP** | Org / OU / account | No (limits) | Maximum for accounts in the org |
| **RCP** (resource control policy) | Org / OU / account | No (limits) | Maximum on resources in the org |
| **Session policy** | Passed on AssumeRole / federation | No (limits) | Narrows one session |
| **ACL** | Resource (S3, VPC NACL, WAF) | Yes (legacy) | Cross-account grants, not JSON policy |

## Identity-based policies: AWS managed vs customer managed vs inline

Three ways to package the same JSON permissions. "Managed" means the policy is a **standalone object with its own ARN** that you attach to many identities; "inline" means it is **embedded** in a single identity.

| | AWS managed | Customer managed | Inline |
|---|---|---|---|
| Created and maintained by | **AWS** | **You** | You |
| ARN | `arn:aws:iam::aws:policy/Name` | `arn:aws:iam::<account-id>:policy/Name` | None (not a standalone object) |
| Editable by you | **No** (read-only) | Yes | Yes |
| Reusable across identities | Yes (all accounts) | Yes (within your account) | **No** — strictly 1:1 |
| Attach to | Users, groups, roles | Users, groups, roles | The one user, group or role it lives in |
| Versioning | AWS updates it centrally; you can't roll back | Up to **5 versions**, set default/rollback | **None** |
| Updates propagate to attached identities | Yes, automatically (AWS may add permissions for new services) | Yes, when you change the default version | n/a |
| Deleted when the identity is deleted? | No | No (must detach, then delete) | **Yes** |
| Size limit | 6,144 chars | 6,144 chars | User 2,048 / group 5,120 / role 10,240 (total across all inline policies of that identity) |
| Best for | Quick start, broad job functions | Least-privilege, org-specific permissions | A permission that must never be reused or detached by mistake |
| Examples | `AdministratorAccess`, `ReadOnlyAccess`, `PowerUserAccess` | `S3-ReportsBucket-ReadOnly` | A one-off exception on a single role |

### Which to pick

- **AWS managed** — fastest, covers common cases, but often broader than needed (e.g. `AmazonS3FullAccess` covers every bucket). Good starting point; tighten later with [Access Advisor / Access Analyzer](monitoring-auditing.md).
- **Customer managed** — the default choice for real workloads: scoped to your resources, reusable, versioned, auditable ("who uses this policy?" is one console click).
- **Inline** — only when you need a strict 1:1 link, so the policy can't be attached to anything else and disappears with the identity. Also what you get from `put-user-policy` / `put-role-policy`.

Note: "managed policy" in exam wording usually means both AWS managed and customer managed together; "inline" is the contrast.

### Job-function managed policies worth knowing

`AdministratorAccess`, `PowerUserAccess` (everything except IAM and Organizations), `ReadOnlyAccess`, `SecurityAudit`, `ViewOnlyAccess`, `DatabaseAdministrator`, `NetworkAdministrator`.

## Resource-based policies

Examples: S3 bucket policy, SQS/SNS queue-topic policy, KMS key policy, Lambda resource policy, ECR repository policy, Secrets Manager resource policy, **role trust policy**.

- Can grant **cross-account** access directly.
- When a principal in the **same account** is named, identity *or* resource policy alone is enough.
- When **cross-account**, **both** sides must allow (caller's identity policy **and** the resource policy).
- KMS is special: the key policy is *required*; IAM policies only work if the key policy allows them (`kms:*` to the account root).

## Common condition keys

| Key | Use |
|---|---|
| `aws:SourceIp` | Restrict to CIDR ranges (public IPs only; not via VPC endpoints) |
| `aws:SourceVpc` / `aws:SourceVpce` | Restrict to a VPC / VPC endpoint |
| `aws:MultiFactorAuthPresent` | Require MFA |
| `aws:RequestedRegion` | Limit regions |
| `aws:PrincipalOrgID` | Allow anyone in the Organization |
| `aws:PrincipalTag/*`, `aws:ResourceTag/*`, `aws:RequestTag/*` | [ABAC](abac.md) |
| `aws:SecureTransport` | Force HTTPS |
| `aws:CurrentTime` | Time windows |
| `s3:x-amz-server-side-encryption` | Force encryption on upload |

Operators: `StringEquals`, `StringLike`, `ArnLike`, `IpAddress`, `NotIpAddress`, `Bool`, `DateGreaterThan`, `Null`, plus `ForAllValues` / `ForAnyValue` set modifiers.

## Policy variables

`${aws:username}` makes one policy per-user:

```json
"Resource": "arn:aws:s3:::company-home/${aws:username}/*"
```

## Limits worth remembering

- Managed policy size: **6,144** characters; inline: user **2,048**, group **5,120**, role **10,240** (total across the identity).
- Managed policies attached per identity: **10** by default (adjustable to 20).
- Trust policy size: 2,048 characters by default.

## Exam traps

- Policy **without** `Principal` in a bucket policy is invalid; with `Principal` in an identity policy is invalid.
- `"Principal": "*"` makes a resource public (watch S3 Block Public Access).
- Deleting a user deletes its inline policies but not managed ones (AWS or customer managed policies stay and can be re-attached).
- You can't edit an AWS managed policy; to change it, copy it into a customer managed policy.
- `Effect: Allow` + `NotResource` etc. often appears as a wrong answer choice for "least privilege".
