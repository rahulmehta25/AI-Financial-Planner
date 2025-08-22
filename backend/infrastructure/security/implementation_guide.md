# Security Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing comprehensive security hardening for the Financial Planning Application in production.

## Table of Contents

1. [Application Security Implementation](#1-application-security-implementation)
2. [Infrastructure Security Setup](#2-infrastructure-security-setup)
3. [Data Security Configuration](#3-data-security-configuration)
4. [Compliance Implementation](#4-compliance-implementation)
5. [Security Monitoring Setup](#5-security-monitoring-setup)
6. [Testing and Validation](#6-testing-and-validation)

## 1. Application Security Implementation

### 1.1 Security Headers Configuration

#### Step 1: Install Security Middleware

```python
# app/main.py
from infrastructure.security.security_headers import SecurityMiddleware, SecurityLevel

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    security_level=SecurityLevel.STRICT
)
```

#### Step 2: Configure CORS

```python
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.security.security_headers import CORS_CONFIG

app.add_middleware(
    CORSMiddleware,
    **CORS_CONFIG
)
```

#### Step 3: Verify Headers

```bash
# Test security headers
curl -I https://api.financialplanner.com
```

### 1.2 Input Validation Implementation

#### Step 1: Import Validation Module

```python
from infrastructure.security.input_validation import InputValidator, SQLParameterizer

# In your API endpoints
@router.post("/api/v1/user/profile")
async def update_profile(profile_data: dict):
    # Validate input
    if InputValidator.check_sql_injection(str(profile_data)):
        raise HTTPException(status_code=400, detail="Invalid input detected")
    
    # Sanitize HTML content
    profile_data['bio'] = InputValidator.sanitize_html(profile_data.get('bio', ''))
    
    # Validate email
    if not InputValidator.validate_email(profile_data.get('email')):
        raise HTTPException(status_code=400, detail="Invalid email format")
```

#### Step 2: Implement SQL Parameterization

```python
# Use parameterized queries
query, params = SQLParameterizer.build_safe_query(
    "SELECT * FROM users",
    {"email": user_email, "active": True}
)
result = await database.fetch_all(query=query, values=params)
```

### 1.3 CSRF Protection

#### Step 1: Generate CSRF Tokens

```python
from infrastructure.security.input_validation import CSRFProtection

csrf_protection = CSRFProtection(settings.SECRET_KEY)

@router.get("/api/v1/csrf-token")
async def get_csrf_token(request: Request):
    session_id = request.session.get("session_id")
    token = csrf_protection.generate_token(session_id)
    return {"csrf_token": token}
```

#### Step 2: Validate CSRF Tokens

```python
@router.post("/api/v1/transaction")
async def create_transaction(
    request: Request,
    csrf_token: str = Header(...),
    transaction_data: dict = Body(...)
):
    session_id = request.session.get("session_id")
    if not csrf_protection.validate_token(csrf_token, session_id):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
```

## 2. Infrastructure Security Setup

### 2.1 WAF Deployment

#### AWS WAF Setup

```bash
# Deploy AWS WAF using Terraform
cd terraform/modules/waf

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=../../environments/production/terraform.tfvars

# Apply configuration
terraform apply -var-file=../../environments/production/terraform.tfvars
```

#### Configure WAF Rules

```python
# Python script to configure WAF rules
import boto3
from infrastructure.security.waf_rules import WAFRuleSet

waf_client = boto3.client('wafv2', region_name='us-east-1')

# Get AWS WAF rules
waf_rules = WAFRuleSet.get_aws_waf_rules()

# Create Web ACL
response = waf_client.create_web_acl(
    Name='financial-planner-waf',
    Scope='REGIONAL',
    DefaultAction={'Allow': {}},
    Rules=waf_rules['Rules'],
    CustomResponseBodies=waf_rules['CustomResponseBodies'],
    VisibilityConfig={
        'SampledRequestsEnabled': True,
        'CloudWatchMetricsEnabled': True,
        'MetricName': 'financial-planner-waf'
    }
)
```

### 2.2 Network Segmentation

#### Step 1: Create VPC and Subnets

```bash
# Using AWS CLI
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=financial-planner-vpc}]'

# Create subnets for each zone
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1a}]'
```

#### Step 2: Configure Security Groups

```python
# Python script to configure security groups
import boto3
from infrastructure.security.network_security import NetworkSegmentation

ec2 = boto3.client('ec2')
network_config = NetworkSegmentation.get_network_architecture()

for sg_name, sg_config in network_config['security_groups'].items():
    response = ec2.create_security_group(
        GroupName=sg_name,
        Description=sg_config['description'],
        VpcId='vpc-xxx'
    )
    
    # Add ingress rules
    for rule in sg_config['ingress']:
        ec2.authorize_security_group_ingress(
            GroupId=response['GroupId'],
            IpPermissions=[{
                'IpProtocol': rule['protocol'],
                'FromPort': rule['port'],
                'ToPort': rule['port'],
                'IpRanges': [{'CidrIp': rule['source']}]
            }]
        )
```

### 2.3 Bastion Host Setup

#### Step 1: Deploy Bastion Host

```bash
# Deploy using AWS Systems Manager Session Manager (recommended)
aws ec2 run-instances \
    --image-id ami-xxx \
    --instance-type t3.small \
    --key-name bastion-key \
    --subnet-id subnet-xxx \
    --security-group-ids sg-xxx \
    --iam-instance-profile Name=BastionHostProfile \
    --user-data file://bastion-userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bastion-host}]'
```

#### Step 2: Configure Session Recording

```bash
# Enable session logging to S3
aws ssm create-document \
    --name SessionManagerRunShell \
    --document-type Session \
    --content file://session-manager-config.json
```

### 2.4 VPN Configuration

#### Site-to-Site VPN

```bash
# Create VPN Gateway
aws ec2 create-vpn-gateway --type ipsec.1 --amazon-side-asn 65000

# Attach to VPC
aws ec2 attach-vpn-gateway --vpn-gateway-id vgw-xxx --vpc-id vpc-xxx

# Create Customer Gateway
aws ec2 create-customer-gateway \
    --bgp-asn 65001 \
    --public-ip 203.0.113.100 \
    --type ipsec.1
```

#### Client VPN

```bash
# Generate certificates
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa build-server-full server nopass
./easyrsa build-client-full client1 nopass

# Create Client VPN endpoint
aws ec2 create-client-vpn-endpoint \
    --client-cidr-block 192.168.100.0/22 \
    --server-certificate-arn arn:aws:acm:region:account:certificate/xxx \
    --authentication-options Type=certificate-authentication,MutualAuthentication={ClientRootCertificateChainArn=arn:aws:acm:region:account:certificate/xxx} \
    --connection-log-options Enabled=true,CloudwatchLogGroup=/aws/vpn/connections
```

## 3. Data Security Configuration

### 3.1 Encryption at Rest

#### Database Encryption

```sql
-- PostgreSQL TDE setup
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encrypted table
CREATE TABLE sensitive_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    encrypted_ssn BYTEA,
    encrypted_account BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Encryption function
CREATE OR REPLACE FUNCTION encrypt_sensitive(plain_text TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(
        plain_text,
        current_setting('app.encryption_key')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### Application-Level Encryption

```python
from infrastructure.security.encryption_config import EncryptionManager

# Initialize encryption manager
encryption_manager = EncryptionManager()

# Encrypt PII data
user_data = {
    'name': 'John Doe',
    'ssn': '123-45-6789',
    'bank_account': '1234567890'
}

encrypted_data = encryption_manager.encrypt_pii(user_data)
```

### 3.2 Key Management

#### AWS KMS Setup

```python
from infrastructure.security.encryption_config import AWSKMSIntegration

kms = AWSKMSIntegration()

# Create master key
key_id = kms.create_master_key()

# Enable key rotation
kms.rotate_key()

# Encrypt data
encrypted = kms.encrypt_data(b"sensitive data")

# Generate data key for envelope encryption
data_key = kms.generate_data_key()
```

#### HashiCorp Vault Integration

```bash
# Initialize Vault
vault operator init
vault operator unseal

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Enable transit engine for encryption
vault secrets enable transit

# Create encryption key
vault write -f transit/keys/financial-planner

# Store database credentials
vault kv put secret/database/postgres username=dbuser password=dbpass
```

## 4. Compliance Implementation

### 4.1 GDPR Compliance

```python
from infrastructure.security.compliance_config import GDPRCompliance

# Generate consent record
consent = GDPRCompliance.generate_consent_record(
    user_id="user123",
    purposes=["marketing", "analytics", "personalization"]
)

# Implement data portability
@router.get("/api/v1/gdpr/export/{user_id}")
async def export_user_data(user_id: str):
    export_data = GDPRCompliance.data_portability_export(user_id)
    # Fetch actual user data
    # ...
    return export_data

# Right to erasure
@router.delete("/api/v1/gdpr/erase/{user_id}")
async def erase_user_data(user_id: str):
    erasure_config = GDPRCompliance.right_to_erasure_config()
    # Implement erasure based on config
    # ...
```

### 4.2 PCI DSS Compliance

```python
from infrastructure.security.compliance_config import PCIDSSCompliance

# Configure tokenization
tokenization_config = PCIDSSCompliance.tokenization_config()

# Never store card data - tokenize immediately
@router.post("/api/v1/payment/tokenize")
async def tokenize_card(card_data: dict):
    # Send to tokenization service
    token = await tokenization_service.tokenize(card_data)
    # Never log card data
    logger.info(f"Card tokenized for user: {user_id}")
    return {"token": token}
```

### 4.3 Audit Logging

```python
import logging
from datetime import datetime

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('/var/log/audit/financial_planner_audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)

# Log security events
def log_security_event(event_type: str, user_id: str, details: dict):
    audit_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details,
        'ip_address': request.client.host
    })
```

## 5. Security Monitoring Setup

### 5.1 SIEM Integration

#### Splunk Setup

```python
from infrastructure.security.siem_integration import SIEMConnector
import splunklib.client as client

# Connect to Splunk
splunk_config = SIEMConnector.get_splunk_config()
service = client.connect(
    host=splunk_config['connection']['host'],
    port=splunk_config['connection']['port'],
    username='admin',
    password='password'
)

# Create saved searches
for search in splunk_config['saved_searches']:
    service.saved_searches.create(
        name=search['name'],
        search=search['search'],
        cron_schedule=search['schedule']
    )
```

#### ELK Stack Setup

```yaml
# docker-compose.yml for ELK stack
version: '3.7'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=changeme
    volumes:
      - elastic_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=changeme
    ports:
      - "5601:5601"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/config:/usr/share/logstash/config
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5000:5000"
      - "9600:9600"
```

### 5.2 Threat Detection

```python
from infrastructure.security.siem_integration import ThreatIntelligence

# Configure threat feeds
threat_feeds = ThreatIntelligence.get_threat_feeds()

# Check IP against threat intelligence
def check_ip_reputation(ip_address: str) -> bool:
    for feed in threat_feeds:
        if ip_in_threat_feed(ip_address, feed):
            log_security_event('threat_detected', ip_address, {'feed': feed['name']})
            return True
    return False

# Implement in middleware
@app.middleware("http")
async def threat_detection_middleware(request: Request, call_next):
    client_ip = request.client.host
    if check_ip_reputation(client_ip):
        return JSONResponse(status_code=403, content={"detail": "Access denied"})
    response = await call_next(request)
    return response
```

### 5.3 Incident Response Automation

```python
from infrastructure.security.siem_integration import SecurityOrchestration

# Get incident response playbooks
playbooks = SecurityOrchestration.get_incident_response_playbooks()

# Implement automated response
async def handle_security_incident(incident_type: str, context: dict):
    if incident_type in playbooks:
        playbook = playbooks[incident_type]
        
        # Check trigger conditions
        if evaluate_trigger(playbook['trigger'], context):
            # Execute response actions
            for action in playbook['actions']:
                await execute_action(action, context)
                log_security_event('incident_response', incident_type, action)
```

## 6. Testing and Validation

### 6.1 Security Testing

```bash
# Run OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t https://api.financialplanner.com \
    -r security_scan_report.html

# Run SQLMap for SQL injection testing
sqlmap -u "https://api.financialplanner.com/api/v1/search?q=test" \
    --batch --random-agent --level=5 --risk=3

# Run Nikto web scanner
nikto -h https://api.financialplanner.com -ssl -Format html -o nikto_report.html
```

### 6.2 Compliance Validation

```python
# Automated compliance checking
from infrastructure.security.compliance_config import ComplianceAuditor

def run_compliance_audit():
    results = {}
    
    # Check GDPR compliance
    results['gdpr'] = ComplianceAuditor.run_compliance_check(ComplianceFramework.GDPR)
    
    # Check PCI DSS compliance
    results['pci_dss'] = ComplianceAuditor.run_compliance_check(ComplianceFramework.PCI_DSS)
    
    # Check SOC 2 compliance
    results['soc2'] = ComplianceAuditor.run_compliance_check(ComplianceFramework.SOC2)
    
    return results

# Schedule daily compliance checks
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(run_compliance_audit, 'cron', hour=2)
scheduler.start()
```

### 6.3 Performance Testing

```bash
# Load testing with k6
cat <<EOF > load_test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '10m', target: 100 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function() {
  let response = http.get('https://api.financialplanner.com/api/v1/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
EOF

k6 run load_test.js
```

## Deployment Checklist

### Pre-Deployment

- [ ] All security configurations reviewed
- [ ] Security headers configured
- [ ] WAF rules deployed
- [ ] Network segmentation verified
- [ ] Encryption keys generated and stored
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Security monitoring active

### Post-Deployment

- [ ] Security scan completed
- [ ] Penetration test scheduled
- [ ] Compliance audit performed
- [ ] Security metrics baseline established
- [ ] Team training completed
- [ ] Documentation updated
- [ ] Emergency contacts verified
- [ ] Monitoring alerts configured

## Support and Maintenance

### Regular Security Tasks

| Task | Frequency | Owner |
|------|-----------|-------|
| Vulnerability scanning | Weekly | Security Team |
| Security patches | As needed (< 30 days) | DevOps |
| Log review | Daily | SOC |
| Access review | Monthly | IAM Team |
| Compliance audit | Quarterly | Compliance Team |
| Penetration testing | Annually | External Vendor |
| Security training | Quarterly | All Staff |
| Incident response drill | Bi-annually | Security Team |

### Emergency Contacts

- **Security Team Lead:** security-lead@financialplanner.com
- **24/7 SOC:** +1-800-SECURITY
- **Data Protection Officer:** dpo@financialplanner.com
- **Incident Response:** incident-response@financialplanner.com

---

**Document Version:** 1.0  
**Last Updated:** 2025-08-22  
**Next Review:** 2025-09-22