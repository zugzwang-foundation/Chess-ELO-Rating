#!/usr/bin/env python3
"""Freeze 3b (docs/decisions/D-0014_forecast-test-and-rulings.md, part A; ELO-8, Phase 0): what the pairings and the
October ratings fix, the PILOT rebuilt on (b′), and the pre-registered forecast test that depends on the results.

Three computations on one event file (tools/events/*.json), on top of Freeze 3a's columns (tools/compare_event_v3a.py
and tools/compare_event_v3.py, unchanged):

1. Fixed by the pairings (R55). Per player, assuming every game is played (a game marked not played under D-0013 removes
   its term): (b′) − (a) = K × Σ(E_a − E_b′) and (b0) − (a), where the score cancels; the PILOT's difference per player
   and the opponents' total, on (b′) at today's K (R56) and on (b) with K × m (withdrawn, superseded); and for (b) − (a),
   which the score enters through m, only what the pairings fix: (b) − (a) = C + K × Σ (m − 1) × score, so C (the value
   with no point scored) and C + W (every game won), W = K × Σ (m − 1). The values come from Freeze 3a's own code, run on
   two copies of the event in which every game not marked not played carries a placeholder result (all draws; all wins
   for White); the two runs must agree exactly, and agree with the direct sums, so that no value depends on a result.
   No real result is read: the copies overwrite whatever the file holds.
2. The PILOT on (b′) (R56): Freeze 3's rung 5 (params/rung5_us2026.json, frozen in Freeze 2) on top of (b′), the same
   computation as Freeze 3's PILOT on (b) with the slope ratio switched off.
3. The forecast test (R54), on every counted game (1-0, 1/2-1/2, 0-1; a game marked not played, or without a result, is
   not counted, D-0013): the per-game three-outcome log-loss (nats) and the expected-score Brier score of FIDE's
   expectation, column (a) (table 8.1.2 as FIDE applies it, Layer 0, on the October 2026 ratings), and of rung 2's,
   column (b′) (Freeze 3's v2 table, its narrowed guard and its colour term: the expectation column (b′) uses). Table
   8.1.2 has no draw model, so (a)'s three outcomes split its expected score with the draw rate of the game's 100-point
   level band in the v2 table's training months (params/draw_rate_2026-10b.json; E2's construction); (b′)'s split its
   expectation with the v2 model's own draw probability at the game's effective gap (eta whole) and band. Both splits
   use E6's rule: E clipped to [0.002, 0.998], the draw share capped so that no outcome falls below 0.001. The Brier
   score uses each column's own expectation, (S − E)². Each game is scored from White's side (no pairing of either
   field has a gap beyond 400, so White's and Black's views coincide). Means per event and pooled, the difference
   (b′) − (a), and percentile bootstrap 95 % intervals, 2,000 resamples, seed 20261009 (annex T8.5's), over games
   (games resampled within each event) and over players (players resampled within each event, each bringing all its
   counted games, so a game enters once for each of its players drawn), paired across the columns.

Python standard library only.

Usage:
  python3 tools/compare_event_v3b.py tools/events/us_championship_2026.json [tools/events/us_womens_championship_2026.json]
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import io
import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402  (Freeze 1's tool, unchanged)
import compare_event_v3 as v3  # noqa: E402  (Freeze 3's tool, unchanged)
import compare_event_v3a as v3a  # noqa: E402  (Freeze 3a's tool, unchanged)
import set_results as sr  # noqa: E402  (the marker for a game not played)
import layer0  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

DEFAULT_DRAW_RATE = "params/draw_rate_2026-10b.json"
SEED = 20261009
RESAMPLES = 2000
PLACEHOLDERS = ("1/2-1/2", "1-0")
FIXED = "fixed by the pairings and the October ratings — the same whatever the results"
SUPERSEDED_PILOT = "PILOT on (b) with K × m: withdrawn (R56), reported once, superseded"
MEASURES = ("ll_a", "ll_bp", "ll_d", "br_a", "br_bp", "br_d")
TEST_BLANKS = (("LL_A", "ll_a", False), ("LL_BP", "ll_bp", False), ("LL_DIFF", "ll_d", True),
               ("BRIER_A", "br_a", False), ("BRIER_BP", "br_bp", False), ("BRIER_DIFF", "br_d", True))
SMALL_SAMPLE = ("The sample is small (at most 66 games an event, 132 in all): the difference may favour either column, "
                "or neither, and it is reported whatever it shows.")


# ------------------------------------------------------------------ 1. what the pairings fix (R55)
def played_copy(event: dict, placeholder: str) -> dict:
    """A copy of the event in which every game not marked not played carries `placeholder` as its result: R55's
    "assuming every game is played". Any result the file holds is overwritten, never read."""
    ev = copy.deepcopy(event)
    for g in ev["games"]:
        if g.get("result") != sr.UNPLAYED:
            g["result"] = placeholder
    return ev


def _terms(event: dict, r2: v3.Rung2) -> dict[int, dict]:
    """Per player, over the games not marked not played: n, sum(E_a - E_b′), sum(E_a - m E_b) and sum(m - 1)."""
    ev = event["event"]
    chapter, start = ev["chapter"], date.fromisoformat(ev["start"])
    players = {p["fide_id"]: p for p in event["players"]}
    acc = {pid: {"n": 0, "bp": Decimal(0), "b": Decimal(0), "m1": Decimal(0)} for pid in players}
    for g in event["games"]:
        if g.get("result") == sr.UNPLAYED:
            continue
        w, b = g["white"], g["black"]
        rw, rb = players[w]["rating"], players[b]["rating"]
        m = v3.scale(r2, rw, rb)
        for pid, own, opp, white in ((w, rw, rb, True), (b, rb, rw, False)):
            e_a = layer0.expected_score(layer0.effective_difference(own, opp, chapter, start))
            e_b, _bind = v3.expectation(r2, own, opp, white, rw, rb, own > opp)
            a = acc[pid]
            a["n"] += 1
            a["bp"] += e_a - e_b
            a["b"] += e_a - m * e_b
            a["m1"] += m - 1
    return acc


@dataclass
class Fixed:
    event: dict
    rows: list[dict]
    games: int                     # games counted when every game not marked not played is played
    unplayed: int
    compensated_games: int
    pilot_bp_total: Decimal        # the PILOT on (b′): the opponents' total change minus (b′)
    pilot_b_total: Decimal         # the PILOT on (b), with K x m: withdrawn, superseded


def fixed_by_pairings(event: dict, r2: v3.Rung2, v1: ce.Params, rung5: dict[int, dict],
                      rung5_path: str = v3.DEFAULT_RUNG5) -> Fixed:
    runs = []
    for ph in PLACEHOLDERS:
        ev = played_copy(event, ph)
        c = v3a.compare(ev, r2, v1, rung5, rung5_path)                                     # (a), (b′), (b), (b0)
        t = v3.compare(ev, dataclasses.replace(r2, scaled=False), v1, rung5, rung5_path)  # the PILOT on (b′)
        runs.append((ev, c, t))
    acc = _terms(event, r2)
    rows = []
    for i, r in enumerate(runs[0][1].rows):
        pid = r["fide_id"]
        k, a = r["k"], acc[pid]
        row = {"fide_id": pid, "rating": r["rating"], "k": k, "games": r["games"],
               "bp_minus_a": r["bp_minus_a"], "b0_minus_a": r["b0_minus_a"],
               "b_const": k * a["b"], "b_span": k * a["m1"],
               "pilot_bp": runs[0][2].rows[i]["p_minus_b"], "pilot_b": runs[0][1].base.rows[i]["p_minus_b"],
               "eligible": r["eligible"], "c_j": r["c_j"]}
        assert row["games"] == a["n"] and row["bp_minus_a"] == k * a["bp"], pid
        for ev, c, t in runs:                     # the same in every run: no value depends on a result
            rc, rt, rb = c.rows[i], t.rows[i], c.base.rows[i]
            assert (rc["fide_id"], rc["bp_minus_a"], rc["b0_minus_a"], rt["p_minus_b"], rb["p_minus_b"]) == \
                (pid, row["bp_minus_a"], row["b0_minus_a"], row["pilot_bp"], row["pilot_b"]), pid
            score_part = k * sum(((v3.scale(r2, *_ratings(ev, g)) - 1) * ce.SCORE[g["result"]][0 if g["white"] == pid
                                                                                                  else 1])
                                 for g in ev["games"] if g.get("result") in ce.SCORE and pid in (g["white"], g["black"]))
            assert rc["b_minus_a"] == row["b_const"] + score_part, pid
        rows.append(row)
    (_ev0, c0, t0), (_ev1, c1, t1) = runs
    assert (c0.base.opponents_diff, t0.opponents_diff, c0.counted) == (c1.base.opponents_diff, t1.opponents_diff,
                                                                       c1.counted)
    return Fixed(event, rows, c0.counted, v3a.unplayed(event), c0.base.compensated_games, t0.opponents_diff,
                 c0.base.opponents_diff)


def _ratings(event: dict, g: dict) -> tuple[int, int]:
    r = {p["fide_id"]: p["rating"] for p in event["players"]}
    return r[g["white"]], r[g["black"]]


def fixed_summary(f: Fixed) -> dict[str, str]:
    """The event-level figures the pairings fix: (b′)'s and (b0)'s mean |x − (a)| and largest x − (a) over the players
    with a game to play, and the PILOT's totals."""
    played = [r for r in f.rows if r["games"] > 0]
    out = {}
    for key, name in (("bp_minus_a", ""), ("b0_minus_a", "B0_")):
        d = [r[key] for r in played]
        out[f"{name}MEAN_ABS_DIFF"] = f"{sum(abs(x) for x in d) / len(d):.2f}" if d else "—"
        out[f"{name}MAX_DIFF"] = f"{max(d, key=abs):+.2f}" if d else "—"
    out.update({"GAMES": f"{f.games}", "R5_GAMES": f"{f.compensated_games}", "R5_DIFF": f"{f.pilot_bp_total:+.2f}",
                "B_R5_DIFF": f"{f.pilot_b_total:+.2f}"})
    return out


def fixed_markdown(f: Fixed) -> str:
    out = io.StringIO()
    ev = f.event["event"]
    excl = f"; {f.unplayed} marked not played, their terms removed (D-0013)" if f.unplayed else ""
    out.write(f"{ev['name']}: {f.games} games{excl}; ratings and K from the {ev['list_in_force']} list. *{FIXED}.*\n\n")
    out.write("| FIDE ID | rating | K | games | (b′) − (a) | (b0) − (a) | (b) − (a): C, no point scored | (b) − (a): "
              "C + W, every game won | PILOT on (b′): (p′) − (b′) | PILOT on (b), superseded: (p) − (b) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in f.rows:
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['bp_minus_a']:+.2f} | "
                  f"{r['b0_minus_a']:+.2f} | {r['b_const']:+.2f} | {r['b_const'] + r['b_span']:+.2f} | "
                  f"{r['pilot_bp']:+.2f} | {r['pilot_b']:+.2f} |\n")
    return out.getvalue()


# ------------------------------------------------------------------ 2. the PILOT on (b′) (R56)
def pilot_bp(event: dict, r2: v3.Rung2, v1: ce.Params, rung5: dict[int, dict],
             rung5_path: str = v3.DEFAULT_RUNG5) -> v3.Comparison:
    """Freeze 3's rung 5 on top of (b′): Freeze 3's PILOT computation with the slope ratio switched off."""
    return v3.compare(event, dataclasses.replace(r2, scaled=False), v1, rung5, rung5_path)


def pilot_bp_markdown(t: v3.Comparison) -> str:
    out = io.StringIO()
    out.write(f"PILOT (rung 5 on top of (b′) at today's K, R56; rung-5 inputs from {t.rung5_path}, frozen, PROVISIONAL): "
              f"games in which a compensated junior met an opponent who is not eligible: {t.compensated_games}; those "
              f"opponents' total change under (p′) minus under (b′): {t.opponents_diff:+.2f} points.\n\n")
    out.write("| FIDE ID | rating | K | games | score | eligible junior (c_j) | (b′) | rounded | (p′) PILOT: (b′) and "
              "rung 5 | rounded | (p′) − (b′) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in t.rows:
        elig = f"yes ({r['c_j']})" if r["eligible"] else "—"
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {elig} | {r['b']:+.2f} | "
                  f"{r['b_rounded']:+d} | {r['p']:+.2f} | {r['p_rounded']:+d} | {r['p_minus_b']:+.2f} |\n")
    return out.getvalue()


# ------------------------------------------------------------------ 3. the forecast test (R54)
def load_draw_rates(path: str = DEFAULT_DRAW_RATE) -> dict[int, float]:
    p = Path(path)
    d = json.loads((p if p.is_absolute() else ROOT / p).read_text(encoding="utf-8"))
    return {int(k): v["rate"] for k, v in d["bands"].items()}


def three_way(e: float, draw: float) -> tuple[float, float, float]:
    """E6's split (analysis/e6_rungs_extract.py, three_way): E clipped to [0.002, 0.998], the draw share capped so that no
    outcome falls below 0.001; (P_W, P_D, P_L) with P_W + P_D / 2 = E."""
    e = min(max(e, 0.002), 0.998)
    d = min(draw, 2 * e - 0.002, 2 * (1 - e) - 0.002)
    return e - d / 2, d, 1 - e - d / 2


def v2_draw(r2: v3.Rung2, x_eff: int, mid: int) -> float:
    """The v2 model's draw probability at White's effective gap x_eff (colour included, eta whole) and band midpoint."""
    kappa, lam, _eta, alpha, beta, gamma, mu = r2.par
    l = t2.ell(mid)
    z = kappa * math.exp(lam * l) * t2.Q * abs(x_eff)
    nu = math.exp(alpha + beta * l - gamma * math.exp(mu * l) * z)
    return nu / (math.exp(z / 2.0) + math.exp(-z / 2.0) + nu)


def _ll(p: tuple[float, float, float], s: float) -> float:
    return -math.log(p[0] if s == 1.0 else p[1] if s == 0.5 else p[2])


@dataclass(frozen=True)
class GameForecast:
    white: int
    black: int
    s: float                       # White's score
    e_a: float                     # column (a)'s expectation for White
    e_bp: float                    # column (b′)'s expectation for White
    p_a: tuple
    p_bp: tuple

    @property
    def values(self) -> dict[str, float]:
        ll_a, ll_bp = _ll(self.p_a, self.s), _ll(self.p_bp, self.s)
        br_a, br_bp = (self.s - self.e_a) ** 2, (self.s - self.e_bp) ** 2
        return {"ll_a": ll_a, "ll_bp": ll_bp, "ll_d": ll_bp - ll_a, "br_a": br_a, "br_bp": br_bp, "br_d": br_bp - br_a}


def game_forecasts(event: dict, r2: v3.Rung2, rates: dict[int, float]) -> list[GameForecast]:
    """Both columns' forecasts of every counted game (D-0013), from White's side."""
    ev = event["event"]
    chapter, start = ev["chapter"], date.fromisoformat(ev["start"])
    players = {p["fide_id"]: p for p in event["players"]}
    out = []
    for g in event["games"]:
        if g.get("result") not in ce.SCORE:
            continue
        w, b = g["white"], g["black"]
        rw, rb = players[w]["rating"], players[b]["rating"]
        s = float(ce.SCORE[g["result"]][0])
        mid = t2.band_mid((rw + rb) // 2)
        if mid not in rates:
            raise ValueError(f"no draw rate for the level band at {mid}")
        e_a = float(layer0.expected_score(layer0.effective_difference(rw, rb, chapter, start)))
        e_bp = float(v3.expectation(r2, rw, rb, True, rw, rb, rw > rb)[0])
        out.append(GameForecast(w, b, s, e_a, e_bp, three_way(e_a, rates[mid]),
                                three_way(e_bp, v2_draw(r2, rw - rb + r2.eta_whole, mid))))
    return out


def _means(rows: list[dict[str, float]]) -> dict[str, float]:
    n = len(rows)
    return {k: sum(r[k] for r in rows) / n for k in MEASURES}


def _interval(stats: list[float]) -> tuple[float, float]:
    stats = sorted(stats)
    return stats[int(0.025 * RESAMPLES)], stats[int(0.975 * RESAMPLES) - 1]


def forecast_test(events: list[list[GameForecast]]) -> dict | None:
    """Means of the six measures over the games of the given events, with bootstrap intervals over games and over
    players, each resampled within its event; None if no game is counted."""
    per_event = [[g.values for g in ev] for ev in events]
    if not any(per_event):
        return None
    allrows = [v for ev in per_event for v in ev]
    means = _means(allrows)
    rnd = random.Random(SEED)
    boot_g = {k: [] for k in MEASURES}
    for _ in range(RESAMPLES):
        sample = [ev[rnd.randrange(len(ev))] for ev in per_event for _j in range(len(ev))]
        for k, v in _means(sample).items():
            boot_g[k].append(v)
    by_player = []
    for ev, rows in zip(events, per_event):
        groups: dict[int, list[dict[str, float]]] = {}
        for g, v in zip(ev, rows):
            groups.setdefault(g.white, []).append(v)
            groups.setdefault(g.black, []).append(v)
        by_player.append([groups[p] for p in sorted(groups)])
    rnd = random.Random(SEED)
    boot_p = {k: [] for k in MEASURES}
    for _ in range(RESAMPLES):
        sample = [v for groups in by_player for _j in range(len(groups)) for v in groups[rnd.randrange(len(groups))]]
        for k, v in _means(sample).items():
            boot_p[k].append(v)
    return {"games": len(allrows), "players": sum(len(g) for g in by_player),
            **{k: (means[k], _interval(boot_g[k]), _interval(boot_p[k])) for k in MEASURES}}


def fmt(q: tuple, signed: bool) -> str:
    f = "{:+.4f}" if signed else "{:.4f}"
    mean, (glo, ghi), (plo, phi) = q
    return (f"{f.format(mean)} (games {f.format(glo)} to {f.format(ghi)}; players {f.format(plo)} to "
            f"{f.format(phi)})")


def test_blanks(res: dict) -> dict[str, str]:
    return {name: fmt(res[key], signed) for name, key, signed in TEST_BLANKS}


def test_markdown(results: dict[str, dict | None]) -> str:
    out = io.StringIO()
    out.write("| scope | games | players | log-loss (a), nats a game | log-loss (b′) | (b′) − (a) | Brier (a) | "
              "Brier (b′) | (b′) − (a) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|\n")
    for scope, res in results.items():
        if res is None:
            out.write(f"| {scope} | 0 | — | — | — | — | — | — | — |\n")
            continue
        cells = " | ".join(fmt(res[k], k.endswith("_d")) for k in MEASURES)
        out.write(f"| {scope} | {res['games']} | {res['players']} | {cells} |\n")
    return out.getvalue()


# ------------------------------------------------------------------ running it
def load(event_path: str, table: str = v3.DEFAULT_TABLE, guard: str = v3.DEFAULT_GUARD,
         rung5: str = v3.DEFAULT_RUNG5) -> tuple[dict, v3.Rung2, ce.Params, dict, str]:
    event = ce.load_event(event_path)
    chapter = event["event"]["chapter"]
    return (event, v3.load_rung2(table, guard, chapter), ce.load_params(ce.DEFAULT_PARAMS, chapter),
            v3.cp.load_rung5(rung5, event_path), rung5)


def main() -> int:
    ap = argparse.ArgumentParser(description="What the pairings fix (R55), the PILOT on (b′) (R56) and the forecast test "
                                             "(R54) for one or two events.")
    ap.add_argument("events", nargs="+")
    ap.add_argument("--draw-rate", default=DEFAULT_DRAW_RATE)
    args = ap.parse_args()
    rates = load_draw_rates(args.draw_rate)
    tests = {}
    for path in args.events:
        event, r2, v1, rung5, rung5_path = load(path)
        sys.stdout.write(fixed_markdown(fixed_by_pairings(event, r2, v1, rung5, rung5_path)) + "\n")
        if v3a.complete(event):
            sys.stdout.write(pilot_bp_markdown(pilot_bp(event, r2, v1, rung5, rung5_path)) + "\n")
            tests[event["event"]["name"]] = game_forecasts(event, r2, rates)
    if tests and len(tests) == len(args.events):
        results = {name: forecast_test([g]) for name, g in tests.items()}
        if len(tests) > 1:
            results["pooled"] = forecast_test(list(tests.values()))
        sys.stdout.write(test_markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
