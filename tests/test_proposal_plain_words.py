"""The proposal and the brief speak plainly (session ELO-12, the one review before submission): no ruling number,
decision record or session name, no "ruling" or "session", and no freeze, in the proposal (front matter, body and
appendices) or the brief. The technical annex keeps its references; the evidence pages and the decision records keep
theirs."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESS = re.compile(r"\bR\d+\b|\bD-\d{4}\b|\bELO-\d+[a-z]?\b|\b[Rr]ulings?\b|\b[Ss]essions?\b|\b[Ff]reez\w*")


def _latest(pattern: str) -> Path:
    def key(p: Path):
        m = re.search(r"_v(\d+)_(\d+)\.md$", p.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    return max(ROOT.glob(pattern), key=key)


def _hits(text: str) -> list[tuple[int, str]]:
    return [(n, m.group()) for n, line in enumerate(text.split("\n"), 1) for m in PROCESS.finditer(line)]


def test_the_proposal_carries_no_ruling_record_session_or_freeze():
    assert _hits(_latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")) == []


def test_the_brief_carries_no_ruling_record_session_or_freeze():
    assert _hits(_latest("docs/proposal/ELO-BRIEF_v*_*.md").read_text(encoding="utf-8")) == []
