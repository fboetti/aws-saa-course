# AWS Access Keys (Programmatic Credentials)

Exam-focused notes on **access keys** — the long-term credentials that let applications, the AWS CLI and the SDKs call AWS service APIs.

## What is an access key?

An access key is a set of credentials used for **programmatic access only** (CLI, SDKs, direct API calls). It has two parts:

| Part | Example | Analogy | Visibility |
|---|---|---|---|
| **Access key ID** | `AKIAIOSFODNN7EXAMPLE` | username | Always visible; not secret (appears in logs, CloudTrail, code) |
| **Secret access key** | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | password | Shown **only once**, at creation; **cannot be recovered afterwards** |

- Requests are signed with **AWS Signature Version 4 (SigV4)**: the secret key signs the request, the service verifies it. The secret never travels over the wire.
- **Temporary credentials** add a third part: a **session token** (required with the key pair). Temporary key IDs start with **`ASIA...`**; long-term access key IDs start with **`AKIA...`** — a classic exam/lab hint about which kind of credential you are looking at.
- Access keys are **per IAM user** (or per role session / federated user), not per account, and are used **only for programmatic access** — the **AWS console** is entered with a username + password (+ MFA), never with an access key.

## Long-term vs temporary credentials

| | **Access keys** (IAM user) | **Temporary credentials** (STS / roles) |
|---|---|---|
| Lifetime | **Never expire** (until you delete them) | Minutes–hours (session duration), renewable |
| Where created | IAM console/CLI (`CreateAccessKey`) | **AWS STS**: `AssumeRole`, `GetSessionToken`, `AssumeRoleWithSAML/WebIdentity` |
| Pairs with | Access key ID + secret access key | Access key ID + secret access key + **session token** |
| Rotation/revocation | Manual (deactivate or delete the key) | Automatic expiry; just stop assuming the role |
| Best for | Legacy apps, CI systems that cannot use roles | Anything on AWS (EC2, Lambda, ECS, EKS) — the **recommended default** |

**Exam rule of thumb:** if the workload can assume a **role** (EC2 instance profile, Lambda execution role, ECS task role), it should — temporary credentials auto-expire, so a leaked credential goes dead by itself. Long-term access keys are the exception, not the norm.

## Limits and lifecycle (exam numbers)

- A user can have at most **2 active access keys** at a time (create a second, migrate, then deactivate/delete the first — that *is* the zero-downtime rotation procedure).
- The secret access key is displayed **only at creation**. Lost it? You cannot recover it — deactivate the key and create a new one.
- States: `Active` → `Inactive` (deactivated keys still count toward the 2-key limit) → deleted. **Deactivation is instant revocation** — the old key stops working immediately even though the application still has it.
- Root account can also have access keys — **best practice: root must have ZERO access keys**; use the root account only for tasks that genuinely require it (creating the first IAM user, closing the account, some billing/support actions).

## Best practices (the "secure default" list)

1. **No access keys for root** — ever.
2. **Prefer IAM roles** with temporary credentials (EC2, Lambda, ECS, CodeBuild, etc.) over IAM user keys.
3. If a user/CI system truly needs keys: **rotate regularly** (AWS Config rule `access-keys-rotated` flags keys older than a configurable threshold, default 90 days).
4. **Never commit keys to code** or bake them into AMIs/containers — use environment variables, `~/.aws/credentials`, or (better) instance/execution roles. This repo, for example, injects them as Gitpod environment variables instead of writing `~/.aws/credentials`.
5. **Least privilege**: attach a policy scoped to exactly the actions/resources the workload needs; add a **permissions boundary** for users who create their own keys.
6. **Watch the account**: alert on root-account usage and key creation (`iam` events in CloudTrail → CloudWatch alarms), and treat `CreateAccessKey`/`AttachUserPolicy` by non-admins as security events.
7. **Found a leaked key?** Deactivate/delete it **first**, rotate it, then investigate with **CloudTrail** (what did the key do?) — order matters: stop the bleeding before forensics.

## Detection and governance tools

| Tool | What it gives you |
|---|---|
| **AWS IAM Access Analyzer** | Flags **unused/external access** and generates least-privilege policies from CloudTrail activity |
| **Amazon GuardDuty** | Detects anomalous/unauthorized API use by credentials (`IAMAnomalousBehavior`, stolen-credential findings) |
| **AWS CloudTrail** | Records every API call, including which access key ID made it — the audit trail for "what did this key do?" |
| **AWS Config** | `access-keys-rotated`, `iam-user-mfa-enabled`, `iam-user-no-policies-check` conformance rules |
| **IAM Identity Center (SSO)** | Replaces long-lived IAM user keys for *humans* with temporary, SSO-brokered sessions |
| **Service control policies (SCPs)** | Organization-wide guardrail, e.g. deny `iam:CreateAccessKey` outside approved OUs, or deny actions when `aws:MultiFactorAuthPresent` is false |

## Exam mapping

| Question phrasing | Answer |
|---|---|
| EC2/Lambda/container needs to call other AWS services | **IAM role** (instance profile / execution role / task role), not access keys |
| Rotate an application's access key with no downtime | Create 2nd key → update app → **deactivate** old → delete old |
| A secret access key was committed to GitHub | Deactivate the key immediately, rotate, audit with **CloudTrail**, then fix the leak |
| Root account alert / "someone used root credentials" | Root should have **no access keys**; add CloudTrail→CloudWatch alarm on root usage; move work to IAM users/roles |
| Users repeatedly share/leak long-term credentials for human access | **IAM Identity Center (SSO)** + temporary sessions instead of IAM user keys |
| Enforce that API calls come only from MFA-verified sessions | IAM policy condition `aws:MultiFactorAuthPresent` (optionally combined with an SCP) |
| Find IAM users with stale (>90 days) keys | **AWS Config** rule `access-keys-rotated` |
| Credentials used from an unusual country/IP | **GuardDuty** credential anomalies → then revoke the key |

## Quick commands

```bash
# Who am I / which credential is being used?
aws sts get-caller-identity

# List a user's access keys and their status/age
aws iam list-access-keys --user-name alice

# Rotate: create a second key, then deactivate and delete the old one
aws iam create-access-key --user-name alice
aws iam update-access-key --user-name alice --access-key-id AKIA... --status Inactive
aws iam delete-access-key --user-name alice --access-key-id AKIA...

# Console password (for contrast: console = password, API = access key)
aws iam create-login-profile --user-name alice --password '...' --password-reset-required
```

## References

- Access keys (IAM User Guide): https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
- Root account best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- SigV4 signing: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv.html
- AWS STS: https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html
- IAM Access Analyzer: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY
