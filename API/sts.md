# AWS STS (Security Token Service)

Exam-specific notes on **STS** — the service that vends **temporary, limited-privilege credentials**. Almost every "how do I get credentials without hard-coding access keys?" question resolves to STS.

## What STS issues

Temporary credentials are **three values + an expiry**, not two:

| Part | Example | Notes |
|---|---|---|
| Access key ID | `ASIAIOSFODNN7EXAMPLE` | Starts with **`ASIA`** (long-term IAM user keys start with `AKIA`) |
| Secret access key | `wJalrXUtnFEMI/...` | Signs the request (SigV4) |
| **Session token** | long base64 blob | **Required with every request**; SDKs/CLI send it automatically (`x-amz-security-token`) |
| Expiration | timestamp | Credentials **cannot be renewed** — call STS again to get fresh ones |

- Raw HTTP clients must send the session token explicitly; forgetting it produces `403` / auth errors even with correct keys.
- Expired credentials fail with `ExpiredToken`; clock skew produces `RequestExpired`/signature errors.
- STS is a **global service**, but AWS recommends the **regional endpoints** (`sts.<region>.amazonaws.com`) over the legacy global one (`sts.amazonaws.com`, pinned to us-east-1) for latency and resilience.

## The API calls you must know

| API | Who calls it | Use case (exam trigger) |
|---|---|---|
| **`AssumeRole`** | IAM user/role/app | **The workhorse.** Cross-account access, EC2/Lambda/ECS roles, CLI profiles, role chaining. Needs `sts:AssumeRole` permission in the caller **and** a trust policy on the target role. |
| **`AssumeRoleWithSAML`** | Enterprise IdP / user | **SAML 2.0 federation**: AD FS, Okta, Azure AD, Ping → console or API access. **No AWS credentials required to call it.** |
| **`AssumeRoleWithWebIdentity`** | Web/mobile app, CI | **OIDC/web identity federation**: Cognito, Google/Facebook, GitHub Actions, EKS IRSA. **No AWS credentials required to call it.** |
| **`GetSessionToken`** | IAM user | Get temp credentials **for MFA-protected API calls** (also used to hand MFA-verified creds to a script). |
| **`GetFederationToken`** | IAM user ("custom identity broker") | Federation when you *cannot* use SAML/OIDC: your own login portal authenticates users, then calls STS. |
| **`GetCallerIdentity`** | Anyone | Returns account ID + ARN of the caller; **needs no permissions** — the debugging/identity check. |
| **`DecodeAuthorizationMessage`** | Anyone with the permission | Decodes the opaque encoded message in an `AccessDenied` error. |

## `AssumeRole` in detail

A role has **two policies**, and the exam loves testing which is which:

- **Trust policy** (resource-based, on the role) — *who may assume it*. `Principal` must be an **account, role, user, federated principal or service** — not an arbitrary "permissions" statement.
- **Permissions policy** (identity-based, attached to the role) — *what the session may do*.

Cross-account flow: (1) the **target** role's trust policy allows the source account/role; (2) the **source** identity policy allows `sts:AssumeRole` on the role ARN. Both sides are required.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::111122223333:root" },
    "Action": "sts:AssumeRole",
    "Condition": { "StringEquals": { "sts:ExternalId": "unique-per-customer-id" } }
  }]
}
```

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::111122223333:role/ReadOnly \
  --role-session-name my-app-session \
  --duration-seconds 3600
```

Key knobs and traps:

- **`DurationSeconds`** — default **1 hour** (3600 s). Max is the role's **`MaxSessionDuration`** (1–12 h). You cannot request longer than the role allows.
- **Role chaining** (using role A's temporary credentials to assume role B) caps the session at **1 hour**, regardless of `MaxSessionDuration` — a classic trap.
- **`RoleSessionName`** is required; it appears in CloudTrail as `arn:aws:sts::<account>:assumed-role/<RoleName>/<session-name>` — this is how you audit *who* used the role.
- **Session policies** (passed to `AssumeRole`) can only **narrow** permissions — the effective permissions are the **intersection** of the role's identity policy and the session policy. They can never grant more.
- **Session tags** (`--tags`) flow into `aws:PrincipalTag` conditions (ABAC); `TransitiveTagKeys` carries them through role chaining.
- **MFA**: require it in the trust policy with `aws:MultiFactorAuthPresent` (optionally `aws:MultiFactorAuthAge`); get the MFA-verified token via `GetSessionToken` (or an MFA-conditional `AssumeRole`).
- **External ID**: the anti-**confused-deputy** control for third-party/SaaS access — the customer's unique ID is baked into the trust policy condition and passed by the vendor on `AssumeRole`.

## Federation: pick the right API

| Scenario | Answer |
|---|---|
| Corporate employees use **AD FS / Okta / Azure AD** to sign in | **SAML 2.0 → `AssumeRoleWithSAML`** (or **IAM Identity Center**, which wraps federation + permission sets) |
| Mobile/web app users sign in with **Google/Facebook/Apple/any OIDC** | **Cognito Identity Pools** → `AssumeRoleWithWebIdentity` |
| **GitHub Actions / GitLab CI / any OIDC CI** needs AWS access with no stored secrets | **`AssumeRoleWithWebIdentity`** with the CI provider as OIDC IdP |
| Custom login portal / legacy IdP that can't do SAML/OIDC | **`GetFederationToken`** (custom identity broker) |
| One AWS account needs to act in **another account** | **`AssumeRole`** + trust policy + `sts:AssumeRole` permission |
| EC2/Lambda/ECS application needs credentials | **IAM role** — the platform calls STS and rotates credentials for you (IMDS/credential provider) |
| You need the current account ID / identity | **`GetCallerIdentity`** |

## Duration limits (memorize the odd ones)

| Credential | Default | Maximum |
|---|---|---|
| `AssumeRole` | 1 h | **12 h** (role's `MaxSessionDuration`) |
| `AssumeRole` **chained** | 1 h | **1 h** (hard cap) |
| `AssumeRoleWithSAML` / `WithWebIdentity` | 1 h | **12 h** (role's `MaxSessionDuration`) |
| `GetSessionToken` (IAM user, MFA) | 12 h | **36 h** (root user: **1 h**) |
| `GetFederationToken` | 12 h | **36 h** (root user: **1 h**) |
| IAM role credentials on EC2/Lambda/ECS | auto-rotated | role max, refreshed before expiry |

The **minimum** for every call is **15 minutes** (900 s).

## What each kind of temporary credential can't do

| Credentials from | Restrictions |
|---|---|
| `GetSessionToken` | Cannot call **IAM** APIs unless MFA was included; cannot call STS except `AssumeRole` and `GetCallerIdentity` |
| `GetFederationToken` | Cannot call **IAM** APIs; cannot call STS except `GetCallerIdentity` (so **no `AssumeRole`**) |
| `AssumeRole*` | Limited to the role's permissions ∩ session policy; can assume other roles (role chaining, 1 h cap) |

## Exam traps

- Temporary credentials are **not renewable** — re-call STS (SDKs refresh automatically; hand-rolled HTTP code must too).
- `AssumeRoleWithSAML` / `AssumeRoleWithWebIdentity` **do not need AWS credentials** to call — that is the point of federation.
- `GetFederationToken` credentials are limited to the **intersection** of the calling IAM user's permissions and the session policy — they can never exceed the caller, and they **cannot be used to assume another role**.
- **Root user credentials cannot call `AssumeRole`** at all — it must be called by an IAM user or role (and root should have no access keys anyway).
- A trust policy with `Principal: arn:aws:iam::<account>:root` does **not** mean "only the root user": it trusts the **whole account**, delegating to that account's IAM policies who may actually call `sts:AssumeRole`.
- Cross-account questions require **both** the trust policy and the caller's identity permission — forgetting one is the standard wrong answer.
- IAM Identity Center is a **front-end for workforce SSO** that uses STS underneath — not a replacement API call.
- The **`ASIA` prefix** on an access key ID tells you it is temporary; `AKIA` means a long-term IAM user key (likely to be flagged in a "stolen credentials" question).

## Exam mapping (quick)

| Question phrasing | Answer |
|---|---|
| "Give an on-premises server/app temporary AWS credentials without storing long-term keys" | **IAM Roles Anywhere** (X.509 certificate from your PKI → `CreateSession` → role credentials); for humans, **IAM Identity Center** |
| "Third-party vendor accesses our account; prevent confused deputy" | `AssumeRole` + **`sts:ExternalId`** |
| "Employees sign in with corporate AD and get AWS console access" | **SAML 2.0** (`AssumeRoleWithSAML`) / **IAM Identity Center** |
| "Mobile app users authenticate with Google and upload to S3" | **Cognito Identity Pools** (`AssumeRoleWithWebIdentity`) |
| "CI pipeline needs AWS access with no long-lived secrets" | OIDC + `AssumeRoleWithWebIdentity` |
| "API calls must require MFA for sensitive actions" | `GetSessionToken` / `AssumeRole` + `aws:MultiFactorAuthPresent` condition |
| "Role session expires after 1 hour even though max is 12 h" | **Role chaining** cap — assume the role again to refresh |
| "Restrict an assumed role further per request" | **Session policies** (intersection, never expansion) |
| "Which account am I in / which identity is this key?" | `aws sts get-caller-identity` |

## References

- AWS STS API reference: https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html
- Temporary credentials (IAM User Guide): https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html
- AssumeRole: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
- SAML federation: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_saml.html
- Web identity federation: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc.html
- Course video: https://www.youtube.com/watch?v=c3Cn4xYfxJY
