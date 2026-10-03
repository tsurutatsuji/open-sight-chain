"""Stage 3: federated learning — train on each device, share only the weights.

Each client holds its own "camera frames" (raw data never leaves the client).
It trains a small model locally and sends back only:
  - the updated weights
  - the number of samples it used
  - a SHA-256 fingerprint of its data (for the provenance ledger)

The server averages the weights (FedAvg, McMahan et al. 2017) and scores each
client's contribution by how much the global model gets worse without it
(leave-one-out). Contributions are written to the ledger (stage 1/2).

The model is plain logistic regression in numpy so the whole loop is readable.
Swapping in a real vision model (PyTorch / Flower) is a roadmap item.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ledger import sha256

IMG = 8  # frames are IMG x IMG grayscale


# ---------- synthetic "what the AI saw" ----------

def make_frames(n: int, rng: np.random.Generator, noise: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """Toy camera frames: an object (vertical bar) seen on the left (label 0)
    or the right (label 1) half of the view."""
    X = rng.normal(0.0, noise, size=(n, IMG, IMG))
    y = rng.integers(0, 2, size=n)
    half = IMG // 2
    for i in range(n):
        k = rng.integers(0, half) + (half if y[i] == 1 else 0)
        X[i, :, k] += 1.0
    return X.reshape(n, -1), y.astype(float)


# ---------- model ----------

def predict(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    z = X @ w[:-1] + w[-1]
    return 1.0 / (1.0 + np.exp(-z))


def accuracy(w: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
    return float(((predict(w, X) > 0.5) == y).mean())


def log_loss(w: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(predict(w, X), 1e-9, 1 - 1e-9)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def local_train(w: np.ndarray, X: np.ndarray, y: np.ndarray, epochs: int = 5, lr: float = 0.5) -> np.ndarray:
    w = w.copy()
    for _ in range(epochs):
        err = predict(w, X) - y
        w[:-1] -= lr * X.T @ err / len(y)
        w[-1] -= lr * err.mean()
    return w


# ---------- clients & server ----------

@dataclass
class Update:
    client_id: str
    weights: np.ndarray
    n_samples: int
    data_hash: str


class Client:
    def __init__(self, client_id: str, X: np.ndarray, y: np.ndarray, malicious: bool = False):
        self.client_id = client_id
        self.X, self.y = X, y
        self.malicious = malicious

    def data_hash(self) -> str:
        return sha256(self.X.tobytes() + self.y.tobytes())

    def train(self, global_w: np.ndarray) -> Update:
        y = 1.0 - self.y if self.malicious else self.y  # poisoner flips labels
        w = local_train(global_w, self.X, y)
        return Update(self.client_id, w, len(self.y), self.data_hash())


def fedavg(updates: list[Update]) -> np.ndarray:
    total = sum(u.n_samples for u in updates)
    return sum(u.weights * (u.n_samples / total) for u in updates)


def contributions(updates: list[Update], X_val: np.ndarray, y_val: np.ndarray) -> dict[str, float]:
    """Leave-one-out: loss(without this client) - loss(with everyone).
    Positive = helped, negative = hurt (possible poisoning).
    Log-loss is used instead of accuracy because accuracy saturates at 100%."""
    full = log_loss(fedavg(updates), X_val, y_val)
    scores = {}
    for u in updates:
        rest = [v for v in updates if v is not u]
        scores[u.client_id] = round(log_loss(fedavg(rest), X_val, y_val) - full, 4) if rest else 0.0
    return scores


def run_round(global_w, clients, X_val, y_val, drop_negative: bool = True):
    """One federated round. Returns (new_weights, record_for_ledger)."""
    updates = [c.train(global_w) for c in clients]
    scores = contributions(updates, X_val, y_val)
    accepted = [u for u in updates if not drop_negative or scores[u.client_id] >= 0] or updates
    new_w = fedavg(accepted)
    record = {
        "type": "fl_round",
        "model_hash": sha256(new_w.tobytes()),
        "val_accuracy": round(accuracy(new_w, X_val, y_val), 4),
        "contributions": [
            {"client": u.client_id, "data_hash": u.data_hash, "n": u.n_samples,
             "score": scores[u.client_id], "accepted": u in accepted}
            for u in updates
        ],
    }
    return new_w, record
