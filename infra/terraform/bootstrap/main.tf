# Bootstrap: the S3 bucket that holds the Terraform state of every other stack.
# Chicken-and-egg: this stack can't keep its own state in a bucket it creates, so its state is
# LOCAL (a few resources, easy to import again). Run it once per AWS account:
#
#   terraform -chdir=infra/terraform/bootstrap init
#   terraform -chdir=infra/terraform/bootstrap apply
#
# Locking: Terraform >= 1.10 locks with a lock file in the bucket itself (use_lockfile = true
# in the backend), so no DynamoDB table is needed any more.

terraform {
  required_version = ">= 1.11"
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.70.0" }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "hiretrack", ManagedBy = "terraform", Stack = "bootstrap" }
  }
}

variable "region" {
  description = "Region of the state bucket (the same as the stacks that use it)."
  type        = string
  default     = "ap-south-1"
}

data "aws_caller_identity" "current" {}

# The account ID makes the name globally unique without hardcoding it anywhere.
resource "aws_s3_bucket" "state" {
  bucket = "hiretrack-tfstate-${data.aws_caller_identity.current.account_id}"
}

# Every state write is a new version: a broken apply can be rolled back to the previous state.
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# State can contain sensitive values: never public.
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Only HTTPS requests are allowed.
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.state]
}

# Old state versions are kept 90 days, then deleted (the bucket doesn't grow forever).
resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = 90 }
  }
}

output "state_bucket" {
  description = "Pass to the other stacks: terraform init -backend-config=\"bucket=<this>\""
  value       = aws_s3_bucket.state.bucket
}
