"""A-3: FIDE's published calculations F-P01 to F-P05 (SPEC-L0 R-11, R-11a, R-11b, R-14, R-16, R-17, R-22b, R-23, R-24, R-25)."""
from datetime import date
from decimal import Decimal

import pytest

from l0_helpers import fixture, month_before, require_layer0

layer0 = require_layer0()
CASES = fixture("fide_calculator", "published_calculations.json")["cases"]
BY_ID = {c["id"]: c for c in CASES}
# Which rounding reproduces the published list (SPEC-L0 R-25, §8 Q-1).
LIST_ROUNDING = {"F-P01": "period", "F-P02": "tournament", "F-P03": "period", "F-P04": "period", "F-P05": "period"}


def period_k(case: dict) -> int:
    n = sum(int(t["n"]) for t in case["tournaments"])
    return layer0.k_for_period(case["published_list_k"][month_before(case["rating_period"])], n)


def deltas(t: dict) -> list[Decimal]:
    start = date.fromisoformat(t["start"])
    return [layer0.game_delta(int(t["Ro"]), int(g["opponent_rating_used"]), Decimal(g["score"]), "standard", start)
            for g in t["games"]]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_every_game_sum_and_k(case):
    k = period_k(case)                                                   # R-22b, R-23
    for t in case["tournaments"]:
        ds = deltas(t)
        assert ds == [Decimal(g["chg"]) for g in t["games"]]             # R-16, R-17
        assert sum(ds) == Decimal(t["chg"])                              # R-11
        assert k == int(t["K"])
        assert k * sum(ds) == Decimal(t["K_chg"])                        # R-24


def test_r23_reduces_k_for_39_games():
    case = BY_ID["F-P05"]
    assert case["published_list_k"]["2026-09"] == 20
    assert period_k(case) == 17


def test_r14_both_sides_of_one_game():
    """F-P01 (rated 2813) and F-P02 (rated 2400) met in event 435715, starting 2025-11-07."""
    top = next(t for t in BY_ID["F-P01"]["tournaments"] if t["event_id"] == 435715)
    low = next(t for t in BY_ID["F-P02"]["tournaments"] if t["event_id"] == 435715)
    r_top, r_low, start = int(top["Ro"]), int(low["Ro"]), date(2025, 11, 7)
    g_top = next(g for g in top["games"] if int(g["opponent_rating_used"]) == r_low)
    g_low = next(g for g in low["games"] if g["capped_marker"] and int(g["opponent_rating_used"]) == r_low + 400)
    assert layer0.effective_difference(r_top, r_low, "standard", start) == 413
    assert layer0.effective_difference(r_low, r_top, "standard", start) == -400
    assert layer0.game_delta(r_top, r_low, Decimal(g_top["score"]), "standard", start) == Decimal(g_top["chg"])
    assert layer0.game_delta(r_low, r_top, Decimal(g_low["score"]), "standard", start) == Decimal(g_low["chg"])


def test_r11a_events_use_the_list_in_force_at_their_start():
    for cid in ("F-P02", "F-P03"):
        case = BY_ID[cid]
        aca = next(t for t in case["tournaments"] if t["start"] == "2025-10-31")
        assert layer0.list_in_force(date.fromisoformat(aca["start"])) == "2025-10"
        assert int(aca["Ro"]) == case["published_list_ratings"]["2025-10"]
        assert int(aca["Ro"]) != case["published_list_ratings"]["2025-11"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_new_rating_on_the_list(case):
    prev = month_before(case["rating_period"])
    pc = layer0.period_change([(str(t["event_id"]), deltas(t)) for t in case["tournaments"]], period_k(case))
    assert pc.change == sum(Decimal(t["K_chg"]) for t in case["tournaments"])
    base = case["published_list_ratings"][prev]
    if case["id"] == "F-P04":                                            # R-11b: FIDE starts from 2053, the list says 2052
        assert {int(t["Ro"]) for t in case["tournaments"]} == {base + 1}
        base += 1
    new = base + (pc.rounded if LIST_ROUNDING[case["id"]] == "period" else pc.rounded_per_tournament)
    assert new == case["published_list_ratings"][case["rating_period"]]


def test_q1_the_two_roundings_disagree_on_f_p02_and_f_p05():
    """SPEC-L0 §8 Q-1, recorded: each case is reproduced by one rounding only."""
    for cid, wrong in (("F-P02", "period"), ("F-P05", "tournament")):
        case = BY_ID[cid]
        pc = layer0.period_change([(str(t["event_id"]), deltas(t)) for t in case["tournaments"]], period_k(case))
        base = case["published_list_ratings"][month_before(case["rating_period"])]
        alt = base + (pc.rounded if wrong == "period" else pc.rounded_per_tournament)
        assert alt != case["published_list_ratings"][case["rating_period"]]
