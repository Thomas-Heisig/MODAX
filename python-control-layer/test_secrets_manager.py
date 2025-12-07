"""Tests for secrets manager"""
import os
import pytest
from secrets_manager import SecretsManager


class TestSecretsManager:
    """Tests for SecretsManager"""
    
    def setup_method(self):
        """Set up test environment"""
        # Save original environment
        self.original_env = {
            'MQTT_USERNAME': os.getenv('MQTT_USERNAME'),
            'MQTT_PASSWORD': os.getenv('MQTT_PASSWORD'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'HMI_API_KEY': os.getenv('HMI_API_KEY'),
            'USE_VAULT': os.getenv('USE_VAULT')
        }
        
        # Set test values
        os.environ['MQTT_USERNAME'] = 'test_mqtt_user'
        os.environ['MQTT_PASSWORD'] = 'test_mqtt_pass'
        os.environ['DB_PASSWORD'] = 'test_db_pass'
        os.environ['HMI_API_KEY'] = 'test_hmi_key'
        os.environ['USE_VAULT'] = 'false'
    
    def teardown_method(self):
        """Restore original environment"""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    def test_initialization_without_vault(self):
        """Test initialization without Vault"""
        manager = SecretsManager(use_vault=False)
        assert manager.use_vault is False
        assert manager.vault_client is None
    
    def test_get_secret_from_env(self):
        """Test getting secret from environment variable"""
        manager = SecretsManager(use_vault=False)
        
        value = manager.get_secret('MQTT_USERNAME')
        assert value == 'test_mqtt_user'
    
    def test_get_secret_with_default(self):
        """Test getting secret with default value"""
        manager = SecretsManager(use_vault=False)
        
        value = manager.get_secret('NON_EXISTENT_KEY', 'default_value')
        assert value == 'default_value'
    
    def test_get_secret_not_found(self):
        """Test getting non-existent secret without default"""
        manager = SecretsManager(use_vault=False)
        
        value = manager.get_secret('NON_EXISTENT_KEY')
        assert value is None
    
    def test_get_mqtt_credentials(self):
        """Test getting MQTT credentials"""
        manager = SecretsManager(use_vault=False)
        
        creds = manager.get_mqtt_credentials()
        assert creds['username'] == 'test_mqtt_user'
        assert creds['password'] == 'test_mqtt_pass'
    
    def test_get_mqtt_tls_config(self):
        """Test getting MQTT TLS configuration"""
        os.environ['MQTT_CA_CERTS'] = '/path/to/ca.crt'
        os.environ['MQTT_CERTFILE'] = '/path/to/cert.crt'
        os.environ['MQTT_KEYFILE'] = '/path/to/key.key'
        
        manager = SecretsManager(use_vault=False)
        
        tls_config = manager.get_mqtt_tls_config()
        assert tls_config['ca_certs'] == '/path/to/ca.crt'
        assert tls_config['certfile'] == '/path/to/cert.crt'
        assert tls_config['keyfile'] == '/path/to/key.key'
        
        # Clean up
        del os.environ['MQTT_CA_CERTS']
        del os.environ['MQTT_CERTFILE']
        del os.environ['MQTT_KEYFILE']
    
    def test_get_api_keys(self):
        """Test getting API keys"""
        os.environ['MONITORING_API_KEY'] = 'test_monitoring_key'
        os.environ['ADMIN_API_KEY'] = 'test_admin_key'
        
        manager = SecretsManager(use_vault=False)
        
        api_keys = manager.get_api_keys()
        assert api_keys['hmi'] == 'test_hmi_key'
        assert api_keys['monitoring'] == 'test_monitoring_key'
        assert api_keys['admin'] == 'test_admin_key'
        
        # Clean up
        del os.environ['MONITORING_API_KEY']
        del os.environ['ADMIN_API_KEY']
    
    def test_get_database_credentials(self):
        """Test getting database credentials"""
        os.environ['DB_HOST'] = 'test_host'
        os.environ['DB_PORT'] = '5433'
        os.environ['DB_NAME'] = 'test_db'
        os.environ['DB_USER'] = 'test_user'
        
        manager = SecretsManager(use_vault=False)
        
        db_creds = manager.get_database_credentials()
        assert db_creds['host'] == 'test_host'
        assert db_creds['port'] == '5433'
        assert db_creds['database'] == 'test_db'
        assert db_creds['user'] == 'test_user'
        assert db_creds['password'] == 'test_db_pass'
        
        # Clean up
        del os.environ['DB_HOST']
        del os.environ['DB_PORT']
        del os.environ['DB_NAME']
        del os.environ['DB_USER']
    
    def test_get_database_credentials_defaults(self):
        """Test getting database credentials with defaults"""
        # Remove optional environment variables
        for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']:
            os.environ.pop(key, None)
        
        manager = SecretsManager(use_vault=False)
        
        db_creds = manager.get_database_credentials()
        assert db_creds['host'] == 'localhost'
        assert db_creds['port'] == '5432'
        assert db_creds['database'] == 'modax'
        assert db_creds['user'] == 'modax_user'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
