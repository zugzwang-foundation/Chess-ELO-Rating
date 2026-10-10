"""KA-1 to KA-6 (docs/specs/SPEC-K-ACTIVITY_v1_0.md §8): K from FIDE's activity record, R16 of D-0009."""
import math

import pytest

ka = pytest.importorskip("layer2.kactivity")
from layer1 import outputs  # noqa: E402

Q = math.log(10) / 400
KAPPA, ALPHA, BETA = 1.212, 0.286, 0.4985


def v_at(rating):
    return ka.score_variance(ALPHA, BETA, rating)


def test_ka_1_k_of_n():
    v = v_at(2300)
    for s in (30.0, 55.0, 80.0, 120.0, 250.0):
        ks = [ka.k_of_n(s * s, n, KAPPA, v) for n in range(1, 60)]
        assert all(a >= b for a, b in zip(ks, ks[1:]))                       # falls with the period's games
        assert all(ka.K_MIN <= k <= ka.K_MAX for k in ks)
        assert abs(ka.k_of_n(s * s, 1, KAPPA, v) - outputs.k_from_sigma(s, KAPPA, v)) < 1e-12   # n = 1 is R6
        c_tc, n_i = ka.published_form(s * s, KAPPA, v)
        for n in (1, 3, 9, 30):
            raw = ka.k_of_n(s * s, n, KAPPA, v, 0.0, 1e9)
            assert abs(raw - c_tc / (n_i + n)) < 1e-9 * max(1.0, raw)          # D-0009 reading 3
            assert abs(raw - Q * s * s / (KAPPA * (1 + n * Q * Q * s * s * v))) < 1e-12
    for n in (1, 4, 9):
        ks = [ka.k_of_n(s * s, n, KAPPA, v) for s in range(5, 400, 5)]
        assert all(a <= b for a, b in zip(ks, ks[1:]))                        # rises with σ
    assert ka.k_printed(55.0 ** 2, 1, 1.0, 0.25) == 17.0


def test_ka_2_idle_growth_and_games():
    c_k, birth = 1.0, 1990
    years = [2015 + (1 + t) // 12 for t in range(30)]
    ratings = [2000] * 30
    games = [0] * 30
    games[20] = 6
    p = ka.trajectory(ratings, games, years, birth, c_k, ALPHA, BETA)
    c = ka.growth(c_k, years[1] - birth)
    assert p[0] == ka.S_LIST ** 2                                              # rated on the first archived list
    assert abs(p[1] - min(p[0] + c * c, ka.S0 ** 2)) < 1e-9
    for t in range(1, 20):                                                     # idle: + c² a month, capped at s_0²
        ct = ka.growth(c_k, years[t] - birth)
        assert abs(p[t] - min(p[t - 1] + ct * ct, ka.S0 ** 2)) < 1e-9
    c20 = ka.growth(c_k, years[20] - birth)
    pre = min(p[19] + c20 * c20, ka.S0 ** 2)
    info = Q * Q * v_at(ratings[19])
    assert abs(p[20] - 1.0 / (1.0 / pre + 6 * info)) < 1e-9                   # six games add 6 I to the precision
    long_idle = ka.trajectory([2000] * 600, [0] * 600, [2015 + t // 12 for t in range(600)], birth, c_k, ALPHA, BETA)
    assert long_idle[-1] == ka.S0 ** 2


def test_ka_3_steady_state():
    c_k, birth, g = 1.0, 1985, 3
    n = 400
    years = [2015] * n                                                          # age 30 throughout
    p = ka.trajectory([1800] * n, [g] * n, years, birth, c_k, ALPHA, BETA)
    c = ka.growth(c_k, 30)
    info = Q * Q * v_at(1800)
    steady = ka.steady_state(c, g, info)
    assert abs(steady - c * c * (1 + math.sqrt(1 + 4 / (c * c * g * info))) / 2) < 1e-9
    assert abs((p[-2] + c * c) - steady) < 1e-6 * steady                      # P⁻ at the steady state


def test_ka_4_first_appearance_and_reentry():
    birth, c_k = 2000, 1.0
    years = [2015 + t // 12 for t in range(12)]
    info = Q * Q * v_at(1500)
    p = ka.trajectory([0, 0, 0, 1500, 1500], [0, 0, 0, 2, 0], years[:5], birth, c_k, ALPHA, BETA)
    assert p[:3] == [None, None, None]
    assert abs(p[3] - ka.newcomer_var(2, info)) < 1e-9
    assert abs(ka.newcomer_var(2, info) - 1.0 / (1.0 / ka.S0 ** 2 + 5 * info)) < 1e-12   # at least N_seed = 5 games
    assert abs(ka.newcomer_var(8, info) - 1.0 / (1.0 / ka.S0 ** 2 + 8 * info)) < 1e-12
    r = [1500, 1500, 1500, 1500, 1500, 0, 0, 1500, 1500]
    g = [0, 3, 3, 3, 3, 0, 0, 6, 2]
    q = ka.trajectory(r, g, years[:9], birth, c_k, ALPHA, BETA)
    assert q[5] is None and q[6] is None
    assert abs(q[7] - ka.newcomer_var(6, info)) < 1e-9                         # a re-entry restarts as a newcomer


def test_ka_5_growth_by_age():
    for age, band in ((8, 0), (13, 1), (17, 2), (22, 3), (30, 4), (50, 5), (70, 6)):
        assert ka.growth(2.0, age) == 2.0 * ka.PROFILE[band]
    assert ka.growth(1.5, None) == 1.5 * ka.PROFILE[4]                       # no year of birth: 25-45 (T2.2)
    assert ka.PROFILE == (25.0, 25.0, 20.0, 14.0, 12.0, 15.0, 15.0)            # SPEC-L1 §3.7


def test_ka_6_cutoff(tmp_path):
    with pytest.raises(ValueError):
        ka.read_lists(tmp_path, "standard", {"1"}, "2015-02", "2026-11")
    assert ka.LAST_LIST == "2026-10"
