"""Conversation Flow Manager for Voice-Guided Interactions."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json

from .voice_commands import CommandIntent

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation flow states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COLLECTING_INFO = "collecting_info"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


class FormField:
    """Represents a form field for voice collection."""
    
    def __init__(
        self,
        name: str,
        prompt: str,
        field_type: str,
        required: bool = True,
        validation: Optional[Callable] = None,
        options: Optional[List[str]] = None,
        help_text: Optional[str] = None
    ):
        self.name = name
        self.prompt = prompt
        self.field_type = field_type
        self.required = required
        self.validation = validation
        self.options = options
        self.help_text = help_text
        self.value = None
        self.attempts = 0
        self.max_attempts = 3


class ConversationFlow:
    """Manages a conversation flow for completing tasks."""
    
    def __init__(
        self,
        flow_id: str,
        name: str,
        description: str,
        fields: List[FormField],
        completion_callback: Optional[Callable] = None
    ):
        self.flow_id = flow_id
        self.name = name
        self.description = description
        self.fields = fields
        self.completion_callback = completion_callback
        self.current_field_index = 0
        self.collected_data = {}
        self.state = ConversationState.IDLE
        self.start_time = None
        self.end_time = None
        self.conversation_history = []
    
    def get_current_field(self) -> Optional[FormField]:
        """Get the current field being collected."""
        if self.current_field_index < len(self.fields):
            return self.fields[self.current_field_index]
        return None
    
    def advance_field(self):
        """Move to the next field."""
        self.current_field_index += 1
    
    def is_complete(self) -> bool:
        """Check if all required fields are collected."""
        for field in self.fields:
            if field.required and field.name not in self.collected_data:
                return False
        return True
    
    def reset(self):
        """Reset the flow to start over."""
        self.current_field_index = 0
        self.collected_data.clear()
        self.state = ConversationState.IDLE
        self.conversation_history.clear()


class ConversationFlowManager:
    """Manages multiple conversation flows for voice-guided form completion."""
    
    def __init__(self):
        """Initialize the conversation flow manager."""
        self.flows: Dict[str, ConversationFlow] = {}
        self.active_flow: Optional[ConversationFlow] = None
        self.session_data: Dict[str, Any] = {}
        
        # Register predefined flows
        self._register_predefined_flows()
    
    def _register_predefined_flows(self):
        """Register common financial planning flows."""
        # Goal Creation Flow
        self.register_flow(
            ConversationFlow(
                flow_id="create_goal",
                name="Create Financial Goal",
                description="Guide through creating a new financial goal",
                fields=[
                    FormField(
                        name="goal_type",
                        prompt="What type of financial goal would you like to create? You can say retirement, education, home purchase, emergency fund, or custom.",
                        field_type="choice",
                        options=["retirement", "education", "home purchase", "emergency fund", "custom"]
                    ),
                    FormField(
                        name="goal_name",
                        prompt="What would you like to name this goal?",
                        field_type="text"
                    ),
                    FormField(
                        name="target_amount",
                        prompt="What is your target amount for this goal in dollars?",
                        field_type="currency",
                        validation=lambda x: x > 0
                    ),
                    FormField(
                        name="target_date",
                        prompt="When do you want to achieve this goal? Please provide a date or timeframe.",
                        field_type="date"
                    ),
                    FormField(
                        name="monthly_contribution",
                        prompt="How much can you contribute monthly towards this goal?",
                        field_type="currency",
                        validation=lambda x: x >= 0,
                        required=False
                    ),
                    FormField(
                        name="risk_tolerance",
                        prompt="What's your risk tolerance for this goal? Say conservative, moderate, or aggressive.",
                        field_type="choice",
                        options=["conservative", "moderate", "aggressive"],
                        required=False
                    )
                ]
            )
        )
        
        # Investment Transaction Flow
        self.register_flow(
            ConversationFlow(
                flow_id="investment_transaction",
                name="Investment Transaction",
                description="Execute an investment transaction",
                fields=[
                    FormField(
                        name="transaction_type",
                        prompt="Would you like to buy or sell?",
                        field_type="choice",
                        options=["buy", "sell"]
                    ),
                    FormField(
                        name="asset_type",
                        prompt="What type of asset? You can say stocks, bonds, ETF, or mutual fund.",
                        field_type="choice",
                        options=["stocks", "bonds", "ETF", "mutual fund"]
                    ),
                    FormField(
                        name="ticker_or_name",
                        prompt="Please provide the ticker symbol or fund name.",
                        field_type="text"
                    ),
                    FormField(
                        name="amount_type",
                        prompt="Would you like to specify the amount in dollars or shares?",
                        field_type="choice",
                        options=["dollars", "shares"]
                    ),
                    FormField(
                        name="amount",
                        prompt="How much would you like to invest?",
                        field_type="number",
                        validation=lambda x: x > 0
                    ),
                    FormField(
                        name="account",
                        prompt="Which account should this transaction use? Say brokerage, IRA, or 401k.",
                        field_type="choice",
                        options=["brokerage", "IRA", "401k"],
                        required=False
                    )
                ]
            )
        )
        
        # Portfolio Review Flow
        self.register_flow(
            ConversationFlow(
                flow_id="portfolio_review",
                name="Portfolio Review",
                description="Voice-guided portfolio review",
                fields=[
                    FormField(
                        name="review_type",
                        prompt="What would you like to review? Say performance, allocation, risk, or holdings.",
                        field_type="choice",
                        options=["performance", "allocation", "risk", "holdings"]
                    ),
                    FormField(
                        name="time_period",
                        prompt="What time period? Say today, this week, this month, this year, or all time.",
                        field_type="choice",
                        options=["today", "week", "month", "year", "all time"],
                        required=False
                    ),
                    FormField(
                        name="comparison",
                        prompt="Would you like to compare with a benchmark? Say yes or no.",
                        field_type="boolean",
                        required=False
                    ),
                    FormField(
                        name="details",
                        prompt="Would you like detailed analysis? Say yes or no.",
                        field_type="boolean",
                        required=False
                    )
                ]
            )
        )
        
        # Retirement Planning Flow
        self.register_flow(
            ConversationFlow(
                flow_id="retirement_planning",
                name="Retirement Planning",
                description="Comprehensive retirement planning session",
                fields=[
                    FormField(
                        name="current_age",
                        prompt="What is your current age?",
                        field_type="number",
                        validation=lambda x: 18 <= x <= 100
                    ),
                    FormField(
                        name="retirement_age",
                        prompt="At what age do you plan to retire?",
                        field_type="number",
                        validation=lambda x: 50 <= x <= 80
                    ),
                    FormField(
                        name="current_savings",
                        prompt="How much do you currently have saved for retirement?",
                        field_type="currency",
                        validation=lambda x: x >= 0
                    ),
                    FormField(
                        name="monthly_income_needed",
                        prompt="How much monthly income will you need in retirement, in today's dollars?",
                        field_type="currency",
                        validation=lambda x: x > 0
                    ),
                    FormField(
                        name="social_security",
                        prompt="Do you expect to receive social security? Say yes or no.",
                        field_type="boolean"
                    ),
                    FormField(
                        name="pension",
                        prompt="Will you have a pension? If yes, what's the expected monthly amount? Say no if not applicable.",
                        field_type="currency",
                        required=False
                    ),
                    FormField(
                        name="inflation_assumption",
                        prompt="What inflation rate should we assume? Default is 3 percent. Say skip to use default.",
                        field_type="percentage",
                        required=False
                    )
                ]
            )
        )
    
    def register_flow(self, flow: ConversationFlow):
        """Register a conversation flow."""
        self.flows[flow.flow_id] = flow
    
    def start_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Start a conversation flow.
        
        Args:
            flow_id: ID of the flow to start
            
        Returns:
            Initial flow state and prompt
        """
        if flow_id not in self.flows:
            return {
                "success": False,
                "error": f"Flow '{flow_id}' not found"
            }
        
        flow = self.flows[flow_id]
        flow.reset()
        flow.state = ConversationState.COLLECTING_INFO
        flow.start_time = datetime.utcnow()
        
        self.active_flow = flow
        
        # Get first field prompt
        first_field = flow.get_current_field()
        
        return {
            "success": True,
            "flow_id": flow_id,
            "flow_name": flow.name,
            "state": flow.state.value,
            "prompt": first_field.prompt if first_field else None,
            "field": {
                "name": first_field.name,
                "type": first_field.field_type,
                "options": first_field.options
            } if first_field else None
        }
    
    async def process_input(
        self,
        user_input: str,
        parsed_command: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user input for the active flow.
        
        Args:
            user_input: Raw user input
            parsed_command: Parsed command data
            
        Returns:
            Flow state and next prompt or result
        """
        if not self.active_flow:
            return {
                "success": False,
                "error": "No active conversation flow"
            }
        
        flow = self.active_flow
        current_field = flow.get_current_field()
        
        if not current_field:
            return await self._complete_flow()
        
        # Record in conversation history
        flow.conversation_history.append({
            "field": current_field.name,
            "prompt": current_field.prompt,
            "user_input": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Process based on field type
        value = await self._extract_field_value(
            user_input, current_field, parsed_command
        )
        
        # Handle special commands
        if self._is_help_request(user_input, parsed_command):
            return self._provide_field_help(current_field)
        
        if self._is_skip_request(user_input, parsed_command):
            if not current_field.required:
                flow.advance_field()
                return await self._get_next_prompt()
            else:
                return {
                    "success": False,
                    "error": "This field is required and cannot be skipped",
                    "prompt": current_field.prompt
                }
        
        if self._is_back_request(user_input, parsed_command):
            return self._go_back()
        
        # Validate value
        if value is not None:
            if current_field.validation:
                try:
                    if not current_field.validation(value):
                        current_field.attempts += 1
                        return self._handle_validation_error(current_field)
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    return self._handle_validation_error(current_field)
            
            # Store value and advance
            current_field.value = value
            flow.collected_data[current_field.name] = value
            flow.advance_field()
            
            # Get next prompt or complete
            return await self._get_next_prompt()
        else:
            # Could not extract value
            current_field.attempts += 1
            
            if current_field.attempts >= current_field.max_attempts:
                return {
                    "success": False,
                    "error": "Maximum attempts reached for this field",
                    "flow_cancelled": True
                }
            
            return {
                "success": False,
                "error": "I couldn't understand that. Please try again.",
                "prompt": current_field.prompt,
                "help": current_field.help_text
            }
    
    async def _extract_field_value(
        self,
        user_input: str,
        field: FormField,
        parsed_command: Optional[Dict[str, Any]]
    ) -> Any:
        """Extract field value from user input based on field type."""
        user_input_lower = user_input.lower().strip()
        
        if field.field_type == "boolean":
            if any(word in user_input_lower for word in ["yes", "yeah", "yep", "true", "correct"]):
                return True
            elif any(word in user_input_lower for word in ["no", "nope", "false", "incorrect"]):
                return False
        
        elif field.field_type == "choice":
            if field.options:
                for option in field.options:
                    if option.lower() in user_input_lower:
                        return option
        
        elif field.field_type == "number":
            # Extract number from entities if available
            if parsed_command and parsed_command.get("entities"):
                entities = parsed_command["entities"]
                if "word_numbers" in entities and entities["word_numbers"]:
                    return entities["word_numbers"][0]
                if "amount" in entities:
                    return int(entities["amount"])
            
            # Try to extract number directly
            import re
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                return int(numbers[0])
        
        elif field.field_type == "currency":
            if parsed_command and parsed_command.get("entities"):
                entities = parsed_command["entities"]
                if "amount" in entities:
                    return float(entities["amount"])
            
            # Try to extract currency amount
            import re
            amounts = re.findall(r'\$?([\d,]+(?:\.\d{2})?)', user_input)
            if amounts:
                return float(amounts[0].replace(',', ''))
        
        elif field.field_type == "percentage":
            if parsed_command and parsed_command.get("entities"):
                entities = parsed_command["entities"]
                if "percentage" in entities:
                    return float(entities["percentage"])
            
            # Try to extract percentage
            import re
            percentages = re.findall(r'([\d.]+)\s*%?', user_input)
            if percentages:
                return float(percentages[0])
        
        elif field.field_type == "date":
            if parsed_command and parsed_command.get("entities"):
                entities = parsed_command["entities"]
                if "date" in entities:
                    return entities["date"]
                if "time_period" in entities:
                    # Convert relative time to date
                    from datetime import datetime, timedelta
                    period = entities["time_period"]
                    if period["unit"] == "year":
                        target_date = datetime.now() + timedelta(days=365 * period["value"])
                    elif period["unit"] == "month":
                        target_date = datetime.now() + timedelta(days=30 * period["value"])
                    else:
                        target_date = datetime.now() + timedelta(days=period["value"])
                    return target_date.strftime("%Y-%m-%d")
        
        elif field.field_type == "text":
            # Return cleaned input for text fields
            return user_input.strip()
        
        return None
    
    async def _get_next_prompt(self) -> Dict[str, Any]:
        """Get the next prompt in the flow."""
        flow = self.active_flow
        
        if flow.is_complete():
            return await self._complete_flow()
        
        next_field = flow.get_current_field()
        if next_field:
            response = {
                "success": True,
                "state": ConversationState.COLLECTING_INFO.value,
                "prompt": next_field.prompt,
                "field": {
                    "name": next_field.name,
                    "type": next_field.field_type,
                    "options": next_field.options,
                    "required": next_field.required
                },
                "progress": {
                    "current": flow.current_field_index + 1,
                    "total": len(flow.fields),
                    "percentage": ((flow.current_field_index + 1) / len(flow.fields)) * 100
                }
            }
            
            # Add help text if available
            if next_field.help_text:
                response["help"] = next_field.help_text
            
            return response
        
        return await self._complete_flow()
    
    async def _complete_flow(self) -> Dict[str, Any]:
        """Complete the current flow."""
        flow = self.active_flow
        
        if not flow:
            return {
                "success": False,
                "error": "No active flow to complete"
            }
        
        flow.state = ConversationState.COMPLETED
        flow.end_time = datetime.utcnow()
        
        # Execute completion callback if provided
        result = None
        if flow.completion_callback:
            try:
                result = await flow.completion_callback(flow.collected_data)
            except Exception as e:
                logger.error(f"Flow completion callback error: {e}")
                flow.state = ConversationState.ERROR
                return {
                    "success": False,
                    "error": "Failed to complete the action",
                    "details": str(e)
                }
        
        # Clear active flow
        self.active_flow = None
        
        # Generate summary
        summary = self._generate_flow_summary(flow)
        
        return {
            "success": True,
            "state": ConversationState.COMPLETED.value,
            "flow_completed": True,
            "flow_id": flow.flow_id,
            "collected_data": flow.collected_data,
            "summary": summary,
            "result": result,
            "duration": (flow.end_time - flow.start_time).total_seconds() if flow.start_time else None
        }
    
    def _generate_flow_summary(self, flow: ConversationFlow) -> str:
        """Generate a summary of the completed flow."""
        parts = [f"Completed {flow.name}."]
        
        # Add key collected data points
        if "goal_name" in flow.collected_data:
            parts.append(f"Goal: {flow.collected_data['goal_name']}")
        
        if "target_amount" in flow.collected_data:
            amount = flow.collected_data["target_amount"]
            parts.append(f"Target: ${amount:,.2f}")
        
        if "transaction_type" in flow.collected_data:
            parts.append(f"Transaction: {flow.collected_data['transaction_type']}")
        
        if "amount" in flow.collected_data:
            amount = flow.collected_data["amount"]
            parts.append(f"Amount: ${amount:,.2f}")
        
        return " ".join(parts)
    
    def _is_help_request(self, user_input: str, parsed_command: Optional[Dict]) -> bool:
        """Check if user is requesting help."""
        if parsed_command and parsed_command.get("intent") == CommandIntent.HELP:
            return True
        
        help_keywords = ["help", "what", "explain", "don't understand", "confused"]
        return any(keyword in user_input.lower() for keyword in help_keywords)
    
    def _is_skip_request(self, user_input: str, parsed_command: Optional[Dict]) -> bool:
        """Check if user wants to skip a field."""
        skip_keywords = ["skip", "next", "pass", "later", "don't know"]
        return any(keyword in user_input.lower() for keyword in skip_keywords)
    
    def _is_back_request(self, user_input: str, parsed_command: Optional[Dict]) -> bool:
        """Check if user wants to go back."""
        back_keywords = ["back", "previous", "undo", "change", "go back"]
        return any(keyword in user_input.lower() for keyword in back_keywords)
    
    def _provide_field_help(self, field: FormField) -> Dict[str, Any]:
        """Provide help for a specific field."""
        help_text = field.help_text or f"Please provide a value for {field.name}."
        
        if field.options:
            help_text += f" Available options are: {', '.join(field.options)}."
        
        if field.field_type == "currency":
            help_text += " Please provide an amount in dollars, like 'five thousand dollars' or '$5000'."
        elif field.field_type == "date":
            help_text += " You can say a specific date or a timeframe like 'in 5 years'."
        elif field.field_type == "boolean":
            help_text += " Please say 'yes' or 'no'."
        
        if not field.required:
            help_text += " This field is optional. Say 'skip' to move on."
        
        return {
            "success": True,
            "help": help_text,
            "prompt": field.prompt,
            "field_info": {
                "name": field.name,
                "type": field.field_type,
                "required": field.required,
                "options": field.options
            }
        }
    
    def _go_back(self) -> Dict[str, Any]:
        """Go back to the previous field."""
        flow = self.active_flow
        
        if flow.current_field_index > 0:
            flow.current_field_index -= 1
            previous_field = flow.get_current_field()
            
            return {
                "success": True,
                "action": "went_back",
                "prompt": previous_field.prompt if previous_field else None,
                "field": {
                    "name": previous_field.name,
                    "type": previous_field.field_type,
                    "options": previous_field.options,
                    "current_value": previous_field.value
                } if previous_field else None
            }
        
        return {
            "success": False,
            "error": "Cannot go back further"
        }
    
    def _handle_validation_error(self, field: FormField) -> Dict[str, Any]:
        """Handle field validation error."""
        error_messages = {
            "currency": "Please provide a valid dollar amount greater than zero.",
            "number": "Please provide a valid number.",
            "percentage": "Please provide a valid percentage.",
            "date": "Please provide a valid date or timeframe.",
            "choice": f"Please choose from: {', '.join(field.options) if field.options else 'the available options'}."
        }
        
        error_msg = error_messages.get(field.field_type, "The value provided is not valid.")
        
        if field.attempts >= field.max_attempts - 1:
            error_msg += " This is your last attempt."
        
        return {
            "success": False,
            "error": error_msg,
            "prompt": field.prompt,
            "attempts_remaining": field.max_attempts - field.attempts
        }
    
    def cancel_flow(self) -> Dict[str, Any]:
        """Cancel the current flow."""
        if self.active_flow:
            flow_name = self.active_flow.name
            self.active_flow = None
            return {
                "success": True,
                "action": "flow_cancelled",
                "message": f"Cancelled {flow_name}"
            }
        
        return {
            "success": False,
            "error": "No active flow to cancel"
        }
    
    def get_flow_state(self) -> Dict[str, Any]:
        """Get the current state of the active flow."""
        if not self.active_flow:
            return {
                "active": False,
                "available_flows": list(self.flows.keys())
            }
        
        flow = self.active_flow
        current_field = flow.get_current_field()
        
        return {
            "active": True,
            "flow_id": flow.flow_id,
            "flow_name": flow.name,
            "state": flow.state.value,
            "progress": {
                "current_field": current_field.name if current_field else None,
                "fields_completed": len(flow.collected_data),
                "total_fields": len(flow.fields),
                "percentage": (len(flow.collected_data) / len(flow.fields)) * 100 if flow.fields else 0
            },
            "collected_data": flow.collected_data
        }