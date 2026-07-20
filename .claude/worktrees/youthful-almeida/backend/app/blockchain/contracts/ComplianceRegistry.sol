// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title ComplianceRegistry
 * @dev Smart contract for proof-of-existence and regulatory compliance
 */
contract ComplianceRegistry is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    struct ProofOfExistence {
        string planId;
        string userId;
        bytes32 planHash;
        uint256 timestamp;
        string ipfsHash;
        uint256 blockNumber;
        bool exists;
    }
    
    struct ComplianceProof {
        string complianceId;
        string standard;
        bytes32 evidenceHash;
        uint256 timestamp;
        string ipfsEvidence;
        uint256 blockNumber;
        bool exists;
    }
    
    // Events
    event ProofOfExistenceCreated(
        string indexed planId,
        string indexed userId,
        bytes32 planHash,
        uint256 timestamp,
        string ipfsHash
    );
    
    event ComplianceProofRecorded(
        string indexed complianceId,
        string indexed standard,
        bytes32 evidenceHash,
        uint256 timestamp
    );
    
    event PlanIntegrityVerified(
        string indexed planId,
        bool verified,
        uint256 timestamp
    );
    
    // State variables
    Counters.Counter private _proofCounter;
    Counters.Counter private _complianceCounter;
    
    mapping(string => ProofOfExistence) private _proofs;
    mapping(string => ComplianceProof) private _complianceProofs;
    mapping(string => string[]) private _userPlans;
    mapping(string => string[]) private _standardCompliance;
    mapping(address => bool) private _authorizedRecorders;
    
    // Compliance standards tracking
    string[] private _supportedStandards;
    mapping(string => bool) private _standardExists;
    
    // Modifiers
    modifier onlyAuthorizedRecorder() {
        require(_authorizedRecorders[msg.sender] || msg.sender == owner(), "Not authorized to record");
        _;
    }
    
    modifier proofExists(string memory planId) {
        require(_proofs[planId].exists, "Proof of existence does not exist");
        _;
    }
    
    modifier complianceExists(string memory complianceId) {
        require(_complianceProofs[complianceId].exists, "Compliance proof does not exist");
        _;
    }
    
    constructor() {
        _authorizedRecorders[msg.sender] = true;
        
        // Initialize supported compliance standards
        _addStandard("SOX");
        _addStandard("GDPR");
        _addStandard("PCI-DSS");
        _addStandard("HIPAA");
        _addStandard("ISO27001");
        _addStandard("NIST");
    }
    
    /**
     * @dev Create proof of existence for a financial plan
     * @param planId Unique identifier for the plan
     * @param userId User who owns the plan
     * @param planHash SHA-256 hash of the plan data
     * @param timestamp Unix timestamp of plan creation
     * @param ipfsHash IPFS hash for plan document storage
     */
    function createProofOfExistence(
        string memory planId,
        string memory userId,
        bytes32 planHash,
        uint256 timestamp,
        string memory ipfsHash
    ) external onlyAuthorizedRecorder nonReentrant {
        require(!_proofs[planId].exists, "Proof already exists for this plan");
        require(bytes(planId).length > 0, "Plan ID cannot be empty");
        require(bytes(userId).length > 0, "User ID cannot be empty");
        require(planHash != bytes32(0), "Plan hash cannot be empty");
        require(timestamp > 0, "Timestamp must be positive");
        
        _proofs[planId] = ProofOfExistence({
            planId: planId,
            userId: userId,
            planHash: planHash,
            timestamp: timestamp,
            ipfsHash: ipfsHash,
            blockNumber: block.number,
            exists: true
        });
        
        _userPlans[userId].push(planId);
        _proofCounter.increment();
        
        emit ProofOfExistenceCreated(planId, userId, planHash, timestamp, ipfsHash);
    }
    
    /**
     * @dev Retrieve proof of existence for a plan
     * @param planId The plan ID to retrieve
     * @return userId User who owns the plan
     * @return planHash SHA-256 hash of the plan
     * @return timestamp Unix timestamp of creation
     * @return ipfsHash IPFS hash for document
     * @return blockNumber Block number where proof was recorded
     */
    function getProofOfExistence(string memory planId) 
        external 
        view 
        proofExists(planId)
        returns (
            string memory userId,
            bytes32 planHash,
            uint256 timestamp,
            string memory ipfsHash,
            uint256 blockNumber
        ) 
    {
        ProofOfExistence memory proof = _proofs[planId];
        return (
            proof.userId,
            proof.planHash,
            proof.timestamp,
            proof.ipfsHash,
            proof.blockNumber
        );
    }
    
    /**
     * @dev Verify the integrity of a financial plan
     * @param planId The plan ID to verify
     * @param planHash The expected plan hash
     * @return True if the plan integrity is verified
     */
    function verifyPlanIntegrity(string memory planId, bytes32 planHash) 
        external 
        view 
        proofExists(planId)
        returns (bool) 
    {
        bool verified = _proofs[planId].planHash == planHash;
        emit PlanIntegrityVerified(planId, verified, block.timestamp);
        return verified;
    }
    
    /**
     * @dev Record compliance proof for regulatory standards
     * @param complianceId Unique identifier for compliance proof
     * @param standard Compliance standard (e.g., SOX, GDPR)
     * @param evidenceHash Hash of compliance evidence
     * @param timestamp Unix timestamp of compliance
     * @param ipfsEvidence IPFS hash for evidence documents
     */
    function recordComplianceProof(
        string memory complianceId,
        string memory standard,
        bytes32 evidenceHash,
        uint256 timestamp,
        string memory ipfsEvidence
    ) external onlyAuthorizedRecorder nonReentrant {
        require(!_complianceProofs[complianceId].exists, "Compliance proof already exists");
        require(bytes(complianceId).length > 0, "Compliance ID cannot be empty");
        require(_standardExists[standard], "Unsupported compliance standard");
        require(evidenceHash != bytes32(0), "Evidence hash cannot be empty");
        require(timestamp > 0, "Timestamp must be positive");
        
        _complianceProofs[complianceId] = ComplianceProof({
            complianceId: complianceId,
            standard: standard,
            evidenceHash: evidenceHash,
            timestamp: timestamp,
            ipfsEvidence: ipfsEvidence,
            blockNumber: block.number,
            exists: true
        });
        
        _standardCompliance[standard].push(complianceId);
        _complianceCounter.increment();
        
        emit ComplianceProofRecorded(complianceId, standard, evidenceHash, timestamp);
    }
    
    /**
     * @dev Get compliance proof by ID
     * @param complianceId The compliance ID to retrieve
     * @return standard Compliance standard
     * @return evidenceHash Hash of evidence
     * @return timestamp Unix timestamp
     * @return ipfsEvidence IPFS hash for evidence
     * @return blockNumber Block number where recorded
     */
    function getComplianceProof(string memory complianceId) 
        external 
        view 
        complianceExists(complianceId)
        returns (
            string memory standard,
            bytes32 evidenceHash,
            uint256 timestamp,
            string memory ipfsEvidence,
            uint256 blockNumber
        ) 
    {
        ComplianceProof memory proof = _complianceProofs[complianceId];
        return (
            proof.standard,
            proof.evidenceHash,
            proof.timestamp,
            proof.ipfsEvidence,
            proof.blockNumber
        );
    }
    
    /**
     * @dev Get all plans for a specific user
     * @param userId The user ID to query
     * @return Array of plan IDs for the user
     */
    function getUserPlans(string memory userId) 
        external 
        view 
        returns (string[] memory) 
    {
        return _userPlans[userId];
    }
    
    /**
     * @dev Get all compliance proofs for a standard
     * @param standard The compliance standard to query
     * @return Array of compliance IDs for the standard
     */
    function getStandardCompliance(string memory standard) 
        external 
        view 
        returns (string[] memory) 
    {
        require(_standardExists[standard], "Unsupported compliance standard");
        return _standardCompliance[standard];
    }
    
    /**
     * @dev Get all supported compliance standards
     * @return Array of supported standards
     */
    function getSupportedStandards() external view returns (string[] memory) {
        return _supportedStandards;
    }
    
    /**
     * @dev Check if a compliance standard is supported
     * @param standard The standard to check
     * @return True if the standard is supported
     */
    function isStandardSupported(string memory standard) external view returns (bool) {
        return _standardExists[standard];
    }
    
    /**
     * @dev Get total number of proofs recorded
     * @return The total count of proofs
     */
    function getTotalProofCount() external view returns (uint256) {
        return _proofCounter.current();
    }
    
    /**
     * @dev Get total number of compliance proofs
     * @return The total count of compliance proofs
     */
    function getTotalComplianceCount() external view returns (uint256) {
        return _complianceCounter.current();
    }
    
    /**
     * @dev Add an authorized recorder address
     * @param recorder Address to authorize for recording
     */
    function addAuthorizedRecorder(address recorder) external onlyOwner {
        _authorizedRecorders[recorder] = true;
    }
    
    /**
     * @dev Remove an authorized recorder address
     * @param recorder Address to remove authorization from
     */
    function removeAuthorizedRecorder(address recorder) external onlyOwner {
        _authorizedRecorders[recorder] = false;
    }
    
    /**
     * @dev Check if an address is authorized to record
     * @param recorder Address to check
     * @return True if the address is authorized
     */
    function isAuthorizedRecorder(address recorder) external view returns (bool) {
        return _authorizedRecorders[recorder];
    }
    
    /**
     * @dev Add a new compliance standard
     * @param standard The standard to add
     */
    function addComplianceStandard(string memory standard) external onlyOwner {
        require(!_standardExists[standard], "Standard already exists");
        _addStandard(standard);
    }
    
    /**
     * @dev Internal function to add a compliance standard
     * @param standard The standard to add
     */
    function _addStandard(string memory standard) internal {
        _supportedStandards.push(standard);
        _standardExists[standard] = true;
    }
    
    /**
     * @dev Batch create multiple proofs of existence
     * @param planIds Array of plan IDs
     * @param userIds Array of user IDs
     * @param planHashes Array of plan hashes
     * @param timestamps Array of timestamps
     * @param ipfsHashes Array of IPFS hashes
     */
    function batchCreateProofs(
        string[] memory planIds,
        string[] memory userIds,
        bytes32[] memory planHashes,
        uint256[] memory timestamps,
        string[] memory ipfsHashes
    ) external onlyAuthorizedRecorder nonReentrant {
        require(planIds.length == userIds.length, "Array length mismatch");
        require(planIds.length == planHashes.length, "Array length mismatch");
        require(planIds.length == timestamps.length, "Array length mismatch");
        require(planIds.length == ipfsHashes.length, "Array length mismatch");
        require(planIds.length <= 50, "Batch size too large");
        
        for (uint256 i = 0; i < planIds.length; i++) {
            require(!_proofs[planIds[i]].exists, "Proof already exists");
            require(bytes(planIds[i]).length > 0, "Plan ID cannot be empty");
            require(planHashes[i] != bytes32(0), "Plan hash cannot be empty");
            
            _proofs[planIds[i]] = ProofOfExistence({
                planId: planIds[i],
                userId: userIds[i],
                planHash: planHashes[i],
                timestamp: timestamps[i],
                ipfsHash: ipfsHashes[i],
                blockNumber: block.number,
                exists: true
            });
            
            _userPlans[userIds[i]].push(planIds[i]);
            _proofCounter.increment();
            
            emit ProofOfExistenceCreated(
                planIds[i], 
                userIds[i], 
                planHashes[i], 
                timestamps[i], 
                ipfsHashes[i]
            );
        }
    }
}