"""A-5: K (SPEC-L0 R-18 to R-23)."""
import itertools

import pytest

from l0_helpers import require_layer0

layer0 = require_layer0()


@pytest.mark.parametrize("ever_2400,junior,ever_2300,games_30", list(itertools.product([False, True], repeat=4)))
def test_r22_precedence_on_every_combination(ever_2400, junior, ever_2300, games_30):
    k = layer0.published_k(rating=2200, games_count=30 if games_30 else 29, ever_2400=ever_2400,
                           ever_2300=ever_2300 or ever_2400, list_month="2026-10",
                           birth_year=2010 if junior else 1990)
    expected = 10 if ever_2400 else 40 if (junior and not ever_2300) else 40 if not games_30 else 20
    assert k == expected


def test_r18_new_player_until_30_games():
    assert layer0.published_k(1800, 29, False, False, "2026-10", 1990) == 40
    assert layer0.published_k(1800, 30, False, False, "2026-10", 1990) == 20


def test_r19_and_r20_the_2400_line():
    assert layer0.published_k(2399, 100, False, True, "2026-10", 1990) == 20
    assert layer0.published_k(2400, 100, False, True, "2026-10", 1990) == 10      # the current rating counts
    assert layer0.published_k(2250, 100, True, True, "2026-10", 1990) == 10       # 10 stays below 2400
    assert layer0.published_k(2400, 5, False, False, "2026-10", 1990) == 10       # before 30 games too


def test_r21_juniors_below_2300():
    assert layer0.published_k(2299, 100, False, False, "2026-10", 2010) == 40
    assert layer0.published_k(2300, 100, False, False, "2026-10", 2010) == 20     # the current rating counts
    assert layer0.published_k(2250, 100, False, True, "2026-10", 2010) == 20      # once rated 2300, not again


def test_r21_turn_of_the_year():
    """Until the end of the year of the 18th birthday: born 2008, junior on the December 2026 list, not in January."""
    assert layer0.published_k(2000, 100, False, False, "2026-12", 2008) == 40
    assert layer0.published_k(2000, 100, False, False, "2027-01", 2008) == 20


def test_unknown_year_of_birth_is_not_junior():
    assert layer0.published_k(2000, 100, False, False, "2026-10", None) == 20


@pytest.mark.parametrize("previous_k,n,expected", [
    (20, 35, 20), (20, 36, 19), (20, 39, 17), (40, 17, 40), (40, 18, 38), (10, 70, 10), (10, 71, 9), (40, 0, 40),
])
def test_r23_k_for_the_period(previous_k, n, expected):
    k = layer0.k_for_period(previous_k, n)
    assert k == expected
    assert k * n <= 700 or n == 0
