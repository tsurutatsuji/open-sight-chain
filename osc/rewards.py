"""Stage 3.5: rewards — pay for making the shared model better, more in the early days.

A device is paid for how much it improved the shared model:

    reward = rate(round) * score        (score = leave-one-out improvement, stage 3)

Two forces make early contributions worth more:

1. The rate halves every `halving_every` rounds (like Bitcoin's halving).
2. Scores shrink by themselves as the model gets better — there is less left
   to improve — so the same honest work earns less later on.

Rejected or non-positive updates get 0.

The rewards are written into the round record, so they end up inside a block
and are covered by the ledger's tamper detection (stage 1).

Amounts are plain numbers ("reward units"). No token, no chain payment yet —
that belongs to stage 4 (on-chain) and stage 5 (open network).
"""

from __future__ import annotations

INITIAL_RATE = 1000.0  # reward units per 1.0 drop in validation log-loss
HALVING_EVERY = 2  # short so the 5-round demo shows it; a real network would use a much longer period


def rate(round_no: int, initial: float = INITIAL_RATE, halving_every: int = HALVING_EVERY) -> float:
    """Reward per unit of improvement in a round. Rounds start at 1."""
    if round_no < 1:
        raise ValueError("round_no starts at 1")
    return initial / 2 ** ((round_no - 1) // halving_every)


def payouts(contributions: list[dict], unit_rate: float) -> dict[str, float]:
    """Pay each accepted device unit_rate * its positive score."""
    return {
        c["client"]: round(unit_rate * c["score"], 6) if c["accepted"] and c["score"] > 0 else 0.0
        for c in contributions
    }


def attach_rewards(record: dict, initial: float = INITIAL_RATE, halving_every: int = HALVING_EVERY) -> dict:
    """Add `rate`, `rewards` and `minted` to an fl_round record (needs record["round"])."""
    r = rate(record["round"], initial, halving_every)
    record["rate"] = r
    record["rewards"] = payouts(record["contributions"], r)
    record["minted"] = round(sum(record["rewards"].values()), 6)
    return record
