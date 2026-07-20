"""
API Performance Optimizer with GraphQL and Response Optimization

Features:
- GraphQL for efficient data fetching
- Response compression (Brotli/Gzip)
- Request batching and deduplication
- Pagination optimization
- Field-level caching
- Query complexity analysis
"""

import gzip
import brotli
import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from strawberry.permission import BasePermission
from strawberry.extensions import Extension

from ..performance.advanced_cache import AdvancedRedisCache, CacheTTL

logger = None  # Will be initialized from main app


class CompressionType(Enum):
    """Supported compression types"""
    BROTLI = "br"
    GZIP = "gzip"
    NONE = "identity"


@dataclass
class QueryComplexity:
    """Query complexity metrics"""
    score: int
    depth: int
    breadth: int
    estimated_time_ms: float
    cache_eligible: bool


class ComplexityAnalyzer:
    """Analyze GraphQL query complexity"""
    
    # Cost factors for different operations
    FIELD_COST = 1
    LIST_COST = 10
    NESTED_COST = 5
    
    @classmethod
    def analyze(cls, query: str, variables: Dict = None) -> QueryComplexity:
        """
        Analyze query complexity
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query complexity metrics
        """
        # Simple complexity calculation (can be enhanced)
        depth = query.count('{')
        breadth = query.count('\n')
        
        # Calculate complexity score
        score = (
            depth * cls.NESTED_COST +
            breadth * cls.FIELD_COST
        )
        
        # Add cost for list operations
        if 'first:' in query or 'last:' in query or 'limit:' in query:
            score += cls.LIST_COST
        
        # Estimate execution time
        estimated_time = score * 0.5  # 0.5ms per complexity point
        
        # Determine if cacheable
        cache_eligible = (
            'mutation' not in query.lower() and
            'subscription' not in query.lower() and
            score < 100  # Don't cache very complex queries
        )
        
        return QueryComplexity(
            score=score,
            depth=depth,
            breadth=breadth,
            estimated_time_ms=estimated_time,
            cache_eligible=cache_eligible
        )


class QueryComplexityExtension(Extension):
    """GraphQL extension to limit query complexity"""
    
    def __init__(self, max_complexity: int = 1000):
        self.max_complexity = max_complexity
    
    async def on_request_start(self):
        """Check query complexity before execution"""
        query = self.execution_context.query
        
        if query:
            complexity = ComplexityAnalyzer.analyze(str(query))
            
            if complexity.score > self.max_complexity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query too complex. Complexity: {complexity.score}, Max: {self.max_complexity}"
                )
            
            # Store complexity for logging
            self.execution_context.context['complexity'] = complexity
    
    async def on_request_end(self):
        """Log query performance"""
        complexity = self.execution_context.context.get('complexity')
        if complexity:
            execution_time = self.execution_context.result.extensions.get('execution_time', 0)
            
            # Log slow queries
            if execution_time > 100:  # 100ms threshold
                logger.warning(
                    f"Slow GraphQL query: {execution_time}ms, Complexity: {complexity.score}"
                )


class CacheExtension(Extension):
    """GraphQL extension for field-level caching"""
    
    def __init__(self, cache: AdvancedRedisCache):
        self.cache = cache
    
    async def resolve(self, _next, root, info, **kwargs):
        """Cache field resolution"""
        field_name = info.field_name
        
        # Check if field is cacheable
        cache_directive = info.field_nodes[0].directives.get('cache')
        if not cache_directive:
            return await _next(root, info, **kwargs)
        
        # Generate cache key
        cache_key = self._generate_cache_key(field_name, root, kwargs)
        
        # Try to get from cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Resolve and cache
        result = await _next(root, info, **kwargs)
        
        # Get TTL from directive
        ttl = cache_directive.arguments.get('ttl', CacheTTL.MEDIUM)
        await self.cache.set(cache_key, result, ttl)
        
        return result
    
    def _generate_cache_key(self, field_name: str, root: Any, kwargs: Dict) -> str:
        """Generate cache key for field"""
        key_parts = [
            'gql',
            field_name,
            str(root.__class__.__name__) if root else 'root',
            json.dumps(kwargs, sort_keys=True)
        ]
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class BatchDataLoader:
    """
    Batch and deduplicate data loading
    
    Implements DataLoader pattern for N+1 query prevention
    """
    
    def __init__(self, batch_fn: Callable, max_batch_size: int = 100):
        """
        Initialize batch loader
        
        Args:
            batch_fn: Async function to load batch of items
            max_batch_size: Maximum batch size
        """
        self.batch_fn = batch_fn
        self.max_batch_size = max_batch_size
        self._queue: List[Tuple[Any, asyncio.Future]] = []
        self._cache: Dict[Any, Any] = {}
        self._batch_promise: Optional[asyncio.Task] = None
    
    async def load(self, key: Any) -> Any:
        """
        Load single item (will be batched)
        
        Args:
            key: Item key
            
        Returns:
            Loaded item
        """
        # Check cache
        if key in self._cache:
            return self._cache[key]
        
        # Create future for this request
        future = asyncio.Future()
        self._queue.append((key, future))
        
        # Schedule batch if not already scheduled
        if not self._batch_promise:
            self._batch_promise = asyncio.create_task(self._dispatch_batch())
        
        # Wait for result
        result = await future
        self._cache[key] = result
        return result
    
    async def load_many(self, keys: List[Any]) -> List[Any]:
        """Load multiple items"""
        return await asyncio.gather(*[self.load(key) for key in keys])
    
    async def _dispatch_batch(self):
        """Dispatch queued requests as batch"""
        await asyncio.sleep(0)  # Yield to collect more requests
        
        # Process queue in batches
        while self._queue:
            # Get batch
            batch = self._queue[:self.max_batch_size]
            self._queue = self._queue[self.max_batch_size:]
            
            keys = [key for key, _ in batch]
            futures = [future for _, future in batch]
            
            try:
                # Load batch
                results = await self.batch_fn(keys)
                
                # Map results to futures
                result_map = {k: v for k, v in zip(keys, results)}
                
                for key, future in batch:
                    if key in result_map:
                        future.set_result(result_map[key])
                    else:
                        future.set_exception(KeyError(f"Key not found: {key}"))
                        
            except Exception as e:
                # Set exception for all futures
                for _, future in batch:
                    future.set_exception(e)
        
        self._batch_promise = None
    
    def clear(self, key: Any = None):
        """Clear cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()


class ResponseOptimizer:
    """
    Optimize API responses with compression and streaming
    """
    
    @staticmethod
    def get_best_compression(accept_encoding: str) -> CompressionType:
        """
        Determine best compression based on Accept-Encoding
        
        Args:
            accept_encoding: Accept-Encoding header value
            
        Returns:
            Best compression type
        """
        if not accept_encoding:
            return CompressionType.NONE
        
        accept_encoding = accept_encoding.lower()
        
        # Prefer Brotli > Gzip > None
        if 'br' in accept_encoding:
            return CompressionType.BROTLI
        elif 'gzip' in accept_encoding:
            return CompressionType.GZIP
        else:
            return CompressionType.NONE
    
    @staticmethod
    def compress_response(
        content: bytes,
        compression_type: CompressionType,
        quality: int = 11
    ) -> bytes:
        """
        Compress response content
        
        Args:
            content: Content to compress
            compression_type: Type of compression
            quality: Compression quality (1-11 for Brotli, 1-9 for Gzip)
            
        Returns:
            Compressed content
        """
        if compression_type == CompressionType.BROTLI:
            return brotli.compress(content, quality=min(quality, 11))
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(content, compresslevel=min(quality, 9))
        else:
            return content
    
    @classmethod
    async def create_optimized_response(
        cls,
        data: Any,
        request: Request,
        cache_ttl: Optional[int] = None,
        enable_compression: bool = True
    ) -> Response:
        """
        Create optimized response with compression and caching headers
        
        Args:
            data: Response data
            request: FastAPI request
            cache_ttl: Cache TTL in seconds
            enable_compression: Enable response compression
            
        Returns:
            Optimized response
        """
        # Serialize data
        if isinstance(data, (dict, list)):
            content = json.dumps(data, separators=(',', ':')).encode('utf-8')
            content_type = 'application/json'
        else:
            content = str(data).encode('utf-8')
            content_type = 'text/plain'
        
        # Determine compression
        headers = {}
        if enable_compression and len(content) > 1000:  # Only compress if > 1KB
            accept_encoding = request.headers.get('accept-encoding', '')
            compression_type = cls.get_best_compression(accept_encoding)
            
            if compression_type != CompressionType.NONE:
                content = cls.compress_response(content, compression_type)
                headers['Content-Encoding'] = compression_type.value
        
        # Add cache headers
        if cache_ttl is not None:
            if cache_ttl == 0:
                headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            else:
                headers['Cache-Control'] = f'public, max-age={cache_ttl}'
                headers['ETag'] = f'"{hashlib.md5(content).hexdigest()}"'
        
        # Add performance headers
        headers['X-Content-Type-Options'] = 'nosniff'
        headers['Vary'] = 'Accept-Encoding'
        
        return Response(
            content=content,
            media_type=content_type,
            headers=headers
        )


class PaginationOptimizer:
    """
    Optimize pagination for large datasets
    """
    
    @staticmethod
    def get_optimal_page_size(
        total_items: int,
        requested_size: int,
        max_size: int = 100,
        min_size: int = 10
    ) -> int:
        """
        Calculate optimal page size
        
        Args:
            total_items: Total number of items
            requested_size: Requested page size
            max_size: Maximum allowed size
            min_size: Minimum allowed size
            
        Returns:
            Optimal page size
        """
        # Clamp to min/max
        page_size = max(min_size, min(requested_size, max_size))
        
        # Adjust based on total items
        if total_items < 100:
            # Small dataset - allow larger pages
            page_size = min(requested_size, total_items)
        elif total_items > 10000:
            # Large dataset - prefer smaller pages
            page_size = min(page_size, 50)
        
        return page_size
    
    @staticmethod
    def create_cursor(
        offset: int,
        timestamp: Optional[datetime] = None,
        id: Optional[str] = None
    ) -> str:
        """
        Create opaque cursor for pagination
        
        Args:
            offset: Current offset
            timestamp: Optional timestamp for time-based pagination
            id: Optional ID for keyset pagination
            
        Returns:
            Encoded cursor string
        """
        cursor_data = {
            'o': offset,
            't': timestamp.isoformat() if timestamp else None,
            'i': id
        }
        
        # Encode as base64
        import base64
        cursor_json = json.dumps(cursor_data, separators=(',', ':'))
        cursor_bytes = cursor_json.encode('utf-8')
        return base64.urlsafe_b64encode(cursor_bytes).decode('utf-8')
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """
        Decode pagination cursor
        
        Args:
            cursor: Encoded cursor string
            
        Returns:
            Cursor data dictionary
        """
        import base64
        
        try:
            cursor_bytes = base64.urlsafe_b64decode(cursor.encode('utf-8'))
            cursor_json = cursor_bytes.decode('utf-8')
            cursor_data = json.loads(cursor_json)
            
            # Parse timestamp if present
            if cursor_data.get('t'):
                cursor_data['t'] = datetime.fromisoformat(cursor_data['t'])
            
            return cursor_data
        except Exception:
            return {'o': 0, 't': None, 'i': None}
    
    @staticmethod
    def create_page_info(
        total_items: int,
        current_offset: int,
        page_size: int,
        items_in_page: int
    ) -> Dict[str, Any]:
        """
        Create pagination metadata
        
        Args:
            total_items: Total number of items
            current_offset: Current offset
            page_size: Page size
            items_in_page: Number of items in current page
            
        Returns:
            Page info dictionary
        """
        has_next = (current_offset + items_in_page) < total_items
        has_previous = current_offset > 0
        
        return {
            'total_items': total_items,
            'page_size': page_size,
            'current_page': (current_offset // page_size) + 1,
            'total_pages': (total_items + page_size - 1) // page_size,
            'has_next_page': has_next,
            'has_previous_page': has_previous,
            'next_cursor': PaginationOptimizer.create_cursor(
                current_offset + page_size
            ) if has_next else None,
            'previous_cursor': PaginationOptimizer.create_cursor(
                max(0, current_offset - page_size)
            ) if has_previous else None
        }


# GraphQL Schema Types
@strawberry.type
class PortfolioType:
    """GraphQL type for portfolio data"""
    id: str
    user_id: str
    total_value: float
    total_invested: float
    total_return: float
    return_percentage: float
    last_updated: datetime
    
    @strawberry.field
    async def investments(self, info: Info) -> List['InvestmentType']:
        """Resolve investments using DataLoader"""
        loader = info.context['loaders']['investments']
        return await loader.load(self.id)
    
    @strawberry.field
    async def performance_metrics(self, info: Info) -> 'PerformanceMetricsType':
        """Resolve performance metrics"""
        loader = info.context['loaders']['metrics']
        return await loader.load(self.id)


@strawberry.type
class InvestmentType:
    """GraphQL type for investment data"""
    id: str
    portfolio_id: str
    asset_class: str
    symbol: str
    quantity: float
    current_value: float
    cost_basis: float
    
    @strawberry.field
    async def market_data(self, info: Info) -> 'MarketDataType':
        """Resolve current market data"""
        loader = info.context['loaders']['market_data']
        return await loader.load(self.symbol)


@strawberry.type
class MarketDataType:
    """GraphQL type for market data"""
    symbol: str
    price: float
    change: float
    change_percentage: float
    volume: int
    timestamp: datetime


@strawberry.type
class PerformanceMetricsType:
    """GraphQL type for performance metrics"""
    portfolio_id: str
    volatility: float
    sharpe_ratio: float
    beta: float
    alpha: float
    max_drawdown: float


@strawberry.type
class PaginatedPortfolios:
    """Paginated portfolio response"""
    items: List[PortfolioType]
    page_info: 'PageInfo'


@strawberry.type
class PageInfo:
    """Pagination information"""
    total_items: int
    page_size: int
    current_page: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    next_cursor: Optional[str]
    previous_cursor: Optional[str]


@strawberry.type
class Query:
    """GraphQL Query root"""
    
    @strawberry.field
    async def portfolio(
        self,
        info: Info,
        user_id: str
    ) -> Optional[PortfolioType]:
        """Get user portfolio"""
        # Implementation would fetch from database
        pass
    
    @strawberry.field
    async def portfolios(
        self,
        info: Info,
        first: int = 20,
        after: Optional[str] = None
    ) -> PaginatedPortfolios:
        """Get paginated portfolios"""
        # Decode cursor
        cursor_data = PaginationOptimizer.decode_cursor(after) if after else {'o': 0}
        offset = cursor_data['o']
        
        # Get optimal page size
        page_size = PaginationOptimizer.get_optimal_page_size(
            total_items=1000,  # Would come from DB count
            requested_size=first
        )
        
        # Fetch data (implementation would query database)
        items = []  # Fetch from DB with offset and limit
        
        # Create page info
        page_info = PaginationOptimizer.create_page_info(
            total_items=1000,
            current_offset=offset,
            page_size=page_size,
            items_in_page=len(items)
        )
        
        return PaginatedPortfolios(items=items, page_info=PageInfo(**page_info))
    
    @strawberry.field
    async def market_data(
        self,
        info: Info,
        symbols: List[str]
    ) -> List[MarketDataType]:
        """Get market data for multiple symbols"""
        loader = info.context['loaders']['market_data']
        return await loader.load_many(symbols)


@strawberry.type
class Mutation:
    """GraphQL Mutation root"""
    
    @strawberry.mutation
    async def update_portfolio(
        self,
        info: Info,
        portfolio_id: str,
        updates: Dict[str, Any]
    ) -> PortfolioType:
        """Update portfolio"""
        # Implementation would update database
        pass


# Create GraphQL app
def create_graphql_app(
    cache: AdvancedRedisCache,
    max_complexity: int = 1000
) -> GraphQLRouter:
    """
    Create optimized GraphQL application
    
    Args:
        cache: Redis cache instance
        max_complexity: Maximum query complexity
        
    Returns:
        GraphQL router
    """
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            QueryComplexityExtension(max_complexity),
            CacheExtension(cache)
        ]
    )
    
    return GraphQLRouter(
        schema,
        context_getter=lambda: {
            'cache': cache,
            'loaders': create_data_loaders()
        }
    )


def create_data_loaders() -> Dict[str, BatchDataLoader]:
    """Create DataLoaders for batching"""
    
    async def load_investments(portfolio_ids: List[str]) -> List[List[InvestmentType]]:
        # Batch load investments for multiple portfolios
        # Implementation would query database
        return []
    
    async def load_market_data(symbols: List[str]) -> List[MarketDataType]:
        # Batch load market data for multiple symbols
        # Implementation would query market data API
        return []
    
    async def load_metrics(portfolio_ids: List[str]) -> List[PerformanceMetricsType]:
        # Batch load performance metrics
        # Implementation would query database
        return []
    
    return {
        'investments': BatchDataLoader(load_investments),
        'market_data': BatchDataLoader(load_market_data),
        'metrics': BatchDataLoader(load_metrics)
    }