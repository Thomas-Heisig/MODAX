"""Wear Prediction - Predicts component wear based on operating conditions"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

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
        self.nominal_lifetime = 10000  # 10,000 hours baseline
        
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
            if avg_current > 5.0:
                load_factor = (avg_current / 5.0) ** 1.5
                wear_factor *= load_factor
                contributing_factors.append(f"High load operation ({avg_current:.1f}A)")
            
            # Current spikes cause additional wear
            if current_max > 8.0:
                spike_factor = 1.1 + (current_max - 8.0) * 0.05
                wear_factor *= spike_factor
                contributing_factors.append(f"Current spikes ({current_max:.1f}A)")
        
        # Factor 2: Vibration (indicates bearing/alignment issues)
        vibration = sensor_data.get('vibration_mean', {})
        vib_magnitude = vibration.get('magnitude', 0)
        
        if vib_magnitude > 3.0:
            vib_factor = 1.0 + (vib_magnitude - 3.0) * 0.15
            wear_factor *= vib_factor
            contributing_factors.append(f"Elevated vibration ({vib_magnitude:.2f} m/s²)")
        
        # Check for vibration imbalance (misalignment)
        vib_std = sensor_data.get('vibration_std', {})
        if vib_std:
            std_magnitude = vib_std.get('magnitude', 0)
            if std_magnitude > 1.0:
                wear_factor *= 1.15
                contributing_factors.append("Vibration variability (possible misalignment)")
        
        # Factor 3: Temperature (thermal stress)
        temperature_mean = sensor_data.get('temperature_mean', [])
        temperature_max = sensor_data.get('temperature_max', [])
        
        if temperature_max:
            max_temp = max(temperature_max)
            
            # Elevated temperature accelerates wear
            if max_temp > 50.0:
                temp_factor = 1.0 + (max_temp - 50.0) * 0.02
                wear_factor *= temp_factor
                contributing_factors.append(f"Elevated temperature ({max_temp:.1f}°C)")
            
            # Temperature cycling causes additional fatigue
            if temperature_mean:
                avg_temp = np.mean(temperature_mean)
                temp_range = max_temp - avg_temp
                if temp_range > 15.0:
                    wear_factor *= 1.1
                    contributing_factors.append("Temperature cycling")
        
        # Factor 4: Operating time accumulation
        if device_id not in self.wear_rates:
            self.wear_rates[device_id] = 0.0
        
        # Accumulate wear (in production, this would be persistent)
        # For demo, use a simplified model
        sample_count = sensor_data.get('sample_count', 0)
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
        if wear_level > 0.7:
            contributing_factors.append(f"High accumulated wear ({wear_level:.1%})")
        elif wear_level > 0.5:
            contributing_factors.append(f"Moderate accumulated wear ({wear_level:.1%})")
        
        # Confidence decreases with wear level (more uncertainty at high wear)
        confidence = 0.75 - (wear_level * 0.2)
        
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
