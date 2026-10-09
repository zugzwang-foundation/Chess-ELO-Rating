"""A-2: every rating-change calculator fixture F-C01 to F-C24 (SPEC-L0 R-13 to R-17, §6.1)."""
from datetime import date
from decimal import Decimal

import pytest

from l0_helpers import fixture, require_layer0

layer0 = require_layer0()
CASES = fixture("fide_calculator", "calculator_rating_change.json")["cases"]
# The calculator applies the 400-point cap to players rated 2650 or above as well (SPEC-L0 §6.1).
NOT_AS_WRITTEN = {"F-C16", "F-C17", "F-C20", "F-C21"}


def change(case: dict, chapter: str, start: date) -> Decimal:
    i = case["inputs"]
    return i["K"] * layer0.game_delta(i["own_rating"], i["opponent_rating"], Decimal(str(i["score"])), chapter, start)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_plain_cap_reproduces_the_calculator(case):
    calc = Decimal(str(case["calculator_change"]))
    assert change(case, "rapid", date(2025, 10, 1)) == calc          # R-15
    assert change(case, "standard", date(2025, 9, 30)) == calc       # R-14a: before 1 October 2025


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_rule_as_written_from_1_october_2025(case):
    got = change(case, "standard", date(2025, 10, 1))                # R-14
    calc = Decimal(str(case["calculator_change"]))
    if case["id"] in NOT_AS_WRITTEN:
        assert got != calc
        assert got == Decimal(str(case["current_rules_change"]))
    else:
        assert got == calc


def test_the_exceptions_are_exactly_the_exempt_players_with_gaps_over_400():
    exempt = {c["id"] for c in CASES
              if c["inputs"]["own_rating"] >= 2650 and abs(c["inputs"]["own_rating"] - c["inputs"]["opponent_rating"]) > 400}
    assert exempt == NOT_AS_WRITTEN
