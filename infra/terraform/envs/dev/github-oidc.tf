# GitHub Actions -> AWS without stored keys. GitHub signs a short-lived OIDC token for each
# workflow run; AWS STS swaps it for temporary credentials of the role below, but only if the
# token says it comes from THIS repo's deploy branch.

locals {
  github_owner = split("/", var.github_repository)[0]
  github_repo  = split("/", var.github_repository)[1]
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  # No thumbprint_list: AWS trusts GitHub's OIDC endpoint through its own CA library.
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Only pushes to the deploy branch: a PR from a fork (or any other branch) can't push images.
    # GitHub puts the owner's and repo's immutable numeric IDs in the subject:
    #   repo:<owner>@<owner id>/<repo>@<repo id>:ref:refs/heads/main
    # so a deleted + re-created account or repo with the same NAME still can't assume this role.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${local.github_owner}@${var.github_owner_id}/${local.github_repo}@${var.github_repository_id}:ref:refs/heads/${var.github_deploy_branch}"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name                 = "${local.name}-github-actions"
  description          = "Assumed by GitHub Actions (OIDC) to push images to ECR"
  assume_role_policy   = data.aws_iam_policy_document.github_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "github_ecr_push" {
  # GetAuthorizationToken can't be scoped to a repository (it is account-wide by design).
  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid = "PushToHiretrackRepos"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [for repo in aws_ecr_repository.app : repo.arn]
  }
}

resource "aws_iam_role_policy" "github_ecr_push" {
  name   = "ecr-push"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_ecr_push.json
}
