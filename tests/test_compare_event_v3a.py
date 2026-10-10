"""Freeze 3a (D-0012; ELO-7, Phase 0): column (b′) and the rule for a game not played (R43, R45).

The tools are tools/compare_event_v3a.py and tools/set_results.py, frozen in Freeze 3a (D-0012). The rule for a game not
played is tested on a synthetic event file kept apart from the 2026 event files (tests/fixtures/events/), copied to a
temporary directory before any result is entered; no 2026 file is written."""
import dataclasses
import json
import math
import shutil
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "analysis"))
import compare_event as ce  # noqa: E402
import compare_event_v3 as v3  # noqa: E402
import compare_event_v3a as v3a  # noqa: E402
import e3_us_championships as e3  # noqa: E402  (the event file's hash without its results)
import e13_us_championships_freeze3 as e13  # noqa: E402
import e13_us_championships_freeze3a as e13a  # noqa: E402
import set_results as sr  # noqa: E402

SYNTH = ROOT / "tests" / "fixtures" / "events" / "synthetic_double_round_robin.json"
Y2025 = "tools/events/us_championship_2025.json"
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


def _copy(tmp_path):
    path = tmp_path / "event.json"
    shutil.copy(SYNTH, path)
    return path


def _enter(path, rnd, *results, ok=True):
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "set_results.py"), str(path), str(rnd), *results],
                          capture_output=True, text=True)
    assert (proc.returncode == 0) == ok, proc.stderr
    return json.loads(path.read_text(encoding="utf-8"))


def _all_rounds(path, unplayed=()):
    """Enter every round of the synthetic event: White wins on board 1, a draw on board 2, except (round, board) pairs in
    `unplayed`, which get the marker."""
    for rnd in range(1, 7):
        given = [sr.UNPLAYED if (rnd, b) in unplayed else ("1-0" if b == 1 else "1/2-1/2") for b in (1, 2)]
        event = _enter(path, rnd, *given)
    return event


def test_bprime_on_2025_is_column_b_without_m_and_the_other_columns_are_freeze_3s():
    c = v3a.run(Y2025)
    base = v3.run(Y2025)
    today = v3.compare(ce.load_event(Y2025), dataclasses.replace(R2, scaled=False), V1, {})
    for r, b, t in zip(c.rows, base.rows, today.rows):
        assert all(r[k] == b[k] for k in ("fide_id", "a", "a_rounded", "b", "b_rounded", "b0", "b0_rounded", "p"))
        assert (r["bp"], r["bp_rounded"]) == (t["b"], t["b_rounded"])
    assert c.complete and c.unplayed == 0 and c.counted == 66
    assert sum(r["bp"] for r in c.rows) == 0                  # equal K: (b′) creates no points
    bl = v3a.blanks(c)
    # E16 §7's "v2 table and guard at today's K", (b) "as frozen" and (b0), on 2025's results
    assert (bl["MEAN_ABS_DIFF"], bl["MAX_DIFF"], bl["N_DIFFER"]) == ("1.94", "-4.30", "10 of 12")
    assert (bl["B_MEAN_ABS_DIFF"], bl["B_MAX_DIFF"], bl["B_N_DIFFER"]) == ("5.49", "+12.05", "12 of 12")
    assert (bl["B0_MEAN_ABS_DIFF"], bl["B0_MAX_DIFF"], bl["B0_N_DIFFER"]) == ("3.33", "-7.00", "11 of 12")


def test_bprime_by_hand_for_one_game_uses_todays_k_without_m():
    event = _event([(1, 2700, 10), (2, 2500, 20)], [(2, 1, "1-0"), (1, 2, None)])
    c = v3a.compare(event, R2, V1, {})
    rows = {r["fide_id"]: r for r in c.rows}
    e_white = 1 - _e_fav(2700 - 2500 - R2.eta_whole, 2650)    # White, the 2500, is the lower-rated
    assert c.counted == 1 and not c.complete                  # round 2 has no result yet
    assert rows[2]["bp"] == 20 * (1 - e_white)
    assert rows[1]["bp"] == 10 * (0 - (1 - e_white))
    m = R2.k_scale[2650]
    assert m != 1 and rows[2]["b"] == m * rows[2]["bp"] and rows[1]["b"] == m * rows[1]["bp"]


def test_the_marker_for_a_game_not_played_is_distinct_from_no_result_yet(tmp_path):
    path = _copy(tmp_path)
    event = _enter(path, 1, "1-0", sr.UNPLAYED)
    games = {(g["round"], g["board"]): g for g in event["games"]}
    assert games[(1, 1)]["result"] == "1-0" and games[(1, 2)]["result"] == sr.UNPLAYED
    assert [(x["round"], x["board"], x["result"]) for x in event["results_read"]] == [(1, 1, "1-0"), (1, 2, sr.UNPLAYED)]
    assert all(x["read_utc"].endswith("Z") for x in event["results_read"])
    event = _enter(path, 1, "-", sr.UNPLAYED)                 # "-" clears a board: no result yet
    games = {(g["round"], g["board"]): g for g in event["games"]}
    assert games[(1, 1)]["result"] is None and games[(1, 2)]["result"] == sr.UNPLAYED
    _enter(path, 1, "1-0F", "1-0", ok=False)                  # only the listed markers are accepted


def test_an_event_is_complete_when_every_game_has_a_result_or_the_marker(tmp_path):
    path = _copy(tmp_path)
    for rnd in range(1, 6):
        _enter(path, rnd, "1-0", sr.UNPLAYED if rnd == 3 else "0-1")
    c = v3a.compare(json.loads(path.read_text(encoding="utf-8")), R2, V1, {})
    assert not c.complete and c.counted == 9 and c.unplayed == 1
    _enter(path, 6, "1/2-1/2", "-")
    assert not v3a.complete(json.loads(path.read_text(encoding="utf-8")))
    _enter(path, 6, "1/2-1/2", "0-1")
    c = v3a.compare(json.loads(path.read_text(encoding="utf-8")), R2, V1, {})
    assert c.complete and c.counted == 11 and c.unplayed == 1 and c.scheduled == 12


def test_a_game_not_played_is_excluded_from_every_column(tmp_path):
    path = _copy(tmp_path)
    marked = json.loads(json.dumps(_all_rounds(path, unplayed={(2, 1), (5, 2)})))
    dropped = json.loads(json.dumps(marked))
    dropped["games"] = [g for g in dropped["games"] if g["result"] != sr.UNPLAYED]
    a, b = v3a.compare(marked, R2, V1, {}), v3a.compare(dropped, R2, V1, {})
    assert a.complete and a.counted == b.counted == 10 and a.unplayed == 2
    keys = ("fide_id", "k", "games", "score", "a", "a_rounded", "bp", "bp_rounded", "b", "b_rounded", "b0",
            "b0_rounded", "p")
    assert [tuple(r[k] for k in keys) for r in a.rows] == [tuple(r[k] for k in keys) for r in b.rows]


def test_k_times_n_counts_played_games_only():
    # Two players with K 40 meet 18 times; the 18th game is not played. FIDE's K x n <= 700 counts 17 games (K stays 40);
    # counting the unplayed game would cut K to 700/18.
    games = [(1, 2, "1/2-1/2") if i % 2 == 0 else (2, 1, "1-0") for i in range(17)] + [(1, 2, sr.UNPLAYED)]
    c = v3a.compare(_event([(1, 2000, 40), (2, 2000, 40)], games), R2, V1, {})
    rows = {r["fide_id"]: r for r in c.rows}
    assert c.complete and c.counted == 17 and rows[1]["games"] == 17 and rows[1]["k"] == 40
    full = v3a.compare(_event([(1, 2000, 40), (2, 2000, 40)], games[:17] + [(1, 2, "1-0")]), R2, V1, {})
    assert {r["fide_id"]: r for r in full.rows}[1]["k"] < 40


def test_the_blanks_count_played_games_and_the_players_who_played(tmp_path):
    path = _copy(tmp_path)
    withdrawn = 9000004
    event = json.loads(SYNTH.read_text(encoding="utf-8"))
    out = {(g["round"], g["board"]) for g in event["games"] if withdrawn in (g["white"], g["black"])}
    c = v3a.compare(_all_rounds(path, unplayed=out), R2, V1, {})
    assert c.complete and c.unplayed == 6 and c.counted == 6
    bl = v3a.blanks(c)
    played = [r for r in c.rows if r["games"] > 0]
    assert len(played) == 3 and bl["GAMES"] == "6"
    assert bl["N_DIFFER"].endswith(" of 3") and bl["B_N_DIFFER"].endswith(" of 3") and bl["B0_N_DIFFER"].endswith(" of 3")
    mean = sum(abs(r["bp"] - r["a"]) for r in played) / 3
    assert bl["MEAN_ABS_DIFF"] == f"{mean:.2f}"


def test_entering_results_or_the_marker_leaves_the_frozen_event_hash_unchanged(tmp_path):
    path = _copy(tmp_path)
    before = e3.event_sha_without_results(str(path))
    _all_rounds(path, unplayed={(4, 2)})
    assert e3.event_sha_without_results(str(path)) == before


def test_the_2026_files_hold_no_result_and_are_pending():
    for path in ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json"):
        c = v3a.run(path)
        assert c.counted == 0 and c.unplayed == 0 and c.scheduled == 66 and not c.complete
        assert all(r[k] == 0 for r in c.rows for k in ("a", "bp", "b", "b0", "p"))
        text = v3a.to_markdown(c) + v3a.pilot_markdown(c)
        assert "first pre-registration, superseded" in text and "PILOT" in text and "PROVISIONAL" in text


def test_freeze_3a_lists_freeze_3s_files_and_the_new_ones():
    assert set(e13.FREEZE3) < set(e13a.FREEZE3A)
    assert set(e13a.FREEZE3A) - set(e13.FREEZE3) == {"analysis/e13_us_championships_freeze3a.py",
                                                      "tools/compare_event_v3a.py"}
    assert set(e13a.CHANGED_BY_3A) <= set(e13.FREEZE3)
    assert len(e13a.freeze3a_lines()) == len(e13.FREEZE3) + 2 + 2
