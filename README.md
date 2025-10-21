# MLOps Experiments - Lesson 8-9

## 📋 Зміст

- [Опис проєкту](#опис-проєкту)
- [Архітектура](#архітектура)
- [Передумови](#передумови)
- [Структура проєкту](#структура-проєкту)
- [Покрокова інструкція](#покрокова-інструкція)
  - [Крок 1: Підготовка Git](#крок-1-підготовка-git)
  - [Крок 2: Розгортання інфраструктури через ArgoCD](#крок-2-розгортання-інфраструктури-через-argocd)
  - [Крок 3: Перевірка розгортання](#крок-3-перевірка-розгортання)
  - [Крок 4: Налаштування port-forward](#крок-4-налаштування-port-forward)
  - [Крок 5: Запуск експериментів](#крок-5-запуск-експериментів)
  - [Крок 6: Перегляд результатів](#крок-6-перегляд-результатів)
- [Troubleshooting](#troubleshooting)
- [Очищення ресурсів](#очищення-ресурсів)

---

## 📝 Опис проєкту

Цей проєкт демонструє повний цикл MLOps для трекінгу ML-експериментів з використанням:

- **MLflow** - для логування експериментів, параметрів, метрик та моделей
- **MinIO** - S3-сумісне сховище для артефактів моделей
- **PostgreSQL** - база даних для метаданих MLflow
- **Prometheus PushGateway** - для експорту метрик в Prometheus
- **Grafana** - для візуалізації метрик
- **ArgoCD** - для декларативного розгортання всіх компонентів

### 🎯 Що робить проєкт:

1. Тренує кілька моделей класифікації (Random Forest, Logistic Regression) з різними гіперпараметрами
2. Логує всі параметри та метрики в MLflow
3. Зберігає моделі як артефакти в MinIO
4. Відправляє метрики в Prometheus через PushGateway
5. Автоматично вибирає найкращу модель за accuracy
6. Зберігає найкращу модель локально в `best_model/`

---

## 🏗️ Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                      │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Namespace: mlflow                     │  │
│  │                                                         │  │
│  │  ┌──────────┐  ┌────────────┐  ┌──────────────────┐  │  │
│  │  │  MinIO   │  │ PostgreSQL │  │  MLflow Tracking │  │  │
│  │  │  (S3)    │  │   (DB)     │  │     Server       │  │  │
│  │  │  :9000   │  │   :5432    │  │     :5000        │  │  │
│  │  └────┬─────┘  └─────┬──────┘  └────────┬─────────┘  │  │
│  │       │              │                  │             │  │
│  │       └──────────────┴──────────────────┘             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                Namespace: monitoring                   │  │
│  │                                                         │  │
│  │  ┌──────────────────┐      ┌──────────────────────┐  │  │
│  │  │   PushGateway    │─────▶│    Prometheus        │  │  │
│  │  │      :9091       │      │                      │  │  │
│  │  └──────────────────┘      └──────────┬───────────┘  │  │
│  │                                       │               │  │
│  │                            ┌──────────▼───────────┐  │  │
│  │                            │      Grafana         │  │  │
│  │                            │                      │  │  │
│  │                            └──────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│                         ▲                                     │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                   ┌──────┴──────┐
                   │   Python    │
                   │   Script    │
                   │ (Local/Pod) │
                   └─────────────┘
```

---

## ✅ Передумови

Перед початком переконайтеся, що у вас встановлено та налаштовано:

### 1. Kubernetes кластер
- Minikube, kind, або хмарний кластер (AWS EKS, GCP GKE, Azure AKS)
- `kubectl` налаштований для роботи з кластером

```bash
# Перевірка доступу до кластера
kubectl cluster-info
kubectl get nodes
```

### 2. ArgoCD
- ArgoCD встановлений в namespace `argocd`
- Доступ до ArgoCD UI

```bash
# Перевірка ArgoCD
kubectl get pods -n argocd
```

### 3. Prometheus та Grafana (опціонально, якщо ще не встановлено)
```bash
# Встановлення Prometheus та Grafana через Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace

# Grafana
helm install grafana grafana/grafana \
  --namespace monitoring
```

### 4. Python 3.8+
```bash
# Перевірка версії Python
python3 --version
```

### 5. Git
```bash
# Перевірка Git
git --version
```

---

## 📁 Структура проєкту

```
mlops-experiments/
├── argocd/
│   └── applications/
│       ├── minio.yaml              # ArgoCD Application для MinIO
│       ├── postgres.yaml           # ArgoCD Application для PostgreSQL
│       ├── mlflow.yaml             # ArgoCD Application для MLflow
│       └── pushgateway.yaml        # ArgoCD Application для PushGateway
├── experiments/
│   ├── train_and_push.py           # Головний скрипт тренування
│   └── requirements.txt            # Python залежності
├── best_model/                     # Найкраща модель (створюється автоматично)
│   ├── MLmodel
│   ├── conda.yaml
│   ├── model.pkl
│   ├── python_env.yaml
│   └── model_info.txt
└── README.md                       # Ця інструкція
```

---

## 🚀 Покрокова інструкція

### Крок 1: Підготовка Git

#### 1.1. Створіть нову гілку

```bash
# Перейдіть в директорію проєкту
cd /Users/mkuzyshyn/Documents/ML/MLOps/lesson-4/lesson-8

# Створіть нову гілку
git checkout -b lesson-8-9

# Перевірте, що ви на правильній гілці
git branch
```

#### 1.2. Додайте файли до Git

```bash
# Додайте всі файли
git add .

# Перевірте статус
git status

# Закомітьте зміни
git commit -m "Add MLflow experiment tracking infrastructure with ArgoCD"
```

#### 1.3. Завантажте гілку на GitHub

```bash
# Замініть URL на ваш репозиторій
git push origin lesson-8-9
```

---

### Крок 2: Розгортання інфраструктури через ArgoCD

#### 2.1. Застосуйте ArgoCD Applications

**ВАЖЛИВО**: Перед застосуванням файлів, потрібно оновити `repoURL` в кожному файлі на URL вашого Git репозиторію.

Відкрийте кожен файл у директорії `argocd/applications/` та замініть:
```yaml
source:
  repoURL: https://github.com/YOUR_USERNAME/YOUR_REPO.git  # Ваш репозиторій
  targetRevision: lesson-8-9
  path: argocd/applications
```

**Але зараз ми використовуємо Helm charts, тому застосуємо їх напряму:**

```bash
# 1. MinIO
kubectl apply -f argocd/applications/minio.yaml

# 2. PostgreSQL
kubectl apply -f argocd/applications/postgres.yaml

# 3. MLflow (чекаємо коли MinIO та Postgres будуть готові)
kubectl apply -f argocd/applications/mlflow.yaml

# 4. PushGateway
kubectl apply -f argocd/applications/pushgateway.yaml
```

#### 2.2. Моніторинг розгортання через ArgoCD UI

```bash
# Відкрийте ArgoCD UI через port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Відкрийте в браузері: https://localhost:8080
# Отримайте пароль:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**В ArgoCD UI ви повинні побачити 4 applications:**
- `minio`
- `postgresql`
- `mlflow`
- `pushgateway`

Всі вони повинні бути в статусі `Healthy` та `Synced`.

---

### Крок 3: Перевірка розгортання

#### 3.1. Перевірте Pods

```bash
# Перевірте pods в namespace mlflow
kubectl get pods -n mlflow

# Очікуваний вивід:
# NAME                              READY   STATUS    RESTARTS   AGE
# minio-xxxxxxxxxx-xxxxx            1/1     Running   0          5m
# postgresql-0                      1/1     Running   0          5m
# mlflow-xxxxxxxxxx-xxxxx           1/1     Running   0          3m

# Перевірте pods в namespace monitoring
kubectl get pods -n monitoring

# Очікуваний вивід:
# NAME                                             READY   STATUS    RESTARTS   AGE
# prometheus-pushgateway-xxxxxxxxxx-xxxxx          1/1     Running   0          5m
```

#### 3.2. Перевірте Services

```bash
# MLflow namespace
kubectl get svc -n mlflow

# Очікуваний вивід:
# NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
# minio        ClusterIP   10.xxx.xxx.xxx   <none>        9000/TCP   5m
# postgresql   ClusterIP   10.xxx.xxx.xxx   <none>        5432/TCP   5m
# mlflow       ClusterIP   10.xxx.xxx.xxx   <none>        5000/TCP   3m

# Monitoring namespace
kubectl get svc -n monitoring

# Очікуваний вивід:
# NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
# prometheus-pushgateway       ClusterIP   10.xxx.xxx.xxx   <none>        9091/TCP   5m
```

#### 3.3. Перевірте логи (якщо щось не працює)

```bash
# Логи MLflow
kubectl logs -n mlflow -l app=mlflow --tail=50

# Логи MinIO
kubectl logs -n mlflow -l app=minio --tail=50

# Логи PostgreSQL
kubectl logs -n mlflow -l app.kubernetes.io/name=postgresql --tail=50

# Логи PushGateway
kubectl logs -n monitoring -l app=prometheus-pushgateway --tail=50
```

---

### Крок 4: Налаштування port-forward

Для доступу до сервісів з локальної машини потрібно налаштувати port-forwarding.

#### 4.1. MLflow UI

**Відкрийте новий термінал:**

```bash
kubectl port-forward -n mlflow svc/mlflow 5000:5000
```

**Перевірте доступ:**
- Відкрийте в браузері: http://localhost:5000
- Ви повинні побачити MLflow UI

**Залиште цей термінал відкритим!**

#### 4.2. PushGateway (для відправки метрик)

**Відкрийте ще один новий термінал:**

```bash
kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091
```

**Перевірте доступ:**
- Відкрийте в браузері: http://localhost:9091
- Ви повинні побачити PushGateway UI

**Залиште цей термінал відкритим!**

#### 4.3. Grafana (для візуалізації)

**Відкрийте ще один новий термінал:**

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

**Отримайте пароль Grafana:**

```bash
kubectl get secret -n monitoring grafana -o jsonpath="{.data.admin-password}" | base64 -d
echo
```

**Перевірте доступ:**
- Відкрийте в браузері: http://localhost:3000
- Login: `admin`
- Password: (вивід з попередньої команди)

**Залиште цей термінал відкритим!**

---

### Крок 5: Запуск експериментів

#### 5.1. Створіть віртуальне середовище Python

```bash
# Перейдіть в директорію experiments
cd experiments

# Створіть віртуальне середовище
python3 -m venv venv

# Активуйте віртуальне середовище
source venv/bin/activate  # macOS/Linux
# або
venv\Scripts\activate     # Windows
```

#### 5.2. Встановіть залежності

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5.3. Встановіть змінні середовища

**ВАЖЛИВО**: Переконайтеся, що port-forward для MLflow та PushGateway все ще працюють!

```bash
# MLflow Tracking URI (локальний port-forward)
export MLFLOW_TRACKING_URI=http://localhost:5000

# PushGateway URL (локальний port-forward)
export PUSHGATEWAY_URL=localhost:9091

# Налаштування для MinIO (якщо потрібно)
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
```

**Для Windows (PowerShell):**
```powershell
$env:MLFLOW_TRACKING_URI="http://localhost:5000"
$env:PUSHGATEWAY_URL="localhost:9091"
$env:AWS_ACCESS_KEY_ID="minioadmin"
$env:AWS_SECRET_ACCESS_KEY="minioadmin123"
$env:MLFLOW_S3_ENDPOINT_URL="http://localhost:9000"
```

#### 5.4. Запустіть скрипт тренування

```bash
python train_and_push.py
```

**Очікуваний вивід:**

```
🎯 MLflow Experiments with Prometheus Integration
📍 MLflow Tracking URI: http://localhost:5000
📍 PushGateway URL: localhost:9091

============================================================
🚀 ПОЧАТОК ЕКСПЕРИМЕНТІВ
============================================================

✓ Створено новий експеримент: iris-classification-experiments (ID: 1)

📊 Завантаження датасету Iris...
✓ Датасет завантажено: 120 train, 30 test зразків

🔄 Тренування RandomForest з параметрами: {'n_estimators': 10, 'max_depth': 3, 'random_state': 42}
  Run ID: a1b2c3d4e5f6g7h8i9j0
  ✓ Accuracy: 0.9667
  ✓ F1 Score: 0.9661
  ✓ Training time: 0.05s
  ✓ Метрики відправлено в PushGateway (localhost:9091)

... (інші експерименти) ...

============================================================
📊 ПІДСУМОК ЕКСПЕРИМЕНТІВ
============================================================

№   Model                Accuracy   Run ID                                  
---------------------------------------------------------------------------
1   RandomForest         0.9667     a1b2c3d4e5f6g7h8i9j0                    
2   RandomForest         0.9667     b2c3d4e5f6g7h8i9j0k1                    
...

============================================================
🏆 ПОШУК НАЙКРАЩОЇ МОДЕЛІ
============================================================

✓ Найкраща модель:
  - Модель: RandomForest
  - Параметри: {'n_estimators': 200, 'max_depth': None, 'random_state': 42}
  - Accuracy: 1.0000
  - Run ID: x1y2z3a4b5c6d7e8f9g0

============================================================
💾 ЗБЕРЕЖЕННЯ НАЙКРАЩОЇ МОДЕЛІ
============================================================

✓ Модель збережено в директорії: ../best_model
✓ Інформація про модель: ../best_model/model_info.txt

============================================================
✅ ЕКСПЕРИМЕНТИ ЗАВЕРШЕНО УСПІШНО!
============================================================

📌 Переглянути результати в MLflow UI:
   http://localhost:5000

📌 Переглянути метрики в Prometheus/Grafana:
   Metrics: mlflow_accuracy, mlflow_f1_score, mlflow_precision, mlflow_recall
```

#### 5.5. Перевірте створену модель

```bash
# Перейдіть на рівень вище
cd ..

# Перегляньте вміст директорії best_model
ls -la best_model/

# Очікуваний вивід:
# MLmodel
# conda.yaml
# model.pkl
# python_env.yaml
# requirements.txt
# model_info.txt

# Перегляньте інформацію про модель
cat best_model/model_info.txt
```

---

### Крок 6: Перегляд результатів

#### 6.1. MLflow UI

1. Відкрийте http://localhost:5000
2. Ви побачите експеримент `iris-classification-experiments`
3. Клацніть на ньому, щоб побачити всі runs
4. Для кожного run можна побачити:
   - Параметри (n_estimators, max_depth, C, max_iter, тощо)
   - Метрики (accuracy, f1_score, precision, recall, training_time)
   - Артефакти (модель)

**Зробіть скріншот MLflow UI з експериментами!**

#### 6.2. PushGateway

1. Відкрийте http://localhost:9091
2. Ви побачите всі метрики, які були відправлені:
   - `mlflow_accuracy`
   - `mlflow_f1_score`
   - `mlflow_precision`
   - `mlflow_recall`

**Зробіть скріншот PushGateway UI!**

#### 6.3. Grafana - Налаштування Prometheus Data Source

Якщо Prometheus ще не доданий як data source:

1. Відкрийте http://localhost:3000
2. Login: `admin`, Password: (з команди вище)
3. Перейдіть: **Configuration → Data Sources → Add data source**
4. Оберіть **Prometheus**
5. URL: `http://prometheus-server.monitoring.svc.cluster.local:80` (або інша адреса вашого Prometheus)
6. Натисніть **Save & Test**

#### 6.4. Grafana - Перегляд метрик

1. Перейдіть: **Explore** (іконка компаса в лівому меню)
2. Оберіть **Prometheus** як data source
3. В полі **Metric** введіть: `mlflow_accuracy`
4. Натисніть **Run Query**
5. Ви побачите графік з accuracy всіх експериментів

**Спробуйте інші метрики:**
- `mlflow_f1_score`
- `mlflow_precision`
- `mlflow_recall`

**Зробіть скріншот Grafana Explore з метриками!**

#### 6.5. Створення Dashboard в Grafana (опціонально)

1. Натисніть **Create → Dashboard**
2. Додайте панелі для кожної метрики
3. Збережіть dashboard з назвою "MLflow Experiments"

**Приклад PromQL запитів:**

```promql
# Accuracy по всіх експериментах
mlflow_accuracy

# Найкраща accuracy
max(mlflow_accuracy)

# Середня accuracy
avg(mlflow_accuracy)

# F1 Score по run_id
mlflow_f1_score{run_id=~".+"}
```

---

## 🔧 Troubleshooting

### Проблема: Pods не стартують

```bash
# Перевірте events
kubectl get events -n mlflow --sort-by='.lastTimestamp'
kubectl get events -n monitoring --sort-by='.lastTimestamp'

# Перевірте describe pod
kubectl describe pod <POD_NAME> -n <NAMESPACE>
```

### Проблема: MLflow не може підключитись до PostgreSQL

```bash
# Перевірте, чи PostgreSQL працює
kubectl get pods -n mlflow -l app.kubernetes.io/name=postgresql

# Перевірте логи PostgreSQL
kubectl logs -n mlflow -l app.kubernetes.io/name=postgresql

# Перевірте connection string в MLflow
kubectl logs -n mlflow -l app=mlflow | grep -i postgres
```

### Проблема: MLflow не може зберегти артефакти в MinIO

```bash
# Перевірте MinIO
kubectl get pods -n mlflow -l app=minio

# Перевірте логи MinIO
kubectl logs -n mlflow -l app=minio

# Перевірте, чи bucket створений
kubectl port-forward -n mlflow svc/minio 9000:9000
# Відкрийте http://localhost:9000 (minioadmin/minioadmin123)
```

### Проблема: Метрики не відображаються в Grafana

```bash
# Перевірте, чи PushGateway працює
kubectl get pods -n monitoring -l app=prometheus-pushgateway

# Перевірте метрики в PushGateway
curl http://localhost:9091/metrics | grep mlflow

# Перевірте, чи Prometheus scrape PushGateway
# В Grafana → Explore → Prometheus → Metrics browser
```

### Проблема: Python скрипт не може підключитись до MLflow

```bash
# Перевірте port-forward
lsof -i :5000  # macOS/Linux
netstat -an | grep 5000  # Windows

# Перевірте змінні середовища
echo $MLFLOW_TRACKING_URI
echo $PUSHGATEWAY_URL

# Спробуйте підключитись вручну
curl http://localhost:5000/api/2.0/mlflow/experiments/list
```

---

## 🧹 Очищення ресурсів

### Видалення Applications з ArgoCD

```bash
# Видалити всі applications
kubectl delete -f argocd/applications/minio.yaml
kubectl delete -f argocd/applications/postgres.yaml
kubectl delete -f argocd/applications/mlflow.yaml
kubectl delete -f argocd/applications/pushgateway.yaml

# Або видалити через ArgoCD CLI
argocd app delete minio -y
argocd app delete postgresql -y
argocd app delete mlflow -y
argocd app delete pushgateway -y
```

### Видалення Namespaces

```bash
# УВАГА: Це видалить ВСІ ресурси в namespace!
kubectl delete namespace mlflow
kubectl delete namespace monitoring  # Тільки якщо ви не використовуєте monitoring для інших цілей
```

### Видалення PersistentVolumeClaims (якщо залишились)

```bash
kubectl get pvc -n mlflow
kubectl delete pvc --all -n mlflow
```

### Terraform (якщо використовується для AWS/GCP/Azure)

```bash
terraform destroy
```

**ВАЖЛИВО**: Не забудьте про S3 бакети для Terraform state!

---

## 📸 Скріншоти

Для здачі домашнього завдання потрібно зробити наступні скріншоти:

1. **ArgoCD UI** - всі 4 applications в статусі Healthy
2. **MLflow UI** - список експериментів з різними runs
3. **MLflow UI** - деталі окремого run (параметри + метрики)
4. **PushGateway UI** - список метрик
5. **Grafana Explore** - графік з метриками mlflow_accuracy
6. **Термінал** - вивід скрипта train_and_push.py
7. **Директорія best_model/** - вміст директорії з найкращою моделлю

---

## 📦 Формат здачі

### 1. Створіть архів

```bash
# Перейдіть на рівень вище
cd /Users/mkuzyshyn/Documents/ML/MLOps/lesson-4

# Створіть архів (замініть Прізвище та Імʼя)
zip -r ДЗ8_Кузишин_Максим.zip lesson-8/ \
  -x "lesson-8/experiments/venv/*" \
  -x "lesson-8/.git/*" \
  -x "lesson-8/**/__pycache__/*" \
  -x "lesson-8/**/.DS_Store"
```

### 2. Завантажте в LMS

- Назва файлу: `ДЗ8_Прізвище_Імʼя.zip`
- Формат: ZIP архів
- Розмір: до 50 МБ

### 3. Додайте посилання на GitHub

В описі до завдання додайте посилання на гілку:
```
https://github.com/YOUR_USERNAME/YOUR_REPO/tree/lesson-8-9
```

---

## ✅ Чеклист перед здачею

- [ ] Всі 4 ArgoCD applications розгорнуті та в статусі Healthy
- [ ] MLflow UI доступний та показує експерименти
- [ ] PushGateway отримує метрики
- [ ] Grafana показує метрики з Prometheus
- [ ] Скрипт `train_and_push.py` успішно виконується
- [ ] Директорія `best_model/` містить найкращу модель
- [ ] Зроблено всі необхідні скріншоти
- [ ] README.md містить всі інструкції
- [ ] Код закомічений в гілку `lesson-8-9`
- [ ] Створено ZIP архів з назвою `ДЗ8_Прізвище_Імʼя.zip`
- [ ] Додано посилання на GitHub гілку

---

## 📚 Додаткові ресурси

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Prometheus PushGateway](https://github.com/prometheus/pushgateway)
- [Grafana Documentation](https://grafana.com/docs/)
- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/)

---

## 🎓 Критерії оцінювання

| Розділ | Макс. балів | Опис |
|--------|-------------|------|
| ArgoCD-деплой (MLflow, MinIO, Postgres) | 30 | Всі компоненти розгорнуті через ArgoCD та працюють |
| PushGateway через ArgoCD | 15 | PushGateway розгорнутий та отримує метрики |
| Скрипт train_and_push.py з MLflow + Prometheus | 30 | Скрипт тренує моделі, логує в MLflow та відправляє метрики |
| Метрики видно в Grafana | 15 | Метрики доступні в Grafana через Prometheus |
| README.md з усіма інструкціями та скрінами | 10 | Повна документація та скріншоти |
| **Разом** | **100** | |

---

**Бажаємо успіхів! 🚀**

Якщо у вас виникли питання, перегляньте секцію [Troubleshooting](#troubleshooting) або зверніться до викладача.
