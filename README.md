# aws-saa-course
The codebase of freeCodeCamp SAA course

## Gitpod environment

This repository is configured for [Gitpod](https://www.gitpod.io/). On workspace start it installs:

- AWS CLI v2
- Terraform
- AWS CDK CLI (`cdk`) plus the Python CDK library (`aws-cdk-lib`, `constructs`)
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

### AWS CDK in Python

The workspace ships both halves of the CDK:

- the `cdk` CLI (Node.js package, installed globally) that runs the commands
- the Python library `aws-cdk-lib` (+ `constructs`) that you write the app with

You only need to download the CDK package manually outside Gitpod. On your machine install Node.js, then:

```bash
npm install -g aws-cdk            # the CLI
pip install aws-cdk-lib constructs  # the Python library
```

Bootstrap the target account/region once (creates the CDK toolkit S3 bucket and roles):

```bash
cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

Create a new Python CDK app and deploy it:

```bash
mkdir my-app && cd my-app
cdk init app --language python     # scaffolds the app and a .venv
source .venv/bin/activate
pip install -r requirements.txt    # aws-cdk-lib + constructs
cdk synth                          # render CloudFormation from app.py
cdk deploy                         # apply the stack
cdk destroy                        # remove the stack when done
```

Inside the repo, `cdk` commands must be run from the folder that contains `cdk.json` (the `cdk` Gitpod task starts you there). The synthesized templates land in `cdk.out/`, which is gitignored.

### Layout

- `bin/` - install scripts used by `.gitpod.yml`, plus `bin/load-env` to source the root `.env`
- `infra/` - Terraform infrastructure as code
- `scripts/` - Bash scripts that use the AWS CLI
- `.env.example` - template for optional local overrides

### Notes

- Credentials are intentionally not written to `~/.aws/credentials`; this avoids leaking secrets if the workspace is shared.
- Destroy any real resources you create (`terraform destroy`) to avoid charges.

### Local `.env` (outside Gitpod)

If you run things locally instead of Gitpod, put your values in a root `.env` (copy `.env.example`; the file is gitignored) and inject them into the current shell with:

```bash
source ./bin/load-env
```

The command parses `KEY=VALUE` lines (quotes, `export ` prefixes and CRLF are handled), exports each variable, and prints only the variable names, never the values. Run it per terminal session; it must be sourced so the exports land in your shell.
