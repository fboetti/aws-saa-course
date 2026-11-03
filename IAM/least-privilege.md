# Principle of Least Privilege (PoLP)

Grant **only the permissions required to do the task, to only the identities that need them, for only as long as needed**. It is the first principle of the AWS Well-Architected **Security pillar** ("implement a strong identity foundation") and the default tie-breaker on SAA-C03 security questions.

## The five dimensions

| Dimension | Tighten by |
|---|---|
| **What** (actions) | List specific actions, not `service:*` or `*` |
| **Where** (resources) | Specific ARNs, not `"Resource": "*"` |
| **When / how** (conditions) | `aws:SourceIp`, `aws:SourceVpce`, `aws:MultiFactorAuthPresent`, `aws:RequestedRegion`, `aws:PrincipalOrgID`, time windows |
| **Who** (principals) | Specific roles/accounts, not `"Principal": "*"` |
| **How long** | Temporary credentials (roles, STS, Identity Center) instead of long-term keys |

## Too broad vs least privilege

```json
// Too broad
{ "Effect": "Allow", "Action": "s3:*", "Resource": "*" }

// Least privilege
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::reports-bucket/2026/*",
  "Condition": { "Bool": { "aws:SecureTransport": "true" } }
}
```

## How to get there in practice

1. **Start small** — begin with no or minimal permissions and add on `AccessDenied`, instead of starting at admin and trimming.
2. **Use AWS managed policies to start**, then move to [customer managed policies](policies.md) scoped to your resources.
3. **Generate policies from activity** — IAM Access Analyzer *policy generation* reads CloudTrail and drafts a least-privilege policy.
4. **Remove what's unused** — [Access Advisor](monitoring-auditing.md) (service last accessed), Access Analyzer *unused access* findings, [credential report](monitoring-auditing.md) for stale users/keys.
5. **Validate** — Access Analyzer policy validation and the IAM Policy Simulator before deploying.
6. **Use guardrails** — [permission boundaries and SCPs](permission-boundaries-scps.md) cap the maximum even if someone writes a broad policy.
7. **Scale with tags** — [ABAC](abac.md) keeps policies narrow without one policy per resource.
8. **Review regularly** — remove permissions, roles and keys that are no longer used.

## Tool cheat sheet

| Goal | Tool |
|---|---|
| Which services has this identity actually used? | **Access Advisor** |
| Draft a policy from real usage | **Access Analyzer policy generation** |
| Find unused roles/keys/permissions | **Access Analyzer unused access**, credential report |
| Find resources shared externally | **Access Analyzer external access** |
| Test allow/deny without running it | **Policy Simulator** |
| Check policy syntax and risky grants | **Access Analyzer policy validation** |
| Cap what delegated admins can create | **Permission boundary** |
| Cap what whole accounts can do | **SCP** |

## Related patterns

- **Separation of duties** — different roles for deploy, audit and admin; no single identity does everything.
- **Break-glass** — a tightly monitored emergency admin role/user with MFA, used rarely, alarmed on use.
- **Roles per workload** — one role per application/function rather than one shared role.
- **Just-in-time access** — short session durations, assume-role on demand.
- **Service-specific controls** — S3 Block Public Access, VPC endpoint policies, KMS key policies, security groups reference SGs instead of CIDR ranges.

## JEA, JIT and Risk-Based Adaptive Access

Least privilege is not only *how much* access but also *how long* and *under what circumstances*. Three related ideas extend it:

| Concept | Idea | AWS building blocks |
|---|---|---|
| **JEA** — Just Enough Administration (a.k.a. just-enough access) | Give an admin/operator **only the specific tasks** they need, not full admin rights | Narrow customer managed policies, task-scoped roles, [permission boundaries](permission-boundaries-scps.md), session policies, Systems Manager Run Command / Automation runbooks (run a *specific* approved action instead of granting shell or admin access) |
| **JIT** — Just-In-Time access | Access is **granted on request, for a short time**, then expires automatically (no standing privilege) | `sts:AssumeRole` with short `DurationSeconds`, [IAM Identity Center](identity-center.md) permission sets with short session duration, time-boxed `aws:CurrentTime` conditions, SSM Session Manager, approval workflows (e.g. Identity Center + ticketing/Lambda/Step Functions, or "TEAM" temporary elevated access) |
| **Risk-based adaptive policies** | Access decisions **adapt to context and risk** (device, location, behaviour) rather than being a static yes/no | Policy **conditions** (`aws:SourceIp`, `aws:MultiFactorAuthPresent`, `aws:MultiFactorAuthAge`, `aws:RequestedRegion`, `aws:CurrentTime`, `aws:SecureTransport`), step-up MFA, Cognito **adaptive authentication** (risk scores for customer sign-ins), GuardDuty / Security Hub findings triggering automated response |

Note: "JEA" is originally a PowerShell/Microsoft term. AWS has no service called JEA; on the exam it appears as the idea of narrowly scoped, task-based permissions.

### JIT in practice

```
Engineer needs prod access
   → requests it (ticket / approval)
   → approver grants a time-boxed assignment (e.g. 1 h)
   → engineer assumes the role → temporary credentials
   → credentials expire; access is gone without anyone remembering to revoke it
```

- **No standing privilege**: normal day-to-day identity is read-only; elevated role is assumed only when needed.
- Role session duration: 15 min – 12 h (role chaining max 1 h). Choose the shortest that works.
- Every assumption is logged in CloudTrail (`AssumeRole`), which gives an audit trail for **break-glass** use.
- Example time-box condition:

```json
"Condition": {
  "DateGreaterThan": { "aws:CurrentTime": "2026-11-03T09:00:00Z" },
  "DateLessThan":    { "aws:CurrentTime": "2026-11-03T11:00:00Z" }
}
```

### Risk-based / adaptive access in practice

Static policy: "Alice can start instances." Adaptive policy: "Alice can start instances **only with MFA, from the corporate network, in approved regions, during business hours**."

```json
{
  "Effect": "Deny",
  "Action": "ec2:*",
  "Resource": "*",
  "Condition": {
    "BoolIfExists": { "aws:MultiFactorAuthPresent": "false" }
  }
}
```

- **Step-up authentication**: require recent MFA for sensitive actions with `aws:MultiFactorAuthAge` (seconds since MFA).
- **Cognito adaptive authentication** (Advanced security): scores each customer sign-in for risk and can allow, require MFA, or block. This is for *application users*, not AWS IAM identities.
- **Automated response**: GuardDuty finding → EventBridge → Lambda that attaches a deny policy, disables keys or revokes sessions.
- **Revoking active sessions**: in the console, "Revoke active sessions" adds an `aws:TokenIssueTime` deny, so temporary credentials issued before that moment stop working.

### Exam hints

- "No standing access / access only when needed / expires automatically" → **JIT** (temporary credentials via roles or Identity Center, short sessions).
- "Operators should perform only specific tasks, not be full admins" → **JEA / least privilege** (scoped policies, SSM Automation runbooks).
- "Require MFA or restrict by IP/time/region/device context" → **conditions** (adaptive/context-aware policy).
- "Risk-based sign-in for mobile/web app customers" → **Cognito adaptive authentication**.
- "Compromised role credentials already issued" → **revoke active sessions** (deny on `aws:TokenIssueTime`), not just detach the policy.

## Exam scenarios

| Question says… | Answer |
|---|---|
| "Grant the **minimum** permissions" / "least operational overhead **and** least privilege" | Scoped customer managed policy or role, not `AdministratorAccess` |
| "App needs read access to one bucket" | Role with `s3:GetObject`/`ListBucket` on that bucket's ARN only |
| "Find out which permissions the role really uses" | **Access Advisor** / **Access Analyzer policy generation** |
| "Developers may create IAM roles but must not become admins" | **Permission boundary** |
| "Stop all accounts from using unapproved regions" | **SCP** |
| "Contractor needs temporary access" | Role with short session duration (or Identity Center), not a user with keys |
| "Only requests from our VPC may read the bucket" | `aws:SourceVpce` / `aws:SourceVpc` condition |
| "Only with MFA" | `aws:MultiFactorAuthPresent` condition |
| "Access reviews find unused users" | Credential report → disable/delete |

## Traps

- `AdministratorAccess` or `*:*` is almost never the right answer, even when "it works".
- `"Resource": "*"` is acceptable only for actions that don't support resource-level permissions (e.g. `ec2:Describe*`).
- Least privilege is **not** the same as default deny: default deny is the starting state, least privilege is how you grant on top of it.
- SCPs and boundaries enforce least privilege by *capping*, but they never replace narrow identity policies.
- Sharing one role/credential across apps breaks both least privilege and auditability.
- Wildcards inside ARNs (`bucket/*`) are fine when scoped; wildcards in `Action` (`s3:*`) are the red flag.
