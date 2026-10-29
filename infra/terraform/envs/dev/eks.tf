# EKS cluster + one managed node group of Graviton spot instances.

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  name               = local.name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets # nodes and pods live in the private subnets

  # API endpoint reachable from the internet (kubectl from a laptop, no VPN) but only with
  # valid IAM credentials, and only from the CIDRs in the variable. The nodes use the private
  # endpoint, so their traffic to the control plane never leaves the VPC.
  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs
  endpoint_private_access      = true

  # Access entries (EKS API) instead of the old aws-auth ConfigMap. Whoever runs
  # `terraform apply` becomes cluster admin.
  authentication_mode                      = "API"
  enable_cluster_creator_admin_permissions = true

  # Pods get AWS credentials from EKS Pod Identity (see pod-identity.tf), so no IRSA/OIDC provider.
  enable_irsa = false

  # Control plane logs to CloudWatch: who called the API (audit) and why logins failed (authenticator).
  enabled_log_types                      = ["api", "audit", "authenticator"]
  cloudwatch_log_group_retention_in_days = 7

  addons = {
    # before_compute: installed before the nodes join, so the first pods get networking/identity.
    vpc-cni = {
      before_compute = true
      most_recent    = true
      # Lets the VPC CNI enforce Kubernetes NetworkPolicies (the chart ships default-deny rules).
      configuration_values = jsonencode({ enableNetworkPolicy = "true" })
    }
    eks-pod-identity-agent = {
      before_compute = true
      most_recent    = true
    }
    kube-proxy = { most_recent = true }
    coredns    = { most_recent = true }
  }

  eks_managed_node_groups = {
    default = {
      # Amazon Linux 2023 for arm64. The CI builds every image for amd64 AND arm64.
      ami_type       = "AL2023_ARM_64_STANDARD"
      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type

      min_size     = var.node_count.min
      max_size     = var.node_count.max
      desired_size = var.node_count.desired

      # Roll nodes one at a time on AMI/config changes; PDBs keep the app up meanwhile.
      update_config = { max_unavailable = 1 }

      labels = { workload = "general" }
    }
  }
}
