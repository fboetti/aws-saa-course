# AWS IAM — Theoretical Overview

Notes on **AWS Identity and Access Management (IAM)**, the service that decides **who** can do **what** on **which** resource. Follows the IAM section of the [freeCodeCamp AWS SAA course](https://www.youtube.com/watch?v=c3Cn4xYfxJY&t=63222s) (section starts around **17:33:42**), refined for the **SAA-C03** exam.

| Note | Read it for |
|---|---|
| **This page** | The whole IAM map: identities, policies, evaluation, federation, exam facts |
| [Identities: Users, Groups, Roles](identities.md) | Root user, IAM users, groups, roles, service-linked roles, instance profiles, trust policies |
| [Root User](root-user.md) | Root-only tasks, hardening checklist, SCP guardrail, compromise response, exam traps |
| [Cross-Account Roles](cross-account-roles.md) | Trust + permission policies, AssumeRole, External ID, role vs resource policy |
| [IAM Policies](policies.md) | Policy JSON anatomy, policy types, managed vs inline, identity vs resource-based, conditions |
| [Policy Evaluation Logic](policy-evaluation.md) | How AWS decides allow/deny: explicit deny, same- vs cross-account, the flowchart |
| [Permission Boundaries and SCPs](permission-boundaries-scps.md) | Guardrails that cap permissions: boundaries, SCPs, session policies and how they intersect |
| [ABAC and Tags](abac.md) | Attribute-based access control with tags vs classic RBAC |
| [MFA, Passwords and Credentials](mfa-passwords-credentials.md) | MFA types, password policy, access keys, credential report, rotation, root hardening |
| [Identity Federation](federation.md) | SAML, OIDC, Cognito, brokers, AD: how external identities get temporary credentials, with examples |
| [IAM Identity Center](identity-center.md) | Workforce SSO across accounts, permission sets, external IdPs |
| [Monitoring and Auditing](monitoring-auditing.md) | Credential report, Access Advisor, Access Analyzer, CloudTrail, policy simulator |
| [Least Privilege](least-privilege.md) | The principle in practice: scoping actions/resources/conditions, tools to get there, exam scenarios |
| [Exam Info and Tips](exam-tips.md) | Scenario → answer cheat sheet, traps, quick-fire facts |

Related notes elsewhere in this repo: [AWS STS](../API/sts.md), [Access Keys](../API/access-keys.md), [SigV4](../API/sigv4.md).

## What is IAM?

IAM is the **authentication and authorization** layer of every AWS account:

- **Authentication** — *who are you?* (password + MFA, access keys, temporary STS credentials)
- **Authorization** — *what may you do?* (policies attached to identities, resources, organizations)

Key properties:

- **Global service** — IAM is not tied to a region; users, groups, roles and policies exist account-wide and are replicated everywhere.
- **Free** — there is no charge for IAM itself (you pay for what the identities use).
- **Default deny** — a new identity can do nothing until a policy allows it.
- **Eventually consistent** — a change can take a few seconds to propagate; do not put IAM writes in a hot path.
- **Every request is checked** — console, CLI, SDK and service-to-service calls all go through IAM.

## The Building Blocks

```
AWS account
├── Root user                  all-powerful, email + password, lock it away
├── IAM users                  long-lived person/app identity (password and/or access keys)
│    └── IAM groups            collection of users; policies attach here (groups cannot nest)
├── IAM roles                  assumed identity with temporary credentials (no password/keys)
│    ├── trust policy          WHO may assume the role
│    └── permission policies   WHAT the role may do
└── IAM policies               JSON documents: Effect / Action / Resource / Condition
```

| Concept | One-liner |
|---|---|
| **Principal** | The entity making the request: root, user, role session, federated user, AWS service |
| **Identity-based policy** | Attached to a user/group/role: "this identity can do X" |
| **Resource-based policy** | Attached to a resource (S3 bucket, SQS queue, KMS key, role trust policy): "these principals can do X to me" |
| **Permission boundary** | Maximum permissions an identity may ever have (never grants by itself) |
| **SCP** | Organization-level maximum permissions for member accounts (never grants by itself) |
| **Session policy** | Inline filter passed when assuming a role/federating; narrows the session |
| **ARN** | `arn:partition:service:region:account-id:resource` — how policies name resources |

## Users vs Roles — the Core Decision

| | IAM user | IAM role |
|---|---|---|
| Credentials | Long-term (password, access keys) | **Temporary** (STS, 15 min – 12 h) |
| Belongs to | One person/app | Anyone/anything who assumes it |
| Typical use | Legacy / break-glass; humans should use Identity Center | EC2, Lambda, ECS, cross-account, federation |
| Exam preference | Avoid | **Preferred** |

> Exam rule of thumb: **"application on AWS needs access" → role; "other account needs access" → role; "employees sign in with corporate directory" → federation / IAM Identity Center; never embed access keys.**

## How a Request Is Authorized (short version)

1. Default is **deny**.
2. Any **explicit Deny** in any applicable policy → denied. Final.
3. Otherwise an **Allow** must exist in the identity-based or resource-based policy (same account) — and must **not** be blocked by an SCP, permission boundary or session policy.
4. No allow found → implicit deny.

Details and the cross-account variant: [Policy Evaluation Logic](policy-evaluation.md).

## Security Best Practices (also exam answers)

- **Lock down the root user**: strong password, **MFA**, no access keys, use only for the few root-only tasks.
- **Grant least privilege**; start from AWS managed policies, tighten with Access Analyzer / Access Advisor.
- **Use groups** to assign permissions to users; use **roles** for workloads and cross-account access.
- **Use temporary credentials** (roles, Identity Center) instead of long-term access keys.
- **Enable MFA** for all humans, especially privileged ones.
- **Rotate** credentials and **remove unused** users, keys and roles.
- Use **conditions** (`aws:SourceIp`, `aws:MultiFactorAuthPresent`, `aws:PrincipalOrgID`, …) to tighten policies.
- Use **SCPs** and **permission boundaries** as guardrails, **CloudTrail** for an audit trail.

## Topics Covered in the Course

> Outline of the IAM chapter as it maps to these notes (adjust to the exact video chapter titles if they differ).

1. IAM core concepts — root user, users, groups, roles → [Identities](identities.md)
2. IAM policies — structure, types, managed vs inline → [Policies](policies.md)
3. Policy evaluation and cross-account access → [Policy Evaluation](policy-evaluation.md)
4. Permission boundaries, SCPs → [Boundaries and SCPs](permission-boundaries-scps.md)
5. ABAC → [ABAC](abac.md)
6. MFA, password policy, credential report → [MFA and Credentials](mfa-passwords-credentials.md)
7. IAM Identity Center (SSO) → [Identity Center](identity-center.md)
8. Access Advisor, Access Analyzer → [Monitoring](monitoring-auditing.md)

## Exam Info (SAA-C03)

IAM is part of **Domain 1: Design Secure Architectures** (30 % of the exam) and is touched by almost every other domain.

Most-tested ideas:

- Roles over access keys (EC2 instance profile, Lambda execution role, cross-account `AssumeRole`).
- **Explicit deny always wins**; SCPs and boundaries only *limit*, never *grant*.
- Resource-based policies allow **cross-account** access without assuming a role.
- Root user: MFA, no keys, root-only tasks.
- IAM Identity Center for multi-account workforce access; Cognito is for *application customers*, not employees.
- Credential report (account-wide, CSV) vs Access Advisor (per-identity, last-accessed) vs Access Analyzer (external access findings).

More: [Exam Info and Tips](exam-tips.md).
