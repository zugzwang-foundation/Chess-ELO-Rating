"""Rung 2 v2 (SPEC-TABLE-FIT v1.1): the level-dependent table, its fit and R32's slope ratio.

src/layer2/table_v2.py and analysis/table_v2_fit.py; the parameter file params/table_fit_2026-10b.yaml."""
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import table_v2_fit as tf  # noqa: E402
from layer2 import table as t1  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

V1 = (1.2120, 35.91, 0.2860, 0.4985, 0.2915)          # Freeze 1's standard parameters (params/table_fit_2026-10.yaml)
STAGED = ROOT / "params" / "table_fit_2026-10b.yaml"


def v2_of(v1: tuple, lam: float = 0.0, mu: float = 0.0) -> tuple:
    kappa, eta, alpha, beta, gamma = v1
    return (kappa, lam, eta, alpha, beta, gamma, mu)


def test_lambda_zero_is_version_one():
    par = v2_of(V1)
    for mid in t2.BAND_MIDS:
        for gap in (-650, -399, -36, 0, 7, 120, 401, 735, 1200):
            a, b = t2.probs(par, gap, mid), t1.probs(V1, gap, mid)
            assert all(abs(x - y) < 1e-15 for x, y in zip(a, b))
        for x in (-736, -400, -1, 0, 1, 36, 250, 400, 735, 1000):
            assert t2.published(x, mid, par) == t1.published(x, mid, V1)


def test_symmetry_and_band_mids():
    par = v2_of(V1, 0.19, 0.08)
    for mid in (1450, 2050, 2850):
        for x in (1, 100, 399, 800):
            assert t2.published(-x, mid, par) == 1 - t2.published(x, mid, par)
            assert abs(t2.expected_effective(-x, mid, par) + t2.expected_effective(x, mid, par) - 1.0) < 1e-15
    assert [t2.band_mid(v) for v in (1100, 1499, 1500, 1599, 2299, 2300, 2799, 2800, 3100)] == \
        [1450, 1450, 1550, 1550, 2250, 2350, 2750, 2850, 2850]
    assert t2.BAND_MIDS == tuple(sorted({t2.band_mid(v) for v in range(1000, 3200)}))


def test_slope_at_zero_is_the_derivative():
    par = v2_of(V1, 0.19, 0.08)
    for mid in (1450, 1750, 2350, 2750):
        h = 1e-5                                          # the |z| kink adds an error linear in h
        num = (t2.expected_effective(h, mid, par) - t2.expected_effective(-h, mid, par)) / (2 * h)
        assert abs(num - t2.slope_at_zero(par, mid)) < 1e-10
    assert round(t2.slope_812(), 5) == 0.00137            # analysis/OUTPUT_v1_0.md, section 13.4


def test_ratio_and_scaling_verdict():
    par = v2_of(V1)                                       # version one: 14 % to 53 % flatter than table 8.1.2 (script 13.4)
    assert t2.ratio_printed(par, 1750) == Decimal("1.17")
    assert t2.needs_scaling(par)
    steep = (2.0, 0.0, 35.0, -3.0, 0.0, 0.25, 0.0)       # few draws, steep: the ratio falls below 0.9 somewhere
    assert t2.needs_scaling(steep)
    # a table whose slope at zero equals table 8.1.2's in every band needs no scaling
    flat = (t2.slope_812() * 2 * (2 + 1.0) / t2.Q, 0.0, 30.0, 0.0, 0.0, 0.25, 0.0)
    assert not t2.needs_scaling(flat)


def test_fit_recovers_known_parameters():
    """ML on expected counts (1,000 games a cell spread over the outcomes by the true model) returns the truth."""
    for truth, tail in (((1.15, 0.2, 30.0, 0.25, 0.55, 0.28, 0.0), False), ((1.15, 0.2, 30.0, 0.25, 0.55, 0.22, 0.15), True)):
        cells = []
        for mid in t2.BAND_MIDS:
            for x in range(-700, 701, 25):
                pw, pd, pl = t2.probs(truth, x, mid)
                for s, p in ((1.0, pw), (0.5, pd), (0.0, pl)):
                    cells.append((x, t2.ell(mid), s, 1000.0 * p))
        f = tf.fit(cells, (1.0, 20.0, 0.0, 0.4, 0.3), tail=tail)
        got = tf.par_of(f)
        assert all(abs(a - b) < 1e-5 * max(1.0, abs(b)) for a, b in zip(got, truth)), (got, truth)
        assert f["se"]["lambda"] and (not tail or f["se"]["mu"])


def test_gamma_bound_holds_in_every_band():
    assert tf.feasible([1.0, 0.0, 30.0, 0.0, 0.5, 0.3, 0.0])
    assert not tf.feasible([1.0, 0.0, 30.0, 0.0, 0.5, 0.3, 0.4])          # 0.3 e^{0.4 x 2.125} > 1/2
    assert not tf.feasible([1.0, 0.0, 30.0, 0.0, 0.5, -0.01, 0.0])
    assert not tf.feasible([0.04, 0.0, 30.0, 0.0, 0.5, 0.3, 0.0])


def test_staged_parameter_file_prints_the_ratios_of_its_own_values():
    text = STAGED.read_text(encoding="utf-8")
    for tc in ("standard", "rapid", "blitz"):
        block = re.search(rf"^{tc}:\n((?:  .*\n?)+)", text, re.M).group(1)
        par = tuple(float(re.search(rf"^  {k}: {{value: (-?[\d.]+)", block, re.M).group(1)) for k in t2.NAMES)
        scale = dict(re.findall(r"(\d{4}): ([\d.]+)", re.search(r"k_scale: \{(.*)\}", block).group(1)))
        assert {int(k): Decimal(v) for k, v in scale.items()} == {m: t2.ratio_printed(par, m) for m in t2.BAND_MIDS}
        applies = re.search(r"k_scale_applies: (\w+)", block).group(1) == "true"
        assert applies == t2.needs_scaling(par)
