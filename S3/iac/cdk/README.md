
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `requirements.txt` file and rerun the `python -m pip install -r requirements.txt`
command.

## This stack: an S3 bucket (and how to add your own constructs)

The `cdk init` template ships an empty `cdk/cdk_stack.py`. Below is how that `CdkStack` was extended
with an S3 bucket plus a stack output, as a pattern to follow for further resources.

### Add a construct

1. Import the module from `aws_cdk` (`constructs.Construct` is already imported).
2. Instantiate it inside `CdkStack.__init__`, after `super().__init__(...)`.

```python
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
)
from constructs import Construct


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self, "MyBucket",                       # (scope, logical id)
            versioned=True,
            bucket_name="my-bucket-with-iac-cdk-fboetti",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,   # course/dev only
            auto_delete_objects=True,               # course/dev only
        )
```

- The first argument (`self`) is the **scope**: it attaches the construct to this stack.
- The second argument (`"MyBucket"`) is the **logical ID**: it must be unique within the stack.
- `removal_policy=DESTROY` + `auto_delete_objects=True` let `cdk destroy` delete a *non-empty* bucket.
  They are convenient for the course, but **remove them for production**: the default is `RETAIN`, so
  `cdk destroy` deletes the stack but leaves the bucket (and its data) in place.
- `block_public_access=BLOCK_ALL` is already the CDK default; it is set explicitly here because it
  matters for the SAA exam.

### Is the `bucket = ...` assignment required?

No. Calling `s3.Bucket(...)` creates the construct and registers it with the scope, so the bucket is
part of the stack even without assignment:

```python
s3.Bucket(self, "MyBucket", versioned=True)   # works, no variable needed
```

Assign to a variable **only if you reference the bucket later** (its properties, or passing it to
other constructs), for example `bucket.bucket_name`, `bucket.bucket_arn`, or
`bucket.grant_read(role)`. If you assign it and never use it, linters such as flake8/ruff flag the
unused variable (`F841`), so in that case drop the assignment.

### Expose a value with `CfnOutput`

A `CfnOutput` prints a value after `cdk deploy` and in the CloudFormation console. It is how you make
a resource attribute usable outside the stack:

```python
CfnOutput(
    self, "BucketName",
    value=bucket.bucket_name,
    description="Name of the S3 bucket created by the stack",
    export_name="MyBucketName",        # optional: makes it importable via Fn::ImportValue
)
```

- `value=` accepts a resource attribute (`bucket.bucket_name`, `bucket.bucket_arn`) or a literal.
- `export_name=` is optional; use it when another stack must import the value with `Fn::ImportValue`.

### Verify before deploying

```bash
cd S3/iac/cdk
cdk synth
```

The generated template in `cdk.out/CdkStack.template.json` shows the bucket (CDK appends a hash to the
logical ID, e.g. `MyBucketF68F3FF0`) and the output:

```json
"Outputs": {
  "BucketName": {
    "Description": "Name of the S3 bucket created by the stack",
    "Value": { "Ref": "MyBucketF68F3FF0" },
    "Export": { "Name": "MyBucketName" }
  }
}
```

The value is a `{"Ref": ...}` reference, not the literal string: CloudFormation resolves the real
bucket name at deploy time.

## Useful commands

 * `cdk bootstrap`   one-time per account/region: creates the `CDKToolkit` stack (assets bucket, deploy roles). Required here, because `auto_delete_objects` ships a Lambda-backed custom resource as an asset
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk diff`        compare deployed stack with current state
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk destroy`     delete the stack (and, here, the bucket and its objects)
 * `cdk docs`        open CDK documentation

Enjoy!
