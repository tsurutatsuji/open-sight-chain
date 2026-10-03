# Architecture

## Roles

| Role | Holds | Sends | Never sends |
|---|---|---|---|
| **Device (client)** | raw frames, local model copy | weights, sample count, SHA-256 of its data | raw frames |
| **Aggregator** | global model, validation set | new global model, round record | — |
| **Ledger node** | full copy of the chain | blocks, chain on request | — |

In the prototype the aggregator runs in `demo.py` and writes to one ledger node. In a real network the aggregator role should itself be decentralized or verifiable (see ROADMAP).

## One round

1. Aggregator sends the current global weights to every device.
2. Each device trains locally (`local_train`) and returns an `Update`.
3. Aggregator scores each update by **leave-one-out log-loss**:
   `score = loss(model without this device) - loss(model with everyone)`.
   Positive = helped. Negative = hurt.
4. Updates with negative scores are dropped; the rest are averaged (**FedAvg**, weighted by sample count).
5. A record is written to the ledger:

```json
{
  "type": "fl_round",
  "round": 3,
  "model_hash": "…",
  "val_accuracy": 1.0,
  "contributions": [
    {"client": "device-0", "data_hash": "…", "n": 80, "score": 0.036, "accepted": true},
    {"client": "device-bad", "data_hash": "…", "n": 80, "score": -0.081, "accepted": false}
  ]
}
```

6. The node mines a block and tells its peers; peers adopt the longest valid chain.

## Ledger

- `Block.hash = sha256(index, prev_hash, records, timestamp, nonce)`
- Validation checks every stored hash, every `prev_hash` link, and the proof-of-work prefix.
- Proof-of-work here is a toy. It shows the mechanism, not real security.

## Known limitations (by design, for now)

| Limitation | Why it matters | Direction |
|---|---|---|
| Leave-one-out costs N extra evaluations per round | Doesn't scale to thousands of devices | Shapley approximation, robust aggregation |
| Aggregator owns the validation set | Single point of trust | Rotating / committee validation, on-chain commitments |
| `data_hash` proves nothing about training | A device can hash one dataset and train on another | Proof-of-learning, TEEs, zk proofs |
| HTTP with full-chain sync | Slow, not adversarial | libp2p, gossip, light clients |
| Toy PoW consensus | Not secure | Use an existing chain for anchoring (stage 4) |

## Stage 4: on-chain anchoring

Heavy work stays off-chain. Only small commitments go on-chain: round id, model hash, and a Merkle root of contribution records. See `contracts/ProvenanceRegistry.sol`.
