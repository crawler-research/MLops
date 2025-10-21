provider "aws" {
  region = var.region
}

module "vpc" {
  source = "./vpc"
  
  region      = var.region
  vpc_cidr    = var.vpc_cidr
  environment = var.environment
  common_tags = local.common_tags
}

module "eks" {
  source = "./eks"
  
  region        = var.region
  cluster_name  = var.cluster_name
  environment   = var.environment
  common_tags   = local.common_tags
  
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnets
  public_subnets = module.vpc.public_subnets
}