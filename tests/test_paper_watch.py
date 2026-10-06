import datetime as dt
import unittest

from tools.paper_watch import collect, parse, to_markdown


def feed(*entries):
    body = "".join(
        f"<entry><id>http://arxiv.org/abs/{i}v1</id><title>{t}</title>"
        f"<published>{d}T00:00:00Z</published><summary>{s}</summary></entry>"
        for i, t, d, s in entries
    )
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{body}</feed>'.encode()


TODAY = dt.date(2026, 10, 6)
NEW_VLA = ("2610.00001", "Federated  VLA\n training", "2026-10-05", "We train robots.")
NEW_LEDGER = ("2610.00002", "Ledger for FL", "2026-10-05", "Hashes on chain.")
OLD = ("2609.00009", "Old paper", "2026-09-01", "Too old.")


class TestPaperWatch(unittest.TestCase):
    def test_parse_strips_version_and_whitespace(self):
        p = parse(feed(NEW_VLA))[0]
        self.assertEqual(p["id"], "2610.00001")
        self.assertEqual(p["title"], "Federated VLA training")
        self.assertEqual(p["published"], "2026-10-05")

    def test_old_and_already_posted_papers_are_skipped(self):
        searches = [("physical", "q")]
        fetcher = lambda q: feed(NEW_VLA, NEW_LEDGER, OLD)
        got = collect(3, TODAY, exclude="see 2610.00002", searches=searches, fetcher=fetcher, pause=0)
        self.assertEqual([p["id"] for p in got], ["2610.00001"])

    def test_paper_found_by_several_searches_is_listed_first(self):
        results = {"a": feed(NEW_LEDGER, NEW_VLA), "b": feed(NEW_VLA)}
        got = collect(3, TODAY, searches=[("ledger", "a"), ("physical", "b")],
                      fetcher=results.__getitem__, pause=0)
        self.assertEqual(got[0]["id"], "2610.00001")
        self.assertEqual(got[0]["parts"], {"ledger", "physical"})

    def test_markdown_lists_link_and_tags(self):
        got = collect(3, TODAY, searches=[("reward", "q")], fetcher=lambda q: feed(NEW_VLA), pause=0)
        md = to_markdown(got, TODAY)
        self.assertIn("https://arxiv.org/abs/2610.00001", md)
        self.assertIn("(2) reward", md)
        self.assertEqual(to_markdown([], TODAY), "")


if __name__ == "__main__":
    unittest.main()
