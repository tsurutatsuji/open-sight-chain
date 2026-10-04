import time
import unittest
import urllib.request
import json

import numpy as np

from osc.fedlearn import IMG, Client, accuracy, make_frames, run_round
from osc.ledger import Chain
from osc.node import start_node
from osc.rewards import attach_rewards, payouts, rate


class TestLedger(unittest.TestCase):
    def test_valid_chain(self):
        c = Chain(difficulty=2)
        c.add_record({"a": 1})
        c.mine()
        c.add_record({"b": 2})
        c.mine()
        self.assertEqual(c.validate(), (True, "ok"))

    def test_tamper_detected(self):
        c = Chain(difficulty=2)
        c.add_record({"amount": 100})
        c.mine()
        c.mine()
        c.blocks[1].records[0]["amount"] = 999
        ok, reason = c.validate()
        self.assertFalse(ok)
        self.assertIn("tampered", reason)

    def test_relinked_tamper_detected(self):
        c = Chain(difficulty=2)
        c.add_record({"amount": 100})
        c.mine()
        c.mine()
        c.blocks[1].records[0]["amount"] = 999
        c.blocks[1].hash = c.blocks[1].compute_hash()  # attacker rehashes block 1
        ok, _ = c.validate()
        self.assertFalse(ok)  # block 2 link or PoW now fails

    def test_longest_valid_chain_wins(self):
        a, b = Chain(), Chain()
        b.blocks = list(a.blocks)
        b.mine()
        b.mine()
        self.assertTrue(a.replace_if_longer(b.blocks))
        self.assertEqual(len(a.blocks), 3)


class TestNodes(unittest.TestCase):
    def test_nodes_sync(self):
        urls = ["http://127.0.0.1:5201", "http://127.0.0.1:5202"]
        servers = [start_node(5201, [urls[1]])[1], start_node(5202, [urls[0]])[1]]
        self.addCleanup(lambda: [s.server_close() for s in servers])
        try:
            time.sleep(0.2)
            req = urllib.request.Request(f"{urls[0]}/records",
                                         data=json.dumps({"record": {"x": 1}}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req)
            urllib.request.urlopen(urllib.request.Request(f"{urls[0]}/mine", data=b"{}"))
            chains = [json.loads(urllib.request.urlopen(f"{u}/chain").read())["blocks"] for u in urls]
            self.assertEqual(len(chains[1]), 2)
            self.assertEqual(chains[0][-1]["hash"], chains[1][-1]["hash"])
        finally:
            for s in servers:
                s.shutdown()


class TestFederated(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        self.clients = [Client(f"c{i}", *make_frames(80, rng)) for i in range(3)]
        self.bad = Client("bad", *make_frames(80, rng), malicious=True)
        self.X_val, self.y_val = make_frames(300, rng)

    def test_learning_improves(self):
        w = np.zeros(IMG * IMG + 1)
        for _ in range(5):
            w, rec = run_round(w, self.clients, self.X_val, self.y_val)
        self.assertGreater(accuracy(w, self.X_val, self.y_val), 0.8)

    def test_poisoner_scores_negative_and_is_rejected(self):
        w = np.zeros(IMG * IMG + 1)
        for _ in range(3):
            w, rec = run_round(w, self.clients + [self.bad], self.X_val, self.y_val)
        bad = [c for c in rec["contributions"] if c["client"] == "bad"][0]
        self.assertLess(bad["score"], 0)
        self.assertFalse(bad["accepted"])

    def test_raw_data_not_in_record(self):
        w = np.zeros(IMG * IMG + 1)
        _, rec = run_round(w, self.clients, self.X_val, self.y_val)
        for c in rec["contributions"]:
            self.assertEqual(set(c), {"client", "data_hash", "n", "score", "accepted"})


class TestRewards(unittest.TestCase):
    def test_rate_halves(self):
        self.assertEqual([rate(r, 100, 2) for r in range(1, 6)], [100, 100, 50, 50, 25])

    def test_paid_by_size_of_improvement(self):
        contribs = [
            {"client": "a", "score": 0.03, "accepted": True},
            {"client": "b", "score": 0.01, "accepted": True},
            {"client": "bad", "score": -0.1, "accepted": False},
        ]
        p = payouts(contribs, 1000)
        self.assertAlmostEqual(p["a"], 30)
        self.assertAlmostEqual(p["b"], 10)
        self.assertEqual(p["bad"], 0.0)

    def test_nothing_positive_pays_nothing(self):
        contribs = [{"client": "a", "score": 0.0, "accepted": True},
                    {"client": "bad", "score": -0.1, "accepted": False}]
        self.assertEqual(payouts(contribs, 100), {"a": 0.0, "bad": 0.0})

    def test_early_rounds_pay_more_and_poisoner_earns_zero(self):
        rng = np.random.default_rng(1)
        clients = [Client(f"c{i}", *make_frames(80, rng)) for i in range(3)]
        clients.append(Client("bad", *make_frames(80, rng), malicious=True))
        X_val, y_val = make_frames(300, rng)
        w = np.zeros(IMG * IMG + 1)
        recs = []
        for r in range(1, 6):
            w, rec = run_round(w, clients, X_val, y_val)
            rec["round"] = r
            recs.append(attach_rewards(rec))
        self.assertGreater(recs[0]["rewards"]["c0"], recs[-1]["rewards"]["c0"])
        self.assertTrue(all(rec["rewards"]["bad"] == 0.0 for rec in recs))
        # later rounds pay less per unit of work too: scores shrink AND the rate halves
        self.assertGreater(recs[0]["minted"], recs[2]["minted"])
        self.assertGreater(recs[2]["minted"], recs[4]["minted"])

    def test_tampering_with_a_reward_is_detected(self):
        c = Chain(difficulty=2)
        c.add_record({"round": 1, "rewards": {"a": 50.0}})
        c.mine()
        c.mine()
        c.blocks[1].records[0]["rewards"]["a"] = 5000.0
        self.assertFalse(c.validate()[0])


if __name__ == "__main__":
    unittest.main()
