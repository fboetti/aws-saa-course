# Lambda as a container image with AWS SAM

Same function as `../basic`, but packaged as a Docker image instead of a zip.

## Files

- `template-sam.yaml`: SAM template (`PackageType: Image`)
- `Dockerfile`: based on the AWS Lambda Python 3.12 base image
- `app.py`: handler

## Prerequisites

- AWS SAM CLI and AWS CLI, with credentials configured (see `../basic/README.md`)
- Docker running (required to build the image)

## Build and deploy

Run from this folder:

```bash
sam build -t template-sam.yaml
sam deploy --guided
```

SAM builds the image and pushes it to an ECR repository. When `--guided` asks
about it, let SAM create the repository automatically. Answers are saved to
`samconfig.toml`, so later deploys only need `sam deploy`.

## Invoke

```bash
aws lambda invoke \
  --function-name hello-docker-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"name": "Fabio"}' \
  response.json && cat response.json
```

Locally:

```bash
echo '{"name": "Fabio"}' > event.json
sam local invoke HelloDockerFunction -t template-sam.yaml -e event.json
```

## Clean up

```bash
sam delete
```

This deletes the stack. SAM also offers to delete the ECR repository and its
images.
