"""Stage 1: a minimal hash-chained ledger.

Each block stores a list of records (e.g. "node A contributed data with hash X")
and the hash of the previous block. Changing any past record changes that
block's hash, which breaks every link after it -> tampering is detectable.

This is intentionally simple. Proof-of-work here is a toy difficulty knob,
not a security mechanism. See docs/ROADMAP.md for what a real system needs.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


@dataclass
class Block:
    index: int
    prev_hash: str
    records: list[dict]
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        body = {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "records": self.records,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        return sha256(json.dumps(body, sort_keys=True))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Block":
        return Block(**d)


class Chain:
    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty
        self.blocks: list[Block] = [self._genesis()]
        self.pending: list[dict] = []

    def _genesis(self) -> Block:
        b = Block(index=0, prev_hash="0" * 64, records=[{"type": "genesis"}], timestamp=0.0)
        b.hash = b.compute_hash()
        return b

    @property
    def head(self) -> Block:
        return self.blocks[-1]

    def add_record(self, record: dict) -> None:
        self.pending.append(record)

    def mine(self) -> Block:
        """Pack pending records into a new block and append it."""
        block = Block(index=self.head.index + 1, prev_hash=self.head.hash, records=self.pending)
        prefix = "0" * self.difficulty
        block.hash = block.compute_hash()
        while not block.hash.startswith(prefix):
            block.nonce += 1
            block.hash = block.compute_hash()
        self.blocks.append(block)
        self.pending = []
        return block

    @staticmethod
    def is_valid(blocks: list[Block], difficulty: int) -> tuple[bool, str]:
        """Return (ok, reason). Checks every hash and every link."""
        prefix = "0" * difficulty
        for i, b in enumerate(blocks):
            if b.hash != b.compute_hash():
                return False, f"block {i}: stored hash does not match contents (tampered)"
            if i == 0:
                continue
            if b.prev_hash != blocks[i - 1].hash:
                return False, f"block {i}: prev_hash does not link to block {i - 1}"
            if not b.hash.startswith(prefix):
                return False, f"block {i}: proof-of-work not satisfied"
        return True, "ok"

    def validate(self) -> tuple[bool, str]:
        return Chain.is_valid(self.blocks, self.difficulty)

    def replace_if_longer(self, other: list[Block]) -> bool:
        """Longest-valid-chain rule (stage 2 consensus)."""
        ok, _ = Chain.is_valid(other, self.difficulty)
        if ok and len(other) > len(self.blocks):
            self.blocks = other
            return True
        return False

    def to_list(self) -> list[dict]:
        return [b.to_dict() for b in self.blocks]
