"""Voice Command Parser and Intent Recognition."""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json

import spacy
from word2number import w2n
from num2words import num2words

from .config import VOICE_INTENTS, VOICE_SHORTCUTS, FINANCIAL_VOCABULARY

logger = logging.getLogger(__name__)


class CommandIntent(str, Enum):
    """Voice command intents."""
    NAVIGATION = "navigation"
    QUERY = "query"
    ACTION = "action"
    HELP = "help"
    CONFIRMATION = "confirmation"
    CORRECTION = "correction"
    CALCULATION = "calculation"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"


class VoiceCommandParser:
    """Parser for voice commands with financial domain understanding."""
    
    def __init__(self):
        """Initialize the voice command parser."""
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found, using basic parsing")
            self.nlp = None
        
        # Command patterns
        self.command_patterns = self._build_command_patterns()
        
        # Entity extractors
        self.entity_extractors = self._build_entity_extractors()
        
        # Context stack for multi-turn conversations
        self.context_stack: List[Dict] = []
        self.max_context_size = 10
    
    def _build_command_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for command recognition."""
        patterns = {
            CommandIntent.NAVIGATION: [
                re.compile(r"\b(go to|open|show|navigate to|display|view)\s+(.+)", re.I),
                re.compile(r"\b(take me to|bring up|pull up)\s+(.+)", re.I)
            ],
            CommandIntent.QUERY: [
                re.compile(r"\b(what is|what's|tell me about|show me|explain)\s+(.+)", re.I),
                re.compile(r"\b(how much|how many|when|where|why)\s+(.+)", re.I)
            ],
            CommandIntent.ACTION: [
                re.compile(r"\b(add|create|update|delete|save|submit)\s+(.+)", re.I),
                re.compile(r"\b(invest|withdraw|transfer|deposit|allocate)\s+(.+)", re.I),
                re.compile(r"\b(buy|sell|rebalance|adjust)\s+(.+)", re.I)
            ],
            CommandIntent.CALCULATION: [
                re.compile(r"\b(calculate|compute|determine|estimate)\s+(.+)", re.I),
                re.compile(r"\b(project|forecast|simulate|model)\s+(.+)", re.I)
            ],
            CommandIntent.COMPARISON: [
                re.compile(r"\b(compare|versus|vs|difference between)\s+(.+)", re.I),
                re.compile(r"\b(better|worse|higher|lower) than\s+(.+)", re.I)
            ],
            CommandIntent.HELP: [
                re.compile(r"\b(help|assist|guide|explain how|tutorial)", re.I),
                re.compile(r"\b(what can you do|how do I|how to)\s*(.*)", re.I)
            ],
            CommandIntent.CONFIRMATION: [
                re.compile(r"^(yes|yeah|yep|correct|confirm|approve|ok|okay)$", re.I),
                re.compile(r"^(no|nope|incorrect|cancel|reject|deny)$", re.I)
            ],
            CommandIntent.CORRECTION: [
                re.compile(r"\b(change|modify|edit|fix|correct|update) (?:that|it) to\s+(.+)", re.I),
                re.compile(r"\b(actually|I meant|make it|should be)\s+(.+)", re.I)
            ]
        }
        return patterns
    
    def _build_entity_extractors(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for entity extraction."""
        return {
            "amount": re.compile(r"\$?([\d,]+(?:\.\d{2})?)\s*(?:dollars?|USD)?", re.I),
            "percentage": re.compile(r"([\d.]+)\s*%|percent", re.I),
            "date": re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"),
            "time_period": re.compile(r"\b(\d+)\s*(year|month|week|day)s?\b", re.I),
            "account_type": re.compile(r"\b(401k|IRA|Roth IRA|brokerage|savings|checking)\b", re.I),
            "asset_type": re.compile(r"\b(stock|bond|mutual fund|ETF|cash|real estate|crypto)\b", re.I),
            "ticker": re.compile(r"\b([A-Z]{1,5})\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
        }
    
    def parse_command(self, text: str, use_context: bool = True) -> Dict[str, Any]:
        """
        Parse a voice command and extract intent and entities.
        
        Args:
            text: The voice command text
            use_context: Whether to use conversation context
            
        Returns:
            Parsed command with intent, entities, and confidence
        """
        # Normalize text
        text = text.strip()
        original_text = text
        
        # Check for shortcuts
        shortcut_result = self._check_shortcuts(text)
        if shortcut_result:
            return shortcut_result
        
        # Detect intent
        intent, confidence = self._detect_intent(text)
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Parse with NLP if available
        nlp_analysis = self._analyze_with_nlp(text) if self.nlp else {}
        
        # Apply context if enabled
        if use_context and self.context_stack:
            intent, entities = self._apply_context(intent, entities)
        
        # Build result
        result = {
            "text": original_text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "nlp_analysis": nlp_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to context stack
        self._update_context(result)
        
        return result
    
    def _check_shortcuts(self, text: str) -> Optional[Dict[str, Any]]:
        """Check if text matches a voice shortcut."""
        text_lower = text.lower().strip()
        
        for shortcut, description in VOICE_SHORTCUTS.items():
            if shortcut.lower() in text_lower:
                return {
                    "text": text,
                    "intent": CommandIntent.ACTION,
                    "confidence": 1.0,
                    "shortcut": shortcut,
                    "action": description,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return None
    
    def _detect_intent(self, text: str) -> Tuple[CommandIntent, float]:
        """Detect the intent of the command."""
        text_lower = text.lower()
        
        # Check each intent pattern
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return intent, 0.9
        
        # Check for intent keywords
        for intent_type, keywords in VOICE_INTENTS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent = CommandIntent(intent_type)
                    return intent, 0.7
        
        # Default to query if it's a question
        if text.strip().endswith("?") or text_lower.startswith(("what", "how", "when", "where", "why")):
            return CommandIntent.QUERY, 0.6
        
        return CommandIntent.UNKNOWN, 0.3
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from the command text."""
        entities = {}
        
        for entity_type, pattern in self.entity_extractors.items():
            matches = pattern.findall(text)
            if matches:
                if entity_type in ["amount", "percentage"]:
                    # Convert to numeric value
                    entities[entity_type] = self._parse_numeric(matches[0])
                elif entity_type == "time_period":
                    # Parse time period
                    entities[entity_type] = {
                        "value": int(matches[0][0]),
                        "unit": matches[0][1].lower()
                    }
                else:
                    entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        # Extract numbers from words
        word_numbers = self._extract_word_numbers(text)
        if word_numbers:
            entities["word_numbers"] = word_numbers
        
        return entities
    
    def _parse_numeric(self, value: str) -> float:
        """Parse numeric value from string."""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', str(value))
            return float(cleaned)
        except:
            return 0.0
    
    def _extract_word_numbers(self, text: str) -> List[int]:
        """Extract numbers written as words."""
        numbers = []
        words = text.lower().split()
        
        for word in words:
            try:
                # Try to convert word to number
                num = w2n.word_to_num(word)
                numbers.append(num)
            except:
                pass
        
        return numbers
    
    def _analyze_with_nlp(self, text: str) -> Dict[str, Any]:
        """Analyze text using spaCy NLP."""
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        
        # Extract named entities
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        # Extract key phrases (noun phrases)
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        # Extract action verbs
        verbs = [token.text for token in doc if token.pos_ == "VERB"]
        
        # Dependency parsing for better understanding
        dependencies = []
        for token in doc:
            if token.dep_ in ["dobj", "pobj", "nsubj"]:
                dependencies.append({
                    "text": token.text,
                    "dep": token.dep_,
                    "head": token.head.text
                })
        
        return {
            "entities": entities,
            "noun_phrases": noun_phrases,
            "verbs": verbs,
            "dependencies": dependencies
        }
    
    def _apply_context(
        self,
        intent: CommandIntent,
        entities: Dict[str, Any]
    ) -> Tuple[CommandIntent, Dict[str, Any]]:
        """Apply conversation context to improve understanding."""
        if not self.context_stack:
            return intent, entities
        
        last_context = self.context_stack[-1]
        
        # If intent is unknown, try to infer from context
        if intent == CommandIntent.UNKNOWN:
            if last_context.get("intent") == CommandIntent.QUERY:
                # Follow-up questions likely continue the query
                intent = CommandIntent.QUERY
        
        # Carry over entities from context if not specified
        if last_context.get("entities"):
            for key, value in last_context["entities"].items():
                if key not in entities:
                    entities[f"context_{key}"] = value
        
        return intent, entities
    
    def _update_context(self, parsed_command: Dict[str, Any]):
        """Update conversation context stack."""
        # Add to context
        self.context_stack.append({
            "intent": parsed_command["intent"],
            "entities": parsed_command.get("entities", {}),
            "timestamp": parsed_command["timestamp"]
        })
        
        # Limit context size
        if len(self.context_stack) > self.max_context_size:
            self.context_stack.pop(0)
    
    def clear_context(self):
        """Clear conversation context."""
        self.context_stack.clear()
    
    def format_response_for_speech(self, data: Any) -> str:
        """
        Format data for speech synthesis.
        
        Args:
            data: Data to format (dict, list, number, etc.)
            
        Returns:
            Speech-friendly text
        """
        if isinstance(data, dict):
            return self._format_dict_for_speech(data)
        elif isinstance(data, list):
            return self._format_list_for_speech(data)
        elif isinstance(data, (int, float)):
            return self._format_number_for_speech(data)
        else:
            return str(data)
    
    def _format_dict_for_speech(self, data: Dict) -> str:
        """Format dictionary for speech."""
        parts = []
        
        for key, value in data.items():
            # Convert camelCase or snake_case to readable
            readable_key = re.sub(r'([A-Z])', r' \1', key)
            readable_key = readable_key.replace('_', ' ').strip().title()
            
            # Format value
            if isinstance(value, (int, float)):
                formatted_value = self._format_number_for_speech(value)
            else:
                formatted_value = str(value)
            
            parts.append(f"{readable_key}: {formatted_value}")
        
        return ". ".join(parts)
    
    def _format_list_for_speech(self, data: List) -> str:
        """Format list for speech."""
        if not data:
            return "No items"
        
        if len(data) == 1:
            return self.format_response_for_speech(data[0])
        
        # Format items
        formatted_items = []
        for i, item in enumerate(data[:5], 1):  # Limit to first 5 items
            if isinstance(item, dict) and "name" in item:
                formatted_items.append(f"{i}. {item['name']}")
            else:
                formatted_items.append(f"{i}. {self.format_response_for_speech(item)}")
        
        result = ", ".join(formatted_items)
        
        if len(data) > 5:
            result += f", and {len(data) - 5} more items"
        
        return result
    
    def _format_number_for_speech(self, number: float) -> str:
        """Format number for speech."""
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f} billion"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.1f} million"
        elif number >= 1_000:
            return f"{number / 1_000:.1f} thousand"
        elif number < 1 and number > 0:
            # Handle percentages and decimals
            if number < 0.01:
                return f"{number * 100:.2f} percent"
            else:
                return f"{number:.2f}"
        else:
            return f"{number:,.0f}"
    
    def generate_confirmation_prompt(
        self,
        action: str,
        entities: Dict[str, Any]
    ) -> str:
        """
        Generate a confirmation prompt for an action.
        
        Args:
            action: The action to confirm
            entities: Extracted entities
            
        Returns:
            Confirmation prompt text
        """
        prompt_parts = [f"Please confirm: {action}"]
        
        if "amount" in entities:
            prompt_parts.append(f"Amount: ${entities['amount']:,.2f}")
        
        if "account_type" in entities:
            prompt_parts.append(f"Account: {entities['account_type']}")
        
        if "asset_type" in entities:
            prompt_parts.append(f"Asset: {entities['asset_type']}")
        
        if "time_period" in entities:
            period = entities["time_period"]
            prompt_parts.append(f"Period: {period['value']} {period['unit']}(s)")
        
        prompt_parts.append("Say 'yes' to confirm or 'no' to cancel.")
        
        return " ".join(prompt_parts)
    
    def get_help_response(self, topic: Optional[str] = None) -> str:
        """
        Generate help response.
        
        Args:
            topic: Specific help topic
            
        Returns:
            Help text
        """
        if not topic:
            return self._get_general_help()
        
        topic_lower = topic.lower()
        
        # Topic-specific help
        help_topics = {
            "navigation": "You can navigate by saying: 'Go to portfolio', 'Show my goals', or 'Open settings'.",
            "portfolio": "Ask about your portfolio: 'What's my portfolio value?', 'Show portfolio performance', or 'Display asset allocation'.",
            "goals": "Manage goals: 'Show retirement goal', 'Add new goal', or 'Update savings goal'.",
            "transactions": "For transactions: 'Invest 1000 dollars', 'Withdraw from IRA', or 'Show recent transactions'.",
            "analysis": "Request analysis: 'Calculate retirement projection', 'Compare portfolios', or 'Run Monte Carlo simulation'.",
            "shortcuts": "Available shortcuts: " + ", ".join(f"'{k}'" for k in list(VOICE_SHORTCUTS.keys())[:5])
        }
        
        for key, response in help_topics.items():
            if key in topic_lower:
                return response
        
        return self._get_general_help()
    
    def _get_general_help(self) -> str:
        """Get general help text."""
        return (
            "I can help you with: "
            "Viewing your portfolio and goals, "
            "Making investments and transactions, "
            "Running financial calculations and projections, "
            "and answering questions about your finances. "
            "Just tell me what you'd like to do, or say 'help' followed by a topic for specific guidance."
        )