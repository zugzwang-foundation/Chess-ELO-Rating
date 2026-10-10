"""A1-1, A1-2 (SPEC-L1 §7): the outcome model and the derivatives of a player's log posterior."""
import math
import random

import pytest

layer1 = pytest.importorskip("layer1")
from layer1 import fit, model  # noqa: E402


def table_probs(kappa, eta, alpha, beta, gamma, x, mid):
    """SPEC-TABLE-FIT §2's form, written out independently."""
    z = kappa * model.Q * (x + eta)
    nu = math.exp(alpha + beta * (mid - 2000.0) / 400.0 - gamma * abs(z))
    a, b = math.exp(z / 2), math.exp(-z / 2)
    return a / (a + b + nu), nu / (a + b + nu), b / (a + b + nu)


@pytest.mark.parametrize("x", [-700, -250, -1, 0, 3, 180, 520, 1200])
@pytest.mark.parametrize("mid", [1450, 2050, 2850])
def test_a1_1_probabilities_equal_the_table_form_with_kappa_one(x, mid):
    eta, alpha, beta, gamma = 36.0, 0.286, 0.4985, 0.2915
    z = model.Q * (x + eta)
    got = model.probs(z, math.exp(alpha + beta * model.ell_of(mid)), gamma)
    want = table_probs(1.0, eta, alpha, beta, gamma, x, mid)
    assert all(abs(g - w) < 1e-12 for g, w in zip(got, want))
    assert abs(sum(got) - 1.0) < 1e-12


@pytest.mark.parametrize("nu0", [0.0, 0.5, 1.93, 4.0])
def test_a1_1_symmetry_and_slope_at_zero(nu0):
    for z in (0.1, 0.7, 2.5):
        assert abs(model.expected_white(z, nu0, 0.3) + model.expected_white(-z, nu0, 0.3) - 1.0) < 1e-12
    h = 1e-6
    slope = (model.expected_white(h, nu0, 0.3) - model.expected_white(-h, nu0, 0.3)) / (2 * h)
    assert abs(slope - model.score_variance_at_zero(nu0)) < 1e-6
    _, _, info = model.game_terms(0.0, nu0, 0.3, 1.0)
    assert abs(info - model.score_variance_at_zero(nu0)) < 1e-12


def test_a1_2_gradient_equals_finite_differences_and_information_is_positive():
    rnd = random.Random(5)
    from l1_synth import pool, OUTCOME
    games, true, birth, init = pool(n=40, months=8, games_per_month=60, seed=11)
    f = fit.build(games, birth, lambda p, m: fit.Prior(init[p], 120.0 ** 2), fit.Hyper(), outcome=OUTCOME)
    for i in range(len(f.players)):
        f.x[i] = [v + rnd.gauss(0, 30) for v in f.x[i]]
    for i in (0, 7, 19):
        X = f.x[i]
        F, G, D, U = fit._assemble(f, i, X)
        for k in range(len(X) // 4):
            for c in range(4):
                h = 1e-4
                Xp, Xm = list(X), list(X)
                Xp[4 * k + c] += h
                Xm[4 * k + c] -= h
                fd = (fit._value(f, i, Xp) - fit._value(f, i, Xm)) / (2 * h)
                assert abs(fd - G[k][c]) <= 1e-6 * max(1.0, abs(G[k][c]))
    for z in (-3.0, -0.4, 0.0, 0.9, 4.0):
        for s in (0.0, 0.5, 1.0):
            assert model.game_terms(z, 1.2, 0.3, s)[2] > 0
