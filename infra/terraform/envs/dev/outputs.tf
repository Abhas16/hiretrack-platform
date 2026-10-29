# Values the Helm chart and CI need (none of them are secret).
# `terraform output` after apply; scripts/bootstrap-cluster.sh reads them.

output "region" {
  value = var.region
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "kubeconfig_command" {
  description = "Adds the cluster to ~/.kube/config."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "ecr_registry" {
  description = "Helm value image.registry"
  value       = split("/", aws_ecr_repository.app["api"].repository_url)[0]
}

output "rds_endpoint" {
  description = "Helm value config.DB_HOST"
  value       = aws_db_instance.main.address
}

output "sqs_queue_url" {
  description = "Helm value config.SQS_QUEUE_URL"
  value       = aws_sqs_queue.jobs.url
}

output "sqs_dlq_url" {
  value = aws_sqs_queue.jobs_dlq.url
}

output "github_actions_role_arn" {
  description = "GitHub repo variable AWS_ROLE_ARN (used by .github/workflows/release.yml)"
  value       = aws_iam_role.github_actions.arn
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
