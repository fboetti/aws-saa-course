## Create a bucket

aws s3 mb s3://my-metadata-bucket-test-12312

## Upload file with metadata

aws s3api put-object --bucket my-metadata-bucket-test-12312 --key test.txt --body test.txt --metadata Planet=Mars 

(go to file, click on it and see Metadata section)

## Delete file and bucket

aws s3 rm s3://my-metadata-bucket-test-12312/test.txt
aws s3 rb s3://my-metadata-bucket-test-12312
