"""
Version-Specific Documentation Management System
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

from .models import APIVersion, VersionedEndpoint
from .manager import VersionManager
from .compatibility import CompatibilityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class DocumentationSection:
    """Documentation section configuration"""
    title: str
    content: str
    order: int = 0
    template: Optional[str] = None
    auto_generated: bool = False
    last_updated: Optional[datetime] = None


@dataclass
class APIDocumentation:
    """Complete API documentation for a version"""
    version: str
    title: str
    description: str
    base_url: str
    sections: List[DocumentationSection] = field(default_factory=list)
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    schemas: Dict[str, Any] = field(default_factory=dict)
    examples: Dict[str, Any] = field(default_factory=dict)
    migration_guides: List[Dict[str, str]] = field(default_factory=list)
    changelog: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'version': self.version,
            'title': self.title, 
            'description': self.description,
            'base_url': self.base_url,
            'sections': [
                {
                    'title': section.title,
                    'content': section.content,
                    'order': section.order,
                    'auto_generated': section.auto_generated,
                    'last_updated': section.last_updated.isoformat() if section.last_updated else None
                }
                for section in self.sections
            ],
            'endpoints': self.endpoints,
            'schemas': self.schemas,
            'examples': self.examples,
            'migration_guides': self.migration_guides,
            'changelog': self.changelog
        }


class DocumentationGenerator:
    """Generate version-specific documentation"""
    
    def __init__(
        self, 
        version_manager: VersionManager,
        compatibility_analyzer: CompatibilityAnalyzer,
        template_dir: str = "app/api/versioning/templates"
    ):
        self.version_manager = version_manager
        self.compatibility_analyzer = compatibility_analyzer
        self.template_dir = Path(template_dir)
        self.output_dir = Path("docs/api")
        
        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Ensure directories exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default documentation templates"""
        templates = {
            "version_overview.md": '''# API Version {{ version }}

{{ description }}

## Status
- **Current Status**: {{ status }}
- **Release Date**: {{ release_date }}
{% if deprecation_date %}
- **Deprecation Date**: {{ deprecation_date }}
{% endif %}
{% if retirement_date %}
- **Retirement Date**: {{ retirement_date }}
{% endif %}

## Base URL
```
{{ base_url }}
```

## Authentication
All requests must include the API version in headers:
```
X-API-Version: {{ version }}
```

## Rate Limiting
- {{ rate_limits.requests_per_minute }} requests per minute
- {{ rate_limits.requests_per_hour }} requests per hour

{% if breaking_changes %}
## Breaking Changes
{% for change in breaking_changes %}
- {{ change }}
{% endfor %}
{% endif %}

{% if new_features %}
## New Features
{% for feature in new_features %}
- {{ feature }}
{% endfor %}
{% endif %}
''',

            "endpoint_documentation.md": '''# {{ method }} {{ path }}

{{ description }}

{% if deprecated %}
> **⚠️ Deprecated**: This endpoint is deprecated as of version {{ deprecated_in }}.
{% if replacement %}Use `{{ replacement }}` instead.{% endif %}
{% endif %}

## Request

### Headers
```
X-API-Version: {{ version }}
Content-Type: application/json
Authorization: Bearer <token>
```

{% if parameters %}
### Parameters
{% for param in parameters %}
- **{{ param.name }}** ({{ param.type }}){% if param.required %} *required*{% endif %}: {{ param.description }}
{% endfor %}
{% endif %}

{% if request_body %}
### Request Body
```json
{{ request_body | tojson(indent=2) }}
```
{% endif %}

## Response

### Success Response ({{ success_status }})
```json
{{ success_response | tojson(indent=2) }}
```

{% if error_responses %}
### Error Responses
{% for error in error_responses %}
#### {{ error.status }} - {{ error.title }}
```json
{{ error.example | tojson(indent=2) }}
```
{% endfor %}
{% endif %}

## Examples

### cURL
```bash
curl -X {{ method }} "{{ base_url }}{{ path }}" \\
  -H "X-API-Version: {{ version }}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN"{% if request_body %} \\
  -d '{{ request_body | tojson }}'{% endif %}
```

### Python
```python
import requests

headers = {
    'X-API-Version': '{{ version }}',
    'Authorization': 'Bearer YOUR_TOKEN'
}

{% if request_body %}
data = {{ request_body | tojson(indent=4) }}
response = requests.{{ method.lower() }}('{{ base_url }}{{ path }}', headers=headers, json=data)
{% else %}
response = requests.{{ method.lower() }}('{{ base_url }}{{ path }}', headers=headers)
{% endif %}
print(response.json())
```

### JavaScript
```javascript
const response = await fetch('{{ base_url }}{{ path }}', {
  method: '{{ method }}',
  headers: {
    'X-API-Version': '{{ version }}',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  }{% if request_body %},
  body: JSON.stringify({{ request_body | tojson }}){% endif %}
});

const data = await response.json();
console.log(data);
```
''',

            "migration_guide.md": '''# Migration Guide: v{{ from_version }} → v{{ to_version }}

This guide helps you migrate from API version {{ from_version }} to {{ to_version }}.

## Overview
- **Compatibility Level**: {{ compatibility_level }}
- **Migration Required**: {{ "Yes" if migration_required else "No" }}
- **Estimated Effort**: {{ estimated_effort }}

## Summary of Changes

### Breaking Changes
{% for issue in breaking_issues %}
- **{{ issue.component }}**: {{ issue.description }}
{% endfor %}

### New Features
{% for feature in new_features %}
- {{ feature }}
{% endfor %}

### Deprecated Features
{% for issue in deprecated_issues %}
- **{{ issue.component }}**: {{ issue.description }}
  {% if issue.workaround %}*Workaround*: {{ issue.workaround }}{% endif %}
{% endfor %}

## Step-by-Step Migration

{% for step in migration_steps %}
### Step {{ step.step }}: {{ step.title }}
{{ step.description }}

**Actions:**
{% for action in step.actions %}
- {{ action }}
{% endfor %}

**Validation:** {{ step.validation }}

{% endfor %}

## Testing
After migration, test these areas:
- Authentication and authorization
- All endpoints you use
- Error handling
- Request/response formats

## Need Help?
- [API Documentation]({{ docs_url }})
- [Support Forum]({{ support_url }})
- [Contact Support]({{ contact_url }})
''',

            "changelog.md": '''# API Changelog

## Version {{ version }} ({{ release_date }})

### Status: {{ status }}

{{ description }}

{% if breaking_changes %}
### 🚨 Breaking Changes
{% for change in breaking_changes %}
- {{ change }}
{% endfor %}
{% endif %}

{% if new_features %}
### ✨ New Features
{% for feature in new_features %}
- {{ feature }}
{% endfor %}
{% endif %}

{% if bug_fixes %}
### 🐛 Bug Fixes
{% for fix in bug_fixes %}
- {{ fix }}
{% endfor %}
{% endif %}

{% if deprecations %}
### ⚠️ Deprecations
{% for deprecation in deprecations %}
- {{ deprecation }}
{% endfor %}
{% endif %}

{% if migration_notes %}
### 📝 Migration Notes
{% for note in migration_notes %}
- {{ note }}
{% endfor %}
{% endif %}
'''
        }
        
        for template_name, content in templates.items():
            template_path = self.template_dir / template_name
            if not template_path.exists():
                template_path.write_text(content)
                logger.info(f"Created template: {template_path}")
    
    def generate_version_documentation(self, version: str) -> APIDocumentation:
        """Generate complete documentation for a version"""
        
        version_obj = self.version_manager.get_version(version)
        if not version_obj:
            raise ValueError(f"Version {version} not found")
        
        # Create documentation object
        docs = APIDocumentation(
            version=version,
            title=f"Financial Planning API v{version}",
            description=version_obj.description,
            base_url=f"https://api.financial-planning.com/api/v{version.split('.')[0]}"
        )
        
        # Generate overview section
        overview_section = self._generate_overview_section(version_obj)
        docs.sections.append(overview_section)
        
        # Generate endpoint documentation
        endpoints = self.version_manager.get_endpoints_for_version(version)
        docs.endpoints = self._generate_endpoint_docs(endpoints, version)
        
        # Generate authentication section
        auth_section = self._generate_auth_section(version)
        docs.sections.append(auth_section)
        
        # Generate error handling section
        error_section = self._generate_error_section(version)
        docs.sections.append(error_section)
        
        # Generate examples section
        docs.examples = self._generate_examples(version)
        
        # Generate migration guides
        docs.migration_guides = self._generate_migration_guides(version)
        
        # Generate changelog
        docs.changelog = self._generate_changelog(version_obj)
        
        return docs
    
    def _generate_overview_section(self, version_obj: APIVersion) -> DocumentationSection:
        """Generate overview section for a version"""
        
        template = self.jinja_env.get_template("version_overview.md")
        
        content = template.render(
            version=version_obj.version,
            description=version_obj.description,
            status=version_obj.status.value,
            release_date=version_obj.release_date.strftime("%Y-%m-%d") if version_obj.release_date else "TBD",
            deprecation_date=version_obj.deprecation_date.strftime("%Y-%m-%d") if version_obj.deprecation_date else None,
            retirement_date=version_obj.retirement_date.strftime("%Y-%m-%d") if version_obj.retirement_date else None,
            base_url=f"https://api.financial-planning.com/api/v{version_obj.version.split('.')[0]}",
            breaking_changes=version_obj.breaking_changes,
            new_features=version_obj.new_features,
            rate_limits={
                "requests_per_minute": 1000,
                "requests_per_hour": 10000
            }
        )
        
        return DocumentationSection(
            title="Overview",
            content=content,
            order=1,
            auto_generated=True,
            last_updated=datetime.utcnow()
        )
    
    def _generate_endpoint_docs(self, endpoints: List[VersionedEndpoint], version: str) -> List[Dict[str, Any]]:
        """Generate endpoint documentation"""
        
        endpoint_docs = []
        template = self.jinja_env.get_template("endpoint_documentation.md")
        
        # Sample endpoint data (in real implementation, this would come from OpenAPI specs)
        sample_endpoints = [
            {
                "path": "/auth/login",
                "method": "POST",
                "description": "Authenticate user and obtain access token",
                "parameters": [
                    {"name": "username", "type": "string", "required": True, "description": "User's email or username"},
                    {"name": "password", "type": "string", "required": True, "description": "User's password"}
                ],
                "request_body": {
                    "username": "user@example.com",
                    "password": "password123"
                },
                "success_status": 200,
                "success_response": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "expires_in": 3600,
                    "token_type": "Bearer"
                },
                "error_responses": [
                    {
                        "status": 401,
                        "title": "Unauthorized",
                        "example": {
                            "error": "invalid_credentials",
                            "message": "Invalid username or password"
                        }
                    }
                ]
            },
            {
                "path": "/users/profile",
                "method": "GET",
                "description": "Get current user's profile information",
                "parameters": [],
                "success_status": 200,
                "success_response": {
                    "id": 12345,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "error_responses": [
                    {
                        "status": 401,
                        "title": "Unauthorized",
                        "example": {
                            "error": "token_invalid",
                            "message": "Access token is invalid or expired"
                        }
                    }
                ]
            }
        ]
        
        for endpoint_data in sample_endpoints:
            # Check if endpoint exists in this version
            endpoint_exists = any(
                ep.path == endpoint_data["path"] and endpoint_data["method"] in ep.methods
                for ep in endpoints
            )
            
            if endpoint_exists:
                # Find matching endpoint for deprecation info
                matching_endpoint = next(
                    (ep for ep in endpoints 
                     if ep.path == endpoint_data["path"] and endpoint_data["method"] in ep.methods),
                    None
                )
                
                doc_content = template.render(
                    **endpoint_data,
                    version=version,
                    base_url=f"https://api.financial-planning.com/api/v{version.split('.')[0]}",
                    deprecated=matching_endpoint.is_deprecated_in_version(version) if matching_endpoint else False,
                    deprecated_in=matching_endpoint.deprecated_in if matching_endpoint else None,
                    replacement=None  # Would be populated from endpoint metadata
                )
                
                endpoint_docs.append({
                    "path": endpoint_data["path"],
                    "method": endpoint_data["method"],
                    "title": endpoint_data["description"],
                    "content": doc_content,
                    "deprecated": matching_endpoint.is_deprecated_in_version(version) if matching_endpoint else False
                })
        
        return endpoint_docs
    
    def _generate_auth_section(self, version: str) -> DocumentationSection:
        """Generate authentication documentation section"""
        
        content = f"""# Authentication

The Financial Planning API uses Bearer token authentication. All requests must include your API key in the Authorization header.

## Getting an Access Token

### 1. Login Request
```http
POST /api/v{version.split('.')[0]}/auth/login
Content-Type: application/json
X-API-Version: {version}

{{
  "username": "your-email@example.com",
  "password": "your-password"
}}
```

### 2. Response
```json
{{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}}
```

## Using the Access Token

Include the access token in the Authorization header of all subsequent requests:

```http
GET /api/v{version.split('.')[0]}/users/profile
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
X-API-Version: {version}
```

## Token Refresh

Access tokens expire after 1 hour. Use the refresh token to get a new access token:

```http
POST /api/v{version.split('.')[0]}/auth/refresh
Content-Type: application/json
X-API-Version: {version}

{{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}}
```

## Security Best Practices

- Store tokens securely (not in localStorage)
- Use HTTPS for all requests
- Implement proper token rotation
- Handle token expiration gracefully
"""
        
        return DocumentationSection(
            title="Authentication",
            content=content,
            order=2,
            auto_generated=True,
            last_updated=datetime.utcnow()
        )
    
    def _generate_error_section(self, version: str) -> DocumentationSection:
        """Generate error handling documentation section"""
        
        content = f"""# Error Handling

The API uses conventional HTTP response codes to indicate success or failure of requests.

## HTTP Status Codes

- `200` - OK: Request succeeded
- `201` - Created: Resource created successfully
- `400` - Bad Request: Invalid request parameters
- `401` - Unauthorized: Authentication required or failed
- `403` - Forbidden: Access denied
- `404` - Not Found: Resource not found
- `422` - Unprocessable Entity: Validation errors
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server error

## Error Response Format

All errors return a consistent JSON structure:

```json
{{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {{
    "field": "Specific field error details"
  }},
  "request_id": "uuid-for-support",
  "timestamp": "2024-01-15T10:30:00Z"
}}
```

## Common Error Codes

### Authentication Errors
- `invalid_credentials` - Username/password incorrect
- `token_expired` - Access token has expired
- `token_invalid` - Access token is malformed or invalid

### Validation Errors
- `validation_failed` - Request data validation failed
- `required_field_missing` - Required field not provided
- `invalid_field_format` - Field format is incorrect

### Rate Limiting
- `rate_limit_exceeded` - Too many requests, retry after delay

## Version-Specific Errors

When using deprecated endpoints in version {version}:
- `endpoint_deprecated` - Endpoint is deprecated
- `version_not_supported` - API version not supported

## Error Handling Examples

### Python
```python
import requests

try:
    response = requests.get(
        f"https://api.financial-planning.com/api/v{version.split('.')[0]}/users/profile",
        headers={{"Authorization": "Bearer token", "X-API-Version": "{version}"}}
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f"API Error: {{error_data['error']}} - {{error_data['message']}}")
```

### JavaScript
```javascript
try {{
  const response = await fetch('/api/v{version.split('.')[0]}/users/profile', {{
    headers: {{
      'Authorization': 'Bearer token',
      'X-API-Version': '{version}'
    }}
  }});
  
  if (!response.ok) {{
    const error = await response.json();
    throw new Error(`${{error.error}}: ${{error.message}}`);
  }}
  
  const data = await response.json();
}} catch (error) {{
  console.error('API Error:', error.message);
}}
```
"""
        
        return DocumentationSection(
            title="Error Handling",
            content=content,
            order=3,
            auto_generated=True,
            last_updated=datetime.utcnow()
        )
    
    def _generate_examples(self, version: str) -> Dict[str, Any]:
        """Generate code examples for the version"""
        
        base_url = f"https://api.financial-planning.com/api/v{version.split('.')[0]}"
        
        examples = {
            "quick_start": {
                "title": "Quick Start Guide",
                "description": "Get started with the API in 5 minutes",
                "steps": [
                    {
                        "step": 1,
                        "title": "Authenticate",
                        "code": f"""
# Login to get access token
curl -X POST "{base_url}/auth/login" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Version: {version}" \\
  -d '{{"username": "your-email@example.com", "password": "your-password"}}'
"""
                    },
                    {
                        "step": 2,
                        "title": "Get Profile",
                        "code": f"""
# Get user profile
curl -X GET "{base_url}/users/profile" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "X-API-Version: {version}"
"""
                    },
                    {
                        "step": 3,
                        "title": "Create Goal",
                        "code": f"""
# Create a financial goal
curl -X POST "{base_url}/goals" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Version: {version}" \\
  -d '{{
    "name": "Emergency Fund",
    "target_amount": 10000,
    "target_date": "2025-12-31",
    "priority": "high"
  }}'
"""
                    }
                ]
            },
            "sdk_examples": {
                "python": f"""
import requests

class FinancialPlanningAPI:
    def __init__(self, base_url="{base_url}", version="{version}"):
        self.base_url = base_url
        self.version = version
        self.token = None
    
    def login(self, username, password):
        response = requests.post(
            f"{{self.base_url}}/auth/login",
            json={{"username": username, "password": password}},
            headers={{"X-API-Version": self.version}}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token
    
    def get_profile(self):
        response = requests.get(
            f"{{self.base_url}}/users/profile",
            headers={{
                "Authorization": f"Bearer {{self.token}}",
                "X-API-Version": self.version
            }}
        )
        response.raise_for_status()
        return response.json()

# Usage
api = FinancialPlanningAPI()
api.login("user@example.com", "password")
profile = api.get_profile()
print(profile)
""",
                "javascript": f"""
class FinancialPlanningAPI {{
  constructor(baseUrl = "{base_url}", version = "{version}") {{
    this.baseUrl = baseUrl;
    this.version = version;
    this.token = null;
  }}
  
  async login(username, password) {{
    const response = await fetch(`${{this.baseUrl}}/auth/login`, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
        'X-API-Version': this.version
      }},
      body: JSON.stringify({{ username, password }})
    }});
    
    if (!response.ok) throw new Error('Login failed');
    
    const data = await response.json();
    this.token = data.access_token;
    return this.token;
  }}
  
  async getProfile() {{
    const response = await fetch(`${{this.baseUrl}}/users/profile`, {{
      headers: {{
        'Authorization': `Bearer ${{this.token}}`,
        'X-API-Version': this.version
      }}
    }});
    
    if (!response.ok) throw new Error('Failed to get profile');
    return response.json();
  }}
}}

// Usage
const api = new FinancialPlanningAPI();
await api.login('user@example.com', 'password');
const profile = await api.getProfile();
console.log(profile);
"""
            }
        }
        
        return examples
    
    def _generate_migration_guides(self, version: str) -> List[Dict[str, str]]:
        """Generate migration guides for this version"""
        
        migration_guides = []
        
        # Find all older versions to create migration guides from
        all_versions = self.version_manager.get_all_versions()
        older_versions = [
            v for v in all_versions 
            if v.version != version and v.is_supported
        ]
        
        for old_version in older_versions:
            try:
                # Generate migration guide using compatibility analyzer
                migration_guide = self.compatibility_analyzer.generate_migration_guide(
                    old_version.version, version
                )
                
                if 'error' not in migration_guide:
                    template = self.jinja_env.get_template("migration_guide.md")
                    
                    # Extract data for template
                    breaking_issues = [
                        issue for issue in migration_guide.get('issues', [])
                        if issue.get('issue_type') == 'breaking_change'
                    ]
                    
                    deprecated_issues = [
                        issue for issue in migration_guide.get('issues', [])
                        if issue.get('issue_type') == 'deprecated_feature'
                    ]
                    
                    to_version_obj = self.version_manager.get_version(version)
                    
                    content = template.render(
                        from_version=old_version.version,
                        to_version=version,
                        compatibility_level=migration_guide.get('compatibility_level', 'unknown'),
                        migration_required=migration_guide.get('migration_required', True),
                        estimated_effort=migration_guide['overview']['estimated_effort'],
                        breaking_issues=breaking_issues,
                        deprecated_issues=deprecated_issues,
                        new_features=to_version_obj.new_features if to_version_obj else [],
                        migration_steps=migration_guide.get('step_by_step', []),
                        docs_url=f"/docs/api/v{version.split('.')[0]}",
                        support_url="/support",
                        contact_url="/contact"
                    )
                    
                    migration_guides.append({
                        "from_version": old_version.version,
                        "to_version": version,
                        "title": f"Migration Guide: v{old_version.version} → v{version}",
                        "content": content,
                        "complexity": migration_guide.get('migration_complexity', 'medium')
                    })
            
            except Exception as e:
                logger.error(f"Failed to generate migration guide from {old_version.version} to {version}: {e}")
        
        return migration_guides
    
    def _generate_changelog(self, version_obj: APIVersion) -> List[Dict[str, Any]]:
        """Generate changelog for the version"""
        
        template = self.jinja_env.get_template("changelog.md")
        
        changelog_content = template.render(
            version=version_obj.version,
            release_date=version_obj.release_date.strftime("%Y-%m-%d") if version_obj.release_date else "TBD",
            status=version_obj.status.value.title(),
            description=version_obj.description,
            breaking_changes=version_obj.breaking_changes,
            new_features=version_obj.new_features,
            bug_fixes=version_obj.bug_fixes,
            deprecations=[],  # Would be populated from deprecation manager
            migration_notes=[]  # Would be populated from migration guides
        )
        
        return [{
            "version": version_obj.version,
            "date": version_obj.release_date.isoformat() if version_obj.release_date else None,
            "content": changelog_content,
            "breaking_changes": len(version_obj.breaking_changes),
            "new_features": len(version_obj.new_features)
        }]
    
    def export_documentation(self, version: str, format: str = "markdown") -> Dict[str, str]:
        """Export documentation for a version"""
        
        docs = self.generate_version_documentation(version)
        output_files = {}
        
        version_dir = self.output_dir / f"v{version.split('.')[0]}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            # Export overview
            overview_file = version_dir / "index.md"
            overview_file.write_text(docs.sections[0].content)
            output_files["overview"] = str(overview_file)
            
            # Export endpoints
            endpoints_dir = version_dir / "endpoints"
            endpoints_dir.mkdir(exist_ok=True)
            
            for endpoint in docs.endpoints:
                endpoint_filename = f"{endpoint['method'].lower()}_{endpoint['path'].replace('/', '_').strip('_')}.md"
                endpoint_file = endpoints_dir / endpoint_filename
                endpoint_file.write_text(endpoint["content"])
                output_files[f"endpoint_{endpoint['path']}"] = str(endpoint_file)
            
            # Export other sections
            for section in docs.sections[1:]:  # Skip overview (already exported)
                section_file = version_dir / f"{section.title.lower().replace(' ', '_')}.md"
                section_file.write_text(section.content)
                output_files[section.title] = str(section_file)
            
            # Export migration guides
            if docs.migration_guides:
                migration_dir = version_dir / "migration"
                migration_dir.mkdir(exist_ok=True)
                
                for guide in docs.migration_guides:
                    guide_file = migration_dir / f"from_v{guide['from_version'].replace('.', '_')}.md"
                    guide_file.write_text(guide["content"])
                    output_files[f"migration_from_{guide['from_version']}"] = str(guide_file)
        
        elif format == "json":
            # Export as JSON
            json_file = version_dir / f"v{version}_docs.json"
            json_file.write_text(json.dumps(docs.to_dict(), indent=2))
            output_files["json"] = str(json_file)
        
        elif format == "openapi":
            # Generate OpenAPI specification
            openapi_spec = self._generate_openapi_spec(docs, version)
            openapi_file = version_dir / "openapi.yaml"
            openapi_file.write_text(yaml.dump(openapi_spec, default_flow_style=False))
            output_files["openapi"] = str(openapi_file)
        
        logger.info(f"Exported documentation for version {version} to {version_dir}")
        return output_files
    
    def _generate_openapi_spec(self, docs: APIDocumentation, version: str) -> Dict[str, Any]:
        """Generate OpenAPI specification for the version"""
        
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": docs.title,
                "description": docs.description,
                "version": version,
                "contact": {
                    "name": "API Support",
                    "url": "https://financial-planning.com/support",
                    "email": "api-support@financial-planning.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": docs.base_url,
                    "description": f"Production server for API v{version}"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "parameters": {
                    "ApiVersion": {
                        "name": "X-API-Version",
                        "in": "header",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": [version]
                        },
                        "description": "API version"
                    }
                }
            },
            "security": [
                {"bearerAuth": []}
            ]
        }
        
        # Add paths from endpoint documentation
        for endpoint in docs.endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            spec["paths"][path][method] = {
                "summary": endpoint["title"],
                "operationId": f"{method}_{path.replace('/', '_').strip('_')}",
                "parameters": [
                    {"$ref": "#/components/parameters/ApiVersion"}
                ],
                "responses": {
                    "200": {
                        "description": "Success"
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "404": {
                        "description": "Not Found"
                    }
                }
            }
            
            if endpoint.get("deprecated"):
                spec["paths"][path][method]["deprecated"] = True
        
        return spec
    
    def generate_documentation_index(self) -> str:
        """Generate documentation index for all versions"""
        
        all_versions = self.version_manager.get_all_versions()
        
        index_content = """# Financial Planning API Documentation

Welcome to the Financial Planning API documentation. Choose your API version below:

## Available Versions

"""
        
        for version_obj in all_versions:
            status_badge = {
                "stable": "🟢 Stable",
                "beta": "🟡 Beta", 
                "deprecated": "🟠 Deprecated",
                "retired": "🔴 Retired",
                "development": "🔵 Development"
            }.get(version_obj.status.value, "⚪ Unknown")
            
            index_content += f"""### [Version {version_obj.version}](v{version_obj.version.split('.')[0]}/) {status_badge}

{version_obj.description}

- **Release Date**: {version_obj.release_date.strftime('%Y-%m-%d') if version_obj.release_date else 'TBD'}
"""
            
            if version_obj.is_deprecated:
                index_content += f"- **⚠️ Deprecated**: {version_obj.deprecation_date.strftime('%Y-%m-%d') if version_obj.deprecation_date else 'Date TBD'}\n"
                if version_obj.retirement_date:
                    index_content += f"- **🗓️ Retirement**: {version_obj.retirement_date.strftime('%Y-%m-%d')}\n"
            
            index_content += "\n"
        
        index_content += """
## Migration Guides

- [Migration Overview](/docs/migration/)
- [Breaking Changes Log](/docs/breaking-changes/)
- [Compatibility Matrix](/docs/compatibility/)

## Support

- [API Support Forum](https://community.financial-planning.com/api)
- [Contact Support](mailto:api-support@financial-planning.com)
- [GitHub Issues](https://github.com/financial-planning/api/issues)
"""
        
        # Write index file
        index_file = self.output_dir / "index.md"
        index_file.write_text(index_content)
        
        return str(index_file)
    
    def export_all_documentation(self) -> Dict[str, List[str]]:
        """Export documentation for all versions"""
        
        exported_files = {}
        
        # Generate index
        index_file = self.generate_documentation_index()
        exported_files["index"] = [index_file]
        
        # Export documentation for each version
        for version_obj in self.version_manager.get_all_versions():
            version_files = self.export_documentation(version_obj.version)
            exported_files[f"v{version_obj.version}"] = list(version_files.values())
        
        logger.info(f"Exported documentation for {len(exported_files)} versions")
        return exported_files