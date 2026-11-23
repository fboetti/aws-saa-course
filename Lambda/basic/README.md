# Basic Lambda with AWS SAM

A minimal Python Lambda function defined with AWS SAM.

## Files

- `template-sam.yaml`: SAM template (function, runtime, memory, timeout, env vars)
- `app.py`: handler; prints and returns `Hello <name> from Lambda!`
- `samconfig.toml`: saved deploy settings (created by `sam deploy --guided`)

## Prerequisites

```bash
brew tap aws/tap
brew install aws-sam-cli awscli
aws configure                  # access key, secret, region (eu-north-1)
aws sts get-caller-identity    # verify credentials
```

Docker is only needed for `sam local invoke`.

## Build and deploy

Run from this folder:

```bash
sam build -t template-sam.yaml
sam deploy --guided            # first time only; answers are saved to samconfig.toml
sam deploy                     # later deploys reuse samconfig.toml
```

## Invoke

Deployed function:

```bash
aws lambda invoke \
  --function-name hello-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"name": "Fabio"}' \
  response.json && cat response.json
```

Locally (requires Docker):

```bash
echo '{"name": "Fabio"}' > event.json
sam local invoke HelloFunction -t template-sam.yaml -e event.json
```

If `name` is missing from the event, it defaults to `World`.

## Clean up

```bash
sam delete
```

This removes the CloudFormation stack and the resources it created.
