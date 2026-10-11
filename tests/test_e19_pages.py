"""E19 (SPEC-SELFCAL v1.0 §10; session ELO-8, Phase 4): the fixed wording above every table, and the aggregate holds what
the deferred video session needs (the operator's addendum of 11 October 2026): each of the 100 players' rating on every
list under both systems, by FIDE ID and name, the two systems equal before the first self-calibrating table."""
import json
from pathlib import Path

from test_e17_pages import tables_without_the_wording

ROOT = Path(__file__).resolve().parents[1]
AGG = json.loads((ROOT / "analysis" / "aggregates" / "E19_top100_selfcal.json").read_text(encoding="utf-8"))


def test_every_table_carries_the_fixed_wording():
    text = (ROOT / "docs" / "evidence" / "E19_top100-selfcal.md").read_text(encoding="utf-8")
    assert "\n|" in text and tables_without_the_wording(text) == []


def test_every_player_has_a_rating_on_every_list_under_both_systems():
    rows = AGG["players_table"]
    lists = sorted(AGG["by_list"])
    assert len(rows) == 100 and len(lists) == 82 and lists[0] == "2020-01" and lists[-1] == "2026-10"
    first = f"{AGG['first_table_year']}-01"
    for r in rows:
        assert r["name"] and r["federation"] and sorted(r["series"]) == lists
        assert all(fide == sc for m, (fide, sc) in r["series"].items() if m < first)
        assert r["series"]["2026-10"] == [r["oct_2026"], r["selfcal"]]
        assert r["selfcal"] - r["oct_2026"] == r["difference"]


def test_the_validation_is_e17s():
    e17 = json.loads((ROOT / "analysis" / "aggregates" / "E17_top100.json").read_text(encoding="utf-8"))
    assert AGG["validation"] == e17["validation"] and AGG["validation_equals_e17"]
