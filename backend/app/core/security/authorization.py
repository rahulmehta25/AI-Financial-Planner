"""
Authorization Module

Implements Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC)
for fine-grained permission management in financial services.
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
from fastapi import HTTPException, status

from app.core.config import settings


class Role(Enum):
    """System roles with hierarchical permissions"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    FINANCIAL_ADVISOR = "financial_advisor"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ANALYST = "analyst"
    CLIENT = "client"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions for system resources"""
    
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # Portfolio Management
    PORTFOLIO_CREATE = "portfolio:create"
    PORTFOLIO_READ = "portfolio:read"
    PORTFOLIO_UPDATE = "portfolio:update"
    PORTFOLIO_DELETE = "portfolio:delete"
    PORTFOLIO_SIMULATE = "portfolio:simulate"
    PORTFOLIO_REBALANCE = "portfolio:rebalance"
    
    # Financial Data
    FINANCIAL_DATA_READ = "financial_data:read"
    FINANCIAL_DATA_WRITE = "financial_data:write"
    FINANCIAL_DATA_EXPORT = "financial_data:export"
    
    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_AUDIT = "compliance:audit"
    COMPLIANCE_REPORT = "compliance:report"
    COMPLIANCE_APPROVE = "compliance:approve"
    
    # System
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"
    
    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Trading
    TRADE_EXECUTE = "trade:execute"
    TRADE_VIEW = "trade:view"
    TRADE_APPROVE = "trade:approve"


@dataclass
class ResourceContext:
    """Context for resource-based authorization"""
    resource_type: str
    resource_id: str
    owner_id: Optional[str] = None
    department: Optional[str] = None
    classification: Optional[str] = None  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    attributes: Dict[str, Any] = None


@dataclass
class UserContext:
    """User context for authorization decisions"""
    user_id: str
    roles: List[Role]
    department: Optional[str] = None
    clearance_level: Optional[str] = None
    attributes: Dict[str, Any] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None


class RBACPolicy:
    """Role-Based Access Control Policy Manager"""
    
    # Define role-permission mappings
    ROLE_PERMISSIONS = {
        Role.SUPER_ADMIN: {permission for permission in Permission},  # All permissions
        
        Role.ADMIN: {
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.USER_LIST,
            Permission.PORTFOLIO_CREATE,
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_UPDATE,
            Permission.PORTFOLIO_DELETE,
            Permission.PORTFOLIO_SIMULATE,
            Permission.PORTFOLIO_REBALANCE,
            Permission.FINANCIAL_DATA_READ,
            Permission.FINANCIAL_DATA_WRITE,
            Permission.FINANCIAL_DATA_EXPORT,
            Permission.COMPLIANCE_VIEW,
            Permission.SYSTEM_MONITOR,
            Permission.ANALYTICS_VIEW,
            Permission.ANALYTICS_EXPORT,
            Permission.TRADE_VIEW
        },
        
        Role.COMPLIANCE_OFFICER: {
            Permission.USER_READ,
            Permission.USER_LIST,
            Permission.PORTFOLIO_READ,
            Permission.FINANCIAL_DATA_READ,
            Permission.FINANCIAL_DATA_EXPORT,
            Permission.COMPLIANCE_VIEW,
            Permission.COMPLIANCE_AUDIT,
            Permission.COMPLIANCE_REPORT,
            Permission.COMPLIANCE_APPROVE,
            Permission.ANALYTICS_VIEW,
            Permission.TRADE_VIEW
        },
        
        Role.FINANCIAL_ADVISOR: {
            Permission.USER_READ,
            Permission.PORTFOLIO_CREATE,
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_UPDATE,
            Permission.PORTFOLIO_SIMULATE,
            Permission.PORTFOLIO_REBALANCE,
            Permission.FINANCIAL_DATA_READ,
            Permission.ANALYTICS_VIEW,
            Permission.TRADE_EXECUTE,
            Permission.TRADE_VIEW
        },
        
        Role.PORTFOLIO_MANAGER: {
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_UPDATE,
            Permission.PORTFOLIO_SIMULATE,
            Permission.PORTFOLIO_REBALANCE,
            Permission.FINANCIAL_DATA_READ,
            Permission.ANALYTICS_VIEW,
            Permission.TRADE_EXECUTE,
            Permission.TRADE_VIEW,
            Permission.TRADE_APPROVE
        },
        
        Role.ANALYST: {
            Permission.PORTFOLIO_READ,
            Permission.PORTFOLIO_SIMULATE,
            Permission.FINANCIAL_DATA_READ,
            Permission.ANALYTICS_VIEW
        },
        
        Role.CLIENT: {
            Permission.PORTFOLIO_READ,  # Own portfolio only
            Permission.PORTFOLIO_SIMULATE,  # Own portfolio only
            Permission.FINANCIAL_DATA_READ,  # Own data only
            Permission.ANALYTICS_VIEW  # Own analytics only
        },
        
        Role.GUEST: {
            # No permissions by default
        }
    }
    
    # Role hierarchy for inheritance
    ROLE_HIERARCHY = {
        Role.SUPER_ADMIN: [Role.ADMIN],
        Role.ADMIN: [Role.COMPLIANCE_OFFICER, Role.FINANCIAL_ADVISOR],
        Role.FINANCIAL_ADVISOR: [Role.PORTFOLIO_MANAGER],
        Role.PORTFOLIO_MANAGER: [Role.ANALYST],
        Role.ANALYST: [Role.CLIENT],
        Role.CLIENT: [Role.GUEST]
    }
    
    @classmethod
    def get_permissions(cls, roles: List[Role]) -> Set[Permission]:
        """Get all permissions for given roles"""
        permissions = set()
        
        for role in roles:
            # Add direct permissions
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role])
            
            # Add inherited permissions
            for parent_role in cls.get_inherited_roles(role):
                if parent_role in cls.ROLE_PERMISSIONS:
                    permissions.update(cls.ROLE_PERMISSIONS[parent_role])
        
        return permissions
    
    @classmethod
    def get_inherited_roles(cls, role: Role) -> List[Role]:
        """Get all inherited roles based on hierarchy"""
        inherited = []
        
        def traverse(r: Role):
            if r in cls.ROLE_HIERARCHY:
                for child in cls.ROLE_HIERARCHY[r]:
                    if child not in inherited:
                        inherited.append(child)
                        traverse(child)
        
        traverse(role)
        return inherited
    
    @classmethod
    def has_permission(cls, roles: List[Role], permission: Permission) -> bool:
        """Check if roles have specific permission"""
        permissions = cls.get_permissions(roles)
        return permission in permissions
    
    @classmethod
    def can_access_resource(
        cls,
        user_context: UserContext,
        resource_context: ResourceContext,
        permission: Permission
    ) -> bool:
        """Check if user can access specific resource"""
        
        # Check basic permission
        if not cls.has_permission(user_context.roles, permission):
            return False
        
        # Additional checks for CLIENT role
        if Role.CLIENT in user_context.roles and Role.ADMIN not in user_context.roles:
            # Clients can only access their own resources
            if resource_context.owner_id != user_context.user_id:
                return False
        
        return True


class ABACPolicy:
    """
    Attribute-Based Access Control Policy Manager
    Provides fine-grained access control based on attributes
    """
    
    def __init__(self):
        self.policies = []
        self.load_policies()
    
    def load_policies(self):
        """Load ABAC policies from configuration"""
        
        # Example policies
        self.policies = [
            {
                "id": "policy_1",
                "name": "Restrict PII access",
                "description": "Only authorized users can access PII data",
                "effect": "DENY",
                "conditions": {
                    "resource.classification": "PII",
                    "user.clearance_level": {"$nin": ["HIGH", "TOP_SECRET"]}
                }
            },
            {
                "id": "policy_2",
                "name": "Department isolation",
                "description": "Users can only access resources in their department",
                "effect": "DENY",
                "conditions": {
                    "resource.department": {"$ne": "user.department"},
                    "user.roles": {"$nin": ["ADMIN", "SUPER_ADMIN"]}
                }
            },
            {
                "id": "policy_3",
                "name": "Time-based access",
                "description": "Restrict access outside business hours",
                "effect": "DENY",
                "conditions": {
                    "time.hour": {"$lt": 8, "$gt": 18},
                    "user.roles": {"$nin": ["ADMIN", "SUPER_ADMIN", "COMPLIANCE_OFFICER"]}
                }
            },
            {
                "id": "policy_4",
                "name": "Geographic restriction",
                "description": "Restrict access from certain countries",
                "effect": "DENY",
                "conditions": {
                    "user.country": {"$in": ["restricted_country_1", "restricted_country_2"]}
                }
            },
            {
                "id": "policy_5",
                "name": "High-value transaction approval",
                "description": "Transactions over $1M require additional approval",
                "effect": "DENY",
                "conditions": {
                    "resource.value": {"$gt": 1000000},
                    "user.approval_limit": {"$lt": 1000000}
                }
            }
        ]
    
    def evaluate_policy(
        self,
        policy: Dict[str, Any],
        user_context: UserContext,
        resource_context: ResourceContext,
        action: str
    ) -> bool:
        """Evaluate a single ABAC policy"""
        
        # Build evaluation context
        context = {
            "user": {
                "id": user_context.user_id,
                "roles": [role.value for role in user_context.roles],
                "department": user_context.department,
                "clearance_level": user_context.clearance_level,
                **(user_context.attributes or {})
            },
            "resource": {
                "type": resource_context.resource_type,
                "id": resource_context.resource_id,
                "owner_id": resource_context.owner_id,
                "department": resource_context.department,
                "classification": resource_context.classification,
                **(resource_context.attributes or {})
            },
            "action": action,
            "time": {
                "hour": datetime.now().hour,
                "day": datetime.now().day,
                "weekday": datetime.now().weekday()
            }
        }
        
        # Evaluate conditions
        conditions = policy.get("conditions", {})
        
        for condition_key, condition_value in conditions.items():
            # Parse the condition key (e.g., "user.department")
            keys = condition_key.split(".")
            actual_value = context
            
            for key in keys:
                if isinstance(actual_value, dict) and key in actual_value:
                    actual_value = actual_value[key]
                else:
                    actual_value = None
                    break
            
            # Evaluate the condition
            if isinstance(condition_value, dict):
                # Complex condition with operators
                for operator, expected in condition_value.items():
                    if operator == "$eq" and actual_value != expected:
                        return False
                    elif operator == "$ne" and actual_value == expected:
                        return False
                    elif operator == "$in" and actual_value not in expected:
                        return False
                    elif operator == "$nin" and actual_value in expected:
                        return False
                    elif operator == "$gt" and actual_value <= expected:
                        return False
                    elif operator == "$lt" and actual_value >= expected:
                        return False
            else:
                # Simple equality check
                if actual_value != condition_value:
                    return False
        
        return True
    
    def check_access(
        self,
        user_context: UserContext,
        resource_context: ResourceContext,
        action: str
    ) -> bool:
        """Check if access is allowed based on ABAC policies"""
        
        for policy in self.policies:
            if self.evaluate_policy(policy, user_context, resource_context, action):
                if policy["effect"] == "DENY":
                    return False
        
        return True


class PermissionChecker:
    """
    Permission checker combining RBAC and ABAC
    """
    
    def __init__(self):
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
        self.permission_cache = {}
    
    def check_permission(
        self,
        user_context: UserContext,
        permission: Permission,
        resource_context: Optional[ResourceContext] = None
    ) -> bool:
        """
        Check if user has permission for action
        Combines RBAC and ABAC policies
        """
        
        # Generate cache key
        cache_key = f"{user_context.user_id}:{permission.value}"
        if resource_context:
            cache_key += f":{resource_context.resource_type}:{resource_context.resource_id}"
        
        # Check cache
        if cache_key in self.permission_cache:
            cached_result, cached_time = self.permission_cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:  # 5 minute cache
                return cached_result
        
        # RBAC check
        if not RBACPolicy.has_permission(user_context.roles, permission):
            self.permission_cache[cache_key] = (False, datetime.now())
            return False
        
        # ABAC check if resource context is provided
        if resource_context:
            if not self.abac_policy.check_access(
                user_context,
                resource_context,
                permission.value
            ):
                self.permission_cache[cache_key] = (False, datetime.now())
                return False
        
        # Additional ownership check for certain permissions
        if resource_context and Role.CLIENT in user_context.roles:
            if resource_context.owner_id != user_context.user_id:
                # Clients can only access their own resources
                self.permission_cache[cache_key] = (False, datetime.now())
                return False
        
        self.permission_cache[cache_key] = (True, datetime.now())
        return True
    
    def require_permission(
        self,
        user_context: UserContext,
        permission: Permission,
        resource_context: Optional[ResourceContext] = None
    ):
        """
        Require permission or raise HTTPException
        """
        
        if not self.check_permission(user_context, permission, resource_context):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
    
    def get_accessible_resources(
        self,
        user_context: UserContext,
        resource_type: str,
        permission: Permission
    ) -> List[str]:
        """
        Get list of resource IDs user can access
        """
        
        # For clients, return only their own resources
        if Role.CLIENT in user_context.roles and Role.ADMIN not in user_context.roles:
            return [user_context.user_id]
        
        # For admins, return all resources
        if Role.ADMIN in user_context.roles or Role.SUPER_ADMIN in user_context.roles:
            return ["*"]  # Wildcard for all resources
        
        # For other roles, apply department-based filtering
        # This would typically query the database
        return []


class AuthorizationManager:
    """
    Central authorization manager
    """
    
    def __init__(self):
        self.permission_checker = PermissionChecker()
        self.audit_log = []
    
    def authorize(
        self,
        user_context: UserContext,
        permission: Permission,
        resource_context: Optional[ResourceContext] = None
    ) -> bool:
        """
        Authorize user action and log the attempt
        """
        
        result = self.permission_checker.check_permission(
            user_context,
            permission,
            resource_context
        )
        
        # Log authorization attempt
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_context.user_id,
            "permission": permission.value,
            "resource": {
                "type": resource_context.resource_type if resource_context else None,
                "id": resource_context.resource_id if resource_context else None
            },
            "result": "GRANTED" if result else "DENIED",
            "ip_address": user_context.ip_address,
            "session_id": user_context.session_id
        })
        
        return result
    
    def require_any_permission(
        self,
        user_context: UserContext,
        permissions: List[Permission],
        resource_context: Optional[ResourceContext] = None
    ):
        """
        Require at least one of the specified permissions
        """
        
        for permission in permissions:
            if self.authorize(user_context, permission, resource_context):
                return
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required one of: {[p.value for p in permissions]}"
        )
    
    def require_all_permissions(
        self,
        user_context: UserContext,
        permissions: List[Permission],
        resource_context: Optional[ResourceContext] = None
    ):
        """
        Require all specified permissions
        """
        
        for permission in permissions:
            if not self.authorize(user_context, permission, resource_context):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {permission.value}"
                )