"""
Market Data Integration System - Usage Examples

Comprehensive examples demonstrating all features of the unified market data platform:
- Real-time quotes with consensus validation
- Historical data with technical indicators  
- WebSocket streaming for high-frequency updates
- Performance monitoring and alerts
- Error handling and failover scenarios
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import the unified system and related components
from ..unified_market_data_system import (
    UnifiedMarketDataSystem,
    MarketDataRequest,
    MarketDataResponse,
    DataSourceType,
    UpdateFrequency,
    PerformanceMonitor
)
from ..aggregator_enhanced import ConsensusMethod, DataQuality
from ..failover_manager import ServiceLevel
from ..cache.high_performance_cache import CacheConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataExamples:
    """Comprehensive examples for the market data integration system"""
    
    def __init__(self):
        self.system = None
        
    async def initialize_system(self):
        """Initialize the market data system with custom configuration"""
        try:
            # Initialize the unified system
            self.system = UnifiedMarketDataSystem()
            
            # Configure high-performance cache
            cache_config = CacheConfig(
                redis_url="redis://localhost:6379",
                max_connections=50,
                pipeline_size=1000,
                batch_size=100,
                compression_threshold=1024,
                quote_ttl=60,  # 1 minute for quotes
                trade_ttl=300,  # 5 minutes for trades
                fundamental_ttl=86400  # 24 hours for fundamentals
            )
            
            # Update system cache configuration
            self.system.cache.config = cache_config
            
            # Initialize the system
            await self.system.initialize()
            
            logger.info("Market data system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def example_1_real_time_quotes(self):
        """Example 1: Get real-time quotes with consensus validation"""
        print("\n=== Example 1: Real-time Quotes with Consensus ===")
        
        try:
            # Create request for multiple symbols
            request = MarketDataRequest(
                symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
                data_types=[DataSourceType.REAL_TIME],
                consensus_method=ConsensusMethod.WEIGHTED_AVERAGE,
                service_level=ServiceLevel.HIGH,
                include_validation=True,
                enable_caching=True,
                max_age_seconds=30
            )
            
            # Get market data
            responses = await self.system.get_market_data(request)
            
            print(f"Retrieved {len(responses)} quotes:")
            
            for response in responses:
                data = response.data
                print(f"""
                Symbol: {response.symbol}
                Last Price: ${data.get('last', 'N/A')}
                Bid/Ask: ${data.get('bid', 'N/A')} / ${data.get('ask', 'N/A')}
                Spread: ${data.get('spread', 'N/A')}
                Volume: {data.get('volume', 'N/A'):,}
                Quality: {response.quality.value}
                Confidence: {response.confidence:.2%}
                Sources: {', '.join(response.sources)}
                Latency: {response.latency_ms:.2f}ms
                From Cache: {response.from_cache}
                """)
                
        except Exception as e:
            logger.error(f"Error in example 1: {e}")
    
    async def example_2_historical_data_with_analytics(self):
        """Example 2: Historical data with technical indicators"""
        print("\n=== Example 2: Historical Data with Analytics ===")
        
        try:
            # Request historical data for the past 30 days
            request = MarketDataRequest(
                symbols=["AAPL", "GOOGL"],
                data_types=[DataSourceType.HISTORICAL],
                service_level=ServiceLevel.HIGH,
                enable_caching=True,
                max_age_seconds=3600  # Cache for 1 hour
            )
            
            responses = await self.system.get_market_data(request)
            
            for response in responses:
                if response.data_type == DataSourceType.HISTORICAL:
                    data = response.data
                    print(f"""
                    Historical Data for {response.symbol}:
                    - Data points: {len(data.get('close', []))} days
                    - Latest close: ${data.get('close', [])[-1] if data.get('close') else 'N/A'}
                    - Technical Indicators:
                      * SMA 20: ${data.get('sma_20', [])[-1]:.2f if data.get('sma_20') else 'N/A'}
                      * RSI: {data.get('rsi', [])[-1]:.1f if data.get('rsi') else 'N/A'}
                      * MACD: {data.get('macd', [])[-1]:.2f if data.get('macd') else 'N/A'}
                      * Volatility (20d): {data.get('volatility_20d', [])[-1]:.2%} if data.get('volatility_20d') else 'N/A'}
                    Quality Score: {self.system._calculate_quality_score(response):.1f}/100
                    """)
                    
        except Exception as e:
            logger.error(f"Error in example 2: {e}")
    
    async def example_3_real_time_streaming(self):
        """Example 3: Real-time streaming with WebSocket-like functionality"""
        print("\n=== Example 3: Real-time Streaming ===")
        
        try:
            # Callback function for real-time updates
            update_count = 0
            
            async def handle_real_time_update(response: MarketDataResponse):
                nonlocal update_count
                update_count += 1
                
                data = response.data
                print(f"[{update_count:03d}] {response.symbol}: ${data.get('last', 'N/A')} "
                      f"(Quality: {response.quality.value}, "
                      f"Confidence: {response.confidence:.1%})")
                
                # Stop after 20 updates for demo
                if update_count >= 20:
                    return False  # Stop streaming
            
            # Subscribe to real-time updates
            symbols = ["AAPL", "GOOGL", "MSFT"]
            subscription_id = await self.system.subscribe_real_time(
                symbols=symbols,
                data_types=[DataSourceType.REAL_TIME],
                callback=handle_real_time_update,
                update_frequency=UpdateFrequency.HIGH
            )
            
            print(f"Subscribed to real-time updates for {symbols}")
            print(f"Subscription ID: {subscription_id}")
            print("Streaming real-time data (will stop after 20 updates)...")
            
            # Let it stream for a while
            await asyncio.sleep(30)
            
            # Unsubscribe
            await self.system.unsubscribe_real_time(subscription_id)
            print(f"Unsubscribed from {subscription_id}")
            
        except Exception as e:
            logger.error(f"Error in example 3: {e}")
    
    async def example_4_high_performance_batch_processing(self):
        """Example 4: High-performance batch processing"""
        print("\n=== Example 4: High-Performance Batch Processing ===")
        
        try:
            # Create a large batch of symbols
            symbols = [
                "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
                "NFLX", "META", "NVDA", "AMD", "INTC",
                "PYPL", "ADBE", "CRM", "ORCL", "CSCO",
                "IBM", "HPQ", "DELL", "VMW", "NOW"
            ]
            
            start_time = asyncio.get_event_loop().time()
            
            # Process batch with high-performance caching
            request = MarketDataRequest(
                symbols=symbols,
                data_types=[DataSourceType.REAL_TIME],
                consensus_method=ConsensusMethod.WEIGHTED_AVERAGE,
                service_level=ServiceLevel.HIGH,
                enable_caching=True,
                max_age_seconds=60
            )
            
            responses = await self.system.get_market_data(request)
            
            end_time = asyncio.get_event_loop().time()
            processing_time = (end_time - start_time) * 1000
            
            print(f"""
            Batch Processing Results:
            - Requested symbols: {len(symbols)}
            - Successful responses: {len(responses)}
            - Total processing time: {processing_time:.2f}ms
            - Average per symbol: {processing_time/len(symbols):.2f}ms
            - Throughput: {len(symbols)/(processing_time/1000):.0f} symbols/second
            """)
            
            # Show cache performance
            cache_stats = await self.system.cache.get_performance_stats()
            print(f"""
            Cache Performance:
            - Operations per second: {cache_stats.get('performance', {}).get('operations_per_second', 0):.0f}
            - Cache hit ratio: {cache_stats.get('performance', {}).get('cache_hit_ratio', 0):.2%}
            - Average latency: {cache_stats.get('performance', {}).get('average_latency_ms', 0):.2f}ms
            - Compression ratio: {cache_stats.get('performance', {}).get('compression_ratio', 1):.1f}x
            """)
            
        except Exception as e:
            logger.error(f"Error in example 4: {e}")
    
    async def example_5_failover_and_circuit_breaker(self):
        """Example 5: Demonstrate failover and circuit breaker functionality"""
        print("\n=== Example 5: Failover and Circuit Breaker ===")
        
        try:
            # Get failover manager status
            failover_status = await self.system.failover_manager.get_status()
            
            print("Provider Status:")
            for provider_name, provider_info in failover_status.get('providers', {}).items():
                cb_status = provider_info.get('circuit_breaker', {})
                health = provider_info.get('health', {})
                
                print(f"""
                {provider_name.upper()}:
                - Priority: {provider_info.get('priority', 'N/A')}
                - Service Level: {provider_info.get('service_level', 'N/A')}
                - Circuit Breaker: {cb_status.get('state', 'Unknown')}
                - Health Status: {'Healthy' if health.get('status') else 'Unhealthy'}
                - Success Rate: {cb_status.get('metrics', {}).get('success_rate', 0):.1f}%
                - Total Requests: {provider_info.get('metrics', {}).get('total_requests', 0)}
                """)
            
            # Demonstrate circuit breaker reset (admin operation)
            print("\nTesting circuit breaker reset for 'polygon' provider...")
            try:
                await self.system.failover_manager.reset_provider('polygon')
                print("✓ Circuit breaker reset successful")
            except Exception as e:
                print(f"✗ Circuit breaker reset failed: {e}")
            
        except Exception as e:
            logger.error(f"Error in example 5: {e}")
    
    async def example_6_fundamental_data_analysis(self):
        """Example 6: Fundamental data and financial ratios"""
        print("\n=== Example 6: Fundamental Analysis ===")
        
        try:
            # Get fundamental data for major tech stocks
            symbols = ["AAPL", "GOOGL", "MSFT"]
            
            for symbol in symbols:
                request = MarketDataRequest(
                    symbols=[symbol],
                    data_types=[DataSourceType.FUNDAMENTAL],
                    service_level=ServiceLevel.MEDIUM,
                    enable_caching=True,
                    max_age_seconds=86400  # Cache fundamentals for 24 hours
                )
                
                responses = await self.system.get_market_data(request)
                
                if responses:
                    response = responses[0]
                    data = response.data
                    
                    print(f"""
                    Fundamental Analysis - {symbol}:
                    - Market Cap: {data.get('market_cap', 'N/A')}
                    - P/E Ratio: {data.get('pe_ratio', 'N/A')}
                    - Dividend Yield: {data.get('dividend_yield', 'N/A')}
                    - Revenue: {data.get('revenue', 'N/A')}
                    - Net Income: {data.get('net_income', 'N/A')}
                    - Data Quality: {response.quality.value}
                    - Last Updated: {data.get('last_updated', 'N/A')}
                    """)
                else:
                    print(f"No fundamental data available for {symbol}")
                
        except Exception as e:
            logger.error(f"Error in example 6: {e}")
    
    async def example_7_performance_monitoring(self):
        """Example 7: Performance monitoring and system health"""
        print("\n=== Example 7: Performance Monitoring ===")
        
        try:
            # Get comprehensive system status
            system_status = await self.system.get_system_status()
            
            print("System Status:")
            print(f"- Initialized: {system_status.get('system', {}).get('initialized', False)}")
            print(f"- Active Subscriptions: {system_status.get('system', {}).get('active_subscriptions', 0)}")
            print(f"- Background Tasks: {system_status.get('system', {}).get('background_tasks', 0)}")
            
            # Performance metrics
            performance = system_status.get('performance', {})
            if performance:
                print(f"""
                Performance Metrics:
                - Success Rate: {performance.get('performance', {}).get('success_rate', 0):.2%}
                - Cache Hit Rate: {performance.get('performance', {}).get('cache_hit_rate', 0):.2%}
                - Average Latency: {performance.get('performance', {}).get('average_latency_ms', 0):.2f}ms
                - Requests/Second: {performance.get('performance', {}).get('requests_per_second', 0):.0f}
                """)
                
                # Alert information
                alerts = performance.get('alerts', {})
                if alerts.get('active_alerts', 0) > 0:
                    print(f"⚠️  Active Alerts: {alerts['active_alerts']}")
                    for alert in alerts.get('recent_alerts', [])[-3:]:  # Show last 3 alerts
                        print(f"   - {alert.get('type', 'Unknown')}: {alert.get('message', 'N/A')}")
            
            # Component health
            components = system_status.get('components', {})
            for component_name, component_status in components.items():
                print(f"\n{component_name.upper()} Component:")
                if isinstance(component_status, dict):
                    for key, value in component_status.items():
                        if key in ['performance', 'redis_info', 'circuit_breaker']:
                            print(f"  - {key}: {type(value).__name__} data available")
                        else:
                            print(f"  - {key}: {value}")
            
        except Exception as e:
            logger.error(f"Error in example 7: {e}")
    
    async def example_8_error_handling_scenarios(self):
        """Example 8: Error handling and recovery scenarios"""
        print("\n=== Example 8: Error Handling Scenarios ===")
        
        try:
            # Test 1: Invalid symbol handling
            print("Test 1: Invalid symbol handling")
            request = MarketDataRequest(
                symbols=["INVALID_SYMBOL_XYZ", "AAPL"],
                data_types=[DataSourceType.REAL_TIME],
                service_level=ServiceLevel.MEDIUM
            )
            
            responses = await self.system.get_market_data(request)
            print(f"Requested 2 symbols (1 invalid), got {len(responses)} valid responses")
            
            # Test 2: Network timeout simulation
            print("\nTest 2: Handling cached data when live data fails")
            
            # First, populate cache
            await self.system.get_market_data(MarketDataRequest(
                symbols=["AAPL"],
                data_types=[DataSourceType.REAL_TIME],
                enable_caching=True
            ))
            
            # Then request with very short max_age to force live data attempt
            cached_request = MarketDataRequest(
                symbols=["AAPL"],
                data_types=[DataSourceType.REAL_TIME],
                enable_caching=True,
                max_age_seconds=1800  # 30 minutes - should use cache
            )
            
            cached_responses = await self.system.get_market_data(cached_request)
            
            if cached_responses:
                response = cached_responses[0]
                print(f"Data served from cache: {response.from_cache}")
                print(f"Cache latency: {response.latency_ms:.2f}ms")
            
            # Test 3: Quality validation
            print("\nTest 3: Data quality validation")
            quality_request = MarketDataRequest(
                symbols=["AAPL"],
                data_types=[DataSourceType.REAL_TIME],
                include_validation=True
            )
            
            quality_responses = await self.system.get_market_data(quality_request)
            
            if quality_responses:
                response = quality_responses[0]
                validation = response.validation_results
                print(f"Validation Results: {validation}")
                print(f"Data Quality: {response.quality.value}")
                print(f"Confidence Score: {response.confidence:.2%}")
            
        except Exception as e:
            logger.error(f"Error in example 8: {e}")
    
    async def run_all_examples(self):
        """Run all examples in sequence"""
        print("🚀 Starting Market Data Integration System Examples")
        print("=" * 60)
        
        try:
            # Initialize the system
            await self.initialize_system()
            
            # Run all examples
            examples = [
                self.example_1_real_time_quotes,
                self.example_2_historical_data_with_analytics,
                self.example_3_real_time_streaming,
                self.example_4_high_performance_batch_processing,
                self.example_5_failover_and_circuit_breaker,
                self.example_6_fundamental_data_analysis,
                self.example_7_performance_monitoring,
                self.example_8_error_handling_scenarios
            ]
            
            for i, example in enumerate(examples, 1):
                try:
                    await example()
                    print(f"✓ Example {i} completed successfully")
                except Exception as e:
                    print(f"✗ Example {i} failed: {e}")
                
                # Small delay between examples
                await asyncio.sleep(2)
            
            print("\n" + "=" * 60)
            print("🎉 All examples completed!")
            
            # Final system status
            final_status = await self.system.get_system_status()
            performance = final_status.get('performance', {}).get('performance', {})
            
            print(f"""
            Final Performance Summary:
            - Total Requests Processed: {final_status.get('performance', {}).get('counters', {}).get('total_requests', 0)}
            - Overall Success Rate: {performance.get('success_rate', 0):.2%}
            - Average Latency: {performance.get('average_latency_ms', 0):.2f}ms
            - Cache Hit Rate: {performance.get('cache_hit_rate', 0):.2%}
            """)
            
        except Exception as e:
            logger.error(f"Failed to run examples: {e}")
        
        finally:
            # Cleanup
            if self.system:
                await self.system.shutdown()
                print("System shutdown complete")


# Utility functions for specific use cases
async def get_portfolio_quotes(symbols: List[str]) -> Dict[str, Any]:
    """Utility function to get quotes for a portfolio of symbols"""
    system = UnifiedMarketDataSystem()
    await system.initialize()
    
    try:
        request = MarketDataRequest(
            symbols=symbols,
            data_types=[DataSourceType.REAL_TIME],
            consensus_method=ConsensusMethod.WEIGHTED_AVERAGE,
            service_level=ServiceLevel.HIGH,
            enable_caching=True
        )
        
        responses = await system.get_market_data(request)
        
        portfolio_data = {}
        total_confidence = 0
        
        for response in responses:
            data = response.data
            portfolio_data[response.symbol] = {
                'price': data.get('last'),
                'bid': data.get('bid'),
                'ask': data.get('ask'),
                'volume': data.get('volume'),
                'quality': response.quality.value,
                'confidence': response.confidence,
                'sources': response.sources,
                'timestamp': response.timestamp
            }
            total_confidence += response.confidence
        
        avg_confidence = total_confidence / len(responses) if responses else 0
        
        return {
            'portfolio': portfolio_data,
            'summary': {
                'symbols_count': len(portfolio_data),
                'average_confidence': avg_confidence,
                'timestamp': datetime.utcnow()
            }
        }
        
    finally:
        await system.shutdown()


async def monitor_symbol_real_time(symbol: str, duration_seconds: int = 60):
    """Utility function to monitor a single symbol in real-time"""
    system = UnifiedMarketDataSystem()
    await system.initialize()
    
    try:
        updates = []
        
        async def capture_update(response: MarketDataResponse):
            data = response.data
            updates.append({
                'timestamp': response.timestamp,
                'price': data.get('last'),
                'volume': data.get('volume'),
                'quality': response.quality.value,
                'confidence': response.confidence
            })
            
            print(f"[{len(updates):03d}] {symbol}: ${data.get('last', 'N/A')} "
                  f"(Vol: {data.get('volume', 'N/A'):,})")
        
        # Subscribe to real-time updates
        subscription_id = await system.subscribe_real_time(
            symbols=[symbol],
            data_types=[DataSourceType.REAL_TIME],
            callback=capture_update,
            update_frequency=UpdateFrequency.HIGH
        )
        
        print(f"Monitoring {symbol} for {duration_seconds} seconds...")
        await asyncio.sleep(duration_seconds)
        
        # Unsubscribe and return data
        await system.unsubscribe_real_time(subscription_id)
        
        return {
            'symbol': symbol,
            'updates': updates,
            'duration_seconds': duration_seconds,
            'total_updates': len(updates),
            'average_update_frequency': len(updates) / duration_seconds if duration_seconds > 0 else 0
        }
        
    finally:
        await system.shutdown()


# Main execution
if __name__ == "__main__":
    examples = MarketDataExamples()
    
    # Run all examples
    asyncio.run(examples.run_all_examples())
    
    # Or run specific utility functions:
    # portfolio_quotes = asyncio.run(get_portfolio_quotes(["AAPL", "GOOGL", "MSFT"]))
    # real_time_data = asyncio.run(monitor_symbol_real_time("AAPL", 30))