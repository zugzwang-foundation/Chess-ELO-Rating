"""The simulator's replacements for rung 2 v2 (src/simulator/v2.py; session ELO-6): the published v2 table and the
narrowed guard in the ledger, today's K (R32's K × m withdrawn by R44), rung 4's K under the v2 table with R25's
bound, R33's accrual window, and determinism of a small run. The frozen simulator's classes are restored after every test that installs the
replacements."""
import json
import math
from dataclasses import replace
from decimal import Decimal

import pytest

sim = pytest.importorskip("simulator")
from layer2 import guard_v2 as gv2  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402
from simulator import config as C  # noqa: E402
from simulator import ledger  # noqa: E402
from simulator import pool as P  # noqa: E402
from simulator import run as R  # noqa: E402
from simulator import v2  # noqa: E402


@pytest.fixture
def installed():
    saved = (P.Pool.play, R.Proxy, R.Ledger, R.fit_table, v2._INSTALLED)
    v2.install()
    yield
    P.Pool.play, R.Proxy, R.Ledger, R.fit_table = saved[:4]
    v2._INSTALLED = saved[4]


def test_published_table_and_the_narrowed_guard():
    tabs, eta = v2.fit_table_v2(C.KAPPA0)
    assert eta == t2.eta_whole(v2.PAR[2])
    for k, mid in enumerate(ledger.MIDS):
        for x in range(0, 1201, 37):
            assert tabs[k][x + ledger.XOFF] == int(t2.published(x, mid, v2.PAR) * 1000)
            assert tabs[k][-x + ledger.XOFF] == 1000 - tabs[k][x + ledger.XOFF]
    led = v2.LedgerV2("R2", {"2"}, (tabs, eta), 1.0)
    k = ledger.mid_index(2350)
    x = 500 + eta
    want, binds = gv2.guard_own(Decimal(tabs[k][x + ledger.XOFF]) / 1000, x, True, gv2.weight(2600, 2100))
    e = led.expect(2600, 2100, 1, k)
    assert binds and e == int(want * 1000) > tabs[k][x + ledger.XOFF]
    assert led.expect(2100, 2600, -1, k) == 1000 - e
    assert v2.LedgerV2("R2U", {"2u"}, (tabs, eta), 1.0).expect(2600, 2100, 1, k) == tabs[k][x + ledger.XOFF]
    assert led.expect(2200, 2100, 1, ledger.mid_index(2150)) == tabs[ledger.mid_index(2150)][100 + eta + ledger.XOFF]


def test_rung2_uses_todays_k_r32_withdrawn():
    tabs, eta = v2.fit_table_v2(C.KAPPA0)
    led = v2.LedgerV2("R2", {"2"}, (tabs, eta), 1.0)
    for _ in range(2):
        led.add()
    led.rated[0] = led.rated[1] = True
    led.R[0], led.R[1] = 2210, 2150
    led.game(0, 1, 2, 1, 0, [0, 0])
    text = (v2.ROOT / "params" / "table_fit_2026-10b.yaml").read_text(encoding="utf-8")
    m = int(t2.load(text, "standard")["k_scale"][2150] * 100)
    assert v2.M100[2150] == m != 100                          # the frozen file still prints R32's m ...
    assert not v2.SCALE_K and not led.scale_k                # ... which R44 withdrew: today's K, m = 1
    e = led.expect(2210, 2150, 1, ledger.mid_index(2180))
    assert led.acc[0] == 100 * (1000 - e) and led.acc[1] == -100 * (1000 - e)


def test_rung4_k_is_the_kalman_gain_under_the_v2_table_with_r25s_bound():
    led = v2.LedgerV2("R4L", {"4l"}, None, 1.0)
    led.add()
    led.rated[0], led.R[0] = True, 2350
    kap, v, f = v2._kv(2350)
    mid = t2.band_mid(2350)
    assert kap == t2.kappa_at(v2.PAR, mid) and f == (kap / C.KAPPA0) ** 2
    assert v == pytest.approx(1 / (2 * (2 + math.exp(v2.PAR[3] + v2.PAR[4] * (mid - 2000) / 400))))

    class Proxy:
        v_prior = [(60.0 * C.KAPPA0) ** 2]                    # 60 points on the published scale
    for n in (1, 5, 30):
        raw = C.Q * kap * 3600.0 / (1 + n * (C.Q * kap) ** 2 * 3600.0 * v)
        assert abs(led.k_event(0, n, Proxy, 30) / 10 - min(40.0, max(10.0, raw))) <= 0.05 + 1e-9
    Proxy.v_prior = [(20.0 * C.KAPPA0) ** 2]                  # K_min binds; 120 games exceed max(C, 700)
    c = 1 / (kap * C.Q * v)
    assert led.k_event(0, 120, Proxy, 30) == math.floor(max(c, 700.0) * 10 / 120) < 100


def test_accrual_ends_three_months_after_the_last_rated_game():
    led = v2.LedgerV2("R6", {"6"}, None, 1.0)
    for i in range(3):
        led.add()
        led.rated[i], led.R[i], led.g12[i] = True, 1800, [1] * 12
    led.last_rated = [10, 7, 6]
    led.members = lambda pool: [0, 1, 2]

    class Pool:
        alive = [True, True, True]
    led.accrue(10, Pool, lambda i: 1.0)
    assert led.B == [1.0, 1.0, 0.0]


def test_small_run_is_deterministic_and_reports_line2(installed):
    cfg = replace(C.scenario("adversaries", 7), n0=1500, burn_in=24, months=24)
    a, b = v2.run_v2(cfg), v2.run_v2(cfg)
    assert json.dumps(a, sort_keys=True, default=list) == json.dumps(b, sort_keys=True, default=list)
    assert set(a["line2"]) == set(cfg.ledgers)
    assert all(x["honest_player_years"] > 0 for x in a["line2"].values())
    assert a["adversaries"]["L0"]["collusion"]["arranged_games"] > 0
