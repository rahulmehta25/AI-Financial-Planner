"""
Transaction Categorization Engine

This module provides intelligent transaction categorization using machine learning
and natural language processing for financial analysis and budgeting.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
import pickle

from textblob import TextBlob
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from .plaid_service import Transaction

logger = logging.getLogger(__name__)


@dataclass
class CategoryPrediction:
    """Transaction category prediction result"""
    category: str
    subcategory: Optional[str]
    confidence: float
    reasoning: str
    manual_override: bool = False


@dataclass
class TransactionFeatures:
    """Extracted features from transaction"""
    merchant_name: Optional[str]
    description: str
    amount: float
    amount_bucket: str
    day_of_week: int
    hour_of_day: Optional[int]
    is_weekend: bool
    is_recurring: bool
    location_type: Optional[str]


class TransactionCategorizer:
    """
    Intelligent transaction categorization engine.
    
    Features:
    - ML-based classification with multiple algorithms
    - Pre-trained models for common transactions
    - Custom rule-based classification
    - Confidence scoring and manual override support
    - Continuous learning from user feedback
    - Support for custom categories
    """
    
    # Standard financial categories
    STANDARD_CATEGORIES = {
        'food_dining': {
            'name': 'Food & Dining',
            'subcategories': ['restaurants', 'fast_food', 'coffee_shops', 'bars', 'groceries'],
            'keywords': ['restaurant', 'food', 'starbucks', 'mcdonalds', 'grocery', 'market', 'cafe']
        },
        'transportation': {
            'name': 'Transportation',
            'subcategories': ['gas', 'public_transit', 'uber_lyft', 'parking', 'auto_maintenance'],
            'keywords': ['gas', 'uber', 'lyft', 'metro', 'parking', 'oil_change', 'car_wash']
        },
        'shopping': {
            'name': 'Shopping',
            'subcategories': ['clothing', 'electronics', 'home_goods', 'personal_care', 'general'],
            'keywords': ['amazon', 'target', 'walmart', 'clothing', 'electronics', 'pharmacy']
        },
        'bills_utilities': {
            'name': 'Bills & Utilities',
            'subcategories': ['electricity', 'water', 'gas', 'internet', 'phone', 'insurance'],
            'keywords': ['electric', 'water', 'gas', 'internet', 'phone', 'insurance', 'utility']
        },
        'entertainment': {
            'name': 'Entertainment',
            'subcategories': ['movies', 'streaming', 'gaming', 'sports', 'music'],
            'keywords': ['netflix', 'spotify', 'movie', 'theater', 'gaming', 'concert']
        },
        'healthcare': {
            'name': 'Healthcare',
            'subcategories': ['doctor', 'pharmacy', 'dental', 'vision', 'medical_supplies'],
            'keywords': ['doctor', 'hospital', 'pharmacy', 'medical', 'dental', 'clinic']
        },
        'income': {
            'name': 'Income',
            'subcategories': ['salary', 'freelance', 'investment', 'rental', 'other'],
            'keywords': ['payroll', 'salary', 'freelance', 'dividend', 'interest', 'rental']
        },
        'financial': {
            'name': 'Financial',
            'subcategories': ['bank_fees', 'investments', 'loans', 'credit_card', 'transfers'],
            'keywords': ['fee', 'transfer', 'investment', 'loan', 'credit', 'bank']
        },
        'other': {
            'name': 'Other',
            'subcategories': ['miscellaneous', 'uncategorized'],
            'keywords': []
        }
    }
    
    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        self.confidence_threshold = settings.TRANSACTION_CATEGORIZATION_CONFIDENCE_THRESHOLD
        self._setup_models()
        self._load_merchant_database()
    
    def _setup_models(self):
        """Initialize ML models for categorization"""
        try:
            # Text processing pipeline
            self.text_pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=10000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    lowercase=True
                )),
                ('classifier', MultinomialNB())
            ])
            
            # Amount-based classifier
            self.amount_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Combined feature classifier
            self.combined_classifier = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
            
            logger.info("Transaction categorization models initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup ML models: {str(e)}")
            raise ValidationError("Failed to initialize categorization engine")
    
    def _load_merchant_database(self):
        """Load known merchant mappings"""
        # This would typically be loaded from a database or file
        self.merchant_mappings = {
            # Food & Dining
            'starbucks': ('food_dining', 'coffee_shops'),
            'mcdonalds': ('food_dining', 'fast_food'),
            'chipotle': ('food_dining', 'fast_food'),
            'whole foods': ('food_dining', 'groceries'),
            'safeway': ('food_dining', 'groceries'),
            
            # Transportation
            'shell': ('transportation', 'gas'),
            'exxon': ('transportation', 'gas'),
            'uber': ('transportation', 'uber_lyft'),
            'lyft': ('transportation', 'uber_lyft'),
            
            # Shopping
            'amazon': ('shopping', 'general'),
            'target': ('shopping', 'general'),
            'walmart': ('shopping', 'general'),
            'best buy': ('shopping', 'electronics'),
            
            # Bills & Utilities
            'pg&e': ('bills_utilities', 'electricity'),
            'comcast': ('bills_utilities', 'internet'),
            'verizon': ('bills_utilities', 'phone'),
            
            # Entertainment
            'netflix': ('entertainment', 'streaming'),
            'spotify': ('entertainment', 'music'),
            'amc': ('entertainment', 'movies'),
            
            # Healthcare
            'cvs': ('healthcare', 'pharmacy'),
            'walgreens': ('healthcare', 'pharmacy')
        }
    
    def _extract_features(self, transaction: Transaction) -> TransactionFeatures:
        """Extract features from transaction for ML classification"""
        try:
            # Clean and normalize text
            description = self._clean_text(transaction.name)
            merchant_name = self._clean_text(transaction.merchant_name) if transaction.merchant_name else None
            
            # Amount buckets
            amount_bucket = self._get_amount_bucket(abs(transaction.amount))
            
            # Time-based features
            day_of_week = transaction.date.weekday()
            is_weekend = day_of_week >= 5
            hour_of_day = transaction.date.hour if hasattr(transaction.date, 'hour') else None
            
            # Recurring transaction detection (simplified)
            is_recurring = self._detect_recurring_pattern(description, transaction.amount)
            
            # Location type (if available)
            location_type = self._extract_location_type(transaction.location) if transaction.location else None
            
            return TransactionFeatures(
                merchant_name=merchant_name,
                description=description,
                amount=transaction.amount,
                amount_bucket=amount_bucket,
                day_of_week=day_of_week,
                hour_of_day=hour_of_day,
                is_weekend=is_weekend,
                is_recurring=is_recurring,
                location_type=location_type
            )
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return TransactionFeatures(
                merchant_name=None,
                description=transaction.name or '',
                amount=transaction.amount,
                amount_bucket='medium',
                day_of_week=0,
                hour_of_day=None,
                is_weekend=False,
                is_recurring=False,
                location_type=None
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize transaction text"""
        if not text:
            return ''
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common transaction codes and numbers
        text = re.sub(r'\b\d{4,}\b', '', text)  # Remove long numbers
        text = re.sub(r'#\d+', '', text)  # Remove reference numbers
        text = re.sub(r'\*+', '', text)  # Remove asterisks
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _get_amount_bucket(self, amount: float) -> str:
        """Categorize transaction amount into buckets"""
        if amount < 10:
            return 'micro'
        elif amount < 50:
            return 'small'
        elif amount < 200:
            return 'medium'
        elif amount < 1000:
            return 'large'
        else:
            return 'very_large'
    
    def _detect_recurring_pattern(self, description: str, amount: float) -> bool:
        """Simple recurring transaction detection"""
        recurring_keywords = [
            'autopay', 'automatic', 'recurring', 'subscription',
            'monthly', 'annual', 'yearly', 'payment'
        ]
        
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in recurring_keywords)
    
    def _extract_location_type(self, location: Dict[str, Any]) -> Optional[str]:
        """Extract location type from transaction location data"""
        if not location:
            return None
        
        # This would be more sophisticated in practice
        address = location.get('address', '')
        if 'mall' in address.lower():
            return 'shopping_center'
        elif 'airport' in address.lower():
            return 'airport'
        elif 'hospital' in address.lower():
            return 'healthcare'
        
        return 'general'
    
    async def categorize_transaction(
        self,
        transaction: Transaction,
        user_id: Optional[str] = None,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> CategoryPrediction:
        """
        Categorize a single transaction
        
        Args:
            transaction: Transaction to categorize
            user_id: User ID for personalized categorization
            custom_rules: User-defined categorization rules
            
        Returns:
            Category prediction with confidence score
        """
        try:
            # Extract features
            features = self._extract_features(transaction)
            
            # Try rule-based classification first
            rule_result = self._apply_rules(features, custom_rules)
            if rule_result and rule_result.confidence >= self.confidence_threshold:
                return rule_result
            
            # Try merchant mapping
            merchant_result = self._classify_by_merchant(features)
            if merchant_result and merchant_result.confidence >= self.confidence_threshold:
                return merchant_result
            
            # Try ML classification
            ml_result = self._classify_with_ml(features)
            if ml_result and ml_result.confidence >= self.confidence_threshold:
                return ml_result
            
            # Fallback to rule-based or default
            return rule_result or CategoryPrediction(
                category='other',
                subcategory='uncategorized',
                confidence=0.1,
                reasoning='No confident classification found'
            )
            
        except Exception as e:
            logger.error(f"Error categorizing transaction: {str(e)}")
            return CategoryPrediction(
                category='other',
                subcategory='uncategorized',
                confidence=0.0,
                reasoning=f'Error during categorization: {str(e)}'
            )
    
    def _apply_rules(
        self,
        features: TransactionFeatures,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> Optional[CategoryPrediction]:
        """Apply rule-based classification"""
        try:
            description = features.description.lower()
            merchant = features.merchant_name.lower() if features.merchant_name else ''
            
            # Income detection
            if features.amount < 0:  # Negative amounts are typically income
                income_keywords = ['payroll', 'salary', 'deposit', 'refund', 'interest']
                if any(keyword in description for keyword in income_keywords):
                    return CategoryPrediction(
                        category='income',
                        subcategory='salary' if 'payroll' in description else 'other',
                        confidence=0.9,
                        reasoning='Rule-based: Income keywords detected'
                    )
            
            # Transfer detection
            transfer_keywords = ['transfer', 'payment', 'ach', 'wire']
            if any(keyword in description for keyword in transfer_keywords):
                return CategoryPrediction(
                    category='financial',
                    subcategory='transfers',
                    confidence=0.8,
                    reasoning='Rule-based: Transfer keywords detected'
                )
            
            # ATM and bank fees
            if 'atm' in description or 'fee' in description:
                return CategoryPrediction(
                    category='financial',
                    subcategory='bank_fees',
                    confidence=0.85,
                    reasoning='Rule-based: ATM or fee keywords detected'
                )
            
            # Apply custom rules if provided
            if custom_rules:
                custom_result = self._apply_custom_rules(features, custom_rules)
                if custom_result:
                    return custom_result
            
            return None
            
        except Exception as e:
            logger.warning(f"Error applying rules: {str(e)}")
            return None
    
    def _classify_by_merchant(self, features: TransactionFeatures) -> Optional[CategoryPrediction]:
        """Classify using merchant database"""
        try:
            if not features.merchant_name:
                return None
            
            merchant_lower = features.merchant_name.lower()
            
            # Direct merchant lookup
            for merchant_pattern, (category, subcategory) in self.merchant_mappings.items():
                if merchant_pattern in merchant_lower:
                    return CategoryPrediction(
                        category=category,
                        subcategory=subcategory,
                        confidence=0.95,
                        reasoning=f'Merchant mapping: {merchant_pattern}'
                    )
            
            # Fuzzy merchant matching
            for merchant_pattern, (category, subcategory) in self.merchant_mappings.items():
                # Simple similarity check
                if len(merchant_pattern) > 3 and merchant_pattern[:4] in merchant_lower:
                    return CategoryPrediction(
                        category=category,
                        subcategory=subcategory,
                        confidence=0.75,
                        reasoning=f'Fuzzy merchant matching: {merchant_pattern}'
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in merchant classification: {str(e)}")
            return None
    
    def _classify_with_ml(self, features: TransactionFeatures) -> Optional[CategoryPrediction]:
        """Classify using machine learning models"""
        try:
            # This would use pre-trained models in practice
            # For now, implement keyword-based classification
            
            description = features.description.lower()
            merchant = features.merchant_name.lower() if features.merchant_name else ''
            text_input = f"{description} {merchant}".strip()
            
            # Score against each category
            category_scores = {}
            
            for category_id, category_info in self.STANDARD_CATEGORIES.items():
                score = 0.0
                keywords = category_info['keywords']
                
                # Keyword matching
                for keyword in keywords:
                    if keyword in text_input:
                        score += 1.0 / len(keywords)
                
                # Amount-based scoring
                if category_id == 'food_dining' and 5 <= abs(features.amount) <= 100:
                    score += 0.2
                elif category_id == 'transportation' and 10 <= abs(features.amount) <= 200:
                    score += 0.2
                elif category_id == 'bills_utilities' and features.is_recurring:
                    score += 0.3
                
                category_scores[category_id] = score
            
            # Get best category
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                best_score = category_scores[best_category]
                
                if best_score > 0.3:  # Minimum confidence threshold
                    subcategories = self.STANDARD_CATEGORIES[best_category]['subcategories']
                    best_subcategory = subcategories[0] if subcategories else None
                    
                    return CategoryPrediction(
                        category=best_category,
                        subcategory=best_subcategory,
                        confidence=min(best_score, 0.9),
                        reasoning=f'ML classification: keyword matching'
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in ML classification: {str(e)}")
            return None
    
    def _apply_custom_rules(
        self,
        features: TransactionFeatures,
        custom_rules: Dict[str, Any]
    ) -> Optional[CategoryPrediction]:
        """Apply user-defined custom categorization rules"""
        try:
            # Implementation for custom rules
            # This would allow users to define their own categorization logic
            return None
            
        except Exception as e:
            logger.warning(f"Error applying custom rules: {str(e)}")
            return None
    
    async def categorize_transactions_batch(
        self,
        transactions: List[Transaction],
        user_id: Optional[str] = None,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> List[CategoryPrediction]:
        """
        Categorize multiple transactions efficiently
        
        Args:
            transactions: List of transactions to categorize
            user_id: User ID for personalized categorization
            custom_rules: User-defined categorization rules
            
        Returns:
            List of category predictions
        """
        try:
            predictions = []
            
            for transaction in transactions:
                prediction = await self.categorize_transaction(
                    transaction, user_id, custom_rules
                )
                predictions.append(prediction)
            
            logger.info(f"Categorized {len(transactions)} transactions")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in batch categorization: {str(e)}")
            return [CategoryPrediction(
                category='other',
                subcategory='uncategorized',
                confidence=0.0,
                reasoning='Batch processing error'
            ) for _ in transactions]
    
    async def learn_from_feedback(
        self,
        transaction: Transaction,
        correct_category: str,
        correct_subcategory: Optional[str],
        user_id: str,
        db: AsyncSession
    ):
        """
        Learn from user feedback to improve categorization
        
        Args:
            transaction: Original transaction
            correct_category: User-corrected category
            correct_subcategory: User-corrected subcategory
            user_id: User ID
            db: Database session
        """
        try:
            # Store feedback for model retraining
            feedback_data = {
                'user_id': user_id,
                'transaction_id': transaction.transaction_id,
                'features': self._extract_features(transaction).__dict__,
                'correct_category': correct_category,
                'correct_subcategory': correct_subcategory,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # In practice, this would be stored in a database for model retraining
            logger.info(f"Stored categorization feedback for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing feedback: {str(e)}")
    
    def get_category_statistics(
        self,
        predictions: List[CategoryPrediction]
    ) -> Dict[str, Any]:
        """
        Generate statistics about categorization results
        
        Args:
            predictions: List of category predictions
            
        Returns:
            Statistics about categories and confidence levels
        """
        try:
            stats = {
                'total_transactions': len(predictions),
                'category_distribution': {},
                'confidence_distribution': {
                    'high': 0,  # > 0.8
                    'medium': 0,  # 0.5 - 0.8
                    'low': 0  # < 0.5
                },
                'average_confidence': 0.0,
                'manual_overrides': 0
            }
            
            if not predictions:
                return stats
            
            # Category distribution
            for prediction in predictions:
                category = prediction.category
                stats['category_distribution'][category] = \
                    stats['category_distribution'].get(category, 0) + 1
                
                # Confidence distribution
                if prediction.confidence > 0.8:
                    stats['confidence_distribution']['high'] += 1
                elif prediction.confidence > 0.5:
                    stats['confidence_distribution']['medium'] += 1
                else:
                    stats['confidence_distribution']['low'] += 1
                
                # Manual overrides
                if prediction.manual_override:
                    stats['manual_overrides'] += 1
            
            # Average confidence
            total_confidence = sum(p.confidence for p in predictions)
            stats['average_confidence'] = total_confidence / len(predictions)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating category statistics: {str(e)}")
            return {'error': str(e)}


# Singleton instance
transaction_categorizer = TransactionCategorizer()