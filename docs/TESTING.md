# Testing and Code Quality Guide

This document describes how to run tests and code quality checks for the MODAX project.

## Quick Start

### Run All Tests
```bash
# Control Layer tests
cd python-control-layer
python -m unittest discover -s . -p 'test_*.py' -v

# AI Layer tests
cd python-ai-layer
python -m unittest discover -s . -p 'test_*.py' -v
```

### Run Tests with Coverage
```bash
./test_with_coverage.sh
```

This will:
- Run all tests for Control Layer and AI Layer
- Generate coverage reports in `coverage_reports/` directory
- Display coverage statistics in the terminal

Current coverage:
- **Control Layer: 97%**
- **AI Layer: 96%**

### Run Code Linting
```bash
./lint.sh
```

This will:
- Run flake8 to check code style and quality
- Run pylint to check for additional issues
- Display any violations found

## Test Structure

### Control Layer Tests

| Test File | Purpose | Tests |
|-----------|---------|-------|
| `test_config.py` | Configuration module tests | 8 |
| `test_ai_interface.py` | AI layer communication tests | 6 |
| `test_data_aggregator.py` | Data aggregation tests | 10 |
| `test_mqtt_handler.py` | MQTT handler tests | 8 |
| `test_integration_mqtt.py` | MQTT integration tests | 10 |

**Total Control Layer Tests: 42**

### AI Layer Tests

| Test File | Purpose | Tests |
|-----------|---------|-------|
| `test_ai_service.py` | AI service API tests | 13 |
| `test_optimizer.py` | Optimization recommender tests | 22 |
| `test_anomaly_detector.py` | Anomaly detection tests | 12 |
| `test_wear_predictor.py` | Wear prediction tests | 9 |

**Total AI Layer Tests: 56**

**Grand Total: 98 tests**

## Writing Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`

### Example Test Structure
```python
"""Unit tests for Example module"""
import unittest
from example_module import ExampleClass


class TestExampleClass(unittest.TestCase):
    """Tests for ExampleClass"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.example = ExampleClass()
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.example.do_something()
        self.assertEqual(result, expected_value)
    
    def test_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            self.example.do_something_invalid()


if __name__ == '__main__':
    unittest.main()
```

## Code Quality Standards

### Flake8 Configuration
- Maximum line length: 100 characters
- Ignores: E203, W503 (conflicts with black)
- Maximum complexity: 12
- Configuration file: `.flake8`

### Pylint Configuration
- Maximum line length: 100 characters
- Maximum arguments: 8
- Maximum locals: 20
- Maximum statements: 60
- Configuration file: `.pylintrc`

### Code Style Guidelines
1. Use descriptive variable and function names
2. Add docstrings to all public functions and classes
3. Keep functions focused and small
4. Extract magic numbers to named constants
5. Handle errors appropriately with try-except blocks
6. Use type hints where appropriate

## Continuous Integration

When implementing CI/CD (TODO), these scripts will be used:

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r python-control-layer/requirements.txt
        pip install -r python-ai-layer/requirements.txt
        pip install flake8 pylint coverage httpx
    
    - name: Run linting
      run: ./lint.sh
    
    - name: Run tests with coverage
      run: ./test_with_coverage.sh
```

## Coverage Goals

We aim to maintain **>95% code coverage** for all Python modules.

### Viewing Coverage Reports

After running `./test_with_coverage.sh`, open the HTML reports:

```bash
# Control Layer
open coverage_reports/control_layer/index.html

# AI Layer
open coverage_reports/ai_layer/index.html
```

Or use your browser:
- Control Layer: `file:///path/to/MODAX/coverage_reports/control_layer/index.html`
- AI Layer: `file:///path/to/MODAX/coverage_reports/ai_layer/index.html`

## Running Specific Tests

### Run Single Test File
```bash
cd python-control-layer
python -m unittest test_config.py -v
```

### Run Single Test Class
```bash
cd python-control-layer
python -m unittest test_config.TestMQTTConfig -v
```

### Run Single Test Method
```bash
cd python-control-layer
python -m unittest test_config.TestMQTTConfig.test_mqtt_config_defaults -v
```

## Debugging Tests

### Run Tests with More Verbose Output
```bash
python -m unittest test_module.py -v
```

### Run Tests with PDB Debugger
```python
import unittest
import pdb

class TestExample(unittest.TestCase):
    def test_something(self):
        # Set breakpoint
        pdb.set_trace()
        result = function_to_test()
        self.assertEqual(result, expected)
```

## Test Data and Fixtures

### Sample Sensor Data
```python
sample_sensor_data = {
    "device_id": "device_001",
    "current_mean": [5.0, 5.1, 4.9],
    "vibration_mean": {"x": 1.0, "y": 1.1, "z": 0.9, "magnitude": 1.8},
    "temperature_mean": [45.0, 46.0, 44.5],
    "sample_count": 10
}
```

### Mock MQTT Client
```python
from unittest.mock import Mock

mock_client = Mock()
mock_client.connect.return_value = 0
mock_client.subscribe.return_value = (0, 1)
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the correct directory
   cd python-control-layer  # or python-ai-layer
   # Or set PYTHONPATH
   export PYTHONPATH=/path/to/MODAX/python-control-layer:$PYTHONPATH
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install httpx  # For FastAPI test client
   ```

3. **Tests Fail After Code Changes**
   - Check if the test expectations need updating
   - Run individual tests to isolate the issue
   - Check for side effects between tests

## Best Practices

1. **Test Independence**: Each test should be able to run independently
2. **Use setUp/tearDown**: Initialize test fixtures in setUp(), cleanup in tearDown()
3. **Mock External Dependencies**: Use unittest.mock for external services
4. **Test Edge Cases**: Test boundary conditions, error cases, and normal operation
5. **Keep Tests Fast**: Unit tests should run quickly (<1 second each)
6. **Descriptive Assertions**: Use clear assertion messages
7. **One Concept Per Test**: Each test should verify one specific behavior

## Related Documentation

- [API Documentation](API.md)
- [Error Handling](ERROR_HANDLING.md)
- [Logging Standards](LOGGING_STANDARDS.md)
- [Configuration](CONFIGURATION.md)
