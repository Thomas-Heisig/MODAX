"""
Main entry point for MODAX AI Layer.

This module initializes and starts the AI analysis service, which provides
intelligent analysis of sensor data for anomaly detection, wear prediction,
and optimization recommendations.

Features:
- Statistical anomaly detection
- Empirical wear prediction
- Rule-based optimization recommendations
- REST API for analysis requests

IMPORTANT: This layer is ADVISORY ONLY and does not participate in
safety-critical decisions. All safety functions remain in the field layer.
"""
import logging
import sys
import os
import signal
import uvicorn
from pythonjsonlogger import jsonlogger
from ai_service import app

# Configure structured JSON logging
use_json_logs = os.getenv("USE_JSON_LOGS", "true").lower() == "true"

if use_json_logs:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={'asctime': 'timestamp', 'name': 'logger', 'levelname': 'level'}
    )
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

# Configuration
AI_HOST = os.getenv("AI_HOST", "0.0.0.0")
AI_PORT = int(os.getenv("AI_PORT", "8001"))


def validate_config():
    """Validate environment configuration"""
    errors = []
    
    if AI_PORT < 1 or AI_PORT > 65535:
        errors.append(f"Invalid AI_PORT: {AI_PORT} (must be 1-65535)")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("Configuration validation passed")
    return True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, exiting gracefully...")
    sys.exit(0)


def main():
    """Main entry point"""
    logger.info("MODAX AI Layer Starting", extra={"component": "main"})
    
    # Validate configuration
    validate_config()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start API server
    logger.info("Starting API server", extra={"host": AI_HOST, "port": AI_PORT})
    uvicorn.run(
        app,
        host=AI_HOST,
        port=AI_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
