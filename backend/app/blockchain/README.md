# Blockchain-Based Audit System

A comprehensive blockchain-based audit system for financial planning applications that provides immutable audit logging, document integrity verification, and regulatory compliance through Ethereum smart contracts and IPFS storage.

## Features

### 🔐 Immutable Audit Logging
- Ethereum smart contracts for tamper-proof audit logs
- Hash-based integrity verification
- Complete audit trail for all user actions
- Real-time verification of audit events

### 📁 Distributed Document Storage
- IPFS integration for decentralized document storage
- Encrypted storage with optional client-side encryption
- Content-addressed storage with integrity verification
- Automatic pinning for important documents

### ✅ Proof of Existence
- Blockchain-based proof of existence for financial plans
- Cryptographic proof of document creation time
- Immutable timestamps and data hashes
- Verification of document integrity over time

### 📊 Regulatory Compliance
- Support for multiple compliance standards (SOX, GDPR, PCI-DSS, HIPAA, ISO27001, NIST)
- Automated compliance proof generation
- Regulatory audit trail creation
- Compliance reporting and export

### 📈 Audit Trail Visualization
- Interactive audit trail visualization
- Network graph representation of audit events
- Compliance dashboards and analytics
- Exportable audit reports (JSON, HTML)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Ethereum      │    │      IPFS       │
│   Endpoints     │◄──►│   Blockchain    │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Audit Service   │    │ Smart Contracts │    │ Document Store  │
│ - Event Logging │    │ - AuditLogger   │    │ - Encrypted     │
│ - Verification  │    │ - Compliance    │    │ - Versioned     │
│ - Search/Query  │    │ - Integrity     │    │ - Retrievable   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Services Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Integrity   │  │ Compliance  │  │    Visualization        │  │
│  │ Service     │  │ Service     │  │    Service             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Smart Contracts

### AuditLogger.sol
- **Purpose**: Immutable logging of audit events
- **Key Functions**:
  - `logAuditEvent()`: Record audit events with IPFS references
  - `getAuditEvent()`: Retrieve audit event details
  - `verifyEventIntegrity()`: Verify data integrity
  - `getUserAuditEvents()`: Get all events for a user

### ComplianceRegistry.sol
- **Purpose**: Proof of existence and compliance tracking
- **Key Functions**:
  - `createProofOfExistence()`: Create proof for financial plans
  - `verifyPlanIntegrity()`: Verify plan integrity
  - `recordComplianceProof()`: Record compliance evidence
  - `getComplianceProof()`: Retrieve compliance proofs

## API Endpoints

### Audit Endpoints (`/api/v1/blockchain/audit`)
- `POST /events` - Create audit event
- `GET /events/{event_id}` - Get audit event
- `GET /events/{event_id}/verify` - Verify event integrity
- `GET /users/{user_id}/events` - Get user audit events
- `POST /events/search` - Search audit events
- `GET /statistics` - Get audit statistics
- `POST /events/batch` - Batch create events

### Compliance Endpoints (`/api/v1/blockchain/compliance`)
- `POST /proof-of-existence` - Create proof of existence
- `GET /proof-of-existence/{plan_id}/verify` - Verify proof
- `GET /users/{user_id}/proofs` - Get user proofs
- `POST /compliance-proof` - Record compliance proof
- `GET /compliance-proof/standard/{standard}` - Get proofs by standard
- `POST /report` - Generate compliance report
- `GET /audit-trail/{plan_id}` - Get audit trail

### Visualization Endpoints (`/api/v1/blockchain/visualization`)
- `GET /audit-trail/{plan_id}` - Get audit trail visualization
- `GET /audit-trail/{plan_id}/export` - Export audit report
- `GET /dashboard/user/{user_id}` - User audit dashboard
- `GET /dashboard/compliance` - Compliance dashboard
- `GET /analytics/trends` - Audit trends
- `GET /network-graph/{plan_id}` - Network graph visualization

## Setup and Installation

### Prerequisites
- Python 3.8+
- Ethereum node (Ganache for development)
- IPFS node
- Required Python packages (see requirements.txt)

### Environment Configuration
```bash
# Copy and configure environment variables
cp .env.example .env

# Key configuration variables:
BLOCKCHAIN_ETHEREUM_PROVIDER_URL=http://localhost:8545
BLOCKCHAIN_IPFS_API_URL=http://localhost:5001
BLOCKCHAIN_ETHEREUM_PRIVATE_KEY=0x...
BLOCKCHAIN_AUDIT_CONTRACT_ADDRESS=0x...
BLOCKCHAIN_COMPLIANCE_CONTRACT_ADDRESS=0x...
```

### Smart Contract Deployment
```bash
# Deploy contracts using Hardhat or Truffle
npx hardhat deploy --network localhost

# Update configuration with deployed contract addresses
```

### System Initialization
```python
from app.blockchain.setup import BlockchainSetup

setup = BlockchainSetup()
results = await setup.initialize_system()
```

## Usage Examples

### Creating an Audit Event
```python
from app.blockchain.services.audit_service import BlockchainAuditService

audit_service = BlockchainAuditService()

audit_log = await audit_service.log_audit_event(
    user_id="user123",
    action="create",
    resource_type="financial_plan",
    resource_id="plan456",
    data={"plan_name": "Retirement Plan 2024"},
    ip_address="192.168.1.100"
)
```

### Creating Proof of Existence
```python
from app.blockchain.services.compliance_service import ComplianceService

compliance_service = ComplianceService()

proof = await compliance_service.create_proof_of_existence(
    plan_id="plan123",
    user_id="user456",
    plan_data={
        "name": "My Retirement Plan",
        "goals": ["retirement", "education"],
        "investments": ["stocks", "bonds"]
    },
    metadata={"version": "1.0"}
)
```

### Verifying Integrity
```python
# Verify audit event
verification = await audit_service.verify_audit_event("event123")
print(f"Event verified: {verification['valid']}")

# Verify proof of existence
proof_verification = await compliance_service.verify_proof_of_existence("plan123")
print(f"Proof verified: {proof_verification['valid']}")
```

### Generating Visualizations
```python
from app.blockchain.services.visualization_service import VisualizationService

viz_service = VisualizationService()

# Generate audit trail visualization
visualization = await viz_service.generate_audit_trail_visualization("plan123")

# Export as HTML report
report = viz_service.export_audit_trail_report(visualization, format="html")
```

## Security Features

### Data Encryption
- AES-256-GCM encryption for sensitive data
- RSA encryption for key exchange
- HMAC for data integrity verification
- Secure key derivation (PBKDF2)

### Blockchain Security
- Smart contract access controls
- Multi-signature support for critical operations
- Gas optimization and limits
- Reentrancy protection

### IPFS Security
- Content-addressed storage
- Optional client-side encryption
- Pinning for persistence
- Integrity verification

## Compliance Standards

The system supports the following compliance standards:
- **SOX**: Sarbanes-Oxley Act compliance
- **GDPR**: General Data Protection Regulation
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **HIPAA**: Health Insurance Portability and Accountability Act
- **ISO27001**: Information Security Management
- **NIST**: National Institute of Standards and Technology

## Monitoring and Health Checks

### Health Check Endpoints
- `/api/v1/blockchain/audit/health` - Audit system health
- `/api/v1/blockchain/compliance/health` - Compliance system health
- `/api/v1/blockchain/visualization/health` - Visualization system health

### System Monitoring
```python
# Check system health
health = await setup.verify_system_health()
print(f"Overall health: {health['overall_health']}")

# Get audit statistics
stats = await audit_service.get_audit_statistics()
print(f"Total events: {stats['total_audit_events']}")
```

## Performance Considerations

### Batch Operations
- Batch audit event creation for high-volume scenarios
- Bulk verification operations
- Optimized IPFS storage patterns

### Caching
- Redis caching for frequently accessed data
- IPFS content caching
- Blockchain query result caching

### Gas Optimization
- Efficient smart contract design
- Batch transactions to reduce gas costs
- Dynamic gas price adjustment

## Troubleshooting

### Common Issues

1. **Blockchain Connection Failed**
   - Verify Ethereum node is running
   - Check provider URL configuration
   - Ensure account has sufficient ETH for gas

2. **IPFS Connection Failed**
   - Verify IPFS daemon is running
   - Check API endpoint configuration
   - Ensure network connectivity

3. **Smart Contract Deployment Issues**
   - Verify contract compilation
   - Check deployment configuration
   - Ensure sufficient gas for deployment

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for blockchain operations
```

## Development

### Running Tests
```bash
pytest tests/blockchain/ -v
```

### Code Quality
```bash
# Linting
flake8 app/blockchain/

# Type checking
mypy app/blockchain/

# Security scanning
bandit -r app/blockchain/
```

## Contributing

1. Follow existing code patterns and style
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure security best practices
5. Test with both mainnet and testnet configurations

## License

This blockchain audit system is part of the financial planning application and follows the same licensing terms.