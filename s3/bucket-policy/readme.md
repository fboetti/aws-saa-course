## Create a bucket

aws s3 mb s3://my-bucket-policy-example-fboetti

## Attach policy

aws s3api put-bucket-policy  --bucket my-bucket-policy-example-fboetti --policy file://policy.json

## After launching it, the user specified in the rule can access the bucket via
aws s3 ls s3://my-bucket-policy-example-fboetti

## To copy a file in it
aws s3 cp <file_name> s3://my-bucket-policy-example-fboetti


You can do a lot of stuff with policies
You can limit users to explicit prefixes, ecc 

