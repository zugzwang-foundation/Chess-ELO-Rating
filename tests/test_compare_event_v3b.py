"""Freeze 3b (D-0014, part A; ELO-8, Phase 0): what the pairings fix (R55), the PILOT on (b′) (R56) and the forecast test
(R54), in tools/compare_event_v3b.py.

Results are entered only in memory, on the synthetic event kept apart from the 2026 files (tests/fixtures/events/) and on
the 2025 event; no 2026 result is read, entered or written."""
import copy
import dataclasses
import json
import math
import random
import sys
from decimal import Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "analysis"))
import compare_event as ce  # noqa: E402
import compare_event_v3 as v3  # noqa: E402
import compare_event_v3a as v3a  # noqa: E402
import compare_event_v3b as v3b  # noqa: E402
import e6_rungs_extract as e6  # noqa: E402  (E6's three-outcome split, which v3b restates)
import e13_us_championships_freeze3a as e13a  # noqa: E402
import e13_us_championships_freeze3b as e13b  # noqa: E402
import set_results as sr  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

SYNTH = ROOT / "tests" / "fixtures" / "events" / "synthetic_double_round_robin.json"
R2 = v3.load_rung2(v3.DEFAULT_TABLE, v3.DEFAULT_GUARD, "standard")
V1 = ce.load_params(ce.DEFAULT_PARAMS, "standard")
RATES = v3b.load_draw_rates()
OUTCOMES = ("1-0", "1/2-1/2", "0-1")


def _synth(results=None):
    event = json.loads(SYNTH.read_text(encoding="utf-8"))
    for i, g in enumerate(event["games"]):
        g["result"] = None if results is None else results[i]
    return event


def _rows(f: v3b.Fixed):
    return [{k: r[k] for k in ("fide_id", "games", "bp_minus_a", "b0_minus_a", "b_const", "b_span", "pilot_bp",
                               "pilot_b")} for r in f.rows]


def test_the_fixed_figures_do_not_depend_on_the_results():
    base = v3b.fixed_by_pairings(_synth(), R2, V1, {})
    rnd = random.Random(1)
    for results in (["1/2-1/2"] * 12, ["0-1"] * 12, [rnd.choice(OUTCOMES) for _ in range(12)],
                    [rnd.choice(OUTCOMES) for _ in range(12)]):
        f = v3b.fixed_by_pairings(_synth(results), R2, V1, {})
        assert _rows(f) == _rows(base) and f.games == base.games == 12


def test_bprime_and_b0_minus_a_equal_the_frozen_tools_on_any_complete_results():
    rnd = random.Random(2)
    results = [rnd.choice(OUTCOMES) for _ in range(12)]
    event = _synth(results)
    f = v3b.fixed_by_pairings(event, R2, V1, {})
    c = v3a.compare(event, R2, V1, {})
    for r, x in zip(f.rows, c.rows):
        assert r["fide_id"] == x["fide_id"]
        assert r["bp_minus_a"] == x["bp"] - x["a"] and r["b0_minus_a"] == x["b0"] - x["a"]
        assert r["b_const"] <= x["b_minus_a"] <= r["b_const"] + r["b_span"]


def test_b_minus_a_is_c_plus_k_times_m_minus_1_times_the_score():
    rnd = random.Random(3)
    event = _synth([rnd.choice(OUTCOMES) for _ in range(12)])
    f = v3b.fixed_by_pairings(event, R2, V1, {})
    c = v3a.compare(event, R2, V1, {})
    rating = {p["fide_id"]: p["rating"] for p in event["players"]}
    for r, x in zip(f.rows, c.rows):
        pid = r["fide_id"]
        part = sum(((v3.scale(R2, rating[g["white"]], rating[g["black"]]) - 1)
                    * ce.SCORE[g["result"]][0 if g["white"] == pid else 1])
                   for g in event["games"] if pid in (g["white"], g["black"]))
        assert x["b_minus_a"] == r["b_const"] + r["k"] * part


def test_a_game_not_counted_removes_exactly_its_term():
    event = _synth()
    event["games"][0]["result"] = sr.UNPLAYED              # 9000001 (White) against 9000004
    full = v3b.fixed_by_pairings(_synth(), R2, V1, {})
    less = v3b.fixed_by_pairings(event, R2, V1, {})
    assert less.games == 11 and less.unplayed == 1
    g = event["games"][0]
    rating = {p["fide_id"]: p["rating"] for p in event["players"]}
    rw, rb = rating[g["white"]], rating[g["black"]]
    for a, b in zip(full.rows, less.rows):
        if a["fide_id"] not in (g["white"], g["black"]):
            assert _rows(v3b.Fixed(None, [a], 0, 0, 0, 0, 0)) == _rows(v3b.Fixed(None, [b], 0, 0, 0, 0, 0))
            continue
        white = a["fide_id"] == g["white"]
        own, opp = (rw, rb) if white else (rb, rw)
        e_a = v3b.layer0.expected_score(v3b.layer0.effective_difference(own, opp, "standard",
                                                                        v3b.date.fromisoformat("2030-01-01")))
        e_b = v3.expectation(R2, own, opp, white, rw, rb, own > opp)[0]
        assert b["games"] == a["games"] - 1
        assert a["bp_minus_a"] - b["bp_minus_a"] == a["k"] * (e_a - e_b)


def test_the_pilot_on_bprime_is_freeze_3s_pilot_without_m():
    for path, today, before in (("tools/events/us_championship_2026.json", Decimal("14.73"), Decimal("24.22")),
                                ("tools/events/us_womens_championship_2026.json", Decimal("0.61"), Decimal("0.89"))):
        event, r2, v1, rung5, rung5_path = v3b.load(path)
        f = v3b.fixed_by_pairings(event, r2, v1, rung5, rung5_path)
        assert round(f.pilot_bp_total, 2) == today and round(f.pilot_b_total, 2) == before
        t = v3.compare(v3b.played_copy(event, "1-0"), dataclasses.replace(r2, scaled=False), v1, rung5, rung5_path)
        assert f.pilot_bp_total == t.opponents_diff
        assert all(e["result"] is None for e in event["games"])     # the file's results were never filled


def test_three_way_is_e6s():
    for e in (0.0, 0.001, 0.2, 0.5, 0.73, 0.999, 1.0):
        for d in (0.0, 0.3, 0.6, 0.95):
            assert v3b.three_way(e, d) == e6.three_way(e, d)


def test_v2_draw_is_the_models_draw_probability_at_the_effective_gap():
    par0 = list(R2.par)
    par0[2] = 0.0
    for x in (-300, -36, 0, 36, 120, 450):
        for mid in (1450, 2250, 2750, 2850):
            assert math.isclose(v3b.v2_draw(R2, x, mid), t2.probs(tuple(par0), x, mid)[1], rel_tol=1e-12)


def test_the_forecasts_by_hand():
    event = _synth(["1-0", "1/2-1/2"] + [sr.UNPLAYED, None] + ["0-1"] * 8)
    games = v3b.game_forecasts(event, R2, RATES)
    assert len(games) == 10                                   # the marker and no result are not counted
    g = games[0]                                              # 9000001 (2650) beat 9000004 (2290) with White
    e_a = float(v3b.layer0.expected_score(360))
    assert g.e_a == e_a and g.s == 1.0
    mid = t2.band_mid((2650 + 2290) // 2)
    d = min(RATES[mid], 2 * e_a - 0.002, 2 * (1 - e_a) - 0.002)     # the band's rate, capped: 0.90 leaves 0.198
    assert d < RATES[mid] and g.p_a == (e_a - d / 2, d, 1 - e_a - d / 2)
    e_bp = float(t2.published(360 + R2.eta_whole, mid, R2.par))
    assert g.e_bp == e_bp
    assert math.isclose(g.values["ll_a"], -math.log(e_a - d / 2))
    assert math.isclose(g.values["br_bp"], (1 - e_bp) ** 2)
    assert math.isclose(games[1].values["ll_bp"], -math.log(games[1].p_bp[1]))


def test_the_bootstrap_is_paired_deterministic_and_centred():
    event = _synth([random.Random(4).choice(OUTCOMES) for _ in range(12)])
    games = v3b.game_forecasts(event, R2, RATES)
    a, b = v3b.forecast_test([games]), v3b.forecast_test([games])
    assert a == b and a["games"] == 12 and a["players"] == 4
    for k in v3b.MEASURES:
        mean, (glo, ghi), (plo, phi) = a[k]
        assert glo <= mean <= ghi and plo <= mean <= phi
    same = [dataclasses.replace(g, e_bp=g.e_a, p_bp=g.p_a) for g in games]   # identical columns: a zero difference
    z = v3b.forecast_test([same])
    assert z["ll_d"] == (0.0, (0.0, 0.0), (0.0, 0.0)) and z["br_d"] == (0.0, (0.0, 0.0), (0.0, 0.0))
    pooled = v3b.forecast_test([games, same])
    assert pooled["games"] == 24 and pooled["players"] == 8
    assert v3b.forecast_test([[]]) is None


def test_the_2026_files_hold_no_result_and_the_test_is_pending():
    for path in ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json"):
        event = ce.load_event(path)
        assert not v3a.complete(event)
        assert v3b.game_forecasts(event, R2, RATES) == []


def test_freeze_3b_extends_freeze_3a_with_five_files():
    assert set(e13a.FREEZE3A) < set(e13b.FREEZE3B)
    assert sorted(set(e13b.FREEZE3B) - set(e13a.FREEZE3A)) == sorted(e13b.NEW_IN_3B) and len(e13b.NEW_IN_3B) == 5
    assert len(e13b.freeze3b_lines()) == len(e13a.freeze3a_lines()) + 5


def test_the_draw_rates_are_counts_over_the_window():
    d = json.loads((ROOT / "params" / "draw_rate_2026-10b.json").read_text(encoding="utf-8"))
    assert d["window"] == ["2023-10", "2026-09"] and sorted(int(k) for k in d["bands"]) == list(t2.BAND_MIDS)
    assert sum(b["games"] for b in d["bands"].values()) == d["reproduces_E11"]["E11_games"]
    for b in d["bands"].values():
        assert b["rate"] == round(b["draws"] / b["games"], 6)


def test_played_copy_never_keeps_a_result():
    event = _synth(["1-0"] * 6 + [sr.UNPLAYED] + ["0-1"] * 5)
    ev = v3b.played_copy(copy.deepcopy(event), "1/2-1/2")
    assert [g["result"] for g in ev["games"]] == ["1/2-1/2"] * 6 + [sr.UNPLAYED] + ["1/2-1/2"] * 5
