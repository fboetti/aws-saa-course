# Bucket Policy Lab

Grant a specific IAM user read access to a bucket with a **bucket policy** (resource-based policy). Theory: [S3 Security — Bucket policies](../security.md#bucket-policies).

[`policy.json`](policy.json) allows the user `aws-examples` to:

- `s3:ListBucket` on the **bucket ARN** (`arn:aws:s3:::my-bucket-policy-example-fboetti`) — listing is a bucket-level action;
- `s3:GetObject` on the **object ARN** (`arn:aws:s3:::my-bucket-policy-example-fboetti/*`) — reading is an object-level action.

Mixing the two ARNs up is the most common bucket-policy mistake: `ListBucket` on `bucket/*` or `GetObject` on `bucket` silently grants nothing.

Replace the account ID `719623059777` and the user name with yours.

## 1. Create the bucket and attach the policy

```bash
aws s3 mb s3://my-bucket-policy-example-fboetti

aws s3api put-bucket-policy \
  --bucket my-bucket-policy-example-fboetti \
  --policy file://policy.json

aws s3api get-bucket-policy --bucket my-bucket-policy-example-fboetti --query Policy --output text
```

## 2. Test as the granted user

Using a profile for the user named in the policy (e.g. `--profile aws-examples`):

```bash
aws s3 ls s3://my-bucket-policy-example-fboetti --profile aws-examples                 # allowed: ListBucket
aws s3 cp s3://my-bucket-policy-example-fboetti/<file> . --profile aws-examples        # allowed: GetObject
aws s3 cp <file_name> s3://my-bucket-policy-example-fboetti --profile aws-examples     # denied: no PutObject
```

Uploading works only from the bucket owner's account (or after adding `s3:PutObject` to the policy). For a principal **in the same account** the bucket policy alone is enough; for a principal in **another account**, its own IAM policy must allow the actions too.

## Going further

Typical additions to try:

- Restrict listing to a prefix with `"Condition": {"StringLike": {"s3:prefix": ["reports/*"]}}`.
- Deny non-HTTPS requests with `"Condition": {"Bool": {"aws:SecureTransport": "false"}}` in a `Deny` statement.
- Allow access only from your organization with `aws:PrincipalOrgID`.

## Clean up

```bash
aws s3api delete-bucket-policy --bucket my-bucket-policy-example-fboetti
aws s3 rb s3://my-bucket-policy-example-fboetti --force   # --force empties the bucket first
```
