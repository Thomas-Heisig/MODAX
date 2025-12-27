# Contributing to MODAX

Thank you for your interest in contributing to MODAX! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Prioritize safety and security in all contributions

## Getting Started

### Prerequisites

- Python 3.8+ for Control and AI layers
- .NET 8.0+ for HMI layer
- ESP32 development tools for Field layer
- Docker and Docker Compose (optional)
- Git for version control

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Thomas-Heisig/MODAX.git
   cd MODAX
   ```

2. **Set up Python environments:**
   ```bash
   # Control Layer
   cd python-control-layer
   pip install -r requirements.txt
   cd ..

   # AI Layer
   cd python-ai-layer
   pip install -r requirements.txt
   cd ..
   ```

3. **Set up .NET HMI:**
   ```bash
   cd csharp-hmi-layer
   dotnet restore
   dotnet build
   cd ..
   ```

4. **Install ESP32 toolchain** (if working on Field layer)
   - Follow instructions in `esp32-field-layer/README.md`

### Running Tests

```bash
# Run all tests with coverage
./test_with_coverage.sh

# Run linting
./lint.sh

# Run end-to-end tests
python test_end_to_end.py
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/modifications

### 2. Make Your Changes

- Follow the coding standards (see below)
- Write tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Test Your Changes

```bash
# Run relevant tests
cd python-control-layer && pytest
cd ../python-ai-layer && pytest

# Run linting
./lint.sh

# Test end-to-end if applicable
python test_end_to_end.py
```

### 4. Commit Your Changes

Follow conventional commit format:

```
type(scope): brief description

Detailed explanation if needed

Fixes #issue-number
```

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting, no code change
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat(control): add G-code validation"
git commit -m "fix(mqtt): resolve reconnection timeout issue"
git commit -m "docs(api): update endpoint documentation"
```

### 5. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots/logs if applicable
- Checklist of completed items

## Coding Standards

⚠️ **WICHTIG:** Bitte lesen Sie die **[GitHub Copilot Instructions](.github/copilot-instructions.md)** für strikte Code-Qualitäts- und Sicherheitsregeln.

**Kernprinzipien:**
- **Payload Strict:** Type hints, Docstrings, Tests sind verpflichtend
- **Immer dokumentieren:** Jede öffentliche Funktion/Klasse muss dokumentiert sein
- **Gleiche Codebase:** Konsistente Patterns und Namenskonventionen
- **Safety First:** KI niemals in sicherheitskritischen Funktionen
- **Ebenentr ennung:** Strikte Trennung der 4 Ebenen einhalten

### Python (Control Layer & AI Layer)

#### Style Guide
- Follow PEP 8 (verpflichtend)
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use descriptive variable names
- **Type hints sind verpflichtend** (siehe Copilot Instructions)
- **Docstrings sind verpflichtend** (Google-Style)

#### Type Hints
```python
def process_sensor_data(
    device_id: str,
    temperature: float,
    current: float
) -> Dict[str, Any]:
    """Process sensor data and return analysis."""
    pass
```

#### Docstrings
Use Google-style docstrings:
```python
def calculate_wear(stress_level: float, duration: float) -> float:
    """
    Calculate wear accumulation based on stress and duration.
    
    Args:
        stress_level: Normalized stress level (0.0 to 1.0)
        duration: Duration in seconds
        
    Returns:
        Accumulated wear value
        
    Raises:
        ValueError: If stress_level is out of range
    """
    if not 0.0 <= stress_level <= 1.0:
        raise ValueError("Stress level must be between 0 and 1")
    return stress_level * duration * WEAR_FACTOR
```

#### Constants
- Use UPPER_CASE for constants
- Group related constants together
- Add comments explaining non-obvious values

```python
# Temperature thresholds in Celsius
TEMP_WARNING_THRESHOLD = 70.0  # Start warning at 70°C
TEMP_CRITICAL_THRESHOLD = 85.0  # Critical at 85°C
TEMP_EMERGENCY_SHUTDOWN = 95.0  # Emergency shutdown
```

#### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

### C# (HMI Layer)

#### Style Guide
- Follow C# conventions
- Use PascalCase for classes and methods
- Use camelCase for local variables
- Use meaningful names

#### Example
```csharp
public class DeviceMonitor
{
    private readonly ILogger _logger;
    
    public async Task<DeviceStatus> GetStatusAsync(string deviceId)
    {
        if (string.IsNullOrEmpty(deviceId))
        {
            throw new ArgumentException("Device ID cannot be null or empty", nameof(deviceId));
        }
        
        try
        {
            return await _client.FetchStatusAsync(deviceId);
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to fetch status for device {DeviceId}", deviceId);
            throw;
        }
    }
}
```

### C++ (ESP32 Field Layer)

- Follow Arduino style guide
- Use meaningful variable names
- Comment complex algorithms
- Keep safety-critical code simple and testable

## Testing Requirements

### Unit Tests

- **Minimum coverage:** 95% for new code
- Test happy path and error cases
- Use meaningful test names
- Mock external dependencies

```python
def test_anomaly_detection_normal_values():
    """Test that normal sensor values don't trigger anomalies."""
    detector = AnomalyDetector()
    result = detector.analyze(temperature=25.0, current=1.5)
    assert not result.is_anomaly
    
def test_anomaly_detection_high_temperature():
    """Test that high temperature triggers anomaly."""
    detector = AnomalyDetector()
    result = detector.analyze(temperature=95.0, current=1.5)
    assert result.is_anomaly
    assert "temperature" in result.anomaly_types
```

### Integration Tests

- Test component interactions
- Use realistic test data
- Verify end-to-end flows

### Performance Tests

- Document expected performance metrics
- Test with realistic data volumes
- Monitor resource usage

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Document parameters, return values, and exceptions
- Explain complex algorithms
- Add inline comments for non-obvious code

### Project Documentation

When adding features, update:
- `docs/API.md` - API changes
- `docs/CONFIGURATION.md` - New configuration options
- `docs/ARCHITECTURE.md` - Architectural changes
- `README.md` - Major features
- `CHANGELOG.md` - All changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation up-to-date with code

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass (`./test_with_coverage.sh`)
- [ ] Linting passes (`./lint.sh`)
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description is clear and complete
- [ ] Related issues are referenced

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123

## Testing
- Describe tests performed
- Include test results

## Checklist
- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)

## Screenshots (if applicable)
```

### Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer review required
3. Address review comments
4. Maintainer will merge when approved

## Issue Reporting

### Before Creating an Issue

- Search existing issues
- Check documentation
- Verify you're using the latest version

### Bug Reports

Include:
- MODAX version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Screenshots if applicable

### Feature Requests

Include:
- Clear use case description
- Expected behavior
- Why this feature is needed
- Proposed implementation (optional)

### Security Issues

**Do not** create public issues for security vulnerabilities.
Contact the maintainers privately via GitHub's private vulnerability reporting feature or by opening a private security advisory.

## Priority Levels

When working on issues, consider priority:

1. **Kritisch (Critical):** Security issues, data loss, system crashes
2. **Hoch (High):** Major functionality broken, significant bugs
3. **Mittel (Medium):** Minor bugs, improvements
4. **Niedrig (Low):** Nice-to-have features, documentation
5. **Sehr Niedrig (Very Low):** Cosmetic issues

## Safety-Critical Code

MODAX includes safety-critical components. When working on:
- Field Layer (ESP32) safety monitoring
- Control Layer safety validation
- Emergency shutdown logic

**Extra requirements:**
- Extensive testing required
- Thorough documentation
- Security review needed
- No AI/ML in safety paths

## Questions?

- Check documentation: `docs/INDEX.md`
- Open a discussion on GitHub
- Contact maintainers

## License

By contributing to MODAX, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to MODAX! 🚀
