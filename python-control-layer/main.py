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
- OPC UA server for industrial integration
"""
import logging
import signal
import sys
import os
import asyncio
import time
import uvicorn
from pythonjsonlogger import jsonlogger
from config import config
from control_layer import ControlLayer
import control_api
from opcua_server import init_opcua_server, stop_opcua_server, get_opcua_server

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
opcua_server_task = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if control_layer_instance:
        control_layer_instance.stop()
    
    # Stop OPC UA server if running
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stop_opcua_server())
    loop.close()
    
    sys.exit(0)


async def start_opcua_background():
    """Start OPC UA server in background"""
    if config.opcua.enabled:
        try:
            logger.info("Starting OPC UA server...")
            await init_opcua_server(
                enable=True,
                endpoint=config.opcua.endpoint,
                enable_security=config.opcua.enable_security
            )
            logger.info("OPC UA server started")
        except Exception as e:
            logger.error("Failed to start OPC UA server", extra={"error": str(e)}, exc_info=True)
            logger.warning("Continuing without OPC UA server")


def main():
    """Main entry point - Fault tolerant startup"""
    global control_layer_instance, opcua_server_task

    logger.info("MODAX Control Layer Starting", extra={"component": "main"})

    # Validate configuration before starting
    try:
        logger.info("Validating configuration...")
        config.validate()
    except Exception as e:
        logger.error("Configuration validation failed", extra={"error": str(e)}, exc_info=True)
        logger.warning("Using default configuration values where possible")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start control layer with fault tolerance
    try:
        control_layer_instance = ControlLayer(config)
        control_api.set_control_layer(control_layer_instance)
    except Exception as e:
        logger.error("Failed to create control layer instance", extra={"error": str(e)}, exc_info=True)
        logger.error("Cannot continue without control layer. Exiting.")
        sys.exit(1)

    # Start control layer with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Starting control layer (attempt {attempt + 1}/{max_retries})...")
            control_layer_instance.start()
            logger.info("Control layer started successfully")
            break
        except Exception as e:
            logger.error(
                f"Failed to start control layer (attempt {attempt + 1}/{max_retries})",
                extra={"error": str(e)}, exc_info=True)
            if attempt < max_retries - 1:
                logger.info("Retrying in 2 seconds...")
                # Blocking sleep is acceptable during startup retry
                time.sleep(2)
            else:
                logger.warning("Control layer failed to start, continuing with API only")

    # Start OPC UA server if enabled (non-critical)
    if config.opcua.enabled:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_opcua_background())
        except Exception as e:
            logger.error("Failed to initialize OPC UA", extra={"error": str(e)}, exc_info=True)
            logger.warning("Continuing without OPC UA server")

    # Start API server in main thread - This MUST succeed for the service to be useful
    try:
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
        logger.error("Failed to start API server", extra={"error": str(e)}, exc_info=True)
        logger.error("API server is critical. Shutting down.")
        
        # Cleanup
        if control_layer_instance:
            try:
                control_layer_instance.stop()
            except Exception as cleanup_error:
                logger.error("Error during cleanup", extra={"error": str(cleanup_error)})
        
        # Stop OPC UA server
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(stop_opcua_server())
            loop.close()
        except Exception as cleanup_error:
            logger.error("Error stopping OPC UA", extra={"error": str(cleanup_error)})
        
        sys.exit(1)


if __name__ == "__main__":
    main()
