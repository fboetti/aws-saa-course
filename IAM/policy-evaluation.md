# Policy Evaluation Logic

How AWS decides whether a request is allowed.

## The three rules

1. **Default deny** — everything is denied unless allowed.
2. **Explicit deny beats everything** — one matching `Deny` in any applicable policy ends the evaluation.
3. **Allow needs to survive every limiting layer** — SCP, permission boundary, session policy.

## Evaluation order (same account)

```
Request
  │
  ├─ Any explicit Deny (identity, resource, boundary, SCP, session)?  ──► DENY
  │
  ├─ Organization SCP / RCP allows the action?   no ──► DENY
  │
  ├─ Resource-based policy allows the principal? yes ──► ALLOW   (same-account only*)
  │
  ├─ Permission boundary allows?   (if set)      no ──► DENY
  │
  ├─ Session policy allows?        (if set)      no ──► DENY
  │
  ├─ Identity-based policy allows?               yes ──► ALLOW
  │
  └─ otherwise                                       ──► DENY (implicit)
```

\* A resource-based policy that names an **IAM user ARN** directly allows that user even through a boundary; one that names a role/session or the account root still needs an identity-based allow in the usual case. Do not memorise the corner cases for SAA — the ordering above is enough.

## Effective permissions = intersection

```
effective = identity policy  ∩  permission boundary  ∩  SCP  ∩  session policy
```

(resource-based policy can add on top for same-account principals.)

| Layer | Can grant on its own? |
|---|---|
| Identity-based policy | Yes |
| Resource-based policy | Yes |
| Permission boundary | **No** |
| SCP | **No** |
| Session policy | **No** |

## Cross-account

Both accounts must agree:

| Direction | Required |
|---|---|
| Account A user → resource in Account B | A's identity policy allows **and** B's resource policy allows A |
| Account A user → assumes role in B | A's identity policy allows `sts:AssumeRole`, B's role **trust policy** trusts A, role's permission policy allows the action |

If the caller **assumes a role**, they act with the role's permissions only. If they use a **resource-based policy**, they keep their own identity and need both sides.

## Worked examples

| Policies | Result |
|---|---|
| Identity: Allow `s3:*`; bucket policy: Deny `s3:DeleteObject` | Delete **denied** (explicit deny) |
| Identity: Allow `ec2:*`; SCP: only `s3:*` allowed | EC2 **denied** (SCP) |
| Identity: Allow `s3:*`; boundary: Allow `ec2:*` | S3 **denied**, nothing effectively allowed |
| Nothing mentions `sqs:SendMessage` | **Denied** (implicit) |
| Bucket policy Allow for Account B principal, B's IAM user has no S3 permission | **Denied** (cross-account needs both) |

## Debugging

- `AccessDenied` message says whether it was an **explicit deny** and in which policy type (recent AWS error messages).
- **IAM Policy Simulator** and `iam:SimulatePrincipalPolicy` test what-ifs.
- **CloudTrail** shows the failing call and error code.
- **IAM Access Analyzer** policy validation flags errors and over-broad grants.

## Exam traps

- "Allow in one policy, Deny in another" → **Deny**.
- SCP "allow" ≠ grant; it only keeps the door open.
- SCPs don't affect the **management account** and don't affect **service-linked roles**.
- Resource-based policies let cross-account principals keep their own permissions.
