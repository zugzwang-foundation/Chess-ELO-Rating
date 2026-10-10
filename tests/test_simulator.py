"""The simulator (docs/specs/SPEC-SIM_v1_0.md): Layer 0's integer port against src/layer0, the pairings, the
ledgers' arithmetic, the κ fit, and determinism of a small run."""
import json
import math
import random
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

sim = pytest.importorskip("simulator")
import layer0  # noqa: E402
from layer2 import guard, table  # noqa: E402
from simulator import config as C  # noqa: E402
from simulator import events as EV  # noqa: E402
from simulator import fide, ledger  # noqa: E402
from simulator import run as R  # noqa: E402

AFTER = date(2026, 1, 1)                               # after the 2650 exemption of 1 October 2025 (SPEC-L0 R-14)


def test_fide_expectation_equals_layer0():
    for own in list(range(1400, 2900, 37)) + [2649, 2650, 2651]:
        for opp in range(1000, 3000, 41):
            want = layer0.expected_score(layer0.effective_difference(own, opp, "standard", AFTER))
            assert fide.pd100(own, opp) == int(want * 100), (own, opp)
    for d in range(-800, 801):
        assert fide.pd100_uncapped(d) * 10 == int(guard.table_812_uncapped(abs(d)) * 1000 if d >= 0
                                                  else (1 - guard.table_812_uncapped(-d)) * 1000)


def test_fide_k_rounding_and_initial_rating_equal_layer0():
    rnd = random.Random(5)
    for _ in range(2000):
        r, g = rnd.randint(1400, 2700), rnd.randint(0, 80)
        e24, e23 = rnd.random() < 0.2, rnd.random() < 0.3
        by = rnd.choice([None, 2005, 2010, 1990])
        assert fide.published_k(r, g, e24, e23, 2026, by) == layer0.published_k(r, g, e24, e23, "2026-03", by)
        k, n = rnd.choice([10, 20, 40]), rnd.randint(0, 90)
        assert fide.k_for_period(k, n) == layer0.k_for_period(k, n)
        num, den = rnd.randint(-100000, 100000), rnd.choice([100, 1000, 10000])
        assert fide.round_half_away(num, den) == layer0.round_change(Decimal(num) / den)
    for _ in range(500):
        events, first = [], True
        for _e in range(rnd.randint(1, 3)):
            res = [(rnd.randint(1400, 2300), rnd.choice([0, 1, 2])) for _ in range(rnd.randint(1, 5))]
            events.append((first, res))
            first = False
        pool = [layer0.PoolEvent("2026-01", tuple((r, Decimal(s) / 2) for r, s in res), first_event=f) for f, res in events]
        assert fide.initial_rating(events) == layer0.initial_rating(pool)


def test_round_robin_and_swiss_pairings():
    ps = list(range(10))
    rounds = EV.round_robin(ps)
    pairs = [frozenset(p) for rd in rounds for p in rd]
    assert len(rounds) == 9 and len(pairs) == 45 and len(set(pairs)) == 45
    for rd in rounds:
        assert sorted(x for p in rd for x in p) == ps
    rnd = random.Random(3)
    players = list(range(40))
    rating = {p: 1500 + 10 * p for p in players}
    sw = EV.Swiss(players, rating)
    seen = set()
    repeats = 0
    for _ in range(9):
        rd = sw.pair()
        flat = [x for p in rd for x in p]
        assert len(flat) == len(set(flat)) == 40
        for w, b in rd:
            repeats += frozenset((w, b)) in seen
            seen.add(frozenset((w, b)))
            sw.record(w, b, rnd.choice([0, 1, 2]))
    assert repeats <= 4
    for p in players:
        assert abs(sum(sw.colours[p])) <= 3


def test_ledger_tables_match_the_published_table_and_the_guard():
    tabs, eta = ledger.fit_table(C.KAPPA0)
    par = (C.KAPPA0, C.ETA, C.ALPHA, C.BETA, C.GAMMA)
    for k, mid in enumerate(ledger.MIDS):
        for x in range(-1200, 1201, 13):
            assert tabs[k][x + ledger.XOFF] == int(table.published(x, mid, par) * 1000)
    led = ledger.Ledger("R2", {"2"}, (tabs, eta), 1.0)
    e = led.expect(2600, 2100, 1, ledger.mid_index(2350))
    assert e == max(tabs[ledger.mid_index(2350)][500 + eta + ledger.XOFF], int(guard.table_812_uncapped(500) * 1000))
    e_b = led.expect(2100, 2600, -1, ledger.mid_index(2350))
    assert e_b == min(tabs[ledger.mid_index(2350)][-500 - eta + ledger.XOFF], 1000 - int(guard.table_812_uncapped(500) * 1000))


def test_kappa_fit_recovers_the_slope():
    rnd = random.Random(11)
    cells = {}
    for _ in range(40000):
        x, mid = int(rnd.gauss(0, 220)), rnd.choice(ledger.MIDS)
        z = 1.4 * C.Q * (x + C.ETA)
        nu = math.exp(C.ALPHA + C.BETA * (mid - 2000) / 400 - C.GAMMA * abs(z))
        a = math.exp(z / 2)
        u = rnd.random() * (a + 1 / a + nu)
        s2 = 2 if u < a else 1 if u < a + nu else 0
        cells[(x, mid, s2)] = cells.get((x, mid, s2), 0) + 1
    assert abs(ledger.fit_kappa(cells) - 1.4) < 0.03


def test_small_run_is_deterministic_and_complete():
    cfg = replace(C.scenario("adversaries", 7), n0=1500, burn_in=24, months=24)
    a, b = R.run(cfg), R.run(cfg)
    assert json.dumps(a, sort_keys=True, default=list) == json.dumps(b, sort_keys=True, default=list)
    assert set(a["series"]) == set(cfg.ledgers)
    assert len(a["series"]["L0"]["level"]) == 24
    assert "adversaries" in a and a["adversaries"]["L0"]["collusion"]["arranged_games"] > 0
    for name in ("deflation", "federations", "ratchet"):
        out = R.run(replace(C.scenario(name, 3), n0=800, burn_in=12, months=12))
        assert out["pool"]["players_end"] > 0
