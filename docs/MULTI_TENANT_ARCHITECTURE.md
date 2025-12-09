# Multi-Tenant Architecture

**Last Updated:** 2025-12-09  
**Status:** Implemented  
**Version:** 1.0

## Overview

MODAX supports multi-tenancy to enable a single deployment to serve multiple organizations (tenants) with complete data isolation, customization, and access control. This architecture is essential for SaaS deployments and managed service providers.

## Multi-Tenancy Model

### Tenant Isolation Strategy

MODAX uses a **hybrid multi-tenancy model** combining:
- **Shared Infrastructure:** Common backend services and database
- **Logical Isolation:** Tenant-based data partitioning
- **Resource Quotas:** Per-tenant resource limits

```
┌─────────────────────────────────────────────────────────┐
│                  MODAX Platform                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Tenant A    │  │  Tenant B    │  │  Tenant C    │  │
│  │              │  │              │  │              │  │
│  │ Device 1,2,3 │  │ Device 4,5   │  │ Device 6,7,8 │  │
│  │ Users: 10    │  │ Users: 5     │  │ Users: 15    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                  │           │
│  ┌──────▼─────────────────▼──────────────────▼──────┐   │
│  │           Authentication & Authorization          │   │
│  │              (RBAC + Tenant Context)              │   │
│  └───────────────────────┬───────────────────────────┘   │
│                          │                                │
│  ┌───────────────────────▼───────────────────────────┐   │
│  │            Shared Application Services            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │  │ Control  │  │    AI    │  │    MQTT      │   │   │
│  │  │  Layer   │  │  Layer   │  │   Broker     │   │   │
│  │  └──────────┘  └──────────┘  └──────────────┘   │   │
│  └───────────────────────┬───────────────────────────┘   │
│                          │                                │
│  ┌───────────────────────▼───────────────────────────┐   │
│  │         Database with Tenant Partitioning         │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │ Tenant A Data │ Tenant B Data │ Tenant C │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### Tenant Data Model

```python
# python-control-layer/models/tenant.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Tenant:
    """Represents a tenant in the multi-tenant system"""
    id: str                    # Unique tenant identifier
    name: str                  # Display name
    devices: List[str]         # List of device IDs
    max_devices: int           # Device quota
    max_users: int             # User quota
    enabled: bool              # Tenant active status
    created_at: datetime
    features: List[str]        # Enabled features
    settings: dict             # Tenant-specific settings
    
    # Resource limits
    api_rate_limit: int        # Requests per minute
    storage_quota_gb: int      # Storage limit
    retention_days: int        # Data retention period
    
    # Billing information (optional)
    subscription_tier: str     # free, basic, professional, enterprise
    billing_contact: Optional[str]


@dataclass
class TenantUser:
    """User belonging to a tenant"""
    user_id: str
    tenant_id: str
    email: str
    role: str                  # admin, operator, maintenance, read_only
    api_key: str
    created_at: datetime
    last_login: Optional[datetime]
    enabled: bool
```

### Database Schema

#### Tenant Partitioning

All tables include `tenant_id` as the first column of composite primary keys:

```sql
-- Tenant table
CREATE TABLE tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    max_devices INTEGER DEFAULT 10,
    max_users INTEGER DEFAULT 5,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb,
    api_rate_limit INTEGER DEFAULT 100,
    storage_quota_gb INTEGER DEFAULT 10,
    retention_days INTEGER DEFAULT 90,
    subscription_tier VARCHAR(32) DEFAULT 'basic'
);

-- Tenant users
CREATE TABLE tenant_users (
    user_id VARCHAR(64),
    tenant_id VARCHAR(64) REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL,
    api_key VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (tenant_id, user_id)
);

-- Devices with tenant isolation
CREATE TABLE devices (
    device_id VARCHAR(64),
    tenant_id VARCHAR(64) REFERENCES tenants(id),
    name VARCHAR(255),
    device_type VARCHAR(32),
    location VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    status VARCHAR(32),
    PRIMARY KEY (tenant_id, device_id)
);

-- Sensor data with tenant partitioning
CREATE TABLE sensor_data (
    tenant_id VARCHAR(64) REFERENCES tenants(id),
    device_id VARCHAR(64),
    timestamp TIMESTAMPTZ NOT NULL,
    current_mean DOUBLE PRECISION,
    vibration_x_mean DOUBLE PRECISION,
    vibration_y_mean DOUBLE PRECISION,
    vibration_z_mean DOUBLE PRECISION,
    temperature_mean DOUBLE PRECISION,
    PRIMARY KEY (tenant_id, device_id, timestamp),
    FOREIGN KEY (tenant_id, device_id) REFERENCES devices(tenant_id, device_id)
);

-- Create indexes for efficient tenant queries
CREATE INDEX idx_sensor_data_tenant_device_time 
ON sensor_data (tenant_id, device_id, timestamp DESC);

CREATE INDEX idx_devices_tenant 
ON devices (tenant_id) WHERE enabled = TRUE;
```

### Authentication & Authorization

#### Enhanced RBAC with Tenant Context

The enhanced `auth.py` (already implemented) provides:

```python
from auth import UserContext, get_user_context, require_device_access

# Example usage in API endpoints
@router.get("/devices/{device_id}/data")
async def get_device_data(
    device_id: str,
    user_context: UserContext = Depends(require_device_access(device_id))
):
    """
    Get device data with tenant isolation
    
    - Automatically validates tenant access
    - User can only access devices in their tenant
    - Admin can override tenant with X-Tenant-ID header
    """
    # Query with tenant_id ensures data isolation
    data = await db.query_device_data(
        tenant_id=user_context.tenant_id,
        device_id=device_id
    )
    return data
```

#### API Key Format

```
Format: {tenant_id}.{user_id}.{random_secret}
Example: acme_corp.user123.a1b2c3d4e5f6...

Benefits:
- Self-describing (contains tenant and user info)
- Enables quick tenant routing
- Maintains security with secret component
```

### Request Flow

```
1. Client Request
   ├─ X-API-Key: acme_corp.user123.secret
   └─ X-Tenant-ID: acme_corp (optional override for admin)
   
2. Authentication Middleware
   ├─ Extract tenant_id from API key
   ├─ Validate API key against database
   ├─ Load UserContext with tenant info
   └─ Check tenant is enabled
   
3. Authorization Middleware
   ├─ Verify user has required permission
   └─ Validate device access for tenant
   
4. Business Logic
   ├─ Query data with tenant_id filter
   ├─ Apply tenant-specific settings
   └─ Enforce tenant quotas
   
5. Response
   └─ Return tenant-scoped data
```

## Tenant Management

### Admin API Endpoints

```python
# Tenant CRUD operations (admin only)

@router.post("/admin/tenants")
async def create_tenant(
    tenant_data: TenantCreate,
    user: UserContext = Depends(require_admin)
) -> Tenant:
    """Create a new tenant"""
    pass

@router.get("/admin/tenants")
async def list_tenants(
    user: UserContext = Depends(require_admin)
) -> List[Tenant]:
    """List all tenants"""
    pass

@router.get("/admin/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    user: UserContext = Depends(require_admin)
) -> Tenant:
    """Get tenant details"""
    pass

@router.put("/admin/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    user: UserContext = Depends(require_admin)
) -> Tenant:
    """Update tenant configuration"""
    pass

@router.delete("/admin/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    user: UserContext = Depends(require_admin)
):
    """Soft delete a tenant"""
    pass

# User management within tenant
@router.post("/admin/tenants/{tenant_id}/users")
async def create_tenant_user(
    tenant_id: str,
    user_data: UserCreate,
    admin: UserContext = Depends(require_user_management)
) -> TenantUser:
    """Create a user for a tenant"""
    pass
```

### Tenant Provisioning Workflow

```python
# python-control-layer/tenant_provisioner.py
class TenantProvisioner:
    """Handles tenant provisioning and setup"""
    
    async def provision_tenant(
        self,
        name: str,
        admin_email: str,
        subscription_tier: str = "basic"
    ) -> Tenant:
        """
        Provision a new tenant with:
        1. Create tenant record
        2. Set up resource quotas
        3. Create admin user
        4. Initialize default settings
        5. Set up monitoring
        """
        # 1. Create tenant
        tenant = await self._create_tenant_record(name, subscription_tier)
        
        # 2. Apply tier-based quotas
        quotas = self._get_tier_quotas(subscription_tier)
        await self._apply_quotas(tenant.id, quotas)
        
        # 3. Create admin user
        admin_user = await self._create_admin_user(
            tenant.id,
            admin_email
        )
        
        # 4. Initialize settings
        await self._initialize_tenant_settings(tenant.id)
        
        # 5. Set up monitoring
        await self._setup_monitoring(tenant.id)
        
        logger.info(f"Tenant provisioned: {tenant.id}")
        return tenant
```

## Resource Isolation & Quotas

### Quota Enforcement

```python
# python-control-layer/quota_manager.py
class QuotaManager:
    """Enforce tenant resource quotas"""
    
    async def check_device_quota(self, tenant_id: str) -> bool:
        """Check if tenant can add more devices"""
        tenant = await self.get_tenant(tenant_id)
        device_count = await self.get_device_count(tenant_id)
        return device_count < tenant.max_devices
    
    async def check_storage_quota(self, tenant_id: str) -> bool:
        """Check if tenant has storage available"""
        tenant = await self.get_tenant(tenant_id)
        storage_used = await self.get_storage_used(tenant_id)
        return storage_used < tenant.storage_quota_gb * 1024**3
    
    async def check_api_rate_limit(
        self,
        tenant_id: str,
        user_id: str
    ) -> bool:
        """Check API rate limit (requests per minute)"""
        key = f"rate_limit:{tenant_id}:{user_id}"
        count = await redis.incr(key)
        
        if count == 1:
            await redis.expire(key, 60)  # 1 minute window
        
        tenant = await self.get_tenant(tenant_id)
        return count <= tenant.api_rate_limit
```

### Subscription Tiers

```python
TIER_QUOTAS = {
    "free": {
        "max_devices": 3,
        "max_users": 2,
        "storage_quota_gb": 1,
        "retention_days": 7,
        "api_rate_limit": 50,
        "features": ["basic_monitoring"]
    },
    "basic": {
        "max_devices": 10,
        "max_users": 5,
        "storage_quota_gb": 10,
        "retention_days": 30,
        "api_rate_limit": 100,
        "features": ["basic_monitoring", "ai_analysis", "alerts"]
    },
    "professional": {
        "max_devices": 50,
        "max_users": 25,
        "storage_quota_gb": 100,
        "retention_days": 90,
        "api_rate_limit": 500,
        "features": [
            "basic_monitoring", "ai_analysis", "alerts",
            "advanced_analytics", "custom_dashboards", "api_access"
        ]
    },
    "enterprise": {
        "max_devices": -1,  # Unlimited
        "max_users": -1,    # Unlimited
        "storage_quota_gb": -1,  # Unlimited
        "retention_days": 365,
        "api_rate_limit": 10000,
        "features": [
            "basic_monitoring", "ai_analysis", "alerts",
            "advanced_analytics", "custom_dashboards", "api_access",
            "sla", "dedicated_support", "custom_integrations",
            "on_premise_option"
        ]
    }
}
```

## Data Isolation & Security

### Query Isolation

All database queries must include tenant_id:

```python
# ✅ CORRECT: Tenant-scoped query
async def get_device_data(tenant_id: str, device_id: str):
    query = """
        SELECT * FROM sensor_data
        WHERE tenant_id = $1 AND device_id = $2
        ORDER BY timestamp DESC
        LIMIT 100
    """
    return await db.fetch(query, tenant_id, device_id)

# ❌ INCORRECT: Missing tenant_id (security vulnerability)
async def get_device_data(device_id: str):
    query = """
        SELECT * FROM sensor_data
        WHERE device_id = $1  -- Missing tenant_id!
        ORDER BY timestamp DESC
        LIMIT 100
    """
    return await db.fetch(query, device_id)
```

### MQTT Topic Isolation

Tenants are isolated at the MQTT broker level:

```
Topic Structure:
modax/{tenant_id}/{device_id}/{data_type}

Examples:
modax/acme_corp/esp32_001/sensor_data
modax/acme_corp/esp32_001/safety_status
modax/globex/esp32_099/sensor_data

ACL Rules:
- Users can only publish/subscribe to their tenant's topics
- Each tenant has separate credentials
- Broker enforces ACL at connection time
```

### API Isolation

```python
# All API responses are filtered by tenant
@router.get("/devices")
async def list_devices(
    user: UserContext = Depends(get_user_context)
):
    """List devices - automatically scoped to user's tenant"""
    devices = await db.query(
        "SELECT * FROM devices WHERE tenant_id = $1",
        user.tenant_id
    )
    return devices
```

## Tenant Customization

### Per-Tenant Configuration

```python
# Tenant-specific settings stored in JSONB column
tenant_settings = {
    "branding": {
        "logo_url": "https://acme.com/logo.png",
        "primary_color": "#FF6600",
        "company_name": "ACME Corp"
    },
    "notifications": {
        "email_enabled": True,
        "sms_enabled": False,
        "webhook_url": "https://acme.com/webhook"
    },
    "thresholds": {
        "temperature_warning": 60.0,
        "temperature_critical": 80.0,
        "current_warning": 8.0,
        "current_critical": 10.0
    },
    "locale": {
        "language": "de",
        "timezone": "Europe/Berlin",
        "date_format": "DD.MM.YYYY"
    }
}
```

### Feature Flags

```python
# python-control-layer/feature_flags.py
class FeatureFlagManager:
    """Manage per-tenant feature flags"""
    
    def is_feature_enabled(
        self,
        tenant_id: str,
        feature: str
    ) -> bool:
        """Check if feature is enabled for tenant"""
        tenant = self.get_tenant(tenant_id)
        return feature in tenant.features
    
    def require_feature(self, feature: str):
        """Dependency to require a feature"""
        async def check_feature(
            user: UserContext = Depends(get_user_context)
        ):
            if not self.is_feature_enabled(user.tenant_id, feature):
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature '{feature}' not available in your plan"
                )
            return user
        return check_feature

# Usage in API
@router.post("/devices/{device_id}/advanced-analysis")
async def advanced_analysis(
    device_id: str,
    user: UserContext = Depends(
        feature_flags.require_feature("advanced_analytics")
    )
):
    """Advanced analytics - only for Professional+ tiers"""
    pass
```

## Monitoring & Observability

### Per-Tenant Metrics

```python
# Prometheus metrics with tenant labels
from prometheus_client import Counter, Histogram, Gauge

# API requests per tenant
api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['tenant_id', 'endpoint', 'method', 'status']
)

# Storage usage per tenant
storage_usage = Gauge(
    'tenant_storage_bytes',
    'Storage used by tenant',
    ['tenant_id']
)

# Device count per tenant
device_count = Gauge(
    'tenant_devices_total',
    'Number of devices per tenant',
    ['tenant_id', 'status']
)
```

### Tenant Health Dashboard

Key metrics to monitor:
- Active devices per tenant
- API request rate per tenant
- Storage usage per tenant
- Error rate per tenant
- Average response time per tenant
- Quota utilization per tenant

## Migration & Tenant Onboarding

### Data Import

```python
# python-control-layer/tenant_migration.py
class TenantMigration:
    """Handle data migration for new tenants"""
    
    async def import_devices(
        self,
        tenant_id: str,
        devices_csv: str
    ):
        """Import devices from CSV"""
        devices = self._parse_csv(devices_csv)
        
        for device in devices:
            await self._create_device(
                tenant_id=tenant_id,
                device_id=device['id'],
                name=device['name'],
                device_type=device['type']
            )
    
    async def import_historical_data(
        self,
        tenant_id: str,
        data_file: str
    ):
        """Import historical sensor data"""
        # Batch insert with tenant_id
        await self._bulk_insert_sensor_data(tenant_id, data_file)
```

## Best Practices

### Development
1. **Always include tenant_id** in database queries
2. **Test with multiple tenants** to ensure isolation
3. **Use tenant context** from authentication
4. **Validate tenant access** before operations
5. **Log with tenant context** for debugging

### Security
1. **Never trust tenant_id from request body** - always use authenticated context
2. **Validate device ownership** before operations
3. **Implement row-level security** in database
4. **Audit cross-tenant access attempts**
5. **Rate limit per tenant** to prevent abuse

### Performance
1. **Index on tenant_id** for all multi-tenant tables
2. **Partition large tables** by tenant_id if needed
3. **Cache tenant settings** to reduce database load
4. **Monitor per-tenant query performance**
5. **Implement tenant-level circuit breakers**

## Testing Multi-Tenancy

### Test Scenarios

```python
# tests/test_multi_tenant.py
class TestMultiTenancy:
    """Test multi-tenant isolation"""
    
    async def test_tenant_isolation(self):
        """Verify users cannot access other tenant's data"""
        # Create two tenants
        tenant_a = await create_tenant("Tenant A")
        tenant_b = await create_tenant("Tenant B")
        
        # Create users for each
        user_a = await create_user(tenant_a.id, "user_a")
        user_b = await create_user(tenant_b.id, "user_b")
        
        # Create device for tenant A
        device_a = await create_device(tenant_a.id, "device_001")
        
        # User B should NOT be able to access device A
        with pytest.raises(HTTPException) as exc:
            await get_device_data(
                device_id=device_a.id,
                user=user_b
            )
        assert exc.value.status_code == 403
    
    async def test_quota_enforcement(self):
        """Verify quota limits are enforced"""
        tenant = await create_tenant("Test", max_devices=3)
        
        # Create 3 devices (should succeed)
        for i in range(3):
            await create_device(tenant.id, f"device_{i}")
        
        # 4th device should fail
        with pytest.raises(QuotaExceededError):
            await create_device(tenant.id, "device_4")
```

## Related Documentation

- [Authentication Implementation Guide](AUTHENTICATION_IMPLEMENTATION_GUIDE.md)
- [Security](SECURITY.md)
- [API Documentation](API.md)
- [RBAC Implementation](auth.py)
