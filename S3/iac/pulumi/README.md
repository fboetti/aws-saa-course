 # AWS Python S3 Bucket Pulumi Template

 A minimal Pulumi template for provisioning a single AWS S3 bucket using Python.

 ## What is Pulumi?

 Pulumi is an Infrastructure as Code (IaC) tool very similar to Terraform: like Terraform, it is **multi-cloud** (AWS, Azure, GCP, Kubernetes, and many more providers), it manages resources through a state file, and it follows the same core workflow (`preview`/`up`/`destroy`, equivalent to Terraform's `plan`/`apply`/`destroy`). The main difference is that instead of writing a declarative DSL (HCL), you define infrastructure using a general-purpose programming language — in this case Python — which allows loops, functions, real libraries, and reuse of existing tooling.

 ## Overview

 This program provisions an S3 bucket (`pulumi_aws.s3.Bucket` — with `pulumi-aws` v7 this is the current resource; `BucketV2` from v6 is deprecated) and exports its ID as an output.

 The string passed to `s3.Bucket(...)` is the **logical name**. Pulumi *auto-names* the real bucket by appending a random suffix (e.g. `my-bucket-with-iac-pulumi-fboetti-1a2b3c4`), which keeps names globally unique across stacks; pass `bucket="..."` to force an exact name.

 It’s an ideal starting point when:
  - You want to learn Pulumi with AWS in Python.
  - You need a barebones S3 bucket deployment to build upon.
  - You prefer a minimal template without extra dependencies.

 ## Prerequisites

 - An AWS account with permissions to create S3 buckets.
 - AWS credentials configured in your environment (for example via AWS CLI or environment variables).
 - Python 3.9 or later installed.
 - Pulumi CLI already installed and logged in.

 ## Getting Started

 The project already exists in this repo (it was generated with `pulumi new aws-python`).

 1. Change into the project directory and install dependencies:
    ```bash
    cd S3/iac/pulumi
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```
 2. Create a stack and set the region:
    ```bash
    pulumi stack init dev
    pulumi config set aws:region eu-north-1
    ```
 3. Preview the planned changes:
    ```bash
    pulumi preview
    ```
 4. Deploy the stack:
    ```bash
    pulumi up
    ```
 5. Tear down when finished:
    ```bash
    pulumi destroy
    ```

 ## Project Layout

 The directory looks like:
 ```
 ├── __main__.py         # Entry point of the Pulumi program
 ├── Pulumi.yaml         # Project metadata and template configuration
 ├── requirements.txt    # Python dependencies
 └── Pulumi.<stack>.yaml # Stack-specific configuration (e.g., Pulumi.dev.yaml)
 ```

 ## Configuration

 This template defines the following config value:

 - `aws:region` (string)
   The AWS region to deploy resources into.
   Default: `us-east-1`

 View or update configuration with:
 ```bash
 pulumi config get aws:region
 pulumi config set aws:region us-west-2
 ```

 ## Outputs

 Once deployed, the stack exports:

 - `bucket_name` — the ID of the created S3 bucket.

 Retrieve outputs with:
 ```bash
 pulumi stack output bucket_name
 ```

 ## Next Steps

 - Customize `__main__.py` to add or configure additional resources.
 - Explore the Pulumi AWS SDK: https://www.pulumi.com/registry/packages/aws/
 - Break your infrastructure into modules for better organization.
 - Integrate into CI/CD pipelines for automated deployments.

 ## Help and Community

 If you have questions or need assistance:
 - Pulumi Documentation: https://www.pulumi.com/docs/
 - Community Slack: https://slack.pulumi.com/
 - GitHub Issues: https://github.com/pulumi/pulumi/issues

 Contributions and feedback are always welcome!