"""The politeness rules of session ELO-9's fetches (ruling R75, docs/decisions/D-0017_rulings-on-the-greats.md): at
least four seconds between requests to ratings.fide.com (and FIDE's other hosts) and at least eight to the Internet
Archive, three to any other host, measured across runs and across tools from every manifest the session's fetch tools
keep. A manifest logs a request's UTC time in whole seconds at sending, so a logged time plus one second bounds the
request's true time from above. And the User-Agent with which every fetch tool outside the freezes identifies the
project (ruling R85, docs/decisions/D-0018_rulings-on-elo-9-questions.md, a founder decision; no email): the frozen
tools of Freeze 2 are not edited and keep their own. Python standard library only.
"""
from __future__ import annotations

import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (ROOT / "data" / "raw" / "probe" / "MANIFEST.tsv",
             ROOT / "data" / "raw" / "fide_old" / "MANIFEST.tsv",
             ROOT / "data" / "raw" / "fide_calculations_greats" / "MANIFEST.tsv",
             ROOT / "data" / "raw" / "fide_site" / "handbook" / "MANIFEST.tsv",
             ROOT / "data" / "fetch_log" / "ELO-D1.tsv",           # session ELO-D1's log (tools/data/fetch_sourcing.py)
             ROOT / "data" / "fetch_log" / "ELO-D2.tsv")           # session ELO-D2's log (the same tool)
MIN_GAP = {"ratings.fide.com": 4.0, "handbook.fide.com": 4.0, "www.fide.com": 4.0, "fide.com": 4.0,
           "web.archive.org": 8.0}
DEFAULT_GAP = 3.0
USER_AGENT = "Zugzwang-Elo-research (+https://github.com/zugzwang-foundation/Chess-ELO-Rating)"     # R85


def headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    """A request's headers: the project's User-Agent (R85), then any others the page itself sends."""
    return {"User-Agent": USER_AGENT, **(extra or {})}


def host_of(url: str) -> str:
    return urlparse(url.split(" ")[0]).netloc


def gap_for(host: str) -> float:
    return MIN_GAP.get(host, DEFAULT_GAP)


def last_request(host: str) -> float:
    """An upper bound, as epoch seconds, of the time of the last request to `host` that any manifest records."""
    last = 0.0
    for path in MANIFESTS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if host_of(r.get("url") or "") == host:
                    t = datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    last = max(last, t.timestamp() + 1)
    return last


def wait(host: str, last_in_run: float | None = None) -> None:
    """Sleep until the host's gap has passed since its last request, in this run (`last_in_run`, epoch seconds) or in
    any manifest."""
    last = max(last_request(host), last_in_run or 0.0)
    delay = last + gap_for(host) - time.time()
    if delay > 0:
        time.sleep(delay)
