"""Optimization Recommendations - Provides actionable recommendations"""
from typing import List

# Optimization recommendation threshold constants
CURRENT_HIGH_THRESHOLD = 6.0  # Amperes - high current consumption
CURRENT_OPTIMAL_MIN = 3.0  # Amperes - optimal range minimum
CURRENT_OPTIMAL_MAX = 5.0  # Amperes - optimal range maximum
CURRENT_IMBALANCE_THRESHOLD = 1.5  # Amperes - current imbalance threshold
CURRENT_SPIKE_RATIO = 1.5  # Ratio of max to avg for spike detection
VIBRATION_HIGH_THRESHOLD = 5.0  # m/s² - high vibration level
VIBRATION_ELEVATED_THRESHOLD = 3.0  # m/s² - elevated vibration level
VIBRATION_AXIS_IMBALANCE_FACTOR = 2.0  # Factor for axis imbalance detection
TEMPERATURE_HIGH_THRESHOLD = 60.0  # °C - high temperature threshold
TEMPERATURE_ELEVATED_THRESHOLD = 50.0  # °C - elevated temperature threshold
TEMPERATURE_CYCLING_THRESHOLD = 15.0  # °C - temperature cycling range
WEAR_URGENT_THRESHOLD = 0.8  # Urgent wear level (80%)
WEAR_MODERATE_THRESHOLD = 0.6  # Moderate wear level (60%)
WEAR_MEDIUM_THRESHOLD = 0.4  # Medium wear level (40%)
ANOMALY_HIGH_THRESHOLD = 0.7  # High anomaly score
ANOMALY_MODERATE_THRESHOLD = 0.5  # Moderate anomaly score
ANOMALY_LOW_THRESHOLD = 0.3  # Low anomaly score (normal operation)
ENERGY_EFFICIENCY_CURRENT_THRESHOLD = 5.0  # Amperes - for energy efficiency check
ENERGY_EFFICIENCY_TEMP_THRESHOLD = 45.0  # °C - for energy efficiency check

class OptimizationRecommender:
    """
    Generates optimization recommendations based on sensor analysis
    Provides actionable advice to improve efficiency and reduce wear
    """
    
    def generate_recommendations(self, sensor_data: dict, 
                                anomaly_score: float,
                                wear_level: float) -> List[str]:
        """
        Generate optimization recommendations
        
        Args:
            sensor_data: Aggregated sensor data
            anomaly_score: Current anomaly score
            wear_level: Current wear level
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Current-based recommendations
        current_mean = sensor_data.get('current_mean', [])
        current_max = sensor_data.get('current_max', [])
        
        if current_mean:
            avg_current = sum(current_mean) / len(current_mean)
            max_current = max(current_max) if current_max else 0
            
            # High current recommendations
            if avg_current > CURRENT_HIGH_THRESHOLD:
                recommendations.append(
                    "Consider reducing load or operating speed to decrease current consumption"
                )
            
            # Current imbalance
            if len(current_mean) > 1:
                current_diff = max(current_mean) - min(current_mean)
                if current_diff > CURRENT_IMBALANCE_THRESHOLD:
                    recommendations.append(
                        "Current imbalance detected - check for mechanical binding or motor issues"
                    )
            
            # Efficiency optimization
            if CURRENT_OPTIMAL_MIN < avg_current < CURRENT_OPTIMAL_MAX:
                recommendations.append(
                    "System operating in optimal current range - maintain current settings"
                )
            
            # Current spikes
            if max_current > avg_current * CURRENT_SPIKE_RATIO:
                recommendations.append(
                    "Frequent current spikes detected - consider smoother acceleration profiles"
                )
        
        # Vibration-based recommendations
        vibration = sensor_data.get('vibration_mean', {})
        vib_magnitude = vibration.get('magnitude', 0)
        
        if vib_magnitude > VIBRATION_HIGH_THRESHOLD:
            recommendations.append(
                "High vibration levels - schedule maintenance check for bearings and alignment"
            )
        elif vib_magnitude > VIBRATION_ELEVATED_THRESHOLD:
            recommendations.append(
                "Elevated vibration - consider re-balancing rotating components"
            )
        
        # Check for axis-specific vibration
        x = abs(vibration.get('x', 0))
        y = abs(vibration.get('y', 0))
        z = abs(vibration.get('z', 0))
        
        if max([x, y, z]) > VIBRATION_AXIS_IMBALANCE_FACTOR * min([x, y, z]):
            axes = ['X', 'Y', 'Z']
            dominant = axes[[x, y, z].index(max([x, y, z]))]
            recommendations.append(
                f"Dominant {dominant}-axis vibration suggests alignment issue in that direction"
            )
        
        # Temperature-based recommendations
        temperature_mean = sensor_data.get('temperature_mean', [])
        temperature_max = sensor_data.get('temperature_max', [])
        
        if temperature_max:
            max_temp = max(temperature_max)
            
            if max_temp > TEMPERATURE_HIGH_THRESHOLD:
                recommendations.append(
                    "High operating temperature - improve cooling or reduce duty cycle"
                )
            elif max_temp > TEMPERATURE_ELEVATED_THRESHOLD:
                recommendations.append(
                    "Monitor temperature trends - ensure adequate ventilation"
                )
            
            # Temperature range check
            if temperature_mean:
                avg_temp = sum(temperature_mean) / len(temperature_mean)
                temp_range = max_temp - avg_temp
                if temp_range > TEMPERATURE_CYCLING_THRESHOLD:
                    recommendations.append(
                        "Large temperature variations - consider thermal management improvements"
                    )
        
        # Wear-based recommendations
        if wear_level > WEAR_URGENT_THRESHOLD:
            recommendations.append(
                "URGENT: High wear level detected - schedule preventive maintenance immediately"
            )
        elif wear_level > WEAR_MODERATE_THRESHOLD:
            recommendations.append(
                "Moderate wear level - plan maintenance within next service window"
            )
        elif wear_level > WEAR_MEDIUM_THRESHOLD:
            recommendations.append(
                "Wear accumulation progressing normally - continue monitoring"
            )
        
        # Anomaly-based recommendations
        if anomaly_score > ANOMALY_HIGH_THRESHOLD:
            recommendations.append(
                "Significant anomaly detected - investigate system conditions promptly"
            )
        elif anomaly_score > ANOMALY_MODERATE_THRESHOLD:
            recommendations.append(
                "Minor anomaly detected - review recent operational changes"
            )
        
        # Preventive recommendations
        sample_count = sensor_data.get('sample_count', 0)
        if sample_count > 0:
            # Good data quality
            if anomaly_score < ANOMALY_LOW_THRESHOLD and wear_level < WEAR_MEDIUM_THRESHOLD and vib_magnitude < VIBRATION_ELEVATED_THRESHOLD:
                recommendations.append(
                    "System operating within normal parameters - no immediate action required"
                )
        
        # Energy efficiency recommendations
        if current_mean and temperature_mean:
            avg_current = sum(current_mean) / len(current_mean)
            avg_temp = sum(temperature_mean) / len(temperature_mean)
            
            # Estimate efficiency
            if avg_current > ENERGY_EFFICIENCY_CURRENT_THRESHOLD and avg_temp > ENERGY_EFFICIENCY_TEMP_THRESHOLD:
                recommendations.append(
                    "Consider optimizing operating parameters for better energy efficiency"
                )
        
        # If no specific recommendations, provide general guidance
        if not recommendations:
            recommendations.append(
                "Insufficient data for specific recommendations - continue normal operation"
            )
        
        return recommendations
