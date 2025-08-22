"""
Client SDK Management System with Compatibility Matrices
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import yaml
from semantic_version import Version

from .models import ClientSDKInfo, APIVersion
from .manager import VersionManager
from .compatibility import CompatibilityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SDKCompatibilityMatrix:
    """SDK compatibility matrix for a language/platform"""
    language: str
    platform: str = "any"
    matrix: Dict[str, Dict[str, str]] = field(default_factory=dict)  # {sdk_version: {api_version: status}}
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def is_compatible(self, sdk_version: str, api_version: str) -> bool:
        """Check if SDK version is compatible with API version"""
        return self.matrix.get(sdk_version, {}).get(api_version) in ["compatible", "supported"]
    
    def get_compatibility_status(self, sdk_version: str, api_version: str) -> str:
        """Get compatibility status between SDK and API versions"""
        return self.matrix.get(sdk_version, {}).get(api_version, "unknown")


@dataclass
class SDKRelease:
    """SDK release information"""
    version: str
    release_date: datetime
    supported_api_versions: List[str]
    changelog: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)
    download_url: str = ""
    documentation_url: str = ""
    size_mb: float = 0.0
    dependencies: Dict[str, str] = field(default_factory=dict)
    
    @property
    def semantic_version(self) -> Version:
        """Get semantic version object"""
        return Version(self.version)


@dataclass
class SDKUpdateNotification:
    """SDK update notification"""
    sdk_name: str
    current_version: str
    latest_version: str
    update_type: str  # "patch", "minor", "major"
    urgency: str  # "low", "medium", "high", "critical"
    reason: str
    breaking_changes: bool = False
    auto_update_available: bool = False
    update_guide_url: Optional[str] = None


class SDKManager:
    """Manage client SDKs and compatibility matrices"""
    
    def __init__(
        self, 
        version_manager: VersionManager,
        compatibility_analyzer: CompatibilityAnalyzer,
        config_path: str = "config/sdk_config.json"
    ):
        self.version_manager = version_manager
        self.compatibility_analyzer = compatibility_analyzer
        self.config_path = config_path
        
        # SDK data
        self.sdks: Dict[str, ClientSDKInfo] = {}
        self.releases: Dict[str, List[SDKRelease]] = {}  # {sdk_name: [releases]}
        self.compatibility_matrices: Dict[str, SDKCompatibilityMatrix] = {}
        self.update_policies: Dict[str, Dict[str, Any]] = {}
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Load SDK configuration from file"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self._load_from_config(config)
                logger.info(f"Loaded SDK configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load SDK config: {e}")
                self._load_default_configuration()
        else:
            self._load_default_configuration()
    
    def _load_default_configuration(self):
        """Load default SDK configuration"""
        
        # Default SDK configurations
        default_sdks = [
            ClientSDKInfo(
                sdk_name="financial-planning-python",
                sdk_version="2.1.0",
                supported_api_versions=["1.0.0", "2.0.0"],
                min_api_version="1.0.0",
                max_api_version="2.0.0",
                language="python",
                release_date=datetime(2024, 6, 1),
                download_url="https://pypi.org/project/financial-planning-api/",
                documentation_url="https://financial-planning-python.readthedocs.io/",
                changelog_url="https://github.com/financial-planning/python-sdk/blob/main/CHANGELOG.md",
                auto_update_available=True
            ),
            ClientSDKInfo(
                sdk_name="financial-planning-js",
                sdk_version="1.5.2",
                supported_api_versions=["1.0.0"],
                min_api_version="1.0.0",
                max_api_version="1.0.0",
                language="javascript",
                release_date=datetime(2024, 5, 15),
                download_url="https://www.npmjs.com/package/@financial-planning/api-client",
                documentation_url="https://financial-planning-js.netlify.app/",
                changelog_url="https://github.com/financial-planning/js-sdk/blob/main/CHANGELOG.md",
                auto_update_available=True
            ),
            ClientSDKInfo(
                sdk_name="financial-planning-java",
                sdk_version="1.3.0",
                supported_api_versions=["1.0.0"],
                min_api_version="1.0.0",
                max_api_version="1.0.0",
                language="java",
                release_date=datetime(2024, 4, 20),
                download_url="https://mvnrepository.com/artifact/com.financial-planning/api-client",
                documentation_url="https://javadoc.financial-planning.com/",
                changelog_url="https://github.com/financial-planning/java-sdk/blob/main/CHANGELOG.md",
                auto_update_available=False
            )
        ]
        
        for sdk in default_sdks:
            self.sdks[f"{sdk.sdk_name}:{sdk.sdk_version}"] = sdk
        
        # Default compatibility matrices
        self._generate_default_compatibility_matrices()
        
        # Default update policies
        self.update_policies = {
            "python": {
                "auto_update_minor": True,
                "auto_update_patch": True,
                "notification_frequency_days": 7,
                "critical_update_notification": True
            },
            "javascript": {
                "auto_update_minor": False,
                "auto_update_patch": True,
                "notification_frequency_days": 14,
                "critical_update_notification": True
            },
            "java": {
                "auto_update_minor": False,
                "auto_update_patch": False,
                "notification_frequency_days": 30,
                "critical_update_notification": True
            }
        }
        
        logger.info("Loaded default SDK configuration")
    
    def _load_from_config(self, config: dict):
        """Load configuration from dictionary"""
        
        # Load SDKs
        if 'sdks' in config:
            for sdk_data in config['sdks']:
                sdk = ClientSDKInfo(**sdk_data)
                self.sdks[f"{sdk.sdk_name}:{sdk.sdk_version}"] = sdk
        
        # Load compatibility matrices
        if 'compatibility_matrices' in config:
            for matrix_data in config['compatibility_matrices']:
                matrix = SDKCompatibilityMatrix(**matrix_data)
                self.compatibility_matrices[matrix.language] = matrix
        
        # Load update policies
        if 'update_policies' in config:
            self.update_policies = config['update_policies']
    
    def _generate_default_compatibility_matrices(self):
        """Generate default compatibility matrices"""
        
        languages = ["python", "javascript", "java"]
        api_versions = [v.version for v in self.version_manager.get_all_versions()]
        
        for language in languages:
            matrix = SDKCompatibilityMatrix(language=language)
            
            # Find SDKs for this language
            language_sdks = [
                sdk for sdk in self.sdks.values() 
                if sdk.language == language
            ]
            
            for sdk in language_sdks:
                matrix.matrix[sdk.sdk_version] = {}
                
                for api_version in api_versions:
                    if api_version in sdk.supported_api_versions:
                        matrix.matrix[sdk.sdk_version][api_version] = "supported"
                    else:
                        # Check compatibility based on version proximity
                        try:
                            api_sem = Version(api_version)
                            supported_versions = [Version(v) for v in sdk.supported_api_versions]
                            
                            # Check if any supported version has same major version
                            compatible = any(
                                sv.major == api_sem.major for sv in supported_versions
                            )
                            
                            matrix.matrix[sdk.sdk_version][api_version] = (
                                "compatible" if compatible else "incompatible"
                            )
                        except ValueError:
                            matrix.matrix[sdk.sdk_version][api_version] = "unknown"
            
            self.compatibility_matrices[language] = matrix
    
    def add_sdk(self, sdk: ClientSDKInfo) -> bool:
        """Add a new SDK"""
        sdk_key = f"{sdk.sdk_name}:{sdk.sdk_version}"
        
        if sdk_key in self.sdks:
            logger.warning(f"SDK {sdk_key} already exists")
            return False
        
        self.sdks[sdk_key] = sdk
        self.version_manager.add_client_sdk(sdk)
        
        # Update compatibility matrix
        self._update_compatibility_matrix(sdk)
        
        logger.info(f"Added SDK: {sdk_key}")
        return True
    
    def _update_compatibility_matrix(self, sdk: ClientSDKInfo):
        """Update compatibility matrix for SDK"""
        
        if sdk.language not in self.compatibility_matrices:
            self.compatibility_matrices[sdk.language] = SDKCompatibilityMatrix(
                language=sdk.language
            )
        
        matrix = self.compatibility_matrices[sdk.language]
        matrix.matrix[sdk.sdk_version] = {}
        
        api_versions = [v.version for v in self.version_manager.get_all_versions()]
        
        for api_version in api_versions:
            if api_version in sdk.supported_api_versions:
                matrix.matrix[sdk.sdk_version][api_version] = "supported"
            else:
                # Analyze compatibility
                status = self._analyze_sdk_api_compatibility(sdk, api_version)
                matrix.matrix[sdk.sdk_version][api_version] = status
        
        matrix.last_updated = datetime.utcnow()
    
    def _analyze_sdk_api_compatibility(self, sdk: ClientSDKInfo, api_version: str) -> str:
        """Analyze compatibility between SDK and API version"""
        
        try:
            api_sem = Version(api_version)
            
            # Find closest supported API version
            supported_versions = [Version(v) for v in sdk.supported_api_versions]
            
            if not supported_versions:
                return "unknown"
            
            # Find the closest version
            closest_version = min(
                supported_versions,
                key=lambda v: abs(v.major - api_sem.major) + abs(v.minor - api_sem.minor)
            )
            
            # Determine compatibility
            if closest_version.major == api_sem.major:
                if closest_version >= api_sem:
                    return "compatible"
                else:
                    # Check if API version has breaking changes
                    api_version_obj = self.version_manager.get_version(api_version)
                    if api_version_obj and api_version_obj.breaking_changes:
                        return "needs_update"
                    return "compatible"
            else:
                return "incompatible"
                
        except ValueError:
            return "unknown"
    
    def get_sdk_for_language(self, language: str, api_version: Optional[str] = None) -> Optional[ClientSDKInfo]:
        """Get the best SDK for a language and API version"""
        
        language_sdks = [
            sdk for sdk in self.sdks.values()
            if sdk.language == language
        ]
        
        if not language_sdks:
            return None
        
        if api_version:
            # Find SDKs that support this API version
            compatible_sdks = [
                sdk for sdk in language_sdks
                if sdk.supports_version(api_version)
            ]
            
            if compatible_sdks:
                # Return the latest SDK version
                return max(compatible_sdks, key=lambda s: Version(s.sdk_version))
        
        # Return the latest SDK for the language
        return max(language_sdks, key=lambda s: Version(s.sdk_version))
    
    def get_compatibility_matrix(self, language: str) -> Optional[SDKCompatibilityMatrix]:
        """Get compatibility matrix for a language"""
        return self.compatibility_matrices.get(language)
    
    def check_sdk_compatibility(self, sdk_name: str, sdk_version: str, api_version: str) -> Dict[str, Any]:
        """Check compatibility between specific SDK and API versions"""
        
        sdk_key = f"{sdk_name}:{sdk_version}"
        sdk = self.sdks.get(sdk_key)
        
        if not sdk:
            return {
                'compatible': False,
                'status': 'sdk_not_found',
                'message': f'SDK {sdk_name} version {sdk_version} not found'
            }
        
        # Check direct support
        if sdk.supports_version(api_version):
            return {
                'compatible': True,
                'status': 'supported',
                'message': f'SDK {sdk_name} v{sdk_version} supports API v{api_version}'
            }
        
        # Check compatibility matrix
        matrix = self.compatibility_matrices.get(sdk.language)
        if matrix:
            status = matrix.get_compatibility_status(sdk_version, api_version)
            
            return {
                'compatible': status in ['compatible', 'supported'],
                'status': status,
                'message': self._get_compatibility_message(status, sdk, api_version),
                'recommendations': self._get_compatibility_recommendations(sdk, api_version)
            }
        
        return {
            'compatible': False,
            'status': 'unknown',
            'message': 'Compatibility information not available'
        }
    
    def _get_compatibility_message(self, status: str, sdk: ClientSDKInfo, api_version: str) -> str:
        """Get human-readable compatibility message"""
        
        messages = {
            'supported': f'SDK {sdk.sdk_name} v{sdk.sdk_version} fully supports API v{api_version}',
            'compatible': f'SDK {sdk.sdk_name} v{sdk.sdk_version} is compatible with API v{api_version}',
            'needs_update': f'SDK {sdk.sdk_name} v{sdk.sdk_version} needs update for API v{api_version}',
            'incompatible': f'SDK {sdk.sdk_name} v{sdk.sdk_version} is not compatible with API v{api_version}',
            'unknown': f'Compatibility between SDK {sdk.sdk_name} v{sdk.sdk_version} and API v{api_version} is unknown'
        }
        
        return messages.get(status, f'Status: {status}')
    
    def _get_compatibility_recommendations(self, sdk: ClientSDKInfo, api_version: str) -> List[str]:
        """Get recommendations for compatibility issues"""
        
        recommendations = []
        
        # Find newer SDK versions that support the API version
        newer_sdks = [
            s for s in self.sdks.values()
            if (s.sdk_name == sdk.sdk_name and 
                Version(s.sdk_version) > Version(sdk.sdk_version) and
                s.supports_version(api_version))
        ]
        
        if newer_sdks:
            latest_sdk = max(newer_sdks, key=lambda s: Version(s.sdk_version))
            recommendations.append(
                f'Upgrade to {sdk.sdk_name} v{latest_sdk.sdk_version} for full API v{api_version} support'
            )
        
        # Check for alternative API versions
        supported_api_versions = [v for v in sdk.supported_api_versions]
        if supported_api_versions:
            latest_supported = max(supported_api_versions, key=Version)
            if latest_supported != api_version:
                recommendations.append(
                    f'Consider using API v{latest_supported} which is fully supported'
                )
        
        return recommendations
    
    def get_update_notifications(self, language: str, current_version: str) -> List[SDKUpdateNotification]:
        """Get update notifications for an SDK"""
        
        notifications = []
        
        # Find current SDK
        current_sdk = None
        for sdk in self.sdks.values():
            if sdk.language == language and sdk.sdk_version == current_version:
                current_sdk = sdk
                break
        
        if not current_sdk:
            return notifications
        
        # Find newer versions
        newer_sdks = [
            sdk for sdk in self.sdks.values()
            if (sdk.sdk_name == current_sdk.sdk_name and 
                Version(sdk.sdk_version) > Version(current_version))
        ]
        
        if not newer_sdks:
            return notifications
        
        latest_sdk = max(newer_sdks, key=lambda s: Version(s.sdk_version))
        
        # Determine update type
        current_sem = Version(current_version)
        latest_sem = Version(latest_sdk.sdk_version)
        
        if latest_sem.major > current_sem.major:
            update_type = "major"
            urgency = "medium"
        elif latest_sem.minor > current_sem.minor:
            update_type = "minor"
            urgency = "low"
        else:
            update_type = "patch"
            urgency = "low"
        
        # Check for security updates or critical fixes
        if any("security" in fix.lower() or "critical" in fix.lower() 
               for fix in getattr(latest_sdk, 'bug_fixes', [])):
            urgency = "critical"
        
        notification = SDKUpdateNotification(
            sdk_name=current_sdk.sdk_name,
            current_version=current_version,
            latest_version=latest_sdk.sdk_version,
            update_type=update_type,
            urgency=urgency,
            reason=f"New {update_type} version available with improvements",
            auto_update_available=latest_sdk.auto_update_available,
            update_guide_url=f"{latest_sdk.documentation_url}/migration"
        )
        
        notifications.append(notification)
        
        return notifications
    
    def generate_sdk_compatibility_report(self) -> Dict[str, Any]:
        """Generate comprehensive SDK compatibility report"""
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'api_versions': [v.version for v in self.version_manager.get_supported_versions()],
            'languages': {},
            'summary': {
                'total_sdks': len(self.sdks),
                'languages_supported': len(set(sdk.language for sdk in self.sdks.values())),
                'compatibility_coverage': 0.0
            }
        }
        
        # Analyze by language
        for language in set(sdk.language for sdk in self.sdks.values()):
            language_sdks = [sdk for sdk in self.sdks.values() if sdk.language == language]
            matrix = self.compatibility_matrices.get(language)
            
            language_report = {
                'sdks': [],
                'latest_version': None,
                'api_coverage': {},
                'recommendations': []
            }
            
            # Find latest SDK
            if language_sdks:
                latest_sdk = max(language_sdks, key=lambda s: Version(s.sdk_version))
                language_report['latest_version'] = latest_sdk.sdk_version
            
            # Analyze each SDK
            for sdk in language_sdks:
                sdk_report = {
                    'version': sdk.sdk_version,
                    'release_date': sdk.release_date.isoformat(),
                    'supported_api_versions': sdk.supported_api_versions,
                    'compatibility': {},
                    'needs_update': False
                }
                
                # Check compatibility with all API versions
                if matrix:
                    for api_version in report['api_versions']:
                        status = matrix.get_compatibility_status(sdk.sdk_version, api_version)
                        sdk_report['compatibility'][api_version] = status
                        
                        if status in ['needs_update', 'incompatible']:
                            sdk_report['needs_update'] = True
                
                language_report['sdks'].append(sdk_report)
            
            # Calculate API coverage
            if matrix:
                for api_version in report['api_versions']:
                    supported_sdks = sum(
                        1 for sdk_version in matrix.matrix
                        if matrix.matrix[sdk_version].get(api_version) in ['supported', 'compatible']
                    )
                    coverage = supported_sdks / len(language_sdks) if language_sdks else 0
                    language_report['api_coverage'][api_version] = coverage
            
            # Add recommendations
            if language_sdks:
                avg_coverage = sum(language_report['api_coverage'].values()) / len(language_report['api_coverage']) if language_report['api_coverage'] else 0
                
                if avg_coverage < 0.8:
                    language_report['recommendations'].append('Update SDKs to improve API version coverage')
                
                outdated_sdks = [
                    sdk for sdk in language_sdks
                    if (datetime.utcnow() - sdk.release_date).days > 180
                ]
                
                if outdated_sdks:
                    language_report['recommendations'].append(f'{len(outdated_sdks)} SDKs are more than 6 months old')
            
            report['languages'][language] = language_report
        
        # Calculate overall compatibility coverage
        total_compatibility_checks = 0
        successful_checks = 0
        
        for language_data in report['languages'].values():
            for sdk_data in language_data['sdks']:
                for api_version, status in sdk_data['compatibility'].items():
                    total_compatibility_checks += 1
                    if status in ['supported', 'compatible']:
                        successful_checks += 1
        
        if total_compatibility_checks > 0:
            report['summary']['compatibility_coverage'] = successful_checks / total_compatibility_checks
        
        return report
    
    def generate_sdk_recommendations(self, language: str, api_version: str) -> Dict[str, Any]:
        """Generate SDK recommendations for specific language and API version"""
        
        recommendations = {
            'language': language,
            'api_version': api_version,
            'recommended_sdk': None,
            'alternatives': [],
            'upgrade_path': [],
            'considerations': []
        }
        
        # Find best SDK for this combination
        best_sdk = self.get_sdk_for_language(language, api_version)
        
        if best_sdk:
            compatibility = self.check_sdk_compatibility(
                best_sdk.sdk_name, best_sdk.sdk_version, api_version
            )
            
            recommendations['recommended_sdk'] = {
                'name': best_sdk.sdk_name,
                'version': best_sdk.sdk_version,
                'compatibility_status': compatibility['status'],
                'download_url': best_sdk.download_url,
                'documentation_url': best_sdk.documentation_url,
                'auto_update_available': best_sdk.auto_update_available
            }
        
        # Find alternative SDKs
        language_sdks = [sdk for sdk in self.sdks.values() if sdk.language == language]
        
        for sdk in language_sdks:
            if sdk == best_sdk:
                continue
            
            compatibility = self.check_sdk_compatibility(
                sdk.sdk_name, sdk.sdk_version, api_version
            )
            
            if compatibility['compatible']:
                recommendations['alternatives'].append({
                    'name': sdk.sdk_name,
                    'version': sdk.sdk_version,
                    'compatibility_status': compatibility['status'],
                    'pros': self._get_sdk_pros(sdk),
                    'cons': self._get_sdk_cons(sdk)
                })
        
        # Generate upgrade path
        if best_sdk:
            older_versions = [
                sdk for sdk in language_sdks
                if (sdk.sdk_name == best_sdk.sdk_name and 
                    Version(sdk.sdk_version) < Version(best_sdk.sdk_version))
            ]
            
            if older_versions:
                sorted_versions = sorted(older_versions, key=lambda s: Version(s.sdk_version))
                recommendations['upgrade_path'] = [
                    {
                        'version': sdk.sdk_version,
                        'release_date': sdk.release_date.isoformat(),
                        'breaking_changes': getattr(sdk, 'breaking_changes', [])
                    }
                    for sdk in sorted_versions
                ]
        
        # Add considerations
        matrix = self.compatibility_matrices.get(language)
        if matrix:
            api_coverage = sum(
                1 for sdk_version in matrix.matrix
                for api_v, status in matrix.matrix[sdk_version].items()
                if status in ['supported', 'compatible']
            )
            total_combinations = sum(len(api_statuses) for api_statuses in matrix.matrix.values())
            
            if total_combinations > 0:
                coverage_ratio = api_coverage / total_combinations
                if coverage_ratio < 0.7:
                    recommendations['considerations'].append(
                        f'Limited API version coverage for {language} SDKs ({coverage_ratio:.1%})'
                    )
        
        update_policy = self.update_policies.get(language, {})
        if not update_policy.get('auto_update_minor', False):
            recommendations['considerations'].append('Manual updates required for minor versions')
        
        return recommendations
    
    def _get_sdk_pros(self, sdk: ClientSDKInfo) -> List[str]:
        """Get pros for an SDK"""
        pros = []
        
        if sdk.auto_update_available:
            pros.append('Auto-update available')
        
        if len(sdk.supported_api_versions) > 1:
            pros.append('Supports multiple API versions')
        
        if (datetime.utcnow() - sdk.release_date).days < 90:
            pros.append('Recently updated')
        
        return pros
    
    def _get_sdk_cons(self, sdk: ClientSDKInfo) -> List[str]:
        """Get cons for an SDK"""
        cons = []
        
        if not sdk.auto_update_available:
            cons.append('Manual updates required')
        
        if (datetime.utcnow() - sdk.release_date).days > 180:
            cons.append('Not recently updated')
        
        if len(sdk.supported_api_versions) == 1:
            cons.append('Limited API version support')
        
        return cons
    
    def export_compatibility_matrices(self, output_dir: str = "docs/sdk") -> Dict[str, str]:
        """Export compatibility matrices to files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        for language, matrix in self.compatibility_matrices.items():
            # Export as JSON
            json_file = output_path / f"{language}_compatibility.json"
            with open(json_file, 'w') as f:
                json.dump({
                    'language': matrix.language,
                    'platform': matrix.platform,
                    'last_updated': matrix.last_updated.isoformat(),
                    'matrix': matrix.matrix
                }, f, indent=2)
            
            exported_files[f"{language}_json"] = str(json_file)
            
            # Export as Markdown table
            md_file = output_path / f"{language}_compatibility.md"
            md_content = self._generate_compatibility_markdown(matrix)
            md_file.write_text(md_content)
            
            exported_files[f"{language}_markdown"] = str(md_file)
        
        # Export summary
        summary = self.generate_sdk_compatibility_report()
        summary_file = output_path / "compatibility_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        exported_files["summary"] = str(summary_file)
        
        logger.info(f"Exported SDK compatibility matrices to {output_path}")
        return exported_files
    
    def _generate_compatibility_markdown(self, matrix: SDKCompatibilityMatrix) -> str:
        """Generate Markdown compatibility table"""
        
        if not matrix.matrix:
            return f"# {matrix.language.title()} SDK Compatibility\n\nNo compatibility data available.\n"
        
        # Get all API versions
        all_api_versions = set()
        for sdk_versions in matrix.matrix.values():
            all_api_versions.update(sdk_versions.keys())
        
        sorted_api_versions = sorted(all_api_versions, key=Version)
        sorted_sdk_versions = sorted(matrix.matrix.keys(), key=Version)
        
        # Generate table
        md_content = f"""# {matrix.language.title()} SDK Compatibility Matrix

Last updated: {matrix.last_updated.strftime('%Y-%m-%d %H:%M:%S')}

## Compatibility Legend
- ✅ **Supported**: Full support with all features
- 🟡 **Compatible**: Works with potential minor issues
- ❌ **Incompatible**: Not compatible, update required
- ❓ **Unknown**: Compatibility not tested
- 🔄 **Needs Update**: SDK update required for full support

## Compatibility Table

| SDK Version | {' | '.join(f'API v{v}' for v in sorted_api_versions)} |
|-------------|{'-|' * len(sorted_api_versions)}
"""
        
        status_symbols = {
            'supported': '✅',
            'compatible': '🟡', 
            'incompatible': '❌',
            'unknown': '❓',
            'needs_update': '🔄'
        }
        
        for sdk_version in sorted_sdk_versions:
            row = [f"v{sdk_version}"]
            
            for api_version in sorted_api_versions:
                status = matrix.matrix[sdk_version].get(api_version, 'unknown')
                symbol = status_symbols.get(status, '❓')
                row.append(f"{symbol}")
            
            md_content += f"| {' | '.join(row)} |\n"
        
        md_content += f"""
## Recommendations

### For New Projects
- Use the latest SDK version that supports your target API version
- Check for auto-update capabilities
- Verify documentation and support quality

### For Existing Projects
- Update SDKs showing 🔄 (needs update) status
- Plan migration for ❌ (incompatible) combinations
- Monitor for security updates

## SDK Information

"""
        
        # Add SDK details
        language_sdks = [sdk for sdk in self.sdks.values() if sdk.language == matrix.language]
        for sdk in sorted(language_sdks, key=lambda s: Version(s.sdk_version), reverse=True):
            md_content += f"""### {sdk.sdk_name} v{sdk.sdk_version}
- **Release Date**: {sdk.release_date.strftime('%Y-%m-%d')}
- **Download**: {sdk.download_url}
- **Documentation**: {sdk.documentation_url}
- **Auto-update**: {'Yes' if sdk.auto_update_available else 'No'}
- **Supported API Versions**: {', '.join(f'v{v}' for v in sdk.supported_api_versions)}

"""
        
        return md_content