
```bash
aws s3 mb s3://terraform-state-mkuzyshyn-eks-vpc --region us-east-1
aws s3api put-bucket-versioning \
    --bucket terraform-state-mkuzyshyn-eks-vpc \
    --versioning-configuration Status=Enabled
```

### 2. Розгортання EKS інфраструктури
```bash
cd eks-vpc-cluster
terraform init
terraform plan
terraform apply -auto-approve
```

### 3. Налаштування доступу до кластера
```bash
aws eks --region us-east-1 update-kubeconfig --name my-eks-cluster
kubectl get nodes
```

### 4. Розгортання ArgoCD
```bash
cd terraform/argocd
terraform init
terraform apply -auto-approve
```

```bash
kubectl -n infra-tools get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

```bash
kubectl port-forward svc/argocd-server -n infra-tools 8080:80
```


### 1. Застосування ArgoCD Application
```bash
kubectl apply -f goit-argo/apps/demo-app.yaml
```

### 2. Перевірка статусу Application
```bash
kubectl get application demo-app -n infra-tools
```

### 3. Перевірка деплоїних ресурсів
```bash
kubectl get all -n application
```

### 4. Тестування демо додатку
```bash
kubectl port-forward svc/demo-app -n application 8081:80
# Відкрийте http://localhost:8081 в браузері
```

# Підтвердження роботи системи

### 1. Перевірка стану EKS кластера
```bash
$ kubectl get nodes
NAME                         STATUS   ROLES    AGE     VERSION
ip-10-0-2-11.ec2.internal    Ready    <none>   17m     v1.30.14-eks-113cf36
ip-10-0-2-234.ec2.internal   Ready    <none>   9m59s   v1.30.14-eks-113cf36
ip-10-0-3-93.ec2.internal    Ready    <none>   10m     v1.30.14-eks-113cf36
```

### 2. Перевірка роботи ArgoCD
```bash
$ kubectl get pods -n infra-tools
NAME                                  READY   STATUS    RESTARTS   AGE
argocd-application-controller-0       1/1     Running   0          51m
argocd-dex-server-688986bb56-68r9k    1/1     Running   0          51m
argocd-redis-6fdf4454d8-m6wlr         1/1     Running   0          51m
argocd-repo-server-575f5fb6dc-frq5m   1/1     Running   0          51m
argocd-server-7b648cbb45-9vgrq        1/1     Running   0          51m
```

### 3. Перевірка статусу ArgoCD Application
```bash
$ kubectl get application demo-app -n infra-tools
NAME       SYNC STATUS   HEALTH STATUS
demo-app   Synced        Healthy
```

### 4. Перевірка деплоїного додатку
```bash
$ kubectl get all -n application
NAME                            READY   STATUS    RESTARTS   AGE
pod/demo-app-6f995757d4-4hp4w   1/1     Running   0          2m6s
pod/demo-app-6f995757d4-xthct   1/1     Running   0          2m6s

NAME               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/demo-app   ClusterIP   172.20.166.149   <none>        80/TCP    2m6s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demo-app   2/2     2            2           2m6s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/demo-app-6f995757d4   2         2         2       2m7s
```

### 5. Перевірка доступу до ArgoCD UI
```bash
$ kubectl -n infra-tools get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
OxY9fIy4z4u1rAYb

$ kubectl port-forward svc/argocd-server -n infra-tools 8080:80
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

**ArgoCD UI доступний на:** http://localhost:8080
- **Login:** admin
- **Password:** OxY9fIy4z4u1rAYb

### 6. Тестування GitOps workflow
Змінити `replicaCount: 3` у файлі `goit-argo/demo-app/values.yaml` в Git репозиторії, і ArgoCD автоматично застосує зміни:

```bash
$ kubectl get pods -n application
NAME                        READY   STATUS    RESTARTS   AGE
demo-app-6f995757d4-4hp4w   1/1     Running   0          5m
demo-app-6f995757d4-xthct   1/1     Running   0          5m
demo-app-6f995757d4-xyz123  1/1     Running   0          30s 
```


**Git Repository:** https://github.com/crawler-research/MLops/tree/lesson-7

## 🔄 GitOps Workflow


```bash
# Видалення ArgoCD Application
kubectl delete application demo-app -n infra-tools

# Видалення ArgoCD
cd terraform/argocd
terraform destroy -auto-approve

# Видалення EKS інфраструктури
cd ../..
terraform destroy -auto-approve
```


