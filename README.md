# EKS VPC Infrastructure

```
mkuzyshyn@mkuzyshyn-mbp eks-vpc-cluster % kubectl get nodes

NAME                         STATUS   ROLES    AGE     VERSION
ip-10-0-1-146.ec2.internal   Ready    <none>   5m8s    v1.30.14-eks-113cf36
ip-10-0-1-225.ec2.internal   Ready    <none>   4m56s   v1.30.14-eks-113cf36
ip-10-0-3-232.ec2.internal   Ready    <none>   5m10s   v1.30.14-eks-113cf36
```

```
eks-vpc-cluster/
├── main.tf              # Головний файл, який викликає модулі
├── variables.tf         # Змінні для кореневого модуля
├── outputs.tf           # Outputs кореневого модуля
├── terraform.tf         # Версії providers
├── backend.tf           # Конфігурація S3 backend
├── vpc/                 # Модуль для створення VPC
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   └── backend.tf
├── eks/                 # Модуль для створення EKS
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   └── backend.tf
└── README.md
```



## Інструкції по розгортанню


```bash
aws s3 mb s3://terraform-state-mkuzyshyn-eks-vpc --region us-east-1

aws s3api put-bucket-versioning \
    --bucket terraform-state-mkuzyshyn-eks-vpc \
    --versioning-configuration Status=Enabled
```


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

kubectl get nodes --show-labels
```

## Видалення ресурсів


```bash
terraform destroy -auto-approve
```

