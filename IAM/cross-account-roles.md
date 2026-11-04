# Cross-Account Roles

A **role in Account B (trusting)** that principals from **Account A (trusted)** can assume to get **temporary credentials** in B. No IAM user or keys are created in B.

```
Account A (trusted)                         Account B (trusting)
 user/role ── sts:AssumeRole ─────────────► role "ReadProd"
   needs identity policy allowing           ├─ trust policy: trusts Account A
   sts:AssumeRole on B's role ARN           └─ permission policy: what it can do
                         ◄── temporary credentials (AccessKeyId, Secret, SessionToken)
```

## Both sides must allow

| Side | What is needed |
|---|---|
| **Account B** (role owner) | **Trust policy** naming Account A (or a specific principal) + **permission policy** on the role |
| **Account A** (caller) | **Identity policy** allowing `sts:AssumeRole` on the role's ARN (unless the trust policy names the exact principal, in which case same-account admin rules still apply to A's side) |

Trust policy in Account B:

```json
{
  "Effect": "Allow",
  "Principal": { "AWS": "arn:aws:iam::111111111111:role/DevOps" },
  "Action": "sts:AssumeRole",
  "Condition": { "Bool": { "aws:MultiFactorAuthPresent": "true" } }
}
```

Permission in Account A:

```json
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "arn:aws:iam::222222222222:role/ReadProd"
}
```

CLI:

```bash
aws sts assume-role --role-arn arn:aws:iam::222222222222:role/ReadProd --role-session-name alice
# or in ~/.aws/config
# [profile prod]
# role_arn = arn:aws:iam::222222222222:role/ReadProd
# source_profile = default
```

Console: **Switch Role** (account ID + role name).

## Key behaviour

- After assuming, you **give up** your original permissions and use the **role's** only.
- Session: default 1 h, up to 12 h (role `MaxSessionDuration`); **role chaining** capped at 1 h.
- Naming the Account A **root** in the trust policy means "any principal in A that A's admin allows".
- Named principal in the trust policy = tighter (only that user/role).
- CloudTrail logs the call in **both** accounts; session name identifies who.

## Third parties: External ID

For SaaS vendors, add `sts:ExternalId` to the trust policy to prevent the **confused deputy** problem:

```json
"Condition": { "StringEquals": { "sts:ExternalId": "unique-customer-id" } }
```

## Cross-account role vs resource-based policy

| | Assume a role | Resource-based policy |
|---|---|---|
| Identity used | **Role's** (caller's own permissions dropped) | Caller keeps **own** identity |
| Works for | Any service/API | Only services with resource policies (S3, SQS, SNS, KMS, Lambda…) |
| Typical use | Admin/ops access, deployments, audits | Share one bucket/queue/key |

## Common uses

- Central **security/audit** account reading all member accounts
- **CI/CD** account deploying to dev/test/prod accounts
- **Organizations**: `OrganizationAccountAccessRole` (created in new member accounts; the management account assumes it)
- Third-party monitoring/backup vendors
- Centralized logging, networking or shared-services accounts

## Exam tips

- "Access to resources in another account without creating users/keys" → **cross-account IAM role**.
- Needs a **trust policy** in the target account **and** `sts:AssumeRole` permission in the source account.
- "Third party needs access" → role + **External ID**.
- "Keep using own identity and permissions" → **resource-based policy**, not a role.
- "Restrict to org members" → `aws:PrincipalOrgID` condition in the trust policy.
- "Switch Role" is a console feature, `AssumeRole` is the API.

Related: [Identities](identities.md), [AWS STS](../API/sts.md), [Policy Evaluation](policy-evaluation.md), [Federation](federation.md).
