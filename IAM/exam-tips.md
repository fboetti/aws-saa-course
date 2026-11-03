# IAM — Exam Info and Tips (SAA-C03)

## Scenario → answer

| Scenario | Answer |
|---|---|
| EC2 app needs to read S3 | **IAM role via instance profile** (no keys) |
| Lambda needs to write to DynamoDB | Lambda **execution role** |
| Other AWS account needs access to my bucket | Bucket policy naming the account, or cross-account role |
| Grant access to a third party safely | Cross-account role with **External ID** |
| Employees SSO into many accounts | **IAM Identity Center** |
| Employees with corporate SAML IdP, one account | IAM SAML provider + role |
| Mobile app users sign in with Google/Facebook | **Amazon Cognito** |
| Prevent anyone in the org from using a region/service | **SCP** |
| Let devs create roles without escalating privilege | **Permission boundary** |
| Scale permissions by project/team tag | **ABAC** |
| Temporary elevated access for a user | `AssumeRole` / `GetSessionToken` with MFA |
| Users with no MFA / old keys | **Credential report** |
| Find permissions never used | **Access Advisor** |
| Find resources shared outside the org | **IAM Access Analyzer** |
| Root user best practice | MFA, no keys, minimal use |
| Credentials leaked in Git | Deactivate/delete keys, rotate, review CloudTrail |
| Restrict S3 to traffic from a VPC | `aws:SourceVpce` / `aws:SourceVpc` condition in bucket policy |
| Restrict API calls to corporate IP | `aws:SourceIp` condition |
| Force HTTPS to S3 | `aws:SecureTransport` deny |
| Only allow users in my Organization | `aws:PrincipalOrgID` |

Least privilege has its own note: [Principle of Least Privilege](least-privilege.md).

## Core rules to memorise

1. **Default deny → explicit deny wins → allow needed.**
2. SCPs, boundaries, session policies **limit**; only identity/resource policies **grant**.
3. **Roles over users over keys.** Temporary credentials always beat long-term.
4. IAM is **global**; roles, users, policies are not regional.
5. Groups: no nesting, not principals; boundaries: users/roles only.
6. Cross-account = trust policy + caller permission **or** resource policy + caller permission.
7. Management account is **not** affected by SCPs.
8. Resource-based policy needs `Principal`; identity-based doesn't.
9. Root-only tasks: close account, change support plan, restore IAM admin, S3 MFA delete…
10. Inline policies die with the identity; managed are reusable.

## Quick numbers

| Item | Value |
|---|---|
| Access keys per user | 2 |
| STS session duration | 15 min – 12 h (role chaining: 1 h) |
| Groups per user | 10 |
| MFA devices per user | 8 |
| Managed policies per identity | 10 (up to 20) |
| Managed policy size | 6,144 chars |
| Credential report refresh | every 4 h |
| Customer managed policy versions | 5 |
| Policy `Version` | `2012-10-17` |

## Common wrong-answer patterns

- Creating IAM users/keys for an application running on AWS.
- Using **Cognito** for employees or **Identity Center** for app customers.
- Believing an SCP can grant access.
- Putting `Principal` in an identity-based policy.
- Using IAM groups as a trust principal.
- Sharing the root credentials with admins.
- Attaching a boundary to a group.

## Related services (often paired with IAM in questions)

- **STS** — temporary credentials: [notes](../API/sts.md)
- **Organizations / Control Tower** — SCPs, multi-account governance
- **KMS** — key policies + grants
- **Cognito** — customer identity (user pools: authentication; identity pools: AWS credentials)
- **Directory Service** — Managed AD, AD Connector, Simple AD
- **Secrets Manager / SSM Parameter Store** — secrets instead of keys
- **CloudTrail / Config / GuardDuty** — audit & detection
