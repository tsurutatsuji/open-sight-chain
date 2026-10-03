// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

/// @title ProvenanceRegistry (stage 4 design skeleton — not audited, not deployed)
/// @notice Anchors one federated-learning round per call.
///         Only small commitments go on-chain; weights and data stay off-chain.
contract ProvenanceRegistry {
    struct Round {
        bytes32 modelHash;          // sha256 of the aggregated weights
        bytes32 contributionsRoot;  // Merkle root of per-device contribution records
        uint64 timestamp;
        address submitter;
    }

    mapping(uint256 => Round) public rounds;
    uint256 public latestRound;
    address public aggregator;

    event RoundAnchored(uint256 indexed roundId, bytes32 modelHash, bytes32 contributionsRoot);

    constructor(address _aggregator) {
        aggregator = _aggregator;
    }

    /// TODO(roadmap): replace single aggregator with a committee / threshold signature.
    function anchorRound(uint256 roundId, bytes32 modelHash, bytes32 contributionsRoot) external {
        require(msg.sender == aggregator, "only aggregator");
        require(roundId == latestRound + 1, "rounds must be sequential");
        rounds[roundId] = Round(modelHash, contributionsRoot, uint64(block.timestamp), msg.sender);
        latestRound = roundId;
        emit RoundAnchored(roundId, modelHash, contributionsRoot);
    }

    /// TODO(roadmap): verify a device's contribution with a Merkle proof,
    ///                then pay rewards proportional to its score.
}
