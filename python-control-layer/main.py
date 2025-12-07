"""
Main entry point for MODAX Control Layer.

This module initializes and starts the Control Layer, which coordinates
data flow between the field layer (ESP32), AI layer, and HMI layer.
It provides a REST API for monitoring and control.

Features:
- MQTT communication with field devices
- Data aggregation for AI analysis
- REST API for HMI integration
- Safety monitoring and command validation
"""
import logging
import signal
import sys
import os
import uvicorn
from pythonjsonlogger import jsonlogger
from config import config
from control_layer import ControlLayer
import control_api

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

# Global control layer instance
control_layer_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if control_layer_instance:
        control_layer_instance.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    global control_layer_instance

    logger.info("MODAX Control Layer Starting", extra={"component": "main"})

    # Validate configuration before starting
    logger.info("Validating configuration...")
    config.validate()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start control layer
    control_layer_instance = ControlLayer(config)
    control_api.set_control_layer(control_layer_instance)

    try:
        # Start control layer
        control_layer_instance.start()

        # Start API server in main thread
        logger.info("Starting API server", extra={
            "host": config.control.api_host,
            "port": config.control.api_port
        })
        uvicorn.run(
            control_api.app,
            host=config.control.api_host,
            port=config.control.api_port,
            log_level="info"
        )

    except Exception as e:
        logger.error("Error in control layer", extra={"error": str(e)}, exc_info=True)
        if control_layer_instance:
            control_layer_instance.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
