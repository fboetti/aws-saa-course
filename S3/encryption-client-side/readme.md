# Client-Side Encryption Lab

With **client-side encryption** you encrypt the file *before* uploading it: S3 stores only ciphertext and never sees the key or the plaintext. Theory: [S3 Security — Client-side encryption](../security.md#client-side-encryption).

This lab uses `openssl` to keep the idea visible. In real applications you would use the **Amazon S3 Encryption Client** (envelope encryption with AES-GCM, data keys from KMS or your own key).

## 1. Create the bucket and a key

```bash
aws s3 mb s3://my-bucket-encryption-client-fboetti

# 256-bit random key, kept only on your machine (never commit it)
openssl rand -hex 32 > local.key
```

## 2. Encrypt locally, upload the ciphertext

```bash
openssl enc -aes-256-cbc -pbkdf2 -salt \
  -in hello.txt -out hello.txt.enc -pass file:local.key

aws s3 cp hello.txt.enc s3://my-bucket-encryption-client-fboetti/hello.txt.enc
```

S3 still applies its default SSE-S3 on top, but what it encrypts is already unreadable without `local.key`.

## 3. Download and decrypt

```bash
aws s3 cp s3://my-bucket-encryption-client-fboetti/hello.txt.enc downloaded.enc

openssl enc -d -aes-256-cbc -pbkdf2 \
  -in downloaded.enc -out hello-decrypted.txt -pass file:local.key

diff hello.txt hello-decrypted.txt && echo "round trip OK"
```

Anyone with S3 access can download `hello.txt.enc`, but nobody — AWS included — can read it without the key. The flip side: **lose the key and the data is gone**, and S3 features that need to read the content (e.g. S3 Select, Macie scans) can't work on it.

## Clean up

```bash
aws s3 rb s3://my-bucket-encryption-client-fboetti --force
rm -f hello.txt.enc downloaded.enc hello-decrypted.txt local.key
```
