"""A-1: tables 8.1.1 and 8.1.2 in the engine equal the transcription entry by entry (SPEC-L0 R-16, R-30, §9)."""
from decimal import Decimal

import pytest

from l0_helpers import require_layer0, transcribed_149, transcribed_811, transcribed_812

T811 = transcribed_811()
T812 = transcribed_812()


def test_transcription_shape():
    """Runs without the engine: the transcribed tables have the shape SPEC-L0 §9 states."""
    assert len(T811) == 101
    assert len(T812) == 51
    assert all(T811[p] == -T811[Decimal(1) - p] for p in T811)
    assert all(h + low == 1 for _, _, h, low in T812)
    assert T812[0][0] == 0 and T812[-1] == (736, None, Decimal("1.0"), Decimal("0.00"))
    assert all(T812[i + 1][0] == T812[i][1] + 1 for i in range(len(T812) - 1))


def test_title_table_equals_811():
    """Runs without the engine: table 1.4.9 [VT 1] equals table 8.1.1 [V 1] entry by entry."""
    assert transcribed_149() == T811


def test_engine_table_811():
    layer0 = require_layer0()
    assert dict(layer0.TABLE_811) == T811


def test_engine_table_812():
    layer0 = require_layer0()
    assert [tuple(row) for row in layer0.TABLE_812] == T812


@pytest.mark.parametrize("row", T812, ids=lambda r: f"{r[0]}-{r[1]}")
def test_expected_score_at_row_edges(row):
    layer0 = require_layer0()
    lo, hi, h, low = row
    for d in (lo, hi if hi is not None else 5000):
        assert layer0.expected_score(d) == h
        if d:
            assert layer0.expected_score(-d) == low


@pytest.mark.parametrize("p", sorted(T811))
def test_dp_from_p_on_the_table(p):
    layer0 = require_layer0()
    assert layer0.dp_from_p(p) == T811[p]


def test_dp_from_p_rounds_p_to_two_decimals_half_up():
    """R-30 reading (NOT VERIFIED): p is rounded to the nearest hundredth, .005 rounded up."""
    layer0 = require_layer0()
    assert layer0.dp_from_p(Decimal(4) / 7) == T811[Decimal("0.57")]
    assert layer0.dp_from_p(Decimal("0.575")) == T811[Decimal("0.58")]
    assert layer0.dp_from_p(Decimal("0.5749")) == T811[Decimal("0.57")]
    assert layer0.dp_from_p(Decimal("0.425")) == T811[Decimal("0.43")]
