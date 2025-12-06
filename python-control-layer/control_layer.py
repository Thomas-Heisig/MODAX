"""Main Control Layer - Orchestrates data flow between field, AI, and HMI layers"""
import logging
import time
import threading
from typing import Dict, Optional
from config import Config
from data_aggregator import DataAggregator, SensorReading, SafetyStatus
from mqtt_handler import MQTTHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ControlLayer:
    """Main control layer coordinating all system components"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize components
        self.aggregator = DataAggregator(
            window_size_seconds=config.control.aggregation_window_seconds,
            max_points=config.control.max_data_points
        )
        
        self.mqtt = MQTTHandler(config.mqtt)
        
        # Set up MQTT callbacks
        self.mqtt.on_sensor_data = self._handle_sensor_data
        self.mqtt.on_safety_status = self._handle_safety_status
        self.mqtt.on_ai_analysis = self._handle_ai_analysis
        
        # AI analysis results cache
        self.ai_analysis_results: Dict[str, dict] = {}
        
        # Timing
        self.last_update_time = 0
        self.last_ai_analysis_time = 0
        
        # AI analysis thread
        self.ai_thread: Optional[threading.Thread] = None
        self.running = False
        
    def start(self):
        """Start the control layer"""
        logger.info("Starting MODAX Control Layer")
        
        # Connect to MQTT broker
        self.mqtt.connect()
        
        # Start AI analysis thread if enabled
        if self.config.control.ai_layer_enabled:
            self.running = True
            self.ai_thread = threading.Thread(target=self._ai_analysis_loop, daemon=True)
            self.ai_thread.start()
            logger.info("AI analysis thread started")
        
        logger.info("Control Layer started successfully")
    
    def stop(self):
        """Stop the control layer"""
        logger.info("Stopping MODAX Control Layer")
        
        self.running = False
        if self.ai_thread:
            self.ai_thread.join(timeout=5)
        
        self.mqtt.disconnect()
        logger.info("Control Layer stopped")
    
    def _handle_sensor_data(self, reading: SensorReading):
        """Handle incoming sensor data from field layer"""
        self.aggregator.add_sensor_reading(reading)
        self.last_update_time = time.time()
        
        logger.debug(f"Received sensor data from {reading.device_id}: "
                    f"currents={reading.motor_currents}, "
                    f"vib_mag={reading.vibration.get('magnitude', 0):.2f}")
    
    def _handle_safety_status(self, status: SafetyStatus):
        """Handle incoming safety status from field layer"""
        self.aggregator.update_safety_status(status)
        
        if not status.is_safe():
            logger.warning(f"SAFETY ALERT from {status.device_id}")
            # Could trigger notifications, alarms, etc.
    
    def _handle_ai_analysis(self, analysis: dict):
        """Handle AI analysis results"""
        device_id = analysis.get('device_id')
        if device_id:
            self.ai_analysis_results[device_id] = analysis
            self.last_ai_analysis_time = time.time()
            
            logger.info(f"Received AI analysis for {device_id}: "
                       f"anomaly={analysis.get('anomaly_detected')}, "
                       f"wear={analysis.get('predicted_wear_level', 0):.2%}")
    
    def _ai_analysis_loop(self):
        """Periodic AI analysis trigger"""
        from ai_interface import request_ai_analysis
        
        interval = self.config.control.ai_analysis_interval_seconds
        logger.info(f"AI analysis loop started with {interval}s interval")
        
        while self.running:
            try:
                time.sleep(interval)
                
                # Request AI analysis for each device
                for device_id in self.aggregator.get_device_ids():
                    # Get aggregated data
                    aggregated = self.aggregator.aggregate_for_ai(device_id)
                    
                    if aggregated:
                        # Request AI analysis
                        analysis = request_ai_analysis(aggregated)
                        
                        if analysis:
                            # Store and publish results
                            self.ai_analysis_results[device_id] = analysis
                            self.mqtt.publish_ai_analysis(analysis)
                            
                            logger.info(f"AI analysis completed for {device_id}")
                    
            except Exception as e:
                logger.error(f"Error in AI analysis loop: {e}")
    
    def get_latest_ai_analysis(self, device_id: str) -> Optional[dict]:
        """Get latest AI analysis for a device"""
        return self.ai_analysis_results.get(device_id)
    
    def send_control_command(self, command_type: str, parameters: dict):
        """Send control command"""
        # Safety check
        if not self.aggregator.is_system_safe():
            raise RuntimeError("Cannot send command: system not in safe state")
        
        command = {
            "timestamp": int(time.time() * 1000),
            "command_type": command_type,
            "parameters": parameters
        }
        
        self.mqtt.publish_control_command(command)
        logger.info(f"Sent control command: {command_type}")
    
    def get_last_update_time(self) -> float:
        """Get timestamp of last data update"""
        return self.last_update_time
    
    def get_last_ai_analysis_time(self) -> float:
        """Get timestamp of last AI analysis"""
        return self.last_ai_analysis_time
