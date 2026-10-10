"""A1-4 to A1-6 (SPEC-L1 §7): recovery, anchoring and determinism on a synthetic pool."""
import math

import pytest

layer1 = pytest.importorskip("layer1")
from layer1 import fit, model  # noqa: E402
from l1_synth import fitted  # noqa: E402


@pytest.fixture(scope="module")
def result():
    return fitted()


def test_a1_4_recovery_and_calibration(result):
    f, true, birth, panel, t_ref = result
    last = fit.month_index(2024, 12)
    xs, ys, zs = [], [], []
    for p in sorted(true):
        i = f.index[p]
        if len(f.glist[i]) < 20:
            continue
        s_hat = fit.strength(f, i, 0, last)
        sd = fit.sigma_tc(fit.covariance_at(f, i, last), 0)
        s_true = true[p][23][0]
        xs.append(s_hat)
        ys.append(s_true)
        zs.append((s_hat - s_true) / sd)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cor = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / math.sqrt(
        sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    mz = sum(zs) / n
    sdz = math.sqrt(sum((z - mz) ** 2 for z in zs) / n)
    assert n >= 100
    assert cor >= 0.9
    assert 0.7 <= sdz <= 1.4
    assert f.max_move < f.hyper.tol


def test_a1_5_anchor_and_zero_drift_for_25_45(result):
    f, true, birth, panel, t_ref = result
    got = sum(sum(fit.state_at(f, i, t_ref)[:2]) for i, _ in panel) / len(panel)
    assert abs(got - sum(r for _, r in panel) / len(panel)) < 1e-6
    assert f.A[model.ANCHOR_BAND] == 0.0 and f.B[model.ANCHOR_BAND] == 0.0


def test_a1_6_two_fits_are_identical(result):
    f1 = result[0]
    f2 = fitted()[0]
    assert f1.x == f2.x and f1.cov_last == f2.cov_last and f1.A == f2.A and f1.B == f2.B
