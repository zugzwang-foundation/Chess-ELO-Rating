"""E20 (SPEC-GREATS v1.0; session ELO-9, Phase 3): the fixed wording of SPEC-GREATS §1, the era caveat included, above
every table of the evidence page and of the proposal's appendix; the aggregates hold no list and no series of FIDE's
published ratings (R72): per player one peak (§4), the highest rating within the replay's window under each system
(§6), and differences."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e20_greats_report as rep  # noqa: E402

LISTS = json.loads((ROOT / "analysis" / "aggregates" / "E20_greats_lists.json").read_text(encoding="utf-8"))
REPLAY = json.loads((ROOT / "analysis" / "aggregates" / "E20_greats_replay.json").read_text(encoding="utf-8"))


def tables_without_the_wording(text: str) -> list[str]:
    """The first row of every table whose last non-blank line before it is not the fixed wording."""
    lines = text.split("\n")
    bad = []
    for i, s in enumerate(lines):
        if s.startswith("|") and (i == 0 or not lines[i - 1].startswith("|")):
            before = [x for x in lines[:i] if x.strip()]
            if not before or before[-1] != rep.FIXED:
                bad.append(s)
    return bad


def test_the_wording_is_spec_greats():
    spec = (ROOT / "docs" / "specs" / "SPEC-GREATS_v1_0.md").read_text(encoding="utf-8")
    assert "> " + rep.FIXED in spec
    assert "A rating measures strength against one's own era." in rep.FIXED


def test_every_table_carries_the_fixed_wording():
    for page in ("docs/evidence/E20_greats.md", "analysis/OUTPUT_E20_appendix.md"):
        text = (ROOT / page).read_text(encoding="utf-8")
        assert "\n|" in text and tables_without_the_wording(text) == [], page


def _keys(o, out=None) -> set:
    out = set() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(k)
            _keys(v, out)
    elif isinstance(o, list):
        for v in o:
            _keys(v, out)
    return out


def test_no_list_and_no_series_of_published_ratings():
    allowed = {"best_by_gap10", "best_by_gap2", "federation", "fide_id", "first_list", "key", "last_list", "lists",
               "lists_rank1", "lists_top10", "lists_top3", "name", "peak", "peak_lists"}
    for p in LISTS["players"]:
        assert set(p) <= allowed, p["name"]
        assert isinstance(p["peak"], int) and all(len(m) == 7 for m in p["peak_lists"])
    assert "series" not in _keys(REPLAY)
    assert set(LISTS["lists"]["series"]) == {"dates", "first", "last"}       # a count of the series' dates, no rating
    for r in REPLAY["players"]:
        for k in ("highest_layer0", "highest_rung2", "highest_rung2_no_colour"):
            assert set(r[k]) == {"rating", "lists"} and isinstance(r[k]["rating"], int)
        assert all(isinstance(d, int) and abs(d) < 400 for d in r["year_end_difference"].values())   # differences
        assert r["difference"] == r["year_end_difference"].get("2019", r["difference"])


def test_the_replay_covers_the_window_it_names():
    w = REPLAY["window"]
    assert (w["start_list"], w["first"], w["last"]) == ("2008-01", "2008-04", "2019-12")
    assert REPLAY["table"]["label"] == "applied backwards, not fitted on that era"
    assert REPLAY["pages"]["read"] == REPLAY["pages"]["planned"] and not REPLAY["pages"]["missing"]


def test_r79_the_replay_commits_counts_only():
    # R79 (D-0017): the full reproduction runs locally from the cache; the aggregate keeps its counts, and per player
    # only the lists of the thin periods with their causes, which SPEC-GREATS §6 asks E20 to list.
    assert "validation_detail" not in REPLAY
    assert all(isinstance(n, int) for n in REPLAY["validation"].values())
    for r in REPLAY["players"]:
        assert all(len(t) == 2 and len(t[0]) == 7 for t in r["thin"])
    for c in REPLAY["checked_with_next_file"]:
        assert len(c) == 4 and c[3] in ("reproduced", "not reproduced")


def test_r74_both_readings_and_the_third_are_reported():
    rd = REPLAY["readings"]
    assert set(rd) == {"R74", "rules record", "towards +infinity throughout"}
    assert rd["R74"]["thin_periods"] == REPLAY["summary"]["thin_periods"]
    assert rd["R74"]["mean_difference"] == REPLAY["summary"]["mean_difference"]
    early = REPLAY["rounding"]["lists to June 2014 (no clause)"]
    # R74's reading is the better of the two on the lists before July 2014 (towards +infinity there)
    assert early["reproduced"] == early["reproduced_towards_plus_infinity"] >= early["reproduced_away_from_zero"]
