"""The proposal's Appendix H is the output of analysis/e19_top100_selfcal_report.py --appendix, verbatim (session ELO-8,
Phase 6): every number in it comes from E18's and E19's aggregates through that script, and this test fails if the
proposal's copy and the script's output part."""
import re
import subprocess
import sys
from pathlib import Path

from test_e17_pages import tables_without_the_wording

ROOT = Path(__file__).resolve().parents[1]


def _latest(pattern: str) -> Path:
    def key(p: Path):
        m = re.search(r"_v(\d+)_(\d+)\.md$", p.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    return max(ROOT.glob(pattern), key=key)


def test_appendix_h_is_the_scripts_output_verbatim():
    out = subprocess.run([sys.executable, str(ROOT / "analysis" / "e19_top100_selfcal_report.py"), "--appendix"],
                         capture_output=True, text=True, check=True).stdout
    assert out == (ROOT / "analysis" / "OUTPUT_E19_appendix.md").read_text(encoding="utf-8")
    text = _latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")
    start = text.index("## Appendix H ")
    end = text.index("\n---\n", start)
    assert text[start:end].rstrip("\n") + "\n" == out
    assert tables_without_the_wording(out) == []
