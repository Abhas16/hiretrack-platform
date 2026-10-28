# One ECR repository per image (names match the Helm chart's image paths).

locals {
  images = ["api", "web", "match-scorer", "job-scout", "reminder-worker", "triage-bot"]
}

resource "aws_ecr_repository" "app" {
  for_each = toset(local.images)

  name = "hiretrack-${each.key}"
  # A tag (the git SHA) can never be pushed twice with different content: what Argo CD
  # deploys for a SHA is exactly what CI built and scanned for it.
  image_tag_mutability = "IMMUTABLE"
  # dev: `terraform destroy` also deletes repos that still contain images.
  force_delete = true

  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}

resource "aws_ecr_lifecycle_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name

  # Only TAGGED images are counted. A multi-arch image is a tagged index pointing at untagged
  # per-arch manifests; an "expire untagged" rule would delete those and break the image.
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 30 newest tagged images"
      selection    = { tagStatus = "tagged", tagPatternList = ["*"], countType = "imageCountMoreThan", countNumber = 30 }
      action       = { type = "expire" }
    }]
  })
}
