#!/usr/bin/env python3
"""One event under FIDE's rules, under rung 2 v2 as Phase 2 left it, under rung 2 as Freeze 2 pre-registered it, and,
labelled PILOT, under rung 5 on top of rung 2 v2 (docs/decisions/D-0011_rulings-and-freeze-3.md; ELO-6, Phase 3).

Reads an event file (tools/events/*.json), the v2 table (params/table_fit_2026-10b.yaml), the guard's outcome
(params/guard_2026-10b.yaml) and the frozen rung-5 inputs (params/rung5_us2026.json), and prints per player:
  (a) the event's change under FIDE's rules, computed by the ratified Layer-0 engine through Freeze 1's tool
      (tools/compare_event.py, unchanged), with K reduced under K x n <= 700;
  (b) rung 2 v2 as Phase 2 left it (E11, E12): the v2 table's published entry (eta whole, three decimals, at the
      game's level band), the narrowed guard where the guard file applies it (analysis/staging/guard_v2.py; R24), and
      each game's K multiplied by the table's printed ratio m(L) of the game's level band where R32 scales it;
  (b0) rung 2 exactly as Freeze 2 pre-registered it, labelled "first pre-registration, superseded": Freeze 1's tool's
      column (b) with Freeze 1's table, unchanged;
  and (b) - (a), (b0) - (a). Separately, labelled PILOT, (p): (b) with rung 5 (annex T4.6), an eligible junior's
opponent who is not eligible (R8) using RX_j = R_j + c_j in the gap of the expectation, the guard's region tested on
the published ratings and its value read at the gap that player's expectation uses (D-0011, reading 6), the junior's
own expectation on published ratings, the level band that of the two published ratings; and (p) - (b). Every column
is K times the sum of (score - expectation) over the event's games (with m inside the sum for (b) and (p)),
unrounded and rounded once. Rungs 3, 4, 6 and 7 stay off. Staged under analysis/staging/ until Freeze 3 (D-0011,
reading 1), then tools/compare_event_v3.py. Python standard library only.

Usage:
  python3 analysis/staging/compare_event_v3.py tools/events/us_championship_2026.json
  python3 analysis/staging/compare_event_v3.py EVENT.json --table T.yaml --guard G.yaml --rung5 R.json
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(ROOT / "analysis" / "staging"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402  (Freeze 1's tool: columns (a) and (b0), unchanged)
import compare_pilot as cp  # noqa: E402  (Freeze 2's PILOT tool: the rung-5 file's reader, unchanged)
import guard_v2 as gv2  # noqa: E402
import layer0  # noqa: E402
import table_v2 as t2  # noqa: E402

DEFAULT_TABLE = "analysis/staging/params/table_fit_2026-10b.yaml"
DEFAULT_GUARD = "analysis/staging/params/guard_2026-10b.yaml"
DEFAULT_RUNG5 = cp.DEFAULT_RUNG5
SUPERSEDED = "first pre-registration, superseded"


def _text(path: str) -> str:
    p = Path(path)
    return (p if p.is_absolute() else ROOT / p).read_text(encoding="utf-8")


@dataclass(frozen=True)
class Rung2:
    """Rung 2 v2 in one time control, as Phase 2 left it."""
    table_path: str
    guard_path: str
    chapter: str
    status: str
    window: str
    par: tuple
    draw_tail: bool
    k_scale: dict
    scaled: bool
    guarded: bool

    @property
    def eta_whole(self) -> int:
        return t2.eta_whole(self.par[2])


def load_rung2(table_path: str, guard_path: str, chapter: str) -> Rung2:
    v = t2.load(_text(table_path), chapter)
    g = _text(guard_path)
    block = re.search(rf"^{chapter}:\n((?:  .*\n?)+)", g, re.M)
    if not block:
        raise SystemExit(f"{guard_path} has no outcome for {chapter}")
    guarded = re.search(r"^  applies: (\w+)$", block.group(1), re.M).group(1) == "true"
    return Rung2(table_path, guard_path, chapter, v["status"], v["window"], v["par"], v["draw_tail"], v["k_scale"],
                 v["k_scale_applies"], guarded)


def expectation(r2: Rung2, own: int, opp_for_e: int, own_white: bool, rw: int, rb: int,
                own_is_favourite: bool) -> tuple[Decimal, bool]:
    """The published v2 entry for `own` at the gap own - opp_for_e (colour added) and the game's published level band,
    with the narrowed guard where it applies: region and weight from the published ratings rw, rb; value read at the
    gap this expectation uses; the favourite is the player with the higher published rating."""
    x = own - opp_for_e + (r2.eta_whole if own_white else -r2.eta_whole)
    mid = t2.band_mid((rw + rb) // 2)
    e = t2.published(x, mid, r2.par)
    if not r2.guarded:
        return e, False
    return gv2.guard_own(e, x, own_is_favourite, gv2.weight(rw, rb))


def scale(r2: Rung2, rw: int, rb: int) -> Decimal:
    """R32: the printed ratio m(L) of the game's level band where the table scales K, otherwise 1."""
    return r2.k_scale[t2.band_mid((rw + rb) // 2)] if r2.scaled else Decimal(1)


@dataclass
class Comparison:
    event: dict
    rung2: Rung2
    v1: ce.Params
    rung5_path: str
    rows: list[dict]
    counted: int
    scheduled: int
    guard_games: int
    compensated_games: int
    opponents_diff: Decimal
    pilot_b_equals_b0_tool: bool


def compare(event: dict, r2: Rung2, v1: ce.Params, rung5: dict[int, dict], rung5_path: str = DEFAULT_RUNG5) -> Comparison:
    frozen = ce.compare(event, v1)                                 # (a) and (b0): Freeze 1's tool, unchanged
    pilot0 = cp.compare(event, v1, {}, rung5_path)                 # Freeze 2's column (b) with R17's guard
    players = {p["fide_id"]: p for p in event["players"]}
    acc = {pid: {"n": 0, "score": Decimal(0), "db": Decimal(0), "dp": Decimal(0), "guard": 0, "comp": 0} for pid in players}
    counted = guard_games = comp_games = 0
    opp_terms: list[tuple[int, Decimal]] = []
    for g in event["games"]:
        if g.get("result") not in ce.SCORE:
            continue
        counted += 1
        w, b = g["white"], g["black"]
        rw, rb = players[w]["rating"], players[b]["rating"]
        sw, sb = ce.SCORE[g["result"]]
        m = scale(r2, rw, rb)
        elig = {pid: bool(rung5.get(pid, {}).get("eligible")) for pid in (w, b)}
        cj = {pid: int(rung5.get(pid, {}).get("c_j", 0)) if elig[pid] else 0 for pid in (w, b)}
        bound = False
        for pid, oid, own, opp, s, white in ((w, b, rw, rb, sw, True), (b, w, rb, rw, sb, False)):
            fav = own > opp
            e_b, bind_b = expectation(r2, own, opp, white, rw, rb, fav)
            comp = elig[oid] and not elig[pid] and cj[oid] > 0          # R8: no compensation between two eligible juniors
            e_p, _ = expectation(r2, own, opp + cj[oid], white, rw, rb, fav) if comp else (e_b, bind_b)
            a = acc[pid]
            a["n"] += 1
            a["score"] += s
            a["db"] += m * (s - e_b)
            a["dp"] += m * (s - e_p)
            a["guard"] += bind_b
            a["comp"] += comp
            bound = bound or bind_b
            if comp:
                comp_games += 1
                opp_terms.append((pid, m * (e_b - e_p)))
        guard_games += bound
    by0 = {r["fide_id"]: r for r in frozen.rows}
    rows = []
    for pid in sorted(players, key=lambda p: (-players[p]["rating"], p)):
        a = acc[pid]
        k = layer0.k_for_period(players[pid]["k"], a["n"])
        cb, cpil = k * a["db"], k * a["dp"]
        r0 = by0[pid]
        r5 = rung5.get(pid, {})
        rows.append({"fide_id": pid, "rating": players[pid]["rating"], "k": k, "games": a["n"], "score": a["score"],
                     "a": r0["a"], "a_rounded": r0["a_rounded"],
                     "b": cb, "b_rounded": layer0.round_change(cb), "b_minus_a": cb - r0["a"],
                     "b0": r0["b"], "b0_rounded": r0["b_rounded"], "b0_minus_a": r0["b"] - r0["a"],
                     "eligible": bool(r5.get("eligible")), "c_j": int(r5.get("c_j", 0)) if r5.get("eligible") else 0,
                     "p": cpil, "p_rounded": layer0.round_change(cpil), "p_minus_b": cpil - cb,
                     "guard_games": a["guard"], "compensated_games": a["comp"]})
    by_id = {r["fide_id"]: r for r in rows}
    opp_diff = sum((by_id[pid]["k"] * d for pid, d in opp_terms), Decimal(0))
    same = all(x["b"] == y["b"] for x, y in zip(frozen.rows, pilot0.rows))
    assert frozen.counted == counted
    return Comparison(event, r2, v1, rung5_path, rows, counted, len(event["games"]), guard_games, comp_games, opp_diff,
                      same)


def label(c: Comparison) -> list[str]:
    ev, r2, v1 = c.event["event"], c.rung2, c.v1
    par = ", ".join(f"{k} {v:g}" for k, v in zip(t2.NAMES, r2.par))
    tail = "; with the draw tail" if r2.draw_tail else ""
    guard = "applies" if r2.guarded else "does not apply"
    k_txt = "scaled by the printed ratio m(L) of the game's level band" if r2.scaled else "not scaled"
    return [
        f"{ev['name']} ({ev['start']} to {ev['end']}, {ev['chapter']}): {c.counted} of {c.scheduled} games counted; "
        f"ratings and K from the {ev['list_in_force']} list.",
        f"(b): {r2.table_path} ({r2.status}; {r2.chapter} fit window {r2.window}; {par}; eta used as {r2.eta_whole}"
        f"{tail}); the narrowed guard {guard} in {r2.chapter} ({r2.guard_path}); K {k_txt} (R32). (b0): {v1.path} "
        f"({v1.status}; fit window {v1.window}), Freeze 1's tool, unchanged ({SUPERSEDED}).",
        "Method: (a) is FIDE today (Layer 0: table 8.1.2, the 400-point rule as it applies to each player, K from the "
        "list in force reduced under K x n <= 700). (b) is rung 2 v2 as Phase 2 left it (D-0011; E11, E12): the v2 "
        "table's entry at the game's level band with colour and draws, the narrowed guard where it applies, and the same "
        "K times m(L) where R32 scales it. (b0) is rung 2 as Freeze 2 pre-registered it, with today's K. Each column is "
        "the sum over the event's games of K (times m for (b)) times (score - expectation), shown unrounded and rounded "
        "once. Rung 2's values illustrate a proposal on PROVISIONAL-FITTED parameters; FIDE's official changes are "
        f"those of the {ev['rating_period']} list.",
        f"Games in which the narrowed guard binds: {c.guard_games}. Freeze 2's PILOT tool's column (b) equals (b0) for "
        f"every player: {c.pilot_b_equals_b0_tool}.",
    ]


def to_markdown(c: Comparison) -> str:
    out = io.StringIO()
    for line in label(c):
        out.write(line + "\n\n")
    out.write(f"| FIDE ID | rating | K | games | score | (a) FIDE today | rounded | (b) rung 2 v2 | rounded | (b) − (a) | "
              f"(b0) {SUPERSEDED} | rounded | (b0) − (a) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in c.rows:
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {r['a']:+.2f} | "
                  f"{r['a_rounded']:+d} | {r['b']:+.2f} | {r['b_rounded']:+d} | {r['b_minus_a']:+.2f} | {r['b0']:+.2f} | "
                  f"{r['b0_rounded']:+d} | {r['b0_minus_a']:+.2f} |\n")
    return out.getvalue()


def pilot_markdown(c: Comparison) -> str:
    out = io.StringIO()
    out.write(f"PILOT (rung 5 on top of (b); rung-5 inputs from {c.rung5_path}, frozen, PROVISIONAL): games in which a "
              f"compensated junior met an opponent who is not eligible: {c.compensated_games}; those opponents' total "
              f"change under (p) minus under (b): {c.opponents_diff:+.2f} points.\n\n")
    out.write("| FIDE ID | rating | K | games | score | eligible junior (c_j) | (b) rung 2 v2 | rounded | "
              "(p) PILOT: rung 2 v2 and rung 5 | rounded | (p) − (b) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in c.rows:
        elig = f"yes ({r['c_j']})" if r["eligible"] else "—"
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {elig} | {r['b']:+.2f} | "
                  f"{r['b_rounded']:+d} | {r['p']:+.2f} | {r['p_rounded']:+d} | {r['p_minus_b']:+.2f} |\n")
    return out.getvalue()


def run(event_path: str, table: str = DEFAULT_TABLE, guard: str = DEFAULT_GUARD, rung5: str = DEFAULT_RUNG5) -> Comparison:
    event = ce.load_event(event_path)
    chapter = event["event"]["chapter"]
    return compare(event, load_rung2(table, guard, chapter), ce.load_params(ce.DEFAULT_PARAMS, chapter),
                   cp.load_rung5(rung5, event_path), rung5)


def main() -> int:
    ap = argparse.ArgumentParser(description="One event under Layer 0, rung 2 v2 (b), Freeze 2's rung 2 (b0) and, "
                                             "labelled PILOT, rung 5 on top of (b).")
    ap.add_argument("event")
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--guard", default=DEFAULT_GUARD)
    ap.add_argument("--rung5", default=DEFAULT_RUNG5)
    args = ap.parse_args()
    c = run(args.event, args.table, args.guard, args.rung5)
    sys.stdout.write(to_markdown(c) + "\n" + pilot_markdown(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
