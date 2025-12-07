# MODAX - Error Handling Guide

This document describes error handling patterns and best practices used throughout the MODAX system.

## Overview

The MODAX system uses structured, layered error handling to ensure system stability while maintaining clear logging and diagnostics.

## Error Handling Principles

### 1. Fail Safely
- **Safety-critical systems** (Field Layer) should fail to a safe state
- **Non-critical systems** (AI Layer) should gracefully degrade
- Always log errors before handling them

### 2. Error Context
- Include relevant context in error messages (device ID, operation, state)
- Use structured logging with consistent format
- Preserve stack traces for debugging

### 3. Recovery Strategies
- Implement automatic recovery where possible (e.g., MQTT reconnection)
- Use exponential backoff for retry logic
- Set maximum retry limits to prevent infinite loops

## Layer-Specific Error Handling

### Field Layer (ESP32)
**Priority: Safety First**

- Hardware interlocks remain active even during software errors
- Watchdog timer ensures system restart on critical failures
- Safety functions are KI-free and deterministic

**Error Types:**
- Sensor read failures → Use last known good value, log warning
- Communication errors → Continue safety monitoring, attempt reconnect
- Critical safety violations → Immediate shutdown, log alert

### Control Layer (Python)
**Priority: Data Integrity and Availability**

#### MQTT Communication Errors
```python
# Automatic reconnection with exponential backoff
MQTT_RECONNECT_DELAY_MIN = 1  # seconds
MQTT_RECONNECT_DELAY_MAX = 60  # seconds
MQTT_RECONNECT_BACKOFF_MULTIPLIER = 2
```

**Error Types:**
- Connection lost → Automatic reconnection with exponential backoff
- Invalid message format → Log error, skip message, continue processing
- Data validation failures → Reject data, log warning

**Implementation:**
```python
try:
    # Operation
    result = perform_operation()
except ConnectionError as e:
    logger.error(f"Connection error: {e}", exc_info=True)
    # Trigger reconnection logic
except ValueError as e:
    logger.warning(f"Invalid data: {e}")
    # Skip this data point
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # Fail gracefully
```

#### API Timeout Configuration
API timeouts are configurable via environment variables:

```bash
AI_LAYER_TIMEOUT=5  # seconds (default: 5)
AI_LAYER_URL=http://localhost:8001/analyze
```

**Error Types:**
- Timeout → Log warning, return None, continue operation
- HTTP errors → Log error, return None, continue operation
- Network errors → Log warning, return None, continue operation

### AI Layer (Python)
**Priority: Advisory Quality**

- All AI errors are non-critical (advisory only)
- System continues operation without AI analysis if errors occur
- Never throw unhandled exceptions to calling code

**Error Types:**
- Model errors → Return error status, log details
- Invalid input → Return validation error, log warning
- Resource exhaustion → Throttle requests, log warning

**Implementation:**
```python
try:
    analysis = perform_analysis(data)
    return {
        "success": True,
        "analysis": analysis
    }
except Exception as e:
    logger.error(f"Analysis failed: {e}", exc_info=True)
    return {
        "success": False,
        "error": str(e),
        "analysis": None
    }
```

### HMI Layer (C#)
**Priority: User Experience**

- Display user-friendly error messages
- Log technical details for debugging
- Provide recovery options where possible

**Error Types:**
- API connection errors → Display connection status indicator
- Data display errors → Show last known good data
- UI errors → Log error, restore previous state

## Logging Standards

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| **DEBUG** | Detailed diagnostic information | Message payloads, internal state changes |
| **INFO** | General informational messages | Connection established, operation completed |
| **WARNING** | Unusual but recoverable conditions | Timeout occurred, retrying operation |
| **ERROR** | Error conditions that don't stop operation | Failed API call, invalid data received |
| **CRITICAL** | Critical conditions requiring immediate action | Safety violation, system shutdown |

### Logging Format

All Python layers use consistent logging format:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

### What to Log

#### Always Log:
- Connection state changes (connect, disconnect, reconnect)
- Safety-related events (warnings, violations)
- Configuration changes
- Error conditions with stack traces

#### Conditionally Log (DEBUG level):
- Message payloads
- Sensor readings (raw values)
- Internal state transitions
- Performance metrics

#### Never Log:
- Passwords or authentication tokens
- Personally identifiable information (PII)
- Excessively verbose repeated messages

## Error Recovery Patterns

### 1. Exponential Backoff
Used for MQTT reconnection and API retries:

```python
delay = min(
    initial_delay * (multiplier ** attempt),
    max_delay
)
time.sleep(delay)
```

**Parameters:**
- Initial delay: 1 second
- Max delay: 60 seconds
- Multiplier: 2

### 2. Circuit Breaker
Prevent cascading failures by temporarily stopping requests after repeated failures:

```python
if failure_count > threshold:
    # Open circuit - reject requests
    logger.warning("Circuit breaker opened")
    return None

# After timeout, try again
if time.time() > circuit_reset_time:
    # Close circuit - allow requests
    failure_count = 0
```

### 3. Graceful Degradation
Continue operation with reduced functionality:

- **No AI Layer?** → Continue with basic monitoring
- **No MQTT?** → Use cached data, attempt reconnection
- **Partial sensor failure?** → Use available sensors

## Configuration

### Environment Variables

Error handling behavior can be configured:

```bash
# AI Layer Timeout
AI_LAYER_TIMEOUT=5  # seconds

# MQTT Reconnection (hardcoded, future configurable)
# MQTT_RECONNECT_MIN_DELAY=1
# MQTT_RECONNECT_MAX_DELAY=60

# Logging Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Testing Error Handling

### Test Scenarios

1. **Network Interruption**
   - Disconnect MQTT broker
   - Verify automatic reconnection
   - Check exponential backoff behavior

2. **Invalid Data**
   - Send malformed JSON messages
   - Verify error logging
   - Check system continues operation

3. **API Timeout**
   - Set very short timeout
   - Verify timeout handling
   - Check graceful degradation

4. **Resource Exhaustion**
   - Simulate high load
   - Verify throttling behavior
   - Check recovery after load reduction

## Best Practices

### DO:
✅ Use try-except blocks for external operations (network, file I/O)  
✅ Log errors with context information  
✅ Implement automatic recovery for transient failures  
✅ Use specific exception types  
✅ Include stack traces in error logs  
✅ Test error handling paths  

### DON'T:
❌ Swallow exceptions silently  
❌ Use bare `except:` clauses  
❌ Log and re-raise the same exception  
❌ Expose internal details in user-facing messages  
❌ Retry indefinitely without backoff  
❌ Let errors crash the entire system  

## Monitoring and Alerting

### Key Metrics
- MQTT connection uptime
- API error rate
- Average response time
- Failed analysis count

### Alert Conditions
- MQTT connection down > 5 minutes
- API error rate > 10%
- Safety violation detected
- Consecutive AI analysis failures > 10

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [MQTT Paho Client Documentation](https://eclipse.org/paho/clients/python/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

---

**Last Updated:** 2025-12-07  
**Maintained By:** MODAX Development Team
