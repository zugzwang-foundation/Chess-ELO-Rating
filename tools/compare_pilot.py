#!/usr/bin/env python3
"""One event under rung 2 with R17's guard and, labelled PILOT, with rung 5 added (ELO-5, Phase 6; Freeze 2).

Reads an event file (tools/events/*.json), the frozen table parameters (params/table_fit_2026-10.yaml, read
through tools/compare_event.py, Freeze 1) and the frozen rung-5 file (params/rung5_us2026.json, written by
analysis/us26_rung5_extract.py), and prints per player:
  (b) the event's change under rung 2 with R17's guard (src/layer2/guard.py; annex T3.6) and today's K reduced
      under K x n <= 700, which equals tools/compare_event.py's column (b) in every game where the guard does
      not bind;
  (p) PILOT: the same with rung 5 (annex T4.6): an eligible junior's opponent who is not eligible (R8) uses
      RX_j = R_j + c_j in the gap of the expectation, the guard read on that gap; the junior's own expectation
      uses published ratings; the level band is that of the two published ratings, without compensation;
  and (p) - (b). Each column is K times the sum of (score - expectation), unrounded and rounded once, as in
tools/compare_event.py. The summary gives the games in which a compensated junior (c_j > 0) met an opponent
who is not eligible, and the total change of those opponents under (p) minus under (b). Rungs 3, 4, 6 and 7
stay off. Python standard library only.

Usage:
  python3 tools/compare_pilot.py tools/events/us_championship_2026.json
  python3 tools/compare_pilot.py EVENT.json --rung5 params/rung5_us2026.json
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402
import layer0  # noqa: E402
from layer2 import guard  # noqa: E402

DEFAULT_RUNG5 = "params/rung5_us2026.json"


def load_rung5(path: str, event_path: str) -> dict[int, dict]:
    """The frozen eligibility flag and c_j of every player of the event (absent players: not eligible)."""
    p = Path(path)
    data = json.loads((p if p.is_absolute() else ROOT / p).read_text(encoding="utf-8"))
    ev = Path(event_path)
    key = str(ev.relative_to(ROOT)) if ev.is_absolute() else str(ev)
    return {r["fide_id"]: r for r in data["players"] if r["event"] == key}


@dataclass
class Pilot:
    event: dict
    params: ce.Params
    rung5_path: str
    rows: list[dict]
    counted: int
    scheduled: int
    guard_games: int
    compensated_games: int
    opponents_diff: Decimal


def expectation(own: int, opp_for_e: int, own_white: bool, mid: int, p: ce.Params,
                opp_published: int | None = None) -> tuple[Decimal, bool]:
    """Rung 2's published entry for `own` at the gap own - opp_for_e (colour added), guarded on that gap (R17), the
    favourite's 2300 read on its published rating (D-0009, reading 4)."""
    x = own - opp_for_e + (p.eta_whole if own_white else -p.eta_whole)
    return guard.guard_own(ce.rung2_expected(x, mid, p), own, opp_for_e, opp_published)


def compare(event: dict, params: ce.Params, rung5: dict[int, dict], rung5_path: str = DEFAULT_RUNG5) -> Pilot:
    players = {p["fide_id"]: p for p in event["players"]}
    acc = {pid: {"n": 0, "score": Decimal(0), "db": Decimal(0), "dp": Decimal(0), "guard": 0, "comp": 0} for pid in players}
    counted = guard_games = comp_games = 0
    opp_ids: list[tuple[int, Decimal]] = []
    for g in event["games"]:
        if g.get("result") not in ce.SCORE:
            continue
        counted += 1
        w, b = g["white"], g["black"]
        rw, rb = players[w]["rating"], players[b]["rating"]
        sw, sb = ce.SCORE[g["result"]]
        mid = ce.band_mid((rw + rb) // 2)
        elig = {pid: bool(rung5.get(pid, {}).get("eligible")) for pid in (w, b)}
        cj = {pid: int(rung5.get(pid, {}).get("c_j", 0)) if elig[pid] else 0 for pid in (w, b)}
        bound = False
        for pid, oid, own, opp, s, white in ((w, b, rw, rb, sw, True), (b, w, rb, rw, sb, False)):
            e_b, bind_b = expectation(own, opp, white, mid, params)
            comp = elig[oid] and not elig[pid] and cj[oid] > 0          # R8: no compensation between two eligible juniors
            e_p, bind_p = expectation(own, opp + cj[oid], white, mid, params, opp) if comp else (e_b, bind_b)
            a = acc[pid]
            a["n"] += 1
            a["score"] += s
            a["db"] += s - e_b
            a["dp"] += s - e_p
            a["guard"] += bind_b
            a["comp"] += comp
            bound = bound or bind_b
            if comp:
                comp_games += 1
                opp_ids.append((pid, e_b - e_p))
        guard_games += bound
    rows = []
    for pid in sorted(players, key=lambda p: (-players[p]["rating"], p)):
        a = acc[pid]
        k = layer0.k_for_period(players[pid]["k"], a["n"])
        cb, cp = k * a["db"], k * a["dp"]
        r5 = rung5.get(pid, {})
        rows.append({"fide_id": pid, "rating": players[pid]["rating"], "k": k, "games": a["n"], "score": a["score"],
                     "eligible": bool(r5.get("eligible")), "c_j": int(r5.get("c_j", 0)) if r5.get("eligible") else 0,
                     "b": cb, "b_rounded": layer0.round_change(cb), "p": cp, "p_rounded": layer0.round_change(cp),
                     "difference": cp - cb, "guard_games": a["guard"], "compensated_games": a["comp"]})
    by_id = {r["fide_id"]: r for r in rows}
    opp_diff = sum((by_id[pid]["k"] * d for pid, d in opp_ids), Decimal(0))
    return Pilot(event, params, rung5_path, rows, counted, len(event["games"]), guard_games, comp_games, opp_diff)


def label(c: Pilot) -> list[str]:
    ev = c.event["event"]
    return [
        f"{ev['name']} ({ev['start']} to {ev['end']}, {ev['chapter']}): {c.counted} of {c.scheduled} games counted; "
        f"ratings and K from the {ev['list_in_force']} list; rung 5 from {c.rung5_path} (frozen, PROVISIONAL).",
        "Method: (b) is rung 2 with R17's guard (annex T3.6): the fitted table's expectation, the favourite's raised to "
        "table 8.1.2 read without the 400-point cap where the gap is 400 or more and the favourite is rated 2300 or "
        "more, the same K as today reduced under K x n <= 700. (p) is labelled PILOT: (b) with rung 5 (annex T4.6), "
        "an eligible junior's opponent who is not eligible using RX_j = R_j + c_j in the gap (R8), the junior's own "
        "expectation on published ratings. Each column is K times the sum of (score - expectation) over the event's "
        "games, shown unrounded and rounded once.",
        f"Games in which the guard binds: {c.guard_games}. PILOT: games in which a compensated junior met an opponent "
        f"who is not eligible: {c.compensated_games}; those opponents' total change under (p) minus under (b): "
        f"{c.opponents_diff:+.2f} points.",
    ]


def to_markdown(c: Pilot) -> str:
    out = io.StringIO()
    for line in label(c):
        out.write(line + "\n\n")
    out.write("| FIDE ID | rating | K | games | score | eligible junior (c_j) | (b) rung 2 with the guard | rounded | "
              "(p) PILOT: rungs 2 and 5 | rounded | (p) − (b) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in c.rows:
        elig = f"yes ({r['c_j']})" if r["eligible"] else "—"
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {elig} | {r['b']:+.2f} | "
                  f"{r['b_rounded']:+d} | {r['p']:+.2f} | {r['p_rounded']:+d} | {r['difference']:+.2f} |\n")
    return out.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description="One event under rung 2 with the guard and, labelled PILOT, with rung 5.")
    ap.add_argument("event")
    ap.add_argument("--params", default=ce.DEFAULT_PARAMS)
    ap.add_argument("--rung5", default=DEFAULT_RUNG5)
    args = ap.parse_args()
    event = ce.load_event(args.event)
    params = ce.load_params(args.params, event["event"]["chapter"])
    c = compare(event, params, load_rung5(args.rung5, args.event), args.rung5)
    sys.stdout.write(to_markdown(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
