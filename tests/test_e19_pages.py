"""E19 (SPEC-SELFCAL v1.0 §10, v1.2 §10; sessions ELO-8 and ELO-9): the fixed wording above every table, and the aggregate
holds, for each of the 100 players on every list, only the difference between the two systems, by FIDE ID and name, zero
before the first self-calibrating table (R72, D-0016): FIDE's published ratings are committed for October 2026 only, for
E19 §2 and Appendix H; both systems' series stay in the local cache under data/."""
import json
from pathlib import Path

from test_e17_pages import tables_without_the_wording

ROOT = Path(__file__).resolve().parents[1]
AGG = json.loads((ROOT / "analysis" / "aggregates" / "E19_top100_selfcal.json").read_text(encoding="utf-8"))


def test_every_table_carries_the_fixed_wording():
    text = (ROOT / "docs" / "evidence" / "E19_top100-selfcal.md").read_text(encoding="utf-8")
    assert "\n|" in text and tables_without_the_wording(text) == []


def test_every_player_has_only_the_difference_on_every_list():
    rows = AGG["players_table"]
    lists = sorted(AGG["by_list"])
    assert len(rows) == 100 and len(lists) == 82 and lists[0] == "2020-01" and lists[-1] == "2026-10"
    first = f"{AGG['first_table_year']}-01"
    for r in rows:
        assert r["name"] and r["federation"] and sorted(r["series"]) == lists
        assert all(isinstance(d, int) for d in r["series"].values())          # R72: no published rating per list
        assert all(d == 0 for m, d in r["series"].items() if m < first)
        assert r["series"]["2026-10"] == r["difference"] == r["selfcal"] - r["oct_2026"]


def test_the_validation_is_e17s():
    e17 = json.loads((ROOT / "analysis" / "aggregates" / "E17_top100.json").read_text(encoding="utf-8"))
    assert AGG["validation"] == e17["validation"] and AGG["validation_equals_e17"]
