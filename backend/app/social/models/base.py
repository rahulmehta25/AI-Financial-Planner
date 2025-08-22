"""
Base model for social features with common fields and audit trail
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from app.database.base import Base


class SocialBase(Base):
    """Base class for all social feature models with common audit fields"""
    
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Privacy and moderation
    is_public = Column(Boolean, default=True, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)
    moderation_notes = Column(Text, nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    
    @declared_attr
    def moderated_by_id(cls):
        return Column(UUID(as_uuid=True), nullable=True)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def flag_for_moderation(self, notes: str = None):
        """Flag content for moderation review"""
        self.is_flagged = True
        if notes:
            self.moderation_notes = notes
        self.updated_at = datetime.utcnow()
    
    def approve_content(self, moderator_id: uuid.UUID, notes: str = None):
        """Approve content after moderation"""
        self.is_flagged = False
        self.is_public = True
        self.moderated_by_id = moderator_id
        self.moderated_at = datetime.utcnow()
        if notes:
            self.moderation_notes = notes
        self.updated_at = datetime.utcnow()
    
    def reject_content(self, moderator_id: uuid.UUID, notes: str = None):
        """Reject content after moderation"""
        self.is_flagged = True
        self.is_public = False
        self.moderated_by_id = moderator_id
        self.moderated_at = datetime.utcnow()
        if notes:
            self.moderation_notes = notes
        self.updated_at = datetime.utcnow()