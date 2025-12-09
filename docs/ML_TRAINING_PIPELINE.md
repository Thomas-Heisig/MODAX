# ML Model Training Pipeline

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0

## Overview

The MODAX ML Training Pipeline provides an end-to-end framework for training, evaluating, and deploying machine learning models for predictive maintenance. It supports continuous learning from production data and automated model updates.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML Training Pipeline                          │
│                                                                  │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐             │
│  │   Data     │──►│  Feature   │──►│  Model     │             │
│  │ Collection │   │Engineering │   │  Training  │             │
│  └────────────┘   └────────────┘   └────────────┘             │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐             │
│  │   Data     │   │  Feature   │   │   Model    │             │
│  │ Validation │   │   Store    │   │ Evaluation │             │
│  └────────────┘   └────────────┘   └────────────┘             │
│                                            │                    │
│                                            ▼                    │
│                                     ┌────────────┐              │
│                                     │   Model    │              │
│                                     │ Deployment │              │
│                                     └────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                                  ┌─────────────────┐
                                  │  ONNX Runtime   │
                                  │  (Production)   │
                                  └─────────────────┘
```

## Components

### 1. Data Collection

#### Historical Data Extraction
```python
# python-ai-layer/training/data_collector.py
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

class DataCollector:
    """Collect and prepare training data from TimescaleDB"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def collect_training_data(
        self,
        tenant_id: str,
        device_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        include_failures: bool = True
    ) -> pd.DataFrame:
        """
        Collect sensor data for training
        
        Args:
            tenant_id: Tenant identifier
            device_ids: List of device IDs to collect data from
            start_date: Start of data collection period
            end_date: End of data collection period
            include_failures: Whether to include failure events
            
        Returns:
            DataFrame with sensor data and labels
        """
        query = """
            SELECT 
                sd.device_id,
                sd.timestamp,
                sd.current_mean,
                sd.vibration_x_mean,
                sd.vibration_y_mean,
                sd.vibration_z_mean,
                sd.temperature_mean,
                fe.event_type,
                fe.rul_hours  -- Remaining Useful Life at this point
            FROM sensor_data sd
            LEFT JOIN failure_events fe ON 
                sd.device_id = fe.device_id AND
                sd.timestamp >= fe.event_time - INTERVAL '1 hour'
            WHERE sd.tenant_id = $1
                AND sd.device_id = ANY($2)
                AND sd.timestamp BETWEEN $3 AND $4
            ORDER BY sd.device_id, sd.timestamp
        """
        
        data = await self.db.fetch(
            query,
            tenant_id,
            device_ids,
            start_date,
            end_date
        )
        
        df = pd.DataFrame(data)
        return df
    
    async def get_failure_events(
        self,
        tenant_id: str,
        device_ids: List[str]
    ) -> pd.DataFrame:
        """Get failure events for labeling"""
        query = """
            SELECT 
                device_id,
                event_time,
                event_type,
                component_failed,
                operating_hours_at_failure
            FROM failure_events
            WHERE tenant_id = $1
                AND device_id = ANY($2)
            ORDER BY event_time DESC
        """
        
        data = await self.db.fetch(query, tenant_id, device_ids)
        return pd.DataFrame(data)
```

#### Data Labeling
```python
# python-ai-layer/training/data_labeler.py
class DataLabeler:
    """Generate labels for supervised learning"""
    
    def calculate_rul(
        self,
        sensor_data: pd.DataFrame,
        failure_events: pd.DataFrame,
        prediction_horizon_hours: int = 100
    ) -> pd.DataFrame:
        """
        Calculate Remaining Useful Life (RUL) for each data point
        
        RUL is calculated as the time until the next failure event.
        Data beyond prediction_horizon before failure is labeled as "normal".
        """
        labeled_data = sensor_data.copy()
        labeled_data['rul_hours'] = prediction_horizon_hours
        labeled_data['health_status'] = 'normal'
        
        for _, failure in failure_events.iterrows():
            device_id = failure['device_id']
            failure_time = failure['event_time']
            
            # Find data points before this failure
            mask = (
                (labeled_data['device_id'] == device_id) &
                (labeled_data['timestamp'] < failure_time)
            )
            
            # Calculate RUL for each point
            time_to_failure = (
                failure_time - labeled_data.loc[mask, 'timestamp']
            ).dt.total_seconds() / 3600  # Convert to hours
            
            # Update RUL
            labeled_data.loc[mask, 'rul_hours'] = time_to_failure
            
            # Classify health status
            labeled_data.loc[
                mask & (time_to_failure < 10), 'health_status'
            ] = 'critical'
            labeled_data.loc[
                mask & (time_to_failure >= 10) & (time_to_failure < 50),
                'health_status'
            ] = 'warning'
        
        return labeled_data
```

### 2. Feature Engineering

```python
# python-ai-layer/training/feature_engineer.py
import numpy as np
from scipy import stats
from scipy.signal import welch

class FeatureEngineer:
    """Extract features from raw sensor data"""
    
    def create_time_series_features(
        self,
        df: pd.DataFrame,
        window_size: int = 50,
        stride: int = 1
    ) -> np.ndarray:
        """
        Create time-series windows for sequence models
        
        Args:
            df: DataFrame with sensor data
            window_size: Number of time steps in each sequence
            stride: Step size for sliding window
            
        Returns:
            3D array (samples, time_steps, features)
        """
        features = [
            'current_mean', 'vibration_x_mean', 'vibration_y_mean',
            'vibration_z_mean', 'temperature_mean'
        ]
        
        sequences = []
        labels = []
        
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id].sort_values('timestamp')
            
            for i in range(0, len(device_data) - window_size, stride):
                window = device_data.iloc[i:i + window_size]
                
                # Extract sequence
                sequence = window[features].values
                sequences.append(sequence)
                
                # Label is RUL at end of window
                labels.append(window.iloc[-1]['rul_hours'])
        
        return np.array(sequences), np.array(labels)
    
    def extract_statistical_features(
        self,
        df: pd.DataFrame,
        window_hours: int = 1
    ) -> pd.DataFrame:
        """
        Extract statistical features for traditional ML models
        
        Features include:
        - Mean, std, min, max, median
        - Skewness, kurtosis
        - Rate of change
        - FFT features (frequency domain)
        """
        features_df = pd.DataFrame()
        
        # Group by device and time windows
        grouped = df.groupby([
            'device_id',
            pd.Grouper(key='timestamp', freq=f'{window_hours}H')
        ])
        
        for sensor in ['current', 'vibration_x', 'vibration_y', 'vibration_z', 'temperature']:
            col = f'{sensor}_mean'
            
            # Time domain features
            features_df[f'{sensor}_mean'] = grouped[col].mean()
            features_df[f'{sensor}_std'] = grouped[col].std()
            features_df[f'{sensor}_min'] = grouped[col].min()
            features_df[f'{sensor}_max'] = grouped[col].max()
            features_df[f'{sensor}_range'] = (
                features_df[f'{sensor}_max'] - features_df[f'{sensor}_min']
            )
            features_df[f'{sensor}_skew'] = grouped[col].apply(stats.skew)
            features_df[f'{sensor}_kurtosis'] = grouped[col].apply(stats.kurtosis)
            
            # Rate of change
            features_df[f'{sensor}_roc'] = grouped[col].apply(
                lambda x: (x.iloc[-1] - x.iloc[0]) / len(x) if len(x) > 1 else 0
            )
        
        # Frequency domain features (vibration)
        features_df = self._add_fft_features(df, features_df)
        
        return features_df
    
    def _add_fft_features(
        self,
        df: pd.DataFrame,
        features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add frequency domain features using FFT"""
        for axis in ['x', 'y', 'z']:
            col = f'vibration_{axis}_mean'
            
            # Calculate power spectral density
            freqs, psd = welch(df[col].values, fs=10.0)  # 10 Hz sampling
            
            # Extract dominant frequencies
            features_df[f'vibration_{axis}_dominant_freq'] = freqs[np.argmax(psd)]
            features_df[f'vibration_{axis}_spectral_energy'] = np.sum(psd)
            
        return features_df
```

### 3. Model Training

#### LSTM Model
```python
# python-ai-layer/training/models/lstm_model.py
import torch
import torch.nn as nn

class LSTMRULPredictor(nn.Module):
    """LSTM-based RUL prediction model"""
    
    def __init__(
        self,
        input_size: int = 5,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 1)
    
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Use last hidden state
        last_hidden = h_n[-1]
        
        # Fully connected layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out
```

#### Training Script
```python
# python-ai-layer/training/train_model.py
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
import mlflow

class ModelTrainer:
    """Train and evaluate ML models"""
    
    def __init__(self, model, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.model = model.to(device)
        self.device = device
        self.optimizer = None
        self.criterion = nn.MSELoss()
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ):
        """Train the model"""
        # Setup optimizer
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate
        )
        
        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        
        # Training loop
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward pass
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs.squeeze(), batch_y)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            # Validation
            val_loss = self._validate(X_val, y_val)
            
            # Log metrics
            mlflow.log_metrics({
                'train_loss': total_loss / len(train_loader),
                'val_loss': val_loss
            }, step=epoch)
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch {epoch+1}/{epochs}, '
                      f'Train Loss: {total_loss/len(train_loader):.4f}, '
                      f'Val Loss: {val_loss:.4f}')
    
    def _validate(self, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """Validate the model"""
        self.model.eval()
        
        with torch.no_grad():
            X_val_tensor = torch.FloatTensor(X_val).to(self.device)
            y_val_tensor = torch.FloatTensor(y_val).to(self.device)
            
            outputs = self.model(X_val_tensor)
            loss = self.criterion(outputs.squeeze(), y_val_tensor)
        
        return loss.item()
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model performance"""
        self.model.eval()
        
        with torch.no_grad():
            X_test_tensor = torch.FloatTensor(X_test).to(self.device)
            y_test_tensor = torch.FloatTensor(y_test).to(self.device)
            
            predictions = self.model(X_test_tensor).squeeze().cpu().numpy()
        
        # Calculate metrics
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'predictions': predictions
        }
```

### 4. Model Evaluation

```python
# python-ai-layer/training/model_evaluator.py
class ModelEvaluator:
    """Comprehensive model evaluation"""
    
    def evaluate_rul_model(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        thresholds: Dict[str, float] = None
    ) -> Dict:
        """
        Evaluate RUL prediction model
        
        Metrics:
        - MAE, RMSE, R²
        - Early prediction rate (predicted failure before actual)
        - Late prediction rate (predicted failure after actual)
        - Critical window accuracy (predictions within 10 hours of failure)
        """
        if thresholds is None:
            thresholds = {
                'critical': 10,
                'warning': 50,
                'normal': 200
            }
        
        # Basic metrics
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        r2 = 1 - (np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2))
        
        # Prediction bias
        early_predictions = np.sum(y_pred > y_true) / len(y_true)
        late_predictions = np.sum(y_pred < y_true) / len(y_true)
        
        # Critical window accuracy
        critical_mask = y_true < thresholds['critical']
        if np.any(critical_mask):
            critical_accuracy = np.mean(
                np.abs(y_true[critical_mask] - y_pred[critical_mask]) < 5  # 5 hour tolerance
            )
        else:
            critical_accuracy = None
        
        # Classification metrics (health status)
        y_true_class = self._classify_rul(y_true, thresholds)
        y_pred_class = self._classify_rul(y_pred, thresholds)
        
        from sklearn.metrics import classification_report
        class_report = classification_report(
            y_true_class,
            y_pred_class,
            target_names=['critical', 'warning', 'normal'],
            output_dict=True
        )
        
        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'early_prediction_rate': early_predictions,
            'late_prediction_rate': late_predictions,
            'critical_accuracy': critical_accuracy,
            'classification_report': class_report
        }
    
    def _classify_rul(self, rul_values, thresholds):
        """Classify RUL into health status categories"""
        classes = np.full(len(rul_values), 'normal')
        classes[rul_values < thresholds['warning']] = 'warning'
        classes[rul_values < thresholds['critical']] = 'critical'
        return classes
```

### 5. Model Deployment

#### ONNX Conversion
```python
# python-ai-layer/training/onnx_converter.py
import torch.onnx

class ONNXConverter:
    """Convert PyTorch models to ONNX format"""
    
    def convert_to_onnx(
        self,
        model: torch.nn.Module,
        input_shape: tuple,
        output_path: str,
        opset_version: int = 11
    ):
        """
        Convert PyTorch model to ONNX
        
        Args:
            model: Trained PyTorch model
            input_shape: Shape of input tensor (batch, seq_len, features)
            output_path: Path to save ONNX model
            opset_version: ONNX opset version
        """
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randn(*input_shape)
        
        # Export to ONNX
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        print(f"Model exported to {output_path}")
    
    def validate_onnx_model(
        self,
        onnx_path: str,
        pytorch_model: torch.nn.Module,
        test_input: np.ndarray
    ) -> bool:
        """Validate ONNX model against PyTorch model"""
        import onnxruntime as ort
        
        # PyTorch inference
        pytorch_model.eval()
        with torch.no_grad():
            pytorch_output = pytorch_model(
                torch.FloatTensor(test_input)
            ).numpy()
        
        # ONNX inference
        ort_session = ort.InferenceSession(onnx_path)
        onnx_output = ort_session.run(
            None,
            {'input': test_input.astype(np.float32)}
        )[0]
        
        # Compare outputs
        np.testing.assert_allclose(
            pytorch_output,
            onnx_output,
            rtol=1e-03,
            atol=1e-05
        )
        
        print("ONNX model validation successful")
        return True
```

## MLflow Integration

### Experiment Tracking
```python
# python-ai-layer/training/mlflow_tracking.py
import mlflow
import mlflow.pytorch

class MLflowTracker:
    """Track experiments with MLflow"""
    
    def __init__(self, experiment_name: str):
        mlflow.set_experiment(experiment_name)
        self.experiment_name = experiment_name
    
    def start_run(self, run_name: str):
        """Start a new MLflow run"""
        return mlflow.start_run(run_name=run_name)
    
    def log_parameters(self, params: Dict):
        """Log training parameters"""
        mlflow.log_params(params)
    
    def log_metrics(self, metrics: Dict, step: int = None):
        """Log training metrics"""
        mlflow.log_metrics(metrics, step=step)
    
    def log_model(
        self,
        model,
        artifact_path: str,
        registered_model_name: str = None
    ):
        """Log model to MLflow"""
        mlflow.pytorch.log_model(
            model,
            artifact_path,
            registered_model_name=registered_model_name
        )
    
    def log_artifacts(self, local_dir: str):
        """Log artifacts (plots, reports, etc.)"""
        mlflow.log_artifacts(local_dir)
```

## Automated Training Pipeline

```python
# python-ai-layer/training/pipeline.py
class TrainingPipeline:
    """End-to-end ML training pipeline"""
    
    async def run_pipeline(
        self,
        config: Dict
    ):
        """
        Execute complete training pipeline
        
        Steps:
        1. Data collection
        2. Data validation
        3. Feature engineering
        4. Model training
        5. Model evaluation
        6. ONNX conversion
        7. Model deployment
        """
        with mlflow.start_run():
            # Log configuration
            mlflow.log_params(config)
            
            # 1. Data Collection
            print("Collecting training data...")
            data_collector = DataCollector(self.db)
            raw_data = await data_collector.collect_training_data(
                tenant_id=config['tenant_id'],
                device_ids=config['device_ids'],
                start_date=config['start_date'],
                end_date=config['end_date']
            )
            
            # 2. Data Validation
            print("Validating data quality...")
            data_validator = DataValidator()
            validation_report = data_validator.validate(raw_data)
            mlflow.log_dict(validation_report, "data_validation.json")
            
            # 3. Feature Engineering
            print("Engineering features...")
            feature_engineer = FeatureEngineer()
            X, y = feature_engineer.create_time_series_features(
                raw_data,
                window_size=config['sequence_length']
            )
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )
            
            # 4. Model Training
            print("Training model...")
            model = LSTMRULPredictor(
                input_size=config['input_size'],
                hidden_size=config['hidden_size'],
                num_layers=config['num_layers']
            )
            
            trainer = ModelTrainer(model)
            trainer.train(
                X_train, y_train,
                X_val, y_val,
                epochs=config['epochs'],
                batch_size=config['batch_size'],
                learning_rate=config['learning_rate']
            )
            
            # 5. Model Evaluation
            print("Evaluating model...")
            evaluator = ModelEvaluator()
            metrics = trainer.evaluate(X_test, y_test)
            rul_metrics = evaluator.evaluate_rul_model(
                y_test,
                metrics['predictions']
            )
            mlflow.log_metrics(rul_metrics)
            
            # 6. ONNX Conversion
            print("Converting to ONNX...")
            converter = ONNXConverter()
            onnx_path = f"models/rul_model_{mlflow.active_run().info.run_id}.onnx"
            converter.convert_to_onnx(
                model,
                input_shape=(1, config['sequence_length'], config['input_size']),
                output_path=onnx_path
            )
            
            # Validate ONNX
            converter.validate_onnx_model(
                onnx_path,
                model,
                X_test[:1]
            )
            
            # 7. Model Deployment (if meets criteria)
            if rul_metrics['mae'] < config['deployment_threshold']:
                print("Model meets deployment criteria. Deploying...")
                await self._deploy_model(onnx_path, config)
            else:
                print(f"Model MAE ({rul_metrics['mae']}) exceeds threshold "
                      f"({config['deployment_threshold']}). Not deploying.")
    
    async def _deploy_model(self, model_path: str, config: Dict):
        """Deploy model to production"""
        # Copy to production model directory
        import shutil
        production_path = "models/rul_predictor.onnx"
        shutil.copy(model_path, production_path)
        
        # Update model metadata
        metadata = {
            'model_version': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'model_type': config['model_type'],
            'training_date': datetime.now().isoformat(),
            'performance_metrics': config.get('metrics', {})
        }
        
        with open("models/model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model deployed to {production_path}")
```

## Continuous Training

### Automated Retraining
```python
# python-ai-layer/training/continuous_training.py
class ContinuousTraining:
    """Automated model retraining based on performance degradation"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.performance_threshold = 0.8  # Retrain if performance drops below this
    
    async def monitor_model_performance(self):
        """Monitor production model performance"""
        while True:
            # Get recent predictions and actual outcomes
            predictions = await self._get_recent_predictions()
            actuals = await self._get_actual_outcomes()
            
            # Calculate performance
            current_performance = self._calculate_performance(
                predictions,
                actuals
            )
            
            # Log performance
            mlflow.log_metric("production_performance", current_performance)
            
            # Trigger retraining if needed
            if current_performance < self.performance_threshold:
                print("Performance degradation detected. Triggering retraining...")
                await self._trigger_retraining()
            
            # Wait before next check
            await asyncio.sleep(3600 * 24)  # Check daily
    
    async def _trigger_retraining(self):
        """Trigger automated model retraining"""
        pipeline = TrainingPipeline()
        config = self._load_training_config()
        await pipeline.run_pipeline(config)
```

## Related Documentation

- [ONNX Model Deployment](ONNX_MODEL_DEPLOYMENT.md)
- [AI Layer](../python-ai-layer/README.md)
- [Data Persistence](DATA_PERSISTENCE.md)
- [Monitoring](MONITORING.md)
