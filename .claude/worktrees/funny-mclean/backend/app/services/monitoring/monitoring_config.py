"""
Portfolio Monitoring Configuration and Templates
Provides pre-configured monitoring rules, alert templates, and usage examples.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from app.services.monitoring.portfolio_monitor import (
    PortfolioMonitoringService, MonitoringRule, RebalancingRule, 
    DrawdownRule, GoalProgressRule, TaxHarvestingMonitorRule, 
    MarketRegimeRule, create_standard_monitoring_rules
)
from app.services.monitoring.alert_engine import AlertEngine, AlertPriority


@dataclass
class MonitoringProfile:
    """Pre-configured monitoring profile"""
    name: str
    description: str
    risk_tolerance: str
    rules_config: Dict[str, Any]
    alert_preferences: Dict[str, Any]


class MonitoringConfigManager:
    """Manages monitoring configurations and profiles"""
    
    def __init__(self):
        self.profiles = self._create_default_profiles()
        self.rule_templates = self._create_rule_templates()
        self.alert_templates = self._create_alert_templates()
    
    def _create_default_profiles(self) -> Dict[str, MonitoringProfile]:
        """Create default monitoring profiles"""
        profiles = {}
        
        # Conservative Profile
        profiles['conservative'] = MonitoringProfile(
            name="Conservative Investor",
            description="Low-risk monitoring with frequent checks and tight thresholds",
            risk_tolerance="conservative",
            rules_config={
                'rebalancing': {
                    'drift_threshold': 0.03,  # 3% drift threshold
                    'check_interval_seconds': 300,  # 5 minutes
                    'cooldown_minutes': 30
                },
                'drawdown': {
                    'max_drawdown': 0.05,  # 5% max drawdown
                    'check_interval_seconds': 60,  # 1 minute
                    'cooldown_minutes': 30
                },
                'tax_harvesting': {
                    'min_loss_amount': 500,
                    'check_interval_seconds': 1800,  # 30 minutes
                    'cooldown_minutes': 120
                },
                'market_regime': {
                    'volatility_threshold': 0.20,
                    'check_interval_seconds': 600,  # 10 minutes
                    'cooldown_minutes': 60
                }
            },
            alert_preferences={
                'email_enabled': True,
                'sms_enabled': True,
                'push_enabled': True,
                'sms_priority_threshold': 'medium',
                'email_frequency_limit': 50,
                'sms_frequency_limit': 10,
                'quiet_hours_start': 21,
                'quiet_hours_end': 8
            }
        )
        
        # Moderate Profile
        profiles['moderate'] = MonitoringProfile(
            name="Moderate Investor",
            description="Balanced monitoring with standard thresholds",
            risk_tolerance="moderate",
            rules_config={
                'rebalancing': {
                    'drift_threshold': 0.05,  # 5% drift threshold
                    'check_interval_seconds': 600,  # 10 minutes
                    'cooldown_minutes': 60
                },
                'drawdown': {
                    'max_drawdown': 0.10,  # 10% max drawdown
                    'check_interval_seconds': 300,  # 5 minutes
                    'cooldown_minutes': 60
                },
                'tax_harvesting': {
                    'min_loss_amount': 1000,
                    'check_interval_seconds': 3600,  # 1 hour
                    'cooldown_minutes': 240
                },
                'market_regime': {
                    'volatility_threshold': 0.25,
                    'check_interval_seconds': 900,  # 15 minutes
                    'cooldown_minutes': 120
                }
            },
            alert_preferences={
                'email_enabled': True,
                'sms_enabled': True,
                'push_enabled': True,
                'sms_priority_threshold': 'high',
                'email_frequency_limit': 20,
                'sms_frequency_limit': 5,
                'quiet_hours_start': 22,
                'quiet_hours_end': 8
            }
        )
        
        # Aggressive Profile
        profiles['aggressive'] = MonitoringProfile(
            name="Aggressive Investor",
            description="High-risk monitoring with relaxed thresholds",
            risk_tolerance="aggressive",
            rules_config={
                'rebalancing': {
                    'drift_threshold': 0.08,  # 8% drift threshold
                    'check_interval_seconds': 1800,  # 30 minutes
                    'cooldown_minutes': 120
                },
                'drawdown': {
                    'max_drawdown': 0.20,  # 20% max drawdown
                    'check_interval_seconds': 600,  # 10 minutes
                    'cooldown_minutes': 120
                },
                'tax_harvesting': {
                    'min_loss_amount': 2000,
                    'check_interval_seconds': 7200,  # 2 hours
                    'cooldown_minutes': 480
                },
                'market_regime': {
                    'volatility_threshold': 0.35,
                    'check_interval_seconds': 1800,  # 30 minutes
                    'cooldown_minutes': 240
                }
            },
            alert_preferences={
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'sms_priority_threshold': 'critical',
                'email_frequency_limit': 10,
                'sms_frequency_limit': 2,
                'quiet_hours_start': 23,
                'quiet_hours_end': 7
            }
        )
        
        # Day Trader Profile
        profiles['day_trader'] = MonitoringProfile(
            name="Day Trader",
            description="High-frequency monitoring for active traders",
            risk_tolerance="aggressive",
            rules_config={
                'rebalancing': {
                    'drift_threshold': 0.02,  # 2% drift threshold
                    'check_interval_seconds': 30,  # 30 seconds
                    'cooldown_minutes': 5
                },
                'drawdown': {
                    'max_drawdown': 0.05,  # 5% max drawdown
                    'check_interval_seconds': 30,  # 30 seconds
                    'cooldown_minutes': 10
                },
                'market_regime': {
                    'volatility_threshold': 0.15,
                    'check_interval_seconds': 60,  # 1 minute
                    'cooldown_minutes': 15
                }
            },
            alert_preferences={
                'email_enabled': False,
                'sms_enabled': False,
                'push_enabled': True,
                'in_app_enabled': True,
                'sms_priority_threshold': 'critical',
                'email_frequency_limit': 100,
                'sms_frequency_limit': 20,
                'quiet_hours_start': 24,  # Never quiet
                'quiet_hours_end': 0
            }
        )
        
        return profiles
    
    def _create_rule_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create rule templates for different scenarios"""
        return {
            'retirement_focused': {
                'description': 'Focused on long-term retirement goals',
                'rules': {
                    'goal_progress': {
                        'milestone_intervals': [0.25, 0.50, 0.75, 0.85, 0.95, 1.0],
                        'check_interval_seconds': 86400  # Daily
                    },
                    'drawdown': {
                        'max_drawdown': 0.15,
                        'check_interval_seconds': 3600
                    }
                }
            },
            'tax_optimization': {
                'description': 'Optimized for tax efficiency',
                'rules': {
                    'tax_harvesting': {
                        'min_loss_amount': 500,
                        'check_interval_seconds': 1800,
                        'min_holding_days': 31
                    },
                    'rebalancing': {
                        'drift_threshold': 0.06,
                        'check_interval_seconds': 86400  # Daily for tax considerations
                    }
                }
            },
            'volatility_sensitive': {
                'description': 'Sensitive to market volatility changes',
                'rules': {
                    'market_regime': {
                        'volatility_threshold': 0.18,
                        'correlation_threshold': 0.60,
                        'check_interval_seconds': 300
                    },
                    'drawdown': {
                        'max_drawdown': 0.08,
                        'check_interval_seconds': 180
                    }
                }
            }
        }
    
    def _create_alert_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create alert configuration templates"""
        return {
            'minimal_alerts': {
                'description': 'Only critical alerts',
                'channels': ['email', 'push'],
                'priority_filter': ['high', 'critical'],
                'frequency_limits': {
                    'email': 5,
                    'sms': 2,
                    'push': 20
                }
            },
            'comprehensive_alerts': {
                'description': 'All types of alerts across all channels',
                'channels': ['email', 'sms', 'push', 'in_app'],
                'priority_filter': ['low', 'medium', 'high', 'critical'],
                'frequency_limits': {
                    'email': 50,
                    'sms': 15,
                    'push': 100
                }
            },
            'business_hours_only': {
                'description': 'Alerts only during business hours',
                'channels': ['email', 'push'],
                'quiet_hours_start': 18,  # 6 PM
                'quiet_hours_end': 9,     # 9 AM
                'priority_override': ['critical']  # Critical alerts bypass quiet hours
            }
        }
    
    def create_monitoring_rules(self, user_id: str, portfolio_id: str, 
                              profile_name: str, custom_config: Dict[str, Any] = None) -> List[MonitoringRule]:
        """Create monitoring rules based on profile and custom configuration"""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        profile = self.profiles[profile_name]
        config = profile.rules_config.copy()
        
        # Apply custom configuration
        if custom_config:
            for rule_type, custom_params in custom_config.items():
                if rule_type in config:
                    config[rule_type].update(custom_params)
                else:
                    config[rule_type] = custom_params
        
        rules = []
        
        # Create rebalancing rule
        if 'rebalancing' in config:
            params = config['rebalancing']
            rules.append(RebalancingRule(
                id=f"rebalance_{portfolio_id}_{profile_name}",
                name=f"Portfolio Rebalancing - {profile.name}",
                user_id=user_id,
                portfolio_id=portfolio_id,
                drift_threshold=params.get('drift_threshold', 0.05),
                check_interval_seconds=params.get('check_interval_seconds', 600),
                cooldown_minutes=params.get('cooldown_minutes', 60)
            ))
        
        # Create drawdown rule
        if 'drawdown' in config:
            params = config['drawdown']
            rules.append(DrawdownRule(
                id=f"drawdown_{portfolio_id}_{profile_name}",
                name=f"Drawdown Monitor - {profile.name}",
                user_id=user_id,
                portfolio_id=portfolio_id,
                max_drawdown=params.get('max_drawdown', 0.10),
                trailing_days=params.get('trailing_days', 30),
                check_interval_seconds=params.get('check_interval_seconds', 300),
                cooldown_minutes=params.get('cooldown_minutes', 60)
            ))
        
        # Create tax harvesting rule
        if 'tax_harvesting' in config:
            params = config['tax_harvesting']
            rules.append(TaxHarvestingMonitorRule(
                id=f"tax_{portfolio_id}_{profile_name}",
                name=f"Tax Harvesting - {profile.name}",
                user_id=user_id,
                portfolio_id=portfolio_id,
                min_loss_amount=params.get('min_loss_amount', 1000),
                min_holding_days=params.get('min_holding_days', 31),
                check_interval_seconds=params.get('check_interval_seconds', 3600),
                cooldown_minutes=params.get('cooldown_minutes', 240)
            ))
        
        # Create market regime rule
        if 'market_regime' in config:
            params = config['market_regime']
            rules.append(MarketRegimeRule(
                id=f"regime_{portfolio_id}_{profile_name}",
                name=f"Market Regime Monitor - {profile.name}",
                user_id=user_id,
                portfolio_id=portfolio_id,
                volatility_threshold=params.get('volatility_threshold', 0.25),
                correlation_threshold=params.get('correlation_threshold', 0.70),
                check_interval_seconds=params.get('check_interval_seconds', 900),
                cooldown_minutes=params.get('cooldown_minutes', 120)
            ))
        
        # Create goal progress rules
        if 'goal_progress' in config:
            params = config['goal_progress']
            # This would typically iterate through user's goals
            for goal_id in ['retirement', 'house']:  # Mock goals
                rules.append(GoalProgressRule(
                    id=f"goal_{goal_id}_{portfolio_id}_{profile_name}",
                    name=f"Goal Progress - {goal_id.title()}",
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    goal_id=goal_id,
                    milestone_intervals=params.get('milestone_intervals', [0.25, 0.50, 0.75, 0.90, 1.0]),
                    check_interval_seconds=params.get('check_interval_seconds', 86400),
                    cooldown_minutes=params.get('cooldown_minutes', 1440)  # 24 hours
                ))
        
        return rules
    
    def get_alert_preferences(self, profile_name: str, template_name: str = None) -> Dict[str, Any]:
        """Get alert preferences for a profile and optional template"""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        preferences = self.profiles[profile_name].alert_preferences.copy()
        
        if template_name and template_name in self.alert_templates:
            template = self.alert_templates[template_name]
            
            # Apply template settings
            if 'channels' in template:
                for channel in ['email', 'sms', 'push', 'in_app', 'webhook']:
                    preferences[f'{channel}_enabled'] = channel in template['channels']
            
            if 'frequency_limits' in template:
                for channel, limit in template['frequency_limits'].items():
                    preferences[f'{channel}_frequency_limit'] = limit
            
            if 'quiet_hours_start' in template:
                preferences['quiet_hours_start'] = template['quiet_hours_start']
            
            if 'quiet_hours_end' in template:
                preferences['quiet_hours_end'] = template['quiet_hours_end']
        
        return preferences
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate monitoring configuration"""
        errors = []
        
        # Validate drift thresholds
        if 'rebalancing' in config:
            drift = config['rebalancing'].get('drift_threshold', 0)
            if not 0.01 <= drift <= 0.50:
                errors.append("Rebalancing drift threshold must be between 1% and 50%")
        
        # Validate drawdown thresholds
        if 'drawdown' in config:
            drawdown = config['drawdown'].get('max_drawdown', 0)
            if not 0.02 <= drawdown <= 0.50:
                errors.append("Max drawdown must be between 2% and 50%")
        
        # Validate check intervals
        for rule_type, params in config.items():
            if 'check_interval_seconds' in params:
                interval = params['check_interval_seconds']
                if not 30 <= interval <= 86400:  # 30 seconds to 1 day
                    errors.append(f"{rule_type} check interval must be between 30 seconds and 1 day")
        
        return errors
    
    def export_configuration(self, profile_name: str) -> str:
        """Export configuration as JSON string"""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        profile = self.profiles[profile_name]
        config = {
            'profile': {
                'name': profile.name,
                'description': profile.description,
                'risk_tolerance': profile.risk_tolerance
            },
            'rules_config': profile.rules_config,
            'alert_preferences': profile.alert_preferences,
            'exported_at': datetime.utcnow().isoformat()
        }
        
        return json.dumps(config, indent=2)
    
    def import_configuration(self, config_json: str) -> MonitoringProfile:
        """Import configuration from JSON string"""
        try:
            config = json.loads(config_json)
            
            profile = MonitoringProfile(
                name=config['profile']['name'],
                description=config['profile']['description'],
                risk_tolerance=config['profile']['risk_tolerance'],
                rules_config=config['rules_config'],
                alert_preferences=config['alert_preferences']
            )
            
            # Validate the imported configuration
            errors = self.validate_configuration(profile.rules_config)
            if errors:
                raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
            
            return profile
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid configuration format: {e}")


class MonitoringSetupWizard:
    """Wizard to help users set up monitoring based on their preferences"""
    
    def __init__(self):
        self.config_manager = MonitoringConfigManager()
    
    def recommend_profile(self, user_responses: Dict[str, Any]) -> str:
        """Recommend monitoring profile based on user responses"""
        
        # Risk tolerance assessment
        risk_score = 0
        risk_tolerance = user_responses.get('risk_tolerance', 'moderate')
        
        if risk_tolerance == 'conservative':
            risk_score = 1
        elif risk_tolerance == 'moderate':
            risk_score = 2
        elif risk_tolerance == 'aggressive':
            risk_score = 3
        
        # Trading frequency assessment
        trading_frequency = user_responses.get('trading_frequency', 'monthly')
        if trading_frequency == 'daily':
            if risk_score >= 3:
                return 'day_trader'
            else:
                return 'aggressive'
        elif trading_frequency == 'weekly':
            return 'aggressive'
        elif trading_frequency == 'monthly':
            return 'moderate'
        else:  # quarterly or less
            return 'conservative'
    
    def customize_profile(self, base_profile: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Customize a base profile based on user preferences"""
        if base_profile not in self.config_manager.profiles:
            raise ValueError(f"Unknown base profile: {base_profile}")
        
        base_config = self.config_manager.profiles[base_profile].rules_config.copy()
        
        # Adjust based on preferences
        if preferences.get('frequent_rebalancing', False):
            if 'rebalancing' in base_config:
                base_config['rebalancing']['check_interval_seconds'] = min(
                    base_config['rebalancing']['check_interval_seconds'], 300
                )
                base_config['rebalancing']['drift_threshold'] *= 0.8  # Tighter threshold
        
        if preferences.get('tax_sensitive', False):
            base_config['tax_harvesting'] = base_config.get('tax_harvesting', {})
            base_config['tax_harvesting']['min_loss_amount'] = 500
            base_config['tax_harvesting']['check_interval_seconds'] = 1800
        
        if preferences.get('volatility_sensitive', False):
            if 'market_regime' in base_config:
                base_config['market_regime']['volatility_threshold'] *= 0.8
                base_config['market_regime']['check_interval_seconds'] = min(
                    base_config['market_regime']['check_interval_seconds'], 600
                )
        
        return base_config
    
    def generate_monitoring_plan(self, user_id: str, portfolio_id: str, 
                                user_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete monitoring plan based on user responses"""
        
        # Recommend base profile
        recommended_profile = self.recommend_profile(user_responses)
        
        # Customize based on preferences
        custom_config = self.customize_profile(recommended_profile, user_responses)
        
        # Create rules
        rules = self.config_manager.create_monitoring_rules(
            user_id=user_id,
            portfolio_id=portfolio_id,
            profile_name=recommended_profile,
            custom_config=custom_config
        )
        
        # Get alert preferences
        alert_template = user_responses.get('alert_style', 'comprehensive_alerts')
        alert_preferences = self.config_manager.get_alert_preferences(
            recommended_profile, 
            alert_template
        )
        
        return {
            'recommended_profile': recommended_profile,
            'rules_count': len(rules),
            'rules': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'type': rule.event_type.value,
                    'check_interval': rule.check_interval_seconds,
                    'cooldown': rule.cooldown_minutes
                }
                for rule in rules
            ],
            'alert_preferences': alert_preferences,
            'estimated_alerts_per_day': self._estimate_alert_frequency(rules, custom_config),
            'setup_summary': self._generate_setup_summary(recommended_profile, rules, alert_preferences)
        }
    
    def _estimate_alert_frequency(self, rules: List[MonitoringRule], config: Dict[str, Any]) -> int:
        """Estimate alerts per day based on configuration"""
        # Simplified estimation - in practice would use historical data
        base_frequency = {
            'rebalancing': 0.5,  # 0.5 alerts per day on average
            'drawdown': 0.2,
            'tax_harvesting': 0.1,
            'market_regime': 0.3,
            'goal_progress': 0.05
        }
        
        total_frequency = 0
        for rule in rules:
            rule_type = rule.event_type.value.split('_')[0]  # Get base type
            if rule_type in base_frequency:
                # Adjust based on check frequency
                frequency_multiplier = 3600 / rule.check_interval_seconds  # Relative to hourly
                frequency_multiplier = min(frequency_multiplier, 2)  # Cap the multiplier
                
                total_frequency += base_frequency[rule_type] * frequency_multiplier
        
        return max(1, int(total_frequency))
    
    def _generate_setup_summary(self, profile_name: str, rules: List[MonitoringRule], 
                               alert_preferences: Dict[str, Any]) -> List[str]:
        """Generate human-readable setup summary"""
        summary = []
        
        summary.append(f"Selected profile: {profile_name.title()}")
        summary.append(f"Active monitoring rules: {len(rules)}")
        
        # Count rule types
        rule_types = {}
        for rule in rules:
            rule_type = rule.event_type.value
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
        
        summary.append("Monitoring coverage:")
        for rule_type, count in rule_types.items():
            summary.append(f"  • {rule_type.replace('_', ' ').title()}: {count} rule(s)")
        
        # Alert channels
        enabled_channels = [
            channel.replace('_enabled', '') 
            for channel, enabled in alert_preferences.items() 
            if channel.endswith('_enabled') and enabled
        ]
        
        if enabled_channels:
            summary.append(f"Alert channels: {', '.join(enabled_channels)}")
        
        # Quiet hours
        if alert_preferences.get('quiet_hours_start') != alert_preferences.get('quiet_hours_end'):
            summary.append(f"Quiet hours: {alert_preferences.get('quiet_hours_start', 22)}:00 - {alert_preferences.get('quiet_hours_end', 8)}:00")
        
        return summary


# Example usage and testing
def example_monitoring_setup():
    """Example of how to set up portfolio monitoring"""
    
    # Initialize services
    config_manager = MonitoringConfigManager()
    setup_wizard = MonitoringSetupWizard()
    monitoring_service = PortfolioMonitoringService()
    alert_engine = AlertEngine()
    
    # User responses for setup wizard
    user_responses = {
        'risk_tolerance': 'moderate',
        'trading_frequency': 'monthly',
        'frequent_rebalancing': True,
        'tax_sensitive': True,
        'volatility_sensitive': False,
        'alert_style': 'comprehensive_alerts'
    }
    
    # Generate monitoring plan
    user_id = "user123"
    portfolio_id = "portfolio456"
    
    monitoring_plan = setup_wizard.generate_monitoring_plan(
        user_id=user_id,
        portfolio_id=portfolio_id,
        user_responses=user_responses
    )
    
    print("Generated Monitoring Plan:")
    print(f"Profile: {monitoring_plan['recommended_profile']}")
    print(f"Rules: {monitoring_plan['rules_count']}")
    print(f"Estimated alerts per day: {monitoring_plan['estimated_alerts_per_day']}")
    print("\nSetup Summary:")
    for item in monitoring_plan['setup_summary']:
        print(f"  {item}")
    
    # Create actual monitoring rules
    rules = config_manager.create_monitoring_rules(
        user_id=user_id,
        portfolio_id=portfolio_id,
        profile_name=monitoring_plan['recommended_profile']
    )
    
    # Set up alert preferences
    alert_preferences = monitoring_plan['alert_preferences']
    
    return {
        'monitoring_service': monitoring_service,
        'alert_engine': alert_engine,
        'rules': rules,
        'alert_preferences': alert_preferences,
        'monitoring_plan': monitoring_plan
    }


if __name__ == "__main__":
    # Run example setup
    example_setup = example_monitoring_setup()
    print("\nMonitoring setup completed successfully!")