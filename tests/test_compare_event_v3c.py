"""Freeze 3c (D-0015; ELO-8, Phase 6): how the forecast test is read (tools/compare_event_v3c.py).

Results are entered only in memory, on the synthetic event and the 2025 event; no 2026 result is read or written."""
import dataclasses
import json
import math
import random
import sys

from l0_helpers import ROOT, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "analysis"))
import compare_event_v3 as v3  # noqa: E402
import compare_event_v3b as v3b  # noqa: E402
import compare_event_v3c as v3c  # noqa: E402
import e13_us_championships_freeze3b as e13b  # noqa: E402
import e13_us_championships_freeze3c as e13c  # noqa: E402

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


def test_one_draw_model_splits_a_with_bprimes_draw_probability():
    for g in v3c.games(_synth(1), R2, RATES):
        f = g.forecast
        assert g.p_a_shared[0] + g.p_a_shared[1] / 2 == min(max(f.e_a, 0.002), 0.998)
        assert g.p_a_shared[1] <= f.p_bp[1] + 1e-12 or g.p_a_shared[1] < 2 * min(f.e_a, 1 - f.e_a)


def test_the_crossed_bootstrap_is_deterministic_and_zero_for_identical_columns():
    gs = v3c.games(_synth(2), R2, RATES)
    a, b = v3c.crossed([gs], v3b.MEASURES), v3c.crossed([gs], v3b.MEASURES)
    assert a == b
    same = [dataclasses.replace(g, forecast=dataclasses.replace(g.forecast, e_bp=g.forecast.e_a, p_bp=g.forecast.p_a))
            for g in gs]
    z = v3c.crossed([same], v3b.MEASURES)
    assert z["ll_d"] == (0.0, 0.0) and z["br_d"] == (0.0, 0.0)


def test_the_reading_on_2025_has_its_primary_sentence_and_its_secondary_lines():
    event, r2, *_ = v3b.load("tools/events/us_championship_2025.json")
    res = v3c.reading([v3c.games(event, r2, RATES)])
    lo, hi = res["primary"]["lo"], res["primary"]["hi"]
    side = "below" if hi < 0 else "above" if lo > 0 else "across"
    assert res["primary"]["side"] == side and res["primary"]["sentence"].startswith(v3c.SENTENCES[side][:30])
    assert res["rounds_3_11"]["games"] == 54 and res["games"] == 66
    assert res["measures"] == v3b.forecast_test([v3b.game_forecasts(event, r2, RATES)])


def test_what_the_pairings_fix_about_the_test():
    for path in ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json"):
        event, r2, *_ = v3b.load(path)
        x = v3c.expected_if_bp_right(event, r2, RATES)
        assert x["games"] == 66 and x["ll_advantage"] >= x["ll_advantage_one_draw_model"] >= 0
        assert x["brier_advantage"] >= 0
        assert all(g["result"] is None for g in event["games"])        # the file's results were never filled
        assert v3c.games(event, r2, RATES) == []                        # no result, no forecast scored


def test_kl_is_the_expected_log_loss_advantage():
    gs = v3c.games(_synth(3), R2, RATES)
    g = gs[0].forecast
    kl = sum(b * math.log(b / a) for b, a in zip(g.p_bp, g.p_a))
    exp = sum(pb * (v3b._ll(g.p_a, s) - v3b._ll(g.p_bp, s)) for pb, s in zip(g.p_bp, (1.0, 0.5, 0.0)))
    assert math.isclose(kl, exp, rel_tol=1e-12)


def test_freeze_3c_extends_freeze_3b_with_three_files():
    assert set(e13b.FREEZE3B) < set(e13c.FREEZE3C) and len(e13c.NEW_IN_3C) == 3
    assert len(e13c.freeze3c_lines()) == len(e13b.freeze3b_lines()) + 3
