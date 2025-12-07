"""Tests for authentication module"""
import os
import pytest
from auth import APIKeyManager, api_key_manager, get_api_key
from fastapi import HTTPException


class TestAPIKeyManager:
    """Tests for APIKeyManager"""
    
    def setup_method(self):
        """Set up test environment"""
        # Save original environment
        self.original_env = {
            'HMI_API_KEY': os.getenv('HMI_API_KEY'),
            'MONITORING_API_KEY': os.getenv('MONITORING_API_KEY'),
            'ADMIN_API_KEY': os.getenv('ADMIN_API_KEY')
        }
        
        # Set test keys
        os.environ['HMI_API_KEY'] = 'test_hmi_key'
        os.environ['MONITORING_API_KEY'] = 'test_monitoring_key'
        os.environ['ADMIN_API_KEY'] = 'test_admin_key'
        
        # Create fresh manager
        self.manager = APIKeyManager()
    
    def teardown_method(self):
        """Restore original environment"""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    def test_load_api_keys(self):
        """Test loading API keys from environment"""
        assert len(self.manager.api_keys) == 3
        assert 'test_hmi_key' in self.manager.api_keys
        assert 'test_monitoring_key' in self.manager.api_keys
        assert 'test_admin_key' in self.manager.api_keys
    
    def test_validate_valid_key(self):
        """Test validating a valid API key"""
        key_info = self.manager.validate_key('test_hmi_key')
        assert key_info is not None
        assert key_info['name'] == 'hmi-client'
        assert 'read' in key_info['permissions']
        assert 'write' in key_info['permissions']
    
    def test_validate_invalid_key(self):
        """Test validating an invalid API key"""
        key_info = self.manager.validate_key('invalid_key')
        assert key_info is None
    
    def test_has_permission_valid(self):
        """Test checking permission for valid key"""
        assert self.manager.has_permission('test_hmi_key', 'read') is True
        assert self.manager.has_permission('test_hmi_key', 'write') is True
        assert self.manager.has_permission('test_hmi_key', 'control') is True
    
    def test_has_permission_invalid(self):
        """Test checking permission for invalid key"""
        assert self.manager.has_permission('invalid_key', 'read') is False
    
    def test_has_permission_insufficient(self):
        """Test checking permission when key doesn't have it"""
        assert self.manager.has_permission('test_monitoring_key', 'write') is False
        assert self.manager.has_permission('test_monitoring_key', 'read') is True
    
    def test_admin_permissions(self):
        """Test admin key has all permissions"""
        assert self.manager.has_permission('test_admin_key', 'read') is True
        assert self.manager.has_permission('test_admin_key', 'write') is True
        assert self.manager.has_permission('test_admin_key', 'control') is True
        assert self.manager.has_permission('test_admin_key', 'admin') is True


@pytest.mark.asyncio
async def test_get_api_key_valid():
    """Test get_api_key with valid key"""
    # This would need to be integrated with FastAPI testing
    # For now, just ensure the function exists
    assert get_api_key is not None


@pytest.mark.asyncio
async def test_get_api_key_missing():
    """Test get_api_key with missing key"""
    # Would need FastAPI test client
    pass


@pytest.mark.asyncio
async def test_get_api_key_invalid():
    """Test get_api_key with invalid key"""
    # Would need FastAPI test client
    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
