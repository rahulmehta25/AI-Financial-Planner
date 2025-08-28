"""
Portfolio Monitoring Service Usage Examples
Demonstrates how to integrate and use the real-time monitoring system.
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List

from app.services.monitoring.portfolio_monitor import (
    PortfolioMonitoringService, PortfolioSnapshot, create_standard_monitoring_rules
)
from app.services.monitoring.alert_engine import AlertEngine, Alert, AlertType, AlertPriority
from app.services.monitoring.monitoring_config import MonitoringConfigManager, MonitoringSetupWizard
from app.services.monitoring.websocket_server import WebSocketManager, BroadcastMessage


class MonitoringIntegrationExample:
    """Complete example of monitoring system integration"""
    
    def __init__(self):
        self.monitoring_service = PortfolioMonitoringService()
        self.alert_engine = AlertEngine()
        self.config_manager = MonitoringConfigManager()
        self.setup_wizard = MonitoringSetupWizard()
        
        # Mock data
        self.mock_users = self._create_mock_users()
        self.mock_portfolios = self._create_mock_portfolios()
    
    def _create_mock_users(self) -> Dict[str, Dict[str, Any]]:
        """Create mock user data"""
        return {
            'user1': {
                'name': 'John Conservative',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'risk_tolerance': 'conservative',
                'investment_goals': ['retirement', 'emergency_fund'],
                'tax_bracket': 0.24
            },
            'user2': {
                'name': 'Sarah Moderate',
                'email': 'sarah@example.com',
                'phone': '+1234567891',
                'risk_tolerance': 'moderate',
                'investment_goals': ['house', 'retirement'],
                'tax_bracket': 0.32
            },
            'user3': {
                'name': 'Mike Aggressive',
                'email': 'mike@example.com',
                'phone': '+1234567892',
                'risk_tolerance': 'aggressive',
                'investment_goals': ['wealth_building'],
                'tax_bracket': 0.37
            }
        }
    
    def _create_mock_portfolios(self) -> Dict[str, Dict[str, Any]]:
        """Create mock portfolio data"""
        return {
            'portfolio1': {
                'user_id': 'user1',
                'name': 'Conservative Retirement',
                'total_value': Decimal('150000'),
                'target_allocation': {
                    'VTI': 0.30,    # US Total Market
                    'BND': 0.50,    # Total Bond Market
                    'VXUS': 0.15,   # International
                    'VNQ': 0.05     # REITs
                },
                'positions': {
                    'VTI': {'shares': 150, 'avg_cost': 200, 'current_price': 220},
                    'BND': {'shares': 1000, 'avg_cost': 75, 'current_price': 74},
                    'VXUS': {'shares': 300, 'avg_cost': 55, 'current_price': 58},
                    'VNQ': {'shares': 80, 'avg_cost': 90, 'current_price': 85}
                }
            },
            'portfolio2': {
                'user_id': 'user2',
                'name': 'Balanced Growth',
                'total_value': Decimal('75000'),
                'target_allocation': {
                    'VTI': 0.60,    # US Total Market
                    'BND': 0.25,    # Total Bond Market
                    'VXUS': 0.15    # International
                },
                'positions': {
                    'VTI': {'shares': 200, 'avg_cost': 180, 'current_price': 220},
                    'BND': {'shares': 250, 'avg_cost': 78, 'current_price': 74},
                    'VXUS': {'shares': 200, 'avg_cost': 60, 'current_price': 58}
                }
            },
            'portfolio3': {
                'user_id': 'user3',
                'name': 'Aggressive Growth',
                'total_value': Decimal('200000'),
                'target_allocation': {
                    'VTI': 0.70,    # US Total Market
                    'QQQ': 0.20,    # NASDAQ
                    'VXUS': 0.10    # International
                },
                'positions': {
                    'VTI': {'shares': 600, 'avg_cost': 190, 'current_price': 220},
                    'QQQ': {'shares': 150, 'avg_cost': 250, 'current_price': 280},
                    'VXUS': {'shares': 350, 'avg_cost': 55, 'current_price': 58}
                }
            }
        }
    
    async def setup_complete_monitoring(self):
        """Complete setup example"""
        print("🚀 Setting up comprehensive portfolio monitoring system...")
        
        # 1. Start monitoring service
        await self.monitoring_service.start_monitoring()
        print("✅ Monitoring service started")
        
        # 2. Set up users and portfolios
        for user_id, user_data in self.mock_users.items():
            # Find user's portfolio
            user_portfolios = {
                pid: pdata for pid, pdata in self.mock_portfolios.items()
                if pdata['user_id'] == user_id
            }
            
            for portfolio_id, portfolio_data in user_portfolios.items():
                await self._setup_user_monitoring(user_id, portfolio_id, user_data, portfolio_data)
        
        print("✅ All users and portfolios configured")
        
        # 3. Simulate market updates and events
        print("\n📊 Starting market simulation...")
        await self._simulate_market_events()
    
    async def _setup_user_monitoring(self, user_id: str, portfolio_id: str, 
                                   user_data: Dict[str, Any], portfolio_data: Dict[str, Any]):
        """Set up monitoring for a specific user"""
        
        # Create monitoring rules based on risk tolerance
        rules = create_standard_monitoring_rules(
            user_id=user_id,
            portfolio_id=portfolio_id,
            risk_tolerance=user_data['risk_tolerance']
        )
        
        # Register portfolio for monitoring
        await self.monitoring_service.register_portfolio(user_id, portfolio_id, rules)
        
        # Set up alert preferences
        profile_name = user_data['risk_tolerance']
        alert_preferences = self.config_manager.get_alert_preferences(profile_name)
        
        await self.alert_engine.set_user_preferences(user_id, alert_preferences)
        
        print(f"✅ Configured monitoring for {user_data['name']} ({user_data['risk_tolerance']})")
        print(f"   📋 {len(rules)} monitoring rules active")
        print(f"   📱 Alert channels: {', '.join([k.replace('_enabled', '') for k, v in alert_preferences.items() if k.endswith('_enabled') and v])}")
    
    async def _simulate_market_events(self):
        """Simulate various market events to trigger alerts"""
        
        scenarios = [
            self._scenario_normal_day,
            self._scenario_portfolio_drift,
            self._scenario_market_volatility,
            self._scenario_drawdown_event,
            self._scenario_tax_harvesting,
            self._scenario_goal_milestone
        ]
        
        for i, scenario in enumerate(scenarios):
            print(f"\n🎭 Running scenario {i+1}/{len(scenarios)}: {scenario.__name__}")
            await scenario()
            await asyncio.sleep(2)  # Pause between scenarios
    
    async def _scenario_normal_day(self):
        """Normal trading day with minor price movements"""
        print("   📈 Simulating normal market day...")
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            # Small price changes (±2%)
            snapshot = self._create_portfolio_snapshot(
                portfolio_id, 
                portfolio_data,
                price_changes={'VTI': 0.01, 'BND': -0.005, 'VXUS': 0.015, 'QQQ': 0.02, 'VNQ': 0.008}
            )
            
            await self.monitoring_service.update_portfolio(snapshot)
        
        print("   ✅ Normal day simulation completed - no alerts expected")
    
    async def _scenario_portfolio_drift(self):
        """Simulate significant portfolio drift requiring rebalancing"""
        print("   ⚖️ Simulating portfolio drift scenario...")
        
        # Create significant price movements that cause drift
        price_changes = {'VTI': 0.15, 'BND': -0.02, 'VXUS': -0.05, 'QQQ': 0.20, 'VNQ': -0.03}
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            snapshot = self._create_portfolio_snapshot(portfolio_id, portfolio_data, price_changes)
            await self.monitoring_service.update_portfolio(snapshot)
        
        print("   ✅ Drift scenario completed - rebalancing alerts expected")
    
    async def _scenario_market_volatility(self):
        """Simulate high volatility market conditions"""
        print("   📊 Simulating market volatility scenario...")
        
        # Large price swings
        for i in range(3):
            sign = 1 if i % 2 == 0 else -1
            price_changes = {
                'VTI': sign * 0.08,
                'BND': sign * -0.01,
                'VXUS': sign * 0.12,
                'QQQ': sign * 0.15,
                'VNQ': sign * 0.06
            }
            
            for portfolio_id, portfolio_data in self.mock_portfolios.items():
                snapshot = self._create_portfolio_snapshot(portfolio_id, portfolio_data, price_changes)
                await self.monitoring_service.update_portfolio(snapshot)
            
            await asyncio.sleep(1)
        
        print("   ✅ Volatility scenario completed - regime change alerts expected")
    
    async def _scenario_drawdown_event(self):
        """Simulate significant market drawdown"""
        print("   📉 Simulating drawdown scenario...")
        
        # Significant decline
        price_changes = {'VTI': -0.12, 'BND': -0.03, 'VXUS': -0.15, 'QQQ': -0.18, 'VNQ': -0.10}
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            snapshot = self._create_portfolio_snapshot(portfolio_id, portfolio_data, price_changes)
            await self.monitoring_service.update_portfolio(snapshot)
        
        print("   ✅ Drawdown scenario completed - drawdown alerts expected")
    
    async def _scenario_tax_harvesting(self):
        """Simulate tax loss harvesting opportunities"""
        print("   💰 Simulating tax harvesting scenario...")
        
        # Create positions with significant losses
        price_changes = {'VTI': -0.08, 'BND': -0.04, 'VXUS': -0.12, 'QQQ': 0.05, 'VNQ': -0.15}
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            snapshot = self._create_portfolio_snapshot(portfolio_id, portfolio_data, price_changes)
            await self.monitoring_service.update_portfolio(snapshot)
        
        print("   ✅ Tax harvesting scenario completed - harvesting alerts expected")
    
    async def _scenario_goal_milestone(self):
        """Simulate reaching a goal milestone"""
        print("   🎯 Simulating goal milestone scenario...")
        
        # Significant gains to trigger milestone
        price_changes = {'VTI': 0.25, 'BND': 0.02, 'VXUS': 0.20, 'QQQ': 0.30, 'VNQ': 0.15}
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            snapshot = self._create_portfolio_snapshot(portfolio_id, portfolio_data, price_changes)
            await self.monitoring_service.update_portfolio(snapshot)
        
        print("   ✅ Goal milestone scenario completed - progress alerts expected")
    
    def _create_portfolio_snapshot(self, portfolio_id: str, portfolio_data: Dict[str, Any], 
                                 price_changes: Dict[str, float] = None) -> PortfolioSnapshot:
        """Create a portfolio snapshot with optional price changes"""
        
        if price_changes is None:
            price_changes = {}
        
        positions = {}
        allocations = {}
        total_value = Decimal('0')
        daily_change = Decimal('0')
        
        for symbol, position in portfolio_data['positions'].items():
            # Apply price change
            current_price = position['current_price']
            if symbol in price_changes:
                new_price = current_price * (1 + price_changes[symbol])
            else:
                new_price = current_price
            
            # Calculate position value
            shares = position['shares']
            position_value = shares * new_price
            total_value += Decimal(str(position_value))
            
            # Calculate daily change
            previous_value = shares * current_price
            change = position_value - previous_value
            daily_change += Decimal(str(change))
            
            # Store position data
            positions[symbol] = {
                'shares': shares,
                'current_price': new_price,
                'value': float(position_value),
                'change': float(change),
                'avg_cost': position['avg_cost'],
                'unrealized_gain': float(position_value - (shares * position['avg_cost'])),
                'weight': 0  # Will calculate after total value is known
            }
        
        # Calculate allocations
        for symbol, position in positions.items():
            weight = position['value'] / float(total_value)
            position['weight'] = weight
            allocations[symbol] = weight
        
        # Calculate daily change percentage
        previous_total = total_value - daily_change
        daily_change_pct = float(daily_change / previous_total) if previous_total > 0 else 0
        
        return PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            user_id=portfolio_data['user_id'],
            portfolio_id=portfolio_id,
            total_value=total_value,
            daily_change=daily_change,
            daily_change_pct=daily_change_pct,
            positions=positions,
            allocations=allocations,
            target_allocations=portfolio_data['target_allocation'],
            risk_metrics={
                'volatility': 0.15,
                'sharpe_ratio': 1.2,
                'var_95': 0.08,
                'max_drawdown': 0.05
            }
        )
    
    async def demonstrate_websocket_features(self):
        """Demonstrate WebSocket real-time features"""
        print("\n🌐 Demonstrating WebSocket features...")
        
        # Start WebSocket server
        websocket_manager = WebSocketManager()
        await websocket_manager.start_server(host="localhost", port=8765)
        print("✅ WebSocket server started on ws://localhost:8765")
        
        # Simulate real-time updates
        for i in range(5):
            # Create market update
            market_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': 'VTI',
                'price': 220 + (i * 0.5),
                'change': i * 0.5,
                'volume': 1000000 + (i * 100000)
            }
            
            # Broadcast market update
            await websocket_manager.broadcast_update(BroadcastMessage(
                type='market_update',
                channel='market:VTI',
                data=market_data
            ))
            
            print(f"   📡 Broadcast market update {i+1}: VTI @ ${market_data['price']}")
            await asyncio.sleep(1)
        
        await websocket_manager.stop_server()
        print("✅ WebSocket demonstration completed")
    
    async def demonstrate_alert_system(self):
        """Demonstrate the alert system capabilities"""
        print("\n🚨 Demonstrating alert system...")
        
        # Create various types of alerts
        alerts = [
            Alert(
                id='demo_rebalancing',
                user_id='user1',
                type=AlertType.REBALANCING,
                priority=AlertPriority.MEDIUM,
                title='Portfolio Rebalancing Needed',
                message='Your conservative portfolio has drifted 6% from target allocation',
                data={
                    'max_drift': 6.2,
                    'total_assets_drifted': 2,
                    'drifted_assets': [
                        {'symbol': 'VTI', 'current_weight': 36.2, 'target_weight': 30.0, 'drift': 6.2},
                        {'symbol': 'BND', 'current_weight': 45.8, 'target_weight': 50.0, 'drift': 4.2}
                    ],
                    'rebalance_value': 12500
                },
                requires_action=True,
                action_url='/portfolio/rebalance'
            ),
            Alert(
                id='demo_drawdown',
                user_id='user2',
                type=AlertType.DRAWDOWN,
                priority=AlertPriority.HIGH,
                title='Portfolio Drawdown Alert',
                message='Your portfolio has declined 12% from recent high',
                data={
                    'current_drawdown': 12.5,
                    'current_value': 65625,
                    'high_water_mark': 75000,
                    'value_from_peak': -9375
                },
                requires_action=True,
                action_url='/portfolio/risk-analysis'
            ),
            Alert(
                id='demo_goal',
                user_id='user3',
                type=AlertType.GOAL_PROGRESS,
                priority=AlertPriority.MEDIUM,
                title='Goal Milestone Reached!',
                message='Congratulations! You\'ve reached 75% of your wealth building goal',
                data={
                    'goal_name': 'Wealth Building',
                    'milestone_achieved': 75.0,
                    'current_amount': 200000,
                    'target_amount': 266667,
                    'progress_percentage': 75.0,
                    'on_track': True
                },
                requires_action=False
            )
        ]
        
        # Send alerts
        for alert in alerts:
            print(f"   📧 Sending alert: {alert.title}")
            await self.alert_engine.send_alert(alert, channels=['email', 'push'])
            await asyncio.sleep(0.5)
        
        print("✅ Alert demonstration completed")
    
    async def show_monitoring_status(self):
        """Display monitoring status for all portfolios"""
        print("\n📊 Current Monitoring Status:")
        print("=" * 50)
        
        for portfolio_id, portfolio_data in self.mock_portfolios.items():
            user_id = portfolio_data['user_id']
            user_name = self.mock_users[user_id]['name']
            
            # Get monitoring status
            status = await self.monitoring_service.get_monitoring_status(user_id, portfolio_id)
            
            print(f"\n👤 {user_name} - {portfolio_data['name']}")
            print(f"   Status: {status['status'].title()}")
            print(f"   Rules: {status['enabled_rules']}/{status['rules_count']} active")
            
            if status['last_update']:
                print(f"   Last Update: {status['last_update']}")
            
            # Show rule details
            for rule in status['rule_details']:
                status_icon = "✅" if rule['enabled'] else "❌"
                print(f"   {status_icon} {rule['name']} ({rule['type']})")
        
        # Show alert statistics
        print("\n📈 Alert Statistics:")
        for user_id in self.mock_users.keys():
            stats = await self.alert_engine.get_delivery_stats(user_id)
            user_name = self.mock_users[user_id]['name']
            
            print(f"   {user_name}: {stats['total_sent']} sent, {stats['total_failed']} failed")
            print(f"      Success rate: {stats['success_rate']:.1%}")
    
    async def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        await self.monitoring_service.stop_monitoring()
        print("✅ Monitoring service stopped")


async def main():
    """Main example execution"""
    print("🏦 Portfolio Monitoring System - Complete Integration Example")
    print("=" * 60)
    
    example = MonitoringIntegrationExample()
    
    try:
        # Run complete setup and simulation
        await example.setup_complete_monitoring()
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Demonstrate additional features
        await example.demonstrate_websocket_features()
        await example.demonstrate_alert_system()
        
        # Show final status
        await example.show_monitoring_status()
        
        print("\n🎉 Integration example completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✅ Real-time portfolio monitoring")
        print("  ✅ Configurable alert rules")
        print("  ✅ Multi-channel alert delivery")
        print("  ✅ WebSocket real-time updates")
        print("  ✅ Tax loss harvesting detection")
        print("  ✅ Market regime monitoring")
        print("  ✅ Goal progress tracking")
        print("  ✅ Risk threshold monitoring")
        
    except Exception as e:
        print(f"❌ Error during example execution: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await example.cleanup()


def simple_usage_example():
    """Simple synchronous usage example"""
    print("\n📚 Simple Usage Example:")
    print("-" * 30)
    
    # Create configuration manager
    config_manager = MonitoringConfigManager()
    
    # Show available profiles
    print("Available monitoring profiles:")
    for profile_name in config_manager.profiles.keys():
        profile = config_manager.profiles[profile_name]
        print(f"  • {profile.name}: {profile.description}")
    
    # Create rules for moderate investor
    user_id = "example_user"
    portfolio_id = "example_portfolio"
    
    rules = config_manager.create_monitoring_rules(
        user_id=user_id,
        portfolio_id=portfolio_id,
        profile_name='moderate'
    )
    
    print(f"\nGenerated {len(rules)} monitoring rules for moderate investor:")
    for rule in rules:
        print(f"  • {rule.name} (checks every {rule.check_interval_seconds}s)")
    
    # Show alert preferences
    alert_prefs = config_manager.get_alert_preferences('moderate')
    enabled_channels = [
        channel.replace('_enabled', '') 
        for channel, enabled in alert_prefs.items() 
        if channel.endswith('_enabled') and enabled
    ]
    
    print(f"\nAlert channels: {', '.join(enabled_channels)}")
    print(f"Email limit: {alert_prefs.get('email_frequency_limit', 'N/A')} per day")
    print(f"SMS limit: {alert_prefs.get('sms_frequency_limit', 'N/A')} per day")
    
    # Export configuration
    config_json = config_manager.export_configuration('moderate')
    print(f"\nConfiguration exported ({len(config_json)} characters)")


if __name__ == "__main__":
    # Run simple example first
    simple_usage_example()
    
    # Then run full async example
    asyncio.run(main())