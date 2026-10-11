"""R70 (D-0016; session ELO-9, Phase 0b): the name match of analysis/e18_name_match_extract.py, on a synthetic roster,
and the committed counts: no game of 2020 to 2023 carries a federation tag, so none matches."""
import json
import sys

from l0_helpers import ROOT

sys.path.insert(0, str(ROOT / "analysis"))
import e18_name_match_extract as nm  # noqa: E402


def test_the_match_needs_the_name_the_federation_and_an_elo_tag_within_ten_points():
    players = {(nm.ex.norm("Carlsen, Magnus"), "NOR"): [("1503014", 2830)],
               (nm.ex.norm("Doe, John"), "USA"): [("1", 2000), ("2", 2005)]}
    assert nm.match("Magnus Carlsen", "NOR", "2840", players) == "1503014"
    assert nm.match("Magnus Carlsen", "NOR", "2841", players) is None      # 11 points away
    assert nm.match("Magnus Carlsen", None, "2830", players) is None       # no federation, no match
    assert nm.match("Magnus Carlsen", "USA", "2830", players) is None      # another federation
    assert nm.match("Magnus Carlsen", "NOR", "", players) is None          # no Elo tag
    assert nm.match("John Doe", "USA", "2003", players) is None            # two within 10 points: not unique
    assert nm.match("John Doe", "USA", "1992", players) == "1"


def test_a_federation_is_read_only_from_a_tag_that_names_one():
    assert nm.federations({"WhiteFed": "nor", "BlackCountry": "USA"}) == ("NOR", "USA")
    assert nm.federations({"WhiteTeam": "Norway", "WhiteElo": "2800", "BlackTitle": "GM"}) == (None, None)


def test_the_committed_counts_find_no_federation_tag_and_no_match():
    agg = json.loads((ROOT / "analysis" / "aggregates" / "E18_name_match.json").read_text(encoding="utf-8"))
    assert agg["matched_games"] == 0 and sorted(agg["by_year"]) == ["2020", "2021", "2022", "2023"]
    assert all(v["both_federation_tags"] == 0 and v["matched"] == 0 for v in agg["by_year"].values())
    assert not any(nm.FED_TAG.match(k) for k in agg["player_tags_in_files"])
    cov = json.loads((ROOT / "analysis" / "aggregates" / "E18_coverage.json").read_text(encoding="utf-8"))
    for y, v in agg["by_year"].items():       # the same games E18 §1 counts
        assert v["games"] == cov["archive_by_year"]["with_result_standard_variant"][y]
        assert v["games"] - v["without_both_fide_ids"] == cov["archive_by_year"]["both_fide_ids"][y]
