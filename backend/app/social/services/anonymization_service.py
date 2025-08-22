"""
Anonymization service for privacy-preserving data sharing
"""

import uuid
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.user_social import UserSocialProfile, UserPrivacySettings
from ..models.goal_sharing import AnonymousGoalShare, AgeGroup, IncomeRange


class AnonymizationService:
    """Service for anonymizing user data for privacy-preserving sharing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def anonymize_user_id(self, user_id: uuid.UUID, context: str = "general") -> str:
        """
        Create anonymous identifier for user that's consistent within context
        but doesn't expose actual user ID
        """
        # Use SHA-256 with salt based on context
        salt = f"social_platform_{context}"
        combined = f"{user_id}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def get_age_group(self, birth_date: datetime) -> AgeGroup:
        """Convert birth date to age group enum for anonymous sharing"""
        if not birth_date:
            return None
            
        age = (datetime.now() - birth_date).days // 365
        
        if age < 25:
            return AgeGroup.UNDER_25
        elif age < 35:
            return AgeGroup.AGE_25_34
        elif age < 45:
            return AgeGroup.AGE_35_44
        elif age < 55:
            return AgeGroup.AGE_45_54
        elif age < 65:
            return AgeGroup.AGE_55_64
        else:
            return AgeGroup.OVER_65
    
    def get_income_range(self, annual_income: float) -> IncomeRange:
        """Convert income to range enum for anonymous sharing"""
        if not annual_income:
            return None
            
        if annual_income < 30000:
            return IncomeRange.UNDER_30K
        elif annual_income < 50000:
            return IncomeRange.RANGE_30K_50K
        elif annual_income < 75000:
            return IncomeRange.RANGE_50K_75K
        elif annual_income < 100000:
            return IncomeRange.RANGE_75K_100K
        elif annual_income < 150000:
            return IncomeRange.RANGE_100K_150K
        elif annual_income < 250000:
            return IncomeRange.RANGE_150K_250K
        else:
            return IncomeRange.OVER_250K
    
    def anonymize_amount_to_range(self, amount: float) -> str:
        """Convert specific amounts to ranges for privacy"""
        if amount < 1000:
            return "Under $1K"
        elif amount < 5000:
            return "$1K - $5K"
        elif amount < 10000:
            return "$5K - $10K"
        elif amount < 25000:
            return "$10K - $25K"
        elif amount < 50000:
            return "$25K - $50K"
        elif amount < 100000:
            return "$50K - $100K"
        elif amount < 250000:
            return "$100K - $250K"
        elif amount < 500000:
            return "$250K - $500K"
        else:
            return "Over $500K"
    
    def get_location_region(self, location: str) -> Optional[str]:
        """Convert specific location to general region for privacy"""
        if not location:
            return None
        
        # Simple region mapping - in production, use a comprehensive location service
        location_lower = location.lower()
        
        northeast_states = ["ny", "nj", "pa", "ct", "ma", "ri", "nh", "vt", "me"]
        southeast_states = ["fl", "ga", "sc", "nc", "va", "wv", "ky", "tn", "al", "ms", "ar", "la"]
        midwest_states = ["oh", "mi", "in", "il", "wi", "mn", "ia", "mo", "nd", "sd", "ne", "ks"]
        southwest_states = ["tx", "ok", "nm", "az"]
        west_states = ["ca", "nv", "or", "wa", "id", "mt", "wy", "co", "ut", "ak", "hi"]
        
        for state in northeast_states:
            if state in location_lower:
                return "Northeast"
        
        for state in southeast_states:
            if state in location_lower:
                return "Southeast"
        
        for state in midwest_states:
            if state in location_lower:
                return "Midwest"
        
        for state in southwest_states:
            if state in location_lower:
                return "Southwest"
        
        for state in west_states:
            if state in location_lower:
                return "West"
        
        return "Other"
    
    def sanitize_goal_title(self, title: str) -> str:
        """Remove potentially identifying information from goal titles"""
        # Remove specific names, addresses, etc.
        # This is a simplified version - production would use NLP
        import re
        
        # Remove email addresses
        title = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', title)
        
        # Remove phone numbers
        title = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone]', title)
        
        # Remove potential addresses
        title = re.sub(r'\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)\b', '[address]', title)
        
        # Remove proper names (simplified - would use NER in production)
        title = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[name]', title)
        
        return title.strip()
    
    def can_share_demographic_data(self, user_id: uuid.UUID, data_type: str) -> bool:
        """Check if user allows sharing of specific demographic data"""
        privacy_settings = self.db.query(UserPrivacySettings).join(
            UserSocialProfile, UserPrivacySettings.user_profile_id == UserSocialProfile.id
        ).filter(UserSocialProfile.user_id == user_id).first()
        
        if not privacy_settings:
            return False
        
        data_type_mapping = {
            "age": privacy_settings.share_age_range,
            "income": privacy_settings.share_income_range,
            "net_worth": privacy_settings.share_net_worth_range,
            "investments": privacy_settings.share_investment_types
        }
        
        return data_type_mapping.get(data_type, False)
    
    def create_anonymous_profile_snapshot(self, user_id: uuid.UUID, context: str = "goal_sharing") -> Dict[str, Any]:
        """Create an anonymous snapshot of user profile for sharing"""
        user_profile = self.db.query(UserSocialProfile).filter(
            UserSocialProfile.user_id == user_id
        ).first()
        
        if not user_profile or not user_profile.privacy_settings:
            return {"anonymous_id": self.anonymize_user_id(user_id, context)}
        
        privacy_settings = user_profile.privacy_settings
        anonymous_data = {
            "anonymous_id": self.anonymize_user_id(user_id, context),
            "experience_level": user_profile.experience_level,
            "reputation_score": user_profile.reputation_score if context == "community" else None,
        }
        
        # Add demographic data based on privacy settings
        if privacy_settings.share_age_range and hasattr(user_profile.user, 'birth_date'):
            anonymous_data["age_group"] = self.get_age_group(user_profile.user.birth_date)
        
        if privacy_settings.share_income_range and hasattr(user_profile.user, 'annual_income'):
            anonymous_data["income_range"] = self.get_income_range(user_profile.user.annual_income)
        
        if privacy_settings.share_investment_types:
            anonymous_data["investment_experience"] = user_profile.expertise_areas
        
        if user_profile.location and context in ["community", "mentorship"]:
            anonymous_data["region"] = self.get_location_region(user_profile.location)
        
        return anonymous_data
    
    def ensure_minimum_group_size(self, query_results: List[Any], minimum_size: int = 10) -> List[Any]:
        """
        Ensure anonymity by only returning results when group size meets minimum threshold
        This prevents identification through small group sizes
        """
        if len(query_results) < minimum_size:
            return []
        return query_results
    
    def add_differential_privacy_noise(self, value: float, epsilon: float = 1.0) -> float:
        """
        Add Laplace noise for differential privacy
        epsilon controls privacy level (lower = more private)
        """
        import random
        import math
        
        # Laplace mechanism
        scale = 1.0 / epsilon
        noise = random.random() - 0.5
        if noise >= 0:
            laplace_noise = scale * math.log(2 * noise)
        else:
            laplace_noise = -scale * math.log(-2 * noise)
        
        return max(0.0, value + laplace_noise)
    
    def anonymize_success_story(self, story_text: str, user_id: uuid.UUID) -> Dict[str, Any]:
        """Create an anonymized version of a success story"""
        sanitized_text = self.sanitize_goal_title(story_text)  # Reuse sanitization logic
        anonymous_profile = self.create_anonymous_profile_snapshot(user_id, "success_story")
        
        return {
            "story": sanitized_text,
            "author": anonymous_profile,
            "anonymized_at": datetime.utcnow(),
            "privacy_level": "high"
        }
    
    def check_k_anonymity(self, dataset: List[Dict], k: int = 5, quasi_identifiers: List[str] = None) -> bool:
        """
        Check if dataset satisfies k-anonymity requirement
        Each combination of quasi-identifiers should appear at least k times
        """
        if not quasi_identifiers:
            quasi_identifiers = ["age_group", "income_range", "region"]
        
        if len(dataset) < k:
            return False
        
        # Group by quasi-identifiers
        groups = {}
        for record in dataset:
            key = tuple(record.get(qi, None) for qi in quasi_identifiers)
            groups.setdefault(key, []).append(record)
        
        # Check if all groups have at least k members
        return all(len(group) >= k for group in groups.values())