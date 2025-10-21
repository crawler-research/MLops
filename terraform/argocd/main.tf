# Створюємо namespace для ArgoCD
resource "kubernetes_namespace" "argocd" {
  metadata {
    name = var.argocd_namespace
    labels = {
      name = var.argocd_namespace
    }
  }
}

# Розгортаємо ArgoCD через Helm
resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = var.argocd_chart_version
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  values = [file("${path.module}/values/argocd-values.yaml")]

  depends_on = [kubernetes_namespace.argocd]
}

# Створюємо namespace для applications
resource "kubernetes_namespace" "application" {
  metadata {
    name = "application"
    labels = {
      name = "application"
    }
  }
}