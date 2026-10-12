"""The superseded Appendix G, as analysis/e17_summary_report.py --appendix writes it (session ELO-7, Phase 3), and the
proposal's Appendix G, one line pointing to the current replay, Appendix H [E19] (session ELO-13; docs/DECISIONS.md,
item 16).

Every number of the superseded appendix comes from E17's aggregate through that script; its output stays on record in
analysis/OUTPUT_E17_appendix.md, which check (a) regenerates. The proposal no longer carries it."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _latest(pattern: str) -> Path:
    def key(p: Path):
        m = re.search(r"_v(\d+)_(\d+)\.md$", p.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    return max(ROOT.glob(pattern), key=key)


def test_the_superseded_appendix_g_stays_on_record_as_the_script_writes_it():
    out = subprocess.run([sys.executable, str(ROOT / "analysis" / "e17_summary_report.py"), "--appendix"],
                         capture_output=True, text=True, check=True).stdout
    assert out == (ROOT / "analysis" / "OUTPUT_E17_appendix.md").read_text(encoding="utf-8")
    assert out.startswith("## Appendix G Today's top 100 under rung 2\n")


def test_the_proposals_appendix_g_is_one_line_pointing_to_the_current_replay():
    text = _latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")
    start = text.index("## Appendix G ")
    end = text.index("\n---\n", start)
    lines = [x for x in text[start:end].split("\n")[1:] if x.strip()]
    assert len(lines) == 1
    assert "Appendix H [E19]" in lines[0] and "[E17]" in lines[0]
    assert text.index("## Appendix G ") < text.index("## Appendix H ")
    # the superseded replay's table is gone from the proposal
    assert "| rank | FIDE ID | October 2026 | rung 2 |" not in text
