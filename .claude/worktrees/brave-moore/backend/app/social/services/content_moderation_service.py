"""
Content moderation service for automated and manual content review
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.forums import ForumModeration, ModerationAction, ModerationReason, ForumPost, ForumTopic
from ..models.base import SocialBase


class ContentModerationService:
    """Service for automated content moderation and safety"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Predefined lists for content analysis
        self.spam_keywords = [
            "click here", "make money fast", "guaranteed profit", "risk-free", 
            "get rich quick", "easy money", "no experience needed", "work from home",
            "buy now", "limited time", "act now", "free money", "100% guaranteed"
        ]
        
        self.financial_misinformation_patterns = [
            r"guaranteed\s+\d+%\s+return",
            r"risk[-\s]?free\s+investment",
            r"double\s+your\s+money",
            r"can\'t\s+lose",
            r"secret\s+trading\s+strategy",
            r"insider\s+information"
        ]
        
        self.harassment_keywords = [
            "stupid", "idiot", "loser", "worthless", "pathetic", "garbage",
            # Add more comprehensive list in production
        ]
        
        self.solicitation_patterns = [
            r"dm\s+me\s+for",
            r"contact\s+me\s+at",
            r"visit\s+my\s+website",
            r"buy\s+my\s+course",
            r"subscribe\s+to\s+my",
            r"follow\s+me\s+at"
        ]
    
    def analyze_content(self, content: str, content_type: str = "post") -> Dict[str, Any]:
        """
        Analyze content for potential policy violations
        Returns moderation score and flags
        """
        analysis = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "flags": [],
            "severity_score": 0.0,  # 0-100, higher = more problematic
            "confidence": 0.0,
            "requires_human_review": False,
            "auto_action": None
        }
        
        # Check for spam
        spam_score = self._check_spam_content(content)
        if spam_score > 0.6:
            analysis["flags"].append("potential_spam")
            analysis["severity_score"] += spam_score * 30
        
        # Check for financial misinformation
        misinfo_score = self._check_financial_misinformation(content)
        if misinfo_score > 0.5:
            analysis["flags"].append("financial_misinformation")
            analysis["severity_score"] += misinfo_score * 50
        
        # Check for harassment
        harassment_score = self._check_harassment(content)
        if harassment_score > 0.3:
            analysis["flags"].append("harassment")
            analysis["severity_score"] += harassment_score * 40
        
        # Check for solicitation
        solicitation_score = self._check_solicitation(content)
        if solicitation_score > 0.4:
            analysis["flags"].append("solicitation")
            analysis["severity_score"] += solicitation_score * 35
        
        # Check for excessive caps/punctuation
        formatting_score = self._check_formatting_issues(content)
        if formatting_score > 0.5:
            analysis["flags"].append("excessive_formatting")
            analysis["severity_score"] += formatting_score * 10
        
        # Determine confidence and action
        analysis["confidence"] = min(1.0, len(analysis["flags"]) * 0.3 + 0.4)
        
        # Auto-moderation thresholds
        if analysis["severity_score"] > 80:
            analysis["auto_action"] = ModerationAction.HIDDEN
            analysis["requires_human_review"] = True
        elif analysis["severity_score"] > 60:
            analysis["auto_action"] = ModerationAction.FLAGGED
            analysis["requires_human_review"] = True
        elif analysis["severity_score"] > 40:
            analysis["requires_human_review"] = True
        
        return analysis
    
    def _check_spam_content(self, content: str) -> float:
        """Check content for spam indicators"""
        content_lower = content.lower()
        spam_indicators = 0
        total_checks = 0
        
        # Check for spam keywords
        for keyword in self.spam_keywords:
            total_checks += 1
            if keyword in content_lower:
                spam_indicators += 1
        
        # Check for excessive links
        link_count = len(re.findall(r'http[s]?://|www\.', content))
        if link_count > 2:
            spam_indicators += min(link_count - 2, 3)
            total_checks += 3
        
        # Check for repetitive text
        words = content_lower.split()
        unique_words = set(words)
        if len(words) > 10 and len(unique_words) / len(words) < 0.5:
            spam_indicators += 1
        total_checks += 1
        
        return spam_indicators / max(total_checks, 1) if total_checks > 0 else 0
    
    def _check_financial_misinformation(self, content: str) -> float:
        """Check for financial misinformation patterns"""
        matches = 0
        total_patterns = len(self.financial_misinformation_patterns)
        
        for pattern in self.financial_misinformation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matches += 1
        
        # Additional checks for unrealistic claims
        unrealistic_returns = re.findall(r'(\d+)%\s*(?:return|profit|gain)', content, re.IGNORECASE)
        for return_str in unrealistic_returns:
            return_val = int(return_str)
            if return_val > 50:  # Unrealistic return claims
                matches += 1
        
        return matches / max(total_patterns + 1, 1)
    
    def _check_harassment(self, content: str) -> float:
        """Check for harassment and abusive language"""
        content_lower = content.lower()
        harassment_count = 0
        
        for keyword in self.harassment_keywords:
            if keyword in content_lower:
                harassment_count += 1
        
        # Check for excessive negative sentiment indicators
        negative_words = ["hate", "terrible", "awful", "disgusting", "trash"]
        for word in negative_words:
            if word in content_lower:
                harassment_count += 0.5
        
        # Check for personal attacks pattern
        attack_patterns = [r'you\s+are\s+\w+', r'you\'re\s+\w+']
        for pattern in attack_patterns:
            if re.search(pattern, content_lower):
                harassment_count += 1
        
        return min(harassment_count / 5.0, 1.0)  # Normalize to 0-1
    
    def _check_solicitation(self, content: str) -> float:
        """Check for commercial solicitation"""
        matches = 0
        
        for pattern in self.solicitation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matches += 1
        
        # Check for contact information
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):
            matches += 1
        
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content):
            matches += 1
        
        return min(matches / 5.0, 1.0)
    
    def _check_formatting_issues(self, content: str) -> float:
        """Check for excessive formatting that might indicate spam"""
        issues = 0
        
        # Excessive caps
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        if caps_ratio > 0.3:
            issues += caps_ratio
        
        # Excessive punctuation
        punct_count = len(re.findall(r'[!?]{2,}', content))
        if punct_count > 2:
            issues += min(punct_count / 10.0, 0.5)
        
        # Excessive emojis (simplified check)
        emoji_like = len(re.findall(r'[:;=][)(\-D]|[!?]{3,}', content))
        if emoji_like > 5:
            issues += min(emoji_like / 20.0, 0.3)
        
        return min(issues, 1.0)
    
    def auto_moderate_content(self, content_id: uuid.UUID, content_type: str, 
                            content: str, user_id: uuid.UUID) -> Optional[ForumModeration]:
        """
        Automatically moderate content based on analysis
        Returns moderation record if action was taken
        """
        analysis = self.analyze_content(content, content_type)
        
        if not analysis["auto_action"]:
            return None
        
        # Determine reason based on flags
        reason = ModerationReason.POLICY_VIOLATION
        if "financial_misinformation" in analysis["flags"]:
            reason = ModerationReason.FINANCIAL_MISINFORMATION
        elif "potential_spam" in analysis["flags"]:
            reason = ModerationReason.SPAM
        elif "harassment" in analysis["flags"]:
            reason = ModerationReason.HARASSMENT
        elif "solicitation" in analysis["flags"]:
            reason = ModerationReason.SOLICITATION
        
        # Create moderation record
        moderation = ForumModeration(
            post_id=content_id if content_type == "post" else None,
            topic_id=content_id if content_type == "topic" else None,
            reported_user_id=user_id,
            action_taken=analysis["auto_action"],
            reason=reason,
            moderator_notes=f"Auto-moderated. Flags: {', '.join(analysis['flags'])}. Score: {analysis['severity_score']:.1f}",
            is_automated_action=True,
            confidence_score=analysis["confidence"],
            auto_moderation_triggers=analysis["flags"]
        )
        
        self.db.add(moderation)
        
        # Apply the moderation action
        if content_type == "post":
            post = self.db.query(ForumPost).filter(ForumPost.id == content_id).first()
            if post:
                if analysis["auto_action"] == ModerationAction.HIDDEN:
                    post.is_public = False
                post.flag_for_moderation(f"Auto-flagged: {', '.join(analysis['flags'])}")
        
        self.db.commit()
        return moderation
    
    def report_content(self, content_id: uuid.UUID, content_type: str,
                      reported_by_user_id: uuid.UUID, report_reason: str,
                      description: str = None) -> ForumModeration:
        """Create a user report for content"""
        
        # Map reason strings to enums
        reason_mapping = {
            "spam": ModerationReason.SPAM,
            "harassment": ModerationReason.HARASSMENT,
            "inappropriate": ModerationReason.INAPPROPRIATE_CONTENT,
            "misinformation": ModerationReason.FINANCIAL_MISINFORMATION,
            "solicitation": ModerationReason.SOLICITATION,
            "off_topic": ModerationReason.OFF_TOPIC,
            "duplicate": ModerationReason.DUPLICATE_POST
        }
        
        reason_enum = reason_mapping.get(report_reason.lower(), ModerationReason.POLICY_VIOLATION)
        
        # Get the user ID of the content creator
        reported_user_id = None
        if content_type == "post":
            post = self.db.query(ForumPost).filter(ForumPost.id == content_id).first()
            if post:
                reported_user_id = post.user_id
        elif content_type == "topic":
            topic = self.db.query(ForumTopic).filter(ForumTopic.id == content_id).first()
            if topic:
                reported_user_id = topic.created_by_user_id
        
        if not reported_user_id:
            raise ValueError("Content not found")
        
        # Create moderation report
        moderation = ForumModeration(
            post_id=content_id if content_type == "post" else None,
            topic_id=content_id if content_type == "topic" else None,
            reported_user_id=reported_user_id,
            reported_by_user_id=reported_by_user_id,
            action_taken=ModerationAction.FLAGGED,
            reason=reason_enum,
            report_description=description,
            report_category=report_reason,
            moderator_notes="User reported content - pending review"
        )
        
        self.db.add(moderation)
        self.db.commit()
        
        return moderation
    
    def get_moderation_queue(self, moderator_user_id: uuid.UUID, 
                           status_filter: str = "pending") -> List[ForumModeration]:
        """Get moderation queue for a moderator"""
        
        query = self.db.query(ForumModeration).filter(
            ForumModeration.is_resolved == False
        )
        
        if status_filter == "pending":
            query = query.filter(ForumModeration.moderator_user_id.is_(None))
        elif status_filter == "assigned":
            query = query.filter(ForumModeration.moderator_user_id == moderator_user_id)
        elif status_filter == "high_priority":
            query = query.filter(
                or_(
                    ForumModeration.reason == ModerationReason.FINANCIAL_MISINFORMATION,
                    ForumModeration.reason == ModerationReason.HARASSMENT,
                    and_(
                        ForumModeration.confidence_score >= 0.8,
                        ForumModeration.is_automated_action == True
                    )
                )
            )
        
        return query.order_by(ForumModeration.created_at.desc()).limit(50).all()
    
    def moderate_content(self, moderation_id: uuid.UUID, moderator_user_id: uuid.UUID,
                        action: ModerationAction, notes: str = None,
                        duration_hours: int = None) -> ForumModeration:
        """Apply moderation action to reported content"""
        
        moderation = self.db.query(ForumModeration).filter(
            ForumModeration.id == moderation_id
        ).first()
        
        if not moderation:
            raise ValueError("Moderation record not found")
        
        moderation.moderator_user_id = moderator_user_id
        moderation.action_taken = action
        moderation.action_date = datetime.utcnow()
        
        if notes:
            moderation.moderator_notes = notes
        
        if duration_hours:
            moderation.duration_hours = duration_hours
            moderation.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        # Apply the action to the content
        if action == ModerationAction.APPROVED:
            if moderation.post_id:
                post = self.db.query(ForumPost).filter(ForumPost.id == moderation.post_id).first()
                if post:
                    post.approve_content(moderator_user_id, notes)
            elif moderation.topic_id:
                topic = self.db.query(ForumTopic).filter(ForumTopic.id == moderation.topic_id).first()
                if topic:
                    topic.approve_content(moderator_user_id, notes)
        
        elif action in [ModerationAction.HIDDEN, ModerationAction.DELETED]:
            if moderation.post_id:
                post = self.db.query(ForumPost).filter(ForumPost.id == moderation.post_id).first()
                if post:
                    post.reject_content(moderator_user_id, notes)
                    if action == ModerationAction.DELETED:
                        post.soft_delete()
            elif moderation.topic_id:
                topic = self.db.query(ForumTopic).filter(ForumTopic.id == moderation.topic_id).first()
                if topic:
                    topic.reject_content(moderator_user_id, notes)
                    if action == ModerationAction.DELETED:
                        topic.soft_delete()
        
        moderation.resolve_report(notes)
        self.db.commit()
        
        return moderation
    
    def get_user_moderation_history(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get moderation history for a user"""
        
        moderations = self.db.query(ForumModeration).filter(
            ForumModeration.reported_user_id == user_id
        ).order_by(ForumModeration.created_at.desc()).all()
        
        total_reports = len(moderations)
        resolved_reports = len([m for m in moderations if m.is_resolved])
        active_violations = len([m for m in moderations if not m.is_resolved])
        
        recent_violations = [m for m in moderations 
                           if m.created_at > datetime.utcnow() - timedelta(days=30)]
        
        # Calculate risk score
        risk_score = 0
        if total_reports > 0:
            risk_score += min(total_reports * 10, 50)  # Max 50 points for report count
        
        if len(recent_violations) > 2:
            risk_score += 30  # Recent activity penalty
        
        serious_violations = [m for m in moderations 
                            if m.reason in [ModerationReason.HARASSMENT, 
                                          ModerationReason.FINANCIAL_MISINFORMATION]]
        if serious_violations:
            risk_score += len(serious_violations) * 15
        
        risk_level = "low"
        if risk_score > 70:
            risk_level = "high"
        elif risk_score > 40:
            risk_level = "medium"
        
        return {
            "user_id": user_id,
            "total_reports": total_reports,
            "resolved_reports": resolved_reports,
            "active_violations": active_violations,
            "recent_violations_count": len(recent_violations),
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "violation_categories": [m.reason.value for m in moderations],
            "last_violation_date": moderations[0].created_at if moderations else None
        }