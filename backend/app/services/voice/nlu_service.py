"""Natural Language Understanding Service for Voice Commands."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import dateparser
from word2number import w2n
from num2words import num2words

from .config import FINANCIAL_VOCABULARY, VOICE_INTENTS

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity."""
    type: str
    value: Any
    text: str
    start: int
    end: int
    confidence: float


@dataclass
class Intent:
    """Represents a detected intent."""
    name: str
    confidence: float
    parameters: Dict[str, Any]


class EntityType(str, Enum):
    """Types of entities to extract."""
    AMOUNT = "amount"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    ACCOUNT = "account"
    ASSET = "asset"
    TICKER = "ticker"
    GOAL = "goal"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"


class NLUService:
    """Natural Language Understanding for financial voice commands."""
    
    def __init__(self):
        """Initialize the NLU service."""
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found. Using basic NLU.")
            self.nlp = None
        
        # Load transformer model for NER (optional)
        self.ner_pipeline = None
        try:
            self.ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
        except:
            logger.warning("Transformer NER model not available")
        
        # Financial entity patterns
        self.entity_patterns = self._build_entity_patterns()
        
        # Intent patterns
        self.intent_patterns = self._build_intent_patterns()
        
        # Context for multi-turn conversations
        self.conversation_context = {}
    
    def _build_entity_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for entity extraction."""
        return {
            EntityType.AMOUNT: re.compile(
                r'\$?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2})?)\s*(?:dollars?|USD)?',
                re.IGNORECASE
            ),
            EntityType.PERCENTAGE: re.compile(
                r'([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent)',
                re.IGNORECASE
            ),
            EntityType.DATE: re.compile(
                r'\b(today|tomorrow|yesterday|' +
                r'next\s+(?:week|month|year)|' +
                r'last\s+(?:week|month|year)|' +
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|' +
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}|' +
                r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?)',
                re.IGNORECASE
            ),
            EntityType.DURATION: re.compile(
                r'(\d+)\s*(years?|months?|weeks?|days?|hours?|minutes?)',
                re.IGNORECASE
            ),
            EntityType.ACCOUNT: re.compile(
                r'\b(401k|403b|ira|roth\s*ira|traditional\s*ira|' +
                r'brokerage|savings|checking|hsa|529|' +
                r'taxable|tax-deferred|retirement)\s*(?:account)?',
                re.IGNORECASE
            ),
            EntityType.ASSET: re.compile(
                r'\b(stocks?|bonds?|mutual\s*funds?|etfs?|' +
                r'equities|fixed\s*income|cash|' +
                r'real\s*estate|reits?|commodities|crypto(?:currency)?)',
                re.IGNORECASE
            ),
            EntityType.TICKER: re.compile(
                r'\b([A-Z]{1,5})\b'
            ),
            EntityType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            EntityType.PHONE: re.compile(
                r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
            )
        }
    
    def _build_intent_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build patterns for intent detection."""
        return {
            "check_balance": [
                re.compile(r'\b(?:what is|show me|check)\s+(?:my\s+)?(?:account\s+)?balance', re.I),
                re.compile(r'\bhow much\s+(?:money\s+)?(?:do I have|is in)', re.I)
            ],
            "view_portfolio": [
                re.compile(r'\b(?:show|display|view)\s+(?:my\s+)?portfolio', re.I),
                re.compile(r'\b(?:what are|show me)\s+(?:my\s+)?investments', re.I)
            ],
            "check_performance": [
                re.compile(r'\b(?:how is|show)\s+(?:my\s+)?(?:portfolio\s+)?performance', re.I),
                re.compile(r'\b(?:am I|how much)\s+(?:up|down|gained|lost)', re.I)
            ],
            "create_goal": [
                re.compile(r'\b(?:create|add|set)\s+(?:a\s+)?(?:new\s+)?(?:financial\s+)?goal', re.I),
                re.compile(r'\bI want to\s+(?:save|invest)\s+for', re.I)
            ],
            "make_transaction": [
                re.compile(r'\b(?:buy|sell|purchase)\s+(?:\$?[0-9,]+\s+(?:worth\s+)?of\s+)?', re.I),
                re.compile(r'\b(?:invest|transfer|deposit|withdraw)\s+\$?[0-9,]+', re.I)
            ],
            "calculate": [
                re.compile(r'\b(?:calculate|compute|what is|how much)\s+.*\s+(?:return|interest|growth)', re.I),
                re.compile(r'\b(?:project|forecast|estimate)\s+(?:my\s+)?(?:retirement|savings)', re.I)
            ],
            "get_advice": [
                re.compile(r'\b(?:what should I|should I|do you recommend)', re.I),
                re.compile(r'\b(?:advice|recommendation|suggestion)\s+(?:for|about|on)', re.I)
            ],
            "market_update": [
                re.compile(r'\b(?:market|stock market)\s+(?:update|news|status)', re.I),
                re.compile(r'\bhow is the\s+(?:market|S&P|Dow|Nasdaq)', re.I)
            ],
            "tax_info": [
                re.compile(r'\b(?:tax|taxes)\s+(?:implications|consequences|info)', re.I),
                re.compile(r'\b(?:capital gains|tax loss|tax deduction)', re.I)
            ]
        }
    
    def understand(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform natural language understanding on text.
        
        Args:
            text: Input text to analyze
            context: Optional conversation context
            
        Returns:
            Understanding result with intents and entities
        """
        # Update context
        if context:
            self.conversation_context.update(context)
        
        # Normalize text
        normalized_text = self._normalize_text(text)
        
        # Extract entities
        entities = self._extract_entities(normalized_text)
        
        # Detect intent
        intent = self._detect_intent(normalized_text, entities)
        
        # Resolve references
        entities, intent = self._resolve_references(entities, intent)
        
        # Perform sentiment analysis
        sentiment = self._analyze_sentiment(normalized_text)
        
        # Build response
        result = {
            "text": text,
            "normalized_text": normalized_text,
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update conversation context
        self._update_context(result)
        
        return result
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for processing."""
        # Convert to lowercase for certain operations
        text_lower = text.lower()
        
        # Expand contractions
        contractions = {
            "what's": "what is",
            "it's": "it is",
            "i'm": "i am",
            "i'd": "i would",
            "i'll": "i will",
            "i've": "i have",
            "let's": "let us",
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "shouldn't": "should not",
            "wouldn't": "would not"
        }
        
        for contraction, expansion in contractions.items():
            text_lower = text_lower.replace(contraction, expansion)
        
        # Handle numbers written as words
        try:
            # Find number words and convert them
            number_words = re.findall(
                r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|' +
                r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|' +
                r'eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|' +
                r'eighty|ninety|hundred|thousand|million|billion)\b',
                text_lower
            )
            
            for word in number_words:
                try:
                    number = w2n.word_to_num(word)
                    text_lower = text_lower.replace(word, str(number))
                except:
                    pass
        except:
            pass
        
        return text_lower
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text."""
        entities = []
        
        # Use regex patterns
        for entity_type, pattern in self.entity_patterns.items():
            for match in pattern.finditer(text):
                entities.append(Entity(
                    type=entity_type,
                    value=self._parse_entity_value(entity_type, match.group()),
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8
                ))
        
        # Use spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                entity_type = self._map_spacy_entity_type(ent.label_)
                if entity_type:
                    entities.append(Entity(
                        type=entity_type,
                        value=self._parse_entity_value(entity_type, ent.text),
                        text=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.9
                    ))
        
        # Use transformer NER if available
        if self.ner_pipeline:
            try:
                ner_results = self.ner_pipeline(text)
                for result in ner_results:
                    entity_type = self._map_transformer_entity_type(result['entity_group'])
                    if entity_type:
                        entities.append(Entity(
                            type=entity_type,
                            value=self._parse_entity_value(entity_type, result['word']),
                            text=result['word'],
                            start=result['start'],
                            end=result['end'],
                            confidence=result['score']
                        ))
            except:
                pass
        
        # Remove duplicates
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _parse_entity_value(self, entity_type: str, text: str) -> Any:
        """Parse entity value based on type."""
        if entity_type == EntityType.AMOUNT:
            # Remove currency symbols and convert to float
            value = re.sub(r'[^0-9.,]', '', text)
            value = value.replace(',', '')
            try:
                return float(value)
            except:
                return text
        
        elif entity_type == EntityType.PERCENTAGE:
            # Extract percentage value
            match = re.search(r'([0-9.]+)', text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
            return text
        
        elif entity_type == EntityType.DATE:
            # Parse date
            try:
                parsed_date = dateparser.parse(text)
                if parsed_date:
                    return parsed_date.date()
            except:
                pass
            return text
        
        elif entity_type == EntityType.DURATION:
            # Parse duration
            match = re.search(r'(\d+)\s*(\w+)', text)
            if match:
                value = int(match.group(1))
                unit = match.group(2).lower()
                
                if 'year' in unit:
                    return timedelta(days=value * 365)
                elif 'month' in unit:
                    return timedelta(days=value * 30)
                elif 'week' in unit:
                    return timedelta(weeks=value)
                elif 'day' in unit:
                    return timedelta(days=value)
                elif 'hour' in unit:
                    return timedelta(hours=value)
                elif 'minute' in unit:
                    return timedelta(minutes=value)
            
            return text
        
        return text
    
    def _map_spacy_entity_type(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types."""
        mapping = {
            "MONEY": EntityType.AMOUNT,
            "PERCENT": EntityType.PERCENTAGE,
            "DATE": EntityType.DATE,
            "TIME": EntityType.TIME,
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "CARDINAL": EntityType.NUMBER
        }
        return mapping.get(label)
    
    def _map_transformer_entity_type(self, label: str) -> Optional[str]:
        """Map transformer NER labels to our entity types."""
        mapping = {
            "PER": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "LOC": EntityType.LOCATION,
            "MISC": None  # Skip miscellaneous
        }
        return mapping.get(label)
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping highest confidence."""
        unique = {}
        
        for entity in entities:
            key = (entity.type, entity.start, entity.end)
            if key not in unique or entity.confidence > unique[key].confidence:
                unique[key] = entity
        
        return list(unique.values())
    
    def _detect_intent(self, text: str, entities: List[Entity]) -> Intent:
        """Detect user intent from text and entities."""
        best_intent = None
        best_confidence = 0
        
        # Check intent patterns
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    confidence = 0.8
                    
                    # Boost confidence if relevant entities present
                    if intent_name == "make_transaction" and any(e.type in [EntityType.AMOUNT, EntityType.ASSET] for e in entities):
                        confidence += 0.1
                    elif intent_name == "create_goal" and any(e.type in [EntityType.AMOUNT, EntityType.DATE] for e in entities):
                        confidence += 0.1
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_name
        
        # Default intent if none found
        if not best_intent:
            if "?" in text:
                best_intent = "query"
                best_confidence = 0.5
            else:
                best_intent = "unknown"
                best_confidence = 0.3
        
        # Extract parameters from entities
        parameters = self._extract_intent_parameters(best_intent, entities)
        
        return Intent(
            name=best_intent,
            confidence=best_confidence,
            parameters=parameters
        )
    
    def _extract_intent_parameters(self, intent: str, entities: List[Entity]) -> Dict[str, Any]:
        """Extract parameters for the intent from entities."""
        parameters = {}
        
        if intent == "make_transaction":
            for entity in entities:
                if entity.type == EntityType.AMOUNT:
                    parameters["amount"] = entity.value
                elif entity.type == EntityType.ASSET:
                    parameters["asset"] = entity.value
                elif entity.type == EntityType.TICKER:
                    parameters["ticker"] = entity.value
                elif entity.type == EntityType.ACCOUNT:
                    parameters["account"] = entity.value
        
        elif intent == "create_goal":
            for entity in entities:
                if entity.type == EntityType.AMOUNT:
                    parameters["target_amount"] = entity.value
                elif entity.type == EntityType.DATE:
                    parameters["target_date"] = entity.value
                elif entity.type == EntityType.DURATION:
                    parameters["timeframe"] = entity.value
        
        elif intent == "check_balance":
            for entity in entities:
                if entity.type == EntityType.ACCOUNT:
                    parameters["account"] = entity.value
        
        return parameters
    
    def _resolve_references(self, entities: List[Entity], intent: Intent) -> Tuple[List[Entity], Intent]:
        """Resolve references using conversation context."""
        # Resolve "it", "that", "this" etc.
        if self.conversation_context:
            # Check for references in the text
            reference_words = ["it", "that", "this", "them", "those"]
            
            # If we have a previous entity in context, use it
            if "last_entity" in self.conversation_context:
                # Add the referenced entity if not present
                last_entity = self.conversation_context["last_entity"]
                if not any(e.type == last_entity["type"] for e in entities):
                    entities.append(Entity(
                        type=last_entity["type"],
                        value=last_entity["value"],
                        text="[referenced]",
                        start=-1,
                        end=-1,
                        confidence=0.7
                    ))
        
        return entities, intent
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of the text."""
        # Simple sentiment analysis based on keywords
        positive_words = ["good", "great", "excellent", "happy", "pleased", "satisfied", "love", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "unhappy", "disappointed", "hate", "frustrated", "angry"]
        
        text_lower = text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_score + negative_score
        if total == 0:
            return {"positive": 0.5, "negative": 0.5, "neutral": 1.0}
        
        return {
            "positive": positive_score / total,
            "negative": negative_score / total,
            "neutral": 1.0 - (abs(positive_score - negative_score) / total)
        }
    
    def _update_context(self, result: Dict[str, Any]):
        """Update conversation context with latest understanding."""
        # Store last intent
        self.conversation_context["last_intent"] = result["intent"]
        
        # Store last entities
        if result["entities"]:
            # Store the most confident entity
            best_entity = max(result["entities"], key=lambda e: e.confidence)
            self.conversation_context["last_entity"] = {
                "type": best_entity.type,
                "value": best_entity.value
            }
        
        # Store timestamp
        self.conversation_context["last_interaction"] = result["timestamp"]
    
    def reset_context(self):
        """Reset conversation context."""
        self.conversation_context.clear()