"""Enhanced multi-language support for AI narratives with translation fallbacks."""

from typing import Dict, Any, Optional, List
from enum import Enum
from langdetect import detect
import json
import re
import logging

from .config import Language

logger = logging.getLogger(__name__)


class MultilingualSupport:
    """Enhanced service for handling multi-language narratives."""
    
    def __init__(self):
        """Initialize multilingual support."""
        # Comprehensive translation mappings
        self.translations = self._load_translations()
        
        # Financial term glossary
        self.financial_glossary = self._load_financial_glossary()
        
        # Number formatting rules
        self.number_formats = self._load_number_formats()
        
        # Disclaimer templates
        self.disclaimers = self._load_disclaimers()
        
        # Phrase templates for common financial expressions
        self.phrase_templates = self._load_phrase_templates()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load comprehensive translation mappings."""
        return {
            Language.ENGLISH: {
                # Basic terms
                "portfolio": "portfolio",
                "investment": "investment",
                "return": "return",
                "risk": "risk",
                "retirement": "retirement",
                "savings": "savings",
                "goal": "goal",
                "allocation": "allocation",
                
                # Time periods
                "monthly": "monthly",
                "annual": "annual",
                "yearly": "yearly",
                "quarterly": "quarterly",
                "years": "years",
                "months": "months",
                
                # Metrics
                "success_rate": "success rate",
                "probability": "probability",
                "expected_value": "expected value",
                "median": "median",
                "average": "average",
                "volatility": "volatility",
                "standard_deviation": "standard deviation",
                
                # Actions
                "increase": "increase",
                "decrease": "decrease",
                "maintain": "maintain",
                "rebalance": "rebalance",
                "adjust": "adjust",
                
                # Analysis terms
                "simulation": "simulation",
                "scenario": "scenario",
                "projection": "projection",
                "analysis": "analysis",
                "recommendation": "recommendation",
                
                # Compliance
                "disclaimer": "Disclaimer",
                "warning": "Warning",
                "note": "Note",
                "important": "Important"
            },
            Language.SPANISH: {
                # Basic terms
                "portfolio": "cartera",
                "investment": "inversión",
                "return": "rendimiento",
                "risk": "riesgo",
                "retirement": "jubilación",
                "savings": "ahorros",
                "goal": "objetivo",
                "allocation": "asignación",
                
                # Time periods
                "monthly": "mensual",
                "annual": "anual",
                "yearly": "anual",
                "quarterly": "trimestral",
                "years": "años",
                "months": "meses",
                
                # Metrics
                "success_rate": "tasa de éxito",
                "probability": "probabilidad",
                "expected_value": "valor esperado",
                "median": "mediana",
                "average": "promedio",
                "volatility": "volatilidad",
                "standard_deviation": "desviación estándar",
                
                # Actions
                "increase": "aumentar",
                "decrease": "disminuir",
                "maintain": "mantener",
                "rebalance": "reequilibrar",
                "adjust": "ajustar",
                
                # Analysis terms
                "simulation": "simulación",
                "scenario": "escenario",
                "projection": "proyección",
                "analysis": "análisis",
                "recommendation": "recomendación",
                
                # Compliance
                "disclaimer": "Descargo de responsabilidad",
                "warning": "Advertencia",
                "note": "Nota",
                "important": "Importante"
            },
            Language.CHINESE: {
                # Basic terms
                "portfolio": "投资组合",
                "investment": "投资",
                "return": "回报",
                "risk": "风险",
                "retirement": "退休",
                "savings": "储蓄",
                "goal": "目标",
                "allocation": "配置",
                
                # Time periods
                "monthly": "每月",
                "annual": "年度",
                "yearly": "每年",
                "quarterly": "季度",
                "years": "年",
                "months": "月",
                
                # Metrics
                "success_rate": "成功率",
                "probability": "概率",
                "expected_value": "期望值",
                "median": "中位数",
                "average": "平均",
                "volatility": "波动性",
                "standard_deviation": "标准差",
                
                # Actions
                "increase": "增加",
                "decrease": "减少",
                "maintain": "维持",
                "rebalance": "再平衡",
                "adjust": "调整",
                
                # Analysis terms
                "simulation": "模拟",
                "scenario": "场景",
                "projection": "预测",
                "analysis": "分析",
                "recommendation": "建议",
                
                # Compliance
                "disclaimer": "免责声明",
                "warning": "警告",
                "note": "注意",
                "important": "重要"
            }
        }
    
    def _load_financial_glossary(self) -> Dict[str, Dict[str, str]]:
        """Load financial term glossary with definitions."""
        return {
            Language.ENGLISH: {
                "sharpe_ratio": "risk-adjusted return measure",
                "monte_carlo": "statistical simulation method",
                "asset_allocation": "distribution of investments across asset classes",
                "diversification": "risk reduction through variety",
                "compound_interest": "interest on interest",
                "inflation": "general price increase over time",
                "liquidity": "ease of converting to cash",
                "bear_market": "declining market",
                "bull_market": "rising market"
            },
            Language.SPANISH: {
                "sharpe_ratio": "medida de retorno ajustado al riesgo",
                "monte_carlo": "método de simulación estadística",
                "asset_allocation": "distribución de inversiones entre clases de activos",
                "diversification": "reducción de riesgo a través de la variedad",
                "compound_interest": "interés compuesto",
                "inflation": "aumento general de precios en el tiempo",
                "liquidity": "facilidad de conversión a efectivo",
                "bear_market": "mercado en declive",
                "bull_market": "mercado en alza"
            },
            Language.CHINESE: {
                "sharpe_ratio": "风险调整回报率",
                "monte_carlo": "统计模拟方法",
                "asset_allocation": "资产类别间的投资分配",
                "diversification": "通过多样化降低风险",
                "compound_interest": "复利",
                "inflation": "通货膨胀",
                "liquidity": "流动性",
                "bear_market": "熊市",
                "bull_market": "牛市"
            }
        }
    
    def _load_number_formats(self) -> Dict[str, Dict[str, str]]:
        """Load number formatting rules by language."""
        return {
            Language.ENGLISH: {
                "decimal": ".",
                "thousands": ",",
                "currency": "$",
                "currency_position": "prefix",
                "percentage": "%",
                "percentage_position": "suffix"
            },
            Language.SPANISH: {
                "decimal": ",",
                "thousands": ".",
                "currency": "€",
                "currency_position": "prefix",
                "percentage": "%",
                "percentage_position": "suffix"
            },
            Language.CHINESE: {
                "decimal": ".",
                "thousands": ",",
                "currency": "¥",
                "currency_position": "prefix",
                "percentage": "%",
                "percentage_position": "suffix"
            }
        }
    
    def _load_disclaimers(self) -> Dict[str, Dict[str, str]]:
        """Load disclaimer templates in multiple languages."""
        return {
            Language.ENGLISH: {
                "general": (
                    "This information is for educational purposes only and should not be "
                    "considered personalized financial advice. Please consult with a qualified "
                    "financial advisor before making investment decisions."
                ),
                "projection": (
                    "These projections are based on historical data and assumptions that may not "
                    "reflect future market conditions. Actual results may vary significantly."
                ),
                "risk": (
                    "All investments carry risk, including the potential loss of principal. "
                    "Past performance does not guarantee future results."
                ),
                "tax": (
                    "This analysis does not constitute tax advice. Please consult with a "
                    "qualified tax professional regarding your specific situation."
                ),
                "regulatory": (
                    "This tool provides general information and is not intended to provide "
                    "legal, tax, or investment advice. Securities offered through registered "
                    "broker-dealers only where applicable."
                )
            },
            Language.SPANISH: {
                "general": (
                    "Esta información es solo para fines educativos y no debe considerarse "
                    "asesoramiento financiero personalizado. Consulte con un asesor financiero "
                    "calificado antes de tomar decisiones de inversión."
                ),
                "projection": (
                    "Estas proyecciones se basan en datos históricos y suposiciones que pueden no "
                    "reflejar las condiciones futuras del mercado. Los resultados reales pueden "
                    "variar significativamente."
                ),
                "risk": (
                    "Todas las inversiones conllevan riesgos, incluida la posible pérdida del capital. "
                    "El rendimiento pasado no garantiza resultados futuros."
                ),
                "tax": (
                    "Este análisis no constituye asesoramiento fiscal. Consulte con un "
                    "profesional fiscal calificado sobre su situación específica."
                ),
                "regulatory": (
                    "Esta herramienta proporciona información general y no pretende brindar "
                    "asesoramiento legal, fiscal o de inversión. Valores ofrecidos a través de "
                    "corredores registrados solo donde sea aplicable."
                )
            },
            Language.CHINESE: {
                "general": (
                    "此信息仅用于教育目的，不应被视为个性化的财务建议。在做出投资决定之前，"
                    "请咨询合格的财务顾问。"
                ),
                "projection": (
                    "这些预测基于历史数据和假设，可能无法反映未来的市场状况。"
                    "实际结果可能会有显著差异。"
                ),
                "risk": (
                    "所有投资都存在风险，包括本金损失的可能性。"
                    "过去的表现不能保证未来的结果。"
                ),
                "tax": (
                    "此分析不构成税务建议。请就您的具体情况咨询合格的税务专业人士。"
                ),
                "regulatory": (
                    "此工具提供一般信息，不旨在提供法律、税务或投资建议。"
                    "证券仅通过注册经纪交易商提供（如适用）。"
                )
            }
        }
    
    def _load_phrase_templates(self) -> Dict[str, Dict[str, str]]:
        """Load common phrase templates."""
        return {
            Language.ENGLISH: {
                "based_on": "Based on",
                "shows_that": "shows that",
                "probability_of": "probability of",
                "expected_to": "is expected to",
                "recommended_action": "We recommend",
                "key_finding": "Key finding:",
                "important_note": "Important note:",
                "in_summary": "In summary",
                "compared_to": "compared to",
                "increase_by": "increase by",
                "decrease_by": "decrease by"
            },
            Language.SPANISH: {
                "based_on": "Basado en",
                "shows_that": "muestra que",
                "probability_of": "probabilidad de",
                "expected_to": "se espera que",
                "recommended_action": "Recomendamos",
                "key_finding": "Hallazgo clave:",
                "important_note": "Nota importante:",
                "in_summary": "En resumen",
                "compared_to": "comparado con",
                "increase_by": "aumentar en",
                "decrease_by": "disminuir en"
            },
            Language.CHINESE: {
                "based_on": "基于",
                "shows_that": "显示",
                "probability_of": "概率为",
                "expected_to": "预计",
                "recommended_action": "我们建议",
                "key_finding": "关键发现：",
                "important_note": "重要提示：",
                "in_summary": "总结",
                "compared_to": "相比",
                "increase_by": "增加",
                "decrease_by": "减少"
            }
        }
    
    def detect_language(self, text: str) -> Language:
        """Detect the language of input text."""
        try:
            detected = detect(text)
            # Map to our supported languages
            if detected == "en":
                return Language.ENGLISH
            elif detected == "es":
                return Language.SPANISH
            elif detected in ["zh", "zh-cn", "zh-tw"]:
                return Language.CHINESE
            else:
                return Language.ENGLISH  # Default
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return Language.ENGLISH
    
    def translate_term(
        self,
        term: str,
        from_lang: Language,
        to_lang: Language
    ) -> str:
        """Translate a financial term between languages."""
        if from_lang == to_lang:
            return term
        
        # Get translation if available
        from_dict = self.translations.get(from_lang, {})
        to_dict = self.translations.get(to_lang, {})
        
        # Find the term key
        term_lower = term.lower()
        for key, value in from_dict.items():
            if value.lower() == term_lower:
                return to_dict.get(key, term)
        
        return term  # Return original if no translation found
    
    def format_number(
        self,
        number: float,
        language: Language,
        number_type: str = "number",  # "number", "currency", "percentage"
        decimals: int = 2
    ) -> str:
        """Format a number according to language conventions."""
        fmt = self.number_formats.get(language, self.number_formats[Language.ENGLISH])
        
        # Format the base number
        if decimals > 0:
            formatted = f"{number:,.{decimals}f}"
        else:
            formatted = f"{number:,.0f}"
        
        # Apply language-specific separators
        if language == Language.SPANISH:
            # Spanish uses opposite separators
            formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        # Add type-specific formatting
        if number_type == "currency":
            symbol = fmt["currency"]
            if fmt["currency_position"] == "prefix":
                formatted = f"{symbol}{formatted}"
            else:
                formatted = f"{formatted}{symbol}"
        elif number_type == "percentage":
            symbol = fmt["percentage"]
            if fmt["percentage_position"] == "suffix":
                formatted = f"{formatted}{symbol}"
            else:
                formatted = f"{symbol}{formatted}"
        
        return formatted
    
    def get_disclaimer(
        self,
        disclaimer_type: str,
        language: Language
    ) -> str:
        """Get localized disclaimer text."""
        disclaimers = self.disclaimers.get(language, self.disclaimers[Language.ENGLISH])
        return disclaimers.get(disclaimer_type, disclaimers.get("general", ""))
    
    def get_all_disclaimers(self, language: Language) -> str:
        """Get all relevant disclaimers combined."""
        disclaimers = self.disclaimers.get(language, self.disclaimers[Language.ENGLISH])
        
        # Combine general and regulatory disclaimers
        combined = [
            disclaimers.get("general", ""),
            disclaimers.get("regulatory", "")
        ]
        
        return "\n\n".join(filter(None, combined))
    
    def localize_narrative(
        self,
        narrative: str,
        from_lang: Language,
        to_lang: Language
    ) -> str:
        """Localize a complete narrative to target language."""
        if from_lang == to_lang:
            return narrative
        
        localized = narrative
        
        # Translate common terms
        from_dict = self.translations.get(from_lang, {})
        to_dict = self.translations.get(to_lang, {})
        
        for key in from_dict:
            from_term = from_dict[key]
            to_term = to_dict.get(key, from_term)
            
            if from_term != to_term:
                # Case-sensitive replacement
                localized = localized.replace(from_term, to_term)
                localized = localized.replace(from_term.capitalize(), to_term.capitalize())
                localized = localized.replace(from_term.upper(), to_term.upper())
        
        # Translate common phrases
        from_phrases = self.phrase_templates.get(from_lang, {})
        to_phrases = self.phrase_templates.get(to_lang, {})
        
        for key in from_phrases:
            from_phrase = from_phrases[key]
            to_phrase = to_phrases.get(key, from_phrase)
            
            if from_phrase != to_phrase:
                localized = localized.replace(from_phrase, to_phrase)
        
        return localized
    
    def validate_numerical_consistency(
        self,
        original: str,
        translated: str,
        tolerance: float = 0.01
    ) -> Tuple[bool, List[str]]:
        """Validate that translation maintains numerical consistency."""
        errors = []
        
        # Extract numbers from both texts
        original_numbers = re.findall(r'[\d,]+\.?\d*', original)
        translated_numbers = re.findall(r'[\d,.]+', translated)
        
        # Clean and parse numbers
        original_values = []
        for num in original_numbers:
            try:
                cleaned = num.replace(',', '')
                original_values.append(float(cleaned))
            except ValueError:
                continue
        
        translated_values = []
        for num in translated_numbers:
            try:
                # Handle different decimal separators
                if ',' in num and '.' in num:
                    # Determine which is decimal separator
                    if num.rfind(',') > num.rfind('.'):
                        # Comma is decimal separator (European style)
                        cleaned = num.replace('.', '').replace(',', '.')
                    else:
                        # Period is decimal separator (US style)
                        cleaned = num.replace(',', '')
                else:
                    cleaned = num.replace(',', '')
                
                translated_values.append(float(cleaned))
            except ValueError:
                continue
        
        # Check if all significant numbers are preserved
        original_set = set(round(v, 2) for v in original_values if abs(v) > tolerance)
        translated_set = set(round(v, 2) for v in translated_values if abs(v) > tolerance)
        
        missing = original_set - translated_set
        extra = translated_set - original_set
        
        if missing:
            errors.append(f"Missing numbers in translation: {missing}")
        if extra:
            errors.append(f"Extra numbers in translation: {extra}")
        
        return len(errors) == 0, errors
    
    async def translate(
        self,
        text: str,
        target_language: Language,
        source_language: Optional[Language] = None
    ) -> str:
        """Translate text to target language (placeholder for future API integration)."""
        # This is a placeholder for future integration with translation APIs
        # For now, return the original text
        logger.info(f"Translation requested from {source_language} to {target_language}")
        return text
    
    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages."""
        return [Language.ENGLISH, Language.SPANISH, Language.CHINESE]
    
    def is_language_supported(self, language: Language) -> bool:
        """Check if a language is supported."""
        return language in self.get_supported_languages()