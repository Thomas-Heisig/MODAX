"""
Unit tests for OPC UA Server
"""

import pytest
import asyncio
from opcua_server import MODAXOpcUaServer, init_opcua_server, stop_opcua_server


@pytest.mark.asyncio
async def test_opcua_server_initialization():
    """Test OPC UA server initialization"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4841",
        enable_security=False
    )
    
    await server.init()
    assert server.namespace_idx is not None
    assert server.devices_folder is not None
    assert server.system_folder is not None
    
    # Clean up
    if server.is_running:
        await server.stop()


@pytest.mark.asyncio
async def test_opcua_server_start_stop():
    """Test starting and stopping OPC UA server"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4842",
        enable_security=False
    )
    
    await server.init()
    assert not server.is_running
    
    await server.start()
    assert server.is_running
    
    await server.stop()
    assert not server.is_running


@pytest.mark.asyncio
async def test_add_device():
    """Test adding a device to OPC UA namespace"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4843",
        enable_security=False
    )
    
    await server.init()
    await server.start()
    
    # Add a device
    device_id = "esp32_test_001"
    await server.add_device(device_id)
    
    assert device_id in server.device_nodes
    assert "variables" in server.device_nodes[device_id]
    
    # Verify variables exist
    variables = server.device_nodes[device_id]["variables"]
    assert "DeviceID" in variables
    assert "Current_A" in variables
    assert "Temperature" in variables
    assert "IsAnomaly" in variables
    
    await server.stop()


@pytest.mark.asyncio
async def test_update_device_data():
    """Test updating device sensor data"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4844",
        enable_security=False
    )
    
    await server.init()
    await server.start()
    
    device_id = "esp32_test_002"
    
    # Update device data (should auto-create device)
    test_data = {
        "current_a": 1.5,
        "current_b": 1.6,
        "current_c": 1.4,
        "vibration": 0.2,
        "temperature": 45.5,
        "rpm": 1500,
        "power_kw": 2.3,
        "is_safe": True,
        "status": "Running"
    }
    
    await server.update_device_data(device_id, test_data)
    
    # Verify device was created
    assert device_id in server.device_nodes
    
    # Read back values
    variables = server.device_nodes[device_id]["variables"]
    current_a_value = await variables["Current_A"].read_value()
    assert abs(current_a_value - 1.5) < 0.001
    
    temp_value = await variables["Temperature"].read_value()
    assert abs(temp_value - 45.5) < 0.001
    
    await server.stop()


@pytest.mark.asyncio
async def test_update_ai_analysis():
    """Test updating AI analysis data"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4845",
        enable_security=False
    )
    
    await server.init()
    await server.start()
    
    device_id = "esp32_test_003"
    await server.add_device(device_id)
    
    # Update AI analysis
    analysis_data = {
        "is_anomaly": True,
        "anomaly_score": 0.85,
        "wear_percentage": 45.2,
        "remaining_hours": 120,
        "confidence": 0.92
    }
    
    await server.update_ai_analysis(device_id, analysis_data)
    
    # Read back values
    variables = server.device_nodes[device_id]["variables"]
    is_anomaly = await variables["IsAnomaly"].read_value()
    assert is_anomaly is True
    
    confidence = await variables["Confidence"].read_value()
    assert abs(confidence - 0.92) < 0.001
    
    await server.stop()


@pytest.mark.asyncio
async def test_update_system_status():
    """Test updating system-level status"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4846",
        enable_security=False
    )
    
    await server.init()
    await server.start()
    
    # Update system status
    await server.update_system_status(connected_devices=5)
    
    # Note: Reading system status requires navigating the OPC UA tree
    # This is a simplified test to ensure no errors occur
    
    await server.stop()


@pytest.mark.asyncio
async def test_init_opcua_server_disabled():
    """Test initializing OPC UA server when disabled"""
    server = await init_opcua_server(enable=False)
    assert server is None


@pytest.mark.asyncio
async def test_init_opcua_server_enabled():
    """Test initializing OPC UA server when enabled"""
    server = await init_opcua_server(
        enable=True,
        endpoint="opc.tcp://localhost:4847",
        enable_security=False
    )
    
    assert server is not None
    assert server.is_running
    
    await stop_opcua_server()


@pytest.mark.asyncio
async def test_duplicate_device_add():
    """Test adding the same device twice (should not error)"""
    server = MODAXOpcUaServer(
        endpoint="opc.tcp://localhost:4848",
        enable_security=False
    )
    
    await server.init()
    await server.start()
    
    device_id = "esp32_test_004"
    
    # Add device twice
    await server.add_device(device_id)
    await server.add_device(device_id)  # Should log warning but not error
    
    # Should still have one device
    assert device_id in server.device_nodes
    
    await server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
