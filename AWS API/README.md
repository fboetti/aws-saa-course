# AWS API — Theoretical Overview

Notes on accessing AWS services through the API: credentials, signing and the tools that talk to it (CLI, SDKs). Hands-on CLI/SDK material for S3 lives in `../AWS S3/`.

## Contents

- [Access Keys](access-keys.md) — long-term programmatic credentials: parts, limits (2 per user), rotation, root keys, temporary credentials vs access keys, and the exam mapping.
- [AWS STS](sts.md) — temporary credentials: AssumeRole, SAML/web identity federation, GetFederationToken, session policies/tags, durations and the cross-account traps.
- [SigV4 Signing](sigv4.md) — how requests are signed: canonical request, credential scope, presigned URL limits, payload hashing and the auth-error traps.
- [Exponential Backoff](exponential-backoff.md) — retrying throttled/failed API calls with doubling waits plus jitter, and which errors are safe to retry.
