import os
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import pickle
import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response
import joblib

try:
    from alibi_detect.cd import TabularDrift
    DRIFT_DETECTOR_AVAILABLE = True
except ImportError:
    DRIFT_DETECTOR_AVAILABLE = False
    print("Warning: Alibi Detect not available. Drift detection disabled.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Model Inference Service",
    description="Inference service with drift detection and monitoring",
    version="1.0.0"
)

REQUEST_COUNT = Counter(
    'inference_requests_total',
    'Total number of inference requests',
    ['status']
)
REQUEST_LATENCY = Histogram(
    'inference_request_duration_seconds',
    'Request latency in seconds'
)
DRIFT_DETECTED = Counter(
    'drift_detections_total',
    'Total number of drift detections'
)
DRIFT_SCORE = Gauge(
    'drift_score',
    'Current drift score'
)
MODEL_PREDICTIONS = Counter(
    'model_predictions_total',
    'Total predictions by class',
    ['predicted_class']
)

model = None
drift_detector = None
reference_data = None


class PredictionRequest(BaseModel):
    features: List[float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [5.1, 3.5, 1.4, 0.2]
            }
        }


class PredictionResponse(BaseModel):
    prediction: int
    probability: Optional[List[float]] = None
    drift_detected: bool = False
    drift_score: Optional[float] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 0,
                "probability": [0.95, 0.03, 0.02],
                "drift_detected": False,
                "drift_score": 0.15,
                "timestamp": "2025-10-22T10:30:00"
            }
        }


def load_model():
    global model
    
    default_path = "models/model.pkl" if not os.path.exists("/app") else "/app/models/model.pkl"
    model_path = os.getenv("MODEL_PATH", default_path)
    
    try:
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            logger.info(f"Model loaded successfully from {model_path}")
        else:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.datasets import load_iris
            
            logger.warning(f"Model not found at {model_path}. Creating mock model.")
            X, y = load_iris(return_X_y=True)
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X, y)
            
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump(model, model_path)
            logger.info(f"Mock model created and saved to {model_path}")
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise


def load_drift_detector():
    global drift_detector, reference_data
    
    if not DRIFT_DETECTOR_AVAILABLE:
        logger.warning("Drift detector not available")
        return
    
    default_drift_path = "models/drift_detector.pkl" if not os.path.exists("/app") else "/app/models/drift_detector.pkl"
    default_ref_path = "models/reference_data.npy" if not os.path.exists("/app") else "/app/models/reference_data.npy"
    
    drift_detector_path = os.getenv("DRIFT_DETECTOR_PATH", default_drift_path)
    reference_data_path = os.getenv("REFERENCE_DATA_PATH", default_ref_path)
    
    try:
        if os.path.exists(drift_detector_path) and os.path.exists(reference_data_path):
            with open(drift_detector_path, 'rb') as f:
                drift_detector = pickle.load(f)
            reference_data = np.load(reference_data_path)
            logger.info("Drift detector loaded successfully")
        else:
            from sklearn.datasets import load_iris
            X, _ = load_iris(return_X_y=True)
            reference_data = X[:100]
            
            drift_detector = TabularDrift(
                reference_data,
                p_val=0.05,
                categories_per_feature=None
            )
            
            os.makedirs(os.path.dirname(drift_detector_path), exist_ok=True)
            with open(drift_detector_path, 'wb') as f:
                pickle.dump(drift_detector, f)
            np.save(reference_data_path, reference_data)
            
            logger.info("Drift detector initialized with reference data")
            
    except Exception as e:
        logger.error(f"Error loading drift detector: {e}")
        drift_detector = None


def predict(features: List[float]) -> Dict:
    if model is None:
        raise ValueError("Model not loaded")
    
    X = np.array(features).reshape(1, -1)
    prediction = int(model.predict(X)[0])
    
    probability = None
    if hasattr(model, 'predict_proba'):
        probability = model.predict_proba(X)[0].tolist()
    
    MODEL_PREDICTIONS.labels(predicted_class=str(prediction)).inc()
    
    return {
        "prediction": prediction,
        "probability": probability
    }


def check_drift(features: List[float]) -> Dict:
    if drift_detector is None or not DRIFT_DETECTOR_AVAILABLE:
        return {"drift_detected": False, "drift_score": None}
    
    try:
        X = np.array(features).reshape(1, -1)
        drift_result = drift_detector.predict(X)
        
        is_drift = bool(drift_result['data']['is_drift'])
        drift_score = float(drift_result['data']['distance'])
        
        if is_drift:
            DRIFT_DETECTED.inc()
            logger.warning(f"DRIFT DETECTED! Score: {drift_score}")
            print(f"[ALERT] Drift detected at {datetime.now().isoformat()} - Score: {drift_score}")
        
        DRIFT_SCORE.set(drift_score)
        
        return {
            "drift_detected": is_drift,
            "drift_score": drift_score
        }
        
    except Exception as e:
        logger.error(f"Error in drift detection: {e}")
        return {"drift_detected": False, "drift_score": None}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting ML Inference Service...")
    load_model()
    load_drift_detector()
    logger.info("Service ready!")


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "ML Inference Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "drift_detector_loaded": drift_detector is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(request: PredictionRequest, http_request: Request):
    start_time = time.time()
    
    try:
        logger.info(f"Prediction request received: {request.features}")
        print(f"[LOG] Incoming request: {json.dumps({'features': request.features, 'timestamp': datetime.now().isoformat()})}")
        
        pred_result = predict(request.features)
        drift_result = check_drift(request.features)
        
        response = PredictionResponse(
            prediction=pred_result["prediction"],
            probability=pred_result.get("probability"),
            drift_detected=drift_result["drift_detected"],
            drift_score=drift_result.get("drift_score"),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Prediction: {response.prediction}, Drift: {response.drift_detected}")
        print(f"[LOG] Response: {json.dumps(response.dict())}")
        
        REQUEST_COUNT.labels(status='success').inc()
        REQUEST_LATENCY.observe(time.time() - start_time)
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        REQUEST_COUNT.labels(status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


@app.get("/model/info")
async def model_info():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    info = {
        "model_type": type(model).__name__,
        "timestamp": datetime.now().isoformat()
    }
    
    if hasattr(model, 'n_features_in_'):
        info["n_features"] = model.n_features_in_
    if hasattr(model, 'classes_'):
        info["classes"] = model.classes_.tolist()
    
    return info


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
