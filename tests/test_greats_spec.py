"""SPEC-GREATS v1.0 §2 (session ELO-9, Phase 2): the table of players is the output of analysis/greats_select.py
--table, verbatim, so that the names fixed before the analysis are the names the selection rule gives; and the
aggregate holds no rating."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "specs" / "SPEC-GREATS_v1_0.md"
AGG = ROOT / "analysis" / "aggregates" / "GREATS_players.json"


def test_the_specs_table_is_the_selection_scripts_output():
    out = subprocess.run([sys.executable, str(ROOT / "analysis" / "greats_select.py"), "--table"],
                         capture_output=True, text=True, check=True).stdout
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("<!-- GREATS-TABLE START -->\n") + len("<!-- GREATS-TABLE START -->\n")
    end = text.index("<!-- GREATS-TABLE END -->")
    assert text[start:end] == out


def test_the_selection_commits_no_rating():
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    keys = {k for p in agg["players"] for k in p}
    assert keys == {"key", "fide_id", "name", "federation", "lists_rank1", "lists_top3", "first_top3", "last_top3",
                    "best_rank"}
    assert all(1 <= p["best_rank"] <= 3 and p["lists_top3"] >= p["lists_rank1"] for p in agg["players"])
