"""
Spending Pattern Detection and Anomaly Detection Service

This module provides intelligent spending pattern analysis and anomaly detection
for fraud prevention and financial insights.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from .plaid_service import Transaction
from .transaction_categorizer import CategoryPrediction

logger = logging.getLogger(__name__)


@dataclass
class SpendingPattern:
    """Identified spending pattern"""
    pattern_id: str
    pattern_type: str  # 'daily', 'weekly', 'monthly', 'seasonal'
    category: str
    frequency: float  # Transactions per period
    average_amount: float
    typical_merchants: List[str]
    typical_times: List[str]  # Time patterns
    confidence: float
    description: str


@dataclass
class SpendingAnomaly:
    """Detected spending anomaly"""
    transaction_id: str
    anomaly_type: str  # 'amount', 'frequency', 'merchant', 'time', 'location'
    severity: str  # 'low', 'medium', 'high', 'critical'
    anomaly_score: float
    expected_value: Optional[float]
    actual_value: float
    reason: str
    suggestions: List[str]


@dataclass
class SpendingInsight:
    """Spending insight and recommendation"""
    insight_type: str
    category: str
    title: str
    description: str
    impact: str  # 'positive', 'negative', 'neutral'
    actionable: bool
    recommendations: List[str]


class SpendingPatternDetector:
    """
    Advanced spending pattern detection and anomaly analysis.
    
    Features:
    - Behavioral pattern recognition
    - Statistical anomaly detection
    - Machine learning-based clustering
    - Fraud detection capabilities
    - Spending habit analysis
    - Personalized insights
    - Real-time monitoring
    """
    
    def __init__(self):
        self.anomaly_threshold = settings.SPENDING_PATTERN_ANOMALY_THRESHOLD
        self.min_transactions_for_pattern = 5
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
    
    async def analyze_spending_patterns(
        self,
        transactions: List[Transaction],
        categorized_transactions: Optional[List[CategoryPrediction]] = None,
        user_id: Optional[str] = None,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Comprehensive spending pattern analysis
        
        Args:
            transactions: List of transactions to analyze
            categorized_transactions: Pre-categorized transactions
            user_id: User identifier
            lookback_days: Analysis period in days
            
        Returns:
            Complete spending pattern analysis
        """
        try:
            # Filter recent transactions
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            recent_transactions = [t for t in transactions if t.date >= cutoff_date and t.amount > 0]
            
            if len(recent_transactions) < self.min_transactions_for_pattern:
                return {
                    'user_id': user_id,
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'error': 'Insufficient transaction data for pattern analysis',
                    'minimum_required': self.min_transactions_for_pattern,
                    'transactions_found': len(recent_transactions)
                }
            
            # Create analysis DataFrame
            df = self._create_analysis_dataframe(recent_transactions, categorized_transactions)
            
            # Detect patterns
            daily_patterns = self._detect_daily_patterns(df)
            weekly_patterns = self._detect_weekly_patterns(df)
            monthly_patterns = self._detect_monthly_patterns(df)
            merchant_patterns = self._detect_merchant_patterns(df)
            
            # Detect anomalies
            amount_anomalies = self._detect_amount_anomalies(df)
            frequency_anomalies = self._detect_frequency_anomalies(df)
            merchant_anomalies = self._detect_merchant_anomalies(df)
            time_anomalies = self._detect_time_anomalies(df)
            
            # Generate insights
            spending_insights = self._generate_spending_insights(df, daily_patterns, weekly_patterns, monthly_patterns)
            
            # Risk assessment
            risk_score = self._calculate_risk_score(amount_anomalies, frequency_anomalies, merchant_anomalies, time_anomalies)
            
            return {
                'user_id': user_id,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'analysis_period': {
                    'lookback_days': lookback_days,
                    'transactions_analyzed': len(recent_transactions),
                    'start_date': min(t.date for t in recent_transactions).isoformat(),
                    'end_date': max(t.date for t in recent_transactions).isoformat()
                },
                'spending_patterns': {
                    'daily': [pattern.__dict__ for pattern in daily_patterns],
                    'weekly': [pattern.__dict__ for pattern in weekly_patterns],
                    'monthly': [pattern.__dict__ for pattern in monthly_patterns],
                    'merchant': [pattern.__dict__ for pattern in merchant_patterns]
                },
                'anomalies': {
                    'amount': [anomaly.__dict__ for anomaly in amount_anomalies],
                    'frequency': [anomaly.__dict__ for anomaly in frequency_anomalies],
                    'merchant': [anomaly.__dict__ for anomaly in merchant_anomalies],
                    'time': [anomaly.__dict__ for anomaly in time_anomalies]
                },
                'insights': [insight.__dict__ for insight in spending_insights],
                'risk_assessment': {
                    'overall_risk_score': risk_score,
                    'risk_level': self._get_risk_level(risk_score),
                    'total_anomalies': len(amount_anomalies) + len(frequency_anomalies) + len(merchant_anomalies) + len(time_anomalies)
                },
                'recommendations': self._generate_pattern_recommendations(daily_patterns, weekly_patterns, spending_insights)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {str(e)}")
            raise ValidationError("Failed to analyze spending patterns")
    
    def _create_analysis_dataframe(
        self,
        transactions: List[Transaction],
        categorized_transactions: Optional[List[CategoryPrediction]] = None
    ) -> pd.DataFrame:
        """Create pandas DataFrame optimized for pattern analysis"""
        try:
            data = []
            
            for i, transaction in enumerate(transactions):
                category_prediction = categorized_transactions[i] if categorized_transactions and i < len(categorized_transactions) else None
                
                data.append({
                    'transaction_id': transaction.transaction_id,
                    'date': transaction.date,
                    'amount': transaction.amount,
                    'merchant_name': transaction.merchant_name or 'Unknown',
                    'description': transaction.name,
                    'category': category_prediction.category if category_prediction else 'other',
                    'subcategory': category_prediction.subcategory if category_prediction else 'uncategorized',
                    'hour': transaction.date.hour if hasattr(transaction.date, 'hour') else 12,
                    'day_of_week': transaction.date.weekday(),
                    'day_of_month': transaction.date.day,
                    'week_of_year': transaction.date.isocalendar()[1],
                    'month': transaction.date.month,
                    'is_weekend': transaction.date.weekday() >= 5,
                    'currency': transaction.currency
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating analysis DataFrame: {str(e)}")
            raise ValidationError("Failed to process transaction data for pattern analysis")
    
    def _detect_daily_patterns(self, df: pd.DataFrame) -> List[SpendingPattern]:
        """Detect daily spending patterns"""
        patterns = []
        
        try:
            # Analyze by category and day of week
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                
                if len(category_df) < self.min_transactions_for_pattern:
                    continue
                
                # Daily frequency analysis
                daily_stats = category_df.groupby('day_of_week').agg({
                    'amount': ['count', 'mean', 'std'],
                    'merchant_name': lambda x: list(x.mode()[:3])  # Top 3 merchants
                }).round(2)
                
                for day_of_week, stats in daily_stats.iterrows():
                    count = stats[('amount', 'count')]
                    mean_amount = stats[('amount', 'mean')]
                    std_amount = stats[('amount', 'std')]
                    top_merchants = stats[('merchant_name', '<lambda>')]
                    
                    if count >= 2:  # At least 2 transactions on this day
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        
                        # Calculate frequency (transactions per week)
                        weeks_in_data = (df['date'].max() - df['date'].min()).days / 7
                        frequency = count / max(weeks_in_data, 1)
                        
                        # Confidence based on consistency
                        confidence = min(0.9, 0.3 + (count * 0.1) - (std_amount / mean_amount if mean_amount > 0 else 0) * 0.2)
                        
                        pattern = SpendingPattern(
                            pattern_id=f"daily_{category}_{day_of_week}",
                            pattern_type='daily',
                            category=category,
                            frequency=frequency,
                            average_amount=mean_amount,
                            typical_merchants=top_merchants,
                            typical_times=[day_names[day_of_week]],
                            confidence=max(0.1, confidence),
                            description=f"Regular {category} spending on {day_names[day_of_week]}s"
                        )
                        patterns.append(pattern)
            
            return sorted(patterns, key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting daily patterns: {str(e)}")
            return []
    
    def _detect_weekly_patterns(self, df: pd.DataFrame) -> List[SpendingPattern]:
        """Detect weekly spending patterns"""
        patterns = []
        
        try:
            # Analyze weekly spending by category
            df['week'] = df['date'].dt.to_period('W')
            
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                
                if len(category_df) < self.min_transactions_for_pattern:
                    continue
                
                weekly_stats = category_df.groupby('week').agg({
                    'amount': ['sum', 'count', 'mean'],
                    'merchant_name': lambda x: list(x.mode()[:3])
                })
                
                if len(weekly_stats) >= 2:  # At least 2 weeks of data
                    avg_weekly_spend = weekly_stats[('amount', 'sum')].mean()
                    avg_weekly_transactions = weekly_stats[('amount', 'count')].mean()
                    std_weekly_spend = weekly_stats[('amount', 'sum')].std()
                    
                    # Top merchants across all weeks
                    all_merchants = []
                    for merchants in weekly_stats[('merchant_name', '<lambda>')]:
                        all_merchants.extend(merchants)
                    top_merchants = list(pd.Series(all_merchants).mode()[:3])
                    
                    # Confidence based on consistency
                    cv = std_weekly_spend / avg_weekly_spend if avg_weekly_spend > 0 else 1
                    confidence = max(0.1, 0.8 - cv)
                    
                    pattern = SpendingPattern(
                        pattern_id=f"weekly_{category}",
                        pattern_type='weekly',
                        category=category,
                        frequency=avg_weekly_transactions,
                        average_amount=avg_weekly_spend,
                        typical_merchants=top_merchants,
                        typical_times=['weekly'],
                        confidence=confidence,
                        description=f"Weekly {category} spending pattern"
                    )
                    patterns.append(pattern)
            
            return sorted(patterns, key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting weekly patterns: {str(e)}")
            return []
    
    def _detect_monthly_patterns(self, df: pd.DataFrame) -> List[SpendingPattern]:
        """Detect monthly spending patterns"""
        patterns = []
        
        try:
            # Analyze monthly spending by category
            df['month_period'] = df['date'].dt.to_period('M')
            
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                
                if len(category_df) < self.min_transactions_for_pattern:
                    continue
                
                monthly_stats = category_df.groupby('month_period').agg({
                    'amount': ['sum', 'count', 'mean'],
                    'merchant_name': lambda x: list(x.mode()[:3])
                })
                
                if len(monthly_stats) >= 2:  # At least 2 months of data
                    avg_monthly_spend = monthly_stats[('amount', 'sum')].mean()
                    avg_monthly_transactions = monthly_stats[('amount', 'count')].mean()
                    std_monthly_spend = monthly_stats[('amount', 'sum')].std()
                    
                    # Top merchants
                    all_merchants = []
                    for merchants in monthly_stats[('merchant_name', '<lambda>')]:
                        all_merchants.extend(merchants)
                    top_merchants = list(pd.Series(all_merchants).mode()[:3])
                    
                    # Confidence based on consistency
                    cv = std_monthly_spend / avg_monthly_spend if avg_monthly_spend > 0 else 1
                    confidence = max(0.1, 0.7 - cv * 0.5)
                    
                    pattern = SpendingPattern(
                        pattern_id=f"monthly_{category}",
                        pattern_type='monthly',
                        category=category,
                        frequency=avg_monthly_transactions,
                        average_amount=avg_monthly_spend,
                        typical_merchants=top_merchants,
                        typical_times=['monthly'],
                        confidence=confidence,
                        description=f"Monthly {category} spending pattern"
                    )
                    patterns.append(pattern)
            
            return sorted(patterns, key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting monthly patterns: {str(e)}")
            return []
    
    def _detect_merchant_patterns(self, df: pd.DataFrame) -> List[SpendingPattern]:
        """Detect merchant-specific spending patterns"""
        patterns = []
        
        try:
            # Analyze by merchant
            merchant_stats = df.groupby('merchant_name').agg({
                'amount': ['count', 'mean', 'std', 'sum'],
                'category': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'other',
                'day_of_week': lambda x: list(x.mode()[:3])
            })
            
            # Filter merchants with sufficient transactions
            frequent_merchants = merchant_stats[merchant_stats[('amount', 'count')] >= self.min_transactions_for_pattern]
            
            for merchant, stats in frequent_merchants.iterrows():
                count = stats[('amount', 'count')]
                mean_amount = stats[('amount', 'mean')]
                std_amount = stats[('amount', 'std')]
                total_spend = stats[('amount', 'sum')]
                category = stats[('category', '<lambda>')]
                typical_days = stats[('day_of_week', '<lambda>')]
                
                # Calculate frequency (visits per month)
                days_in_data = (df['date'].max() - df['date'].min()).days
                frequency = count / max(days_in_data / 30, 1)  # Per month
                
                # Confidence based on regularity
                cv = std_amount / mean_amount if mean_amount > 0 else 1
                confidence = min(0.9, 0.4 + (count * 0.05) - cv * 0.2)
                
                day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                typical_day_names = [day_names[day] for day in typical_days if 0 <= day <= 6]
                
                pattern = SpendingPattern(
                    pattern_id=f"merchant_{merchant.replace(' ', '_')}",
                    pattern_type='merchant',
                    category=category,
                    frequency=frequency,
                    average_amount=mean_amount,
                    typical_merchants=[merchant],
                    typical_times=typical_day_names,
                    confidence=max(0.1, confidence),
                    description=f"Regular spending at {merchant}"
                )
                patterns.append(pattern)
            
            return sorted(patterns, key=lambda x: x.confidence, reverse=True)[:20]  # Top 20
            
        except Exception as e:
            logger.error(f"Error detecting merchant patterns: {str(e)}")
            return []
    
    def _detect_amount_anomalies(self, df: pd.DataFrame) -> List[SpendingAnomaly]:
        """Detect anomalous transaction amounts"""
        anomalies = []
        
        try:
            # Analyze by category
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                
                if len(category_df) < 5:  # Need minimum data
                    continue
                
                amounts = category_df['amount'].values
                
                # Statistical outlier detection (Z-score)
                z_scores = np.abs(stats.zscore(amounts))
                outlier_mask = z_scores > self.anomaly_threshold
                
                for idx, is_outlier in enumerate(outlier_mask):
                    if is_outlier:
                        transaction_id = category_df.iloc[idx]['transaction_id']
                        amount = amounts[idx]
                        expected_amount = np.median(amounts)
                        z_score = z_scores[idx]
                        
                        # Determine severity
                        if z_score > 3:
                            severity = 'critical'
                        elif z_score > 2.5:
                            severity = 'high'
                        elif z_score > 2:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        anomaly = SpendingAnomaly(
                            transaction_id=transaction_id,
                            anomaly_type='amount',
                            severity=severity,
                            anomaly_score=z_score,
                            expected_value=expected_amount,
                            actual_value=amount,
                            reason=f"Transaction amount ${amount:.2f} is {z_score:.1f} standard deviations from typical {category} spending",
                            suggestions=[
                                f"Verify this {category} transaction",
                                "Check if this was an intended large purchase",
                                "Review merchant and transaction details"
                            ]
                        )
                        anomalies.append(anomaly)
            
            return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting amount anomalies: {str(e)}")
            return []
    
    def _detect_frequency_anomalies(self, df: pd.DataFrame) -> List[SpendingAnomaly]:
        """Detect unusual spending frequency patterns"""
        anomalies = []
        
        try:
            # Daily frequency analysis
            daily_counts = df.groupby(df['date'].dt.date).size()
            
            if len(daily_counts) < 7:  # Need at least a week of data
                return anomalies
            
            # Detect days with unusually high transaction counts
            mean_daily = daily_counts.mean()
            std_daily = daily_counts.std()
            
            for date, count in daily_counts.items():
                if count > mean_daily + (2 * std_daily):  # 2 standard deviations
                    z_score = (count - mean_daily) / std_daily if std_daily > 0 else 0
                    
                    # Get transactions for this day
                    day_transactions = df[df['date'].dt.date == date]
                    
                    # Determine severity
                    if z_score > 3:
                        severity = 'high'
                    elif z_score > 2.5:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    for _, transaction in day_transactions.iterrows():
                        anomaly = SpendingAnomaly(
                            transaction_id=transaction['transaction_id'],
                            anomaly_type='frequency',
                            severity=severity,
                            anomaly_score=z_score,
                            expected_value=mean_daily,
                            actual_value=count,
                            reason=f"Unusually high spending frequency on {date} ({count} transactions vs typical {mean_daily:.1f})",
                            suggestions=[
                                "Review all transactions from this day",
                                "Check for duplicate or fraudulent transactions",
                                "Verify if this was a planned shopping day"
                            ]
                        )
                        anomalies.append(anomaly)
            
            return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"Error detecting frequency anomalies: {str(e)}")
            return []
    
    def _detect_merchant_anomalies(self, df: pd.DataFrame) -> List[SpendingAnomaly]:
        """Detect spending at unusual merchants"""
        anomalies = []
        
        try:
            # Identify merchants with only 1-2 transactions (potentially unusual)
            merchant_counts = df['merchant_name'].value_counts()
            rare_merchants = merchant_counts[merchant_counts <= 2]
            
            for merchant in rare_merchants.index:
                merchant_transactions = df[df['merchant_name'] == merchant]
                
                for _, transaction in merchant_transactions.iterrows():
                    # Check if this merchant/category combination is unusual
                    category = transaction['category']
                    amount = transaction['amount']
                    
                    # Compare with typical spending in this category
                    category_df = df[df['category'] == category]
                    typical_merchants = category_df['merchant_name'].value_counts().head(10)
                    
                    if merchant not in typical_merchants.index:
                        # Calculate anomaly score based on rarity and amount
                        category_median = category_df['amount'].median()
                        amount_ratio = amount / category_median if category_median > 0 else 1
                        
                        anomaly_score = min(5.0, 2.0 + np.log(amount_ratio))
                        
                        severity = 'medium' if amount > category_median * 2 else 'low'
                        
                        anomaly = SpendingAnomaly(
                            transaction_id=transaction['transaction_id'],
                            anomaly_type='merchant',
                            severity=severity,
                            anomaly_score=anomaly_score,
                            expected_value=None,
                            actual_value=amount,
                            reason=f"Spending at unusual merchant '{merchant}' for {category} category",
                            suggestions=[
                                f"Verify transaction at {merchant}",
                                "Check if this merchant is legitimate",
                                "Consider if this fits your typical spending pattern"
                            ]
                        )
                        anomalies.append(anomaly)
            
            return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)[:15]  # Top 15
            
        except Exception as e:
            logger.error(f"Error detecting merchant anomalies: {str(e)}")
            return []
    
    def _detect_time_anomalies(self, df: pd.DataFrame) -> List[SpendingAnomaly]:
        """Detect spending at unusual times"""
        anomalies = []
        
        try:
            # Analyze spending by hour (if available)
            if 'hour' in df.columns:
                # Identify late night transactions (11 PM - 5 AM)
                late_night_mask = (df['hour'] >= 23) | (df['hour'] <= 5)
                late_night_transactions = df[late_night_mask]
                
                for _, transaction in late_night_transactions.iterrows():
                    # Higher anomaly score for larger amounts at unusual times
                    amount = transaction['amount']
                    hour = transaction['hour']
                    
                    # Calculate anomaly score
                    if 23 <= hour <= 24 or 0 <= hour <= 2:
                        base_score = 2.5  # Very late/early
                    else:
                        base_score = 2.0  # Early morning
                    
                    # Adjust for amount
                    category_df = df[df['category'] == transaction['category']]
                    median_amount = category_df['amount'].median()
                    amount_multiplier = min(2.0, amount / median_amount if median_amount > 0 else 1.0)
                    
                    anomaly_score = base_score * amount_multiplier
                    
                    severity = 'high' if anomaly_score > 4 else 'medium' if anomaly_score > 3 else 'low'
                    
                    time_str = f"{hour:02d}:00"
                    anomaly = SpendingAnomaly(
                        transaction_id=transaction['transaction_id'],
                        anomaly_type='time',
                        severity=severity,
                        anomaly_score=anomaly_score,
                        expected_value=None,
                        actual_value=hour,
                        reason=f"Transaction at unusual time {time_str}",
                        suggestions=[
                            f"Verify transaction made at {time_str}",
                            "Check if this was an intended purchase",
                            "Consider if someone else might have used your card"
                        ]
                    )
                    anomalies.append(anomaly)
            
            return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"Error detecting time anomalies: {str(e)}")
            return []
    
    def _generate_spending_insights(
        self,
        df: pd.DataFrame,
        daily_patterns: List[SpendingPattern],
        weekly_patterns: List[SpendingPattern],
        monthly_patterns: List[SpendingPattern]
    ) -> List[SpendingInsight]:
        """Generate actionable spending insights"""
        insights = []
        
        try:
            # Weekend vs weekday spending
            weekend_spend = df[df['is_weekend']]['amount'].sum()
            weekday_spend = df[~df['is_weekend']]['amount'].sum()
            
            if weekend_spend > weekday_spend:
                insights.append(SpendingInsight(
                    insight_type='temporal',
                    category='general',
                    title='Higher Weekend Spending',
                    description=f"You spend ${weekend_spend:.2f} on weekends vs ${weekday_spend:.2f} on weekdays",
                    impact='negative',
                    actionable=True,
                    recommendations=[
                        "Plan weekend activities with a budget",
                        "Consider free or low-cost weekend activities",
                        "Set a weekend spending limit"
                    ]
                ))
            
            # Category insights
            category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
            top_category = category_spending.index[0] if len(category_spending) > 0 else None
            
            if top_category:
                top_amount = category_spending.iloc[0]
                total_spending = category_spending.sum()
                percentage = (top_amount / total_spending) * 100
                
                if percentage > 40:  # More than 40% in one category
                    insights.append(SpendingInsight(
                        insight_type='category',
                        category=top_category,
                        title='High Category Concentration',
                        description=f"{top_category} represents {percentage:.1f}% of your spending (${top_amount:.2f})",
                        impact='negative',
                        actionable=True,
                        recommendations=[
                            f"Review {top_category} expenses for optimization opportunities",
                            "Consider diversifying spending across categories",
                            f"Set a monthly budget for {top_category}"
                        ]
                    ))
            
            # Frequent merchant insights
            merchant_frequency = df['merchant_name'].value_counts()
            if len(merchant_frequency) > 0:
                top_merchant = merchant_frequency.index[0]
                visits = merchant_frequency.iloc[0]
                
                if visits > len(df) * 0.2:  # More than 20% of transactions at one merchant
                    merchant_spend = df[df['merchant_name'] == top_merchant]['amount'].sum()
                    insights.append(SpendingInsight(
                        insight_type='merchant',
                        category='general',
                        title='Frequent Merchant',
                        description=f"You visit {top_merchant} frequently ({visits} times, ${merchant_spend:.2f} total)",
                        impact='neutral',
                        actionable=True,
                        recommendations=[
                            f"Consider loyalty programs or discounts at {top_merchant}",
                            "Look for alternatives to reduce dependency",
                            "Monitor spending at frequently visited merchants"
                        ]
                    ))
            
            # Pattern-based insights
            strong_patterns = [p for p in daily_patterns + weekly_patterns + monthly_patterns if p.confidence > 0.7]
            if strong_patterns:
                insights.append(SpendingInsight(
                    insight_type='pattern',
                    category='general',
                    title='Strong Spending Patterns Detected',
                    description=f"You have {len(strong_patterns)} well-established spending patterns",
                    impact='positive',
                    actionable=True,
                    recommendations=[
                        "Use these patterns for budget planning",
                        "Set up automatic savings around predictable expenses",
                        "Monitor for deviations from established patterns"
                    ]
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating spending insights: {str(e)}")
            return []
    
    def _calculate_risk_score(
        self,
        amount_anomalies: List[SpendingAnomaly],
        frequency_anomalies: List[SpendingAnomaly],
        merchant_anomalies: List[SpendingAnomaly],
        time_anomalies: List[SpendingAnomaly]
    ) -> float:
        """Calculate overall risk score based on anomalies"""
        try:
            all_anomalies = amount_anomalies + frequency_anomalies + merchant_anomalies + time_anomalies
            
            if not all_anomalies:
                return 0.0
            
            # Weight different types of anomalies
            weights = {
                'amount': 1.0,
                'frequency': 0.8,
                'merchant': 0.9,
                'time': 0.7
            }
            
            # Severity multipliers
            severity_multipliers = {
                'low': 1.0,
                'medium': 1.5,
                'high': 2.0,
                'critical': 3.0
            }
            
            total_risk = 0.0
            for anomaly in all_anomalies:
                weight = weights.get(anomaly.anomaly_type, 1.0)
                severity_mult = severity_multipliers.get(anomaly.severity, 1.0)
                anomaly_risk = anomaly.anomaly_score * weight * severity_mult
                total_risk += anomaly_risk
            
            # Normalize to 0-100 scale
            max_possible_risk = len(all_anomalies) * 5.0 * 3.0  # Max anomaly score * max severity
            risk_score = min(100.0, (total_risk / max_possible_risk) * 100) if max_possible_risk > 0 else 0.0
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 0.0
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 75:
            return 'high'
        elif risk_score >= 50:
            return 'medium'
        elif risk_score >= 25:
            return 'low'
        else:
            return 'minimal'
    
    def _generate_pattern_recommendations(
        self,
        daily_patterns: List[SpendingPattern],
        weekly_patterns: List[SpendingPattern],
        insights: List[SpendingInsight]
    ) -> List[str]:
        """Generate recommendations based on detected patterns"""
        recommendations = []
        
        try:
            # Pattern-based recommendations
            if daily_patterns:
                strong_daily = [p for p in daily_patterns if p.confidence > 0.8]
                if strong_daily:
                    recommendations.append("Use your consistent daily spending patterns to create automatic budgets")
            
            if weekly_patterns:
                recommendations.append("Consider setting up weekly spending alerts based on your patterns")
            
            # Insight-based recommendations
            negative_insights = [i for i in insights if i.impact == 'negative']
            if negative_insights:
                recommendations.append("Address spending patterns that may be impacting your financial goals")
            
            # General recommendations
            recommendations.extend([
                "Monitor spending regularly to detect changes in patterns",
                "Set up alerts for unusual transactions",
                "Review and update your budget based on spending patterns"
            ])
            
            return recommendations[:10]  # Limit to 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating pattern recommendations: {str(e)}")
            return ["Regular monitoring of spending patterns is recommended"]


# Singleton instance
spending_pattern_detector = SpendingPatternDetector()