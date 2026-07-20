// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title AuditLogger
 * @dev Smart contract for immutable audit logging in financial planning system
 */
contract AuditLogger is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    struct AuditEvent {
        string eventId;
        string userId;
        string action;
        uint256 timestamp;
        bytes32 dataHash;
        string ipfsHash;
        uint256 blockNumber;
        bool exists;
    }
    
    // Events
    event AuditEventLogged(
        string indexed eventId,
        string indexed userId,
        string action,
        uint256 timestamp,
        bytes32 dataHash,
        string ipfsHash
    );
    
    event AuditEventVerified(
        string indexed eventId,
        bool verified,
        uint256 timestamp
    );
    
    // State variables
    Counters.Counter private _eventCounter;
    mapping(string => AuditEvent) private _auditEvents;
    mapping(string => string[]) private _userEvents;
    mapping(address => bool) private _authorizedLoggers;
    
    // Modifiers
    modifier onlyAuthorizedLogger() {
        require(_authorizedLoggers[msg.sender] || msg.sender == owner(), "Not authorized to log events");
        _;
    }
    
    modifier eventExists(string memory eventId) {
        require(_auditEvents[eventId].exists, "Audit event does not exist");
        _;
    }
    
    constructor() {
        _authorizedLoggers[msg.sender] = true;
    }
    
    /**
     * @dev Log an audit event to the blockchain
     * @param eventId Unique identifier for the event
     * @param userId User who performed the action
     * @param action Description of the action performed
     * @param timestamp Unix timestamp of the event
     * @param dataHash SHA-256 hash of the event data
     * @param ipfsHash IPFS hash for detailed event data storage
     */
    function logAuditEvent(
        string memory eventId,
        string memory userId,
        string memory action,
        uint256 timestamp,
        bytes32 dataHash,
        string memory ipfsHash
    ) external onlyAuthorizedLogger nonReentrant {
        require(!_auditEvents[eventId].exists, "Event ID already exists");
        require(bytes(eventId).length > 0, "Event ID cannot be empty");
        require(bytes(userId).length > 0, "User ID cannot be empty");
        require(bytes(action).length > 0, "Action cannot be empty");
        require(timestamp > 0, "Timestamp must be positive");
        require(dataHash != bytes32(0), "Data hash cannot be empty");
        
        _auditEvents[eventId] = AuditEvent({
            eventId: eventId,
            userId: userId,
            action: action,
            timestamp: timestamp,
            dataHash: dataHash,
            ipfsHash: ipfsHash,
            blockNumber: block.number,
            exists: true
        });
        
        _userEvents[userId].push(eventId);
        _eventCounter.increment();
        
        emit AuditEventLogged(eventId, userId, action, timestamp, dataHash, ipfsHash);
    }
    
    /**
     * @dev Retrieve an audit event by ID
     * @param eventId The event ID to retrieve
     * @return userId User who performed the action
     * @return action Description of the action
     * @return timestamp Unix timestamp of the event
     * @return dataHash SHA-256 hash of the event data
     * @return ipfsHash IPFS hash for detailed data
     * @return blockNumber Block number where event was logged
     */
    function getAuditEvent(string memory eventId) 
        external 
        view 
        eventExists(eventId)
        returns (
            string memory userId,
            string memory action,
            uint256 timestamp,
            bytes32 dataHash,
            string memory ipfsHash,
            uint256 blockNumber
        ) 
    {
        AuditEvent memory event = _auditEvents[eventId];
        return (
            event.userId,
            event.action,
            event.timestamp,
            event.dataHash,
            event.ipfsHash,
            event.blockNumber
        );
    }
    
    /**
     * @dev Get all audit event IDs for a specific user
     * @param userId The user ID to query
     * @return Array of event IDs for the user
     */
    function getUserAuditEvents(string memory userId) 
        external 
        view 
        returns (string[] memory) 
    {
        return _userEvents[userId];
    }
    
    /**
     * @dev Verify the integrity of an audit event
     * @param eventId The event ID to verify
     * @param dataHash The expected data hash
     * @return True if the event data integrity is verified
     */
    function verifyEventIntegrity(string memory eventId, bytes32 dataHash) 
        external 
        view 
        eventExists(eventId)
        returns (bool) 
    {
        bool verified = _auditEvents[eventId].dataHash == dataHash;
        emit AuditEventVerified(eventId, verified, block.timestamp);
        return verified;
    }
    
    /**
     * @dev Check if an audit event exists
     * @param eventId The event ID to check
     * @return True if the event exists
     */
    function eventExists(string memory eventId) external view returns (bool) {
        return _auditEvents[eventId].exists;
    }
    
    /**
     * @dev Get the total number of audit events logged
     * @return The total count of events
     */
    function getTotalEventCount() external view returns (uint256) {
        return _eventCounter.current();
    }
    
    /**
     * @dev Add an authorized logger address
     * @param logger Address to authorize for logging
     */
    function addAuthorizedLogger(address logger) external onlyOwner {
        _authorizedLoggers[logger] = true;
    }
    
    /**
     * @dev Remove an authorized logger address
     * @param logger Address to remove authorization from
     */
    function removeAuthorizedLogger(address logger) external onlyOwner {
        _authorizedLoggers[logger] = false;
    }
    
    /**
     * @dev Check if an address is authorized to log events
     * @param logger Address to check
     * @return True if the address is authorized
     */
    function isAuthorizedLogger(address logger) external view returns (bool) {
        return _authorizedLoggers[logger];
    }
    
    /**
     * @dev Batch log multiple audit events (gas optimization)
     * @param eventIds Array of event IDs
     * @param userIds Array of user IDs
     * @param actions Array of actions
     * @param timestamps Array of timestamps
     * @param dataHashes Array of data hashes
     * @param ipfsHashes Array of IPFS hashes
     */
    function batchLogAuditEvents(
        string[] memory eventIds,
        string[] memory userIds,
        string[] memory actions,
        uint256[] memory timestamps,
        bytes32[] memory dataHashes,
        string[] memory ipfsHashes
    ) external onlyAuthorizedLogger nonReentrant {
        require(eventIds.length == userIds.length, "Array length mismatch");
        require(eventIds.length == actions.length, "Array length mismatch");
        require(eventIds.length == timestamps.length, "Array length mismatch");
        require(eventIds.length == dataHashes.length, "Array length mismatch");
        require(eventIds.length == ipfsHashes.length, "Array length mismatch");
        require(eventIds.length <= 50, "Batch size too large");
        
        for (uint256 i = 0; i < eventIds.length; i++) {
            require(!_auditEvents[eventIds[i]].exists, "Event ID already exists");
            require(bytes(eventIds[i]).length > 0, "Event ID cannot be empty");
            require(bytes(userIds[i]).length > 0, "User ID cannot be empty");
            require(timestamps[i] > 0, "Timestamp must be positive");
            require(dataHashes[i] != bytes32(0), "Data hash cannot be empty");
            
            _auditEvents[eventIds[i]] = AuditEvent({
                eventId: eventIds[i],
                userId: userIds[i],
                action: actions[i],
                timestamp: timestamps[i],
                dataHash: dataHashes[i],
                ipfsHash: ipfsHashes[i],
                blockNumber: block.number,
                exists: true
            });
            
            _userEvents[userIds[i]].push(eventIds[i]);
            _eventCounter.increment();
            
            emit AuditEventLogged(
                eventIds[i], 
                userIds[i], 
                actions[i], 
                timestamps[i], 
                dataHashes[i], 
                ipfsHashes[i]
            );
        }
    }
}