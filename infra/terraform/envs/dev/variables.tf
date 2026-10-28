# Defaults are the dev settings, so `terraform apply` needs no .tfvars file.
# Override any of them with -var or a (git-ignored) terraform.tfvars, see terraform.tfvars.example.

variable "region" {
  description = "AWS region for everything in this stack."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name, used in resource names and tags."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR of the VPC. /16 leaves room for many pods (the VPC CNI gives each pod a VPC IP)."
  type        = string
  default     = "10.40.0.0/16"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.35"
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "Who may reach the EKS API endpoint. Narrow it to your own IP (x.x.x.x/32) if you can."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  description = "Graviton (arm64) types for the spot node group. Several types = more spot pools = fewer interruptions."
  type        = list(string)
  default     = ["t4g.large", "m6g.large", "m7g.large"]
}

variable "node_capacity_type" {
  description = "SPOT (about 70% cheaper, can be reclaimed with 2 minutes' notice) or ON_DEMAND."
  type        = string
  default     = "SPOT"
}

variable "node_count" {
  description = "Desired / min / max size of the node group."
  type        = object({ desired = number, min = number, max = number })
  default     = { desired = 3, min = 2, max = 5 }
}

variable "db_instance_class" {
  description = "RDS instance class (Graviton burstable for dev)."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "github_repository" {
  description = "owner/name of the GitHub repo whose Actions may push images (OIDC trust)."
  type        = string
  default     = "Abhas16/hiretrack-platform"
}

variable "github_deploy_branch" {
  description = "Only workflows running on this branch can assume the CI role."
  type        = string
  default     = "main"
}

variable "app_namespace" {
  description = "Kubernetes namespace of the app (Pod Identity associations are per namespace + service account)."
  type        = string
  default     = "hiretrack"
}

variable "secrets_version" {
  description = "Bump this number to generate new values for the app secrets (DB password, JWT secret, webhook token)."
  type        = number
  default     = 1
}
