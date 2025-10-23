import os
import sys
import logging
import argparse
from datetime import datetime
import pickle

import numpy as np
import joblib
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

try:
    from alibi_detect.cd import TabularDrift
    DRIFT_DETECTOR_AVAILABLE = True
except ImportError:
    DRIFT_DETECTOR_AVAILABLE = False
    print("Warning: Alibi Detect not available. Drift detector will not be created.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(data_path: str = None):
    if data_path and os.path.exists(data_path):
        logger.info(f"Loading custom data from {data_path}")
        data = np.load(data_path)
        X = data['X']
        y = data['y']
    else:
        logger.info("Loading Iris dataset")
        X, y = load_iris(return_X_y=True)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, **model_params):
    logger.info("Training Random Forest model...")
    
    default_params = {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42,
        'n_jobs': -1
    }
    default_params.update(model_params)
    
    model = RandomForestClassifier(**default_params)
    model.fit(X_train, y_train)
    
    logger.info("Model training completed")
    return model


def evaluate_model(model, X_test, y_test):
    logger.info("Evaluating model...")
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred))
    logger.info("\nConfusion Matrix:")
    logger.info("\n" + str(confusion_matrix(y_test, y_pred)))
    
    return {
        'accuracy': accuracy,
        'timestamp': datetime.now().isoformat()
    }


def save_model(model, model_path: str):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")


def create_drift_detector(reference_data, detector_path: str):
    if not DRIFT_DETECTOR_AVAILABLE:
        logger.warning("Alibi Detect not available. Skipping drift detector creation.")
        return
    
    logger.info("Creating drift detector...")
    
    drift_detector = TabularDrift(
        reference_data,
        p_val=0.05,
        categories_per_feature=None
    )
    
    os.makedirs(os.path.dirname(detector_path), exist_ok=True)
    with open(detector_path, 'wb') as f:
        pickle.dump(drift_detector, f)
    
    logger.info(f"Drift detector saved to {detector_path}")


def save_reference_data(data, data_path: str):
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    np.save(data_path, data)
    logger.info(f"Reference data saved to {data_path}")


def main():
    parser = argparse.ArgumentParser(description='Train ML model')
    parser.add_argument('--data-path', type=str, default=None,
                       help='Path to training data')
    parser.add_argument('--model-path', type=str, 
                       default='models/model.pkl',
                       help='Path to save trained model')
    parser.add_argument('--drift-detector-path', type=str,
                       default='models/drift_detector.pkl',
                       help='Path to save drift detector')
    parser.add_argument('--reference-data-path', type=str,
                       default='models/reference_data.npy',
                       help='Path to save reference data')
    parser.add_argument('--n-estimators', type=int, default=100,
                       help='Number of trees in random forest')
    parser.add_argument('--max-depth', type=int, default=10,
                       help='Maximum depth of trees')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Starting Model Training Pipeline")
    logger.info("="*60)
    
    X_train, X_test, y_train, y_test = load_data(args.data_path)
    
    model_params = {
        'n_estimators': args.n_estimators,
        'max_depth': args.max_depth
    }
    model = train_model(X_train, y_train, **model_params)
    
    metrics = evaluate_model(model, X_test, y_test)
    
    save_model(model, args.model_path)
    
    reference_data = X_train[:100]
    create_drift_detector(reference_data, args.drift_detector_path)
    save_reference_data(reference_data, args.reference_data_path)
    
    logger.info("="*60)
    logger.info("Training Pipeline Completed Successfully!")
    logger.info(f"Final Accuracy: {metrics['accuracy']:.4f}")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
