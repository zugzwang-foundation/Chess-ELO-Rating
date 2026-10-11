"""The proposal's Appendix I is the output of analysis/e20_greats_report.py --appendix, verbatim (session ELO-9, Phase 4):
every number in it comes from the greats' aggregates through that script, and this test fails if the proposal's copy and
the script's output part; every table carries SPEC-GREATS §1's wording with the era caveat and, where it uses
OlimpBase's lists, the credit line R77 asks for; the data limits and the permission route are stated."""
import re
import subprocess
import sys
from pathlib import Path

from test_e20_greats import tables_without_the_wording

ROOT = Path(__file__).resolve().parents[1]


def _latest(pattern: str) -> Path:
    def key(p: Path):
        m = re.search(r"_v(\d+)_(\d+)\.md$", p.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    return max(ROOT.glob(pattern), key=key)


def test_appendix_i_is_the_scripts_output_verbatim():
    out = subprocess.run([sys.executable, str(ROOT / "analysis" / "e20_greats_report.py"), "--appendix"],
                         capture_output=True, text=True, check=True).stdout
    assert out == (ROOT / "analysis" / "OUTPUT_E20_appendix.md").read_text(encoding="utf-8")
    text = _latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")
    start = text.index("## Appendix I ")
    end = text.index("\n---\n", start)
    assert text[start:end].rstrip("\n") + "\n" == out
    assert tables_without_the_wording(out) == []


def test_the_appendix_states_the_limits_and_the_permission_route():
    out = (ROOT / "analysis" / "OUTPUT_E20_appendix.md").read_text(encoding="utf-8")
    assert "## Appendix I The greats, on FIDE's own data" in out
    assert "**TWIC and Chessmetrics were not used**" in out
    assert "With written permission from TWIC, ChessBase or Chessmetrics, the full study becomes possible" in out
    assert "Lists to 2000: OlimpBase's transcription of FIDE's lists" in out          # R77, under the table using it
