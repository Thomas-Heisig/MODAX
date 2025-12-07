"""Security audit logging for MODAX Control Layer"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityAuditLogger:
    """Handles security audit logging for authentication, authorization, and control events"""
    
    # Event type constants
    EVENT_AUTH = "authentication"
    EVENT_AUTHZ = "authorization"
    EVENT_CONTROL = "control_command"
    EVENT_CONFIG = "configuration_change"
    
    # Severity levels
    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"
    SEVERITY_CRITICAL = "CRITICAL"
    
    def __init__(self, audit_log_path: Optional[str] = None):
        """
        Initialize security audit logger
        
        Args:
            audit_log_path: Path to audit log file. If None, uses default location.
        """
        if audit_log_path is None:
            audit_log_path = "/var/log/modax/security_audit.log"
        
        self.audit_log_path = Path(audit_log_path)
        
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up file handler for audit logs
        self.audit_handler = logging.FileHandler(self.audit_log_path)
        self.audit_handler.setLevel(logging.INFO)
        
        # Use JSON format for structured logging
        formatter = logging.Formatter('%(message)s')
        self.audit_handler.setFormatter(formatter)
        
        # Create separate logger for audit events
        self.audit_logger = logging.getLogger("modax.security.audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(self.audit_handler)
        self.audit_logger.propagate = False
    
    def _log_event(self, event_type: str, severity: str, **kwargs):
        """Log a security audit event"""
        event = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "event_type": event_type,
            "severity": severity,
            **kwargs
        }
        
        self.audit_logger.info(json.dumps(event))
    
    def log_authentication_success(
        self,
        user: str,
        source_ip: Optional[str] = None,
        method: str = "api_key",
        user_agent: Optional[str] = None
    ):
        """Log successful authentication"""
        self._log_event(
            self.EVENT_AUTH,
            self.SEVERITY_INFO,
            action="login_success",
            user=user,
            source_ip=source_ip,
            metadata={
                "method": method,
                "user_agent": user_agent
            }
        )
    
    def log_authentication_failure(
        self,
        attempted_user: str,
        source_ip: Optional[str] = None,
        reason: str = "invalid_credentials"
    ):
        """Log failed authentication attempt"""
        self._log_event(
            self.EVENT_AUTH,
            self.SEVERITY_WARNING,
            action="login_failed",
            attempted_user=attempted_user,
            source_ip=source_ip,
            reason=reason
        )
    
    def log_authorization_denied(
        self,
        user: str,
        resource: str,
        action: str,
        reason: str = "insufficient_permissions"
    ):
        """Log authorization denial"""
        self._log_event(
            self.EVENT_AUTHZ,
            self.SEVERITY_WARNING,
            action="access_denied",
            user=user,
            resource=resource,
            requested_action=action,
            reason=reason
        )
    
    def log_control_command(
        self,
        user: str,
        device_id: str,
        command: str,
        status: str,
        parameters: Optional[Dict] = None,
        reason: Optional[str] = None
    ):
        """Log control command execution or blocking"""
        severity = self.SEVERITY_WARNING if status == "blocked" else self.SEVERITY_INFO
        
        self._log_event(
            self.EVENT_CONTROL,
            severity,
            user=user,
            device_id=device_id,
            command=command,
            status=status,
            parameters=parameters,
            reason=reason
        )
    
    def log_configuration_change(
        self,
        user: str,
        parameter: str,
        old_value: str,
        new_value: str,
        reason: Optional[str] = None
    ):
        """Log configuration change"""
        self._log_event(
            self.EVENT_CONFIG,
            self.SEVERITY_INFO,
            user=user,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        **kwargs
    ):
        """Log a custom security event"""
        self._log_event(
            event_type,
            severity,
            description=description,
            **kwargs
        )


# Global security audit logger instance
_audit_logger: Optional[SecurityAuditLogger] = None


def get_security_audit_logger() -> SecurityAuditLogger:
    """Get or create the global security audit logger"""
    global _audit_logger
    if _audit_logger is None:
        # In development, use local directory
        import os
        if os.getenv("ENVIRONMENT", "development") == "development":
            audit_path = "./logs/security_audit.log"
        else:
            audit_path = None  # Use default production path
        
        _audit_logger = SecurityAuditLogger(audit_path)
    return _audit_logger


def set_security_audit_logger(audit_logger: SecurityAuditLogger):
    """Set a custom security audit logger (for testing)"""
    global _audit_logger
    _audit_logger = audit_logger
