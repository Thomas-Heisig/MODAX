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
import uvicorn
from ai_service import app

# Configure logging at application entry point
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("MODAX AI Layer Starting")
    logger.info("=" * 60)

    # Start API server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
