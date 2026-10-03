"""End-to-end demo: 3 ledger nodes + 4 learning clients (1 of them poisons).

    python demo.py

1. Start 3 ledger nodes on localhost and connect them as peers.
2. Run federated learning rounds. Each round's model hash and per-client
   contribution scores are written to node 1 and mined into a block.
3. Nodes sync; all three end up holding the same chain.
4. Tamper with a past record and show that validation catches it.
"""

import json
import time
import urllib.request

import numpy as np

from osc.fedlearn import IMG, Client, make_frames, run_round
from osc.ledger import Block, Chain
from osc.node import start_node

PORTS = [5101, 5102, 5103]
ROUNDS = 5


def post(url, payload=None):
    req = urllib.request.Request(url, data=json.dumps(payload or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())


def get(url):
    return json.loads(urllib.request.urlopen(url).read())


def main():
    urls = [f"http://127.0.0.1:{p}" for p in PORTS]
    nodes = [start_node(p, [u for u in urls if u != urls[i]])[0] for i, p in enumerate(PORTS)]
    time.sleep(0.3)
    print(f"[stage 2] {len(nodes)} ledger nodes up: {', '.join(urls)}")

    rng = np.random.default_rng(0)
    clients = [Client(f"device-{i}", *make_frames(80, rng, noise=0.3 + 0.1 * i)) for i in range(3)]
    clients.append(Client("device-bad", *make_frames(80, rng), malicious=True))
    X_val, y_val = make_frames(300, rng)
    w = np.zeros(IMG * IMG + 1)

    print(f"[stage 3] federated learning: {len(clients)} clients, {ROUNDS} rounds")
    for r in range(1, ROUNDS + 1):
        w, record = run_round(w, clients, X_val, y_val)
        record["round"] = r
        post(f"{urls[0]}/records", {"record": record})
        post(f"{urls[0]}/mine")
        scores = ", ".join(f"{c['client']}={c['score']:+.3f}{'' if c['accepted'] else ' (rejected)'}"
                           for c in record["contributions"])
        print(f"  round {r}: val_acc={record['val_accuracy']:.3f} | {scores}")

    time.sleep(0.3)
    heads = {u: get(f"{u}/chain")["blocks"][-1]["hash"][:12] for u in urls}
    same = len(set(heads.values())) == 1
    print(f"[stage 2] chain heads: {heads} -> {'all nodes agree' if same else 'MISMATCH'}")

    print("[stage 1] tamper test: change device-bad's score in round 2 to +0.5")
    data = get(f"{urls[1]}/chain")
    blocks = [Block.from_dict(b) for b in data["blocks"]]
    print(f"  before: {Chain.is_valid(blocks, data['difficulty'])}")
    blocks[2].records[0]["contributions"][-1]["score"] = 0.5
    print(f"  after:  {Chain.is_valid(blocks, data['difficulty'])}")


if __name__ == "__main__":
    main()
