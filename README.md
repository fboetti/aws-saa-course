# aws-saa-course
The codebase of freeCodeCamp SAA course

## Gitpod environment

This repository is configured for [Gitpod](https://www.gitpod.io/). On workspace start it installs:

- AWS CLI v2
- Terraform
- Python 3 with `boto3` and `requests`
- VS Code extensions for AWS, Terraform, Python and ShellCheck

### AWS credentials in Gitpod

Store your AWS access keys as Gitpod environment variables (never commit them):

```bash
# Run inside a Gitpod terminal once
gp env AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
gp env AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
gp env AWS_DEFAULT_REGION=eu-north-1
gp env AWS_REGION=eu-north-1
```

Alternatively set them in the Gitpod web UI: *Settings -> Variables*. Then restart the workspace. The AWS CLI reads these variables automatically, and `aws sts get-caller-identity` in the `aws-cli` task confirms the login.

### Layout

- `bin/` - install scripts used by `.gitpod.yml`
- `infra/` - Terraform infrastructure as code
- `scripts/` - Bash scripts that use the AWS CLI
- `.env.example` - template for optional local overrides

### Notes

- Credentials are intentionally not written to `~/.aws/credentials`; this avoids leaking secrets if the workspace is shared.
- Destroy any real resources you create (`terraform destroy`) to avoid charges.
" path="README.md