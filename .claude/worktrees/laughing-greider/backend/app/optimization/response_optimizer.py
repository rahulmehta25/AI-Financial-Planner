"""
API Response Optimizer for Ultra-Low Latency

This module ensures API response times meet SLA:
- p50 < 100ms
- p95 < 300ms  
- p99 < 500ms

Optimization techniques:
- Response compression (gzip, brotli)
- Partial response / field filtering
- Response streaming for large datasets
- ETag-based caching
- HTTP/2 Server Push
- Response pre-computation
"""

import asyncio
import gzip
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Set, Union

import brotli
import orjson
from fastapi import Request, Response, Header
from fastapi.responses import StreamingResponse, ORJSONResponse
from prometheus_client import Counter, Histogram, Summary
from pydantic import BaseModel
import numpy as np


# Metrics
response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['endpoint', 'method'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
response_size = Histogram(
    'api_response_size_bytes',
    'API response size',
    ['endpoint', 'compression']
)
cache_efficiency = Counter(
    'api_cache_efficiency',
    'Cache hit/miss for API responses',
    ['endpoint', 'result']
)
compression_ratio = Summary(
    'api_compression_ratio',
    'Compression ratio achieved',
    ['algorithm']
)


class CompressionAlgorithm(Enum):
    """Supported compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "br"
    ZSTD = "zstd"


class ResponseFormat(Enum):
    """Response format options"""
    JSON = "json"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"
    CSV = "csv"


@dataclass
class PerformanceTarget:
    """Performance SLA targets"""
    p50_ms: float = 100  # 50th percentile target
    p95_ms: float = 300  # 95th percentile target
    p99_ms: float = 500  # 99th percentile target
    max_response_size_mb: float = 10  # Maximum response size
    
    def is_meeting_sla(self, metrics: Dict[str, float]) -> bool:
        """Check if current metrics meet SLA"""
        return (
            metrics.get('p50', float('inf')) <= self.p50_ms and
            metrics.get('p95', float('inf')) <= self.p95_ms and
            metrics.get('p99', float('inf')) <= self.p99_ms
        )


@dataclass
class OptimizationConfig:
    """Response optimization configuration"""
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress responses > 1KB
    compression_level: int = 6  # 1-9, higher = better compression
    preferred_compression: CompressionAlgorithm = CompressionAlgorithm.BROTLI
    
    enable_streaming: bool = True
    streaming_threshold: int = 10 * 1024 * 1024  # Stream responses > 10MB
    chunk_size: int = 8192  # 8KB chunks
    
    enable_etag: bool = True
    enable_partial_response: bool = True
    enable_response_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    enable_http2_push: bool = False
    enable_precomputation: bool = True
    
    max_response_size: int = 50 * 1024 * 1024  # 50MB max
    response_timeout: float = 30.0  # 30 seconds timeout


class ResponseCompressor:
    """High-performance response compression"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        
    def compress(
        self,
        data: bytes,
        accept_encoding: Optional[str] = None,
        algorithm: Optional[CompressionAlgorithm] = None
    ) -> Tuple[bytes, str]:
        """
        Compress data using the best available algorithm
        
        Args:
            data: Raw data to compress
            accept_encoding: Client's Accept-Encoding header
            algorithm: Force specific algorithm
            
        Returns:
            Tuple of (compressed_data, encoding)
        """
        if not self.config.enable_compression:
            return data, "identity"
            
        if len(data) < self.config.compression_threshold:
            return data, "identity"
            
        # Determine algorithm
        if algorithm:
            selected_algorithm = algorithm
        else:
            selected_algorithm = self._select_algorithm(accept_encoding)
            
        start_time = time.time()
        original_size = len(data)
        
        # Compress based on algorithm
        if selected_algorithm == CompressionAlgorithm.BROTLI:
            compressed = brotli.compress(
                data,
                quality=self.config.compression_level,
                mode=brotli.MODE_TEXT
            )
            encoding = "br"
        elif selected_algorithm == CompressionAlgorithm.GZIP:
            buffer = BytesIO()
            with gzip.GzipFile(
                fileobj=buffer,
                mode='wb',
                compresslevel=self.config.compression_level
            ) as gz:
                gz.write(data)
            compressed = buffer.getvalue()
            encoding = "gzip"
        else:
            return data, "identity"
            
        # Calculate compression ratio
        compressed_size = len(compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 1
        
        compression_ratio.labels(algorithm=encoding).observe(ratio)
        
        # Only use compression if it's beneficial
        if compressed_size >= original_size * 0.9:  # Less than 10% savings
            return data, "identity"
            
        return compressed, encoding
        
    def _select_algorithm(self, accept_encoding: Optional[str]) -> CompressionAlgorithm:
        """Select best compression algorithm based on client support"""
        if not accept_encoding:
            return CompressionAlgorithm.NONE
            
        accept_encoding = accept_encoding.lower()
        
        # Prefer Brotli > Gzip > None
        if "br" in accept_encoding and self.config.preferred_compression == CompressionAlgorithm.BROTLI:
            return CompressionAlgorithm.BROTLI
        elif "gzip" in accept_encoding:
            return CompressionAlgorithm.GZIP
        else:
            return CompressionAlgorithm.NONE


class ResponseStreamer:
    """Stream large responses efficiently"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        
    async def stream_json_array(
        self,
        data_generator: AsyncIterator,
        chunk_size: int = 100
    ) -> StreamingResponse:
        """
        Stream JSON array response
        
        Args:
            data_generator: Async generator yielding items
            chunk_size: Number of items per chunk
            
        Returns:
            Streaming response
        """
        async def generate():
            yield b'['
            
            first = True
            buffer = []
            
            async for item in data_generator:
                if not first:
                    buffer.append(b',')
                else:
                    first = False
                    
                # Serialize item
                buffer.append(orjson.dumps(item))
                
                # Flush buffer when full
                if len(buffer) >= chunk_size:
                    yield b''.join(buffer)
                    buffer = []
                    
            # Flush remaining buffer
            if buffer:
                yield b''.join(buffer)
                
            yield b']'
            
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={
                "X-Content-Stream": "true",
                "Cache-Control": "no-cache"
            }
        )
        
    async def stream_csv(
        self,
        headers: List[str],
        data_generator: AsyncIterator[List],
        chunk_size: int = 1000
    ) -> StreamingResponse:
        """Stream CSV response"""
        async def generate():
            # Yield headers
            yield ','.join(headers).encode() + b'\n'
            
            buffer = []
            for row in data_generator:
                buffer.append(','.join(str(v) for v in row).encode() + b'\n')
                
                if len(buffer) >= chunk_size:
                    yield b''.join(buffer)
                    buffer = []
                    
            if buffer:
                yield b''.join(buffer)
                
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=export.csv"
            }
        )


class ETagManager:
    """ETag-based caching for responses"""
    
    def __init__(self):
        self.etag_cache: Dict[str, Tuple[str, datetime]] = {}
        
    def generate_etag(self, data: Union[str, bytes, dict]) -> str:
        """Generate ETag for response data"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            data = data.encode()
            
        return f'W/"{hashlib.md5(data).hexdigest()}"'
        
    def check_etag(
        self,
        request_etag: Optional[str],
        current_etag: str
    ) -> bool:
        """Check if client's ETag matches current"""
        if not request_etag:
            return False
            
        # Handle weak ETags
        request_etag = request_etag.replace('W/', '').strip('"')
        current_etag = current_etag.replace('W/', '').strip('"')
        
        return request_etag == current_etag


class FieldFilter:
    """Implement partial response with field filtering"""
    
    @staticmethod
    def filter_response(
        data: Union[dict, list],
        fields: Optional[str] = None,
        exclude: Optional[str] = None
    ) -> Union[dict, list]:
        """
        Filter response fields
        
        Args:
            data: Response data
            fields: Comma-separated fields to include
            exclude: Comma-separated fields to exclude
            
        Returns:
            Filtered data
        """
        if not fields and not exclude:
            return data
            
        if isinstance(data, list):
            return [
                FieldFilter._filter_dict(item, fields, exclude)
                for item in data
            ]
        else:
            return FieldFilter._filter_dict(data, fields, exclude)
            
    @staticmethod
    def _filter_dict(
        data: dict,
        fields: Optional[str],
        exclude: Optional[str]
    ) -> dict:
        """Filter a dictionary"""
        if fields:
            field_set = set(fields.split(','))
            return {k: v for k, v in data.items() if k in field_set}
        elif exclude:
            exclude_set = set(exclude.split(','))
            return {k: v for k, v in data.items() if k not in exclude_set}
        return data


class ResponseOptimizer:
    """Main response optimizer ensuring SLA compliance"""
    
    def __init__(
        self,
        config: Optional[OptimizationConfig] = None,
        targets: Optional[PerformanceTarget] = None
    ):
        self.config = config or OptimizationConfig()
        self.targets = targets or PerformanceTarget()
        
        self.compressor = ResponseCompressor(self.config)
        self.streamer = ResponseStreamer(self.config)
        self.etag_manager = ETagManager()
        
        # Response time tracking
        self.response_times: Dict[str, List[float]] = {}
        
        # Precomputed responses cache
        self.precomputed_cache: Dict[str, Tuple[Any, datetime]] = {}
        
    def optimize_response(
        self,
        request: Request,
        data: Any,
        endpoint: str,
        format: ResponseFormat = ResponseFormat.JSON
    ) -> Response:
        """
        Optimize response for performance
        
        Args:
            request: FastAPI request
            data: Response data
            endpoint: API endpoint name
            format: Response format
            
        Returns:
            Optimized response
        """
        start_time = time.time()
        
        # Check precomputed cache
        if self.config.enable_precomputation:
            cached = self._get_precomputed(endpoint, request.url.query)
            if cached is not None:
                data = cached
                cache_efficiency.labels(endpoint=endpoint, result='hit').inc()
            else:
                cache_efficiency.labels(endpoint=endpoint, result='miss').inc()
                
        # Apply field filtering if requested
        if self.config.enable_partial_response:
            fields = request.query_params.get('fields')
            exclude = request.query_params.get('exclude')
            if fields or exclude:
                data = FieldFilter.filter_response(data, fields, exclude)
                
        # Serialize based on format
        if format == ResponseFormat.JSON:
            content = orjson.dumps(data)
            media_type = "application/json"
        else:
            content = json.dumps(data).encode()
            media_type = "application/json"
            
        # Generate ETag
        etag = None
        if self.config.enable_etag:
            etag = self.etag_manager.generate_etag(content)
            
            # Check If-None-Match header
            if_none_match = request.headers.get('If-None-Match')
            if self.etag_manager.check_etag(if_none_match, etag):
                # Return 304 Not Modified
                return Response(
                    status_code=304,
                    headers={'ETag': etag}
                )
                
        # Check if streaming is needed
        if (self.config.enable_streaming and 
            len(content) > self.config.streaming_threshold):
            # Use streaming for large responses
            return self._create_streaming_response(content, media_type, etag)
            
        # Compress response
        accept_encoding = request.headers.get('Accept-Encoding')
        compressed_content, encoding = self.compressor.compress(
            content,
            accept_encoding
        )
        
        # Create response
        headers = {
            'Content-Length': str(len(compressed_content)),
            'X-Response-Time': f"{(time.time() - start_time) * 1000:.2f}ms"
        }
        
        if encoding != "identity":
            headers['Content-Encoding'] = encoding
            
        if etag:
            headers['ETag'] = etag
            headers['Cache-Control'] = f"private, max-age={self.config.cache_ttl}"
            
        # Track response time
        response_time_ms = (time.time() - start_time) * 1000
        self._track_response_time(endpoint, response_time_ms)
        
        # Record metrics
        response_time.labels(
            endpoint=endpoint,
            method=request.method
        ).observe(response_time_ms / 1000)
        
        response_size.labels(
            endpoint=endpoint,
            compression=encoding
        ).observe(len(compressed_content))
        
        return Response(
            content=compressed_content,
            media_type=media_type,
            headers=headers
        )
        
    def _create_streaming_response(
        self,
        content: bytes,
        media_type: str,
        etag: Optional[str]
    ) -> StreamingResponse:
        """Create a streaming response for large data"""
        async def generate():
            chunk_size = self.config.chunk_size
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]
                
        headers = {}
        if etag:
            headers['ETag'] = etag
            
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers=headers
        )
        
    def _get_precomputed(
        self,
        endpoint: str,
        query_params: Optional[str]
    ) -> Optional[Any]:
        """Get precomputed response from cache"""
        cache_key = f"{endpoint}:{query_params or ''}"
        
        if cache_key in self.precomputed_cache:
            data, timestamp = self.precomputed_cache[cache_key]
            
            # Check TTL
            if (datetime.utcnow() - timestamp).seconds < self.config.cache_ttl:
                return data
                
            # Expired
            del self.precomputed_cache[cache_key]
            
        return None
        
    async def precompute_response(
        self,
        endpoint: str,
        compute_func: Callable,
        query_params: Optional[str] = None
    ) -> None:
        """
        Precompute response in background
        
        Args:
            endpoint: API endpoint
            compute_func: Function to compute response
            query_params: Query parameters
        """
        cache_key = f"{endpoint}:{query_params or ''}"
        
        # Compute response
        if asyncio.iscoroutinefunction(compute_func):
            data = await compute_func()
        else:
            data = compute_func()
            
        # Cache result
        self.precomputed_cache[cache_key] = (data, datetime.utcnow())
        
    def _track_response_time(self, endpoint: str, time_ms: float) -> None:
        """Track response time for SLA monitoring"""
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
            
        # Keep last 1000 response times
        times = self.response_times[endpoint]
        times.append(time_ms)
        if len(times) > 1000:
            times.pop(0)
            
    def get_performance_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            endpoint: Specific endpoint or None for all
            
        Returns:
            Performance metrics dictionary
        """
        if endpoint and endpoint in self.response_times:
            times = self.response_times[endpoint]
        else:
            # Aggregate all endpoints
            times = []
            for endpoint_times in self.response_times.values():
                times.extend(endpoint_times)
                
        if not times:
            return {
                'p50': 0,
                'p95': 0,
                'p99': 0,
                'mean': 0,
                'count': 0,
                'meeting_sla': True
            }
            
        metrics = {
            'p50': np.percentile(times, 50),
            'p95': np.percentile(times, 95),
            'p99': np.percentile(times, 99),
            'mean': np.mean(times),
            'count': len(times)
        }
        
        metrics['meeting_sla'] = self.targets.is_meeting_sla(metrics)
        
        return metrics
        
    def auto_tune(self) -> Dict[str, Any]:
        """
        Auto-tune optimization settings based on metrics
        
        Returns:
            Tuning recommendations
        """
        recommendations = []
        
        metrics = self.get_performance_metrics()
        
        # Check if we're meeting SLA
        if not metrics['meeting_sla']:
            # Increase compression threshold if p99 is high
            if metrics['p99'] > self.targets.p99_ms:
                recommendations.append({
                    'setting': 'compression_threshold',
                    'current': self.config.compression_threshold,
                    'recommended': self.config.compression_threshold * 2,
                    'reason': f"p99 ({metrics['p99']:.1f}ms) exceeds target ({self.targets.p99_ms}ms)"
                })
                
            # Enable more aggressive caching
            if not self.config.enable_precomputation:
                recommendations.append({
                    'setting': 'enable_precomputation',
                    'current': False,
                    'recommended': True,
                    'reason': "Enable precomputation to improve response times"
                })
                
            # Reduce compression level for faster processing
            if self.config.compression_level > 3:
                recommendations.append({
                    'setting': 'compression_level',
                    'current': self.config.compression_level,
                    'recommended': 3,
                    'reason': "Reduce compression level for faster processing"
                })
                
        return {
            'current_metrics': metrics,
            'recommendations': recommendations,
            'sla_status': 'PASS' if metrics['meeting_sla'] else 'FAIL'
        }


# FastAPI middleware
def optimize_api_response(
    config: Optional[OptimizationConfig] = None,
    targets: Optional[PerformanceTarget] = None
):
    """
    Decorator for optimizing FastAPI endpoint responses
    
    Args:
        config: Optimization configuration
        targets: Performance targets
    """
    optimizer = ResponseOptimizer(config, targets)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Execute endpoint
            result = await func(request, *args, **kwargs) if asyncio.iscoroutinefunction(func) else func(request, *args, **kwargs)
            
            # Optimize response
            endpoint = func.__name__
            return optimizer.optimize_response(request, result, endpoint)
            
        return wrapper
    return decorator