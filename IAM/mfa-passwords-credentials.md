# MFA, Passwords and Credentials

## Multi-Factor Authentication (MFA)

Something you **know** (password) + something you **have** (device).

| MFA type | Examples |
|---|---|
| **Virtual MFA** | Authy, Google Authenticator, 1Password (TOTP app) |
| **FIDO2 / passkey / security key** | YubiKey, Touch ID, Windows Hello |
| **Hardware TOTP token** | Gemalto token, SurePassID |

- Up to **8 MFA devices** per user/root (since 2022).
- Enforce with a policy condition: `"Bool": {"aws:MultiFactorAuthPresent": "true"}` (e.g. deny everything except `iam:*MFA*` until MFA is set).
- CLI with MFA: `aws sts get-session-token --serial-number <arn> --token-code <code>`.
- **MFA Delete** (S3 versioning) — enabled only by the bucket-owner **root**, via CLI.

## Password policy

An **account-wide** setting that defines the rules for **IAM user console passwords**. One policy per account (set in IAM → Account settings), applied to all IAM users.

| Setting | Options / range |
|---|---|
| Minimum length | **6–128** characters |
| Character types | Require uppercase, lowercase, number, non-alphanumeric symbol |
| Password expiration | Enable, **1–1095 days** |
| Expiration requires admin reset | Users can't set a new password after expiry; an admin must reset it |
| Allow users to change own password | Needs `iam:ChangePassword` too (the console option adds it) |
| Prevent password reuse | Remember the last **1–24** passwords |

CLI: `aws iam update-account-password-policy --minimum-password-length 14 --require-numbers --max-password-age 90 --password-reuse-prevention 12`.

### What it does and does not cover

| Covered | Not covered |
|---|---|
| IAM users' **console passwords** | **Root user** password |
| Users changing their password | **Access keys** (use rotation, not the policy) |
| | **MFA** (separate; enforce via policy conditions) |
| | Identity Center / federated / Cognito users (they have their own policies in their directory or user pool) |

### Behaviour worth knowing

- Changes apply to **new** passwords; existing passwords stay valid until they expire or are changed.
- Expired password → user must change it at next sign-in (unless "admin reset required" is on).
- Administrators can force a reset by setting **"user must create a new password at next sign-in"**.
- Without a custom policy, the AWS default applies (min 8 characters, at least 3 of the 4 character types, no expiry).
- Combine with **MFA** (the policy only raises password quality; it doesn't stop phished passwords).
- Reuse prevention and expiry are largely **legacy advice**; current guidance (NIST) favours **long passphrases + MFA** over frequent forced rotation.
- Audit with the [credential report](monitoring-auditing.md): `password_last_changed`, `password_next_rotation`, `password_last_used`. AWS Config rule `iam-password-policy` checks compliance.

### Exam hints

- "Enforce strong passwords / rotation for IAM users" → **IAM account password policy**.
- "Password policy for the root user" → **doesn't apply**; use MFA and a strong password.
- "Prevent users reusing old passwords" → **password reuse prevention** (1–24).
- "Force users to change password every 90 days" → **password expiration** (max 1095 days).
- "Check for compliance across accounts" → **AWS Config** managed rule `iam-password-policy`.
- "Passwords for employees" → better answer is often **Identity Center / federation with MFA**, not IAM users.

## Credential types and lifecycle

| Credential | Rotation / limits |
|---|---|
| Console password | Password policy |
| Access keys | Max **2**; rotate: create 2nd → switch apps → deactivate old → delete |
| MFA | Resync/replace device |
| Temporary STS creds | Auto-expire (15 min–12 h) |
| Root | MFA, no keys |

Key hygiene:

- Never commit keys to Git (use `git-secrets`, GitHub secret scanning; AWS auto-quarantines exposed keys with `AWSCompromisedKeyQuarantine`).
- Prefer roles / Identity Center / `aws configure sso`.
- Use Secrets Manager / SSM Parameter Store for third-party secrets.
- Deactivate unused credentials (see credential report).

See also [Access Keys](../API/access-keys.md).

## Access keys at a glance

Full notes (parts, limits, rotation, commands, exam mapping): **[Access Keys](../API/access-keys.md)**. The IAM-side summary:

| Fact | Detail |
|---|---|
| What | Long-term **programmatic** credentials: access key ID (`AKIA…`) + secret access key |
| Belongs to | An **IAM user** (or the root user, which you should never do) |
| Use | CLI / SDK / API only; **not** for the console |
| Limit | **2** keys per user; secret shown **once** |
| Expiry | **Never** (until deleted); temporary STS keys start with `ASIA…` and need a session token |
| Rotate | Create 2nd → switch app → **deactivate** old → verify → delete old |

### Prefer an alternative

| Instead of keys for… | Use |
|---|---|
| EC2 / Lambda / ECS / EKS workloads | **IAM role** (instance profile, execution role, task role, IRSA) |
| Human CLI access | **IAM Identity Center** (`aws configure sso`) or **CloudShell** |
| CI/CD (GitHub Actions, GitLab) | **OIDC provider + `AssumeRoleWithWebIdentity`** |
| On-premises servers | **IAM Roles Anywhere** (X.509 certificate → temporary credentials) |
| Third-party SaaS | Cross-account role + **External ID** |
| App secrets for other systems | **Secrets Manager** / SSM Parameter Store |

### Detection and response

- AWS scans public GitHub repos for exposed keys: it notifies you (AWS Health event) and may attach the **`AWSCompromisedKeyQuarantine`** policy (denies expensive actions such as launching EC2 or creating users/keys). The key is **not** deleted: you must.
- Response order: **deactivate the key → check CloudTrail** for what it did → rotate/delete → remove any resources or users the attacker created.
- Find stale keys with the [credential report](monitoring-auditing.md) (`access_key_1_last_used_date`, `access_key_1_last_rotated`) or the AWS Config rule `access-keys-rotated`.
- Block key creation org-wide with an SCP denying `iam:CreateAccessKey`.

### Exam hints

- "Application on EC2 needs AWS access" → **role**, never keys on disk or in user data.
- "Developer's keys were pushed to GitHub" → deactivate, rotate, review CloudTrail.
- "More than 2 keys needed?" → impossible: 2 per user; use roles.
- "Access key vs password" → keys = programmatic, password = console.
- "Key ID starts with ASIA" → temporary credentials (needs session token).

## Temporary security credentials

Short-lived credentials issued by **AWS STS**. Full details (API calls, durations, federation): **[AWS STS](../API/sts.md)**.

- Three parts: **access key ID (`ASIA…`) + secret access key + session token**. The token is mandatory on every request.
- **Expire automatically** (15 min – 12 h) and are **not stored** by AWS: once expired they cannot be reused or extended, you request new ones.
- Permissions come from the **role** (or the IAM user for `GetSessionToken`), optionally narrowed by a session policy.
- Never need rotation or cleanup, so a leak is time-limited: this is why they are the exam default.

| Source | API / mechanism | Typical use |
|---|---|---|
| IAM role on a service | Instance profile, Lambda execution role, ECS task role | AWS workloads |
| `AssumeRole` | Same or cross-account role | Admin elevation, cross-account |
| `AssumeRoleWithSAML` | SAML 2.0 IdP | Corporate federation |
| `AssumeRoleWithWebIdentity` | OIDC (Google, GitHub, EKS IRSA); Cognito identity pools | Web/mobile apps, CI/CD |
| `GetSessionToken` | IAM user (+ MFA) | MFA-protected CLI/API access |
| `GetFederationToken` | IAM user (custom broker) | Legacy federation proxy |
| IAM Identity Center | `aws sso login` | Human workforce access |

Quick facts:

- Role session default **1 h**; max set on the role (1–12 h); **role chaining** limited to **1 h**.
- `GetSessionToken` 15 min – 36 h (12 h default); root user limited to 1 h.
- Revoke early by denying on `aws:TokenIssueTime` ("Revoke active sessions" in the role).
- Calls are logged in CloudTrail as `AssumeRole…`; the session name identifies who assumed it.

**Exam hint:** "avoid long-term credentials / credentials that expire automatically / cross-account / federated users" → **temporary credentials via STS (role)**.

## Root account hardening checklist

- [x] MFA (hardware preferred)
- [x] No access keys
- [x] Strong unique password, shared mailbox for the email
- [x] Alternate contacts + billing alerts
- [x] Daily work through IAM Identity Center / IAM roles

## AWS CLI sign-in options

| Method | Command |
|---|---|
| Long-term keys | `aws configure` |
| Identity Center | `aws configure sso` → `aws sso login` |
| Assume role | profile with `role_arn` + `source_profile` |
| CloudShell | Uses console session credentials |

## Exam traps

- MFA cannot be "forced" by IAM alone — you enforce it with **conditions/deny policies**.
- Password policy ≠ root.
- "Lost access keys / compromised keys" → deactivate, rotate, check CloudTrail.
- "Programmatic access with MFA" → `GetSessionToken`.
