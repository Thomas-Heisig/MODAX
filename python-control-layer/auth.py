"""Authentication and authorization for API endpoints"""
import logging
import os
from typing import Dict, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API Key header name
API_KEY_HEADER = "X-API-Key"
api_key_header_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


class APIKeyManager:
    """Manages API keys and permissions"""

    def __init__(self):
        """Initialize API key manager with keys from environment"""
        self.api_keys: Dict[str, Dict] = {}
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment variables"""
        # HMI client key
        hmi_key = os.getenv("HMI_API_KEY")
        if hmi_key:
            self.api_keys[hmi_key] = {
                "name": "hmi-client",
                "permissions": ["read", "write", "control"],
                "rate_limit": 100
            }

        # Monitoring read-only key
        monitoring_key = os.getenv("MONITORING_API_KEY")
        if monitoring_key:
            self.api_keys[monitoring_key] = {
                "name": "monitoring",
                "permissions": ["read"],
                "rate_limit": 1000
            }

        # Admin key with full access
        admin_key = os.getenv("ADMIN_API_KEY")
        if admin_key:
            self.api_keys[admin_key] = {
                "name": "admin",
                "permissions": ["read", "write", "control", "admin"],
                "rate_limit": 1000
            }

        logger.info(f"Loaded {len(self.api_keys)} API keys")

    def validate_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return its info"""
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        return None

    def has_permission(self, api_key: str, permission: str) -> bool:
        """Check if an API key has a specific permission"""
        key_info = self.validate_key(api_key)
        if not key_info:
            return False
        return permission in key_info.get("permissions", [])


# Global API key manager instance
api_key_manager = APIKeyManager()


async def get_api_key(api_key: str = Security(api_key_header_scheme)) -> str:
    """Dependency to validate API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_info = api_key_manager.validate_key(api_key)
    if not key_info:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug(f"API key validated: {key_info['name']}")
    return api_key


async def require_permission(permission: str):
    """Dependency factory to require specific permission"""
    async def check_permission(api_key: str = Security(get_api_key)) -> str:
        """
        Check if the API key has the required permission
        
        Args:
            api_key: The API key to check
            
        Returns:
            The validated API key
            
        Raises:
            HTTPException: If the API key doesn't have the required permission
        """
        if not api_key_manager.has_permission(api_key, permission):
            key_info = api_key_manager.validate_key(api_key)
            logger.warning(
                f"Permission denied: {key_info['name']} "
                f"attempted '{permission}' without access"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission}' required"
            )
        return api_key
    return check_permission


# Pre-defined permission dependencies
require_read = require_permission("read")
require_write = require_permission("write")
require_control = require_permission("control")
require_admin = require_permission("admin")
