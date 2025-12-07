"""Unit tests for Optimization Recommender module"""
import unittest
from optimizer import OptimizationRecommender


class TestOptimizationRecommender(unittest.TestCase):
    """Tests for OptimizationRecommender class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.recommender = OptimizationRecommender()
        self.base_sensor_data = {
            'current_mean': [5.0, 5.1, 4.9],
            'current_max': [6.0, 6.2, 5.8],
            'vibration_mean': {'x': 1.0, 'y': 1.1, 'z': 0.9, 'magnitude': 1.8},
            'vibration_max': {'x': 2.0, 'y': 2.1, 'z': 1.9, 'magnitude': 3.0},
            'temperature_mean': [45.0, 46.0, 44.5],
            'temperature_max': [48.0, 49.0, 47.5],
            'sample_count': 10
        }
    
    def test_initialization(self):
        """Test recommender initialization"""
        self.assertIsInstance(self.recommender, OptimizationRecommender)
    
    def test_normal_operation_recommendations(self):
        """Test recommendations for normal operation"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.2,
            wear_level=0.3
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should include normal operation message
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue(
            'normal' in rec_text or 'optimal' in rec_text or 'no immediate action' in rec_text
        )
    
    def test_high_current_recommendation(self):
        """Test recommendation for high current"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [7.0, 7.2, 6.8]  # High current
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.5,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('load' in rec_text or 'speed' in rec_text or 'current' in rec_text)
    
    def test_current_imbalance_recommendation(self):
        """Test recommendation for current imbalance"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [5.0, 8.0, 5.1]  # Significant imbalance
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.4,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('imbalance' in rec_text or 'binding' in rec_text or 'motor' in rec_text)
    
    def test_optimal_current_recommendation(self):
        """Test recommendation for optimal current range"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [4.0, 4.1, 3.9]  # In optimal range
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.1,
            wear_level=0.2
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('optimal' in rec_text or 'maintain' in rec_text)
    
    def test_current_spikes_recommendation(self):
        """Test recommendation for current spikes"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [5.0, 5.1, 4.9]
        sensor_data['current_max'] = [10.0, 10.5, 9.8]  # Large spikes
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.3,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('spike' in rec_text or 'acceleration' in rec_text)
    
    def test_high_vibration_recommendation(self):
        """Test recommendation for high vibration"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['vibration_mean']['magnitude'] = 6.0  # High vibration
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.6,
            wear_level=0.5
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue(
            'vibration' in rec_text and ('bearing' in rec_text or 'alignment' in rec_text or 'maintenance' in rec_text)
        )
    
    def test_elevated_vibration_recommendation(self):
        """Test recommendation for elevated vibration"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['vibration_mean']['magnitude'] = 3.5  # Elevated
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.4,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('vibration' in rec_text or 'balanc' in rec_text)
    
    def test_vibration_axis_imbalance_recommendation(self):
        """Test recommendation for vibration axis imbalance"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['vibration_mean'] = {'x': 1.0, 'y': 5.0, 'z': 1.0, 'magnitude': 5.2}
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.5,
            wear_level=0.4
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('axis' in rec_text or 'alignment' in rec_text)
    
    def test_high_temperature_recommendation(self):
        """Test recommendation for high temperature"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['temperature_max'] = [65.0, 66.0, 64.0]  # High temp
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.6,
            wear_level=0.4
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue(
            'temperature' in rec_text and ('cooling' in rec_text or 'duty cycle' in rec_text or 'ventilation' in rec_text)
        )
    
    def test_elevated_temperature_recommendation(self):
        """Test recommendation for elevated temperature"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['temperature_max'] = [55.0, 56.0, 54.0]  # Elevated
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.3,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('temperature' in rec_text or 'ventilation' in rec_text)
    
    def test_temperature_cycling_recommendation(self):
        """Test recommendation for temperature cycling"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['temperature_mean'] = [45.0, 46.0, 44.5]
        sensor_data['temperature_max'] = [70.0, 71.0, 69.0]  # Large range
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.4,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('temperature' in rec_text and 'thermal' in rec_text)
    
    def test_urgent_wear_recommendation(self):
        """Test recommendation for urgent wear level"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.5,
            wear_level=0.85  # Urgent level
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('urgent' in rec_text or 'immediately' in rec_text)
    
    def test_moderate_wear_recommendation(self):
        """Test recommendation for moderate wear level"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.3,
            wear_level=0.65  # Moderate level
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('moderate' in rec_text or 'plan maintenance' in rec_text)
    
    def test_medium_wear_recommendation(self):
        """Test recommendation for medium wear level"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.2,
            wear_level=0.45  # Medium level
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('wear' in rec_text and 'monitoring' in rec_text)
    
    def test_high_anomaly_recommendation(self):
        """Test recommendation for high anomaly score"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.8,  # High anomaly
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('anomaly' in rec_text and 'investigate' in rec_text)
    
    def test_moderate_anomaly_recommendation(self):
        """Test recommendation for moderate anomaly score"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.55,  # Moderate anomaly
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('anomaly' in rec_text or 'review' in rec_text)
    
    def test_energy_efficiency_recommendation(self):
        """Test recommendation for energy efficiency"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [6.0, 6.1, 5.9]  # Higher current
        sensor_data['temperature_mean'] = [50.0, 51.0, 49.0]  # Higher temp
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.3,
            wear_level=0.3
        )
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('energy' in rec_text or 'efficiency' in rec_text)
    
    def test_insufficient_data_recommendation(self):
        """Test recommendation when no data available"""
        sensor_data = {'sample_count': 0}
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.0,
            wear_level=0.0
        )
        
        self.assertGreater(len(recommendations), 0)
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('insufficient' in rec_text or 'no' in rec_text)
    
    def test_empty_sensor_data(self):
        """Test with empty sensor data"""
        recommendations = self.recommender.generate_recommendations(
            {},
            anomaly_score=0.0,
            wear_level=0.0
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_multiple_recommendations(self):
        """Test that multiple issues generate multiple recommendations"""
        sensor_data = self.base_sensor_data.copy()
        sensor_data['current_mean'] = [7.0, 7.2, 6.8]  # High current
        sensor_data['vibration_mean']['magnitude'] = 6.0  # High vibration
        sensor_data['temperature_max'] = [65.0, 66.0, 64.0]  # High temp
        
        recommendations = self.recommender.generate_recommendations(
            sensor_data,
            anomaly_score=0.7,
            wear_level=0.7
        )
        
        # Should have multiple recommendations for multiple issues
        self.assertGreater(len(recommendations), 2)
    
    def test_recommendations_are_strings(self):
        """Test that all recommendations are strings"""
        recommendations = self.recommender.generate_recommendations(
            self.base_sensor_data,
            anomaly_score=0.5,
            wear_level=0.5
        )
        
        for rec in recommendations:
            self.assertIsInstance(rec, str)
            self.assertGreater(len(rec), 0)


if __name__ == '__main__':
    unittest.main()
