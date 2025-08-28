"""
Daily Operations Automation Module

Provides automated daily operations management for:
- Pre-market data updates and preparations
- Market hours monitoring and rebalancing  
- Post-market reconciliation and reporting
- Risk monitoring and alert generation
- Tax optimization and compliance checks
"""

from .daily_operations import DailyOperationsManager

__all__ = ["DailyOperationsManager"]