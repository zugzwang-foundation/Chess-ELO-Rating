"""SPEC-COMPARE §4: tools/compare_event.py against FIDE (2025 US Championship) and by hand."""
import math
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal

import pytest

from l0_helpers import ROOT, fixture, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
import compare_event  # noqa: E402

FX = fixture("validation", "us_championship_2025.json")


def run(event_file: str):
    event = compare_event.load_event(event_file)
    return compare_event.compare(event, compare_event.load_params(compare_event.DEFAULT_PARAMS, event["event"]["chapter"]))


def test_column_a_equals_fides_calculation_for_2025():
    rows = {r["fide_id"]: r for r in run("tools/events/us_championship_2025.json").rows}
    for p in FX["players"]:
        r = rows[p["fide_id"]]
        assert r["games"] == int(p["fide_tournament"]["n"])
        assert r["k"] == int(p["fide_tournament"]["K"])
        assert r["a"] == Decimal(p["fide_tournament"]["K_chg"])


def test_both_columns_sum_to_zero_with_equal_k():
    rows = run("tools/events/us_championship_2025.json").rows
    assert sum(r["a"] for r in rows) == 0
    assert sum(r["b"] for r in rows) == 0


def test_column_b_by_hand_for_one_game():
    event = {"event": {"name": "t", "start": "2026-10-09", "end": "2026-10-09", "chapter": "standard",
                       "rating_period": "2026-11", "list_in_force": "2026-10"},
             "players": [{"fide_id": 1, "rating": 2700, "k": 10}, {"fide_id": 2, "rating": 2500, "k": 20}],
             "games": [{"round": 1, "board": 1, "white": 2, "black": 1, "result": "1-0"},
                       {"round": 2, "board": 1, "white": 1, "black": 2, "result": None}]}
    p = compare_event.load_params(compare_event.DEFAULT_PARAMS, "standard")
    eta = int(Decimal(repr(p.eta)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    x = 2500 - 2700 + eta                              # White is the lower-rated player
    z = p.kappa * math.log(10) / 400 * abs(x)
    nu = math.exp(p.alpha + p.beta * (2650 - 2000) / 400 - p.gamma * z)   # level 2600 -> band 2600-2699, midpoint 2650
    e_abs = Decimal(repr((math.exp(z / 2) + nu / 2) / (math.exp(z / 2) + math.exp(-z / 2) + nu))).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP)
    e_white = Decimal(1) - e_abs                       # x < 0: E(-x) = 1 - E(x)
    c = compare_event.compare(event, p)
    rows = {r["fide_id"]: r for r in c.rows}
    assert c.counted == 1 and rows[2]["games"] == 1    # the unplayed game is not counted
    assert rows[2]["b"] == 20 * (1 - e_white)
    assert rows[1]["b"] == 10 * (0 - (1 - e_white))


@pytest.mark.parametrize("switch", ["--rung4", "--rung5"])
def test_switches_refuse_on(switch):
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "compare_event.py"),
                           "tools/events/us_championship_2025.json", switch, "on"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Layer 1" in proc.stderr


def test_outputs_carry_the_label():
    c = run("tools/events/us_championship_2025.json")
    md, csv_text = compare_event.to_markdown(c), compare_event.to_csv(c)
    for text in (md, csv_text):
        assert "params/table_fit_2026-10.yaml" in text and "PROVISIONAL-FITTED" in text and "Method:" in text
    assert csv_text.splitlines()[3].startswith("fide_id,")
