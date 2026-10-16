# Terraform - AWS provider configuration
# Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
# Docs:    https://developer.hashicorp.com/terraform/language/providers

# This is idempotent and declarative!

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws" # Official AWS provider (multi cloud provider from HashiCorp)
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1" # Default region for all resources in this config
}
