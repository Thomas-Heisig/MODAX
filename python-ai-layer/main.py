"""Main entry point for AI Layer"""
import logging
import uvicorn
from ai_service import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
