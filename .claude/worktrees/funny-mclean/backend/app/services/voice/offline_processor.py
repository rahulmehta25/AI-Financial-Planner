"""Offline Voice Processing for Network-Independent Operation."""

import logging
import json
import pickle
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

from .config import VoiceSettings, FINANCIAL_VOCABULARY, VOICE_INTENTS

logger = logging.getLogger(__name__)


class OfflineCommandProcessor:
    """Process voice commands offline using local models."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize offline processor."""
        self.settings = settings or VoiceSettings()
        
        # Model paths
        self.model_dir = Path("models/voice")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Intent classifier
        self.intent_classifier = None
        self.intent_vectorizer = None
        
        # Command patterns
        self.command_patterns = self._build_command_patterns()
        
        # Cached responses
        self.response_cache = {}
        
        # Load or train models
        self._initialize_models()
    
    def _build_command_patterns(self) -> Dict[str, List[str]]:
        """Build offline command patterns."""
        return {
            "check_balance": [
                "show balance",
                "check balance",
                "how much money",
                "account balance",
                "what is my balance"
            ],
            "view_portfolio": [
                "show portfolio",
                "view investments",
                "portfolio summary",
                "investment overview",
                "show my stocks"
            ],
            "check_goals": [
                "show goals",
                "financial goals",
                "goal progress",
                "retirement progress",
                "savings goals"
            ],
            "recent_transactions": [
                "recent transactions",
                "latest trades",
                "recent activity",
                "transaction history",
                "what did I buy"
            ],
            "market_update": [
                "market update",
                "market status",
                "how is the market",
                "stock market today",
                "market performance"
            ],
            "help": [
                "help",
                "what can you do",
                "available commands",
                "how do I",
                "show commands"
            ],
            "calculator": [
                "calculate",
                "compute",
                "how much will",
                "interest calculator",
                "retirement calculator"
            ]
        }
    
    def _initialize_models(self):
        """Initialize or load offline models."""
        intent_model_path = self.model_dir / "intent_classifier.pkl"
        
        if intent_model_path.exists():
            # Load existing model
            try:
                with open(intent_model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.intent_classifier = model_data['classifier']
                    self.intent_vectorizer = model_data['vectorizer']
                logger.info("Loaded offline intent classifier")
            except Exception as e:
                logger.error(f"Failed to load intent model: {e}")
                self._train_intent_classifier()
        else:
            # Train new model
            self._train_intent_classifier()
    
    def _train_intent_classifier(self):
        """Train intent classification model."""
        logger.info("Training offline intent classifier")
        
        # Prepare training data
        X_train = []
        y_train = []
        
        for intent, examples in self.command_patterns.items():
            for example in examples:
                X_train.append(example)
                y_train.append(intent)
                
                # Add variations
                X_train.append(f"please {example}")
                y_train.append(intent)
                
                X_train.append(f"can you {example}")
                y_train.append(intent)
                
                X_train.append(f"I want to {example}")
                y_train.append(intent)
        
        # Create and train model
        self.intent_vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        X_vectors = self.intent_vectorizer.fit_transform(X_train)
        
        self.intent_classifier = MultinomialNB(alpha=0.1)
        self.intent_classifier.fit(X_vectors, y_train)
        
        # Save model
        model_path = self.model_dir / "intent_classifier.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump({
                'classifier': self.intent_classifier,
                'vectorizer': self.intent_vectorizer
            }, f)
        
        logger.info("Intent classifier trained and saved")
    
    def process_command(self, text: str) -> Dict[str, Any]:
        """
        Process voice command offline.
        
        Args:
            text: Command text
            
        Returns:
            Processing result
        """
        # Normalize text
        text_lower = text.lower().strip()
        
        # Check cache
        if text_lower in self.response_cache:
            cached = self.response_cache[text_lower]
            cached["from_cache"] = True
            return cached
        
        # Detect intent
        intent = self._detect_intent(text_lower)
        
        # Extract entities
        entities = self._extract_entities_offline(text_lower)
        
        # Generate response
        response = self._generate_response(intent, entities, text)
        
        # Cache response
        self.response_cache[text_lower] = response
        
        # Limit cache size
        if len(self.response_cache) > 100:
            # Remove oldest entry
            oldest = min(self.response_cache.keys())
            del self.response_cache[oldest]
        
        return response
    
    def _detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect intent from text."""
        if self.intent_classifier and self.intent_vectorizer:
            try:
                # Use trained model
                X = self.intent_vectorizer.transform([text])
                intent = self.intent_classifier.predict(X)[0]
                proba = self.intent_classifier.predict_proba(X)[0]
                confidence = float(np.max(proba))
                
                return {
                    "name": intent,
                    "confidence": confidence
                }
            except:
                pass
        
        # Fallback to pattern matching
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return {
                        "name": intent,
                        "confidence": 0.7
                    }
        
        # Default
        return {
            "name": "unknown",
            "confidence": 0.3
        }
    
    def _extract_entities_offline(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text offline."""
        entities = []
        
        # Extract numbers
        import re
        
        # Money amounts
        money_pattern = r'\$([0-9,]+(?:\.[0-9]{2})?)|([0-9,]+(?:\.[0-9]{2})?)\s*dollars?'
        for match in re.finditer(money_pattern, text, re.I):
            value = match.group(1) or match.group(2)
            if value:
                entities.append({
                    "type": "amount",
                    "value": float(value.replace(',', '')),
                    "text": match.group()
                })
        
        # Percentages
        percent_pattern = r'([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent)'
        for match in re.finditer(percent_pattern, text, re.I):
            entities.append({
                "type": "percentage",
                "value": float(match.group(1)),
                "text": match.group()
            })
        
        # Time periods
        time_pattern = r'(\d+)\s*(years?|months?|weeks?|days?)'
        for match in re.finditer(time_pattern, text, re.I):
            entities.append({
                "type": "duration",
                "value": int(match.group(1)),
                "unit": match.group(2),
                "text": match.group()
            })
        
        # Account types
        for account in ['401k', 'ira', 'roth ira', 'brokerage', 'savings', 'checking']:
            if account in text:
                entities.append({
                    "type": "account",
                    "value": account,
                    "text": account
                })
        
        # Asset types
        for asset in ['stocks', 'bonds', 'etf', 'mutual fund', 'cash']:
            if asset in text:
                entities.append({
                    "type": "asset",
                    "value": asset,
                    "text": asset
                })
        
        return entities
    
    def _generate_response(self, intent: Dict, entities: List[Dict], original_text: str) -> Dict[str, Any]:
        """Generate response for offline command."""
        intent_name = intent["name"]
        
        # Build response based on intent
        response = {
            "success": True,
            "intent": intent,
            "entities": entities,
            "original_text": original_text,
            "offline_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add intent-specific information
        if intent_name == "check_balance":
            response["action"] = "show_balance_screen"
            response["message"] = "Opening balance view..."
            
            # Check for specific account
            account_entities = [e for e in entities if e["type"] == "account"]
            if account_entities:
                response["parameters"] = {"account": account_entities[0]["value"]}
        
        elif intent_name == "view_portfolio":
            response["action"] = "show_portfolio_screen"
            response["message"] = "Loading portfolio overview..."
        
        elif intent_name == "check_goals":
            response["action"] = "show_goals_screen"
            response["message"] = "Displaying financial goals..."
        
        elif intent_name == "recent_transactions":
            response["action"] = "show_transactions_screen"
            response["message"] = "Loading recent transactions..."
        
        elif intent_name == "market_update":
            response["action"] = "show_market_screen"
            response["message"] = "Fetching market data..."
        
        elif intent_name == "calculator":
            response["action"] = "open_calculator"
            response["message"] = "Opening financial calculator..."
            
            # Check for calculation type
            if "retirement" in original_text.lower():
                response["calculator_type"] = "retirement"
            elif "interest" in original_text.lower():
                response["calculator_type"] = "compound_interest"
            elif "loan" in original_text.lower():
                response["calculator_type"] = "loan"
        
        elif intent_name == "help":
            response["action"] = "show_help"
            response["message"] = "Here are available voice commands..."
            response["available_commands"] = self._get_help_text()
        
        else:
            response["action"] = "unknown"
            response["message"] = "I didn't understand that command. Try saying 'help' for available commands."
            response["success"] = False
        
        return response
    
    def _get_help_text(self) -> List[str]:
        """Get help text for available commands."""
        return [
            "Say 'check balance' to view account balances",
            "Say 'show portfolio' to see your investments",
            "Say 'show goals' to check financial goal progress",
            "Say 'recent transactions' to view recent activity",
            "Say 'market update' for market status",
            "Say 'calculator' to open financial calculators",
            "Say 'help' to hear these commands again"
        ]
    
    def train_custom_commands(
        self,
        commands: Dict[str, List[str]],
        retrain: bool = False
    ) -> bool:
        """
        Train on custom commands.
        
        Args:
            commands: Dictionary of intent to example commands
            retrain: Whether to retrain from scratch
            
        Returns:
            True if training successful
        """
        try:
            if retrain:
                self.command_patterns = commands
            else:
                # Merge with existing patterns
                for intent, examples in commands.items():
                    if intent in self.command_patterns:
                        self.command_patterns[intent].extend(examples)
                    else:
                        self.command_patterns[intent] = examples
            
            # Retrain classifier
            self._train_intent_classifier()
            
            # Clear cache
            self.response_cache.clear()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to train custom commands: {e}")
            return False
    
    def export_model(self, path: str) -> bool:
        """
        Export trained model.
        
        Args:
            path: Export path
            
        Returns:
            True if export successful
        """
        try:
            export_data = {
                'classifier': self.intent_classifier,
                'vectorizer': self.intent_vectorizer,
                'command_patterns': self.command_patterns,
                'version': '1.0',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(path, 'wb') as f:
                pickle.dump(export_data, f)
            
            logger.info(f"Model exported to {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to export model: {e}")
            return False
    
    def import_model(self, path: str) -> bool:
        """
        Import trained model.
        
        Args:
            path: Import path
            
        Returns:
            True if import successful
        """
        try:
            with open(path, 'rb') as f:
                export_data = pickle.load(f)
            
            self.intent_classifier = export_data['classifier']
            self.intent_vectorizer = export_data['vectorizer']
            self.command_patterns = export_data['command_patterns']
            
            # Clear cache
            self.response_cache.clear()
            
            logger.info(f"Model imported from {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to import model: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get offline processor statistics."""
        return {
            "model_trained": self.intent_classifier is not None,
            "intents_count": len(self.command_patterns),
            "total_patterns": sum(len(p) for p in self.command_patterns.values()),
            "cache_size": len(self.response_cache),
            "model_dir": str(self.model_dir)
        }