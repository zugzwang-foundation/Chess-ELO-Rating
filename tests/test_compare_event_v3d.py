"""Freeze 3d (D-0016, R66; ELO-9, Phase 0): every log-loss line read with the crossed interval (tools/compare_event_v3d.py).

Results are entered only in memory, on the synthetic event and the 2025 event; no 2026 result is read or written."""
import dataclasses
import json
import random
import sys

from l0_helpers import ROOT, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "analysis"))
import compare_event_v3 as v3  # noqa: E402
import compare_event_v3b as v3b  # noqa: E402
import compare_event_v3c as v3c  # noqa: E402
import compare_event_v3d as v3d  # noqa: E402
import e13_us_championships_freeze3c as e13c  # noqa: E402
import e13_us_championships_freeze3d as e13d  # noqa: E402

SYNTH = ROOT / "tests" / "fixtures" / "events" / "synthetic_double_round_robin.json"
R2 = v3.load_rung2(v3.DEFAULT_TABLE, v3.DEFAULT_GUARD, "standard")
RATES = v3b.load_draw_rates()
OUTCOMES = ("1-0", "1/2-1/2", "0-1")


def _synth(seed: int):
    event = json.loads(SYNTH.read_text(encoding="utf-8"))
    rnd = random.Random(seed)
    for g in event["games"]:
        g["result"] = rnd.choice(OUTCOMES)
    return event


def test_the_crossed_intervals_of_r54s_measures_equal_freeze_3cs():
    gs = v3c.games(_synth(4), R2, RATES)
    ll = v3d.log_loss_lines([gs])
    c = v3c.crossed([gs], v3b.MEASURES)
    for k in v3d.LL_KEYS:
        assert ll["all"][k] == c[k]


def test_every_log_loss_line_has_a_crossed_interval_around_its_mean():
    event, r2, *_ = v3b.load("tools/events/us_championship_2025.json")
    gs = v3c.games(event, r2, RATES)
    res, ll = v3c.reading([gs]), v3d.log_loss_lines([gs])
    for k in ("ll_a", "ll_bp", "ll_d"):
        lo, hi = ll["all"][k]
        assert lo <= res["measures"][k][0] <= hi
    lo, hi = ll["all"]["ll_d_shared"]
    assert lo <= res["shared"]["ll_d_shared"][0] <= hi
    lo, hi = ll["rounds_3_11"]["ll_d"]
    assert lo <= res["rounds_3_11"]["ll_d"][0] <= hi


def test_identical_columns_give_a_zero_crossed_interval():
    gs = v3c.games(_synth(5), R2, RATES)
    same = [dataclasses.replace(g, forecast=dataclasses.replace(g.forecast, e_bp=g.forecast.e_a, p_bp=g.forecast.p_a),
                                p_a_shared=g.forecast.p_a) for g in gs]
    ll = v3d.log_loss_lines([same])
    assert ll["all"]["ll_d"] == (0.0, 0.0) and ll["all"]["ll_d_shared"] == (0.0, 0.0)
    assert ll["rounds_3_11"]["ll_d"] == (0.0, 0.0)


def test_pooled_lines_and_empty_events():
    a, b = v3c.games(_synth(6), R2, RATES), v3c.games(_synth(7), R2, RATES)
    assert v3d.log_loss_lines([]) == {} and v3d.log_loss_lines([[], []]) == {}
    pooled = v3d.log_loss_lines([a, b])
    assert set(pooled) == {"all", "rounds_3_11"} and v3d.log_loss_lines([a, []]) == v3d.log_loss_lines([a])


def test_no_2026_result_is_scored():
    for path in ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json"):
        event, r2, *_ = v3b.load(path)
        assert all(g["result"] is None for g in event["games"])        # the file's results were never filled
        assert v3d.log_loss_lines([v3c.games(event, r2, RATES)]) == {}


def test_freeze_3d_extends_freeze_3c_with_three_files():
    assert set(e13c.FREEZE3C) < set(e13d.FREEZE3D) and len(e13d.NEW_IN_3D) == 3
    assert len(e13d.freeze3d_lines()) == len(e13c.freeze3c_lines()) + 3
