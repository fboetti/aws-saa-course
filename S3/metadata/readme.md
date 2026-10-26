# Object Metadata Lab

Upload an object with **user-defined metadata** and read it back. Theory: [Object Overview — Metadata](../objects.md#metadata).

## 1. Create the bucket and upload with metadata

```bash
aws s3 mb s3://my-metadata-bucket-test-12312

aws s3api put-object \
  --bucket my-metadata-bucket-test-12312 \
  --key test.txt \
  --body test.txt \
  --metadata Planet=Mars
```

## 2. Read the metadata back

```bash
aws s3api head-object --bucket my-metadata-bucket-test-12312 --key test.txt
```

The output contains `"Metadata": {"planet": "Mars"}` next to system metadata such as `ContentLength`, `ETag` and `LastModified`. Note that the **key was lowercased**: user metadata travels as HTTP headers (`x-amz-meta-planet: Mars`), and S3 stores the names in lowercase. In the console it appears under the object's **Metadata** section.

Metadata cannot be edited in place: changing it means copying the object onto itself with new metadata (which creates a new version if versioning is on).

```bash
aws s3api copy-object \
  --bucket my-metadata-bucket-test-12312 --key test.txt \
  --copy-source my-metadata-bucket-test-12312/test.txt \
  --metadata Planet=Venus --metadata-directive REPLACE
```

## Clean up

```bash
aws s3 rm s3://my-metadata-bucket-test-12312/test.txt
aws s3 rb s3://my-metadata-bucket-test-12312
```
