"""
Dependency Injection System for Service Architecture

Provides:
- Service registration and discovery
- Dependency resolution
- Lifecycle management
- Scoped services (singleton, transient, scoped)
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, get_type_hints
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options"""
    SINGLETON = "singleton"     # Single instance for application lifetime
    TRANSIENT = "transient"     # New instance every time
    SCOPED = "scoped"          # Single instance per scope (e.g., request)


class ServiceRegistry:
    """
    Central registry for dependency injection services
    """
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}  # Singleton instances
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}  # Scoped instances by scope_id
        self._factories: Dict[str, Callable] = {}
        self._resolving: set = set()  # Circular dependency detection
    
    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Union[Type[T], Callable[..., T]]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Optional[Callable] = None,
        name: Optional[str] = None
    ) -> None:
        """
        Register a service with the DI container
        
        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            lifetime: Service lifetime (singleton, transient, scoped)
            factory: Custom factory function
            name: Optional service name for multiple implementations
        """
        service_key = self._get_service_key(service_type, name)
        
        self._services[service_key] = {
            'service_type': service_type,
            'implementation': implementation or service_type,
            'lifetime': lifetime,
            'factory': factory,
            'name': name
        }
        
        if factory:
            self._factories[service_key] = factory
            
        logger.debug(f"Registered service: {service_key} with lifetime {lifetime}")
    
    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Union[Type[T], T]] = None,
        name: Optional[str] = None
    ) -> None:
        """Register a singleton service"""
        if isinstance(implementation, type):
            self.register(service_type, implementation, ServiceLifetime.SINGLETON, name=name)
        else:
            # Pre-created instance
            service_key = self._get_service_key(service_type, name)
            self._instances[service_key] = implementation or service_type()
            self._services[service_key] = {
                'service_type': service_type,
                'implementation': service_type,
                'lifetime': ServiceLifetime.SINGLETON,
                'factory': None,
                'name': name
            }
    
    def register_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        name: Optional[str] = None
    ) -> None:
        """Register a transient service"""
        self.register(service_type, implementation, ServiceLifetime.TRANSIENT, name=name)
    
    def register_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        name: Optional[str] = None
    ) -> None:
        """Register a scoped service"""
        self.register(service_type, implementation, ServiceLifetime.SCOPED, name=name)
    
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        name: Optional[str] = None
    ) -> None:
        """Register a service with a factory function"""
        self.register(service_type, None, lifetime, factory, name)
    
    async def resolve(
        self,
        service_type: Type[T],
        name: Optional[str] = None,
        scope_id: Optional[str] = None
    ) -> T:
        """
        Resolve a service instance
        
        Args:
            service_type: The service type to resolve
            name: Optional service name
            scope_id: Scope identifier for scoped services
        """
        service_key = self._get_service_key(service_type, name)
        
        if service_key not in self._services:
            raise ValueError(f"Service {service_key} not registered")
        
        # Circular dependency detection
        if service_key in self._resolving:
            raise ValueError(f"Circular dependency detected for service {service_key}")
        
        service_info = self._services[service_key]
        lifetime = service_info['lifetime']
        
        # Handle different lifetimes
        if lifetime == ServiceLifetime.SINGLETON:
            return await self._resolve_singleton(service_key, service_info)
        elif lifetime == ServiceLifetime.SCOPED:
            return await self._resolve_scoped(service_key, service_info, scope_id)
        else:  # TRANSIENT
            return await self._create_instance(service_key, service_info)
    
    async def _resolve_singleton(self, service_key: str, service_info: Dict[str, Any]) -> Any:
        """Resolve singleton service"""
        if service_key in self._instances:
            return self._instances[service_key]
        
        instance = await self._create_instance(service_key, service_info)
        self._instances[service_key] = instance
        return instance
    
    async def _resolve_scoped(
        self,
        service_key: str,
        service_info: Dict[str, Any],
        scope_id: Optional[str]
    ) -> Any:
        """Resolve scoped service"""
        if not scope_id:
            scope_id = "default"
        
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        
        scoped_services = self._scoped_instances[scope_id]
        
        if service_key in scoped_services:
            return scoped_services[service_key]
        
        instance = await self._create_instance(service_key, service_info)
        scoped_services[service_key] = instance
        return instance
    
    async def _create_instance(self, service_key: str, service_info: Dict[str, Any]) -> Any:
        """Create a new service instance"""
        self._resolving.add(service_key)
        
        try:
            implementation = service_info['implementation']
            factory = service_info['factory']
            
            if factory:
                # Use custom factory
                if asyncio.iscoroutinefunction(factory):
                    instance = await factory()
                else:
                    instance = factory()
            else:
                # Create instance using constructor injection
                instance = await self._create_with_dependency_injection(implementation)
            
            return instance
            
        finally:
            self._resolving.remove(service_key)
    
    async def _create_with_dependency_injection(self, implementation_type: Type) -> Any:
        """Create instance with automatic dependency injection"""
        # Get constructor signature
        if hasattr(implementation_type, '__init__'):
            signature = inspect.signature(implementation_type.__init__)
            type_hints = get_type_hints(implementation_type.__init__)
        else:
            return implementation_type()
        
        # Resolve constructor dependencies
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            # Get parameter type
            param_type = type_hints.get(param_name)
            
            if param_type:
                try:
                    # Try to resolve the dependency
                    dependency = await self.resolve(param_type)
                    kwargs[param_name] = dependency
                except (ValueError, KeyError):
                    # If dependency can't be resolved and has default value, use default
                    if param.default is not inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        logger.warning(f"Could not resolve dependency {param_name}: {param_type}")
        
        # Create instance
        if asyncio.iscoroutinefunction(implementation_type.__init__):
            return await implementation_type(**kwargs)
        else:
            return implementation_type(**kwargs)
    
    def clear_scope(self, scope_id: str) -> None:
        """Clear all scoped services for a given scope"""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
            logger.debug(f"Cleared scope: {scope_id}")
    
    def _get_service_key(self, service_type: Type, name: Optional[str] = None) -> str:
        """Generate service key"""
        type_name = getattr(service_type, '__name__', str(service_type))
        return f"{type_name}:{name}" if name else type_name
    
    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered services for debugging"""
        return self._services.copy()


# Global service registry instance
service_registry = ServiceRegistry()


def inject(
    service_type: Type[T],
    name: Optional[str] = None,
    scope_id: Optional[str] = None
) -> Callable:
    """
    Decorator for dependency injection
    
    Usage:
    @inject(SomeService)
    async def some_function(service: SomeService):
        return await service.do_something()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Resolve the service
            service_instance = await service_registry.resolve(
                service_type,
                name=name,
                scope_id=scope_id
            )
            
            # Add service as first argument or named parameter
            if 'service' not in kwargs:
                return await func(service_instance, *args, **kwargs)
            else:
                kwargs[service_type.__name__.lower()] = service_instance
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


@asynccontextmanager
async def service_scope(scope_id: str = None):
    """
    Context manager for service scoping
    
    Usage:
    async with service_scope("request_123") as scope:
        service = await scope.resolve(SomeService)
    """
    if not scope_id:
        scope_id = f"scope_{id(asyncio.current_task())}"
    
    class ScopedResolver:
        def __init__(self, scope_id: str):
            self.scope_id = scope_id
        
        async def resolve(self, service_type: Type[T], name: Optional[str] = None) -> T:
            return await service_registry.resolve(service_type, name, self.scope_id)
    
    resolver = ScopedResolver(scope_id)
    try:
        yield resolver
    finally:
        service_registry.clear_scope(scope_id)


class ServiceProvider:
    """
    Service provider for manual service resolution
    Used in contexts where decorator injection is not suitable
    """
    
    def __init__(self, registry: ServiceRegistry = None):
        self.registry = registry or service_registry
    
    async def get_service(
        self,
        service_type: Type[T],
        name: Optional[str] = None,
        scope_id: Optional[str] = None
    ) -> T:
        """Get service instance"""
        return await self.registry.resolve(service_type, name, scope_id)
    
    async def get_required_service(
        self,
        service_type: Type[T],
        name: Optional[str] = None,
        scope_id: Optional[str] = None
    ) -> T:
        """Get service instance, raising exception if not found"""
        try:
            return await self.registry.resolve(service_type, name, scope_id)
        except ValueError as e:
            raise ValueError(f"Required service {service_type.__name__} not available: {e}")


# Convenience functions
def register_service(
    service_type: Type[T],
    implementation: Optional[Type[T]] = None,
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    name: Optional[str] = None
) -> None:
    """Register a service with the global registry"""
    service_registry.register(service_type, implementation, lifetime, name)


def register_singleton(
    service_type: Type[T],
    implementation: Optional[Union[Type[T], T]] = None,
    name: Optional[str] = None
) -> None:
    """Register a singleton service with the global registry"""
    service_registry.register_singleton(service_type, implementation, name)


def register_factory(
    service_type: Type[T],
    factory: Callable[..., T],
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    name: Optional[str] = None
) -> None:
    """Register a factory service with the global registry"""
    service_registry.register_factory(service_type, factory, lifetime, name)


async def resolve_service(
    service_type: Type[T],
    name: Optional[str] = None,
    scope_id: Optional[str] = None
) -> T:
    """Resolve a service from the global registry"""
    return await service_registry.resolve(service_type, name, scope_id)