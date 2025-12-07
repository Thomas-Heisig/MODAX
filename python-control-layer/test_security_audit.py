"""Tests for security audit logging"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from security_audit import SecurityAuditLogger


class TestSecurityAuditLogger:
    """Tests for SecurityAuditLogger"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create temporary log file
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, 'test_audit.log')
        self.logger = SecurityAuditLogger(self.log_path)
    
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up temp files
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def read_log_entries(self):
        """Read and parse log entries"""
        if not os.path.exists(self.log_path):
            return []
        
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        entries = []
        for line in lines:
            if line.strip():
                entries.append(json.loads(line))
        return entries
    
    def test_log_authentication_success(self):
        """Test logging successful authentication"""
        self.logger.log_authentication_success(
            user="test_user",
            source_ip="192.168.1.100",
            method="api_key"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'authentication'
        assert entry['severity'] == 'INFO'
        assert entry['action'] == 'login_success'
        assert entry['user'] == 'test_user'
        assert entry['source_ip'] == '192.168.1.100'
        assert entry['metadata']['method'] == 'api_key'
    
    def test_log_authentication_failure(self):
        """Test logging failed authentication"""
        self.logger.log_authentication_failure(
            attempted_user="bad_user",
            source_ip="192.168.1.200",
            reason="invalid_credentials"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'authentication'
        assert entry['severity'] == 'WARNING'
        assert entry['action'] == 'login_failed'
        assert entry['attempted_user'] == 'bad_user'
        assert entry['reason'] == 'invalid_credentials'
    
    def test_log_authorization_denied(self):
        """Test logging authorization denial"""
        self.logger.log_authorization_denied(
            user="operator1",
            resource="/control/emergency-stop",
            action="execute",
            reason="insufficient_permissions"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'authorization'
        assert entry['severity'] == 'WARNING'
        assert entry['action'] == 'access_denied'
        assert entry['user'] == 'operator1'
        assert entry['resource'] == '/control/emergency-stop'
    
    def test_log_control_command_executed(self):
        """Test logging executed control command"""
        self.logger.log_control_command(
            user="operator1",
            device_id="esp32_001",
            command="motor_start",
            status="executed",
            parameters={"speed": 50}
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'control_command'
        assert entry['severity'] == 'INFO'
        assert entry['user'] == 'operator1'
        assert entry['device_id'] == 'esp32_001'
        assert entry['command'] == 'motor_start'
        assert entry['status'] == 'executed'
        assert entry['parameters']['speed'] == 50
    
    def test_log_control_command_blocked(self):
        """Test logging blocked control command"""
        self.logger.log_control_command(
            user="operator1",
            device_id="esp32_001",
            command="motor_start",
            status="blocked",
            reason="safety_interlock_active"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'control_command'
        assert entry['severity'] == 'WARNING'
        assert entry['status'] == 'blocked'
        assert entry['reason'] == 'safety_interlock_active'
    
    def test_log_configuration_change(self):
        """Test logging configuration change"""
        self.logger.log_configuration_change(
            user="admin1",
            parameter="AI_LAYER_TIMEOUT",
            old_value="5",
            new_value="10",
            reason="network_latency_adjustment"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry['event_type'] == 'configuration_change'
        assert entry['severity'] == 'INFO'
        assert entry['user'] == 'admin1'
        assert entry['parameter'] == 'AI_LAYER_TIMEOUT'
        assert entry['old_value'] == '5'
        assert entry['new_value'] == '10'
    
    def test_log_multiple_events(self):
        """Test logging multiple events"""
        self.logger.log_authentication_success(user="user1", source_ip="192.168.1.1")
        self.logger.log_authentication_failure(attempted_user="user2", source_ip="192.168.1.2")
        self.logger.log_control_command(
            user="user1",
            device_id="esp32_001",
            command="test",
            status="executed"
        )
        
        entries = self.read_log_entries()
        assert len(entries) == 3
        
        # Verify order is preserved
        assert entries[0]['event_type'] == 'authentication'
        assert entries[0]['action'] == 'login_success'
        assert entries[1]['event_type'] == 'authentication'
        assert entries[1]['action'] == 'login_failed'
        assert entries[2]['event_type'] == 'control_command'
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format"""
        self.logger.log_authentication_success(user="test_user")
        
        entries = self.read_log_entries()
        assert len(entries) == 1
        
        timestamp = entries[0]['timestamp']
        # Should be in ISO format with timezone info
        assert 'T' in timestamp
        # Should have timezone info (either Z or +00:00 or similar)
        assert (timestamp.endswith('Z') or '+' in timestamp or timestamp.endswith('+00:00'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
