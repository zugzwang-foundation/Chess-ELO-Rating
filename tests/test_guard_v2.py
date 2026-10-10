"""The narrowed guard of R24's rule (ii) (D-0011, reading 6): src/layer2/guard_v2.py and params/guard_2026-10b.yaml."""
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from layer2 import guard_v2 as gv2  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

STAGED = ROOT / "params" / "guard_2026-10b.yaml"


def test_region_and_weight_on_published_ratings():
    assert not gv2.in_region(2700, 2301) and gv2.weight(2700, 2301) == 0          # gap 399
    assert gv2.in_region(2700, 2300) and gv2.weight(2700, 2300) == 0              # gap 400: the edge, weight 0
    assert gv2.weight(2300, 2700) == gv2.weight(2700, 2300)                        # the order (colour) does not enter
    assert gv2.weight(2750, 2300) == 1                                             # gap 450, level 2525
    assert gv2.weight(2749, 2300) == Decimal("0.98")                               # gap 449
    assert gv2.weight(2575, 2125) == 1                                             # gap 450, level 2350
    assert gv2.weight(2574, 2125) == Decimal("0.9702")                             # gap 449 (0.98), level 2349.5 (0.99)
    assert gv2.in_region(2600, 2000) and gv2.weight(2600, 2000) == 0              # level 2300 exactly: w_L = 0
    assert gv2.weight(2601, 2000) == Decimal("0.01")                               # level 2300.5, gap 601
    assert gv2.weight(2800, 2000) == 1                                             # level 2400, gap 800
    assert not gv2.in_region(2500, 2099) and gv2.weight(2500, 2099) == 0          # level 2299.5: outside


def test_favourite_raised_underdog_lowered_and_sum_one():
    w = Decimal(1)
    e, b = gv2.guard_own(0.85, 470, True, w)              # T(470) = 0.95
    assert b and abs(e - 0.95) < 1e-12
    e, b = gv2.guard_own(0.15, -470, False, w)
    assert b and abs(e - 0.05) < 1e-12
    e, b = gv2.guard_own(0.97, 470, True, w)              # the v2 value is larger: kept
    assert not b and e == 0.97
    half = Decimal("0.5")
    e, b = gv2.guard_own(0.85, 470, True, half)           # blended halfway
    assert b and abs(e - 0.90) < 1e-12
    for x in (401, 430, 500, 600, 735):
        for ef in (0.80, 0.88, 0.93):
            for w in (Decimal("0.02"), Decimal("0.5"), Decimal(1)):
                a = gv2.guard_own(ef, x, True, w)[0]
                b_ = gv2.guard_own(1 - ef, -x, False, w)[0]
                assert abs(a + b_ - 1.0) < 1e-12


def test_stop_beyond_735_and_no_guard_at_weight_zero():
    assert gv2.guard_own(0.95, 736, True, Decimal(1)) == (0.95, False)
    assert gv2.guard_own(0.05, -736, False, Decimal(1)) == (0.05, False)
    e, b = gv2.guard_own(0.95, 735, True, Decimal(1))
    assert b and abs(e - 0.99) < 1e-12                    # the last row below 1.0
    assert gv2.guard_own(0.85, 500, True, Decimal(0)) == (0.85, False)
    with pytest.raises(ValueError):
        gv2.table_812_full(-1)


def test_published_entries_mirror_exactly():
    """Rounded on the favourite's side and mirrored, so that the published E(-x) = 1 - E(x) holds exactly."""
    par = (1.1771, 0.1866, 36.47, 0.2491, 0.6093, 0.2629, 0.0756)
    for r_fav, r_und in ((2600, 2150), (2700, 2201), (2451, 1990), (2390, 1940), (2999, 2290)):
        w = gv2.weight(r_fav, r_und)
        mid = t2.band_mid((r_fav + r_und) // 2)
        for x in (r_fav - r_und + 36, r_fav - r_und - 36):
            e_f = gv2.guard_own(t2.published(x, mid, par), x, True, w)[0]
            e_u = gv2.guard_own(t2.published(-x, mid, par), -x, False, w)[0]
            assert isinstance(e_f, Decimal) and e_f + e_u == 1 and e_f == e_f.quantize(Decimal("0.001"))


def test_staged_guard_file_records_the_rule():
    text = STAGED.read_text(encoding="utf-8")
    assert re.search(r"region: \{level_min: 2300, gap_min: 400, gap_blend: 50, level_blend: 50, x_max: 735\}", text)
    for tc in ("standard", "rapid", "blitz"):
        block = re.search(rf"^{tc}:\n((?:  .*\n?)+)", text, re.M).group(1)
        applies = re.search(r"applies: (\w+)", block).group(1) == "true"
        inside = re.search(r"rule_i_interval_inside: (\w+)", block).group(1) == "true"
        assert applies == (not inside)                                       # rule (i), as D-0011 reading 4 reads it
