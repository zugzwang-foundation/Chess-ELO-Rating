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
               "lists_rank1", "lists_top10", "lists_top3", "name", "peak", "peak_lists",
               "top3_only_by_a_shared_third", "top3_lists_shared_third", "absent_from_lists_in_span"}   # dates, flags
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


def test_r80_and_the_other_readings_are_reported():
    # R80 (D-0018): E20 prints the thin periods and §5's mean under D-0017's reading and under R80's, which §5 uses;
    # R74 asks for the rules record's first reading; the fourth is for information only (D-0017 reading 2).
    rd = REPLAY["readings"]
    assert set(rd) == {"R80", "D-0017", "rules record", "towards +infinity throughout"}
    assert rd["R80"]["thin_periods"] == REPLAY["summary"]["thin_periods"]
    assert rd["R80"]["mean_difference"] == REPLAY["summary"]["mean_difference"]
    assert rd["R80"]["thin_periods"] <= min(x["thin_periods"] for x in rd.values())
    rnd = REPLAY["rounding"]
    early = rnd["lists to June 2014 (the 2007 and 2010 texts)"]
    # towards +infinity on the lists before July 2014 (R74) and to October 2018 (R80); away from zero after (R80)
    assert early["reproduced"] == early["reproduced_towards_plus_infinity"] >= early["reproduced_away_from_zero"]
    for era in ("lists of July 2014 to June 2017 (the 2014 clause)", "lists of July 2017 to October 2018 (the 2017 clause)"):
        assert rnd[era]["half_negative_away_from_zero"] == 0 < rnd[era]["half_negative_towards_plus_infinity"]
    late = rnd["lists from November 2018 (the 2017 clause)"]
    assert late["half_negative_towards_plus_infinity"] == 0 < late["half_negative_away_from_zero"]
    nh = REPLAY["negative_half_points"]
    assert nh["from_july_2014"]["last_list_towards_plus_infinity"] < "2018-11" <= nh["from_july_2014"]["first_list_away_from_zero"]
    between = nh["lists_between_the_last_up_and_the_first_away"]
    assert between and all(b["negative_half_points"] == 0 for b in between)     # the switch's list is not dated


def test_no_unrendered_placeholder_in_the_generated_pages():
    # ELO9-QC-4: a string missing its f prefix printed "{rdg['R74']...}" into E20; no generated page may carry one.
    import re
    for page in ("docs/evidence/E20_greats.md", "analysis/OUTPUT_E20_appendix.md", "docs/research/DATA-PROBE_greats.md",
                 "docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md"):
        text = (ROOT / page).read_text(encoding="utf-8")
        assert not re.search(r"\{[A-Za-z_][A-Za-z0-9_]*(\[|\(|\.|:|\})", text), page
