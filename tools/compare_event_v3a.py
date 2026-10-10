#!/usr/bin/env python3
"""Freeze 3a (docs/decisions/D-0012_pre-results-amendments.md; ELO-7, Phase 0): one event under FIDE's rules, under rung 2
at today's K, under rung 2 as Freeze 3 and Freeze 2 pre-registered it, and, labelled PILOT, under rung 5 on top of
Freeze 3's column, with the rule for a game not played.

Prints per player:
  (a)  the event's change under FIDE's rules (Layer 0), through tools/compare_event_v3.py, unchanged;
  (b′) "v2 table and narrowed guard at today's K" (R45), §10's main column: tools/compare_event_v3.py's column (b) with
       the slope ratio switched off, so computed only from Freeze 3's frozen table (params/table_fit_2026-10b.yaml) and
       guard (params/guard_2026-10b.yaml) and Layer 0's K, reduced under K x n <= 700; no new parameter;
  (b)  rung 2 v2 with K x m(L), exactly as Freeze 3 pre-registered it (D-0011; R32, withdrawn by R44), labelled;
  (b0) rung 2 as Freeze 2 pre-registered it, labelled "first pre-registration, superseded";
  and (b′) - (a), (b) - (a), (b0) - (a); separately, labelled PILOT, Freeze 3's rung 5 on top of (b), unchanged.
A game marked not played (tools/set_results.py, R43) is excluded from every column, as FIDE does not rate it (§5.1 of
the rating regulations): it adds no game to n in K x n <= 700 and none to the games counted. An event is complete when
every game of rounds 1-11 has a result or that marker. Python standard library only.

Usage:
  python3 tools/compare_event_v3a.py tools/events/us_championship_2026.json
"""
from __future__ import annotations

import argparse
import dataclasses
import io
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402  (Freeze 1's tool, unchanged)
import compare_event_v3 as v3  # noqa: E402  (Freeze 3's tool, unchanged)
import set_results as sr  # noqa: E402  (the marker for a game not played)

BP = "v2 table and narrowed guard at today's K"
B = "Freeze 3, K × m (R32, withdrawn)"
SUPERSEDED = v3.SUPERSEDED
LAST_ROUND = 11


def complete(event: dict) -> bool:
    """R43: every game of rounds 1-11 has a result or the marker for a game not played."""
    return all(g.get("result") in ce.SCORE or g.get("result") == sr.UNPLAYED
               for g in event["games"] if g["round"] <= LAST_ROUND)


def unplayed(event: dict) -> int:
    return sum(1 for g in event["games"] if g.get("result") == sr.UNPLAYED)


@dataclass
class Comparison:
    event: dict
    base: v3.Comparison            # Freeze 3's columns (a), (b), (b0) and the PILOT, unchanged
    rows: list[dict]
    counted: int
    scheduled: int
    unplayed: int
    complete: bool


def compare(event: dict, r2: v3.Rung2, v1: ce.Params, rung5: dict[int, dict],
            rung5_path: str = v3.DEFAULT_RUNG5) -> Comparison:
    base = v3.compare(event, r2, v1, rung5, rung5_path)
    today = v3.compare(event, dataclasses.replace(r2, scaled=False), v1, rung5, rung5_path)   # (b′): no m
    rows = []
    for r, t in zip(base.rows, today.rows):
        assert (r["fide_id"], r["a"], r["b0"], r["k"], r["games"]) == (t["fide_id"], t["a"], t["b0"], t["k"], t["games"])
        rows.append(dict(r, bp=t["b"], bp_rounded=t["b_rounded"], bp_minus_a=t["b"] - r["a"]))
    return Comparison(event, base, rows, base.counted, base.scheduled, unplayed(event), complete(event))


def run(event_path: str, table: str = v3.DEFAULT_TABLE, guard: str = v3.DEFAULT_GUARD,
        rung5: str = v3.DEFAULT_RUNG5) -> Comparison:
    event = ce.load_event(event_path)
    chapter = event["event"]["chapter"]
    return compare(event, v3.load_rung2(table, guard, chapter), ce.load_params(ce.DEFAULT_PARAMS, chapter),
                   v3.cp.load_rung5(rung5, event_path), rung5)


def _stats(rows: list[dict], key: str, rounded: str) -> tuple[str, str, str]:
    """Mean |x - (a)|, the x - (a) of largest absolute value (signed), and the players whose rounded x differs from their
    rounded (a), over the players with at least one counted game (R43: §10 counts played games only)."""
    played = [r for r in rows if r["games"] > 0]
    if not played:
        return "—", "—", "0 of 0"
    d = [r[key] - r["a"] for r in played]
    n_differ = sum(1 for r in played if r[rounded] != r["a_rounded"])
    return f"{sum(abs(x) for x in d) / len(d):.2f}", f"{max(d, key=abs):+.2f}", f"{n_differ} of {len(played)}"


def blanks(c: Comparison) -> dict[str, str]:
    """The blanks of the proposal's §10 for one event, as D-0012 redefines them: the main three for (b′)."""
    out = {"GAMES": f"{c.counted}"}
    for prefix, key, rounded in (("", "bp", "bp_rounded"), ("B_", "b", "b_rounded"), ("B0_", "b0", "b0_rounded")):
        mean, mx, nd = _stats(c.rows, key, rounded)
        out.update({f"{prefix}MEAN_ABS_DIFF": mean, f"{prefix}MAX_DIFF": mx, f"{prefix}N_DIFFER": nd})
    out.update({"R5_GAMES": f"{c.base.compensated_games}", "R5_DIFF": f"{c.base.opponents_diff:+.2f}"})
    return out


BLANKS = ("GAMES", "MEAN_ABS_DIFF", "MAX_DIFF", "N_DIFFER", "B_MEAN_ABS_DIFF", "B_MAX_DIFF", "B_N_DIFFER",
          "B0_MEAN_ABS_DIFF", "B0_MAX_DIFF", "B0_N_DIFFER", "R5_GAMES", "R5_DIFF")


def label(c: Comparison) -> list[str]:
    ev, r2, v1 = c.event["event"], c.base.rung2, c.base.v1
    par = ", ".join(f"{k} {v:g}" for k, v in zip(v3.t2.NAMES, r2.par))
    tail = "; with the draw tail" if r2.draw_tail else ""
    guard = "applies" if r2.guarded else "does not apply"
    excluded = (f"; {c.unplayed} marked not played, excluded from every column (§5.1 of FIDE's rating regulations)"
                if c.unplayed else "")
    return [
        f"{ev['name']} ({ev['start']} to {ev['end']}, {ev['chapter']}): {c.counted} of {c.scheduled} games counted"
        f"{excluded}; ratings and K from the {ev['list_in_force']} list.",
        f"(b′), {BP}, §10's main column (Freeze 3a, D-0012, R45): {r2.table_path} ({r2.status}; {r2.chapter} fit window "
        f"{r2.window}; {par}; eta used as {r2.eta_whole}{tail}); the narrowed guard {guard} in {r2.chapter} "
        f"({r2.guard_path}); K from the list in force, reduced under K x n <= 700, not scaled. (b): the same table and "
        f"guard with K times the printed ratio m(L) of the game's level band, as Freeze 3 pre-registered it (D-0011; R32, "
        f"withdrawn by R44). (b0): {v1.path} ({v1.status}; fit window {v1.window}), Freeze 1's tool, unchanged "
        f"({SUPERSEDED}).",
        "Method: (a) is FIDE today (Layer 0: table 8.1.2, the 400-point rule as it applies to each player, K from the "
        "list in force reduced under K x n <= 700). (b′) is rung 2 at today's K: the v2 table's entry at the game's level "
        "band with colour and draws, the narrowed guard where it applies, and (a)'s K. (b) is the same with K times m(L), "
        "(b0) rung 2 as Freeze 2 pre-registered it, with today's K. Each column is the sum over the event's counted games "
        "of K (times m for (b)) times (score - expectation), shown unrounded and rounded once. Rung 2's values illustrate "
        "a proposal on PROVISIONAL-FITTED parameters; FIDE's official changes are those of the "
        f"{ev['rating_period']} list.",
        f"Games in which the narrowed guard binds: {c.base.guard_games}.",
    ]


def to_markdown(c: Comparison) -> str:
    out = io.StringIO()
    for line in label(c):
        out.write(line + "\n\n")
    out.write(f"| FIDE ID | rating | K | games | score | (a) FIDE today | rounded | (b′) {BP} | rounded | (b′) − (a) | "
              f"(b) {B} | rounded | (b) − (a) | (b0) {SUPERSEDED} | rounded | (b0) − (a) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in c.rows:
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {r['a']:+.2f} | "
                  f"{r['a_rounded']:+d} | {r['bp']:+.2f} | {r['bp_rounded']:+d} | {r['bp_minus_a']:+.2f} | "
                  f"{r['b']:+.2f} | {r['b_rounded']:+d} | {r['b_minus_a']:+.2f} | {r['b0']:+.2f} | "
                  f"{r['b0_rounded']:+d} | {r['b0_minus_a']:+.2f} |\n")
    return out.getvalue()


def pilot_markdown(c: Comparison) -> str:
    return v3.pilot_markdown(c.base)


def main() -> int:
    ap = argparse.ArgumentParser(description="One event under Layer 0 (a), rung 2 at today's K (b′), Freeze 3's rung 2 "
                                             "(b), Freeze 2's (b0) and, labelled PILOT, rung 5 on top of (b).")
    ap.add_argument("event")
    ap.add_argument("--table", default=v3.DEFAULT_TABLE)
    ap.add_argument("--guard", default=v3.DEFAULT_GUARD)
    ap.add_argument("--rung5", default=v3.DEFAULT_RUNG5)
    args = ap.parse_args()
    c = run(args.event, args.table, args.guard, args.rung5)
    sys.stdout.write(to_markdown(c) + "\n" + pilot_markdown(c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
