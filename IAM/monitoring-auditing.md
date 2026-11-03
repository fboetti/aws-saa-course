# Monitoring and Auditing IAM

| Tool | Scope | Answers |
|---|---|---|
| **Credential report** | Account (CSV) | Which users have passwords/keys/MFA, when last used/rotated? |
| **Access Advisor** (last accessed) | One user/group/role/policy | Which services were actually used? → trim permissions |
| **Access Analyzer** | Account / Org | Which resources are shared **externally**? Unused access? Policy validation |
| **CloudTrail** | Account | Who called which API, when, from where |
| **Policy Simulator** | Policy | What-if testing of allow/deny |
| **AWS Config** | Resources | IAM config compliance rules (e.g. `iam-user-mfa-enabled`) |
| **Security Hub / GuardDuty** | Account | Findings on compromised credentials, anomalies |

## Credential report

- Account-level **CSV** listing all users and their credential status (password enabled, last used, last rotated, MFA, access keys 1/2 active, last used).
- Generated at most **once every 4 hours**.
- Great for finding unused credentials and missing MFA.

## Access Advisor

- Per-identity view of **service last accessed** (and actions for some services).
- Use it to **remove unused permissions** → least privilege.
- Data window: up to 400 days (tracking period).

## IAM Access Analyzer

- **External access findings**: S3 buckets, IAM roles, KMS keys, Lambda, SQS, Secrets Manager, etc. shared outside your **zone of trust** (account or organization).
- **Unused access findings**: unused roles, keys, permissions.
- **Policy validation** and **custom policy checks**.
- **Policy generation** from CloudTrail activity → builds a least-privilege policy.
- Free for external access (unused access analyzer is paid).

## CloudTrail

- IAM and STS events are in the **global** service events; logged in `us-east-1` for the global endpoint.
- Look for `ConsoleLogin`, `AssumeRole`, `CreateAccessKey`, `AttachUserPolicy`, `AccessDenied` error codes.
- Send to S3 + CloudWatch Logs; alert via EventBridge (e.g. root user login).

## Exam hints

- "Find users without MFA / old keys" → **credential report**.
- "Which permissions are unused?" → **Access Advisor**.
- "Is this bucket/role accessible from outside our org?" → **Access Analyzer**.
- "Who deleted this role?" → **CloudTrail**.
