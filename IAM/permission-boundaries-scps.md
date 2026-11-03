# Permission Boundaries, SCPs and Session Policies

Three different guardrails that **limit** but never **grant**.

| | Permission boundary | SCP | Session policy |
|---|---|---|---|
| Scope | One IAM **user or role** | **Accounts / OUs** in an Organization | One **role session** or federated user |
| Set by | IAM admins in the account | Organization management account | Whoever calls AssumeRole / federation |
| Grants permissions? | No | No | No |
| Affects root user? | n/a | **Yes** (member accounts) | n/a |
| Affects management account? | n/a | **No** | n/a |
| Typical use | Delegate IAM admin safely | Account-wide guardrails (deny regions, services) | Per-session least privilege |

## Permission boundaries

A managed policy used as the **maximum** permissions for a user or role.

```
effective permissions = identity policy  ∩  boundary
```

Classic use case — **delegated administration**: let developers create roles/users, but only if the new identity has a boundary attached, so they can't escalate beyond it.

```json
{
  "Effect": "Allow",
  "Action": ["iam:CreateRole", "iam:AttachRolePolicy"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "iam:PermissionsBoundary": "arn:aws:iam::123456789012:policy/DevBoundary"
    }
  }
}
```

- Supported on **users and roles**, **not groups**.
- A boundary alone gives nothing.

## Service Control Policies (SCPs)

Part of **AWS Organizations**; apply to every principal in the target accounts (including each account's root).

- Attach to the **root**, an **OU** or an **account**; inherited down the tree.
- An action is allowed only if **every level** (root → OU → account) allows it.
- Default `FullAWSAccess` SCP is attached; remove it and you must allow explicitly (**allow-list**), or leave it and add **Deny** statements (**deny-list**, the common approach).
- **Do not** affect the management account, and do not affect **service-linked roles**.
- Require "All features" mode of Organizations.

Typical SCPs:

- Deny leaving the organization
- Deny all actions outside approved regions (`aws:RequestedRegion`)
- Deny disabling CloudTrail / GuardDuty
- Deny root user actions
- Require encryption or specific instance types

```json
{
  "Effect": "Deny",
  "NotAction": ["iam:*", "organizations:*", "support:*"],
  "Resource": "*",
  "Condition": { "StringNotEquals": { "aws:RequestedRegion": ["eu-west-1", "eu-central-1"] } }
}
```

## Resource Control Policies (RCPs)

Org-level guardrail on **resources** (e.g. S3, KMS, STS, SQS, Secrets Manager): cap what external principals can do to your resources, regardless of resource policies. Think "SCP for resources".

## Session policies

Passed as a parameter on `AssumeRole`, `AssumeRoleWithSAML`, `GetFederationToken` or the console federation URL. The session gets the **intersection** of the role's policies and the session policy.

## Putting it together

```
Org SCP        ──┐
Permission     ──┼─►  intersect  ─► what the identity can possibly do
 boundary        │                   (still needs an Allow in an identity/resource policy)
Session policy ──┘
```

## Exam traps

- "Prevent users from granting themselves admin" → **permission boundary** (and conditions on `iam:PermissionsBoundary`).
- "Restrict all accounts in the org from using a region/service" → **SCP**.
- SCPs don't give permissions — you still need IAM policies.
- SCP on the management account has **no effect**.
- Boundaries on **groups** don't exist.
