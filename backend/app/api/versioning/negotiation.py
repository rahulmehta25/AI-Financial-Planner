"""
Version Negotiation - Handle version negotiation through headers and content types
"""

import re
import logging
from typing import Optional, List, Dict, Tuple
from semantic_version import Version

from .manager import VersionManager

logger = logging.getLogger(__name__)


class VersionNegotiator:
    """Handle API version negotiation"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        
        # Content type patterns for version negotiation
        self.vendor_mime_pattern = re.compile(
            r'application/vnd\.financial-planning\.(?P<version>v\d+(?:\.\d+)?(?:\.\d+)?)\+json'
        )
        self.versioned_json_pattern = re.compile(
            r'application/json;\s*version=(?P<version>\d+(?:\.\d+)?(?:\.\d+)?)'
        )
    
    def negotiate_from_accept_header(self, accept_header: str) -> Optional[str]:
        """Negotiate version from Accept header"""
        if not accept_header:
            return None
        
        # Parse accept header for vendor-specific MIME types
        vendor_version = self._parse_vendor_mime_type(accept_header)
        if vendor_version:
            return vendor_version
        
        # Parse accept header for versioned JSON
        json_version = self._parse_versioned_json(accept_header)
        if json_version:
            return json_version
        
        return None
    
    def _parse_vendor_mime_type(self, accept_header: str) -> Optional[str]:
        """Parse vendor-specific MIME type for version"""
        # Example: application/vnd.financial-planning.v2+json
        # Example: application/vnd.financial-planning.v2.1+json
        
        for mime_type in accept_header.split(','):
            mime_type = mime_type.strip()
            match = self.vendor_mime_pattern.search(mime_type)
            
            if match:
                version_str = match.group('version')
                # Convert v2 -> 2.0.0, v2.1 -> 2.1.0
                semantic_version = self._convert_to_semantic_version(version_str)
                
                if self.version_manager.is_version_supported(semantic_version):
                    return semantic_version
                
                # Try to find compatible version
                compatible_version = self._find_compatible_version(semantic_version)
                if compatible_version:
                    return compatible_version
        
        return None
    
    def _parse_versioned_json(self, accept_header: str) -> Optional[str]:
        """Parse JSON with version parameter"""
        # Example: application/json; version=2.0
        # Example: application/json; version=2
        
        for mime_type in accept_header.split(','):
            mime_type = mime_type.strip()
            match = self.versioned_json_pattern.search(mime_type)
            
            if match:
                version_str = match.group('version')
                semantic_version = self._convert_to_semantic_version(version_str)
                
                if self.version_manager.is_version_supported(semantic_version):
                    return semantic_version
                
                # Try to find compatible version
                compatible_version = self._find_compatible_version(semantic_version)
                if compatible_version:
                    return compatible_version
        
        return None
    
    def _convert_to_semantic_version(self, version_str: str) -> str:
        """Convert version string to semantic version"""
        # Remove 'v' prefix if present
        if version_str.startswith('v'):
            version_str = version_str[1:]
        
        # Split into parts
        parts = version_str.split('.')
        
        # Ensure we have major.minor.patch
        while len(parts) < 3:
            parts.append('0')
        
        return '.'.join(parts[:3])
    
    def _find_compatible_version(self, requested_version: str) -> Optional[str]:
        """Find a compatible version for the requested version"""
        try:
            requested = Version(requested_version)
        except ValueError:
            return None
        
        supported_versions = self.version_manager.get_supported_versions()
        
        # Look for exact match first
        for version in supported_versions:
            if version.semantic_version == requested:
                return version.version
        
        # Look for compatible versions (same major, higher or equal minor)
        compatible_versions = []
        for version in supported_versions:
            version_obj = version.semantic_version
            
            # Same major version
            if version_obj.major == requested.major:
                # Higher or equal minor version (backward compatible)
                if version_obj >= requested:
                    compatible_versions.append(version)
        
        if compatible_versions:
            # Return the closest version
            closest = min(
                compatible_versions,
                key=lambda v: abs(v.semantic_version.minor - requested.minor)
            )
            return closest.version
        
        # Look for newer major versions if configured for migration
        migration_versions = []
        for version in supported_versions:
            if version.semantic_version.major > requested.major:
                migration_versions.append(version)
        
        if migration_versions:
            # Return the lowest major version that's higher
            migration_version = min(
                migration_versions,
                key=lambda v: v.semantic_version.major
            )
            
            # Check if migration is available
            compatibility = self.version_manager.get_compatibility(
                requested_version, migration_version.version
            )
            
            if compatibility and not compatibility.is_breaking_change:
                return migration_version.version
        
        return None
    
    def generate_content_type_for_version(self, version: str, 
                                        format_type: str = "vendor") -> str:
        """Generate appropriate Content-Type for response"""
        if format_type == "vendor":
            # Convert semantic version to vendor format
            version_obj = Version(version)
            vendor_version = f"v{version_obj.major}"
            if version_obj.minor > 0:
                vendor_version += f".{version_obj.minor}"
            
            return f"application/vnd.financial-planning.{vendor_version}+json"
        
        elif format_type == "parameter":
            return f"application/json; version={version}"
        
        else:
            return "application/json"
    
    def negotiate_best_version(self, 
                              accept_header: str,
                              user_preferences: Optional[Dict] = None) -> Tuple[str, str]:
        """Negotiate the best version considering all factors"""
        
        # 1. Try header negotiation first
        header_version = self.negotiate_from_accept_header(accept_header)
        
        # 2. Consider user preferences if available
        preferred_version = None
        if user_preferences:
            preferred_version = user_preferences.get('api_version')
            if preferred_version and self.version_manager.is_version_supported(preferred_version):
                pass  # Use preferred version if supported
            else:
                preferred_version = None
        
        # 3. Determine final version
        final_version = header_version or preferred_version
        
        if not final_version:
            # Fall back to latest stable version
            latest = self.version_manager.get_latest_version()
            final_version = latest.version if latest else "1.0.0"
        
        # 4. Generate appropriate content type
        content_type = self.generate_content_type_for_version(final_version)
        
        return final_version, content_type
    
    def get_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from URL path"""
        # Pattern: /api/v1/... or /api/v2.1/...
        path_pattern = re.compile(r'/api/v(?P<version>\d+(?:\.\d+)?)')
        match = path_pattern.search(path)
        
        if match:
            version_str = match.group('version')
            return self._convert_to_semantic_version(version_str)
        
        return None
    
    def validate_version_request(self, 
                                requested_version: str,
                                client_info: Optional[Dict] = None) -> Dict:
        """Validate a version request and return detailed information"""
        result = {
            'valid': False,
            'version': requested_version,
            'supported': False,
            'deprecated': False,
            'retired': False,
            'alternatives': [],
            'migration_required': False,
            'warnings': [],
            'errors': []
        }
        
        # Check if version exists
        version_obj = self.version_manager.get_version(requested_version)
        if not version_obj:
            result['errors'].append(f"Version {requested_version} does not exist")
            
            # Suggest alternatives
            result['alternatives'] = self._suggest_alternative_versions(requested_version)
            return result
        
        result['valid'] = True
        result['supported'] = version_obj.is_supported
        result['deprecated'] = version_obj.is_deprecated
        result['retired'] = version_obj.is_retired
        
        # Add deprecation warnings
        if version_obj.is_deprecated:
            result['warnings'].append(f"Version {requested_version} is deprecated")
            
            if version_obj.retirement_date:
                days_until_retirement = version_obj.days_until_retirement()
                if days_until_retirement is not None:
                    if days_until_retirement <= 30:
                        result['warnings'].append(
                            f"Version will be retired in {days_until_retirement} days"
                        )
            
            # Check for migration options
            latest = self.version_manager.get_latest_version()
            if latest:
                compatibility = self.version_manager.get_compatibility(
                    requested_version, latest.version
                )
                if compatibility:
                    result['migration_required'] = compatibility.migration_required
                    result['alternatives'].append({
                        'version': latest.version,
                        'migration_guide': compatibility.migration_guide_url,
                        'breaking_changes': compatibility.breaking_changes
                    })
        
        # Add retirement errors
        if version_obj.is_retired:
            result['errors'].append(f"Version {requested_version} has been retired")
            result['alternatives'] = self._suggest_alternative_versions(requested_version)
        
        return result
    
    def _suggest_alternative_versions(self, requested_version: str) -> List[Dict]:
        """Suggest alternative versions for an unsupported version"""
        alternatives = []
        
        try:
            requested = Version(requested_version)
        except ValueError:
            # If invalid version format, suggest latest
            latest = self.version_manager.get_latest_version()
            if latest:
                alternatives.append({
                    'version': latest.version,
                    'reason': 'latest_stable',
                    'description': 'Latest stable version'
                })
            return alternatives
        
        supported_versions = self.version_manager.get_supported_versions()
        
        # Same major version alternatives
        same_major = [
            v for v in supported_versions
            if v.semantic_version.major == requested.major
        ]
        
        if same_major:
            latest_same_major = max(same_major, key=lambda v: v.semantic_version)
            alternatives.append({
                'version': latest_same_major.version,
                'reason': 'same_major_version',
                'description': f'Latest version in v{requested.major} series'
            })
        
        # Next major version
        next_major = [
            v for v in supported_versions
            if v.semantic_version.major == requested.major + 1
        ]
        
        if next_major:
            latest_next_major = max(next_major, key=lambda v: v.semantic_version)
            alternatives.append({
                'version': latest_next_major.version,
                'reason': 'next_major_version',
                'description': f'Upgrade to v{requested.major + 1} series'
            })
        
        # Latest stable as fallback
        latest = self.version_manager.get_latest_version()
        if latest and not any(alt['version'] == latest.version for alt in alternatives):
            alternatives.append({
                'version': latest.version,
                'reason': 'latest_stable',
                'description': 'Latest stable version'
            })
        
        return alternatives
    
    def create_version_negotiation_response(self, 
                                          negotiation_result: Dict,
                                          request_info: Dict) -> Dict:
        """Create a comprehensive version negotiation response"""
        return {
            'negotiated_version': negotiation_result.get('version'),
            'request_info': request_info,
            'validation': negotiation_result,
            'content_type': self.generate_content_type_for_version(
                negotiation_result.get('version', '1.0.0')
            ),
            'documentation_url': f"/docs/api/v{negotiation_result.get('version', '1.0.0').split('.')[0]}",
            'supported_versions': [
                v.version for v in self.version_manager.get_supported_versions()
            ]
        }