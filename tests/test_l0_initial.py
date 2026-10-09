"""A-4: initial ratings (SPEC-L0 R-26 to R-30; F-N01; the archived-rule fixtures F-I01 to F-I08)."""
from decimal import Decimal

import pytest

from l0_helpers import fixture, require_layer0

layer0 = require_layer0()
FN01 = fixture("fide_calculator", "published_initial_rating.json")["cases"][0]
FI = fixture("fide_calculator", "calculator_initial_rating.json")["cases"]


def event(results, first: bool = False, period: str = "2025-12"):
    return layer0.PoolEvent(period=period, results=tuple((int(r), Decimal(str(s))) for r, s in results), first_event=first)


def test_f_n01_first_published_rating():
    results = [(g["opponent_rating_used"], g["score"]) for g in FN01["games"]]
    assert layer0.initial_rating([event(results, first=True)]) == FN01["published_list"]["2025-12"]["rating"] == 1922


def test_fewer_than_five_games_is_not_published():
    assert layer0.initial_rating([event([(1800, 1), (1800, 1), (1800, 0.5), (1800, 0)], first=True)]) is None


def test_results_pool_across_events():
    a = event([(1800, 1), (1800, 1)], first=True, period="2025-11")
    b = event([(1800, 0.5), (1800, 0), (1800, 0)], period="2025-12")
    # Ra = (5 x 1800 + 3600) / 7 = 1800; p = 3.5 / 7 = .50; dp = 0
    assert layer0.initial_rating([a, b]) == 1800


def test_below_1400_is_not_published():
    # Ra = (5 x 1400 + 3600) / 7 = 1514.29; p = 1.5 / 7 = .21; dp = -230; Ru = 1284
    assert layer0.initial_rating([event([(1400, 0.5), (1400, 0), (1400, 0), (1400, 0), (1400, 0)], first=True)]) is None


def test_maximum_2200():
    # Ra = (5 x 2500 + 3600) / 7 = 2300; p = 6 / 7 = .86; dp = 309; Ru = 2609 -> 2200
    assert layer0.initial_rating([event([(2500, 1)] * 5, first=True)]) == 2200


def test_zero_in_the_first_event_is_disregarded():
    zero = event([(2000, 0), (2000, 0), (2000, 0)], first=True, period="2025-11")
    later = event([(1800, 1), (1800, 1), (1800, 0.5), (1800, 0), (1800, 0)], period="2025-12")
    assert layer0.initial_rating([zero, later]) == layer0.initial_rating([later]) == 1800


def test_zero_in_a_later_event_counts():
    first = event([(1800, 1), (1800, 1), (1800, 0.5), (1800, 0), (1800, 0)], first=True, period="2025-11")
    zero = event([(1800, 0), (1800, 0)], period="2025-12")
    # Ra = (7 x 1800 + 3600) / 9 = 1800; p = 3.5 / 9 = .39; dp = -80
    assert layer0.initial_rating([first, zero]) == 1720


def test_ru_half_is_rounded_up():
    """R-26 reading (NOT VERIFIED): Ra = (12004 + 3600) / 8 = 1950.5, p = 4 / 8 = .50, Ru = 1950.5 -> 1951."""
    results = [(2000, 1), (2000, 1), (2000, 0.5), (2000, 0.5), (2002, 0), (2002, 0)]
    assert layer0.initial_rating([event(results, first=True)]) == 1951


def scores(w: Decimal, n: int) -> list[Decimal]:
    whole = int(w)
    half = [Decimal("0.5")] if w - whole else []
    return [Decimal(1)] * whole + half + [Decimal(0)] * (n - whole - len(half))


@pytest.mark.parametrize("case", FI, ids=lambda c: c["id"])
def test_archived_rule_fixtures_are_not_reproduced(case):
    """The online calculator applies the archived rule [VT 2]; Layer 0 applies the current one (SPEC-L0 §6.1)."""
    i = case["inputs"]
    w, n = Decimal(str(i["W"])), i["N"]
    got = layer0.initial_rating([event([(i["Rc"], s) for s in scores(w, n)], first=True)])
    assert got == case["rule_2024"]["Ru"]
    if case["id"] == "F-I04":                     # 2100 + 100 under the archived rule equals the 2200 maximum
        assert got == case["calculator_initial_rating"]
    else:
        assert got != case["calculator_initial_rating"]
