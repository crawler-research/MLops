import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Logging training metrics")
    
    source = event.get('source', 'unknown')
    commit = event.get('commit', 'unknown')
    validation_status = event.get('validation_status', 'unknown')
    
    metrics = {
        'accuracy': 0.95,
        'loss': 0.05,
        'precision': 0.93,
        'recall': 0.94,
        'f1_score': 0.935,
        'training_time': 120,
        'epochs': 10
    }
    
    metadata = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source': source,
        'commit': commit,
        'validation_status': validation_status,
        'model_version': f'v1.0.{commit[:7]}' if commit != 'unknown' else 'v1.0.0',
        'environment': 'aws'
    }
    
    logger.info(f"Metrics: {json.dumps(metrics)}")
    logger.info(f"Metadata: {json.dumps(metadata)}")
    
    return {
        'statusCode': 200,
        'message': 'Metrics logged',
        'metrics': metrics,
        'metadata': metadata,
        'training_status': 'completed'
    }
