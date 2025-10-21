terraform {
  backend "s3" {
    bucket = "terraform-state-mkuzyshyn-eks-vpc"
    key    = "eks/terraform.tfstate"
    region = "us-east-1"
  }
}