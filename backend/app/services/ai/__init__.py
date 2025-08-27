"""
AI Services Module
Provides LLM integration, behavioral analysis, recommendations, and RAG capabilities
"""

from .llm_service import (
    FinancialLLMIntegration,
    PersonalizedAdvice,
    UserContext,
    MarketContext,
    TaskType,
    ModelProvider
)

from .behavioral_analysis_service import (
    BehavioralAnalysisService,
    UserBehaviorProfile,
    RiskProfile,
    LifeStage,
    BehaviorPattern,
    PredictedBehavior
)

from .recommendations import (
    RecommendationEngine,
    Recommendation,
    PortfolioRecommendation,
    GoalRecommendation,
    NextBestAction,
    RecommendationType,
    Priority
)

from .context_management import (
    ContextManager,
    ComprehensiveContext,
    ConversationContext,
    MarketContext as MarketContextData,
    PortfolioContext,
    UserLifeContext,
    TaxContext,
    GoalContext,
    ContextType
)

from .rag_system import (
    FinancialRAGSystem,
    KnowledgeSource,
    DocumentType,
    KnowledgeDocument,
    RetrievalResult
)

__all__ = [
    # LLM Integration
    'FinancialLLMIntegration',
    'PersonalizedAdvice',
    'UserContext',
    'MarketContext',
    'TaskType',
    'ModelProvider',
    
    # Behavioral Analysis
    'BehavioralAnalysisService',
    'UserBehaviorProfile',
    'RiskProfile',
    'LifeStage',
    'BehaviorPattern',
    'PredictedBehavior',
    
    # Recommendations
    'RecommendationEngine',
    'Recommendation',
    'PortfolioRecommendation',
    'GoalRecommendation',
    'NextBestAction',
    'RecommendationType',
    'Priority',
    
    # Context Management
    'ContextManager',
    'ComprehensiveContext',
    'ConversationContext',
    'MarketContextData',
    'PortfolioContext',
    'UserLifeContext',
    'TaxContext',
    'GoalContext',
    'ContextType',
    
    # RAG System
    'FinancialRAGSystem',
    'KnowledgeSource',
    'DocumentType',
    'KnowledgeDocument',
    'RetrievalResult'
]