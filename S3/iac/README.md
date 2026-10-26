# S3 with Infrastructure as Code

The same idea — "create one S3 bucket" — written with four IaC tools. All four are **declarative and idempotent**: you describe the desired state, the tool works out what to create, change or delete, and running it twice changes nothing the second time.

| Folder | Tool | Language | State lives in | Commands |
|---|---|---|---|---|
| [`cfn/`](cfn/template.yaml) | **AWS CloudFormation** | YAML/JSON template | AWS (the **stack**) | `./deploy`, `./delete` |
| [`terraform/`](terraform/s3.tf) | **Terraform** | HCL | `terraform.tfstate` (local or remote backend) | `terraform init / plan / apply / destroy` |
| [`pulumi/`](pulumi/README.md) | **Pulumi** | Python | Pulumi Cloud or a self-managed backend | `pulumi preview / up / destroy` |
| [`cdk/`](cdk/README.md) | **AWS CDK** | Python → synthesizes CloudFormation | AWS (a CloudFormation stack) | `cdk synth / deploy / destroy` |

## How they compare

- **CloudFormation** is the AWS-native engine: no state file to manage, rollback on failure, drift detection, StackSets for multi-account/region. AWS-only.
- **CDK** is not a separate engine: it generates a CloudFormation template from real code, and adds high-level constructs (e.g. `grant_read`, auto-delete of objects) that would be many lines of raw YAML.
- **Terraform** and **Pulumi** are **multi-cloud** and keep their own state. Terraform uses a DSL (HCL); Pulumi uses general-purpose languages.

**Exam note:** SAA-C03 asks only about **CloudFormation** (and CDK/SAM as ways to produce it): "repeatable, version-controlled infrastructure across accounts/regions" → CloudFormation (StackSets for many accounts). Terraform and Pulumi are third-party tools and never the expected answer.

## Notes on each folder

- **`cfn/`** — `deploy` runs `aws cloudformation deploy --no-execute-changeset`: it only **creates a change set** for review. Execute it from the CloudFormation console (or rerun without the flag) to actually create the bucket. Both scripts load credentials from the repo's `.env`.
- **`terraform/`** — `main.tf` pins the AWS provider (`~> 5.0`) and the region (`eu-north-1`); `s3.tf` defines the bucket. Run `terraform init` once, then `plan`/`apply`.
- **`pulumi/`** — the name passed to `s3.Bucket(...)` is the **logical name**: Pulumi appends a random suffix to form the real bucket name (auto-naming), so it stays globally unique across stacks.
- **`cdk/`** — the stack enables versioning, SSE-S3 and Block Public Access, and sets `RemovalPolicy.DESTROY` + `auto_delete_objects` so `cdk destroy` can remove a non-empty bucket (lab only).

← Back to the [S3 overview](../README.md)
