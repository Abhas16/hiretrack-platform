# VPC with three tiers of subnets over two AZs:
#   public    ALB + NAT gateway            (route to the internet gateway)
#   private   EKS nodes and pods           (outbound only, through the NAT gateway)
#   database  RDS                          (no route to the internet at all)

locals {
  name = "hiretrack-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)
}

data "aws_availability_zones" "available" {
  state = "available"
  # Skip Local Zones / Wavelength zones: EKS and RDS need regular AZs.
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = local.name
  cidr = var.vpc_cidr
  azs  = local.azs

  # cidrsubnet(10.40.0.0/16, 4, n) = /20 blocks (4096 IPs) for the private (pod) subnets,
  # /24 blocks for the small public and database subnets.
  private_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets   = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, 200 + i)]
  database_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, 210 + i)]

  create_database_subnet_group = true

  # dev: ONE NAT gateway for both AZs (~$35/month less than one per AZ). If its AZ goes down,
  # the private subnets lose outbound internet. Prod: one_nat_gateway_per_az = true.
  enable_nat_gateway = true
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  # The AWS Load Balancer Controller finds subnets by these tags:
  # internet-facing ALBs go in "elb" subnets, internal ones in "internal-elb" subnets.
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}
