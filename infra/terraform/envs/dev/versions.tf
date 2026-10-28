terraform {
  # >= 1.11: write-only arguments (password_wo, value_wo) + ephemeral resources, so generated
  # secrets are sent to AWS but never written to the Terraform state.
  required_version = ">= 1.11"

  required_providers {
    aws    = { source = "hashicorp/aws", version = "6.70.0" }
    random = { source = "hashicorp/random", version = "3.9.1" }
  }

  # Remote state in the bucket made by ../../bootstrap. The bucket name contains the account
  # ID, so it is passed at init time instead of being hardcoded here:
  #   terraform init -backend-config="bucket=hiretrack-tfstate-<account id>"
  backend "s3" {
    key          = "hiretrack/dev/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true # S3-native locking (no DynamoDB table)
  }
}

provider "aws" {
  region = var.region
  # Every resource gets these tags: easy to find in Cost Explorer and the console.
  default_tags {
    tags = {
      Project     = "hiretrack"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = var.github_repository
    }
  }
}
