"""tools/compare_pilot.py: rung 2 with R17's guard equals the frozen comparison tool where the guard does not bind,
the guard where it binds, and rung 5 (PILOT) under R8."""
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402
import compare_pilot as cp  # noqa: E402
import layer0  # noqa: E402

PARAMS = ce.load_params(ce.DEFAULT_PARAMS, "standard")


def _event(players, games):
    return {"event": {"name": "test", "start": "2026-10-09", "end": "2026-10-21", "chapter": "standard",
                      "rating_period": "2026-11", "list_in_force": "2026-10"},
            "players": [{"fide_id": i, "rating": r, "k": k} for i, r, k in players],
            "games": [{"round": 1, "white": w, "black": b, "result": res} for w, b, res in games]}


def test_column_b_equals_the_frozen_tool_without_the_guard():
    event = ce.load_event("tools/events/us_championship_2025.json")
    frozen = ce.compare(event, PARAMS)
    pilot = cp.compare(event, PARAMS, {})
    assert pilot.counted == frozen.counted == 66
    assert pilot.guard_games == 0 and pilot.compensated_games == 0
    for a, b in zip(frozen.rows, pilot.rows):
        assert a["fide_id"] == b["fide_id"] and a["k"] == b["k"]
        assert a["b"] == b["b"] and a["b_rounded"] == b["b_rounded"]
        assert b["p"] == b["b"] and b["difference"] == 0


def test_guard_binds_in_its_region():
    event = _event([(1, 2600, 10), (2, 2100, 20)], [(1, 2, "1-0")])
    out = cp.compare(event, PARAMS, {})
    assert out.guard_games == 1
    fav, und = (r for r in out.rows if r["fide_id"] == 1), (r for r in out.rows if r["fide_id"] == 2)
    fav, und = next(fav), next(und)
    h = layer0.expected_score(500)                     # table 8.1.2 at the full gap: 0.96 [V 1]
    assert fav["b"] == 10 * (Decimal(1) - h)
    assert und["b"] == 20 * (Decimal(0) - (Decimal(1) - h))


def test_rung5_pilot_under_r8():
    players = [(1, 1900, 20), (2, 1500, 40), (3, 1500, 40)]
    games = [(1, 2, "1/2-1/2"), (2, 3, "1-0")]
    rung5 = {2: {"eligible": True, "c_j": 197}, 3: {"eligible": True, "c_j": 100}}
    out = cp.compare(_event(players, games), PARAMS, rung5)
    rows = {r["fide_id"]: r for r in out.rows}
    mid = ce.band_mid((1900 + 1500) // 2)
    e_adult = ce.rung2_expected(1900 - 1697 + PARAMS.eta_whole, mid, PARAMS)    # RX = 1500 + 197 (annex T10.1)
    assert rows[1]["p"] == 20 * (Decimal("0.5") - e_adult)
    assert rows[1]["b"] == 20 * (Decimal("0.5") - ce.rung2_expected(400 + PARAMS.eta_whole, mid, PARAMS))
    assert rows[2]["p"] == rows[2]["b"] and rows[3]["p"] == rows[3]["b"]     # juniors: published ratings; R8 between them
    assert out.compensated_games == 1
    assert out.opponents_diff == rows[1]["p"] - rows[1]["b"]
