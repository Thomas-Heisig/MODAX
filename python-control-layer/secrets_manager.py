"""Secrets management for MODAX Control Layer"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secrets with support for environment variables and Vault"""

    def __init__(self, use_vault: bool = False):
        """
        Initialize secrets manager

        Args:
            use_vault: Whether to use HashiCorp Vault for secrets
        """
        self.use_vault = use_vault
        self.vault_client = None

        if use_vault:
            self._initialize_vault()

    def _initialize_vault(self):
        """Initialize HashiCorp Vault client"""
        try:
            import hvac

            vault_addr = os.getenv('VAULT_ADDR')
            vault_token = os.getenv('VAULT_TOKEN')

            if not vault_addr or not vault_token:
                logger.warning(
                    "Vault is enabled but VAULT_ADDR or VAULT_TOKEN is not set. "
                    "Falling back to environment variables."
                )
                self.use_vault = False
                return

            self.vault_client = hvac.Client(
                url=vault_addr,
                token=vault_token
            )

            if not self.vault_client.is_authenticated():
                logger.error("Failed to authenticate with Vault")
                self.use_vault = False
            else:
                logger.info("Successfully connected to HashiCorp Vault")

        except ImportError:
            logger.warning(
                "hvac package not installed. Install with: pip install hvac. "
                "Falling back to environment variables."
            )
            self.use_vault = False
        except Exception as e:
            logger.error(f"Failed to initialize Vault: {e}")
            self.use_vault = False

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value

        Args:
            key: Secret key name
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        if self.use_vault and self.vault_client:
            return self._get_vault_secret(key, default)
        else:
            return self._get_env_secret(key, default)

    def _get_env_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable"""
        value = os.getenv(key, default)
        if value is None:
            logger.warning(f"Secret '{key}' not found in environment variables")
        return value

    def _get_vault_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        try:
            # Secrets are stored in KV v2 secret engine at path 'modax/secrets'
            secret_path = f"modax/secrets"
            secret = self.vault_client.secrets.kv.v2.read_secret_version(
                path=secret_path
            )

            value = secret['data']['data'].get(key)
            if value is None:
                logger.warning(f"Secret '{key}' not found in Vault")
                return default

            return value

        except Exception as e:
            logger.error(f"Failed to retrieve secret '{key}' from Vault: {e}")
            return default

    def get_mqtt_credentials(self) -> Dict[str, Optional[str]]:
        """Get MQTT credentials"""
        return {
            'username': self.get_secret('MQTT_USERNAME'),
            'password': self.get_secret('MQTT_PASSWORD')
        }

    def get_mqtt_tls_config(self) -> Dict[str, Optional[str]]:
        """Get MQTT TLS configuration"""
        return {
            'ca_certs': self.get_secret('MQTT_CA_CERTS'),
            'certfile': self.get_secret('MQTT_CERTFILE'),
            'keyfile': self.get_secret('MQTT_KEYFILE')
        }

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys for authentication"""
        return {
            'hmi': self.get_secret('HMI_API_KEY'),
            'monitoring': self.get_secret('MONITORING_API_KEY'),
            'admin': self.get_secret('ADMIN_API_KEY')
        }

    def get_database_credentials(self) -> Dict[str, Optional[str]]:
        """Get database credentials"""
        return {
            'host': self.get_secret('DB_HOST', 'localhost'),
            'port': self.get_secret('DB_PORT', '5432'),
            'database': self.get_secret('DB_NAME', 'modax'),
            'user': self.get_secret('DB_USER', 'modax_user'),
            'password': self.get_secret('DB_PASSWORD')
        }


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager"""
    global _secrets_manager
    if _secrets_manager is None:
        use_vault = os.getenv('USE_VAULT', 'false').lower() == 'true'
        _secrets_manager = SecretsManager(use_vault=use_vault)
    return _secrets_manager


def set_secrets_manager(secrets_manager: SecretsManager):
    """Set a custom secrets manager (for testing)"""
    global _secrets_manager
    _secrets_manager = secrets_manager
