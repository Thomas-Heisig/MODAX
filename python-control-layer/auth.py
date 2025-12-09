"""Authentication and authorization for API endpoints with Multi-Tenant and RBAC support"""
import logging
import os
from typing import Dict, Optional, List, Set
from enum import Enum
from dataclasses import dataclass
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API Key header name
API_KEY_HEADER = "X-API-Key"
TENANT_HEADER = "X-Tenant-ID"
api_key_header_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
tenant_header_scheme = APIKeyHeader(name=TENANT_HEADER, auto_error=False)


class Role(str, Enum):
    """System roles with hierarchical permissions"""
    ADMIN = "admin"
    OPERATOR = "operator"
    MAINTENANCE = "maintenance"
    READ_ONLY = "read_only"


class Permission(str, Enum):
    """Fine-grained permissions"""
    READ = "read"
    WRITE = "write"
    CONTROL = "control"
    ADMIN = "admin"
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    AI_MODELS = "ai_models"
    AUDIT_LOGS = "audit_logs"


# Role to Permission mapping (hierarchical)
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.READ, Permission.WRITE, Permission.CONTROL,
        Permission.ADMIN, Permission.SYSTEM_CONFIG, Permission.USER_MANAGEMENT,
        Permission.AI_MODELS, Permission.AUDIT_LOGS
    },
    Role.OPERATOR: {
        Permission.READ, Permission.WRITE, Permission.CONTROL
    },
    Role.MAINTENANCE: {
        Permission.READ, Permission.AI_MODELS
    },
    Role.READ_ONLY: {
        Permission.READ
    }
}


@dataclass
class Tenant:
    """Represents a tenant in the multi-tenant system"""
    id: str
    name: str
    devices: List[str]  # List of device IDs accessible to this tenant
    max_devices: int
    enabled: bool = True


@dataclass
class UserContext:
    """User context with tenant and role information"""
    api_key: str
    name: str
    tenant_id: str
    role: Role
    permissions: Set[Permission]
    rate_limit: int


class APIKeyManager:
    """Manages API keys, permissions, and multi-tenant access"""

    def __init__(self):
        """Initialize API key manager with keys and tenants from environment"""
        self.api_keys: Dict[str, UserContext] = {}
        self.tenants: Dict[str, Tenant] = {}
        self._load_tenants()
        self._load_api_keys()

    def _load_tenants(self):
        """Load tenant configurations"""
        # Default tenant for backwards compatibility
        self.tenants["default"] = Tenant(
            id="default",
            name="Default Tenant",
            devices=["*"],  # Access to all devices
            max_devices=100,
            enabled=True
        )
        
        # Load additional tenants from environment
        # Format: TENANT_<ID>=name:max_devices:device1,device2
        for key, value in os.environ.items():
            if key.startswith("TENANT_"):
                tenant_id = key.replace("TENANT_", "").lower()
                parts = value.split(":")
                if len(parts) >= 2:
                    name = parts[0]
                    max_devices = int(parts[1])
                    devices = parts[2].split(",") if len(parts) > 2 else []
                    self.tenants[tenant_id] = Tenant(
                        id=tenant_id,
                        name=name,
                        devices=devices,
                        max_devices=max_devices,
                        enabled=True
                    )
        
        logger.info(f"Loaded {len(self.tenants)} tenants")

    def _load_api_keys(self):
        """Load API keys from environment variables with RBAC and tenant support"""
        # HMI client key - Operator role
        hmi_key = os.getenv("HMI_API_KEY")
        if hmi_key:
            self.api_keys[hmi_key] = UserContext(
                api_key=hmi_key,
                name="hmi-client",
                tenant_id="default",
                role=Role.OPERATOR,
                permissions=ROLE_PERMISSIONS[Role.OPERATOR],
                rate_limit=100
            )

        # Monitoring read-only key
        monitoring_key = os.getenv("MONITORING_API_KEY")
        if monitoring_key:
            self.api_keys[monitoring_key] = UserContext(
                api_key=monitoring_key,
                name="monitoring",
                tenant_id="default",
                role=Role.READ_ONLY,
                permissions=ROLE_PERMISSIONS[Role.READ_ONLY],
                rate_limit=1000
            )

        # Admin key with full access
        admin_key = os.getenv("ADMIN_API_KEY")
        if admin_key:
            self.api_keys[admin_key] = UserContext(
                api_key=admin_key,
                name="admin",
                tenant_id="default",
                role=Role.ADMIN,
                permissions=ROLE_PERMISSIONS[Role.ADMIN],
                rate_limit=1000
            )

        logger.info(f"Loaded {len(self.api_keys)} API keys")

    def validate_key(self, api_key: str) -> Optional[UserContext]:
        """Validate an API key and return its user context"""
        return self.api_keys.get(api_key)

    def has_permission(self, api_key: str, permission: Permission) -> bool:
        """Check if an API key has a specific permission"""
        user_context = self.validate_key(api_key)
        if not user_context:
            return False
        return permission in user_context.permissions
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)
    
    def validate_device_access(self, user_context: UserContext, device_id: str) -> bool:
        """Check if a user has access to a specific device based on tenant"""
        tenant = self.get_tenant(user_context.tenant_id)
        if not tenant or not tenant.enabled:
            return False
        
        # Admin can access all devices
        if user_context.role == Role.ADMIN:
            return True
        
        # Check if device is in tenant's allowed devices
        if "*" in tenant.devices:  # Wildcard access
            return True
        
        return device_id in tenant.devices


# Global API key manager instance
api_key_manager = APIKeyManager()


async def get_user_context(
    api_key: str = Security(api_key_header_scheme),
    tenant_id: Optional[str] = Security(tenant_header_scheme)
) -> UserContext:
    """
    Dependency to validate API key and get user context with tenant information
    
    Args:
        api_key: API key from X-API-Key header
        tenant_id: Optional tenant ID from X-Tenant-ID header
        
    Returns:
        UserContext with user and tenant information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    user_context = api_key_manager.validate_key(api_key)
    if not user_context:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Override tenant if provided and user is admin
    if tenant_id and user_context.role == Role.ADMIN:
        tenant = api_key_manager.get_tenant(tenant_id)
        if tenant:
            # Create a new context with overridden tenant
            user_context = UserContext(
                api_key=user_context.api_key,
                name=user_context.name,
                tenant_id=tenant_id,
                role=user_context.role,
                permissions=user_context.permissions,
                rate_limit=user_context.rate_limit
            )

    logger.debug(f"User authenticated: {user_context.name} (tenant: {user_context.tenant_id})")
    return user_context


async def get_api_key(api_key: str = Security(api_key_header_scheme)) -> str:
    """
    Dependency to validate API key (backwards compatible)
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        The validated API key string
        
    Raises:
        HTTPException: If authentication fails
    """
    user_context = await get_user_context(api_key)
    return user_context.api_key


async def require_permission(permission: Permission):
    """Dependency factory to require specific permission"""
    async def check_permission(user_context: UserContext = Security(get_user_context)) -> UserContext:
        """
        Check if the user has the required permission
        
        Args:
            user_context: The user context to check
            
        Returns:
            The validated user context
            
        Raises:
            HTTPException: If the user doesn't have the required permission
        """
        if permission not in user_context.permissions:
            logger.warning(
                f"Permission denied: {user_context.name} (role: {user_context.role}) "
                f"attempted '{permission.value}' without access"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission.value}' required"
            )
        return user_context
    return check_permission


async def require_device_access(device_id: str):
    """Dependency factory to require device access based on tenant"""
    async def check_device_access(user_context: UserContext = Security(get_user_context)) -> UserContext:
        """
        Check if the user has access to a specific device
        
        Args:
            user_context: The user context to check
            
        Returns:
            The validated user context
            
        Raises:
            HTTPException: If the user doesn't have access to the device
        """
        if not api_key_manager.validate_device_access(user_context, device_id):
            logger.warning(
                f"Device access denied: {user_context.name} (tenant: {user_context.tenant_id}) "
                f"attempted to access device '{device_id}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Device '{device_id}' not accessible to tenant '{user_context.tenant_id}'"
            )
        return user_context
    return check_device_access


# Pre-defined permission dependencies
require_read = require_permission(Permission.READ)
require_write = require_permission(Permission.WRITE)
require_control = require_permission(Permission.CONTROL)
require_admin = require_permission(Permission.ADMIN)
require_system_config = require_permission(Permission.SYSTEM_CONFIG)
require_user_management = require_permission(Permission.USER_MANAGEMENT)
