# ABAC — Attribute-Based Access Control

Authorize based on **tags** (attributes) instead of enumerating resources per identity.

| | RBAC (classic IAM) | ABAC |
|---|---|---|
| Model | Policy per job function | Policy per **attribute match** |
| New project/resource | Edit or add policies | **Just tag** the resource and principal |
| Policy count | Grows with resources | Small, stable |
| Risk | Policy sprawl | Tag governance (who may set tags?) |

## How it works

Match a tag on the **principal** with a tag on the **resource**:

```json
{
  "Effect": "Allow",
  "Action": ["ec2:StartInstances", "ec2:StopInstances"],
  "Resource": "arn:aws:ec2:*:*:instance/*",
  "Condition": {
    "StringEquals": { "aws:ResourceTag/Project": "${aws:PrincipalTag/Project}" }
  }
}
```

A user tagged `Project=Blue` can only start/stop instances tagged `Project=Blue`.

## Tag condition keys

| Key | Refers to |
|---|---|
| `aws:PrincipalTag/key` | Tag on the user/role making the call |
| `aws:ResourceTag/key` or `ec2:ResourceTag/key` | Tag on the target resource |
| `aws:RequestTag/key` | Tag passed in the create/tag request |
| `aws:TagKeys` | Which tag keys are in the request |

## Session tags and federation

- Pass **session tags** on `AssumeRole`/SAML/OIDC so corporate attributes (department, cost-center) become principal tags.
- IAM Identity Center can pass IdP attributes as principal tags (ABAC for workforce).

## Governance

- Restrict who can add/modify tags (`ec2:CreateTags`, `iam:TagUser`…), otherwise users can tag themselves into access.
- Use **tag policies** (Organizations) to standardise keys/values.
- Not every service/action supports tag-based authorization; check the service's "Actions, resources and condition keys" docs.

## Exam hints

- "Scale permissions as projects/teams grow without editing policies" → **ABAC**.
- "Fewer policies, tag-based" → ABAC; "job function" → RBAC.
