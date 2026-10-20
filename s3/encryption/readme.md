## Create a bucket

aws s3 mb s3://my-bucket-encrypted-fboetti

## Create a file

aws s3 cp hello.txt s3://my-bucket-encrypted-fboetti/hello.txt

# Create a KMS key if necessary
## Put object with encryption of KMS

aws s3api put-object --bucket my-bucket-encrypted-fboetti --body hello.txt --key hello.txt --server-side-encryption aws:kms


## Download the file

aws s3 cp s3://my-bucket-encrypted-fboetti/hello.txt hello.txt 

(we can do this because we have the permissions / private key)
