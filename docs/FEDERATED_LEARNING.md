# Federated Learning Framework

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0

## Overview

Federated Learning enables MODAX installations to collaboratively train machine learning models without sharing raw sensor data. This approach preserves data privacy, reduces bandwidth requirements, and allows organizations to benefit from collective learning while maintaining data sovereignty.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Central Aggregation Server                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Global Model Coordinator                             │  │
│  │  - Model versioning                                   │  │
│  │  - Aggregation algorithms (FedAvg, FedProx)          │  │
│  │  - Client selection                                   │  │
│  │  - Performance monitoring                             │  │
│  └───────────────────────┬───────────────────────────────┘  │
└────────────────────────────┼──────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Location A  │    │  Location B  │    │  Location C  │
│  (Client 1)  │    │  (Client 2)  │    │  (Client 3)  │
│              │    │              │    │              │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │  Local   │ │    │ │  Local   │ │    │ │  Local   │ │
│ │  Model   │ │    │ │  Model   │ │    │ │  Model   │ │
│ │ Training │ │    │ │ Training │ │    │ │ Training │ │
│ └────┬─────┘ │    │ └────┬─────┘ │    │ └────┬─────┘ │
│      │       │    │      │       │    │      │       │
│ ┌────▼─────┐ │    │ ┌────▼─────┐ │    │ ┌────▼─────┐ │
│ │  Local   │ │    │ │  Local   │ │    │ │  Local   │ │
│ │   Data   │ │    │ │   Data   │ │    │ │   Data   │ │
│ │ (Private)│ │    │ │ (Private)│ │    │ │ (Private)│ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
└──────────────┘    └──────────────┘    └──────────────┘

Training Flow:
1. Server sends global model to clients
2. Each client trains locally on private data
3. Clients send model updates (gradients) to server
4. Server aggregates updates
5. Repeat until convergence
```

## Core Components

### 1. Federated Server

```python
# python-ai-layer/federated/server.py
from typing import List, Dict
import torch
import torch.nn as nn
import numpy as np
from dataclasses import dataclass
import asyncio

@dataclass
class ClientUpdate:
    """Model update from a client"""
    client_id: str
    model_weights: Dict[str, torch.Tensor]
    num_samples: int
    loss: float
    accuracy: float

class FederatedServer:
    """Central server for federated learning"""
    
    def __init__(
        self,
        model: nn.Module,
        aggregation_strategy: str = 'fedavg'
    ):
        self.global_model = model
        self.aggregation_strategy = aggregation_strategy
        self.round_number = 0
        self.client_history = {}
        
        # Training configuration
        self.min_clients_per_round = 3
        self.client_fraction = 0.5  # Sample 50% of clients per round
        self.max_rounds = 100
        
        # Performance tracking
        self.global_metrics = {
            'round': [],
            'loss': [],
            'accuracy': [],
            'num_clients': []
        }
    
    async def train_round(self, available_clients: List[str]) -> Dict:
        """
        Execute one round of federated training
        
        Args:
            available_clients: List of client IDs available for training
            
        Returns:
            Round statistics
        """
        # Select clients for this round
        selected_clients = self._select_clients(available_clients)
        
        if len(selected_clients) < self.min_clients_per_round:
            raise ValueError(f"Insufficient clients: {len(selected_clients)} < {self.min_clients_per_round}")
        
        # Send global model to selected clients
        global_weights = self.global_model.state_dict()
        
        # Collect updates from clients (parallel)
        client_updates = await self._collect_client_updates(
            selected_clients,
            global_weights
        )
        
        # Aggregate updates
        aggregated_weights = self._aggregate_updates(client_updates)
        
        # Update global model
        self.global_model.load_state_dict(aggregated_weights)
        
        # Calculate round statistics
        round_stats = self._calculate_round_stats(client_updates)
        
        # Update metrics
        self.round_number += 1
        self.global_metrics['round'].append(self.round_number)
        self.global_metrics['loss'].append(round_stats['avg_loss'])
        self.global_metrics['accuracy'].append(round_stats['avg_accuracy'])
        self.global_metrics['num_clients'].append(len(client_updates))
        
        return round_stats
    
    def _select_clients(self, available_clients: List[str]) -> List[str]:
        """Select subset of clients for training round"""
        num_clients = max(
            self.min_clients_per_round,
            int(len(available_clients) * self.client_fraction)
        )
        
        # Random selection (can be replaced with smarter selection)
        selected = np.random.choice(
            available_clients,
            size=min(num_clients, len(available_clients)),
            replace=False
        )
        
        return list(selected)
    
    async def _collect_client_updates(
        self,
        selected_clients: List[str],
        global_weights: Dict
    ) -> List[ClientUpdate]:
        """Collect model updates from selected clients"""
        tasks = []
        for client_id in selected_clients:
            task = asyncio.create_task(
                self._request_client_update(client_id, global_weights)
            )
            tasks.append(task)
        
        updates = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed updates
        valid_updates = [u for u in updates if isinstance(u, ClientUpdate)]
        
        return valid_updates
    
    async def _request_client_update(
        self,
        client_id: str,
        global_weights: Dict
    ) -> ClientUpdate:
        """Request model update from a client"""
        # Send request to client API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{client_id}/federated/train",
                json={
                    'round': self.round_number,
                    'model_weights': self._serialize_weights(global_weights)
                }
            ) as response:
                data = await response.json()
                
                return ClientUpdate(
                    client_id=client_id,
                    model_weights=self._deserialize_weights(data['model_weights']),
                    num_samples=data['num_samples'],
                    loss=data['loss'],
                    accuracy=data['accuracy']
                )
    
    def _aggregate_updates(self, client_updates: List[ClientUpdate]) -> Dict:
        """
        Aggregate client updates to create new global model
        
        Supports multiple aggregation strategies:
        - FedAvg: Weighted average by number of samples
        - FedProx: FedAvg with proximal term
        - FedOpt: Adaptive optimizers (FedAdam, FedYogi)
        """
        if self.aggregation_strategy == 'fedavg':
            return self._fedavg(client_updates)
        elif self.aggregation_strategy == 'fedprox':
            return self._fedprox(client_updates)
        else:
            raise ValueError(f"Unknown aggregation strategy: {self.aggregation_strategy}")
    
    def _fedavg(self, client_updates: List[ClientUpdate]) -> Dict:
        """
        Federated Averaging (FedAvg)
        
        Computes weighted average of client models based on number of samples
        """
        # Calculate total samples
        total_samples = sum(update.num_samples for update in client_updates)
        
        # Initialize aggregated weights
        aggregated_weights = {}
        
        # Get first client's weights as template
        first_weights = client_updates[0].model_weights
        
        for key in first_weights.keys():
            # Weighted sum of parameters
            weighted_sum = torch.zeros_like(first_weights[key])
            
            for update in client_updates:
                weight = update.num_samples / total_samples
                weighted_sum += weight * update.model_weights[key]
            
            aggregated_weights[key] = weighted_sum
        
        return aggregated_weights
    
    def _calculate_round_stats(self, client_updates: List[ClientUpdate]) -> Dict:
        """Calculate statistics for the round"""
        total_samples = sum(u.num_samples for u in client_updates)
        
        # Weighted averages
        avg_loss = sum(
            u.loss * u.num_samples for u in client_updates
        ) / total_samples
        
        avg_accuracy = sum(
            u.accuracy * u.num_samples for u in client_updates
        ) / total_samples
        
        return {
            'round': self.round_number,
            'num_clients': len(client_updates),
            'avg_loss': avg_loss,
            'avg_accuracy': avg_accuracy,
            'total_samples': total_samples
        }
```

### 2. Federated Client

```python
# python-ai-layer/federated/client.py
class FederatedClient:
    """Client for federated learning"""
    
    def __init__(
        self,
        client_id: str,
        model: nn.Module,
        local_data_loader: torch.utils.data.DataLoader
    ):
        self.client_id = client_id
        self.model = model
        self.data_loader = local_data_loader
        
        # Training configuration
        self.local_epochs = 5
        self.learning_rate = 0.01
        self.optimizer = torch.optim.SGD(
            self.model.parameters(),
            lr=self.learning_rate,
            momentum=0.9
        )
        self.criterion = nn.MSELoss()
    
    def train_local_model(
        self,
        global_weights: Dict,
        num_epochs: int = None
    ) -> ClientUpdate:
        """
        Train model locally on private data
        
        Args:
            global_weights: Weights from global model
            num_epochs: Number of local training epochs
            
        Returns:
            ClientUpdate with trained model weights
        """
        if num_epochs is None:
            num_epochs = self.local_epochs
        
        # Load global model weights
        self.model.load_state_dict(global_weights)
        self.model.train()
        
        # Training metrics
        total_loss = 0.0
        total_samples = 0
        correct_predictions = 0
        
        # Train for specified epochs
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            
            for batch_x, batch_y in self.data_loader:
                # Forward pass
                self.optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                # Track metrics
                epoch_loss += loss.item() * batch_x.size(0)
                total_samples += batch_x.size(0)
                
                # Calculate accuracy (for classification)
                if hasattr(outputs, 'shape') and len(outputs.shape) > 1:
                    predictions = torch.argmax(outputs, dim=1)
                    correct_predictions += (predictions == batch_y).sum().item()
            
            total_loss += epoch_loss
        
        # Calculate average metrics
        avg_loss = total_loss / (total_samples * num_epochs)
        accuracy = correct_predictions / (total_samples * num_epochs)
        
        # Create update with trained weights
        update = ClientUpdate(
            client_id=self.client_id,
            model_weights=self.model.state_dict(),
            num_samples=total_samples,
            loss=avg_loss,
            accuracy=accuracy
        )
        
        return update
    
    def evaluate_local_model(self, test_loader) -> Dict:
        """Evaluate model on local test data"""
        self.model.eval()
        
        total_loss = 0.0
        total_samples = 0
        correct = 0
        
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
                
                total_loss += loss.item() * batch_x.size(0)
                total_samples += batch_x.size(0)
                
                if hasattr(outputs, 'shape') and len(outputs.shape) > 1:
                    predictions = torch.argmax(outputs, dim=1)
                    correct += (predictions == batch_y).sum().item()
        
        return {
            'loss': total_loss / total_samples,
            'accuracy': correct / total_samples
        }
```

### 3. Privacy-Preserving Techniques

```python
# python-ai-layer/federated/privacy.py
class DifferentialPrivacy:
    """Add differential privacy to federated learning"""
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize differential privacy
        
        Args:
            epsilon: Privacy budget
            delta: Probability of privacy violation
        """
        self.epsilon = epsilon
        self.delta = delta
        self.noise_multiplier = self._calculate_noise_multiplier()
    
    def _calculate_noise_multiplier(self) -> float:
        """Calculate noise multiplier based on epsilon and delta"""
        # Simplified calculation (should use proper DP analysis)
        return np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
    
    def add_noise_to_gradients(
        self,
        gradients: Dict[str, torch.Tensor],
        sensitivity: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        Add Gaussian noise to gradients for differential privacy
        
        Args:
            gradients: Model gradients
            sensitivity: L2 sensitivity of the query
            
        Returns:
            Noisy gradients
        """
        noisy_gradients = {}
        
        for key, grad in gradients.items():
            # Calculate noise scale
            noise_scale = sensitivity * self.noise_multiplier
            
            # Add Gaussian noise
            noise = torch.randn_like(grad) * noise_scale
            noisy_gradients[key] = grad + noise
        
        return noisy_gradients
    
    def clip_gradients(
        self,
        gradients: Dict[str, torch.Tensor],
        max_norm: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        Clip gradients to bound sensitivity
        
        Args:
            gradients: Model gradients
            max_norm: Maximum L2 norm
            
        Returns:
            Clipped gradients
        """
        # Calculate total gradient norm
        total_norm = 0.0
        for grad in gradients.values():
            total_norm += grad.norm().item() ** 2
        total_norm = np.sqrt(total_norm)
        
        # Clip if necessary
        if total_norm > max_norm:
            clip_coef = max_norm / total_norm
            clipped_gradients = {
                key: grad * clip_coef
                for key, grad in gradients.items()
            }
            return clipped_gradients
        
        return gradients

class SecureAggregation:
    """Secure aggregation using cryptographic techniques"""
    
    def __init__(self, num_clients: int):
        self.num_clients = num_clients
        self.threshold = num_clients // 2 + 1  # Majority required
    
    def encrypt_update(
        self,
        model_update: torch.Tensor,
        public_keys: List
    ) -> bytes:
        """
        Encrypt model update using homomorphic encryption
        
        Uses Paillier or CKKS homomorphic encryption
        """
        # Simplified placeholder - would use tenseal or similar
        # In production, use proper homomorphic encryption library
        pass
    
    def aggregate_encrypted(
        self,
        encrypted_updates: List[bytes]
    ) -> bytes:
        """
        Aggregate encrypted updates without decrypting
        
        Leverages additive homomorphic property
        """
        pass
    
    def decrypt_aggregated(
        self,
        encrypted_aggregate: bytes,
        private_key
    ) -> torch.Tensor:
        """Decrypt the aggregated result"""
        pass
```

## Implementation Examples

### RUL Prediction with Federated Learning

```python
# python-ai-layer/federated/examples/rul_federated.py
async def train_federated_rul_model():
    """Train RUL prediction model using federated learning"""
    
    # Initialize server
    global_model = LSTMRULPredictor(
        input_size=6,
        hidden_size=128,
        num_layers=2
    )
    
    server = FederatedServer(
        model=global_model,
        aggregation_strategy='fedavg'
    )
    
    # Register clients (different factories/locations)
    clients = [
        'factory_a.modax.com',
        'factory_b.modax.com',
        'factory_c.modax.com'
    ]
    
    # Training loop
    for round_num in range(100):
        print(f"\n=== Round {round_num + 1} ===")
        
        # Execute training round
        round_stats = await server.train_round(clients)
        
        print(f"Clients: {round_stats['num_clients']}")
        print(f"Avg Loss: {round_stats['avg_loss']:.4f}")
        print(f"Avg Accuracy: {round_stats['avg_accuracy']:.4f}")
        
        # Check convergence
        if round_stats['avg_loss'] < 0.01:
            print("\nModel converged!")
            break
    
    # Export final model
    torch.save(global_model.state_dict(), 'federated_rul_model.pth')
    
    # Convert to ONNX
    converter = ONNXConverter()
    converter.convert_to_onnx(
        global_model,
        input_shape=(1, 50, 6),
        output_path='federated_rul_model.onnx'
    )
    
    print("\nFederated model training complete!")
```

## API Endpoints

```python
# python-control-layer/federated_api.py
from fastapi import APIRouter, Depends, BackgroundTasks
from auth import UserContext, get_user_context, require_admin

router = APIRouter(prefix="/federated", tags=["federated"])

@router.post("/server/start")
async def start_federated_training(
    config: Dict,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(require_admin)
):
    """Start federated learning training"""
    background_tasks.add_task(run_federated_training, config)
    
    return {
        'status': 'started',
        'config': config
    }

@router.get("/server/status")
async def get_training_status(
    user: UserContext = Depends(get_user_context)
):
    """Get federated training status"""
    return federated_server.get_status()

@router.post("/client/train")
async def train_local_model(
    round_config: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Train local model (called by server)"""
    client = federated_client_manager.get_client(user.tenant_id)
    
    update = client.train_local_model(
        global_weights=round_config['model_weights'],
        num_epochs=round_config.get('local_epochs', 5)
    )
    
    return {
        'client_id': client.client_id,
        'model_weights': serialize_weights(update.model_weights),
        'num_samples': update.num_samples,
        'loss': update.loss,
        'accuracy': update.accuracy
    }

@router.post("/client/register")
async def register_as_client(
    client_config: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Register instance as federated learning client"""
    client_id = f"{user.tenant_id}.{client_config['location_id']}"
    
    # Create local client
    client = FederatedClient(
        client_id=client_id,
        model=create_model(client_config['model_type']),
        local_data_loader=create_data_loader(user.tenant_id)
    )
    
    federated_client_manager.register_client(client_id, client)
    
    return {
        'client_id': client_id,
        'registered': True
    }
```

## Benefits

### Privacy & Security
- **Data sovereignty**: Raw data never leaves premises
- **Compliance**: Meets GDPR, HIPAA requirements
- **Reduced attack surface**: No central data repository
- **Differential privacy**: Additional protection against inference attacks

### Performance
- **Reduced bandwidth**: Only model updates transferred
- **Faster training**: Parallel local training
- **Scalability**: Easily add new locations
- **Edge computing**: Training on edge devices

### Business Value
- **Collaborative learning**: Benefit from collective knowledge
- **Competitive advantage**: Learn from diverse environments
- **Cost reduction**: Shared training costs
- **Better models**: More diverse training data

## Best Practices

1. **Client Selection**: Ensure diverse client sampling per round
2. **Convergence Monitoring**: Track global and local metrics
3. **Model Versioning**: Maintain compatibility across versions
4. **Differential Privacy**: Balance privacy and model quality
5. **Secure Communication**: Use TLS for all communications
6. **Fault Tolerance**: Handle client failures gracefully
7. **Resource Management**: Consider client computational capacity
8. **Data Quality**: Validate local data quality

## Related Documentation

- [ML Training Pipeline](ML_TRAINING_PIPELINE.md)
- [ONNX Model Deployment](ONNX_MODEL_DEPLOYMENT.md)
- [Multi-Tenant Architecture](MULTI_TENANT_ARCHITECTURE.md)
- [Cloud Integration](CLOUD_INTEGRATION.md)
- [Security](SECURITY.md)
