# The AWS Account Root User

The identity created with the account, signed in with the **email address + password** used at sign-up. It has **complete, unrestricted access** to every service and resource in the account, including billing.

## Key facts

- **One root user per account** (each member account in an Organization has its own).
- **Cannot be limited by IAM policies**, permission boundaries, or deleted. In an Organization, **SCPs can restrict the root user of member accounts** (but not the management account).
- Not an IAM user: it doesn't appear in the IAM user list, and you can't attach IAM policies to it.
- Signs in on the **root user** option of the console sign-in page (not the IAM user option, which needs an account ID/alias).
- The email address is the account's recovery channel: use a **shared mailbox** you control (e.g. `aws-root@company.com`), not a person's inbox.
- Billing and Cost Management data is visible to root; IAM users need **IAM access to billing** activated (a root-only action) plus policies.

## Root-only tasks

Everything else should be done with IAM roles/Identity Center. Tasks that **require** root credentials (classic exam list):

- Change the account **name, email address or root password**
- Change or cancel the **AWS Support plan**
- **Close** the AWS account
- **Activate IAM access** to the Billing and Cost Management console
- **Restore IAM permissions** when the last IAM admin locked themselves out
- Create or edit **root access keys** (you shouldn't)
- Enable **MFA Delete** on an S3 bucket's versioning (configured with root credentials via CLI/API)
- **Edit or delete an S3 bucket policy** that denies all principals (lock-out recovery)
- Edit or delete an **SQS queue policy** or **Amazon SNS** topic policy that denies all principals
- Register as a seller in the **Reserved Instance Marketplace**
- Change the **CloudFront key pair** (legacy root-signed URLs)
- Sign up for **GovCloud**, certain tax/payment registrations and Outposts-related ordering

Memory hook: *account settings, billing/support, lock-out recovery, and a few legacy items.*

> Newer: with **centralized root access management** in AWS Organizations you can **remove root credentials from member accounts** and perform privileged root tasks (e.g. unlock a bucket policy, delete a bad SQS policy) from the management account through a short-lived **root session** (`sts:AssumeRoot`) without ever signing in as root.

## Hardening checklist

| Action | Why |
|---|---|
| Enable **MFA**, ideally hardware or FIDO2 passkey (up to 8 devices) | Single biggest protection |
| **Delete/never create root access keys** | Keys bypass the console MFA prompt and never expire |
| Long unique **password** in a password manager / vault | Root isn't covered by the IAM password policy |
| Use a **shared, monitored email** and keep **alternate contacts** current | Recovery and security notices |
| Create an **IAM Identity Center / IAM admin** for daily work | Root is for the root-only tasks above |
| Alarm on root usage (CloudTrail → EventBridge/CloudWatch → SNS) | Any root sign-in is unusual |
| In Organizations, apply an **SCP that denies root user actions** in member accounts | Guardrail |
| Check Trusted Advisor / Security Hub: "MFA on root account" | Continuous compliance |
| Store MFA devices and recovery info separately, with 2 people able to recover | Avoid lock-in to one person |

Detect root activity with a CloudWatch Events/EventBridge rule on CloudTrail `userIdentity.type = "Root"`, or AWS Config/Security Hub controls.

## SCP that blocks the root user in member accounts

```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": {
    "StringLike": { "aws:PrincipalArn": "arn:aws:iam::*:root" }
  }
}
```

(Doesn't apply to the management account.)

## Root vs admin IAM identity

| | Root user | IAM admin (`AdministratorAccess`) |
|---|---|---|
| Restrictable by IAM policy | **No** | Yes |
| Restrictable by SCP | Yes (member accounts) | Yes |
| Can do root-only tasks | **Yes** | **No** |
| Can be deleted/disabled | No | Yes |
| Recommended for daily use | **No** | Better: roles/Identity Center instead |

## If root credentials are compromised

1. Sign in (or recover through the email), **change the password** and **re-secure MFA**.
2. **Delete any root access keys**; check for new IAM users, roles, keys, and unexpected resources in **all regions**.
3. Review **CloudTrail** and billing; contact AWS Support.
4. Rotate credentials of anything the attacker could read (secrets, keys).

## Exam tips

| Question says… | Answer |
|---|---|
| "Most secure way to protect the root user" | **Enable MFA** and don't create access keys |
| "Daily administration of the account" | Create **IAM admin users/roles** (or Identity Center), not root |
| "Change AWS Support plan / close account" | **Root user** |
| "Enable MFA Delete on an S3 bucket" | **Root** of the bucket-owning account |
| "Bucket policy accidentally denies everyone" | Sign in as **root** to fix it (or root session via centralized root management) |
| "Last IAM admin locked out" | **Root** restores IAM permissions |
| "Restrict what the root user can do" | **SCP** (member accounts only); IAM policies can't |
| "Does an SCP affect the management account's root?" | **No** |
| "Where do I get root access keys?" | Don't: "best practice is to have none" |
| "Alert when root logs in" | **CloudTrail + EventBridge/CloudWatch alarm → SNS** |
| "Multiple accounts, reduce root risk" | Organizations **centralized root access** (remove member-account root credentials) |

### Traps

- **IAM policies cannot restrict root.** Only SCPs (and only in member accounts).
- Root ≠ an IAM user with `AdministratorAccess`: some tasks are root-only.
- The **IAM password policy does not apply** to root.
- "Share the root password with the admin team" is always wrong; create individual identities.
- Root MFA is protected by AWS but **don't** tie it to one person's phone with no recovery.
- The account **root user email** is not the same as the **IAM user** sign-in; IAM users sign in with account ID/alias.

Related: [Identities](identities.md), [MFA and Credentials](mfa-passwords-credentials.md), [Permission Boundaries and SCPs](permission-boundaries-scps.md), [Monitoring and Auditing](monitoring-auditing.md).
