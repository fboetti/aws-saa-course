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

Account-wide settings for IAM users:

- Minimum length (6–128), require upper/lower/number/symbol
- Password expiration (up to 1095 days) and reuse prevention (last 1–24)
- Allow users to change their own password
- Require administrator reset after expiry

It does **not** apply to the root user.

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
