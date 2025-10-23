# Результат

``` curl http://localhost:8000/health```
{"status":"healthy","model_loaded":true,"drift_detector_loaded":true,"timestamp":"2025-10-22T20:10:32.419902"}%


```mkuzyshyn@mkuzyshyn-mbp final_project % curl -X POST http://localhost:8000/predict 
>   -H "Content-Type: application/json" \
>   -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
{"prediction":0,"probability":[1.0,0.0,0.0],"drift_detected":false,"drift_score":null,"timestamp":"2025-10-22T20:10:36.813192"} ```
```

```mkuzyshyn@mkuzyshyn-mbp final_project % curl -X POST http://localhost:8000/predict \
>   -H "Content-Type: application/json" \
>   -d '{"features": [100.0, 200.0, 300.0, 400.0]}' ```
{"prediction":2,"probability":[0.0,0.0,1.0],"drift_detected":false,"drift_score":null,"timestamp":"2025-10-22T20:10:42.539012"}


mkuzyshyn@mkuzyshyn-mbp final_project % curl http://localhost:8000/metrics | grep -E "(inference_requests|drift_|model_predictions)"
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  3447  100  3447    0     0  2074k      0 --:--:-- --:--:-- --:--:-- 3366k
# HELP inference_requests_total Total number of inference requests
# TYPE inference_requests_total counter
inference_requests_total{status="success"} 2.0
# HELP inference_requests_created Total number of inference requests
# TYPE inference_requests_created gauge
inference_requests_created{status="success"} 1.761189036815857e+09
# HELP drift_detections_total Total number of drift detections
# TYPE drift_detections_total counter
drift_detections_total 0.0
# HELP drift_detections_created Total number of drift detections
# TYPE drift_detections_created gauge
drift_detections_created 1.7611889801264498e+09
# HELP drift_score Current drift score
# TYPE drift_score gauge
drift_score 0.0
# HELP model_predictions_total Total predictions by class
# TYPE model_predictions_total counter
model_predictions_total{predicted_class="0"} 1.0
model_predictions_total{predicted_class="2"} 1.0
# HELP model_predictions_created Total predictions by class
# TYPE model_predictions_created gauge
model_predictions_created{predicted_class="0"} 1.761189036805158e+09
model_predictions_created{predicted_class="2"} 1.761189042537787e+09
mkuzyshyn@mkuzyshyn-mbp final_project % curl http://localhost:8000/model/info
{"model_type":"RandomForestClassifier","timestamp":"2025-10-22T20:10:50.907899","n_features":4,"classes":[0,1,2]}%                                                                         

## Компоненти

- **FastAPI** - inference API з predict() функцією
- **Alibi Detect** - drift detection
- **Helm** - Kubernetes deployment
- **ArgoCD** - GitOps з auto-sync та self-heal
- **GitLab CI** - retrain pipeline
- **Prometheus** - метрики
- **Grafana** - dashboard
- **Loki** - логування

## Структура

```
├── app/main.py                  # FastAPI сервіс
├── model/train.py               # Тренування моделі
├── helm/                        # Helm chart
├── argocd/application.yaml      # ArgoCD config
├── prometheus/                  # Prometheus config
├── grafana/dashboards.json      # Grafana dashboard
├── Dockerfile
├── requirements.txt
└── .gitlab-ci.yml              # CI/CD pipeline
```

**Локально:**
```bash
pip install -r requirements.txt
python model/train.py
python -m uvicorn app.main:app --reload
```

**Docker:**
```bash
docker build -t ml-inference .
docker run -p 8000:8000 ml-inference
```

**Kubernetes:**
```bash
helm install ml-inference ./helm -n ml-inference --create-namespace
kubectl port-forward -n ml-inference svc/ml-inference-service 8000:80
```

## Тестування

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'

kubectl logs -n ml-inference -l app.kubernetes.io/name=ml-inference-service -f

# Метрики
curl http://localhost:8000/metrics
```

## API Endpoints

- `GET /health` - health check
- `POST /predict` - inference
- `GET /metrics` - Prometheus метрики
- `GET /model/info` - інформація про модель

## Оновлення моделі

### Автоматичне 
Через GitLab CI

### Локально

```bash
# 1. Перетренувати модель
python model/train.py
pkill -f uvicorn
uvicorn app.main:app --reload

helm upgrade ml-inference ./helm -n ml-inference
```

# Логи в Kubernetes
kubectl logs -n ml-inference -l app.kubernetes.io/name=ml-inference-service --tail=50
```




