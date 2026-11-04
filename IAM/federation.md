# Identity Federation

**Federation** = trusting an **external identity provider (IdP)** to authenticate users, then giving them **temporary AWS credentials** (through a role) instead of creating an IAM user for each person. AWS never sees the user's password; it trusts a signed assertion/token from the IdP.

```
User ──► IdP (Okta, Entra ID, AD FS, Google, GitHub…) ──► assertion / token / JWT
                                                              │
                         AWS STS (AssumeRoleWith…) ◄──────────┘
                                │
                      temporary credentials (role) ──► AWS APIs / console
```

Why: no per-user IAM users or keys, single place to disable a leaver, MFA and password rules live in the IdP, credentials expire on their own.

## The federation options

| Option | Protocol | Who it is for | STS call |
|---|---|---|---|
| **IAM Identity Center** | SAML 2.0 / SCIM / AD | Workforce → many accounts and apps | Managed for you (permission sets → roles) |
| **IAM SAML identity provider** | SAML 2.0 | Workforce → a single account/few roles | `AssumeRoleWithSAML` |
| **IAM OIDC identity provider** | OpenID Connect | Workloads/CI (GitHub Actions, GitLab, EKS service accounts) | `AssumeRoleWithWebIdentity` |
| **Amazon Cognito** | User pools (OIDC/SAML/social) + identity pools | Customers of your web/mobile app | Identity pool calls `AssumeRoleWithWebIdentity` for you |
| **Custom identity broker** | Your own code | Legacy IdP that can't do SAML/OIDC | `AssumeRole` / `GetFederationToken` |
| **AWS Directory Service** | Managed AD / AD Connector | Windows/AD shops; EC2 domain-join, SSO | Via Identity Center or AD trust |

## Example 1: Corporate SAML federation (Okta / Entra ID / AD FS)

Setup:

1. In the IdP, create an AWS application; download its **SAML metadata XML**.
2. In IAM, create an **identity provider** (type SAML) and upload the metadata.
3. Create a **role** whose trust policy trusts the SAML provider:

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::123456789012:saml-provider/Okta" },
  "Action": "sts:AssumeRoleWithSAML",
  "Condition": { "StringEquals": { "SAML:aud": "https://signin.aws.amazon.com/saml" } }
}
```

4. In the IdP, map groups/attributes to the role ARN + provider ARN (the `https://aws.amazon.com/SAML/Attributes/Role` attribute).

Flow: user logs in to the IdP → IdP posts a **SAML assertion** to `https://signin.aws.amazon.com/saml` → AWS calls `AssumeRoleWithSAML` → user lands in the console (or the CLI gets credentials).

Better today: connect the same IdP to **IAM Identity Center** so you also get multi-account permission sets and the access portal.

## Example 2: GitHub Actions to AWS with OIDC (no stored keys)

Create an OIDC provider for `token.actions.githubusercontent.com`, then a role:

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
    "StringLike":   { "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:ref:refs/heads/main" }
  }
}
```

Workflow step: `aws-actions/configure-aws-credentials` with `role-to-assume`. The `sub` condition is the important security control: without it any repo could assume the role.

## Example 3: Mobile app users with Cognito

- **User pool**: sign-up/sign-in directory that returns JWT tokens (also federates Google, Facebook, Apple, SAML, OIDC).
- **Identity pool**: exchanges a user-pool (or social) token for **temporary AWS credentials** mapped to an *authenticated* role (and optionally a *guest/unauthenticated* role).

```
App ──login──► Cognito User Pool ──JWT──► Cognito Identity Pool ──► STS ──► temp creds ──► S3 / DynamoDB
```

Typical use: each signed-in user uploads to `s3://bucket/${cognito-identity.amazonaws.com:sub}/*` (policy variable restricts them to their own prefix).

## Example 4: Custom identity broker

A company portal authenticates users against its own directory, then calls `sts:AssumeRole` (or `GetFederationToken`) with the broker's IAM credentials and returns a **console sign-in URL** or credentials to the user. Used only when SAML/OIDC isn't possible.

## Example 5: Microsoft Active Directory

- **AWS Managed Microsoft AD**: real AD in AWS; can trust on-prem AD; used with Identity Center or domain-joined EC2/RDS.
- **AD Connector**: proxy to on-prem AD, no data stored in AWS.
- **Simple AD**: basic Samba-based, no trust.

## Security details to know

- Federated principals appear in policies as `"Principal": {"Federated": "..."}` in the **trust policy**; the role's permission policy defines what they can do.
- Pass **session tags** from SAML/OIDC attributes to enable [ABAC](abac.md).
- Narrow a session further with a **session policy**.
- Restrict who may assume the role with conditions on `SAML:` / provider-specific claims (`sub`, `aud`, `amr`).
- Session duration: 1 h default, up to 12 h; users re-authenticate with the IdP afterward.
- All activity is in CloudTrail with the federated user/session name.

## Choosing quickly

| Scenario | Use |
|---|---|
| Employees, many accounts, SSO | **IAM Identity Center** |
| Employees, one account, existing SAML IdP | **IAM SAML provider + role** |
| App customers / social login | **Cognito** |
| CI/CD (GitHub, GitLab, Bitbucket) | **OIDC provider + role** |
| Kubernetes pods on EKS | **IRSA** / EKS Pod Identity |
| Legacy non-SAML directory | **Custom identity broker** |
| Corporate AD in the cloud | **Managed AD / AD Connector** |
| On-prem servers, no IdP | **IAM Roles Anywhere** |

## Exam tips

- "Users already exist in a corporate directory, avoid creating IAM users" → **federation** (SAML 2.0 or Identity Center).
- "Millions of mobile users, social login" → **Cognito**, not IAM users.
- "Sign-in with SAML" → trust policy on the role + `AssumeRoleWithSAML`.
- "GitHub Actions without storing keys" → **OIDC + `AssumeRoleWithWebIdentity`**.
- "Identity broker/legacy IdP" → `GetFederationToken` or `AssumeRole`.
- Federation gives **temporary credentials**; it never creates IAM users.
- Cognito **user pools** authenticate; **identity pools** authorize with AWS credentials.

Related: [Identity Center](identity-center.md), [AWS STS](../API/sts.md), [Identities](identities.md).
