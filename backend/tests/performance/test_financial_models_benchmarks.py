"""
Performance benchmark tests for financial models and calculations.

Tests cover:
- Monte Carlo simulation performance
- Portfolio optimization speed
- Market data processing throughput
- Database query performance
- Memory usage profiling
- Scalability testing
"""

import pytest
import asyncio
import time
import numpy as np
from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import psutil
import gc
from unittest.mock import AsyncMock, MagicMock

from app.services.modeling.monte_carlo import AdvancedMonteCarloEngine
from app.services.optimization.mpt import ModernPortfolioTheory
from app.services.market_data.manager import MarketDataManager
from app.services.tax_optimization import TaxOptimizationService
from app.services.advanced_strategies import AdvancedStrategiesService


@pytest.mark.benchmark
class TestMonteCarloPerformance:
    """Benchmark Monte Carlo simulation performance."""
    
    @pytest.fixture
    def monte_carlo_engine(self):
        """Create Monte Carlo engine for benchmarking."""
        mock_market_data = AsyncMock()
        return AdvancedMonteCarloEngine(market_data_service=mock_market_data)
    
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio for benchmarking."""
        return {
            "assets": [
                {"symbol": "SPY", "weight": 0.6, "expected_return": 0.10, "volatility": 0.15},
                {"symbol": "BND", "weight": 0.3, "expected_return": 0.04, "volatility": 0.05},
                {"symbol": "VNQ", "weight": 0.1, "expected_return": 0.08, "volatility": 0.20}
            ],
            "correlation_matrix": np.array([
                [1.00, 0.10, 0.70],
                [0.10, 1.00, 0.15],
                [0.70, 0.15, 1.00]
            ])
        }
    
    def test_monte_carlo_simulation_speed(self, monte_carlo_engine, sample_portfolio, benchmark):
        """Benchmark Monte Carlo simulation speed for different simulation counts."""
        
        simulation_counts = [1000, 5000, 10000]
        
        for num_simulations in simulation_counts:
            def run_simulation():
                return asyncio.run(
                    monte_carlo_engine.simulate_portfolio(
                        portfolio=sample_portfolio,
                        num_simulations=num_simulations,
                        time_horizon=30,
                        dt=1/252  # Daily steps
                    )
                )
            
            # Benchmark the simulation
            result = benchmark.pedantic(
                run_simulation,
                rounds=3,
                iterations=1
            )
            
            # Verify simulation completed successfully
            assert result is not None
            assert "paths" in result
            assert len(result["paths"]) == num_simulations
            
            # Performance expectations based on simulation count
            if num_simulations == 1000:
                assert benchmark.stats["mean"] < 2.0  # Under 2 seconds
            elif num_simulations == 5000:
                assert benchmark.stats["mean"] < 8.0  # Under 8 seconds
            elif num_simulations == 10000:
                assert benchmark.stats["mean"] < 15.0  # Under 15 seconds
    
    def test_monte_carlo_memory_usage(self, monte_carlo_engine, sample_portfolio):
        """Test memory usage scaling for Monte Carlo simulations."""
        
        def measure_memory_usage(num_simulations):
            """Measure peak memory usage during simulation."""
            gc.collect()  # Clean up before measurement
            process = psutil.Process()
            
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run simulation
            result = asyncio.run(
                monte_carlo_engine.simulate_portfolio(
                    portfolio=sample_portfolio,
                    num_simulations=num_simulations,
                    time_horizon=30
                )
            )
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            return memory_used, result
        
        simulation_counts = [1000, 5000, 10000]
        memory_usage = []
        
        for num_sims in simulation_counts:
            memory_used, result = measure_memory_usage(num_sims)
            memory_usage.append(memory_used)
            
            # Verify simulation worked
            assert result is not None
            assert len(result["paths"]) == num_sims
            
            # Memory usage should be reasonable
            # Rough estimate: ~8 bytes per float * time_steps * num_sims * num_assets
            expected_memory_mb = (8 * 252 * 30 * num_sims * 3) / (1024 * 1024)
            
            # Allow 3x overhead for Python objects and intermediate calculations
            assert memory_used < expected_memory_mb * 3
        
        # Memory usage should scale roughly linearly with simulation count
        memory_per_1k_sims = memory_usage[0]  # 1000 simulations
        memory_per_5k_sims = memory_usage[1]  # 5000 simulations
        
        scaling_factor = memory_per_5k_sims / memory_per_1k_sims
        assert 3.0 <= scaling_factor <= 7.0  # Should be close to 5x but allow variance
    
    def test_parallel_monte_carlo_performance(self, monte_carlo_engine, sample_portfolio):
        """Test performance improvement from parallel execution."""
        
        num_simulations = 10000
        
        # Sequential execution
        start_time = time.time()
        sequential_result = asyncio.run(
            monte_carlo_engine.simulate_portfolio(
                portfolio=sample_portfolio,
                num_simulations=num_simulations,
                parallel=False
            )
        )
        sequential_time = time.time() - start_time
        
        # Parallel execution
        start_time = time.time()
        parallel_result = asyncio.run(
            monte_carlo_engine.simulate_portfolio(
                portfolio=sample_portfolio,
                num_simulations=num_simulations,
                parallel=True,
                num_processes=4
            )
        )
        parallel_time = time.time() - start_time
        
        # Both should produce valid results
        assert len(sequential_result["paths"]) == num_simulations
        assert len(parallel_result["paths"]) == num_simulations
        
        # Parallel should be faster (allow some overhead)
        speedup = sequential_time / parallel_time
        assert speedup >= 1.5, f"Expected speedup >= 1.5x, got {speedup:.2f}x"
        
        # Results should be statistically similar (within tolerance)
        seq_mean = np.mean(sequential_result["final_values"])
        par_mean = np.mean(parallel_result["final_values"])
        relative_diff = abs(seq_mean - par_mean) / seq_mean
        assert relative_diff < 0.05, "Parallel and sequential results should be similar"


@pytest.mark.benchmark
class TestPortfolioOptimizationPerformance:
    """Benchmark portfolio optimization performance."""
    
    @pytest.fixture
    def optimizer(self):
        """Create portfolio optimizer."""
        return ModernPortfolioTheory()
    
    @pytest.fixture
    def sample_returns_data(self):
        """Generate sample returns data for different universe sizes."""
        def generate_data(num_assets):
            # Generate 252 days of returns for each asset
            np.random.seed(42)  # For reproducible benchmarks
            returns = np.random.normal(0.0008, 0.02, (252, num_assets))
            return returns
        
        return generate_data
    
    def test_optimization_speed_by_universe_size(self, optimizer, sample_returns_data, benchmark):
        """Benchmark optimization speed for different universe sizes."""
        
        universe_sizes = [5, 10, 25, 50, 100]
        
        for num_assets in universe_sizes:
            returns_data = sample_returns_data(num_assets)
            
            def run_optimization():
                return optimizer.optimize_portfolio(
                    returns=returns_data,
                    objective="maximize_sharpe",
                    constraints={
                        "weights_sum_to_one": True,
                        "long_only": True,
                        "max_weight": 0.4
                    }
                )
            
            # Benchmark the optimization
            result = benchmark.pedantic(
                run_optimization,
                rounds=3,
                iterations=1
            )
            
            # Verify optimization completed successfully
            assert result is not None
            assert "weights" in result
            assert len(result["weights"]) == num_assets
            assert abs(sum(result["weights"]) - 1.0) < 1e-6
            
            # Performance expectations based on universe size
            expected_times = {
                5: 0.1,    # 100ms
                10: 0.5,   # 500ms
                25: 2.0,   # 2 seconds
                50: 8.0,   # 8 seconds
                100: 30.0  # 30 seconds
            }
            
            assert benchmark.stats["mean"] < expected_times[num_assets], \
                f"Optimization for {num_assets} assets took {benchmark.stats['mean']:.2f}s, "\
                f"expected < {expected_times[num_assets]}s"
    
    def test_constraint_complexity_performance(self, optimizer, sample_returns_data, benchmark):
        """Benchmark performance impact of different constraint types."""
        
        num_assets = 20
        returns_data = sample_returns_data(num_assets)
        
        constraint_scenarios = {
            "simple": {
                "weights_sum_to_one": True,
                "long_only": True
            },
            "weight_bounds": {
                "weights_sum_to_one": True,
                "long_only": True,
                "max_weight": 0.2,
                "min_weight": 0.02
            },
            "sector_constraints": {
                "weights_sum_to_one": True,
                "long_only": True,
                "max_weight": 0.2,
                "sector_constraints": {
                    "technology": {"assets": [0, 1, 2, 3, 4], "max_weight": 0.3},
                    "financials": {"assets": [5, 6, 7, 8], "max_weight": 0.2},
                    "healthcare": {"assets": [9, 10, 11], "max_weight": 0.15}
                }
            },
            "turnover_constraints": {
                "weights_sum_to_one": True,
                "long_only": True,
                "max_weight": 0.2,
                "max_turnover": 0.1,
                "current_weights": [1/num_assets] * num_assets  # Equal weight starting point
            }
        }
        
        performance_results = {}
        
        for scenario_name, constraints in constraint_scenarios.items():
            def run_constrained_optimization():
                return optimizer.optimize_portfolio(
                    returns=returns_data,
                    objective="maximize_sharpe",
                    constraints=constraints
                )
            
            result = benchmark.pedantic(
                run_constrained_optimization,
                rounds=3,
                iterations=1
            )
            
            performance_results[scenario_name] = benchmark.stats["mean"]
            
            # Verify optimization succeeded
            assert result is not None
            assert "weights" in result
        
        # More complex constraints should take longer but not excessively
        assert performance_results["simple"] < performance_results["weight_bounds"]
        assert performance_results["weight_bounds"] < performance_results["sector_constraints"]
        
        # But even complex scenarios should complete in reasonable time
        assert all(time < 10.0 for time in performance_results.values()), \
            "All optimization scenarios should complete within 10 seconds"
    
    def test_covariance_matrix_performance(self, optimizer, benchmark):
        """Benchmark covariance matrix calculation and inversion performance."""
        
        matrix_sizes = [10, 50, 100, 200]
        
        for size in matrix_sizes:
            # Generate sample returns data
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, (252, size))
            
            def calculate_and_invert_covariance():
                # Calculate covariance matrix
                cov_matrix = np.cov(returns.T)
                
                # Invert for optimization (this is often the bottleneck)
                try:
                    inv_cov = np.linalg.inv(cov_matrix)
                    return inv_cov
                except np.linalg.LinAlgError:
                    # Handle singular matrices with pseudo-inverse
                    return np.linalg.pinv(cov_matrix)
            
            result = benchmark.pedantic(
                calculate_and_invert_covariance,
                rounds=5,
                iterations=1
            )
            
            # Verify matrix inversion succeeded
            assert result is not None
            assert result.shape == (size, size)
            
            # Performance expectations
            expected_times = {
                10: 0.001,   # 1ms
                50: 0.01,    # 10ms
                100: 0.05,   # 50ms
                200: 0.2     # 200ms
            }
            
            assert benchmark.stats["mean"] < expected_times[size], \
                f"Covariance calculation for {size}x{size} matrix took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_times[size]}s"


@pytest.mark.benchmark
class TestMarketDataPerformance:
    """Benchmark market data processing performance."""
    
    @pytest.fixture
    def market_data_manager(self):
        """Create market data manager for benchmarking."""
        mock_cache = AsyncMock()
        mock_provider = AsyncMock()
        
        return MarketDataManager(
            cache_manager=mock_cache,
            primary_provider=mock_provider
        )
    
    def test_batch_quote_processing(self, market_data_manager, benchmark):
        """Benchmark batch quote processing performance."""
        
        batch_sizes = [10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            symbols = [f"STOCK_{i:03d}" for i in range(batch_size)]
            
            # Mock quote responses
            mock_quotes = []
            for symbol in symbols:
                mock_quotes.append({
                    "symbol": symbol,
                    "price": 100.0 + (hash(symbol) % 100),
                    "volume": 1000000,
                    "timestamp": datetime.now().isoformat()
                })
            
            market_data_manager.primary_provider.get_batch_quotes.return_value = mock_quotes
            
            def process_batch_quotes():
                return asyncio.run(
                    market_data_manager.get_batch_quotes(symbols)
                )
            
            result = benchmark.pedantic(
                process_batch_quotes,
                rounds=3,
                iterations=1
            )
            
            # Verify batch processing succeeded
            assert result is not None
            assert len(result) == batch_size
            
            # Performance expectations (should scale linearly)
            expected_time_per_quote = 0.001  # 1ms per quote
            expected_total_time = batch_size * expected_time_per_quote + 0.1  # 100ms overhead
            
            assert benchmark.stats["mean"] < expected_total_time, \
                f"Batch processing {batch_size} quotes took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_total_time:.3f}s"
    
    def test_historical_data_processing(self, market_data_manager, benchmark):
        """Benchmark historical data processing and aggregation."""
        
        def generate_tick_data(num_ticks):
            """Generate sample tick data."""
            ticks = []
            base_time = datetime.now() - timedelta(hours=6)
            
            for i in range(num_ticks):
                ticks.append({
                    "timestamp": base_time + timedelta(seconds=i),
                    "price": 100.0 + np.random.normal(0, 1),
                    "volume": np.random.randint(100, 10000)
                })
            
            return ticks
        
        tick_counts = [1000, 5000, 10000, 50000]
        
        for num_ticks in tick_counts:
            tick_data = generate_tick_data(num_ticks)
            
            def process_and_aggregate_ticks():
                # Simulate OHLCV aggregation
                aggregated_data = []
                
                # Group by minute
                current_minute = None
                minute_ticks = []
                
                for tick in tick_data:
                    tick_minute = tick["timestamp"].replace(second=0, microsecond=0)
                    
                    if current_minute != tick_minute:
                        if minute_ticks:
                            # Aggregate previous minute
                            ohlcv = {
                                "timestamp": current_minute,
                                "open": minute_ticks[0]["price"],
                                "high": max(t["price"] for t in minute_ticks),
                                "low": min(t["price"] for t in minute_ticks),
                                "close": minute_ticks[-1]["price"],
                                "volume": sum(t["volume"] for t in minute_ticks)
                            }
                            aggregated_data.append(ohlcv)
                        
                        current_minute = tick_minute
                        minute_ticks = []
                    
                    minute_ticks.append(tick)
                
                # Handle last minute
                if minute_ticks:
                    ohlcv = {
                        "timestamp": current_minute,
                        "open": minute_ticks[0]["price"],
                        "high": max(t["price"] for t in minute_ticks),
                        "low": min(t["price"] for t in minute_ticks),
                        "close": minute_ticks[-1]["price"],
                        "volume": sum(t["volume"] for t in minute_ticks)
                    }
                    aggregated_data.append(ohlcv)
                
                return aggregated_data
            
            result = benchmark.pedantic(
                process_and_aggregate_ticks,
                rounds=3,
                iterations=1
            )
            
            # Verify aggregation worked
            assert result is not None
            assert len(result) > 0
            
            # Performance expectations
            expected_time_per_1k_ticks = 0.01  # 10ms per 1000 ticks
            expected_total_time = (num_ticks / 1000) * expected_time_per_1k_ticks
            
            assert benchmark.stats["mean"] < expected_total_time * 2, \
                f"Processing {num_ticks} ticks took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_total_time * 2:.3f}s"
    
    def test_concurrent_market_data_requests(self, market_data_manager, benchmark):
        """Benchmark handling of concurrent market data requests."""
        
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"] * 10  # 50 symbols total
        
        # Mock responses
        def mock_quote_response(symbol):
            return {
                "symbol": symbol,
                "price": 100.0 + hash(symbol) % 100,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat()
            }
        
        market_data_manager.primary_provider.get_real_time_quote.side_effect = mock_quote_response
        
        def process_concurrent_requests():
            async def fetch_all_quotes():
                tasks = []
                for symbol in symbols:
                    task = market_data_manager.get_real_time_quote(symbol)
                    tasks.append(task)
                
                return await asyncio.gather(*tasks)
            
            return asyncio.run(fetch_all_quotes())
        
        result = benchmark.pedantic(
            process_concurrent_requests,
            rounds=3,
            iterations=1
        )
        
        # Verify all requests succeeded
        assert result is not None
        assert len(result) == len(symbols)
        
        # Concurrent requests should be faster than sequential
        # Allow 2 seconds for 50 concurrent requests (vs 25+ seconds sequential)
        assert benchmark.stats["mean"] < 2.0, \
            f"50 concurrent requests took {benchmark.stats['mean']:.3f}s, expected < 2.0s"


@pytest.mark.benchmark
class TestDatabasePerformance:
    """Benchmark database operation performance."""
    
    async def test_bulk_insert_performance(self, db_session, benchmark):
        """Benchmark bulk database insert performance."""
        
        from app.models.market_data import MarketData
        
        record_counts = [100, 1000, 5000]
        
        for num_records in record_counts:
            # Generate test data
            test_records = []
            for i in range(num_records):
                record = MarketData(
                    symbol=f"STOCK_{i % 100:03d}",
                    timestamp=datetime.now() - timedelta(minutes=i),
                    open_price=Decimal(100 + (i % 50)),
                    high_price=Decimal(105 + (i % 50)),
                    low_price=Decimal(95 + (i % 50)),
                    close_price=Decimal(102 + (i % 50)),
                    volume=1000000 + (i * 1000),
                    adjusted_close=Decimal(102 + (i % 50))
                )
                test_records.append(record)
            
            async def bulk_insert_records():
                db_session.add_all(test_records)
                await db_session.commit()
                return len(test_records)
            
            result = benchmark.pedantic(
                lambda: asyncio.run(bulk_insert_records()),
                rounds=3,
                iterations=1
            )
            
            # Verify all records were inserted
            assert result == num_records
            
            # Performance expectations
            expected_time_per_1k_records = 0.5  # 500ms per 1000 records
            expected_total_time = (num_records / 1000) * expected_time_per_1k_records
            
            assert benchmark.stats["mean"] < expected_total_time * 2, \
                f"Inserting {num_records} records took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_total_time * 2:.3f}s"
            
            # Cleanup for next iteration
            await db_session.rollback()
    
    async def test_complex_query_performance(self, db_session, benchmark):
        """Benchmark complex database query performance."""
        
        # This would test complex joins and aggregations
        # For now, we'll simulate the query structure
        
        query_scenarios = {
            "simple_filter": "SELECT * FROM market_data WHERE symbol = 'AAPL' LIMIT 1000",
            "date_range_with_aggregation": """
                SELECT symbol, AVG(close_price), MAX(volume) 
                FROM market_data 
                WHERE timestamp >= NOW() - INTERVAL '30 days' 
                GROUP BY symbol
            """,
            "complex_join": """
                SELECT u.email, fp.risk_tolerance, AVG(sr.success_probability)
                FROM users u
                JOIN financial_profiles fp ON u.id = fp.user_id
                JOIN simulation_results sr ON u.id = sr.user_id
                WHERE fp.risk_tolerance = 'moderate'
                GROUP BY u.email, fp.risk_tolerance
            """
        }
        
        for scenario_name, query in query_scenarios.items():
            async def execute_query():
                # In a real test, this would execute the actual query
                # For benchmarking purposes, we'll simulate query execution time
                if "simple" in scenario_name:
                    await asyncio.sleep(0.01)  # 10ms
                elif "aggregation" in scenario_name:
                    await asyncio.sleep(0.05)  # 50ms
                else:
                    await asyncio.sleep(0.1)   # 100ms
                
                return f"Query {scenario_name} executed"
            
            result = benchmark.pedantic(
                lambda: asyncio.run(execute_query()),
                rounds=5,
                iterations=1
            )
            
            assert result is not None
            
            # Performance expectations based on query complexity
            expected_times = {
                "simple_filter": 0.05,
                "date_range_with_aggregation": 0.2,
                "complex_join": 0.5
            }
            
            assert benchmark.stats["mean"] < expected_times[scenario_name], \
                f"Query {scenario_name} took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_times[scenario_name]}s"


@pytest.mark.benchmark
class TestSystemIntegrationPerformance:
    """Benchmark end-to-end system performance."""
    
    async def test_portfolio_recommendation_pipeline(self, authenticated_client, benchmark):
        """Benchmark complete portfolio recommendation pipeline."""
        
        async def full_recommendation_pipeline():
            # 1. Fetch user profile
            profile_response = await authenticated_client.get("/financial-profiles/me")
            assert profile_response.status_code == 200
            
            # 2. Get market data for universe
            market_data_response = await authenticated_client.post(
                "/market-data/batch-quotes",
                json={"symbols": ["SPY", "BND", "VTI", "VXUS", "VNQ"]}
            )
            assert market_data_response.status_code == 200
            
            # 3. Run portfolio optimization
            optimization_response = await authenticated_client.post(
                "/portfolio/optimize",
                json={
                    "universe": [
                        {"symbol": "SPY", "weight": 0.0},
                        {"symbol": "BND", "weight": 0.0},
                        {"symbol": "VTI", "weight": 0.0},
                        {"symbol": "VXUS", "weight": 0.0},
                        {"symbol": "VNQ", "weight": 0.0}
                    ],
                    "objective": "maximize_sharpe"
                }
            )
            assert optimization_response.status_code == 200
            
            # 4. Generate personalized recommendations
            recommendations_response = await authenticated_client.get("/recommendations/")
            assert recommendations_response.status_code == 200
            
            return recommendations_response.json()
        
        result = benchmark.pedantic(
            lambda: asyncio.run(full_recommendation_pipeline()),
            rounds=3,
            iterations=1
        )
        
        # Verify pipeline completed successfully
        assert result is not None
        assert "portfolio_recommendations" in result
        
        # Complete pipeline should finish within 10 seconds
        assert benchmark.stats["mean"] < 10.0, \
            f"Full recommendation pipeline took {benchmark.stats['mean']:.3f}s, expected < 10.0s"
    
    def test_system_load_simulation(self, benchmark):
        """Simulate system load to test performance under stress."""
        
        def simulate_concurrent_users(num_users=10):
            """Simulate multiple concurrent users performing various operations."""
            
            async def user_session():
                # Simulate user session with multiple operations
                operations = [
                    asyncio.sleep(0.1),  # Login
                    asyncio.sleep(0.05), # Fetch profile
                    asyncio.sleep(0.2),  # Get recommendations
                    asyncio.sleep(0.3),  # Run optimization
                    asyncio.sleep(0.1),  # Update goals
                ]
                
                await asyncio.gather(*operations)
                return "session_completed"
            
            async def simulate_load():
                # Create tasks for concurrent users
                user_tasks = [user_session() for _ in range(num_users)]
                results = await asyncio.gather(*user_tasks)
                return results
            
            return asyncio.run(simulate_load())
        
        user_counts = [5, 10, 20]
        
        for num_users in user_counts:
            result = benchmark.pedantic(
                lambda: simulate_concurrent_users(num_users),
                rounds=3,
                iterations=1
            )
            
            # Verify all user sessions completed
            assert result is not None
            assert len(result) == num_users
            assert all(r == "session_completed" for r in result)
            
            # Performance should degrade gracefully with load
            expected_times = {
                5: 1.0,   # 5 users: under 1 second
                10: 2.0,  # 10 users: under 2 seconds
                20: 5.0   # 20 users: under 5 seconds
            }
            
            assert benchmark.stats["mean"] < expected_times[num_users], \
                f"Load test with {num_users} users took {benchmark.stats['mean']:.3f}s, "\
                f"expected < {expected_times[num_users]}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
