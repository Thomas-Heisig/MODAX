"""Tests for WebSocket manager"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Tests for WebSocketManager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = WebSocketManager()
    
    def teardown_method(self):
        """Clean up test environment"""
        self.manager.active_connections.clear()
        self.manager.device_subscriptions.clear()
    
    @pytest.mark.asyncio
    async def test_connect_without_device(self):
        """Test connecting WebSocket without device subscription"""
        mock_ws = AsyncMock()
        
        await self.manager.connect(mock_ws)
        
        assert len(self.manager.active_connections) == 1
        assert mock_ws in self.manager.active_connections
        mock_ws.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_with_device(self):
        """Test connecting WebSocket with device subscription"""
        mock_ws = AsyncMock()
        device_id = "esp32_001"
        
        await self.manager.connect(mock_ws, device_id)
        
        assert len(self.manager.active_connections) == 1
        assert mock_ws in self.manager.active_connections
        assert device_id in self.manager.device_subscriptions
        assert mock_ws in self.manager.device_subscriptions[device_id]
        mock_ws.accept.assert_called_once()
    
    def test_disconnect(self):
        """Test disconnecting WebSocket"""
        mock_ws = MagicMock()
        device_id = "esp32_001"
        
        # Manually add connection
        self.manager.active_connections.append(mock_ws)
        self.manager.device_subscriptions[device_id] = {mock_ws}
        
        self.manager.disconnect(mock_ws)
        
        assert len(self.manager.active_connections) == 0
        assert mock_ws not in self.manager.device_subscriptions[device_id]
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message to WebSocket"""
        mock_ws = AsyncMock()
        message = {"type": "test", "data": "value"}
        
        await self.manager.send_personal_message(message, mock_ws)
        
        mock_ws.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting to all connections"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        self.manager.active_connections = [mock_ws1, mock_ws2]
        
        message = {"type": "broadcast", "data": "test"}
        await self.manager.broadcast(message)
        
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_device_subscribers(self):
        """Test broadcasting to device-specific subscribers"""
        device_id = "esp32_001"
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()
        
        # ws1 and ws2 subscribed to device, ws3 is general
        self.manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        self.manager.device_subscriptions[device_id] = {mock_ws1, mock_ws2}
        
        message = {"type": "sensor_data", "device_id": device_id}
        await self.manager.broadcast(message, device_id)
        
        # Only device subscribers should receive
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
        mock_ws3.send_json.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_sensor_data(self):
        """Test broadcasting sensor data"""
        device_id = "esp32_001"
        mock_ws = AsyncMock()
        self.manager.active_connections = [mock_ws]
        
        data = {"current": 5.2, "vibration": 100.0}
        await self.manager.broadcast_sensor_data(device_id, data)
        
        # Verify message structure
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args['type'] == 'sensor_data'
        assert call_args['device_id'] == device_id
        assert call_args['data'] == data
    
    @pytest.mark.asyncio
    async def test_broadcast_safety_status(self):
        """Test broadcasting safety status"""
        device_id = "esp32_001"
        mock_ws = AsyncMock()
        self.manager.active_connections = [mock_ws]
        
        status = {"is_safe": True, "emergency_stop": False}
        await self.manager.broadcast_safety_status(device_id, status)
        
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args['type'] == 'safety_status'
        assert call_args['device_id'] == device_id
        assert call_args['status'] == status
    
    @pytest.mark.asyncio
    async def test_broadcast_ai_analysis(self):
        """Test broadcasting AI analysis"""
        device_id = "esp32_001"
        mock_ws = AsyncMock()
        self.manager.active_connections = [mock_ws]
        
        analysis = {"anomaly_detected": False, "confidence": 0.95}
        await self.manager.broadcast_ai_analysis(device_id, analysis)
        
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args['type'] == 'ai_analysis'
        assert call_args['device_id'] == device_id
        assert call_args['analysis'] == analysis
    
    @pytest.mark.asyncio
    async def test_broadcast_system_status(self):
        """Test broadcasting system status"""
        mock_ws = AsyncMock()
        self.manager.active_connections = [mock_ws]
        
        status = {"is_safe": True, "devices_online": 3}
        await self.manager.broadcast_system_status(status)
        
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args['type'] == 'system_status'
        assert call_args['status'] == status
    
    def test_get_connection_count(self):
        """Test getting connection count"""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        
        self.manager.active_connections = [mock_ws1, mock_ws2]
        
        assert self.manager.get_connection_count() == 2
    
    def test_get_device_subscriber_count(self):
        """Test getting device subscriber count"""
        device_id = "esp32_001"
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        
        self.manager.device_subscriptions[device_id] = {mock_ws1, mock_ws2}
        
        assert self.manager.get_device_subscriber_count(device_id) == 2
        assert self.manager.get_device_subscriber_count("unknown_device") == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
