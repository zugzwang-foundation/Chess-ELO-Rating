"""The self-calibrating table's model and fit (analysis/selfcal_fit.py; SPEC-SELFCAL v1.0 §5, SPEC-TABLE-FIT v1.2 §2).

Synthetic cells only: the likelihood equals Freeze 3's (analysis/table_v2_fit.py) where the models coincide, the score
equals a finite difference, a fit recovers the parameters that generated the data, the caps bind as bounds, form P
equals form E at the knots it is given, and the published entry follows annex T3.4."""
import math
import random
import sys
from decimal import Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "analysis"))
import selfcal_fit as sf  # noqa: E402
import table_v2_fit as tf  # noqa: E402  (Freeze 3's fit, unchanged)
from layer2 import table_v2 as t2  # noqa: E402

E_TAIL = {"slope": "E", "colour_by_level": False, "tail": True}
TRUE = {"kappa": 1.18, "lambda": 0.19, "eta": 36.5, "zeta": 0.0, "alpha": 0.25, "beta": 0.61, "gamma": 0.26, "mu": 0.08}


def _cells(table: dict, n: int, seed: int) -> list[tuple]:
    rnd = random.Random(seed)
    from collections import Counter
    c = Counter()
    for _ in range(n):
        mid = rnd.choice(sf.BAND_MIDS)
        x = int(rnd.gauss(0, 150))
        pw, pd, _pl = sf.probs(table, x, mid)
        u = rnd.random()
        s = 1.0 if u < pw else 0.5 if u < pw + pd else 0.0
        c[(x, mid, s)] += 1
    return [(x, mid, s, float(w)) for (x, mid, s), w in sorted(c.items())]


def test_the_likelihood_is_freeze_3s_where_the_models_coincide():
    cells = _cells({"form": E_TAIL, "par": TRUE}, 3000, 1)
    theta = [TRUE[k] for k in sf.names(E_TAIL)]
    ll, _g = sf.loglik_grad(E_TAIL, theta, sf.group(cells))
    par7 = (TRUE["kappa"], TRUE["lambda"], TRUE["eta"], TRUE["alpha"], TRUE["beta"], TRUE["gamma"], TRUE["mu"])
    ll_tf, _ = tf.loglik_grad(list(par7), tf.group([(x, t2.ell(mid), s, w) for x, mid, s, w in cells]))
    assert math.isclose(ll, ll_tf, rel_tol=1e-12)
    for x in (-250, 0, 120):
        for mid in (1450, 2250, 2850):
            assert all(math.isclose(a, b, rel_tol=1e-12) for a, b in
                       zip(sf.probs({"form": E_TAIL, "par": TRUE}, x, mid), t2.probs(par7, x, mid)))


def test_the_score_is_the_derivative_of_the_likelihood():
    for form in (E_TAIL, {"slope": "P", "colour_by_level": True, "tail": True}):
        names = sf.names(form)
        start = {**TRUE, **{f"kappa_{k}": 1.0 + 0.1 * i for i, k in enumerate(sf.KNOTS)}, "zeta": 3.0}
        theta = [start[k] for k in names]
        grouped = sf.group(_cells({"form": E_TAIL, "par": TRUE}, 2000, 2))
        _ll, g = sf.loglik_grad(form, theta, grouped)
        for j in range(len(names)):
            h = 1e-6 * max(1.0, abs(theta[j]))
            up, dn = theta[:], theta[:]
            up[j] += h
            dn[j] -= h
            num = (sf.loglik_grad(form, up, grouped)[0] - sf.loglik_grad(form, dn, grouped)[0]) / (2 * h)
            assert math.isclose(g[j], num, rel_tol=1e-4, abs_tol=1e-4), names[j]


def test_a_fit_recovers_the_parameters_that_made_the_data():
    cells = _cells({"form": E_TAIL, "par": TRUE}, 60000, 3)
    f = sf.fit(E_TAIL, cells, {"kappa": 1.0, "eta": 30.0, "alpha": 0.2, "beta": 0.5, "gamma": 0.2})
    for k in ("kappa", "lambda", "eta", "alpha", "beta", "gamma"):
        assert abs(f["par"][k] - TRUE[k]) < 4 * f["se"][k], k
    assert f["par"]["zeta"] == 0.0 and not f["on_bound"] and f["max_abs_score"] < 1e-3


def test_a_cap_is_a_bound_and_is_reported():
    cells = _cells({"form": E_TAIL, "par": TRUE}, 20000, 4)
    caps = {"kappa": (1.0, 1.05)}
    f = sf.fit(E_TAIL, cells, TRUE, caps)
    assert f["par"]["kappa"] == 1.05 and f["on_bound"]["kappa"] == "upper" and "kappa" not in f["free"]


def test_form_p_takes_its_knots_and_interpolates_between_them():
    p = {"form": {"slope": "P", "colour_by_level": False, "tail": False},
         "par": {**{f"kappa_{k}": 1.0 + 0.05 * i for i, k in enumerate(sf.KNOTS)}, "eta": 0, "zeta": 0, "alpha": 0,
                 "beta": 0, "gamma": 0, "mu": 0}}
    assert sf.kappa_at(p, 1450) == sf.kappa_at(p, 1500) == 1.0
    assert sf.kappa_at(p, 2850) == p["par"]["kappa_2700"]
    assert math.isclose(sf.kappa_at(p, 1550), 1.0 + 0.05 * 0.25)
    assert sum(sf.knot_weights(2350)) == 1.0


def test_the_published_entry():
    tab = {"form": E_TAIL, "par": TRUE}
    assert sf.eta_whole(tab, 2050) == 37                     # 36.5 rounds half up
    e = sf.published(tab, 136, 2750)
    assert e == Decimal(repr(sf.expected_effective(tab, 136, 2750))).quantize(Decimal("0.001"))
    assert sf.published(tab, -136, 2750) == Decimal(1) - e
    assert math.isclose(sf.expected_effective(tab, 0, 2250), 0.5)


def test_draws_follow_the_covariance():
    cells = _cells({"form": E_TAIL, "par": TRUE}, 30000, 5)
    f = sf.fit(E_TAIL, cells, TRUE)
    d = sf.draws(f, 2000)
    ks = [x["kappa"] for x in d]
    mean = sum(ks) / len(ks)
    sd = math.sqrt(sum((k - mean) ** 2 for k in ks) / len(ks))
    assert abs(mean - f["par"]["kappa"]) < 0.2 * f["se"]["kappa"] and abs(sd / f["se"]["kappa"] - 1) < 0.1
    assert sf.draws(f, 10) == sf.draws(f, 10)
