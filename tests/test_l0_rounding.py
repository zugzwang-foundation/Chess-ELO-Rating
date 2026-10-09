"""A-6: rounding (SPEC-L0 R-25, R-26)."""
from decimal import Decimal

import pytest

from l0_helpers import require_layer0

layer0 = require_layer0()


@pytest.mark.parametrize("x,expected", [
    ("0.5", 1), ("-0.5", -1), ("1.5", 2), ("-1.5", -2), ("2.5", 3), ("-2.5", -3), ("2.49", 2), ("-2.49", -2),
    ("2.51", 3), ("-2.51", -3), ("0", 0), ("-0.49", 0), ("92.48", 92), ("-2.50", -3), ("5.40", 5), ("15.30", 15),
])
def test_r25_half_away_from_zero(x, expected):
    assert layer0.round_change(Decimal(x)) == expected


@pytest.mark.parametrize("x,expected", [("1922.43", 1922), ("1950.5", 1951), ("1950.49", 1950), ("2199.5", 2200)])
def test_r26_initial_rating_half_up(x, expected):
    """R-26 reading (NOT VERIFIED): 0.5 rounded up, as §1.4.7 b) of the Title Regulations rounds an average."""
    assert layer0.round_initial(Decimal(x)) == expected


def test_period_change_rounds_once_and_reports_the_alternative():
    pc = layer0.period_change([("a", [Decimal("0.35")]), ("b", [Decimal("0.35")])], 10)
    assert pc.change == Decimal("7.00")
    assert pc.rounded == 7
    assert pc.rounded_per_tournament == 8           # 3.5 -> 4, twice
    assert [t.change for t in pc.tournaments] == [Decimal("3.50"), Decimal("3.50")]
