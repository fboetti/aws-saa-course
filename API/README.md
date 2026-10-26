# AWS API — Theoretical Overview

Notes on accessing AWS services through the API: credentials, signing and the tools that talk to it (CLI, SDKs). Hands-on CLI/SDK material for S3 lives in [`../S3/`](../S3/README.md).

Every AWS action — a console click, a CLI command, an SDK call, a CloudFormation deploy — ends up as a **signed HTTPS request to a service API endpoint**. Four questions decide whether it succeeds:

1. **Which credentials?** Long-term [access keys](access-keys.md) (`AKIA…`) or temporary [STS credentials](sts.md) (`ASIA…` + session token).
2. **Is the request authentic?** It must carry a valid [SigV4 signature](sigv4.md), scoped to date, region and service.
3. **Is it authorized?** IAM evaluates the identity, resource, session and organization policies (explicit deny wins).
4. **What if the service pushes back?** Throttling and transient errors are retried with [exponential backoff and jitter](exponential-backoff.md).

## Contents

- [Access Keys](access-keys.md) — long-term programmatic credentials: parts, limits (2 per user), rotation, root keys, temporary credentials vs access keys, and the exam mapping.
- [AWS STS](sts.md) — temporary credentials: AssumeRole, SAML/web identity federation, GetFederationToken, session policies/tags, durations and the cross-account traps.
- [SigV4 Signing](sigv4.md) — how requests are signed: canonical request, credential scope, presigned URL limits, payload hashing and the auth-error traps.
- [Exponential Backoff](exponential-backoff.md) — retrying throttled/failed API calls with doubling waits plus jitter, and which errors are safe to retry.
- [STS hands-on lab](sts/readme.md) — create a permission-less user, deploy a role with CloudFormation and assume it from the CLI.

## How credentials are found (CLI and SDKs)

The CLI and SDKs look for credentials in a fixed order and use the **first** they find — the usual cause of "it uses the wrong account":

1. Command-line options (`--profile`, or explicit credentials in code)
2. **Environment variables** — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`
3. **Shared files** — `~/.aws/credentials` and `~/.aws/config` (profiles, `role_arn` + `source_profile`, SSO)
4. **Container credentials** — ECS task role (via `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`)
5. **EC2 instance profile** — role credentials from the instance metadata service (IMDSv2)

Points 4 and 5 are why the exam answer is almost always "**use an IAM role**": the SDK picks up the role's temporary credentials automatically and refreshes them before they expire. Check what is actually being used with `aws sts get-caller-identity`.
