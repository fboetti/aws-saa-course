# STS Lab — Assume a Role from the CLI

Hands-on companion to [AWS STS](../sts.md). Goal: start from an IAM user with **no permissions**, let it assume a role that can use S3, and see the difference between long-term (`AKIA…`) and temporary (`ASIA…`) credentials.

| File | What it does |
|---|---|
| [`template.yaml`](template.yaml) | CloudFormation stack: an S3 bucket + the role `StsRole` (trust policy + S3 permissions policy) |
| [`deploy-role`](deploy-role) | Deploys the stack (`CAPABILITY_NAMED_IAM` is required because the role has a fixed name) |
| [`policy.json`](policy.json) | Inline policy for the user: allows **only** `sts:AssumeRole` on `StsRole` |

Replace the account ID `719623059777` in `policy.json`, `template.yaml` and the commands below with yours (`aws sts get-caller-identity --query Account --output text`).

## 1. Create a user with no permissions and give it access keys

```bash
aws iam create-user --user-name sts-machine-user
aws iam create-access-key --user-name sts-machine-user --output table
```

The secret access key is shown **only now**. Store the pair in a dedicated profile:

```bash
aws configure --profile sts
```

The user has no policies, so every call is denied — but authentication works:

```bash
aws s3 ls --profile sts                    # AccessDenied: authenticated, not authorized
aws sts get-caller-identity --profile sts  # works: GetCallerIdentity needs no permissions
```

## 2. Create the role

```bash
./deploy-role
```

The stack creates `StsRole` with two policies — the distinction the exam tests:

- **Trust policy** (`AssumeRolePolicyDocument`) — *who may assume the role*. Its principal is `arn:aws:iam::719623059777:root`, which means **the whole account**, not the root user: any identity in the account whose own IAM policy allows `sts:AssumeRole` on this role can assume it.
- **Permissions policy** (`s3-access-policy`) — *what the session may do*: here all actions on S3 resources. Fine for a lab; in real life scope it to the actions you need (least privilege).

## 3. Allow the user to assume the role, then assume it

Trust policy alone is not enough — the caller needs permission too:

```bash
aws iam put-user-policy \
  --user-name sts-machine-user \
  --policy-name StsAssumePolicy \
  --policy-document file://policy.json

aws sts assume-role \
  --role-arn arn:aws:iam::719623059777:role/StsRole \
  --role-session-name s3-sts-fun \
  --profile sts
```

The output contains `AccessKeyId` (`ASIA…`), `SecretAccessKey`, `SessionToken` and `Expiration` (1 hour by default). Put them in `~/.aws/credentials` under a new profile — **all three values**, the session token is mandatory:

```ini
[assumed]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
```

```bash
aws sts get-caller-identity --profile assumed   # arn:aws:sts::…:assumed-role/StsRole/s3-sts-fun
aws s3 ls --profile assumed                     # now allowed
```

The ARN shows the **role name and the session name** — this is what CloudTrail records, and why `--role-session-name` matters for auditing.

**Shortcut** instead of copying credentials by hand: let the CLI assume the role (and refresh it) for you in `~/.aws/config`:

```ini
[profile assumed]
role_arn = arn:aws:iam::719623059777:role/StsRole
source_profile = sts
```

## 4. Clean up

```bash
# Empty the bucket first if you uploaded anything, then delete the stack (bucket + role)
aws cloudformation delete-stack --stack-name sts-aws-saa-course

# Remove the user: inline policy, access keys, then the user
aws iam delete-user-policy --user-name sts-machine-user --policy-name StsAssumePolicy
aws iam list-access-keys --user-name sts-machine-user
aws iam delete-access-key --user-name sts-machine-user --access-key-id AKIA...
aws iam delete-user --user-name sts-machine-user
```

Temporary credentials cannot be "deleted", but they are useless once the role is gone: permissions are evaluated on every request against the role's current policies. To cut off live sessions *without* deleting the role, use **Revoke active sessions** on the role in the IAM console (it adds a deny for tokens issued before now).
