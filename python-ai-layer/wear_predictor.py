"""Wear Prediction - Predicts component wear based on operating conditions"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

# Wear prediction threshold constants
CURRENT_NORMAL_THRESHOLD = 5.0  # Amperes - normal operating current
CURRENT_HIGH_LOAD_EXPONENT = 1.5  # Exponent for high load wear factor
CURRENT_SPIKE_THRESHOLD = 8.0  # Amperes - current spike threshold
CURRENT_SPIKE_BASE_FACTOR = 1.1  # Base wear factor for current spikes
CURRENT_SPIKE_INCREMENT = 0.05  # Incremental wear factor per amp above threshold
VIBRATION_NORMAL_THRESHOLD = 3.0  # m/s² - normal vibration level
VIBRATION_WEAR_FACTOR = 0.15  # Wear factor multiplier per m/s² above threshold
VIBRATION_STD_THRESHOLD = 1.0  # m/s² - vibration variability threshold
VIBRATION_STD_WEAR_FACTOR = 1.15  # Wear factor for high vibration variability
TEMPERATURE_NORMAL_THRESHOLD = 50.0  # °C - normal operating temperature
TEMPERATURE_WEAR_FACTOR = 0.02  # Wear factor per °C above threshold
TEMPERATURE_CYCLING_THRESHOLD = 15.0  # °C - temperature cycling range
TEMPERATURE_CYCLING_FACTOR = 1.1  # Wear factor for temperature cycling
WEAR_HIGH_THRESHOLD = 0.7  # High wear level (70%)
WEAR_MODERATE_THRESHOLD = 0.5  # Moderate wear level (50%)
WEAR_MEDIUM_THRESHOLD = 0.4  # Medium wear level (40%)
CONFIDENCE_BASE = 0.75  # Base confidence level
CONFIDENCE_WEAR_PENALTY = 0.2  # Confidence penalty factor based on wear level
NOMINAL_LIFETIME_HOURS = 10000  # Baseline component lifetime in hours

@dataclass
class WearPrediction:
    """Wear prediction result"""
    wear_level: float  # 0.0 to 1.0
    estimated_remaining_hours: int
    contributing_factors: List[str]
    confidence: float

class SimpleWearPredictor:
    """
    Simple wear prediction model based on cumulative stress factors
    Uses empirical models from industrial machinery maintenance
    """
    
    def __init__(self):
        # Wear accumulation factors (hours of operation equivalent per actual hour)
        self.wear_rates: Dict[str, float] = {}
        
        # Typical component lifetimes (hours)
        self.nominal_lifetime = NOMINAL_LIFETIME_HOURS
        
    def predict_wear(self, sensor_data: dict, device_id: str) -> WearPrediction:
        """
        Predict wear level based on sensor data
        
        Args:
            sensor_data: Aggregated sensor statistics
            device_id: Device identifier
            
        Returns:
            WearPrediction with wear level and estimated remaining life
        """
        contributing_factors = []
        wear_factor = 1.0  # Baseline wear rate multiplier
        
        # Factor 1: Current load
        current_mean = sensor_data.get('current_mean', [])
        if current_mean:
            avg_current = np.mean(current_mean)
            current_max = max(sensor_data.get('current_max', [0]))
            
            # High current increases wear exponentially
            if avg_current > CURRENT_NORMAL_THRESHOLD:
                load_factor = (avg_current / CURRENT_NORMAL_THRESHOLD) ** CURRENT_HIGH_LOAD_EXPONENT
                wear_factor *= load_factor
                contributing_factors.append(f"High load operation ({avg_current:.1f}A)")
            
            # Current spikes cause additional wear
            if current_max > CURRENT_SPIKE_THRESHOLD:
                spike_factor = CURRENT_SPIKE_BASE_FACTOR + (current_max - CURRENT_SPIKE_THRESHOLD) * CURRENT_SPIKE_INCREMENT
                wear_factor *= spike_factor
                contributing_factors.append(f"Current spikes ({current_max:.1f}A)")
        
        # Factor 2: Vibration (indicates bearing/alignment issues)
        vibration = sensor_data.get('vibration_mean', {})
        vib_magnitude = vibration.get('magnitude', 0)
        
        if vib_magnitude > VIBRATION_NORMAL_THRESHOLD:
            vib_factor = 1.0 + (vib_magnitude - VIBRATION_NORMAL_THRESHOLD) * VIBRATION_WEAR_FACTOR
            wear_factor *= vib_factor
            contributing_factors.append(f"Elevated vibration ({vib_magnitude:.2f} m/s²)")
        
        # Check for vibration imbalance (misalignment)
        vib_std = sensor_data.get('vibration_std', {})
        if vib_std:
            std_magnitude = vib_std.get('magnitude', 0)
            if std_magnitude > VIBRATION_STD_THRESHOLD:
                wear_factor *= VIBRATION_STD_WEAR_FACTOR
                contributing_factors.append("Vibration variability (possible misalignment)")
        
        # Factor 3: Temperature (thermal stress)
        temperature_mean = sensor_data.get('temperature_mean', [])
        temperature_max = sensor_data.get('temperature_max', [])
        
        if temperature_max:
            max_temp = max(temperature_max)
            
            # Elevated temperature accelerates wear
            if max_temp > TEMPERATURE_NORMAL_THRESHOLD:
                temp_factor = 1.0 + (max_temp - TEMPERATURE_NORMAL_THRESHOLD) * TEMPERATURE_WEAR_FACTOR
                wear_factor *= temp_factor
                contributing_factors.append(f"Elevated temperature ({max_temp:.1f}°C)")
            
            # Temperature cycling causes additional fatigue
            if temperature_mean:
                avg_temp = np.mean(temperature_mean)
                temp_range = max_temp - avg_temp
                if temp_range > TEMPERATURE_CYCLING_THRESHOLD:
                    wear_factor *= TEMPERATURE_CYCLING_FACTOR
                    contributing_factors.append("Temperature cycling")
        
        # Factor 4: Operating time accumulation
        if device_id not in self.wear_rates:
            self.wear_rates[device_id] = 0.0
        
        # Accumulate wear (in production, this would be persistent)
        # For demo, use a simplified model based on time window
        time_window = sensor_data.get('time_window_end', 0) - sensor_data.get('time_window_start', 0)
        
        # Accumulate wear based on operating time and conditions
        wear_increment = (time_window / 3600.0) * wear_factor  # Convert to hours
        self.wear_rates[device_id] += wear_increment
        
        # Calculate wear level (0.0 to 1.0)
        accumulated_hours = self.wear_rates[device_id]
        wear_level = min(1.0, accumulated_hours / self.nominal_lifetime)
        
        # Estimate remaining hours
        remaining_nominal_hours = max(0, self.nominal_lifetime - accumulated_hours)
        estimated_remaining_hours = int(remaining_nominal_hours / wear_factor)
        
        # Add wear level to factors
        if wear_level > WEAR_HIGH_THRESHOLD:
            contributing_factors.append(f"High accumulated wear ({wear_level:.1%})")
        elif wear_level > WEAR_MODERATE_THRESHOLD:
            contributing_factors.append(f"Moderate accumulated wear ({wear_level:.1%})")
        
        # Confidence decreases with wear level (more uncertainty at high wear)
        confidence = CONFIDENCE_BASE - (wear_level * CONFIDENCE_WEAR_PENALTY)
        
        if not contributing_factors:
            contributing_factors.append("Normal operating conditions")
        
        return WearPrediction(
            wear_level=wear_level,
            estimated_remaining_hours=estimated_remaining_hours,
            contributing_factors=contributing_factors,
            confidence=confidence
        )
    
    def reset_wear(self, device_id: str):
        """Reset wear counter (e.g., after maintenance)"""
        if device_id in self.wear_rates:
            self.wear_rates[device_id] = 0.0
