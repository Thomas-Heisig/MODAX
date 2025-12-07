"""Interface to AI Layer - Handles communication with AI analysis components"""
import logging
import requests
from typing import Optional
from data_aggregator import AggregatedData
from config import config

logger = logging.getLogger(__name__)


def request_ai_analysis(aggregated_data: AggregatedData) -> Optional[dict]:
    """
    Request AI analysis from the AI layer

    Args:
        aggregated_data: Aggregated sensor data

    Returns:
        AI analysis results or None if failed
    """
    try:
        # Prepare data for AI layer
        payload = {
            "device_id": aggregated_data.device_id,
            "time_window_start": aggregated_data.time_window_start,
            "time_window_end": aggregated_data.time_window_end,
            "current_mean": aggregated_data.current_mean,
            "current_std": aggregated_data.current_std,
            "current_max": aggregated_data.current_max,
            "vibration_mean": aggregated_data.vibration_mean,
            "vibration_std": aggregated_data.vibration_std,
            "vibration_max": aggregated_data.vibration_max,
            "temperature_mean": aggregated_data.temperature_mean,
            "temperature_max": aggregated_data.temperature_max,
            "sample_count": aggregated_data.sample_count
        }

        # Send request to AI layer with configurable timeout
        response = requests.post(
            config.control.ai_layer_url,
            json=payload,
            timeout=config.control.ai_layer_timeout
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"AI layer returned error: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to AI layer - is it running?")
        return None
    except Exception as e:
        logger.error(f"Error requesting AI analysis: {e}")
        return None
