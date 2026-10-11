"""The proposal's Appendix G is the output of analysis/e17_summary_report.py --appendix, verbatim (session ELO-7, Phase 3).

Every number in the appendix comes from E17's aggregate through that script; this test fails if the proposal's copy and
the script's output part, so that the appendix cannot drift from the evidence."""
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


def test_appendix_g_is_the_scripts_output_verbatim():
    out = subprocess.run([sys.executable, str(ROOT / "analysis" / "e17_summary_report.py"), "--appendix"],
                         capture_output=True, text=True, check=True).stdout
    assert out == (ROOT / "analysis" / "OUTPUT_E17_appendix.md").read_text(encoding="utf-8")
    text = _latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")
    start = text.index("## Appendix G ")
    end = text.index("\n---\n", start)
    assert text[start:end].rstrip("\n") + "\n" == out

