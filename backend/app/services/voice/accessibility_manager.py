"""Accessibility Manager for Screen Reader and Accessibility Support."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import re

from .config import VoiceSettings

logger = logging.getLogger(__name__)


class AccessibilityLevel(str, Enum):
    """Accessibility support levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


class ScreenReaderMode(str, Enum):
    """Screen reader compatibility modes."""
    JAWS = "jaws"
    NVDA = "nvda"
    VOICEOVER = "voiceover"
    TALKBACK = "talkback"
    GENERIC = "generic"


class AccessibilityManager:
    """Manages accessibility features for voice interface."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize the accessibility manager."""
        self.settings = settings or VoiceSettings()
        
        # Accessibility state
        self.screen_reader_enabled = self.settings.screen_reader_enabled
        self.high_contrast_mode = self.settings.high_contrast_mode
        self.keyboard_navigation = self.settings.keyboard_navigation
        self.voice_feedback_enabled = self.settings.voice_feedback_enabled
        
        # Screen reader settings
        self.screen_reader_mode = ScreenReaderMode.GENERIC
        self.verbosity_level = "medium"  # low, medium, high
        
        # Navigation state
        self.focus_element = None
        self.navigation_history = []
        self.landmarks = {}
        
        # ARIA attributes
        self.aria_live_regions = {}
        self.aria_descriptions = {}
        
        # Keyboard shortcuts
        self.keyboard_shortcuts = self._initialize_keyboard_shortcuts()
    
    def _initialize_keyboard_shortcuts(self) -> Dict[str, str]:
        """Initialize keyboard shortcuts for voice commands."""
        return {
            "ctrl+shift+v": "toggle_voice",
            "ctrl+shift+m": "start_voice_command",
            "ctrl+shift+h": "voice_help",
            "ctrl+shift+s": "stop_listening",
            "ctrl+shift+r": "repeat_last",
            "alt+p": "portfolio_summary",
            "alt+g": "goals_summary",
            "alt+t": "transactions_summary",
            "alt+n": "navigate_next",
            "alt+b": "navigate_back",
            "escape": "cancel_action",
            "enter": "confirm_action",
            "tab": "next_field",
            "shift+tab": "previous_field",
            "f1": "context_help",
            "ctrl+z": "undo_last"
        }
    
    def format_for_screen_reader(
        self,
        content: Any,
        element_type: str = "text",
        context: Optional[Dict] = None
    ) -> str:
        """
        Format content for screen reader consumption.
        
        Args:
            content: Content to format
            element_type: Type of element (text, button, input, table, etc.)
            context: Additional context for formatting
            
        Returns:
            Screen reader friendly text
        """
        if not self.screen_reader_enabled:
            return str(content) if content else ""
        
        formatted = ""
        
        # Format based on element type
        if element_type == "button":
            formatted = f"Button: {content}. Press Enter to activate."
        
        elif element_type == "input":
            label = context.get("label", "Input field")
            value = context.get("value", "empty")
            required = context.get("required", False)
            formatted = f"{label}: {value}. {'Required field. ' if required else ''}Type to enter text."
        
        elif element_type == "table":
            formatted = self._format_table_for_screen_reader(content, context)
        
        elif element_type == "list":
            formatted = self._format_list_for_screen_reader(content, context)
        
        elif element_type == "heading":
            level = context.get("level", 1)
            formatted = f"Heading level {level}: {content}"
        
        elif element_type == "link":
            formatted = f"Link: {content}. Press Enter to follow."
        
        elif element_type == "form":
            formatted = self._format_form_for_screen_reader(content, context)
        
        elif element_type == "chart":
            formatted = self._format_chart_for_screen_reader(content, context)
        
        elif element_type == "currency":
            formatted = self._format_currency_for_screen_reader(content)
        
        elif element_type == "percentage":
            formatted = self._format_percentage_for_screen_reader(content)
        
        elif element_type == "date":
            formatted = self._format_date_for_screen_reader(content)
        
        else:
            formatted = str(content) if content else ""
        
        # Add navigation hints if in high verbosity mode
        if self.verbosity_level == "high":
            formatted = self._add_navigation_hints(formatted, element_type)
        
        return formatted
    
    def _format_table_for_screen_reader(self, table_data: Any, context: Optional[Dict]) -> str:
        """Format table data for screen reader."""
        if isinstance(table_data, list) and table_data:
            rows = len(table_data)
            cols = len(table_data[0]) if isinstance(table_data[0], (list, dict)) else 1
            
            result = f"Table with {rows} rows and {cols} columns. "
            
            # Add caption if provided
            if context and context.get("caption"):
                result += f"Caption: {context['caption']}. "
            
            # Format headers if provided
            if context and context.get("headers"):
                result += "Column headers: " + ", ".join(context["headers"]) + ". "
            
            # Add navigation instructions
            result += "Use arrow keys to navigate cells."
            
            return result
        
        return "Empty table"
    
    def _format_list_for_screen_reader(self, list_data: List, context: Optional[Dict]) -> str:
        """Format list data for screen reader."""
        if not list_data:
            return "Empty list"
        
        count = len(list_data)
        list_type = context.get("type", "unordered") if context else "unordered"
        
        result = f"{list_type.capitalize()} list with {count} items. "
        
        if self.verbosity_level in ["medium", "high"]:
            # Include first few items as preview
            preview_items = list_data[:3]
            for i, item in enumerate(preview_items, 1):
                result += f"Item {i}: {item}. "
            
            if count > 3:
                result += f"And {count - 3} more items. "
        
        result += "Use arrow keys to navigate items."
        
        return result
    
    def _format_form_for_screen_reader(self, form_data: Dict, context: Optional[Dict]) -> str:
        """Format form data for screen reader."""
        if not form_data:
            return "Empty form"
        
        field_count = len(form_data)
        required_count = sum(1 for f in form_data.values() if f.get("required"))
        
        result = f"Form with {field_count} fields"
        
        if required_count:
            result += f", {required_count} required"
        
        result += ". "
        
        # Add form title if provided
        if context and context.get("title"):
            result += f"Form: {context['title']}. "
        
        # List fields if verbosity is high
        if self.verbosity_level == "high":
            for field_name, field_info in form_data.items():
                field_type = field_info.get("type", "text")
                required = field_info.get("required", False)
                result += f"{field_name}: {field_type} field"
                if required:
                    result += " (required)"
                result += ". "
        
        result += "Press Tab to navigate between fields."
        
        return result
    
    def _format_chart_for_screen_reader(self, chart_data: Dict, context: Optional[Dict]) -> str:
        """Format chart data for screen reader."""
        chart_type = context.get("type", "chart") if context else "chart"
        title = context.get("title", "") if context else ""
        
        result = f"{chart_type.capitalize()}"
        
        if title:
            result += f": {title}"
        
        result += ". "
        
        # Provide data summary
        if isinstance(chart_data, dict):
            if "summary" in chart_data:
                result += chart_data["summary"] + ". "
            elif "data_points" in chart_data:
                count = len(chart_data["data_points"])
                result += f"Contains {count} data points. "
                
                # Describe trend if available
                if "trend" in chart_data:
                    result += f"Trend: {chart_data['trend']}. "
                
                # Provide min/max if available
                if "min" in chart_data and "max" in chart_data:
                    result += f"Range: {chart_data['min']} to {chart_data['max']}. "
        
        result += "Press Enter for detailed data table."
        
        return result
    
    def _format_currency_for_screen_reader(self, amount: float) -> str:
        """Format currency amount for screen reader."""
        if amount < 0:
            return f"Negative ${abs(amount):,.2f}"
        else:
            return f"${amount:,.2f}"
    
    def _format_percentage_for_screen_reader(self, value: float) -> str:
        """Format percentage for screen reader."""
        if value < 0:
            return f"Negative {abs(value):.2f} percent"
        else:
            return f"{value:.2f} percent"
    
    def _format_date_for_screen_reader(self, date: Any) -> str:
        """Format date for screen reader."""
        if isinstance(date, datetime):
            return date.strftime("%B %d, %Y")
        elif isinstance(date, str):
            # Try to parse and reformat
            try:
                from dateutil import parser
                parsed_date = parser.parse(date)
                return parsed_date.strftime("%B %d, %Y")
            except:
                return date
        return str(date)
    
    def _add_navigation_hints(self, content: str, element_type: str) -> str:
        """Add navigation hints based on element type."""
        hints = {
            "button": "Space or Enter to activate",
            "link": "Enter to follow",
            "input": "Type to enter text",
            "select": "Arrow keys to choose options",
            "checkbox": "Space to toggle",
            "radio": "Arrow keys to select",
            "table": "Arrow keys to navigate cells",
            "list": "Arrow keys to navigate items"
        }
        
        hint = hints.get(element_type)
        if hint:
            content += f" ({hint})"
        
        return content
    
    def generate_aria_attributes(
        self,
        element_type: str,
        content: Any,
        context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate ARIA attributes for an element.
        
        Args:
            element_type: Type of element
            content: Element content
            context: Additional context
            
        Returns:
            Dictionary of ARIA attributes
        """
        aria = {}
        
        # Basic role
        role_map = {
            "button": "button",
            "link": "link",
            "navigation": "navigation",
            "form": "form",
            "table": "table",
            "list": "list",
            "heading": "heading",
            "alert": "alert",
            "dialog": "dialog",
            "tab": "tab",
            "tabpanel": "tabpanel"
        }
        
        if element_type in role_map:
            aria["role"] = role_map[element_type]
        
        # Labels and descriptions
        if context:
            if "label" in context:
                aria["aria-label"] = context["label"]
            
            if "description" in context:
                aria["aria-describedby"] = context["description"]
            
            if "required" in context and context["required"]:
                aria["aria-required"] = "true"
            
            if "invalid" in context and context["invalid"]:
                aria["aria-invalid"] = "true"
            
            if "expanded" in context:
                aria["aria-expanded"] = str(context["expanded"]).lower()
            
            if "selected" in context:
                aria["aria-selected"] = str(context["selected"]).lower()
            
            if "checked" in context:
                aria["aria-checked"] = str(context["checked"]).lower()
            
            if "level" in context:
                aria["aria-level"] = str(context["level"])
            
            if "live" in context:
                aria["aria-live"] = context["live"]  # polite, assertive, off
            
            if "busy" in context:
                aria["aria-busy"] = str(context["busy"]).lower()
        
        return aria
    
    def create_landmark(
        self,
        landmark_type: str,
        label: str,
        content: Any
    ) -> Dict[str, Any]:
        """
        Create a landmark region for navigation.
        
        Args:
            landmark_type: Type of landmark (main, navigation, search, etc.)
            label: Landmark label
            content: Landmark content
            
        Returns:
            Landmark structure with ARIA attributes
        """
        landmark_roles = {
            "main": "main",
            "navigation": "navigation",
            "search": "search",
            "banner": "banner",
            "contentinfo": "contentinfo",
            "complementary": "complementary",
            "form": "form",
            "region": "region"
        }
        
        landmark = {
            "type": landmark_type,
            "label": label,
            "content": content,
            "aria": {
                "role": landmark_roles.get(landmark_type, "region"),
                "aria-label": label
            }
        }
        
        # Store landmark for navigation
        self.landmarks[label] = landmark
        
        return landmark
    
    def navigate_to_landmark(self, landmark_label: str) -> Dict[str, Any]:
        """Navigate to a specific landmark."""
        if landmark_label in self.landmarks:
            landmark = self.landmarks[landmark_label]
            
            # Update focus
            self.focus_element = landmark
            self.navigation_history.append(landmark_label)
            
            return {
                "success": True,
                "landmark": landmark,
                "announcement": f"Navigated to {landmark_label}"
            }
        
        return {
            "success": False,
            "error": f"Landmark '{landmark_label}' not found",
            "available_landmarks": list(self.landmarks.keys())
        }
    
    def get_keyboard_shortcut(self, action: str) -> Optional[str]:
        """Get keyboard shortcut for an action."""
        for shortcut, shortcut_action in self.keyboard_shortcuts.items():
            if shortcut_action == action:
                return shortcut
        return None
    
    def handle_keyboard_shortcut(self, shortcut: str) -> Dict[str, Any]:
        """Handle a keyboard shortcut."""
        if shortcut in self.keyboard_shortcuts:
            action = self.keyboard_shortcuts[shortcut]
            
            return {
                "success": True,
                "action": action,
                "shortcut": shortcut,
                "announcement": f"Executing: {action.replace('_', ' ')}"
            }
        
        return {
            "success": False,
            "error": f"Unknown shortcut: {shortcut}"
        }
    
    def create_skip_link(self, target: str, label: str) -> Dict[str, Any]:
        """Create a skip link for navigation."""
        return {
            "type": "skip_link",
            "target": target,
            "label": label,
            "aria": {
                "role": "link",
                "aria-label": f"Skip to {label}"
            },
            "keyboard_shortcut": f"Press Enter to skip to {label}"
        }
    
    def format_validation_error(
        self,
        field_name: str,
        error_message: str,
        suggestions: Optional[List[str]] = None
    ) -> str:
        """Format validation error for screen reader."""
        result = f"Error in {field_name}: {error_message}. "
        
        if suggestions:
            result += "Suggestions: " + ", ".join(suggestions) + ". "
        
        result += "Press Tab to move to the next field or Shift+Tab to go back."
        
        return result
    
    def generate_focus_announcement(
        self,
        element: Dict[str, Any],
        entering: bool = True
    ) -> str:
        """Generate announcement when focus changes."""
        element_type = element.get("type", "element")
        label = element.get("label", element_type)
        
        if entering:
            announcement = f"Entering {label}"
            
            # Add type-specific information
            if element_type == "form":
                field_count = element.get("field_count", 0)
                announcement += f" with {field_count} fields"
            elif element_type == "table":
                rows = element.get("rows", 0)
                cols = element.get("cols", 0)
                announcement += f" with {rows} rows and {cols} columns"
            elif element_type == "list":
                items = element.get("items", 0)
                announcement += f" with {items} items"
            
            # Add navigation hints
            if self.verbosity_level in ["medium", "high"]:
                nav_hint = element.get("navigation_hint")
                if nav_hint:
                    announcement += f". {nav_hint}"
        else:
            announcement = f"Leaving {label}"
        
        return announcement
    
    def set_verbosity_level(self, level: str):
        """Set screen reader verbosity level."""
        if level in ["low", "medium", "high"]:
            self.verbosity_level = level
            logger.info(f"Verbosity level set to: {level}")
    
    def toggle_screen_reader(self) -> bool:
        """Toggle screen reader on/off."""
        self.screen_reader_enabled = not self.screen_reader_enabled
        logger.info(f"Screen reader {'enabled' if self.screen_reader_enabled else 'disabled'}")
        return self.screen_reader_enabled
    
    def get_accessibility_status(self) -> Dict[str, Any]:
        """Get current accessibility settings status."""
        return {
            "screen_reader_enabled": self.screen_reader_enabled,
            "screen_reader_mode": self.screen_reader_mode.value,
            "verbosity_level": self.verbosity_level,
            "high_contrast_mode": self.high_contrast_mode,
            "keyboard_navigation": self.keyboard_navigation,
            "voice_feedback_enabled": self.voice_feedback_enabled,
            "landmarks_count": len(self.landmarks),
            "focus_element": self.focus_element.get("label") if self.focus_element else None,
            "navigation_history_length": len(self.navigation_history)
        }
    
    def export_accessibility_report(self) -> Dict[str, Any]:
        """Export accessibility compliance report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "wcag_compliance": "WCAG 2.1 AA",
            "features": {
                "screen_reader_support": self.screen_reader_enabled,
                "keyboard_navigation": self.keyboard_navigation,
                "aria_support": True,
                "high_contrast_mode": self.high_contrast_mode,
                "voice_control": self.voice_feedback_enabled,
                "skip_links": True,
                "landmarks": True,
                "focus_management": True
            },
            "keyboard_shortcuts": len(self.keyboard_shortcuts),
            "landmarks": list(self.landmarks.keys()),
            "supported_screen_readers": [
                "JAWS", "NVDA", "VoiceOver", "TalkBack"
            ],
            "languages_supported": [
                "English", "Spanish", "French", "German",
                "Italian", "Portuguese", "Chinese", "Japanese",
                "Korean", "Arabic", "Hindi", "Russian"
            ]
        }