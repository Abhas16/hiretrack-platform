# EKS Pod Identity: one IAM role per component, bound to ONE (namespace, service account).
# The Pod Identity agent (an EKS add-on) gives matching pods temporary credentials; boto3 and
# the AWS SDKs pick them up through the default credential chain. No access keys anywhere.
#
# Who gets what (least privilege):
#   hiretrack/hiretrack-job-scout        send to the jobs queue
#   hiretrack/hiretrack-match-scorer     receive/delete from the jobs queue
#   keda/keda-operator                   read the queue depth (to scale match-scorer)
#   external-secrets/external-secrets    read /hiretrack/<env>/* from SSM
#   kube-system/aws-load-balancer-controller   manage ALBs and target groups
# api, web, reminder-worker and triage-bot need no AWS access, so they get no role.

module "job_scout_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.10.0"

  name = "${local.name}-job-scout"

  attach_custom_policy = true
  policy_statements = [{
    sid       = "PublishNewJobs"
    actions   = ["sqs:SendMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.jobs.arn]
  }]

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = var.app_namespace
      service_account = "hiretrack-job-scout"
    }
  }
}

module "match_scorer_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.10.0"

  name = "${local.name}-match-scorer"

  attach_custom_policy = true
  policy_statements = [{
    sid = "ConsumeJobs"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]
    resources = [aws_sqs_queue.jobs.arn]
  }]

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = var.app_namespace
      service_account = "hiretrack-match-scorer"
    }
  }
}

# KEDA's operator reads ApproximateNumberOfMessages to decide how many scorer pods to run.
module "keda_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.10.0"

  name = "${local.name}-keda"

  attach_custom_policy = true
  policy_statements = [{
    sid       = "ReadQueueDepth"
    actions   = ["sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.jobs.arn]
  }]

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = "keda"
      service_account = "keda-operator"
    }
  }
}

module "external_secrets_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.10.0"

  name = "${local.name}-external-secrets"

  # Read-only access to this environment's parameters, nothing else in the account.
  attach_external_secrets_policy        = true
  external_secrets_ssm_parameter_arns   = ["arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*"]
  external_secrets_secrets_manager_arns = []
  external_secrets_create_permission    = false

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = "external-secrets"
      service_account = "external-secrets"
    }
  }
}

module "aws_lb_controller_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.10.0"

  name = "${local.name}-aws-lbc"

  # The controller's official IAM policy (create/modify ALBs, target groups, security groups).
  attach_aws_lb_controller_policy = true

  associations = {
    this = {
      cluster_name    = module.eks.cluster_name
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
    }
  }
}

data "aws_caller_identity" "current" {}
