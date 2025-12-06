"""Optimization Recommendations - Provides actionable recommendations"""
from typing import List

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
            if avg_current > 6.0:
                recommendations.append(
                    "Consider reducing load or operating speed to decrease current consumption"
                )
            
            # Current imbalance
            if len(current_mean) > 1:
                current_diff = max(current_mean) - min(current_mean)
                if current_diff > 1.5:
                    recommendations.append(
                        "Current imbalance detected - check for mechanical binding or motor issues"
                    )
            
            # Efficiency optimization
            if 3.0 < avg_current < 5.0:
                recommendations.append(
                    "System operating in optimal current range - maintain current settings"
                )
            
            # Current spikes
            if max_current > avg_current * 1.5:
                recommendations.append(
                    "Frequent current spikes detected - consider smoother acceleration profiles"
                )
        
        # Vibration-based recommendations
        vibration = sensor_data.get('vibration_mean', {})
        vib_magnitude = vibration.get('magnitude', 0)
        
        if vib_magnitude > 5.0:
            recommendations.append(
                "High vibration levels - schedule maintenance check for bearings and alignment"
            )
        elif vib_magnitude > 3.0:
            recommendations.append(
                "Elevated vibration - consider re-balancing rotating components"
            )
        
        # Check for axis-specific vibration
        x = abs(vibration.get('x', 0))
        y = abs(vibration.get('y', 0))
        z = abs(vibration.get('z', 0))
        
        if max([x, y, z]) > 2 * min([x, y, z]):
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
            
            if max_temp > 60.0:
                recommendations.append(
                    "High operating temperature - improve cooling or reduce duty cycle"
                )
            elif max_temp > 50.0:
                recommendations.append(
                    "Monitor temperature trends - ensure adequate ventilation"
                )
            
            # Temperature range check
            if temperature_mean:
                avg_temp = sum(temperature_mean) / len(temperature_mean)
                temp_range = max_temp - avg_temp
                if temp_range > 15.0:
                    recommendations.append(
                        "Large temperature variations - consider thermal management improvements"
                    )
        
        # Wear-based recommendations
        if wear_level > 0.8:
            recommendations.append(
                "URGENT: High wear level detected - schedule preventive maintenance immediately"
            )
        elif wear_level > 0.6:
            recommendations.append(
                "Moderate wear level - plan maintenance within next service window"
            )
        elif wear_level > 0.4:
            recommendations.append(
                "Wear accumulation progressing normally - continue monitoring"
            )
        
        # Anomaly-based recommendations
        if anomaly_score > 0.7:
            recommendations.append(
                "Significant anomaly detected - investigate system conditions promptly"
            )
        elif anomaly_score > 0.5:
            recommendations.append(
                "Minor anomaly detected - review recent operational changes"
            )
        
        # Preventive recommendations
        sample_count = sensor_data.get('sample_count', 0)
        if sample_count > 0:
            # Good data quality
            if anomaly_score < 0.3 and wear_level < 0.4 and vib_magnitude < 3.0:
                recommendations.append(
                    "System operating within normal parameters - no immediate action required"
                )
        
        # Energy efficiency recommendations
        if current_mean and temperature_mean:
            avg_current = sum(current_mean) / len(current_mean)
            avg_temp = sum(temperature_mean) / len(temperature_mean)
            
            # Estimate efficiency
            if avg_current > 5.0 and avg_temp > 45.0:
                recommendations.append(
                    "Consider optimizing operating parameters for better energy efficiency"
                )
        
        # If no specific recommendations, provide general guidance
        if not recommendations:
            recommendations.append(
                "Insufficient data for specific recommendations - continue normal operation"
            )
        
        return recommendations
