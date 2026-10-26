# Server-Side Encryption Lab

Upload the same file with **SSE-S3** (the default) and with **SSE-KMS**, and see that reading it back needs no extra step: with server-side encryption, S3 encrypts on write and decrypts on read. Theory: [S3 Security — Server-side encryption](../security.md#server-side-encryption).

## 1. Create the bucket and upload with the default encryption (SSE-S3)

```bash
aws s3 mb s3://my-bucket-encrypted-fboetti

aws s3 cp hello.txt s3://my-bucket-encrypted-fboetti/hello.txt

aws s3api head-object --bucket my-bucket-encrypted-fboetti --key hello.txt \
  --query ServerSideEncryption            # "AES256" = SSE-S3, applied automatically
```

## 2. Upload with SSE-KMS

Without `--ssekms-key-id`, S3 uses the AWS managed key `aws/s3` (created on first use). Pass the ID/ARN of a **customer managed key** to control its key policy and rotation yourself.

```bash
aws s3api put-object \
  --bucket my-bucket-encrypted-fboetti \
  --key hello-kms.txt \
  --body hello.txt \
  --server-side-encryption aws:kms
# optionally: --ssekms-key-id <key-id-or-arn>

aws s3api head-object --bucket my-bucket-encrypted-fboetti --key hello-kms.txt \
  --query "[ServerSideEncryption,SSEKMSKeyId]"
```

## 3. Download

```bash
aws s3 cp s3://my-bucket-encrypted-fboetti/hello-kms.txt hello-downloaded.txt
```

This works because the caller has `s3:GetObject` **and** `kms:Decrypt` on the key — S3 asks KMS to decrypt the object's data key on our behalf. A user with `s3:GetObject` but without `kms:Decrypt` gets `AccessDenied`: with SSE-KMS the key policy is a second lock on the data. (KMS keys are symmetric AES keys that never leave KMS — there is no "private key" to hold.)

## Clean up

```bash
aws s3 rb s3://my-bucket-encrypted-fboetti --force
```
