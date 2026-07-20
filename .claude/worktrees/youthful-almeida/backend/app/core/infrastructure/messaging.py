"""
Message Broker Infrastructure with RabbitMQ and Redis Support

Provides:
- Message publishing and consumption
- Event-driven architecture support
- Queue management
- Dead letter handling
- Message routing and filtering
- Retry mechanisms with exponential backoff
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aioredis
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType

from app.core.config import settings

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class ExchangeTypes(Enum):
    """RabbitMQ exchange types"""
    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"
    HEADERS = "headers"


@dataclass
class Message:
    """Message container with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, Any] = field(default_factory=dict)
    routing_key: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expiration: Optional[int] = None  # TTL in seconds
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'headers': self.headers,
            'routing_key': self.routing_key,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'expiration': self.expiration,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        message = cls(
            id=data.get('id', str(uuid.uuid4())),
            content=data.get('content', {}),
            headers=data.get('headers', {}),
            routing_key=data.get('routing_key', ''),
            priority=MessagePriority(data.get('priority', MessagePriority.NORMAL.value)),
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to'),
            expiration=data.get('expiration'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
        
        if 'created_at' in data:
            message.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        return message


class MessageBroker(ABC):
    """Abstract message broker interface"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to message broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from message broker"""
        pass
    
    @abstractmethod
    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Union[Message, Dict[str, Any]],
        **kwargs
    ) -> bool:
        """Publish message to exchange"""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        queue: str,
        callback: Callable,
        **kwargs
    ) -> None:
        """Subscribe to queue with message handler"""
        pass
    
    @abstractmethod
    async def create_exchange(
        self,
        name: str,
        exchange_type: ExchangeTypes,
        durable: bool = True,
        **kwargs
    ) -> None:
        """Create exchange"""
        pass
    
    @abstractmethod
    async def create_queue(
        self,
        name: str,
        durable: bool = True,
        **kwargs
    ) -> None:
        """Create queue"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        pass


class RabbitMQBroker(MessageBroker):
    """RabbitMQ message broker implementation"""
    
    def __init__(self):
        self.connection: Optional[AsyncioConnection] = None
        self.channel = None
        self.url = self._build_connection_url()
        self.is_connected = False
        self._subscribers: Dict[str, Callable] = {}
        
    def _build_connection_url(self) -> str:
        """Build RabbitMQ connection URL"""
        host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        port = getattr(settings, 'RABBITMQ_PORT', 5672)
        username = getattr(settings, 'RABBITMQ_USERNAME', 'guest')
        password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        vhost = getattr(settings, 'RABBITMQ_VHOST', '/')
        
        return f"amqp://{username}:{password}@{host}:{port}/{vhost}"
    
    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            connection_params = pika.URLParameters(self.url)
            self.connection = await AsyncioConnection.create(
                connection_params,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_error,
                on_close_callback=self._on_connection_closed
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            self.is_connected = True
            logger.info("Connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        try:
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
            
            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    async def create_exchange(
        self,
        name: str,
        exchange_type: ExchangeTypes,
        durable: bool = True,
        **kwargs
    ) -> None:
        """Create RabbitMQ exchange"""
        if not self.is_connected:
            await self.connect()
        
        await self.channel.exchange_declare(
            exchange=name,
            exchange_type=exchange_type.value,
            durable=durable,
            **kwargs
        )
        
        logger.debug(f"Created exchange: {name} ({exchange_type.value})")
    
    async def create_queue(
        self,
        name: str,
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Create RabbitMQ queue"""
        if not self.is_connected:
            await self.connect()
        
        await self.channel.queue_declare(
            queue=name,
            durable=durable,
            exclusive=exclusive,
            auto_delete=auto_delete,
            arguments=arguments or {}
        )
        
        logger.debug(f"Created queue: {name}")
    
    async def bind_queue(
        self,
        queue: str,
        exchange: str,
        routing_key: str = "",
        arguments: Optional[Dict[str, Any]] = None
    ) -> None:
        """Bind queue to exchange"""
        if not self.is_connected:
            await self.connect()
        
        await self.channel.queue_bind(
            exchange=exchange,
            queue=queue,
            routing_key=routing_key,
            arguments=arguments
        )
        
        logger.debug(f"Bound queue {queue} to exchange {exchange} with routing key {routing_key}")
    
    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Union[Message, Dict[str, Any]],
        mandatory: bool = False,
        immediate: bool = False
    ) -> bool:
        """Publish message to RabbitMQ exchange"""
        if not self.is_connected:
            await self.connect()
        
        if isinstance(message, dict):
            message = Message(content=message, routing_key=routing_key)
        
        try:
            properties = pika.BasicProperties(
                message_id=message.id,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                priority=message.priority.value,
                timestamp=int(message.created_at.timestamp()),
                headers=message.headers,
                expiration=str(message.expiration * 1000) if message.expiration else None,
                delivery_mode=2  # Persistent
            )
            
            body = json.dumps(message.to_dict()).encode('utf-8')
            
            await self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=properties,
                mandatory=mandatory,
                immediate=immediate
            )
            
            logger.debug(f"Published message {message.id} to exchange {exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    async def subscribe(
        self,
        queue: str,
        callback: Callable,
        auto_ack: bool = False,
        exclusive: bool = False,
        consumer_tag: Optional[str] = None
    ) -> None:
        """Subscribe to RabbitMQ queue"""
        if not self.is_connected:
            await self.connect()
        
        async def message_handler(channel, method, properties, body):
            """Handle incoming messages"""
            try:
                data = json.loads(body.decode('utf-8'))
                message = Message.from_dict(data)
                
                # Call user-defined callback
                success = await callback(message)
                
                if success and not auto_ack:
                    await channel.basic_ack(delivery_tag=method.delivery_tag)
                elif not success and not auto_ack:
                    # Reject and requeue for retry
                    await channel.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=message.retry_count < message.max_retries
                    )
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if not auto_ack:
                    await channel.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False
                    )
        
        await self.channel.basic_consume(
            queue=queue,
            on_message_callback=message_handler,
            auto_ack=auto_ack,
            exclusive=exclusive,
            consumer_tag=consumer_tag
        )
        
        self._subscribers[queue] = callback
        logger.info(f"Subscribed to queue: {queue}")
    
    async def health_check(self) -> Dict[str, Any]:
        """RabbitMQ health check"""
        try:
            if not self.is_connected:
                return {
                    'status': 'unhealthy',
                    'error': 'Not connected to RabbitMQ'
                }
            
            # Check connection and channel health
            if self.connection.is_closed or self.channel.is_closed:
                return {
                    'status': 'unhealthy', 
                    'error': 'Connection or channel is closed'
                }
            
            return {
                'status': 'healthy',
                'connection_state': 'open',
                'subscribers': len(self._subscribers)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _on_connection_open(self, connection):
        """Connection opened callback"""
        logger.info("RabbitMQ connection opened")
    
    def _on_connection_error(self, connection, error):
        """Connection error callback"""
        logger.error(f"RabbitMQ connection error: {error}")
    
    def _on_connection_closed(self, connection, reason):
        """Connection closed callback"""
        logger.warning(f"RabbitMQ connection closed: {reason}")
        self.is_connected = False


class RedisBroker(MessageBroker):
    """Redis-based message broker for lightweight messaging"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.is_connected = False
        self._subscribers: Dict[str, Callable] = {}
        self._subscriber_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            await self.redis.ping()
            
            self.is_connected = True
            logger.info("Connected to Redis message broker")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        try:
            # Cancel subscriber tasks
            for task in self._subscriber_tasks.values():
                task.cancel()
            
            if self.redis:
                await self.redis.close()
            
            self.is_connected = False
            logger.info("Disconnected from Redis")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
    
    async def create_exchange(
        self,
        name: str,
        exchange_type: ExchangeTypes,
        durable: bool = True,
        **kwargs
    ) -> None:
        """Create exchange (Redis streams)"""
        if not self.is_connected:
            await self.connect()
        
        # Create stream if it doesn't exist
        try:
            await self.redis.xadd(name, {'_init': 'true'}, id='0-1')
            await self.redis.xdel(name, '0-1')
        except Exception:
            pass  # Stream already exists
        
        logger.debug(f"Created Redis stream: {name}")
    
    async def create_queue(
        self,
        name: str,
        durable: bool = True,
        **kwargs
    ) -> None:
        """Create queue (Redis list)"""
        if not self.is_connected:
            await self.connect()
        
        # Initialize list if it doesn't exist
        exists = await self.redis.exists(name)
        if not exists:
            await self.redis.lpush(name, json.dumps({'_init': True}))
            await self.redis.lpop(name)
        
        logger.debug(f"Created Redis queue: {name}")
    
    async def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Union[Message, Dict[str, Any]],
        **kwargs
    ) -> bool:
        """Publish message to Redis"""
        if not self.is_connected:
            await self.connect()
        
        if isinstance(message, dict):
            message = Message(content=message, routing_key=routing_key)
        
        try:
            queue_name = f"{exchange}:{routing_key}" if routing_key else exchange
            message_data = json.dumps(message.to_dict())
            
            await self.redis.lpush(queue_name, message_data)
            
            # Set expiration if specified
            if message.expiration:
                await self.redis.expire(queue_name, message.expiration)
            
            logger.debug(f"Published message {message.id} to Redis queue {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to Redis: {e}")
            return False
    
    async def subscribe(
        self,
        queue: str,
        callback: Callable,
        **kwargs
    ) -> None:
        """Subscribe to Redis queue"""
        if not self.is_connected:
            await self.connect()
        
        async def message_consumer():
            """Consume messages from Redis queue"""
            while True:
                try:
                    # Block and wait for message
                    result = await self.redis.brpop(queue, timeout=1)
                    
                    if result:
                        _, message_data = result
                        data = json.loads(message_data)
                        message = Message.from_dict(data)
                        
                        # Call user-defined callback
                        try:
                            await callback(message)
                        except Exception as e:
                            logger.error(f"Error in message callback: {e}")
                            
                            # Implement retry logic
                            if message.retry_count < message.max_retries:
                                message.retry_count += 1
                                await asyncio.sleep(2 ** message.retry_count)  # Exponential backoff
                                await self.redis.lpush(queue, json.dumps(message.to_dict()))
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in Redis message consumer: {e}")
                    await asyncio.sleep(1)
        
        task = asyncio.create_task(message_consumer())
        self._subscriber_tasks[queue] = task
        self._subscribers[queue] = callback
        
        logger.info(f"Subscribed to Redis queue: {queue}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Redis health check"""
        try:
            if not self.is_connected:
                return {
                    'status': 'unhealthy',
                    'error': 'Not connected to Redis'
                }
            
            # Test Redis connection
            pong = await self.redis.ping()
            
            if pong:
                return {
                    'status': 'healthy',
                    'subscribers': len(self._subscribers),
                    'active_tasks': len(self._subscriber_tasks)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Redis ping failed'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


class EventPublisher:
    """High-level event publisher for domain events"""
    
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.default_exchange = "financial_events"
    
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        routing_key: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish domain event"""
        message = Message(
            content={
                'event_type': event_type,
                'payload': payload,
                'published_at': datetime.now(timezone.utc).isoformat()
            },
            routing_key=routing_key or event_type,
            priority=priority,
            correlation_id=correlation_id,
            headers={
                'event_type': event_type,
                'version': '1.0'
            }
        )
        
        return await self.broker.publish(
            exchange=self.default_exchange,
            routing_key=message.routing_key,
            message=message
        )
    
    async def publish_user_event(
        self,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Publish user-specific event"""
        payload['user_id'] = user_id
        routing_key = f"user.{user_id}.{event_type}"
        
        return await self.publish_event(
            event_type=event_type,
            payload=payload,
            routing_key=routing_key,
            **kwargs
        )
    
    async def publish_plan_event(
        self,
        plan_id: str,
        event_type: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Publish plan-specific event"""
        payload['plan_id'] = plan_id
        routing_key = f"plan.{plan_id}.{event_type}"
        
        return await self.publish_event(
            event_type=event_type,
            payload=payload,
            routing_key=routing_key,
            **kwargs
        )


# Global broker instances
rabbitmq_broker = RabbitMQBroker()
redis_broker = RedisBroker()


# Factory function to get appropriate broker
def get_message_broker(broker_type: str = None) -> MessageBroker:
    """Get message broker instance"""
    broker_type = broker_type or getattr(settings, 'MESSAGE_BROKER_TYPE', 'redis')
    
    if broker_type.lower() == 'rabbitmq':
        return rabbitmq_broker
    elif broker_type.lower() == 'redis':
        return redis_broker
    else:
        raise ValueError(f"Unsupported message broker type: {broker_type}")


# Event publisher with default broker
event_publisher = EventPublisher(get_message_broker())


@asynccontextmanager
async def message_broker_context(broker_type: str = None):
    """Context manager for message broker connection"""
    broker = get_message_broker(broker_type)
    
    try:
        await broker.connect()
        yield broker
    finally:
        await broker.disconnect()