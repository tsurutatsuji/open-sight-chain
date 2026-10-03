# Roadmap

Pick anything. Open an issue first for large changes so others can join.

## Good first issues

- [ ] Add a CLI flag to `demo.py` for number of clients / rounds / malicious clients
- [ ] Print a readable summary of the chain (`python -m osc.inspect`)
- [ ] Add type checking (mypy) and linting (ruff) to CI
- [ ] Persist the chain to disk (JSON) so nodes survive restarts
- [ ] Translate docs into more languages

## Learning (stage 3)

- [ ] Replace logistic regression with a small CNN (PyTorch)
- [ ] Integrate with [Flower](https://flower.ai) as the FL runtime
- [ ] Use a real image dataset (e.g. CIFAR-10 split non-IID across clients)
- [ ] Robust aggregation: Krum, coordinate-wise median, trimmed mean
- [ ] Scalable contribution scoring (Shapley value approximation)
- [ ] Secure aggregation and differential privacy

## Ledger & network (stages 1–2)

- [ ] Gossip-based block propagation instead of full-chain pull
- [ ] libp2p transport
- [ ] Merkle root of records in each block
- [ ] Replace toy PoW (or drop it and anchor to an existing chain)

## On-chain (stage 4)

- [ ] Hardhat / Foundry project for `contracts/ProvenanceRegistry.sol`
- [ ] Deploy to a public testnet (Sepolia)
- [ ] Python client that anchors each round's commitment

## Open problems (stage 5)

- [ ] Proof that an update was really trained on the data behind `data_hash`
- [ ] Sybil resistance: one person running many fake devices
- [ ] Decentralized validation set (who decides what "better" means?)
- [ ] Incentive design that rewards rare / valuable footage, not just volume
- [ ] Video-specific data: action labels, egocentric footage, robot demonstrations
