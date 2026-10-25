## Create a user with no permissions and generate out access keys

aws iam create-user --user-name sts-machine-user
aws iam create-access-key --user-name sts-machine-user --output table

(copy the credentials and then configure with)

aws configure (save them in [sts] profile)

aws s3 ls --profile sts (we cannot do this)

## Create a role

with deploy-role bash script

## Assume the role

aws iam put-user-policy --user-name sts-machine-user --policy-name StsAssumePolicy --policy-document file://policy.json

aws sts assume-role \
    --role-arn arn:aws:iam::719623059777:role/StsRole \
    --role-session-name s3-sts-fun \
    --profile sts

(copy credentials in file under profile [assumed])

aws sts get-caller-identity --profile assumed
