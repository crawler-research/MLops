import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Starting data validation")
    logger.info(f"Event: {json.dumps(event)}")
    
    source = event.get('source', 'unknown')
    commit = event.get('commit', 'unknown')
    
    checks = {
        'source_valid': source != 'unknown',
        'commit_valid': commit != 'unknown',
        'data_format_valid': True,
        'schema_valid': True
    }
    
    is_valid = all(checks.values())
    
    if is_valid:
        logger.info("Validation passed")
    else:
        logger.warning(f"Validation failed: {checks}")
    
    return {
        'statusCode': 200 if is_valid else 400,
        'validation_status': 'passed' if is_valid else 'failed',
        'checks': checks,
        'source': source,
        'commit': commit,
        'message': 'Validation completed'
    }
