output "argocd_namespace" {
  description = "Namespace where ArgoCD is deployed"
  value       = kubernetes_namespace.argocd.metadata[0].name
}

output "application_namespace" {
  description = "Namespace for applications"
  value       = kubernetes_namespace.application.metadata[0].name
}

output "argocd_server_service_name" {
  description = "ArgoCD server service name"
  value       = "${helm_release.argocd.name}-server"
}