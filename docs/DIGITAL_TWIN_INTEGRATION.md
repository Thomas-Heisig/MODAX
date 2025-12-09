# Digital Twin Integration

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0

## Overview

Digital Twin technology creates virtual replicas of physical MODAX devices and systems, enabling real-time simulation, predictive analysis, and "what-if" scenarios without affecting production equipment.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Physical Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  ESP32   │  │  CNC     │  │  Sensors │                   │
│  │ Devices  │  │ Machine  │  │ & Motors │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
└───────┼─────────────┼─────────────┼──────────────────────────┘
        │             │             │
        │  Real-time  │  Telemetry  │
        │    Data     │             │
        ▼             ▼             ▼
┌──────────────────────────────────────────────────────────────┐
│              Data Synchronization Layer                       │
│  ┌────────────────────────────────────────────────┐          │
│  │  State Synchronization Engine                  │          │
│  │  - Real-time data ingestion                    │          │
│  │  - State reconciliation                        │          │
│  │  - Event streaming                             │          │
│  └────────────────────┬───────────────────────────┘          │
└────────────────────────┼────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  Digital Twin Core                            │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Virtual    │  │   Physics    │  │  Behavioral  │       │
│  │   Device     │  │   Engine     │  │    Model     │       │
│  │   Model      │  │              │  │              │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │               │
│         └──────────────────┴──────────────────┘               │
│                            │                                  │
│                ┌───────────▼───────────┐                      │
│                │  Simulation Engine    │                      │
│                │  - Real-time sim      │                      │
│                │  - What-if analysis   │                      │
│                │  - Optimization       │                      │
│                └───────────┬───────────┘                      │
└────────────────────────────┼──────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│              Analytics & Visualization Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 3D Visual-   │  │  Predictive  │  │  Optimization│       │
│  │ ization      │  │  Analysis    │  │  Engine      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Virtual Device Model

```python
# python-control-layer/digital_twin/virtual_device.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

@dataclass
class VirtualDeviceState:
    """State of the virtual device"""
    timestamp: datetime
    device_id: str
    
    # Mechanical state
    position: np.ndarray  # [x, y, z] coordinates
    velocity: np.ndarray  # [vx, vy, vz] velocities
    acceleration: np.ndarray
    
    # Electrical state
    motor_current: float
    motor_voltage: float
    power_consumption: float
    
    # Thermal state
    temperature: float
    thermal_mass: float
    
    # Wear state
    spindle_wear: float  # 0.0 - 1.0
    bearing_wear: float
    tool_wear: float
    
    # Operational state
    is_running: bool
    current_program: Optional[str]
    cycle_count: int

class VirtualDevice:
    """Digital Twin of a physical device"""
    
    def __init__(self, device_id: str, device_config: Dict):
        self.device_id = device_id
        self.config = device_config
        self.state = self._initialize_state()
        self.physics_model = PhysicsModel(device_config)
        self.wear_model = WearModel()
        self.thermal_model = ThermalModel()
        
        # Simulation parameters
        self.dt = 0.1  # Time step (seconds)
        self.realtime_factor = 1.0  # 1.0 = real-time, >1 = faster than real-time
    
    def _initialize_state(self) -> VirtualDeviceState:
        """Initialize device state"""
        return VirtualDeviceState(
            timestamp=datetime.now(),
            device_id=self.device_id,
            position=np.zeros(3),
            velocity=np.zeros(3),
            acceleration=np.zeros(3),
            motor_current=0.0,
            motor_voltage=0.0,
            power_consumption=0.0,
            temperature=20.0,
            thermal_mass=10.0,
            spindle_wear=0.0,
            bearing_wear=0.0,
            tool_wear=0.0,
            is_running=False,
            current_program=None,
            cycle_count=0
        )
    
    def update(self, control_inputs: Dict, dt: float = None) -> VirtualDeviceState:
        """
        Update device state based on control inputs
        
        Args:
            control_inputs: Dictionary with control commands
            dt: Time step (optional, uses self.dt if not provided)
            
        Returns:
            Updated device state
        """
        if dt is None:
            dt = self.dt
        
        # Physics simulation
        self.state = self.physics_model.simulate_step(
            self.state,
            control_inputs,
            dt
        )
        
        # Thermal simulation
        self.state = self.thermal_model.update_temperature(
            self.state,
            dt
        )
        
        # Wear progression
        self.state = self.wear_model.update_wear(
            self.state,
            dt
        )
        
        self.state.timestamp = datetime.now()
        
        return self.state
    
    def synchronize_with_physical(self, physical_data: Dict):
        """Synchronize twin with physical device data"""
        # Update state from physical device
        self.state.motor_current = physical_data.get('current_mean', self.state.motor_current)
        self.state.temperature = physical_data.get('temperature_mean', self.state.temperature)
        
        # Calibrate models if divergence detected
        divergence = self._calculate_divergence(physical_data)
        if divergence > 0.1:  # 10% divergence threshold
            self._recalibrate_models(physical_data)
    
    def _calculate_divergence(self, physical_data: Dict) -> float:
        """Calculate divergence between twin and physical device"""
        predicted_current = self.state.motor_current
        actual_current = physical_data.get('current_mean', 0)
        
        if actual_current == 0:
            return 0.0
        
        return abs(predicted_current - actual_current) / actual_current
    
    def _recalibrate_models(self, physical_data: Dict):
        """Recalibrate physics and wear models based on real data"""
        logger.info(f"Recalibrating models for device {self.device_id}")
        self.physics_model.calibrate(physical_data)
        self.wear_model.calibrate(physical_data)
```

### 2. Physics Engine

```python
# python-control-layer/digital_twin/physics_model.py
class PhysicsModel:
    """Physics-based simulation of device behavior"""
    
    def __init__(self, device_config: Dict):
        # Device physical properties
        self.mass = device_config.get('mass', 100.0)  # kg
        self.friction_coefficient = device_config.get('friction', 0.1)
        self.max_acceleration = device_config.get('max_accel', 5.0)  # m/s²
        self.max_velocity = device_config.get('max_velocity', 2.0)  # m/s
        
        # Motor properties
        self.motor_efficiency = device_config.get('motor_efficiency', 0.85)
        self.gear_ratio = device_config.get('gear_ratio', 10.0)
        self.motor_constant = device_config.get('motor_constant', 0.5)  # Torque/Amp
    
    def simulate_step(
        self,
        state: VirtualDeviceState,
        control_inputs: Dict,
        dt: float
    ) -> VirtualDeviceState:
        """
        Simulate one physics time step
        
        Uses Newton's laws and motor dynamics
        """
        # Extract control inputs
        target_velocity = np.array(control_inputs.get('target_velocity', [0, 0, 0]))
        feedrate = control_inputs.get('feedrate', 0.0)  # mm/min
        
        # Calculate required acceleration
        velocity_error = target_velocity - state.velocity
        required_accel = velocity_error / dt
        
        # Limit acceleration
        accel_magnitude = np.linalg.norm(required_accel)
        if accel_magnitude > self.max_acceleration:
            required_accel = required_accel / accel_magnitude * self.max_acceleration
        
        # Calculate motor current required
        # Force = mass * acceleration + friction
        force = self.mass * required_accel + self.friction_coefficient * self.mass * 9.81
        torque = force * 0.1  # Assuming 10cm moment arm
        motor_torque = torque * self.gear_ratio
        motor_current = motor_torque / self.motor_constant
        
        # Update state
        state.acceleration = required_accel
        state.velocity = state.velocity + required_accel * dt
        state.position = state.position + state.velocity * dt
        state.motor_current = abs(motor_current)
        state.power_consumption = state.motor_current * 24.0 * (1 / self.motor_efficiency)
        
        return state
    
    def calibrate(self, physical_data: Dict):
        """Calibrate model parameters from physical data"""
        # Adjust friction coefficient based on actual vs predicted current
        actual_current = physical_data.get('current_mean', 0)
        if actual_current > 0:
            correction_factor = actual_current / max(self.motor_current, 0.1)
            self.friction_coefficient *= correction_factor
            self.friction_coefficient = max(0.05, min(0.5, self.friction_coefficient))
```

### 3. Wear Model

```python
# python-control-layer/digital_twin/wear_model.py
class WearModel:
    """Model component wear and degradation"""
    
    def __init__(self):
        # Wear coefficients (calibrated from historical data)
        self.spindle_wear_rate = 1e-6  # Per hour at nominal load
        self.bearing_wear_rate = 5e-7
        self.tool_wear_rate = 1e-5
        
        # Wear acceleration factors
        self.overload_factor = 2.0  # Wear doubles when overloaded
        self.speed_factor = 1.5  # Higher speeds increase wear
        self.temperature_factor = 1.2  # Higher temps increase wear
    
    def update_wear(
        self,
        state: VirtualDeviceState,
        dt: float
    ) -> VirtualDeviceState:
        """Update wear levels"""
        if not state.is_running:
            return state
        
        # Calculate wear acceleration factors
        load_factor = 1.0
        if state.motor_current > 8.0:  # Above nominal
            load_factor = self.overload_factor
        
        temp_factor = 1.0
        if state.temperature > 60.0:
            temp_factor = self.temperature_factor
        
        # Update wear (in hours)
        dt_hours = dt / 3600.0
        
        state.spindle_wear += (
            self.spindle_wear_rate * dt_hours * load_factor * temp_factor
        )
        state.bearing_wear += (
            self.bearing_wear_rate * dt_hours * load_factor
        )
        state.tool_wear += (
            self.tool_wear_rate * dt_hours * load_factor
        )
        
        # Ensure wear is bounded [0, 1]
        state.spindle_wear = min(1.0, state.spindle_wear)
        state.bearing_wear = min(1.0, state.bearing_wear)
        state.tool_wear = min(1.0, state.tool_wear)
        
        return state
    
    def predict_rul(self, state: VirtualDeviceState) -> Dict:
        """Predict Remaining Useful Life based on wear state"""
        # Calculate RUL for each component
        spindle_rul = self._calculate_component_rul(
            state.spindle_wear,
            self.spindle_wear_rate,
            threshold=0.8
        )
        
        bearing_rul = self._calculate_component_rul(
            state.bearing_wear,
            self.bearing_wear_rate,
            threshold=0.8
        )
        
        tool_rul = self._calculate_component_rul(
            state.tool_wear,
            self.tool_wear_rate,
            threshold=1.0  # Tool can wear to 100%
        )
        
        return {
            'spindle_rul_hours': spindle_rul,
            'bearing_rul_hours': bearing_rul,
            'tool_rul_hours': tool_rul,
            'limiting_component': min(
                [('spindle', spindle_rul), ('bearing', bearing_rul), ('tool', tool_rul)],
                key=lambda x: x[1]
            )[0]
        }
    
    def _calculate_component_rul(
        self,
        current_wear: float,
        wear_rate: float,
        threshold: float
    ) -> float:
        """Calculate RUL for a component"""
        remaining_wear = threshold - current_wear
        if remaining_wear <= 0:
            return 0.0
        
        # RUL in hours
        return remaining_wear / wear_rate
```

## Simulation Scenarios

### 1. What-If Analysis

```python
# python-control-layer/digital_twin/simulator.py
class DigitalTwinSimulator:
    """Run simulations and what-if scenarios"""
    
    def __init__(self, virtual_device: VirtualDevice):
        self.twin = virtual_device
        self.initial_state = None
    
    def run_scenario(
        self,
        scenario_name: str,
        control_sequence: List[Dict],
        duration_hours: float
    ) -> Dict:
        """
        Run a simulation scenario
        
        Args:
            scenario_name: Name of the scenario
            control_sequence: Sequence of control inputs
            duration_hours: Simulation duration
            
        Returns:
            Simulation results
        """
        # Save initial state
        self.initial_state = self.twin.state
        
        # Run simulation
        results = {
            'scenario': scenario_name,
            'duration_hours': duration_hours,
            'timeline': [],
            'final_state': None,
            'metrics': {}
        }
        
        simulation_time = 0.0
        dt = 0.1  # 100ms time step
        
        while simulation_time < duration_hours * 3600:
            # Get control input for this time
            control = self._interpolate_control(
                control_sequence,
                simulation_time
            )
            
            # Simulate one step
            state = self.twin.update(control, dt)
            
            # Record state
            results['timeline'].append({
                'time': simulation_time,
                'state': state
            })
            
            simulation_time += dt
        
        # Calculate metrics
        results['final_state'] = state
        results['metrics'] = self._calculate_metrics(results['timeline'])
        
        # Restore initial state
        self.twin.state = self.initial_state
        
        return results
    
    def compare_scenarios(
        self,
        scenarios: List[Dict]
    ) -> Dict:
        """Compare multiple scenarios"""
        results = []
        
        for scenario in scenarios:
            result = self.run_scenario(
                scenario['name'],
                scenario['control_sequence'],
                scenario['duration_hours']
            )
            results.append(result)
        
        # Compare metrics
        comparison = {
            'scenarios': [r['scenario'] for r in results],
            'total_energy': [r['metrics']['total_energy'] for r in results],
            'final_wear': [r['final_state'].spindle_wear for r in results],
            'cycle_time': [r['metrics']['cycle_time'] for r in results],
            'best_scenario': self._select_best_scenario(results)
        }
        
        return comparison
    
    def optimize_parameters(
        self,
        objective: str,  # 'minimize_energy', 'minimize_wear', 'minimize_time'
        constraints: Dict
    ) -> Dict:
        """
        Optimize operational parameters
        
        Uses genetic algorithm or gradient descent to find optimal settings
        """
        from scipy.optimize import differential_evolution
        
        def objective_function(params):
            # Run simulation with parameters
            control_sequence = self._params_to_control_sequence(params)
            result = self.run_scenario(
                'optimization',
                control_sequence,
                duration_hours=1.0
            )
            
            # Return objective value
            if objective == 'minimize_energy':
                return result['metrics']['total_energy']
            elif objective == 'minimize_wear':
                return result['final_state'].spindle_wear
            elif objective == 'minimize_time':
                return result['metrics']['cycle_time']
        
        # Define parameter bounds
        bounds = [
            (constraints.get('min_feedrate', 100), constraints.get('max_feedrate', 3000)),
            (constraints.get('min_spindle_speed', 1000), constraints.get('max_spindle_speed', 12000))
        ]
        
        # Optimize
        result = differential_evolution(
            objective_function,
            bounds,
            maxiter=100,
            popsize=15
        )
        
        return {
            'optimal_params': result.x,
            'objective_value': result.fun,
            'feedrate': result.x[0],
            'spindle_speed': result.x[1]
        }
```

### 2. Failure Prediction

```python
# python-control-layer/digital_twin/failure_predictor.py
class FailurePredictor:
    """Predict failures using digital twin"""
    
    def __init__(self, twin: VirtualDevice):
        self.twin = twin
        self.failure_thresholds = {
            'spindle_wear': 0.8,
            'bearing_wear': 0.8,
            'temperature': 85.0,
            'current_overload': 10.0
        }
    
    def predict_failure_probability(
        self,
        lookahead_hours: float = 24.0
    ) -> Dict:
        """
        Predict probability of failure in the next N hours
        
        Runs simulation forward to detect potential failures
        """
        # Save current state
        initial_state = self.twin.state
        
        # Simulate forward
        failure_events = []
        simulation_time = 0.0
        dt = 60.0  # 1 minute steps for faster simulation
        
        while simulation_time < lookahead_hours * 3600:
            # Assume current operating conditions continue
            control = {
                'target_velocity': initial_state.velocity,
                'feedrate': 1000.0
            }
            
            state = self.twin.update(control, dt)
            
            # Check for failure conditions
            if state.spindle_wear > self.failure_thresholds['spindle_wear']:
                failure_events.append({
                    'time_hours': simulation_time / 3600,
                    'type': 'spindle_wear',
                    'severity': 'high',
                    'value': state.spindle_wear
                })
            
            if state.temperature > self.failure_thresholds['temperature']:
                failure_events.append({
                    'time_hours': simulation_time / 3600,
                    'type': 'thermal_overload',
                    'severity': 'critical',
                    'value': state.temperature
                })
            
            simulation_time += dt
        
        # Restore state
        self.twin.state = initial_state
        
        # Calculate failure probability
        failure_probability = len(failure_events) / (lookahead_hours * 60)  # Failures per hour
        
        return {
            'lookahead_hours': lookahead_hours,
            'failure_probability': min(1.0, failure_probability),
            'predicted_failures': failure_events,
            'risk_level': self._assess_risk_level(failure_probability)
        }
    
    def _assess_risk_level(self, probability: float) -> str:
        """Assess risk level based on failure probability"""
        if probability < 0.1:
            return 'low'
        elif probability < 0.5:
            return 'medium'
        else:
            return 'high'
```

## API Endpoints

```python
# python-control-layer/digital_twin_api.py
from fastapi import APIRouter, Depends
from auth import UserContext, get_user_context

router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])

@router.post("/devices/{device_id}/twin/create")
async def create_digital_twin(
    device_id: str,
    device_config: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Create a digital twin for a device"""
    twin = VirtualDevice(device_id, device_config)
    twin_manager.register_twin(device_id, twin)
    
    return {
        'device_id': device_id,
        'twin_created': True,
        'initial_state': twin.state
    }

@router.get("/devices/{device_id}/twin/state")
async def get_twin_state(
    device_id: str,
    user: UserContext = Depends(get_user_context)
):
    """Get current state of digital twin"""
    twin = twin_manager.get_twin(device_id)
    return twin.state

@router.post("/devices/{device_id}/twin/simulate")
async def run_simulation(
    device_id: str,
    scenario: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Run a simulation scenario"""
    twin = twin_manager.get_twin(device_id)
    simulator = DigitalTwinSimulator(twin)
    
    result = simulator.run_scenario(
        scenario['name'],
        scenario['control_sequence'],
        scenario['duration_hours']
    )
    
    return result

@router.post("/devices/{device_id}/twin/optimize")
async def optimize_parameters(
    device_id: str,
    objective: str,
    constraints: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Optimize operational parameters"""
    twin = twin_manager.get_twin(device_id)
    simulator = DigitalTwinSimulator(twin)
    
    result = simulator.optimize_parameters(objective, constraints)
    
    return result

@router.get("/devices/{device_id}/twin/predict-failure")
async def predict_failure(
    device_id: str,
    lookahead_hours: float = 24.0,
    user: UserContext = Depends(get_user_context)
):
    """Predict failure probability"""
    twin = twin_manager.get_twin(device_id)
    predictor = FailurePredictor(twin)
    
    return predictor.predict_failure_probability(lookahead_hours)

@router.post("/devices/{device_id}/twin/synchronize")
async def synchronize_twin(
    device_id: str,
    physical_data: Dict,
    user: UserContext = Depends(get_user_context)
):
    """Synchronize twin with physical device"""
    twin = twin_manager.get_twin(device_id)
    twin.synchronize_with_physical(physical_data)
    
    return {
        'synchronized': True,
        'divergence': twin._calculate_divergence(physical_data)
    }
```

## Visualization

### 3D Visualization
```javascript
// Use Three.js or Babylon.js for 3D rendering
const digitalTwinViewer = {
  scene: null,
  device3DModel: null,
  
  init() {
    this.scene = new THREE.Scene();
    this.loadDeviceModel();
    this.setupCamera();
    this.setupLights();
  },
  
  updateFromState(state) {
    // Update 3D model position
    this.device3DModel.position.set(
      state.position[0],
      state.position[1],
      state.position[2]
    );
    
    // Update visual indicators
    this.updateWearIndicators(state);
    this.updateTemperatureHeatmap(state);
  },
  
  renderWhatIfScenario(simulationResults) {
    // Animate through simulation timeline
    simulationResults.timeline.forEach((frame, index) => {
      setTimeout(() => {
        this.updateFromState(frame.state);
      }, index * 100);  // 10 FPS playback
    });
  }
};
```

## Benefits

### Operational Benefits
- **Risk-free testing** of operational changes
- **Predictive maintenance** with high accuracy
- **Parameter optimization** before production
- **Training platform** for operators
- **Failure root cause analysis**

### Cost Benefits
- **Reduced downtime** through predictive insights
- **Optimized energy consumption**
- **Extended equipment life**
- **Reduced trial-and-error** costs
- **Better maintenance planning**

## Related Documentation

- [ML Training Pipeline](ML_TRAINING_PIPELINE.md)
- [ONNX Model Deployment](ONNX_MODEL_DEPLOYMENT.md)
- [Fleet Analytics](FLEET_ANALYTICS.md)
- [Predictive Maintenance](ADVANCED_CNC_INDUSTRY_4_0.md)
- [Cloud Integration](CLOUD_INTEGRATION.md)
