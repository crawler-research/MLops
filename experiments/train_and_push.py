#!/usr/bin/env python3

import os
import shutil
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "localhost:9091")
EXPERIMENT_NAME = "iris-classification-experiments"


def setup_experiment():
    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment is None:
            experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
            print(f"✓ Створено новий експеримент: {EXPERIMENT_NAME} (ID: {experiment_id})")
        else:
            experiment_id = experiment.experiment_id
            print(f"✓ Використовується існуючий експеримент: {EXPERIMENT_NAME} (ID: {experiment_id})")
        mlflow.set_experiment(EXPERIMENT_NAME)
        return experiment_id
    except Exception as e:
        print(f"✗ Помилка при налаштуванні експерименту: {e}")
        raise


def load_data():
    print("\n📊 Завантаження датасету Iris...")
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42
    )
    print(f"✓ Датасет завантажено: {len(X_train)} train, {len(X_test)} test зразків")
    return X_train, X_test, y_train, y_test


def push_metrics_to_prometheus(run_id, metrics, job_name="mlflow_experiments"):
    try:
        registry = CollectorRegistry()
        
        accuracy_gauge = Gauge('mlflow_accuracy', 'Model accuracy', ['run_id'], registry=registry)
        f1_gauge = Gauge('mlflow_f1_score', 'Model F1 score', ['run_id'], registry=registry)
        precision_gauge = Gauge('mlflow_precision', 'Model precision', ['run_id'], registry=registry)
        recall_gauge = Gauge('mlflow_recall', 'Model recall', ['run_id'], registry=registry)
        
        accuracy_gauge.labels(run_id=run_id).set(metrics['accuracy'])
        f1_gauge.labels(run_id=run_id).set(metrics['f1_score'])
        precision_gauge.labels(run_id=run_id).set(metrics['precision'])
        recall_gauge.labels(run_id=run_id).set(metrics['recall'])
        
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        print(f"  ✓ Метрики відправлено в PushGateway ({PUSHGATEWAY_URL})")
    except Exception as e:
        print(f"  ✗ Помилка при відправці метрик в PushGateway: {e}")


def train_model(model, model_name, params, X_train, X_test, y_train, y_test):
    print(f"\n🔄 Тренування {model_name} з параметрами: {params}")
    
    with mlflow.start_run(run_name=f"{model_name}_{params}") as run:
        run_id = run.info.run_id
        print(f"  Run ID: {run_id}")
        
        mlflow.log_params(params)
        mlflow.log_param("model_type", model_name)
        
        start_time = time.time()
        model.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        y_pred = model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'training_time': training_time
        }
        
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model")
        
        print(f"  ✓ Accuracy: {metrics['accuracy']:.4f}")
        print(f"  ✓ F1 Score: {metrics['f1_score']:.4f}")
        print(f"  ✓ Training time: {training_time:.2f}s")
        
        push_metrics_to_prometheus(run_id, metrics)
        
        return run_id, metrics['accuracy'], model


def run_experiments():
    print("\n" + "="*60)
    print("🚀 ПОЧАТОК ЕКСПЕРИМЕНТІВ")
    print("="*60)
    
    setup_experiment()
    X_train, X_test, y_train, y_test = load_data()
    
    experiments = [
        {
            'model': RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42),
            'name': 'RandomForest',
            'params': {'n_estimators': 10, 'max_depth': 3, 'random_state': 42}
        },
        {
            'model': RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42),
            'name': 'RandomForest',
            'params': {'n_estimators': 50, 'max_depth': 5, 'random_state': 42}
        },
        {
            'model': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'name': 'RandomForest',
            'params': {'n_estimators': 100, 'max_depth': 10, 'random_state': 42}
        },
        {
            'model': RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42),
            'name': 'RandomForest',
            'params': {'n_estimators': 200, 'max_depth': None, 'random_state': 42}
        },
        {
            'model': LogisticRegression(C=0.1, max_iter=100, random_state=42),
            'name': 'LogisticRegression',
            'params': {'C': 0.1, 'max_iter': 100, 'random_state': 42}
        },
        {
            'model': LogisticRegression(C=1.0, max_iter=200, random_state=42),
            'name': 'LogisticRegression',
            'params': {'C': 1.0, 'max_iter': 200, 'random_state': 42}
        },
        {
            'model': LogisticRegression(C=10.0, max_iter=500, random_state=42),
            'name': 'LogisticRegression',
            'params': {'C': 10.0, 'max_iter': 500, 'random_state': 42}
        },
    ]
    
    results = []
    for exp in experiments:
        run_id, accuracy, model = train_model(
            exp['model'],
            exp['name'],
            exp['params'],
            X_train, X_test, y_train, y_test
        )
        results.append({
            'run_id': run_id,
            'name': exp['name'],
            'params': exp['params'],
            'accuracy': accuracy,
            'model': model
        })
    
    return results


def find_best_model(results):
    print("\n" + "="*60)
    print("🏆 ПОШУК НАЙКРАЩОЇ МОДЕЛІ")
    print("="*60)
    
    best_result = max(results, key=lambda x: x['accuracy'])
    
    print(f"\n✓ Найкраща модель:")
    print(f"  - Модель: {best_result['name']}")
    print(f"  - Параметри: {best_result['params']}")
    print(f"  - Accuracy: {best_result['accuracy']:.4f}")
    print(f"  - Run ID: {best_result['run_id']}")
    
    return best_result


def save_best_model(best_result):
    print("\n" + "="*60)
    print("💾 ЗБЕРЕЖЕННЯ НАЙКРАЩОЇ МОДЕЛІ")
    print("="*60)
    
    best_model_dir = "../best_model"
    
    if os.path.exists(best_model_dir):
        shutil.rmtree(best_model_dir)
    
    os.makedirs(best_model_dir, exist_ok=True)
    
    model_uri = f"runs:/{best_result['run_id']}/model"
    mlflow.sklearn.save_model(
        mlflow.sklearn.load_model(model_uri),
        best_model_dir
    )
    
    info_file = os.path.join(best_model_dir, "model_info.txt")
    with open(info_file, 'w') as f:
        f.write(f"Best Model Information\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Model Type: {best_result['name']}\n")
        f.write(f"Parameters: {best_result['params']}\n")
        f.write(f"Accuracy: {best_result['accuracy']:.4f}\n")
        f.write(f"MLflow Run ID: {best_result['run_id']}\n")
        f.write(f"Saved at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"✓ Модель збережено в директорії: {best_model_dir}")
    print(f"✓ Інформація про модель: {info_file}")


def print_summary(results):
    print("\n" + "="*60)
    print("📊 ПІДСУМОК ЕКСПЕРИМЕНТІВ")
    print("="*60)
    
    print(f"\n{'№':<3} {'Model':<20} {'Accuracy':<10} {'Run ID':<40}")
    print("-" * 75)
    
    for i, result in enumerate(sorted(results, key=lambda x: x['accuracy'], reverse=True), 1):
        print(f"{i:<3} {result['name']:<20} {result['accuracy']:<10.4f} {result['run_id']:<40}")
    
    print("\n" + "="*60)


def main():
    try:
        print("\n🎯 MLflow Experiments with Prometheus Integration")
        print(f"📍 MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
        print(f"📍 PushGateway URL: {PUSHGATEWAY_URL}")
        
        results = run_experiments()
        print_summary(results)
        best_result = find_best_model(results)
        save_best_model(best_result)
        
        print("\n" + "="*60)
        print("✅ ЕКСПЕРИМЕНТИ ЗАВЕРШЕНО УСПІШНО!")
        print("="*60)
        print(f"\n📌 Переглянути результати в MLflow UI:")
        print(f"   {MLFLOW_TRACKING_URI}")
        print(f"\n📌 Переглянути метрики в Prometheus/Grafana:")
        print(f"   Metrics: mlflow_accuracy, mlflow_f1_score, mlflow_precision, mlflow_recall")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
