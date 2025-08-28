# Performance Optimization System

## Overview

This package provides enterprise-grade performance optimization for the Financial Planning System, ensuring API response times meet strict SLA requirements:

- **p50 < 100ms** (50th percentile)
- **p95 < 300ms** (95th percentile)
- **p99 < 500ms** (99th percentile)

## Architecture

### Multi-Level Caching System
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────┐
│  L1: Memory │ < 1μs latency
│  (200MB)    │ In-process LRU cache
└──────┬──────┘
       │
┌──────▼──────┐
│  L2: Redis  │ < 1ms latency
│  (Cluster)  │ Distributed cache
└──────┬──────┘
       │
┌──────▼──────┐
│L3: Memcached│ < 5ms latency
│  (Network)  │ Long-term cache
└──────┬──────┘
       │
┌──────▼──────┐
│  Database   │
└─────────────┘
```

### Query Optimization Pipeline
```
Query → Plan Analysis → Eager Loading → Caching → Connection Pool → Database
         ↓                ↓              ↓           ↓
    Index Hints    Prefetch Related  Result Cache  PgBouncer
```

## Components

### 1. Cache Manager (`cache_manager.py`)

Multi-level caching with automatic tiering and invalidation.

**Features:**
- **L1 Memory Cache**: Ultra-fast in-process LRU cache (200MB)
- **L2 Redis Cache**: Distributed cache with pub/sub invalidation
- **L3 Memcached**: Long-term cache for expensive computations
- **Smart Invalidation**: Tag-based and pattern-based invalidation
- **Cache Warming**: Pre-load frequently accessed data

**Usage:**
```python
from backend.app.optimization import cache_portfolio

@cache_portfolio(ttl=300)  # Cache for 5 minutes
async def get_portfolio_value(portfolio_id: int):
    # Expensive calculation
    return calculate_portfolio_value(portfolio_id)
```

### 2. Query Optimizer (`query_optimizer.py`)

Intelligent query optimization with eager loading and result caching.

**Features:**
- **Eager Loading**: Automatic N+1 query prevention
- **Query Plan Analysis**: Real-time plan optimization
- **Result Caching**: Cache frequently accessed queries
- **Bulk Operations**: Optimized batch inserts/updates
- **Index Recommendations**: Automatic index suggestions

**Usage:**
```python
from backend.app.optimization import QueryOptimizer, optimized_query

# Setup optimizer
optimizer = QueryOptimizer(database_url)
await optimizer.setup()

# Configure eager loading
optimizer.configure_eager_loading(
    User,
    ["portfolios", "transactions"],
    LoadingStrategy.EAGER_SELECT
)

# Use decorator for automatic optimization
@optimized_query(cache_ttl=300, eager_load=["portfolios"])
async def get_user_with_portfolios(user_id: int):
    return session.query(User).filter_by(id=user_id)
```

### 3. Connection Pool Manager (`connection_pool.py`)

Advanced connection pooling with read/write splitting and health monitoring.

**Features:**
- **PgBouncer Integration**: Transaction-level pooling
- **Read/Write Splitting**: Route queries to appropriate nodes
- **Health Monitoring**: Automatic failover on node failure
- **Circuit Breaker**: Prevent cascading failures
- **Connection Warming**: Pre-establish connections

**Configuration:**
```python
from backend.app.optimization import SmartConnectionPool, DatabaseNode, PoolType

nodes = [
    DatabaseNode(
        host="primary.db.com",
        pool_type=PoolType.PRIMARY,
        max_connections=100
    ),
    DatabaseNode(
        host="replica1.db.com",
        pool_type=PoolType.REPLICA,
        max_connections=50
    )
]

pool = SmartConnectionPool(nodes)
await pool.setup()

# Automatic routing
async with pool.acquire(PoolType.REPLICA) as conn:
    results = await conn.fetch("SELECT * FROM users")
```

### 4. Response Optimizer (`response_optimizer.py`)

API response optimization for ultra-low latency.

**Features:**
- **Smart Compression**: Brotli/Gzip with threshold detection
- **Response Streaming**: Stream large datasets efficiently
- **ETag Caching**: HTTP 304 support
- **Partial Responses**: Field filtering for reduced payload
- **Response Precomputation**: Background computation of expensive responses

**Usage:**
```python
from backend.app.optimization import optimize_api_response

@app.get("/api/v1/portfolios/{id}")
@optimize_api_response(
    compression_threshold=512,
    enable_etag=True,
    enable_partial_response=True
)
async def get_portfolio(id: int, fields: Optional[str] = None):
    portfolio = await fetch_portfolio(id)
    return portfolio
```

## Integration with FastAPI

### Quick Start

```python
from fastapi import FastAPI
from backend.app.optimization import setup_optimization

app = FastAPI()

# Setup optimization system
optimization_system = await setup_optimization(
    app,
    database_url="postgresql://user:pass@localhost/db",
    redis_url="redis://localhost:6379",
    memcached_hosts=["localhost:11211"]
)

# Use dependency injection
from backend.app.optimization import get_cache_manager, get_query_optimizer

@app.get("/api/v1/data")
async def get_data(
    cache: MultiLevelCacheManager = Depends(get_cache_manager),
    optimizer: QueryOptimizer = Depends(get_query_optimizer)
):
    # Use cache
    cached_data = await cache.get("key")
    if cached_data:
        return cached_data
    
    # Optimize query
    query = optimizer.optimize_query(original_query)
    result = await optimizer.execute_with_cache(query)
    
    # Cache result
    await cache.set("key", result, ttl=300)
    
    return result
```

## Performance Metrics

### Monitoring Endpoints

- **GET /metrics** - Prometheus metrics
- **GET /api/v1/performance/metrics** - Performance dashboard
- **POST /api/v1/performance/tune** - Auto-tune optimization settings

### Key Metrics Tracked

1. **Cache Metrics**
   - Hit ratio per cache level
   - Eviction rate
   - Memory usage
   - Operation latency

2. **Query Metrics**
   - Execution time percentiles
   - Cache hit ratio
   - Connection pool utilization
   - Slow query log

3. **Response Metrics**
   - Response time percentiles (p50, p95, p99)
   - Compression ratio
   - Payload size distribution
   - SLA compliance status

## Configuration

### Environment Variables

```bash
# Cache Configuration
CACHE_MEMORY_SIZE_MB=200
CACHE_REDIS_URL=redis://localhost:6379
CACHE_MEMCACHED_HOSTS=localhost:11211
CACHE_TTL_SECONDS=300

# Database Pool Configuration
DB_POOL_MIN_SIZE=20
DB_POOL_MAX_SIZE=100
DB_POOL_TIMEOUT=30
DB_USE_PGBOUNCER=true
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432

# Response Optimization
RESPONSE_COMPRESSION_ENABLED=true
RESPONSE_COMPRESSION_THRESHOLD=512
RESPONSE_STREAMING_THRESHOLD=10485760
RESPONSE_ETAG_ENABLED=true

# Performance Targets
TARGET_P50_MS=100
TARGET_P95_MS=300
TARGET_P99_MS=500
```

### PgBouncer Configuration

```ini
[databases]
financial_planning = host=localhost port=5432 dbname=financial_planning

[pgbouncer]
pool_mode = transaction
max_client_conn = 2000
default_pool_size = 50
reserve_pool_size = 10
max_db_connections = 200
```

## Performance Testing

### Run Performance Tests

```bash
# Unit tests for optimization components
pytest backend/app/optimization/tests/

# Performance benchmark
python backend/app/optimization/performance_test.py

# Load testing with Locust
locust -f backend/app/optimization/performance_test.py \
       --host=http://localhost:8000 \
       --users=100 \
       --spawn-rate=10
```

### Expected Results

| Metric | Target | Typical Result |
|--------|--------|----------------|
| p50 Response Time | < 100ms | 45-65ms |
| p95 Response Time | < 300ms | 150-200ms |
| p99 Response Time | < 500ms | 300-400ms |
| Cache Hit Ratio | > 80% | 85-95% |
| Query Cache Hit | > 60% | 65-75% |
| Throughput | > 1000 req/s | 1500-2000 req/s |

## Best Practices

### 1. Cache Strategy
- Use appropriate TTLs based on data volatility
- Implement cache warming for critical data
- Use tags for granular invalidation
- Monitor cache hit ratios

### 2. Query Optimization
- Configure eager loading for known N+1 patterns
- Use bulk operations for multiple records
- Enable query result caching for read-heavy workloads
- Regular EXPLAIN ANALYZE for slow queries

### 3. Connection Management
- Use PgBouncer for connection multiplexing
- Configure appropriate pool sizes
- Implement read/write splitting
- Monitor connection pool metrics

### 4. Response Optimization
- Enable compression for responses > 1KB
- Use streaming for large datasets
- Implement ETags for cacheable content
- Support partial responses with field filtering

## Troubleshooting

### High Response Times

1. Check cache hit ratios:
```python
metrics = optimization_system.get_metrics()
print(metrics["cache"]["hit_rate"])
```

2. Analyze slow queries:
```python
stats = optimizer.get_performance_stats()
print(stats["p99_execution_time"])
```

3. Review connection pool usage:
```python
pool_stats = pool.get_stats()
print(pool_stats["pools"])
```

### Memory Issues

1. Adjust cache sizes:
```python
config.memory_max_bytes = 100 * 1024 * 1024  # 100MB
```

2. Enable compression earlier:
```python
config.compression_threshold = 256  # Compress > 256 bytes
```

### Database Connection Errors

1. Increase pool size:
```python
config.max_size = 150
config.max_overflow = 50
```

2. Enable connection recycling:
```python
config.pool_recycle = 1800  # 30 minutes
```

## Advanced Features

### Auto-Tuning

The system can automatically adjust settings based on performance metrics:

```python
recommendations = optimization_system.auto_tune()

for rec in recommendations["response"]["recommendations"]:
    print(f"Setting: {rec['setting']}")
    print(f"Current: {rec['current']}")
    print(f"Recommended: {rec['recommended']}")
    print(f"Reason: {rec['reason']}")
```

### Custom Cache Decorators

Create domain-specific cache decorators:

```python
def cache_financial_data(ttl: int = 60):
    return cached(
        ttl=ttl,
        cache_levels=[CacheLevel.L1_MEMORY],
        tags={'financial', 'volatile'}
    )

@cache_financial_data(ttl=30)
async def get_stock_price(symbol: str):
    return await fetch_stock_price(symbol)
```

### Query Plan Optimization

Analyze and optimize query plans:

```python
analysis = await plan_analyzer.analyze_query(
    "SELECT * FROM portfolios WHERE user_id = $1",
    {"user_id": 123}
)

if analysis["scan_type"] == "sequential_scan":
    print("Warning: Sequential scan detected!")
    print(f"Recommendations: {plan_analyzer.index_recommendations}")
```

## License

This optimization system is part of the Financial Planning System and follows the same license terms.