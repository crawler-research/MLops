terraform {
  backend "s3" {
    bucket = "terraform-state-mkuzyshyn-eks-vpc"
    key    = "vpc/terraform.tfstate"
    region = "us-east-1"
  }
}