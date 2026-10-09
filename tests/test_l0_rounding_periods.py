"""SPEC-L0 §8 Q-1 evidence (D-0008, R10): multi-event periods from FIDE's published calculations, F-Mnn.

Each case is a rating period in which FIDE's published calculation for one adult
shows two or more tournaments. The engine in src/layer0 is not changed by these
fixtures: they check its arithmetic (R-16, R-17, R-22b, R-23, R-24) on every game
and tournament, and record, per period, which rounding of R-25 reproduces the
published list (`list_follows`), so that the evidence for Q-1 is executable.
"""
from datetime import date
from decimal import Decimal

import pytest

from l0_helpers import fixture, month_before, require_layer0

layer0 = require_layer0()
DATA = fixture("fide_calculator", "published_multi_event_periods.json")
CASES = DATA["cases"]


def period_k(case: dict) -> int:
    n = sum(int(t["n"]) for t in case["tournaments"])
    return layer0.k_for_period(case["published_list_k"][month_before(case["rating_period"])], n)


def deltas(t: dict) -> list[Decimal]:
    start = date.fromisoformat(t["start"])
    return [layer0.game_delta(int(t["Ro"]), int(g["opponent_rating_used"]), Decimal(g["score"]), "standard", start)
            for g in t["games"]]


def test_fixtures_are_multi_event_adult_periods():
    assert len(CASES) >= 5                                               # R10: at least five more multi-event periods
    for c in CASES:
        assert len(c["tournaments"]) >= 2
        assert c["birth_year"] <= 2007


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_every_game_sum_and_k(case):
    k = period_k(case)                                                   # R-22b, R-23
    for t in case["tournaments"]:
        ds = deltas(t)
        assert ds == [Decimal(g["chg"]) for g in t["games"]]             # R-16, R-17
        assert sum(ds) == Decimal(t["chg"])                              # R-11
        assert k == int(t["K"])
        assert k * sum(ds) == Decimal(t["K_chg"])                        # R-24
    assert sum(Decimal(t["K_chg"]) for t in case["tournaments"]) == Decimal(case["total_change_shown"])


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_both_roundings_and_what_the_list_follows(case):
    pc = layer0.period_change([(str(t["event_id"]), deltas(t)) for t in case["tournaments"]], period_k(case))
    assert pc.rounded == case["change_rounded_per_period"]               # R-25 as written
    assert pc.rounded_per_tournament == case["change_rounded_per_tournament"]
    change = case["published_change"]
    lists = case["published_list_ratings"]
    assert change == lists[case["rating_period"]] - lists[month_before(case["rating_period"])]
    expected = ("both" if pc.rounded == pc.rounded_per_tournament == change else "period" if pc.rounded == change
                else "tournament" if pc.rounded_per_tournament == change else "neither")
    assert case["list_follows"] == expected
