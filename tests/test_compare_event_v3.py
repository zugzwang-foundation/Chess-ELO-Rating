"""The championship comparison of Freeze 3 (D-0011; ELO-6, Phase 3): columns (a), (b), (b0) and the PILOT table.

The tool is tools/compare_event_v3.py, frozen in Freeze 3 (D-0011, part B)."""
import math
import sys
from decimal import ROUND_HALF_UP, Decimal

from l0_helpers import ROOT, fixture, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
import compare_event as ce  # noqa: E402
import compare_event_v3 as v3  # noqa: E402

FX = fixture("validation", "us_championship_2025.json")
R2 = v3.load_rung2(v3.DEFAULT_TABLE, v3.DEFAULT_GUARD, "standard")
V1 = ce.load_params(ce.DEFAULT_PARAMS, "standard")


def _event(players, games):
    return {"event": {"name": "t", "start": "2026-10-09", "end": "2026-10-21", "chapter": "standard",
                      "rating_period": "2026-11", "list_in_force": "2026-10"},
            "players": [{"fide_id": i, "rating": r, "k": k} for i, r, k in players],
            "games": [{"round": n + 1, "board": 1, "white": w, "black": b, "result": res}
                      for n, (w, b, res) in enumerate(games)]}


def _e_fav(x: int, mid: int) -> Decimal:
    """The v2 table's entry at effective gap x >= 0 by hand (SPEC-TABLE-FIT v1.1 section 2), three decimals half up."""
    kappa, lam, _eta, alpha, beta, gamma, mu = R2.par
    l = (mid - 2000) / 400
    z = kappa * math.exp(lam * l) * math.log(10) / 400 * x
    nu = math.exp(alpha + beta * l - gamma * math.exp(mu * l) * z)
    e = (math.exp(z / 2) + nu / 2) / (math.exp(z / 2) + math.exp(-z / 2) + nu)
    return Decimal(repr(e)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def test_column_a_equals_fides_calculation_for_2025():
    c = v3.run("tools/events/us_championship_2025.json")
    rows = {r["fide_id"]: r for r in c.rows}
    assert c.counted == 66
    for p in FX["players"]:
        r = rows[p["fide_id"]]
        assert r["games"] == int(p["fide_tournament"]["n"])
        assert r["k"] == int(p["fide_tournament"]["K"])
        assert r["a"] == Decimal(p["fide_tournament"]["K_chg"])


def test_b0_is_freeze_2s_column_b_and_every_column_sums_to_zero_with_equal_k():
    c = v3.run("tools/events/us_championship_2025.json")
    frozen = ce.compare(ce.load_event("tools/events/us_championship_2025.json"), V1)
    for r, f in zip(c.rows, frozen.rows):
        assert (r["fide_id"], r["b0"], r["b0_rounded"]) == (f["fide_id"], f["b"], f["b_rounded"])
    assert c.pilot_b_equals_b0_tool
    for key in ("a", "b", "b0", "p"):
        assert sum(r[key] for r in c.rows) == 0
    assert R2.guarded and R2.scaled                       # Phase 2's outcome in standard (E12)


def test_column_b_by_hand_for_one_game():
    event = _event([(1, 2700, 10), (2, 2500, 20)], [(2, 1, "1-0"), (1, 2, None)])
    c = v3.compare(event, R2, V1, {})
    rows = {r["fide_id"]: r for r in c.rows}
    eta = R2.eta_whole
    e_white = 1 - _e_fav(2700 - 2500 - eta, 2650)         # White, the 2500, is the lower-rated: E(-x) = 1 - E(x)
    m = R2.k_scale[2650]
    assert c.counted == 1 and rows[2]["games"] == 1
    assert rows[2]["b"] == 20 * m * (1 - e_white)
    assert rows[1]["b"] == 10 * m * (0 - (1 - e_white))
    assert c.guard_games == 0                             # gap 200: outside the region


def test_the_narrowed_guard_binds_in_its_region():
    event = _event([(1, 2750, 10), (2, 2300, 20)], [(1, 2, "1/2-1/2")])   # gap 450, level 2525: weight 1
    c = v3.compare(event, R2, V1, {})
    rows = {r["fide_id"]: r for r in c.rows}
    x = 450 + R2.eta_whole                                # the favourite has White
    e_fit = _e_fav(x, 2550)
    t = ce.layer0.expected_score(x)                       # table 8.1.2 without the cap, at the colour-adjusted gap
    e = max(e_fit, t)
    assert c.guard_games == 1 and e == t
    m = R2.k_scale[2550]
    assert rows[1]["b"] == 10 * m * (Decimal("0.5") - e)
    assert rows[2]["b"] == 20 * m * (Decimal("0.5") - (1 - e))


def test_pilot_compensates_the_adult_side_only():
    event = _event([(1, 2450, 10), (2, 2300, 40)], [(1, 2, "1-0"), (2, 1, "1/2-1/2")])
    rung5 = {2: {"eligible": True, "c_j": 89}}
    c = v3.compare(event, R2, V1, rung5)
    rows = {r["fide_id"]: r for r in c.rows}
    m = R2.k_scale[2350]
    eta = R2.eta_whole
    e_b = [_e_fav(150 + eta, 2350), _e_fav(150 - eta, 2350)]               # the adult with White, then with Black
    e_p = [_e_fav(150 - 89 + eta, 2350), _e_fav(150 - 89 - eta, 2350)]     # against RX_j = 2300 + 89
    want = 10 * m * ((1 - e_p[0]) + (Decimal("0.5") - e_p[1])) - 10 * m * ((1 - e_b[0]) + (Decimal("0.5") - e_b[1]))
    assert c.compensated_games == 2 and rows[1]["p_minus_b"] == want
    assert rows[2]["p_minus_b"] == 0                      # the junior's own expectation uses published ratings
    assert c.opponents_diff == want


def test_every_column_runs_on_the_2026_files_and_counts_no_result():
    for path in ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json"):
        c = v3.run(path)
        assert c.counted == 0 and c.scheduled == 66 and c.guard_games == 0 and c.compensated_games == 0
        assert all(r[k] == 0 for r in c.rows for k in ("a", "b", "b0", "p"))
        text = v3.to_markdown(c) + v3.pilot_markdown(c)
        assert "first pre-registration, superseded" in text and "PILOT" in text and "PROVISIONAL" in text
