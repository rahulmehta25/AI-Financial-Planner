"""Multi-language support for AI narratives."""

from typing import Dict, Any, Optional
from enum import Enum
from langdetect import detect
import json


class TranslationService:
    """Service for handling multi-language narratives."""
    
    def __init__(self):
        """Initialize translation service."""
        # Translation mappings for common financial terms
        self.translations = {
            "en": {
                "portfolio": "portfolio",
                "investment": "investment",
                "return": "return",
                "risk": "risk",
                "retirement": "retirement",
                "savings": "savings",
                "goal": "goal",
                "success_rate": "success rate",
                "allocation": "allocation",
                "monthly": "monthly",
                "annual": "annual",
                "years": "years",
                "disclaimer": "Disclaimer"
            },
            "es": {
                "portfolio": "cartera",
                "investment": "inversión",
                "return": "rendimiento",
                "risk": "riesgo",
                "retirement": "jubilación",
                "savings": "ahorros",
                "goal": "objetivo",
                "success_rate": "tasa de éxito",
                "allocation": "asignación",
                "monthly": "mensual",
                "annual": "anual",
                "years": "años",
                "disclaimer": "Descargo de responsabilidad"
            },
            "zh": {
                "portfolio": "投资组合",
                "investment": "投资",
                "return": "回报",
                "risk": "风险",
                "retirement": "退休",
                "savings": "储蓄",
                "goal": "目标",
                "success_rate": "成功率",
                "allocation": "配置",
                "monthly": "每月",
                "annual": "年度",
                "years": "年",
                "disclaimer": "免责声明"
            }
        }
        
        # Disclaimer translations
        self.disclaimers = {
            "en": {
                "general": (
                    "This information is for educational purposes only and should not be "
                    "considered personalized financial advice. Please consult with a qualified "
                    "financial advisor before making investment decisions."
                ),
                "projection": (
                    "These projections are based on historical data and assumptions that may not "
                    "reflect future market conditions. Actual results may vary significantly."
                )
            },
            "es": {
                "general": (
                    "Esta información es solo para fines educativos y no debe considerarse "
                    "asesoramiento financiero personalizado. Consulte con un asesor financiero "
                    "calificado antes de tomar decisiones de inversión."
                ),
                "projection": (
                    "Estas proyecciones se basan en datos históricos y suposiciones que pueden no "
                    "reflejar las condiciones futuras del mercado. Los resultados reales pueden "
                    "variar significativamente."
                )
            },
            "zh": {
                "general": (
                    "此信息仅用于教育目的，不应被视为个性化的财务建议。在做出投资决定之前，"
                    "请咨询合格的财务顾问。"
                ),
                "projection": (
                    "这些预测基于历史数据和假设，可能无法反映未来的市场状况。"
                    "实际结果可能会有显著差异。"
                )
            }
        }
        
        # Number formatting rules by language
        self.number_formats = {
            "en": {"decimal": ".", "thousands": ",", "currency": "$"},
            "es": {"decimal": ",", "thousands": ".", "currency": "€"},
            "zh": {"decimal": ".", "thousands": ",", "currency": "¥"}
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (en, es, zh)
        """
        try:
            detected = detect(text)
            # Map to our supported languages
            if detected in ["en", "es", "zh"]:
                return detected
            elif detected in ["zh-cn", "zh-tw"]:
                return "zh"
            else:
                return "en"  # Default to English
        except:
            return "en"
    
    def translate_term(self, term: str, from_lang: str, to_lang: str) -> str:
        """Translate a financial term.
        
        Args:
            term: Term to translate
            from_lang: Source language
            to_lang: Target language
            
        Returns:
            Translated term
        """
        if from_lang == to_lang:
            return term
        
        # Get translation if available
        if term.lower() in self.translations.get(from_lang, {}):
            term_key = term.lower()
            return self.translations.get(to_lang, {}).get(
                term_key,
                self.translations["en"].get(term_key, term)
            )
        
        return term
    
    def format_number(self, 
                     number: float,
                     language: str,
                     is_currency: bool = False,
                     decimals: int = 0) -> str:
        """Format a number according to language conventions.
        
        Args:
            number: Number to format
            language: Target language
            is_currency: Whether this is a currency value
            decimals: Number of decimal places
            
        Returns:
            Formatted number string
        """
        fmt = self.number_formats.get(language, self.number_formats["en"])
        
        # Format the number
        if decimals > 0:
            formatted = f"{number:,.{decimals}f}"
        else:
            formatted = f"{number:,.0f}"
        
        # Replace separators based on language
        if language == "es":
            # Spanish uses opposite separators
            formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        # Add currency symbol if needed
        if is_currency:
            formatted = fmt["currency"] + formatted
        
        return formatted
    
    def get_disclaimer(self, 
                      disclaimer_type: str,
                      language: str) -> str:
        """Get localized disclaimer text.
        
        Args:
            disclaimer_type: Type of disclaimer
            language: Target language
            
        Returns:
            Localized disclaimer text
        """
        disclaimers = self.disclaimers.get(language, self.disclaimers["en"])
        return disclaimers.get(disclaimer_type, disclaimers.get("general", ""))
    
    def localize_template(self,
                         template: str,
                         language: str) -> str:
        """Localize a template for a specific language.
        
        Args:
            template: Template text
            language: Target language
            
        Returns:
            Localized template
        """
        if language == "en":
            return template
        
        # Replace common financial terms
        localized = template
        for en_term, translation in self.translations["en"].items():
            target_term = self.translations.get(language, {}).get(en_term, en_term)
            if target_term != en_term:
                # Case-insensitive replacement
                localized = localized.replace(translation, target_term)
                localized = localized.replace(translation.capitalize(), target_term.capitalize())
        
        return localized
    
    def validate_translation_consistency(self,
                                       original: str,
                                       translated: str,
                                       language: str) -> bool:
        """Validate that translation maintains numerical consistency.
        
        Args:
            original: Original text
            translated: Translated text
            language: Target language
            
        Returns:
            Whether translation is consistent
        """
        import re
        
        # Extract numbers from both texts
        original_numbers = re.findall(r'\d+\.?\d*', original)
        translated_numbers = re.findall(r'\d+[,.]?\d*', translated)
        
        # Clean up numbers (remove formatting)
        original_clean = [float(n.replace(',', '')) for n in original_numbers]
        translated_clean = []
        
        for n in translated_numbers:
            # Handle different decimal separators
            if language == "es":
                n = n.replace('.', '').replace(',', '.')
            else:
                n = n.replace(',', '')
            try:
                translated_clean.append(float(n))
            except ValueError:
                continue
        
        # Check if all numbers are preserved
        return set(original_clean) == set(translated_clean)