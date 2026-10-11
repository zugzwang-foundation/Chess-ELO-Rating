"""SPEC-L0 v1.2 §11 (ruling R63, D-0014): the readings the replay of today's top 100 tested on FIDE's output, as tests.

The fixture, tests/fixtures/fide_history/tested_readings.json (tools/data/assemble_tested_readings.py), quotes single
figures from FIDE's published calculations and lists, without names, FIDE IDs or events:
  F-H06  R-14a: the 400-point rule of 1 March 2024 to 30 September 2025 read as the plain cap (NOT VERIFIED as text);
  F-H07  the 2017 rounding text read as away from zero (src/layer0_history/, beside R-25);
  F-H08  R-22b where K changes inside a period: FIDE used the K of the list in force at the tournament's start.
No rule of the engine changes (src/layer0/, Freeze 1); these tests record what FIDE's output shows."""
import json
from datetime import date
from decimal import Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402

FX = json.loads((ROOT / "tests" / "fixtures" / "fide_history" / "tested_readings.json").read_text(encoding="utf-8"))
CASE = {c["id"]: c for c in FX["cases"]}


def test_the_fixture_holds_the_three_readings_and_no_identifier():
    assert sorted(CASE) == ["F-H06", "F-H07", "F-H08"]
    rows = [r for c in FX["cases"] for k in ("tournaments", "periods") for r in c.get(k, [])]
    assert rows and all(set(r) <= {"differences", "fide_capped", "list", "sum", "published_change", "n", "k_previous_list",
                                   "k_start_list", "start_list_is_earlier", "k_fide"} for r in rows)


def test_r14a_march_2024_is_the_plain_cap_in_every_tournament_that_can_tell():
    tours = CASE["F-H06"]["tournaments"]
    assert len(tours) == 111
    ro = 2700                                       # only the differences matter below 2650 and before 1 October 2025
    for t in tours:
        assert len(t["differences"]) >= 2 and all(d > 400 for d in t["differences"])
        opponents = [ro - d for d in t["differences"]]
        plain = [abs(d) == 400 for d in lh.differences(ro, opponents, date(2024, 9, 1))]
        one_upgrade = [abs(d) == 400 for d in lh.differences(ro, opponents, date(2023, 6, 1))]
        assert plain == t["fide_capped"] == [True] * len(opponents)
        assert one_upgrade != t["fide_capped"]      # the 2022 clause would have capped the greatest difference only


def test_the_2017_rounding_is_away_from_zero_in_every_period_that_can_tell():
    periods = CASE["F-H07"]["periods"]
    assert len(periods) == 28
    for p in periods:
        s = Decimal(p["sum"])
        assert p["list"] < lh.ROUNDING_2022_LIST and s < 0 and abs(s) % 1 == Decimal("0.5")
        assert lh.round_change(s, p["list"]) == p["published_change"] == layer0.round_change(s)
        assert lh.round_change_literal_2017(s) == p["published_change"] + 1     # towards +infinity: refuted


def test_r22b_where_k_changes_inside_a_period_fide_used_the_start_lists_k():
    tours = CASE["F-H08"]["tournaments"]
    assert len(tours) == 2
    for t in tours:
        assert t["start_list_is_earlier"] and t["k_start_list"] != t["k_previous_list"]
        assert t["k_fide"] == layer0.k_for_period(t["k_start_list"], t["n"])
        assert t["k_fide"] != layer0.k_for_period(t["k_previous_list"], t["n"])   # R-22b as the engine reads it
