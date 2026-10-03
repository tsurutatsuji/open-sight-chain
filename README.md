# open-sight-chain

**Machines see the world. Let them learn from it together — without handing raw footage to anyone, and with a tamper-proof record of who contributed what.**

[日本語版はこちら](README.ja.md)

> Status: **rough prototype (v0.0.1)**. The idea is published early on purpose.
> The architecture is open for debate. Pull requests that rewrite large parts are welcome.

---

## The idea

Cameras on robots, cars, phones, and workplaces capture huge amounts of footage every day. Almost none of it becomes training data, because:

1. **Raw footage can't leave the device** — privacy, contracts, bandwidth.
2. **Nobody can prove where data came from** — so buyers can't trust it and contributors can't get paid for it.
3. **Bad or poisoned data is hard to catch** once it's mixed in.

open-sight-chain combines three known pieces to address all three:

| Problem | Piece | What it does here |
|---|---|---|
| Raw data can't move | **Federated learning** | Each device trains locally and sends only model weights |
| Provenance can't be proven | **Hash-chained ledger** | Every round records data fingerprints, model hash, and contribution scores; tampering is detectable |
| Bad data sneaks in | **Contribution scoring** | Each update is scored by how much it helps the shared model; harmful updates are rejected |

```
 device A ──┐  weights + data hash            ┌── ledger node 1
 device B ──┼────────────────▶ aggregator ────┼── ledger node 2   (same chain on every node)
 device C ──┘   (raw frames stay on device)   └── ledger node 3
                    │
                    └─ FedAvg + leave-one-out contribution score → record → block
```

## What works today

| Stage | Component | File | Status |
|---|---|---|---|
| 1 | Hash-chained ledger with tamper detection | `osc/ledger.py` | ✅ working |
| 2 | Multiple nodes syncing over HTTP (longest valid chain) | `osc/node.py` | ✅ working |
| 3 | Federated learning + contribution scoring + poisoning rejection | `osc/fedlearn.py` | ✅ working (toy model) |
| 4 | On-chain provenance registry (smart contract) | `contracts/ProvenanceRegistry.sol` | 📐 design skeleton |
| 5 | Open network with incentives & Sybil resistance | — | 💡 open problem |

## Quick start

```bash
git clone https://github.com/tsurutatsuji/open-sight-chain
cd open-sight-chain
pip install -r requirements.txt   # numpy only
python demo.py
python -m unittest -v
```

Expected demo output (abridged):

```
[stage 2] 3 ledger nodes up
[stage 3] federated learning: 4 clients, 5 rounds
  round 1: val_acc=1.000 | device-0=+0.060, device-1=+0.065, device-2=+0.063, device-bad=-0.150 (rejected)
  ...
[stage 2] chain heads: {...} -> all nodes agree
[stage 1] tamper test: change device-bad's score in round 2 to +0.5
  before: (True, 'ok')
  after:  (False, 'block 2: stored hash does not match contents (tampered)')
```

## Where we need you

The prototype is deliberately small and readable. Every part has a clear next step — see [docs/ROADMAP.md](docs/ROADMAP.md).
Highlights:

- Replace the toy model with a real vision model (PyTorch / [Flower](https://flower.ai))
- Real P2P networking instead of HTTP polling
- Byzantine-robust aggregation (Krum, trimmed mean) instead of leave-one-out
- Deploy the provenance contract on a testnet
- Privacy: secure aggregation, differential privacy
- Proof that an update was actually computed on the claimed data

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), then open an issue or a PR.

## Prior work

This project stands on existing research, not a claim of novelty for the combination:
FedAvg (McMahan et al., 2017), BlockFL (Kim et al., 2019), Bittensor, Ocean Protocol, Flower.

## License

[Apache License 2.0](LICENSE). "open-sight-chain" is the project name maintained by [@tsurutatsuji](https://github.com/tsurutatsuji).
