module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  # EKS Auto Mode: AWS manages compute, drivers (incl. NVIDIA on GPU nodes),
  # networking, storage. We only declare intent via NodePools.
  cluster_compute_config = {
    enabled    = true
    node_pools = ["general-purpose", "system"]
  }

  cluster_endpoint_public_access = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}
