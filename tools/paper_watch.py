"""Paper watch: find new arXiv papers that matter for open-sight-chain.

Runs every day in GitHub Actions (.github/workflows/paper-watch.yml) and posts
the new papers to a weekly issue, so anyone can pick one and bring it into the
code. Standard library only.

Each search is tagged with the part of the project it informs:

    ledger   (1) protect the numbers: provenance, verification, blockchain
    reward   (2) pay for contribution: valuation, incentives, robust aggregation
    compute  (3) split the compute: federated / decentralized / low-communication training
    physical     robots, video, vision-language-action models

A paper found by several searches touches several parts and is listed first.

Run:  python tools/paper_watch.py --days 2 --exclude issue.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}

SEARCHES: list[tuple[str, str]] = [
    ("physical", 'all:"vision-language-action" AND all:federated'),
    ("physical", 'all:robot AND all:"federated learning"'),
    ("physical", 'all:"robot learning" AND all:decentralized'),
    ("compute", 'all:"decentralized training"'),
    ("compute", "all:DiLoCo"),
    ("compute", 'all:"low-communication" AND all:training'),
    ("compute", 'all:"federated fine-tuning" AND all:"language model"'),
    ("ledger", 'all:blockchain AND all:"federated learning"'),
    ("ledger", 'abs:"proof of learning" OR abs:"proof of training"'),
    ("ledger", 'abs:verifiable AND abs:decentralized AND abs:training'),
    ("reward", 'all:"contribution evaluation" AND all:federated'),
    ("reward", 'all:"incentive mechanism" AND all:"federated learning"'),
    ("reward", 'all:"byzantine" AND all:"federated learning"'),
    ("reward", 'all:"decentralized AI"'),
]

LABEL = {"ledger": "(1) ledger", "reward": "(2) reward", "compute": "(3) compute", "physical": "physical AI"}


def fetch(query: str, max_results: int = 50) -> bytes:
    params = urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    })
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": "open-sight-chain-paper-watch"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(feed: bytes) -> list[dict]:
    """Atom feed -> [{id, title, published, summary}]. id is the bare arXiv id (no version)."""
    papers = []
    for e in ET.fromstring(feed).findall("a:entry", NS):
        url = e.findtext("a:id", "", NS)
        papers.append({
            "id": re.sub(r"v\d+$", "", url.rsplit("/abs/", 1)[-1]),
            "title": " ".join(e.findtext("a:title", "", NS).split()),
            "published": e.findtext("a:published", "", NS)[:10],
            "summary": " ".join(e.findtext("a:summary", "", NS).split()),
        })
    return papers


def collect(days: int, today: dt.date, exclude: str = "", searches=SEARCHES, fetcher=fetch, pause: float = 3.0) -> list[dict]:
    """Run every search, keep papers published in the last `days` days that are
    not mentioned in `exclude`, and merge the part tags of duplicates."""
    since = (today - dt.timedelta(days=days)).isoformat()
    found: dict[str, dict] = {}
    for i, (part, query) in enumerate(searches):
        if i and pause:
            time.sleep(pause)  # arXiv asks for 3 seconds between calls
        for p in parse(fetcher(query)):
            if p["published"] < since or p["id"] in exclude:
                continue
            found.setdefault(p["id"], {**p, "parts": set()})["parts"].add(part)
    return sorted(found.values(), key=lambda p: (len(p["parts"]), p["published"]), reverse=True)


def to_markdown(papers: list[dict], today: dt.date) -> str:
    if not papers:
        return ""
    lines = [f"### New on {today.isoformat()} ({len(papers)})", ""]
    for p in papers:
        tags = " · ".join(LABEL[k] for k in LABEL if k in p["parts"])
        gist = p["summary"][:220] + ("…" if len(p["summary"]) > 220 else "")
        lines.append(f"- [ ] **{p['title']}** — [{p['id']}](https://arxiv.org/abs/{p['id']}) · {p['published']} · {tags}")
        lines.append(f"  > {gist}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=2, help="look back this many days")
    ap.add_argument("--exclude", help="text file; papers whose id appears in it are skipped")
    args = ap.parse_args()
    exclude = open(args.exclude, encoding="utf-8").read() if args.exclude else ""
    today = dt.datetime.now(dt.timezone.utc).date()
    sys.stdout.reconfigure(encoding="utf-8")  # titles contain non-ASCII; Windows consoles default to cp932 etc.
    sys.stdout.write(to_markdown(collect(args.days, today, exclude), today))


if __name__ == "__main__":
    main()
