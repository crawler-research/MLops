
- MLflow Tracking Server
- PostgreSQL (backend)
- MinIO (artifacts)
- Prometheus PushGateway
- ArgoCD deployment
- EKS cluster (2x t3.small)


![Prometheus Metrics](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/1.png)

![](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/2.png)
![](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/3.png)
![](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/4.png)
![](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/5.png)
![](https://github.com/crawler-research/MLops/blob/lesson-8-9/screenshots/6.png)

## Результат

Найкраща модель:
- Accuracy: **96.67%**
- Params: n_estimators=150, max_depth=15
- Saved: `best_model/model`



## Як запустити

### 1. AWS Infrastructure

```bash
cd terraform
terraform init
terraform apply
aws eks update-kubeconfig --region us-east-1 --name mlops-eks-cluster
```

### 2. ArgoCD + Applications

```bash
# ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Додати Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add community-charts https://community-charts.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deploy apps
kubectl create namespace mlflow
kubectl apply -f argocd/applications/minio.yaml

helm install postgresql bitnami/postgresql -n mlflow \
  --set auth.username=mlflow \
  --set auth.password=mlflow123 \
  --set auth.database=mlflow

helm install mlflow community-charts/mlflow -n mlflow \
  --set backendStore.postgres.enabled=true \
  --set backendStore.postgres.host=postgresql.mlflow.svc.cluster.local \
  --set backendStore.postgres.user=mlflow \
  --set backendStore.postgres.password=mlflow123

helm install pushgateway prometheus-community/prometheus-pushgateway -n mlflow
```

### 3. Port-forward

```bash
kubectl port-forward -n mlflow pod/<mlflow-pod> 5000:5000 &
kubectl port-forward -n mlflow svc/pushgateway-prometheus-pushgateway 9091:9091 &
kubectl port-forward -n mlflow svc/minio 9000:9000 &
```

### 4. Тренування

Або:

```bash
python experiments/train_and_push.py
```

