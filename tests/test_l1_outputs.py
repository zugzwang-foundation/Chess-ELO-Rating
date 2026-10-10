"""A1-9 to A1-12 (SPEC-L1 §7): K by R6, θ̃ by R2, the information share and compensation by R5, seeds."""
import math

import pytest

layer1 = pytest.importorskip("layer1")
from layer1 import outputs as o  # noqa: E402

Q = math.log(10) / 400


def test_a1_9_k_from_sigma():
    ks = [o.k_from_sigma(s, 1.212, 0.124) for s in range(0, 400, 5)]
    assert all(a <= b for a, b in zip(ks, ks[1:]))
    assert all(o.K_MIN <= k <= o.K_MAX for k in ks)
    for s in (45, 55, 60, 70):
        d3 = Q * s * s / (1 + Q * Q * s * s / 4)
        assert abs(o.k_from_sigma(s, 1.0, 0.25) - min(40, max(10, d3))) < 1e-12
        raw1 = Q * s * s / (1 + Q * Q * s * s * 0.15)
        assert abs(o.k_from_sigma(s, 1.25, 0.15, 0, 1e9) - raw1 / 1.25) < 1e-12
    assert o.k_printed(55, 1.0, 0.25) == 17.0


def test_a1_10_theta_tilde():
    assert o.theta_tilde(2110.0, 2050.0, 2060.0, 1.2) == 2050.0 + 50.0 / 1.2
    assert o.theta_tilde(2110.0, 2050.0, 2060.0, 1.0) == 2110.0 - (2060.0 - 2050.0)


def test_a1_11_information_share_and_compensation():
    assert o.info_share(1.0, 0.4, 0.1, only_tc=True) == 1.0
    for p_all, p_tc, p0 in ((5e-4, 3e-4, 1e-4), (5e-4, 6e-4, 1e-4), (2e-4, 1e-5, 1e-4)):
        assert 0.0 <= o.info_share(p_all, p_tc, p0) <= 1.0
    assert not o.junior_eligible(16, 12, 6, 3, 0.49)
    assert o.junior_eligible(16, 12, 6, 3, 0.5)
    assert not o.junior_eligible(20, 12, 6, 3, 0.9)
    assert not o.junior_eligible(16, 9, 6, 3, 0.9)
    assert o.compensation(1850.0, 100.0, 1500, True) == 197          # annex T10.1: 1850 − 128.16 − 1500 − 25
    assert o.compensation(1850.0, 100.0, 1500, False) == 0
    assert o.compensation(2500.0, 50.0, 1500, True) == o.C_CAP
    assert o.compensation(1600.0, 100.0, 1500, True) == 0


def test_a1_12_seeds():
    assert o.seed(1287.6, 80.0, 6, 4, 2) is None                    # below 1400: not published (annex T4.7)
    assert o.seed(1650.0, 80.0, 6, 4, 2) == 1650
    assert o.seed(2466.0, 80.0, 6, 4, 2) == 2200
    assert o.seed(1650.0, 121.0, 6, 4, 2) is None
    assert o.seed(1650.0, 80.0, 4, 4, 2) is None
    assert o.monthly_adjustment(7.2) == 0.9 and o.monthly_adjustment(-8.0) == -1.0 and o.monthly_adjustment(1.5) == 0.0
