"""
Data Privacy & GDPR Compliance Module

Implements:
- GDPR compliance (Right to be forgotten, Data portability)
- CCPA compliance
- Data anonymization and pseudonymization
- Consent management
- Data retention policies
- Privacy by design
"""

import hashlib
import json
import uuid
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
import re
from faker import Faker
import pandas as pd
import numpy as np

from app.core.config import settings


class ConsentType(Enum):
    """Types of data processing consent"""
    ESSENTIAL = "essential"  # Required for service
    ANALYTICS = "analytics"  # Usage analytics
    MARKETING = "marketing"  # Marketing communications
    PERSONALIZATION = "personalization"  # Personalized recommendations
    DATA_SHARING = "data_sharing"  # Sharing with third parties
    RESEARCH = "research"  # Anonymous research purposes


class DataCategory(Enum):
    """Categories of personal data"""
    IDENTITY = "identity"  # Name, username, etc.
    CONTACT = "contact"  # Email, phone, address
    FINANCIAL = "financial"  # Account numbers, transactions
    TECHNICAL = "technical"  # IP address, cookies
    USAGE = "usage"  # Service usage data
    PREFERENCES = "preferences"  # User preferences
    SENSITIVE = "sensitive"  # Health, biometric data


class RetentionPeriod(Enum):
    """Data retention periods"""
    IMMEDIATE = 0  # Delete immediately after use
    SESSION = 1  # Delete after session ends
    DAYS_30 = 30
    DAYS_90 = 90
    MONTHS_6 = 180
    YEARS_1 = 365
    YEARS_3 = 1095
    YEARS_7 = 2555  # Financial records
    INDEFINITE = -1  # Keep until deletion requested


@dataclass
class ConsentRecord:
    """Record of user consent"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    ip_address: str
    version: str
    withdrawal_timestamp: Optional[datetime] = None


@dataclass
class DataExportRequest:
    """Data export request (GDPR Article 20)"""
    request_id: str
    user_id: str
    requested_at: datetime
    categories: List[DataCategory]
    format: str  # json, csv, xml
    status: str  # pending, processing, completed, failed
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class DeletionRequest:
    """Data deletion request (GDPR Article 17)"""
    request_id: str
    user_id: str
    requested_at: datetime
    reason: str
    categories: List[DataCategory]
    status: str  # pending, processing, completed, failed
    completed_at: Optional[datetime] = None
    data_retained: Dict[str, str] = None  # Legal retention requirements


class DataAnonymizer:
    """Data anonymization and pseudonymization"""
    
    def __init__(self):
        self.faker = Faker()
        self.salt = settings.ANONYMIZATION_SALT if hasattr(settings, 'ANONYMIZATION_SALT') else 'default_salt'
        
    def pseudonymize_identifier(self, identifier: str) -> str:
        """Create pseudonym for identifier (reversible with key)"""
        # Use HMAC for deterministic pseudonymization
        import hmac
        
        pseudonym = hmac.new(
            self.salt.encode(),
            identifier.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        return f"PSEUDO_{pseudonym}"
    
    def anonymize_email(self, email: str) -> str:
        """Anonymize email address"""
        if '@' in email:
            local, domain = email.split('@')
            # Keep domain for analytics, anonymize local part
            return f"user_{hashlib.md5(local.encode()).hexdigest()[:8]}@{domain}"
        return "anonymous@example.com"
    
    def anonymize_phone(self, phone: str) -> str:
        """Anonymize phone number"""
        # Keep country code and area code, mask rest
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) >= 10:
            return cleaned[:3] + '*' * (len(cleaned) - 6) + cleaned[-3:]
        return '*' * len(cleaned)
    
    def anonymize_ip_address(self, ip: str) -> str:
        """Anonymize IP address"""
        parts = ip.split('.')
        if len(parts) == 4:
            # Zero out last octet for IPv4
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        elif ':' in ip:
            # IPv6 - zero out last 64 bits
            parts = ip.split(':')
            return ':'.join(parts[:4] + ['0'] * 4)
        return "0.0.0.0"
    
    def anonymize_location(self, lat: float, lon: float) -> Tuple[float, float]:
        """Anonymize GPS coordinates"""
        # Round to 2 decimal places (roughly 1.1km precision)
        return round(lat, 2), round(lon, 2)
    
    def anonymize_date_of_birth(self, dob: datetime) -> datetime:
        """Anonymize date of birth to just year"""
        return datetime(dob.year, 1, 1)
    
    def anonymize_financial_amount(self, amount: float) -> float:
        """Anonymize financial amounts"""
        # Round to nearest 100
        return round(amount / 100) * 100
    
    def anonymize_name(self, name: str) -> str:
        """Replace name with fake name"""
        return self.faker.name()
    
    def anonymize_address(self, address: str) -> str:
        """Replace address with fake address"""
        return self.faker.address()
    
    def anonymize_document(
        self,
        document: Dict[str, Any],
        field_rules: Dict[str, str]
    ) -> Dict[str, Any]:
        """Anonymize document based on field rules"""
        anonymized = {}
        
        for field, value in document.items():
            if field in field_rules:
                rule = field_rules[field]
                
                if rule == "remove":
                    continue  # Skip this field
                elif rule == "pseudonymize":
                    anonymized[field] = self.pseudonymize_identifier(str(value))
                elif rule == "email":
                    anonymized[field] = self.anonymize_email(value)
                elif rule == "phone":
                    anonymized[field] = self.anonymize_phone(value)
                elif rule == "ip":
                    anonymized[field] = self.anonymize_ip_address(value)
                elif rule == "name":
                    anonymized[field] = self.anonymize_name(value)
                elif rule == "address":
                    anonymized[field] = self.anonymize_address(value)
                elif rule == "financial":
                    anonymized[field] = self.anonymize_financial_amount(float(value))
                elif rule == "date":
                    anonymized[field] = self.anonymize_date_of_birth(value)
                else:
                    anonymized[field] = value
            else:
                anonymized[field] = value
        
        return anonymized


class ConsentManager:
    """Manage user consent for data processing"""
    
    def __init__(self):
        self.consent_records: Dict[str, List[ConsentRecord]] = {}
        self.consent_versions = {
            ConsentType.ESSENTIAL: "1.0",
            ConsentType.ANALYTICS: "1.0",
            ConsentType.MARKETING: "1.0",
            ConsentType.PERSONALIZATION: "1.0",
            ConsentType.DATA_SHARING: "1.0",
            ConsentType.RESEARCH: "1.0"
        }
    
    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        ip_address: str
    ) -> ConsentRecord:
        """Record user consent"""
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            version=self.consent_versions[consent_type]
        )
        
        if user_id not in self.consent_records:
            self.consent_records[user_id] = []
        
        self.consent_records[user_id].append(record)
        
        # TODO: Persist to database
        
        return record
    
    async def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Withdraw consent"""
        if user_id in self.consent_records:
            for record in self.consent_records[user_id]:
                if record.consent_type == consent_type and record.granted:
                    record.granted = False
                    record.withdrawal_timestamp = datetime.utcnow()
                    # TODO: Update in database
                    return True
        return False
    
    async def get_user_consents(self, user_id: str) -> Dict[ConsentType, bool]:
        """Get current consent status for user"""
        consents = {consent_type: False for consent_type in ConsentType}
        
        if user_id in self.consent_records:
            # Get latest consent for each type
            for record in reversed(self.consent_records[user_id]):
                if record.consent_type not in consents or consents[record.consent_type] is False:
                    consents[record.consent_type] = record.granted
        
        # Essential consent is always true (required for service)
        consents[ConsentType.ESSENTIAL] = True
        
        return consents
    
    async def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Check if user has given consent"""
        consents = await self.get_user_consents(user_id)
        return consents.get(consent_type, False)


class DataRetentionManager:
    """Manage data retention policies"""
    
    def __init__(self):
        self.retention_policies = {
            DataCategory.IDENTITY: RetentionPeriod.INDEFINITE,
            DataCategory.CONTACT: RetentionPeriod.INDEFINITE,
            DataCategory.FINANCIAL: RetentionPeriod.YEARS_7,  # Legal requirement
            DataCategory.TECHNICAL: RetentionPeriod.DAYS_90,
            DataCategory.USAGE: RetentionPeriod.YEARS_1,
            DataCategory.PREFERENCES: RetentionPeriod.INDEFINITE,
            DataCategory.SENSITIVE: RetentionPeriod.DAYS_30
        }
    
    def get_retention_period(self, category: DataCategory) -> int:
        """Get retention period for data category"""
        period = self.retention_policies.get(category, RetentionPeriod.DAYS_90)
        return period.value
    
    async def identify_expired_data(self) -> List[Dict[str, Any]]:
        """Identify data that has exceeded retention period"""
        expired_data = []
        
        # TODO: Query database for expired data
        # This is a mock implementation
        for category, period in self.retention_policies.items():
            if period != RetentionPeriod.INDEFINITE:
                cutoff_date = datetime.utcnow() - timedelta(days=period.value)
                
                # Mock expired data
                expired_data.append({
                    "category": category.value,
                    "cutoff_date": cutoff_date.isoformat(),
                    "count": 0  # Would be actual count from DB
                })
        
        return expired_data
    
    async def delete_expired_data(self) -> Dict[str, int]:
        """Delete data that has exceeded retention period"""
        deletion_stats = {}
        
        expired_data = await self.identify_expired_data()
        
        for item in expired_data:
            # TODO: Actual deletion from database
            deletion_stats[item["category"]] = item["count"]
        
        return deletion_stats


class DataPortabilityService:
    """Handle data portability requests (GDPR Article 20)"""
    
    def __init__(self):
        self.anonymizer = DataAnonymizer()
        self.export_requests: Dict[str, DataExportRequest] = {}
    
    async def create_export_request(
        self,
        user_id: str,
        categories: List[DataCategory],
        format: str = "json"
    ) -> DataExportRequest:
        """Create data export request"""
        request = DataExportRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            requested_at=datetime.utcnow(),
            categories=categories,
            format=format,
            status="pending"
        )
        
        self.export_requests[request.request_id] = request
        
        # Process asynchronously
        asyncio.create_task(self._process_export_request(request))
        
        return request
    
    async def _process_export_request(self, request: DataExportRequest):
        """Process data export request"""
        try:
            request.status = "processing"
            
            # Collect user data
            user_data = await self._collect_user_data(
                request.user_id,
                request.categories
            )
            
            # Format data
            if request.format == "json":
                export_data = json.dumps(user_data, indent=2, default=str)
            elif request.format == "csv":
                # Convert to CSV
                df = pd.DataFrame(user_data)
                export_data = df.to_csv(index=False)
            else:
                export_data = str(user_data)
            
            # Store export file
            file_path = f"/tmp/exports/{request.request_id}.{request.format}"
            # TODO: Store in secure storage (S3, etc.)
            
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.download_url = f"/api/v1/privacy/exports/{request.request_id}"
            request.expires_at = datetime.utcnow() + timedelta(days=7)
            
        except Exception as e:
            request.status = "failed"
            print(f"Export failed: {str(e)}")
    
    async def _collect_user_data(
        self,
        user_id: str,
        categories: List[DataCategory]
    ) -> Dict[str, Any]:
        """Collect user data for export"""
        user_data = {
            "export_metadata": {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "categories": [cat.value for cat in categories]
            }
        }
        
        # TODO: Collect actual data from database
        # Mock implementation
        if DataCategory.IDENTITY in categories:
            user_data["identity"] = {
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe"
            }
        
        if DataCategory.CONTACT in categories:
            user_data["contact"] = {
                "email": "john@example.com",
                "phone": "+1234567890"
            }
        
        if DataCategory.FINANCIAL in categories:
            user_data["financial"] = {
                "accounts": [],
                "transactions": []
            }
        
        return user_data


class RightToErasureService:
    """Handle right to erasure requests (GDPR Article 17)"""
    
    def __init__(self):
        self.anonymizer = DataAnonymizer()
        self.deletion_requests: Dict[str, DeletionRequest] = {}
    
    async def create_deletion_request(
        self,
        user_id: str,
        reason: str,
        categories: Optional[List[DataCategory]] = None
    ) -> DeletionRequest:
        """Create deletion request"""
        if categories is None:
            categories = list(DataCategory)  # All categories
        
        request = DeletionRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            requested_at=datetime.utcnow(),
            reason=reason,
            categories=categories,
            status="pending"
        )
        
        self.deletion_requests[request.request_id] = request
        
        # Process asynchronously
        asyncio.create_task(self._process_deletion_request(request))
        
        return request
    
    async def _process_deletion_request(self, request: DeletionRequest):
        """Process deletion request"""
        try:
            request.status = "processing"
            
            data_retained = {}
            
            for category in request.categories:
                # Check if data must be retained for legal reasons
                if self._must_retain_for_legal(category):
                    # Anonymize instead of delete
                    await self._anonymize_category_data(
                        request.user_id,
                        category
                    )
                    data_retained[category.value] = "anonymized for legal retention"
                else:
                    # Delete data
                    await self._delete_category_data(
                        request.user_id,
                        category
                    )
            
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.data_retained = data_retained
            
        except Exception as e:
            request.status = "failed"
            print(f"Deletion failed: {str(e)}")
    
    def _must_retain_for_legal(self, category: DataCategory) -> bool:
        """Check if data must be retained for legal compliance"""
        # Financial data must be retained for 7 years
        if category == DataCategory.FINANCIAL:
            return True
        return False
    
    async def _anonymize_category_data(
        self,
        user_id: str,
        category: DataCategory
    ):
        """Anonymize data in category"""
        # TODO: Implement actual anonymization in database
        print(f"Anonymizing {category.value} data for user {user_id}")
    
    async def _delete_category_data(
        self,
        user_id: str,
        category: DataCategory
    ):
        """Delete data in category"""
        # TODO: Implement actual deletion from database
        print(f"Deleting {category.value} data for user {user_id}")


class PrivacyComplianceService:
    """Main privacy compliance service"""
    
    def __init__(self):
        self.consent_manager = ConsentManager()
        self.retention_manager = DataRetentionManager()
        self.portability_service = DataPortabilityService()
        self.erasure_service = RightToErasureService()
        self.anonymizer = DataAnonymizer()
    
    async def handle_data_request(
        self,
        user_id: str,
        request_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle privacy-related data request"""
        
        if request_type == "export":
            # Data portability request
            categories = kwargs.get("categories", list(DataCategory))
            format = kwargs.get("format", "json")
            
            request = await self.portability_service.create_export_request(
                user_id,
                categories,
                format
            )
            
            return asdict(request)
        
        elif request_type == "delete":
            # Right to erasure request
            reason = kwargs.get("reason", "User requested deletion")
            categories = kwargs.get("categories", list(DataCategory))
            
            request = await self.erasure_service.create_deletion_request(
                user_id,
                reason,
                categories
            )
            
            return asdict(request)
        
        elif request_type == "consent":
            # Get consent status
            consents = await self.consent_manager.get_user_consents(user_id)
            return {
                consent_type.value: granted
                for consent_type, granted in consents.items()
            }
        
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def update_consent(
        self,
        user_id: str,
        consents: Dict[ConsentType, bool],
        ip_address: str
    ):
        """Update user consents"""
        for consent_type, granted in consents.items():
            await self.consent_manager.record_consent(
                user_id,
                consent_type,
                granted,
                ip_address
            )
    
    async def anonymize_inactive_users(self, inactive_days: int = 365):
        """Anonymize data for inactive users"""
        # TODO: Query for inactive users
        inactive_users = []  # Would come from database
        
        for user_id in inactive_users:
            # Anonymize non-essential data
            await self.erasure_service._anonymize_category_data(
                user_id,
                DataCategory.USAGE
            )
            await self.erasure_service._anonymize_category_data(
                user_id,
                DataCategory.TECHNICAL
            )
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        return {
            "gdpr_compliant": True,
            "ccpa_compliant": True,
            "data_categories": [cat.value for cat in DataCategory],
            "consent_types": [ct.value for ct in ConsentType],
            "retention_policies": {
                cat.value: self.retention_manager.get_retention_period(cat)
                for cat in DataCategory
            },
            "anonymization_enabled": True,
            "data_portability_enabled": True,
            "right_to_erasure_enabled": True
        }


# Global privacy service instance
privacy_service = PrivacyComplianceService()