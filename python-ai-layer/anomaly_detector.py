"""Statistical Anomaly Detection - Simple statistical models for anomaly detection"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats

@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    score: float  # 0.0 to 1.0
    description: str
    confidence: float

class StatisticalAnomalyDetector:
    """
    Statistical anomaly detector using z-score and moving statistics
    This is a simple, interpretable approach suitable for industrial control systems
    """
    
    def __init__(self, z_threshold: float = 3.0):
        """
        Args:
            z_threshold: Number of standard deviations for anomaly threshold
        """
        self.z_threshold = z_threshold
        
        # Historical statistics (would be loaded from storage in production)
        self.baseline_stats: Dict[str, Dict[str, Tuple[float, float]]] = {}
        
    def detect_current_anomaly(self, current_mean: List[float], 
                               current_max: List[float],
                               device_id: str) -> AnomalyResult:
        """Detect current anomalies"""
        anomalies = []
        max_score = 0.0
        
        # Check each motor
        for i, (mean, max_val) in enumerate(zip(current_mean, current_max)):
            # Check against historical baseline
            if device_id in self.baseline_stats and f'current_{i}' in self.baseline_stats[device_id]:
                baseline_mean, baseline_std = self.baseline_stats[device_id][f'current_{i}']
                
                if baseline_std > 0:
                    z_score = abs((mean - baseline_mean) / baseline_std)
                    
                    if z_score > self.z_threshold:
                        score = min(1.0, z_score / (self.z_threshold * 2))
                        max_score = max(max_score, score)
                        anomalies.append(f"Motor {i+1} current anomaly: {mean:.2f}A (expected {baseline_mean:.2f}±{baseline_std:.2f})")
            
            # Simple threshold checks (domain knowledge)
            if max_val > 12.0:  # Absolute maximum threshold
                max_score = max(max_score, 0.9)
                anomalies.append(f"Motor {i+1} current spike: {max_val:.2f}A")
            
            # Detect current imbalance between motors
            if i > 0 and len(current_mean) > 1:
                diff = abs(current_mean[i] - current_mean[0])
                if diff > 2.0:  # More than 2A difference
                    max_score = max(max_score, 0.6)
                    anomalies.append(f"Current imbalance detected: {diff:.2f}A difference")
        
        if anomalies:
            return AnomalyResult(
                is_anomaly=True,
                score=max_score,
                description="; ".join(anomalies),
                confidence=0.85
            )
        else:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                description="Current levels normal",
                confidence=0.85
            )
    
    def detect_vibration_anomaly(self, vibration_mean: Dict[str, float],
                                 vibration_max: Dict[str, float],
                                 device_id: str) -> AnomalyResult:
        """Detect vibration anomalies"""
        anomalies = []
        max_score = 0.0
        
        # Check overall magnitude
        magnitude = vibration_mean.get('magnitude', 0)
        max_magnitude = vibration_max.get('magnitude', 0)
        
        # Threshold checks (typical values for industrial machinery)
        if magnitude > 5.0:  # m/s² - moderate concern
            max_score = max(max_score, 0.6)
            anomalies.append(f"Elevated vibration: {magnitude:.2f} m/s²")
        
        if max_magnitude > 10.0:  # m/s² - high concern
            max_score = max(max_score, 0.9)
            anomalies.append(f"High vibration spike: {max_magnitude:.2f} m/s²")
        
        # Check for axis imbalance (could indicate misalignment)
        x = abs(vibration_mean.get('x', 0))
        y = abs(vibration_mean.get('y', 0))
        z = abs(vibration_mean.get('z', 0))
        
        axes = [x, y, z]
        if max(axes) > 2 * min(axes):  # One axis significantly higher
            max_score = max(max_score, 0.5)
            dominant_axis = ['X', 'Y', 'Z'][axes.index(max(axes))]
            anomalies.append(f"Vibration imbalance on {dominant_axis} axis")
        
        # Check against baseline
        if device_id in self.baseline_stats and 'vibration_magnitude' in self.baseline_stats[device_id]:
            baseline_mean, baseline_std = self.baseline_stats[device_id]['vibration_magnitude']
            
            if baseline_std > 0:
                z_score = abs((magnitude - baseline_mean) / baseline_std)
                
                if z_score > self.z_threshold:
                    score = min(1.0, z_score / (self.z_threshold * 2))
                    max_score = max(max_score, score)
                    anomalies.append(f"Vibration pattern anomaly (z-score: {z_score:.2f})")
        
        if anomalies:
            return AnomalyResult(
                is_anomaly=True,
                score=max_score,
                description="; ".join(anomalies),
                confidence=0.80
            )
        else:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                description="Vibration levels normal",
                confidence=0.80
            )
    
    def detect_temperature_anomaly(self, temperature_mean: List[float],
                                   temperature_max: List[float],
                                   device_id: str) -> AnomalyResult:
        """Detect temperature anomalies"""
        anomalies = []
        max_score = 0.0
        
        for i, (mean, max_val) in enumerate(zip(temperature_mean, temperature_max)):
            # Absolute thresholds
            if max_val > 70.0:
                max_score = max(max_score, 0.8)
                anomalies.append(f"Sensor {i+1} high temperature: {max_val:.1f}°C")
            elif max_val > 60.0:
                max_score = max(max_score, 0.5)
                anomalies.append(f"Sensor {i+1} elevated temperature: {max_val:.1f}°C")
            
            # Check rate of change (rapid temperature increase)
            if device_id in self.baseline_stats and f'temp_{i}' in self.baseline_stats[device_id]:
                baseline_mean, baseline_std = self.baseline_stats[device_id][f'temp_{i}']
                
                temp_increase = mean - baseline_mean
                if temp_increase > 10.0:  # More than 10°C increase
                    max_score = max(max_score, 0.7)
                    anomalies.append(f"Sensor {i+1} rapid temperature increase: +{temp_increase:.1f}°C")
        
        if anomalies:
            return AnomalyResult(
                is_anomaly=True,
                score=max_score,
                description="; ".join(anomalies),
                confidence=0.90
            )
        else:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                description="Temperature levels normal",
                confidence=0.90
            )
    
    def update_baseline(self, device_id: str, sensor_data: dict):
        """Update baseline statistics with new data"""
        if device_id not in self.baseline_stats:
            self.baseline_stats[device_id] = {}
        
        # Update current baselines
        for i, current in enumerate(sensor_data.get('current_mean', [])):
            key = f'current_{i}'
            # Simple exponential moving average
            if key in self.baseline_stats[device_id]:
                old_mean, old_std = self.baseline_stats[device_id][key]
                new_mean = 0.9 * old_mean + 0.1 * current
                new_std = 0.9 * old_std + 0.1 * abs(current - new_mean)
            else:
                new_mean = current
                new_std = 0.5  # Initial estimate
            
            self.baseline_stats[device_id][key] = (new_mean, new_std)
        
        # Update vibration baseline
        vib_magnitude = sensor_data.get('vibration_mean', {}).get('magnitude', 0)
        if vib_magnitude > 0:
            key = 'vibration_magnitude'
            if key in self.baseline_stats[device_id]:
                old_mean, old_std = self.baseline_stats[device_id][key]
                new_mean = 0.9 * old_mean + 0.1 * vib_magnitude
                new_std = 0.9 * old_std + 0.1 * abs(vib_magnitude - new_mean)
            else:
                new_mean = vib_magnitude
                new_std = 0.5
            
            self.baseline_stats[device_id][key] = (new_mean, new_std)
        
        # Update temperature baselines
        for i, temp in enumerate(sensor_data.get('temperature_mean', [])):
            key = f'temp_{i}'
            if key in self.baseline_stats[device_id]:
                old_mean, old_std = self.baseline_stats[device_id][key]
                new_mean = 0.9 * old_mean + 0.1 * temp
                new_std = 0.9 * old_std + 0.1 * abs(temp - new_mean)
            else:
                new_mean = temp
                new_std = 2.0
            
            self.baseline_stats[device_id][key] = (new_mean, new_std)
