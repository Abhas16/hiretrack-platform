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

# No default on purpose: the EKS API must never be open to the whole internet. Set your own IP
# in terraform.tfvars (git-ignored):  cluster_endpoint_public_access_cidrs = ["x.x.x.x/32"]
# (curl -s https://checkip.amazonaws.com). Home IP changed -> update it and apply again.
variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint (e.g. your IP as x.x.x.x/32)."
  type        = list(string)

  validation {
    condition     = length(var.cluster_endpoint_public_access_cidrs) > 0 && !contains(var.cluster_endpoint_public_access_cidrs, "0.0.0.0/0")
    error_message = "Use specific CIDRs (your IP as x.x.x.x/32), never 0.0.0.0/0."
  }
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
  # db.t4g.micro failed with "insufficient-capacity" in ap-south-1 (2026-10-28); t4g.small is
  # the next Graviton size (~$0.04/h). Try db.t3.micro if that is short on capacity too.
  description = "RDS instance class (burstable for dev)."
  type        = string
  default     = "db.t4g.small"
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
