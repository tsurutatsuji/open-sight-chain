"""Stage 2: several nodes sharing the same ledger over HTTP.

Standard library only. Each node keeps its own copy of the chain and syncs
with peers using the longest-valid-chain rule.

Endpoints:
  GET  /chain            -> full chain
  POST /records          -> add a record to the pending pool   {"record": {...}}
  POST /mine             -> pack pending records into a block, then tell peers
  POST /peers            -> register peers                     {"peers": ["http://..."]}
  POST /resolve          -> pull peers' chains, adopt the longest valid one

Run:  python -m osc.node --port 5001 --peers http://localhost:5002
"""

from __future__ import annotations

import argparse
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .ledger import Block, Chain


def _post(url: str, payload: dict | None = None, timeout: float = 3.0) -> dict:
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get(url: str, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


class Node:
    def __init__(self, difficulty: int = 2):
        self.chain = Chain(difficulty=difficulty)
        self.peers: set[str] = set()
        self.lock = threading.Lock()

    def resolve(self) -> bool:
        replaced = False
        for peer in list(self.peers):
            try:
                data = _get(f"{peer}/chain")
            except OSError:
                continue  # peer offline: skip, do not crash
            blocks = [Block.from_dict(b) for b in data["blocks"]]
            with self.lock:
                replaced |= self.chain.replace_if_longer(blocks)
        return replaced

    def broadcast_resolve(self) -> None:
        for peer in list(self.peers):
            try:
                _post(f"{peer}/resolve")
            except OSError:
                pass


def make_handler(node: Node):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep demo output clean
            pass

        def _send(self, obj: dict, code: int = 200) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            if self.path == "/chain":
                with node.lock:
                    self._send({"difficulty": node.chain.difficulty, "blocks": node.chain.to_list()})
            else:
                self._send({"error": "not found"}, 404)

        def do_POST(self):
            body = self._body()
            if self.path == "/records":
                with node.lock:
                    node.chain.add_record(body["record"])
                self._send({"pending": len(node.chain.pending)})
            elif self.path == "/mine":
                with node.lock:
                    block = node.chain.mine()
                node.broadcast_resolve()
                self._send({"block": block.to_dict()})
            elif self.path == "/peers":
                node.peers.update(body.get("peers", []))
                self._send({"peers": sorted(node.peers)})
            elif self.path == "/resolve":
                self._send({"replaced": node.resolve()})
            else:
                self._send({"error": "not found"}, 404)

    return Handler


def start_node(port: int, peers: list[str] | None = None, difficulty: int = 2):
    """Start a node in a background thread. Returns (node, server)."""
    node = Node(difficulty=difficulty)
    node.peers.update(peers or [])
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(node))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return node, server


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--peers", nargs="*", default=[])
    ap.add_argument("--difficulty", type=int, default=2)
    args = ap.parse_args()
    node = Node(difficulty=args.difficulty)
    node.peers.update(args.peers)
    print(f"node listening on http://127.0.0.1:{args.port}  peers={args.peers}")
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(node)).serve_forever()


if __name__ == "__main__":
    main()
