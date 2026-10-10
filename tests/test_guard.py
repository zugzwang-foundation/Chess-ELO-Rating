"""R17 (D-0009, reading 4): the farming guard for rung 2, and rung 2's table as library code (src/layer2)."""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

guard = pytest.importorskip("layer2.guard")
from layer2 import table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import compare_event  # noqa: E402


def test_region_edges():
    assert guard.in_region(2300, 1900)                    # gap 400, favourite 2300: inside
    assert not guard.in_region(2300, 1901)                # gap 399
    assert not guard.in_region(2299, 1800)                # favourite below 2300
    assert guard.in_region(2800, 2100)
    assert guard.table_812_uncapped(500) == Decimal("0.96")
    assert guard.table_812_uncapped(735) == Decimal("0.99") and guard.table_812_uncapped(736) == Decimal("1.0")
    with pytest.raises(ValueError):
        guard.table_812_uncapped(-1)


def test_larger_of_the_two_and_one_minus_it():
    e, binds = guard.guard_own(0.85, 2600, 2100)          # 8.1.2 at the full gap 500: .96
    assert binds and e == 0.96
    e, binds = guard.guard_own(0.97, 2600, 2100)          # the fitted value is larger: kept
    assert not binds and e == 0.97
    e, binds = guard.guard_own(0.15, 2100, 2600)          # the underdog: one minus the favourite's
    assert binds and abs(e - 0.04) < 1e-12
    e, binds = guard.guard_own(0.85, 2299, 1799)          # outside the region: unchanged
    assert not binds and e == 0.85
    assert guard.guard_own(0.9, 3000, 2200)[0] == 1.0     # beyond 735 points table 8.1.2 gives 1.0
    assert guard.guard_own(0.1, 2200, 3000)[0] == 0.0


def test_sums_to_one_without_compensation():
    for rw, rb in ((2650, 2200), (2200, 2650), (2400, 1990), (2350, 1950), (2500, 2499)):
        for ew in (0.05, 0.3, 0.5, 0.82, 0.9, 0.97):
            a = guard.guard_own(ew, rw, rb)[0]
            b = guard.guard_own(1.0 - ew, rb, rw)[0]
            assert abs(a + b - 1.0) < 1e-12
    a = guard.guard_own(Decimal("0.856"), 2400, 2000)[0]
    b = guard.guard_own(Decimal("0.144"), 2000, 2400)[0]
    assert a == Decimal("0.92") and a + b == 1


def test_compensated_side_uses_its_own_gap():
    # the adult's expectation against a compensated junior uses R_j + c_j; the junior's own uses published ratings
    e_adult, binds = guard.guard_own(0.80, 2400, 1900 + 150)
    assert not binds and e_adult == 0.80                    # 2400 − 2050 = 350: outside the region
    e_junior, binds = guard.guard_own(0.08, 1900, 2400)
    assert binds and abs(e_junior - (1 - 0.96)) < 1e-12     # 500 points on the junior's own gap: 8.1.2 gives .96


def test_table_matches_the_frozen_comparison_tool():
    for tc in ("standard", "rapid", "blitz"):
        p = compare_event.load_params(compare_event.DEFAULT_PARAMS, tc)
        par = (p.kappa, p.eta, p.alpha, p.beta, p.gamma)
        assert table.eta_whole(p.eta) == p.eta_whole
        for x in range(-900, 901, 7):
            for level in (1400, 1777, 2050, 2399, 2650, 2900):
                mid = table.band_mid(level)
                assert mid == compare_event.band_mid(level)
                assert table.published(x, mid, par) == compare_event.rung2_expected(x, mid, p)


def test_evaluation_form_symmetry():
    par = (1.212, 0.0, 0.286, 0.4985, 0.2915)
    for x in (0, 50, 200, 450, 900):
        for mid in (1450, 2050, 2650):
            assert abs(table.expected_white(par, x, mid) + table.expected_white(par, -x, mid) - 1.0) < 1e-12
            pw, pd, pl = table.probs(par, x, mid)
            assert abs(pw + pd + pl - 1.0) < 1e-12


def test_guard_reads_the_favourites_published_rating_under_compensation():
    """D-0009 reading 4: "rated 2300 or more" is the favourite's published rating, also when the gap uses RX_j."""
    from decimal import Decimal as D
    # a junior published at 2250 with RX = 2350 against an adult rated 1900: the adult's gap is −450 on RX, but the
    # favourite (the junior) is rated 2250 on the list, so the guard does not apply
    e, binds = guard.guard_own(D("0.100"), 1900, 2350, r_opp_published=2250)
    assert (e, binds) == (D("0.100"), False)
    # the same pairing without compensation information reads 2350 and binds
    e2, binds2 = guard.guard_own(D("0.100"), 1900, 2350)
    assert binds2 and e2 < D("0.100")
