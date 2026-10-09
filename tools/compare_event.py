#!/usr/bin/env python3
"""One event under FIDE's rules (Layer 0) and under rung 2 (docs/specs/SPEC-COMPARE_v1_0.md).

Reads an event file (tools/events/*.json) and a parameter file (params/*.yaml) and
prints, per player, the rating change from the event under (a) FIDE today, computed
by the ratified Layer-0 engine (src/layer0), and (b) rung 2, the fitted table with
colour and draws and the same K. Rungs 4 and 5 stay off until Layer 1 exists.
Python standard library only.

Usage:
  python3 tools/compare_event.py tools/events/us_championship_2026.json
  python3 tools/compare_event.py EVENT.json --params params/table_fit_2026-10.yaml --csv out.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import layer0  # noqa: E402

Q = math.log(10.0) / 400.0
DEFAULT_PARAMS = "params/table_fit_2026-10.yaml"
SCORE = {"1-0": (Decimal(1), Decimal(0)), "1/2-1/2": (Decimal("0.5"), Decimal("0.5")), "0-1": (Decimal(0), Decimal(1))}


@dataclass(frozen=True)
class Params:
    path: str
    status: str
    chapter: str
    window: str
    kappa: float
    eta: float
    alpha: float
    beta: float
    gamma: float

    @property
    def eta_whole(self) -> int:
        """η rounded to a whole number: the published table has one row per whole-number gap (annex T3.4)."""
        return int(Decimal(repr(self.eta)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def load_params(path: str, chapter: str) -> Params:
    """Read one time control's parameters from a params/table_fit_*.yaml file (the format the report script writes)."""
    text = (ROOT / path).read_text(encoding="utf-8") if not Path(path).is_absolute() else Path(path).read_text()
    status = re.search(r"^status: (.+)$", text, re.M).group(1).strip()
    block = re.search(rf"^{chapter}:\n((?:  .*\n?)+)", text, re.M)
    if not block:
        raise SystemExit(f"{path} has no parameters for {chapter}")
    b = block.group(1)
    val = {k: float(re.search(rf"^  {k}: {{value: (-?[\d.]+)", b, re.M).group(1)) for k in
           ("kappa", "eta", "alpha", "beta", "gamma")}
    w = re.search(r'fit_window: \{from: "([\d-]+)", to: "([\d-]+)"\}', b)
    return Params(path, status, chapter, f"{w.group(1)} to {w.group(2)}", **val)


def band_mid(level: int) -> int:
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


def rung2_expected(x: int, mid: int, p: Params) -> Decimal:
    """Annex T3.1 at gap x and level band midpoint, three decimals half up, E(-x) = 1 - E(x) (T3.4)."""
    z = p.kappa * Q * abs(x)
    nu = math.exp(p.alpha + p.beta * (mid - 2000.0) / 400.0 - p.gamma * z)
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    e = Decimal(repr((a + nu / 2.0) / (a + b + nu))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return e if x >= 0 else Decimal(1) - e


def load_event(path: str) -> dict:
    p = Path(path)
    return json.loads((p if p.is_absolute() else ROOT / p).read_text(encoding="utf-8"))


@dataclass
class Comparison:
    event: dict
    params: Params
    rows: list[dict]
    counted: int
    scheduled: int


def compare(event: dict, params: Params) -> Comparison:
    ev = event["event"]
    chapter = ev["chapter"]
    start = date.fromisoformat(ev["start"])
    players = {p["fide_id"]: p for p in event["players"]}
    acc = {pid: {"n": 0, "score": Decimal(0), "d0": Decimal(0), "d2": Decimal(0)} for pid in players}
    counted = 0
    for g in event["games"]:
        if g.get("result") not in SCORE:
            continue
        counted += 1
        w, b = g["white"], g["black"]
        rw, rb = players[w]["rating"], players[b]["rating"]
        sw, sb = SCORE[g["result"]]
        mid = band_mid((rw + rb) // 2)
        e_w = rung2_expected(rw - rb + params.eta_whole, mid, params)
        for pid, own, opp, s, e2 in ((w, rw, rb, sw, e_w), (b, rb, rw, sb, Decimal(1) - e_w)):
            a = acc[pid]
            a["n"] += 1
            a["score"] += s
            a["d0"] += layer0.game_delta(own, opp, s, chapter, start)
            a["d2"] += s - e2
    rows = []
    for pid in sorted(players, key=lambda p: (-players[p]["rating"], p)):
        a = acc[pid]
        k = layer0.k_for_period(players[pid]["k"], a["n"])
        c0, c2 = k * a["d0"], k * a["d2"]
        rows.append({"fide_id": pid, "rating": players[pid]["rating"], "k": k, "games": a["n"], "score": a["score"],
                     "a": c0, "a_rounded": layer0.round_change(c0), "b": c2, "b_rounded": layer0.round_change(c2),
                     "difference": c2 - c0})
    return Comparison(event, params, rows, counted, len(event["games"]))


def label(c: Comparison) -> list[str]:
    ev, p = c.event["event"], c.params
    return [
        f"{ev['name']} ({ev['start']} to {ev['end']}, {ev['chapter']}): {c.counted} of {c.scheduled} games counted; "
        f"ratings and K from the {ev['list_in_force']} list.",
        f"Parameter file: {p.path} ({p.status}; {p.chapter} fit window {p.window}; kappa {p.kappa:.4f}, eta "
        f"{p.eta:.2f}, used as {p.eta_whole}, alpha {p.alpha:.4f}, beta {p.beta:.4f}, gamma {p.gamma:.4f}).",
        "Method: (a) is FIDE today, computed by the ratified Layer-0 engine (SPEC-L0 v1.0): table 8.1.2, the "
        "400-point rule as it applies to each player, K from the list in force reduced under K x n <= 700 for the "
        "event's games. (b) is rung 2 of the adoption ladder: the expected score from the fitted table with colour "
        "and draws (annex T3; eta rounded to a whole number, E to three decimals at the midpoint of the game's "
        "100-point level band), the same K, nothing else changed; rungs 4 and 5 are off because Layer 1 does not "
        "exist yet. Each column is K times the sum of (score - expectation) over the event's games, shown unrounded "
        "and rounded once. Rung 2's values illustrate a proposal on PROVISIONAL-FITTED parameters; FIDE's official "
        f"changes are those of the {ev['rating_period']} list.",
    ]


def to_markdown(c: Comparison) -> str:
    out = io.StringIO()
    for line in label(c):
        out.write(line + "\n\n")
    out.write("| FIDE ID | rating | K | games | score | (a) FIDE today | rounded | (b) rung 2 | rounded | (b) − (a) |\n")
    out.write("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in c.rows:
        out.write(f"| {r['fide_id']} | {r['rating']} | {r['k']} | {r['games']} | {r['score']} | {r['a']:+.2f} | "
                  f"{r['a_rounded']:+d} | {r['b']:+.2f} | {r['b_rounded']:+d} | {r['difference']:+.2f} |\n")
    return out.getvalue()


def to_csv(c: Comparison) -> str:
    out = io.StringIO()
    for line in label(c):
        out.write("# " + line + "\n")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["fide_id", "rating", "k", "games", "score", "a_fide_today", "a_rounded", "b_rung2", "b_rounded",
                "b_minus_a"])
    for r in c.rows:
        w.writerow([r["fide_id"], r["rating"], r["k"], r["games"], r["score"], f"{r['a']:.2f}", r["a_rounded"],
                    f"{r['b']:.2f}", r["b_rounded"], f"{r['difference']:.2f}"])
    return out.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description="One event under FIDE's rules (Layer 0) and under rung 2.")
    ap.add_argument("event")
    ap.add_argument("--params", default=DEFAULT_PARAMS)
    ap.add_argument("--csv", help="also write the CSV to this path")
    ap.add_argument("--rung4", choices=["off", "on"], default="off", help="K from certainty (needs Layer 1)")
    ap.add_argument("--rung5", choices=["off", "on"], default="off", help="junior compensation (needs Layer 1)")
    args = ap.parse_args()
    for rung, value in (("4 (K from certainty)", args.rung4), ("5 (junior compensation)", args.rung5)):
        if value == "on":
            print(f"rung {rung} needs Layer 1, which does not exist yet; it stays off (SPEC-COMPARE §2).", file=sys.stderr)
            return 2
    event = load_event(args.event)
    c = compare(event, load_params(args.params, event["event"]["chapter"]))
    sys.stdout.write(to_markdown(c))
    if args.csv:
        Path(args.csv).write_text(to_csv(c), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
