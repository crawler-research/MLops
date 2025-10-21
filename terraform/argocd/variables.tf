variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "my-eks-cluster"
}

variable "argocd_namespace" {
  description = "Namespace for ArgoCD"
  type        = string
  default     = "infra-tools"
}

variable "argocd_chart_version" {
  description = "Version of ArgoCD Helm chart"
  type        = string
  default     = "5.51.6"
}