# IAM Identity Center (successor to AWS SSO)

Central **workforce** sign-on for many AWS accounts and business apps.

## AWS Single Sign-On (AWS SSO) in brief

**AWS SSO** is the former name of IAM Identity Center (renamed in **July 2022**). Old courses, videos and exam material may still say "AWS SSO"; it is the same service, and the CLI commands (`aws sso login`, `aws configure sso`, `aws sso-admin`) and the `awsapps.com/start` portal URL kept the old name.

**Single sign-on** means a user authenticates **once** with a central identity and then reaches many accounts and applications without signing in again.

```
User ─► sign in once (+ MFA) ─► access portal ─┬─► AWS account A (role: Admin)
                                               ├─► AWS account B (role: ReadOnly)
                                               └─► SAML apps (Salesforce, Slack, Microsoft 365…)
```

What it gives you:

- One login for **all AWS accounts in an Organization** plus **SAML 2.0 business apps**.
- Users and groups come from the built-in directory, **Active Directory**, or an **external IdP** (Okta, Entra ID, Google) via SAML + SCIM.
- Access is defined once as **permission sets** and assigned to users/groups per account; behind the scenes they become IAM roles with temporary credentials.
- Central off-boarding: disable the user in the directory and every account loses access.
- Free; requires AWS Organizations.

**Exam hint:** "single sign-on to multiple AWS accounts and applications" → **IAM Identity Center (formerly AWS SSO)**.

## Core ideas

| Term | Meaning |
|---|---|
| **Identity source** | Where users live: Identity Center directory (built-in), Active Directory (AWS Managed AD / AD Connector), or external IdP (Okta, Entra ID, Google) via SAML + SCIM |
| **User / group** | Identities in the source |
| **Permission set** | Template of IAM policies (AWS managed, customer managed, inline, boundary); Identity Center creates a **role** in each assigned account |
| **Assignment** | user/group + permission set + account(s) |
| **Access portal** | `https://<name>.awsapps.com/start` — one place to pick account and role |

```
Identity source ──► Identity Center ──► Assignment ──► role in Account A / B / C
(AD, Okta, …)        (permission sets)                   (temporary credentials)
```

## Key facts

- Requires **AWS Organizations**; enable it in the management account (delegated admin possible).
- Regional resource — pick one home region; users sign in anywhere.
- Gives **temporary credentials** — no IAM users or long-term keys.
- CLI: `aws configure sso`, `aws sso login --profile x`.
- Supports **MFA**, session duration (1–12 h), and **ABAC** with attributes from the IdP.
- Also grants access to SAML apps (Salesforce, Slack, custom) and EC2 Windows via SSO.
- Free.

## Federation options compared

| Need | Use |
|---|---|
| Employees → many AWS accounts, central | **IAM Identity Center** |
| Employees → single account, existing SAML IdP | IAM SAML identity provider + role |
| Mobile/web app customers sign in | **Amazon Cognito** (user pools + identity pools) |
| Kubernetes/GitHub Actions/OIDC workloads | IAM OIDC provider + `AssumeRoleWithWebIdentity` |
| Microsoft AD on AWS | AWS Managed Microsoft AD (+ trust) |

## Exam hints

- "Single sign-on across multiple accounts for workforce" → **IAM Identity Center**.
- "Customers of a mobile app" → **Cognito**, not Identity Center.
- Identity Center users get access via **permission sets**, which become roles.
- Avoid creating IAM users per account.
