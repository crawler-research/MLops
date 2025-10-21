module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.30"

  vpc_id                         = var.vpc_id
  subnet_ids                     = var.subnet_ids
  cluster_endpoint_public_access = true

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    cpu_nodes = {
      name = "cpu-nodes"
      
      instance_types = ["t3.small"]
      
      min_size     = 1
      max_size     = 3
      desired_size = 2

      capacity_type = "ON_DEMAND"
      
      labels = {
        Environment = var.environment
        NodeType    = "cpu"
      }
      
      tags = merge(var.common_tags, {
        Name = "${var.cluster_name}-cpu-nodes"
      })
    }

    gpu_nodes = {
      name = "gpu-nodes"
      
      instance_types = ["t3.small"]  # Використовуємо t3.small для достатніх ресурсів
      
      min_size     = 0
      max_size     = 2
      desired_size = 1

      capacity_type = "ON_DEMAND"
      
      labels = {
        Environment = var.environment
        NodeType    = "gpu"
      }
      
      tags = merge(var.common_tags, {
        Name = "${var.cluster_name}-gpu-nodes"
      })
    }
  }

  tags = merge(var.common_tags, {
    Name = var.cluster_name
  })
}