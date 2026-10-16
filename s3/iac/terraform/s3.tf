# Terraform (TF) deploy
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
# AWS docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html

# This is idempotent and declarative!

resource "aws_s3_bucket" "this" {             # Logical name (we can choose whatever we want)
  bucket = "my-bucket-created-with-terraform-fboetti" # Bucket name (must be globally unique)

  tags = {
    Name        = "my-bucket-created-with-terraform-fboetti"
    Environment = "dev"
  }
}
