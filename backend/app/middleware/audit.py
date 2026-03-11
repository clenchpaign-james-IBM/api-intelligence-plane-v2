"""
Audit Logging Middleware

Implements comprehensive audit logging for all API operations to meet
FedRAMP 140-3 compliance requirements.

Audit logs capture:
- User actions and API calls
- Authentication/authorization events
- Data access and modifications
- Security-relevant events
- System configuration changes
"""

import json
import logging
import time
from typing import Callable, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings

# Setup audit logger with separate handler
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False

# Create audit log handler
if settings.LOG_FILE:
    audit_handler = logging.FileHandler(
        settings.LOG_FILE.replace(".log", "_audit.log")
    )
else:
    audit_handler = logging.StreamHandler()

# Format audit logs as JSON
audit_formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"logger": "%(name)s", "message": %(message)s}'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)


class AuditEvent:
    """
    Structured audit event for compliance logging.
    """
    
    # Event categories
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    SYSTEM = "system"
    
    # Event outcomes
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    
    def __init__(
        self,
        event_id: str,
        category: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        self.event_id = event_id
        self.timestamp = datetime.utcnow().isoformat()
        self.category = category
        self.action = action
        self.outcome = outcome
        self.user_id = user_id or "anonymous"
        self.resource = resource
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert audit event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "category": self.category,
            "action": self.action,
            "outcome": self.outcome,
            "user_id": self.user_id,
            "resource": self.resource,
            "details": self.details,
        }
    
    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Centralized audit logging service.
    """
    
    @staticmethod
    def log_event(event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: AuditEvent to log
        """
        audit_logger.info(event.to_json())
    
    @staticmethod
    def log_authentication(
        user_id: str,
        outcome: str,
        method: str,
        ip_address: str,
        details: Optional[dict] = None,
    ):
        """Log authentication event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.AUTHENTICATION,
            action=f"authentication_{method}",
            outcome=outcome,
            user_id=user_id,
            details={
                "method": method,
                "ip_address": ip_address,
                **(details or {}),
            },
        )
        AuditLogger.log_event(event)
    
    @staticmethod
    def log_authorization(
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        details: Optional[dict] = None,
    ):
        """Log authorization event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.AUTHORIZATION,
            action=f"authorization_{action}",
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            details=details,
        )
        AuditLogger.log_event(event)
    
    @staticmethod
    def log_data_access(
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        details: Optional[dict] = None,
    ):
        """Log data access event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.DATA_ACCESS,
            action=action,
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            details=details,
        )
        AuditLogger.log_event(event)
    
    @staticmethod
    def log_data_modification(
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        details: Optional[dict] = None,
    ):
        """Log data modification event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.DATA_MODIFICATION,
            action=action,
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            details=details,
        )
        AuditLogger.log_event(event)
    
    @staticmethod
    def log_configuration_change(
        user_id: str,
        resource: str,
        action: str,
        outcome: str,
        details: Optional[dict] = None,
    ):
        """Log configuration change event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.CONFIGURATION,
            action=action,
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            details=details,
        )
        AuditLogger.log_event(event)
    
    @staticmethod
    def log_security_event(
        user_id: str,
        action: str,
        outcome: str,
        details: Optional[dict] = None,
    ):
        """Log security event."""
        event = AuditEvent(
            event_id=str(uuid4()),
            category=AuditEvent.SECURITY,
            action=action,
            outcome=outcome,
            user_id=user_id,
            details=details,
        )
        AuditLogger.log_event(event)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit all HTTP requests.
    """
    
    # Paths to exclude from audit logging
    EXCLUDED_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    # Methods that modify data
    MODIFICATION_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and log audit event.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Extract request details
        user_id = self._get_user_id(request)
        ip_address = self._get_client_ip(request)
        
        # Start timing
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            outcome = AuditEvent.SUCCESS if response.status_code < 400 else AuditEvent.FAILURE
        except Exception as e:
            outcome = AuditEvent.ERROR
            response = None
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine category and action
            category = self._get_category(request)
            action = f"{request.method}_{request.url.path}"
            
            # Log audit event
            event = AuditEvent(
                event_id=request_id,
                category=category,
                action=action,
                outcome=outcome,
                user_id=user_id,
                resource=request.url.path,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "ip_address": ip_address,
                    "user_agent": request.headers.get("user-agent"),
                    "status_code": response.status_code if response else None,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
            AuditLogger.log_event(event)
        
        return response
    
    def _get_user_id(self, request: Request) -> str:
        """
        Extract user ID from request.
        
        For MVP without authentication, use IP address as identifier.
        In production, extract from JWT token or session.
        """
        # TODO: Extract from authentication token when implemented
        return request.client.host if request.client else "unknown"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Use direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_category(self, request: Request) -> str:
        """Determine audit event category based on request."""
        # Configuration changes
        if "/config" in request.url.path or "/settings" in request.url.path:
            return AuditEvent.CONFIGURATION
        
        # Data modifications
        if request.method in self.MODIFICATION_METHODS:
            return AuditEvent.DATA_MODIFICATION
        
        # Data access (read operations)
        return AuditEvent.DATA_ACCESS


# Convenience function for manual audit logging
def audit_log(
    category: str,
    action: str,
    outcome: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[dict] = None,
):
    """
    Manually log an audit event.
    
    Args:
        category: Event category
        action: Action performed
        outcome: Event outcome (success/failure/error)
        user_id: User identifier
        resource: Resource accessed/modified
        details: Additional event details
    """
    event = AuditEvent(
        event_id=str(uuid4()),
        category=category,
        action=action,
        outcome=outcome,
        user_id=user_id,
        resource=resource,
        details=details,
    )
    AuditLogger.log_event(event)

# Made with Bob
