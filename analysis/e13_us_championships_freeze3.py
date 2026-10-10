#!/usr/bin/env python3
"""E13: the 2026 U.S. Championships under Freeze 3; prints docs/evidence/E13_us-championship-2026-freeze-3.md.

Freeze 3 (docs/decisions/D-0011_rulings-and-freeze-3.md, part B) supersedes Freeze 2 for the comparison. This script
runs tools/compare_event_v3.py on the committed event files: per player (a) Layer 0, (b) rung 2 v2 as session ELO-6
left it (the v2 table, the narrowed guard, K times the printed slope ratio), (b0) rung 2 as Freeze 2 pre-registered it,
labelled "first pre-registration, superseded", and, labelled PILOT, rung 5 on top of (b). By the operator's decision
of 2026-10-09 the 2026 comparison runs once, after the event ends: an event's tables are printed only when all its
games have results. The page prints the blanks of the proposal's §10 as D-0011 part B redefines them (their values
once both events are complete), and the SHA-256 of every file the comparison depends on with their manifest, which
check (a) compares with the one D-0011 records. Python standard library only.

Usage: python3 analysis/e13_us_championships_freeze3.py > docs/evidence/E13_us-championship-2026-freeze-3.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event_v3 as v3  # noqa: E402
import e3_us_championships as e3  # noqa: E402  (the event files' hash without results, the round-robin check)
from layer2 import guard_v2 as gv2  # noqa: E402

OPEN, WOMEN, Y2025 = e3.OPEN, e3.WOMEN, e3.Y2025
PAGE = e3.PAGE
PENDING = "pending: runs after the event ends, with the model frozen beforehand"
FREEZE_RECORD = "docs/decisions/D-0011_rulings-and-freeze-3.md"
# Freeze 3 (D-0011, part B): every file the championship comparison depends on, sorted. The comparison's code and
# parameter files; the engine; the scripts and aggregates that produce the parameter files (E2, E11, E12 and rung 5's
# extract, with what they import or read); Freeze 2's page script; this script; and check (a), which enforces it.
FREEZE3 = sorted([
    "analysis/aggregates/E11_table_by_level.json", "analysis/aggregates/E12_guard_v2.json",
    "analysis/aggregates/E1_standard.json", "analysis/aggregates/E2_broadcast.json", "analysis/aggregates/L1_history.json",
    "analysis/e10_guard_extract.py", "analysis/e10_guard_report.py", "analysis/e11_table_by_level_extract.py",
    "analysis/e11_table_by_level_report.py", "analysis/e12_guard_v2_extract.py", "analysis/e12_guard_v2_report.py",
    "analysis/e13_us_championships_freeze3.py", "analysis/e2_broadcast_extract.py", "analysis/e2_broadcast_report.py",
    "analysis/e3_us_championships.py", "analysis/e6_rungs_extract.py", "analysis/e6_rungs_report.py",
    "analysis/l1_common.py", "analysis/table_v2_fit.py", "analysis/us26_rung5_extract.py",
    "params/guard_2026-10b.yaml", "params/rung5_us2026.json", "params/table_fit_2026-10.yaml",
    "params/table_fit_2026-10b.yaml",
    "src/layer0/__init__.py", "src/layer0/lists.py", "src/layer0/records.py", "src/layer0/rules.py", "src/layer0/tables.py",
    "src/layer1/__init__.py", "src/layer1/data.py", "src/layer1/fit.py", "src/layer1/forecast.py", "src/layer1/model.py",
    "src/layer1/outputs.py", "src/layer1/solver.py",
    "src/layer2/__init__.py", "src/layer2/guard.py", "src/layer2/guard_v2.py", "src/layer2/table_v2.py",
    "tools/checks/_repo.py", "tools/checks/check_outputs.py", "tools/compare_event.py", "tools/compare_event_v3.py",
    "tools/compare_pilot.py", "tools/events/us_championship_2025.json", "tools/set_results.py",
])
BLANKS = ("GAMES", "MEAN_ABS_DIFF", "MAX_DIFF", "N_DIFFER", "B0_MEAN_ABS_DIFF", "B0_MAX_DIFF", "B0_N_DIFFER", "R5_GAMES",
          "R5_DIFF")


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def freeze3_lines() -> list[tuple[str, str]]:
    """(file, SHA-256) for every file Freeze 3 freezes, and the 2026 event files with their results removed."""
    return [(f, sha(f)) for f in FREEZE3] + [(f + " (without results)", e3.event_sha_without_results(f))
                                             for f in (OPEN, WOMEN)]


def freeze3_manifest(lines: list[tuple[str, str]] | None = None) -> str:
    """SHA-256 of the lines "hash  file", one per frozen file: the value D-0011 records."""
    lines = freeze3_lines() if lines is None else lines
    return hashlib.sha256("".join(f"{h}  {f}\n" for f, h in lines).encode("utf-8")).hexdigest()


def blanks(c: v3.Comparison) -> dict[str, str]:
    """The blanks of the proposal's §10 for one event, as D-0011 part B defines them."""
    d_b = [r["b_minus_a"] for r in c.rows]
    d_0 = [r["b0_minus_a"] for r in c.rows]
    n = len(c.rows)
    return {"GAMES": f"{c.counted}",
            "MEAN_ABS_DIFF": f"{sum(abs(x) for x in d_b) / n:.2f}", "MAX_DIFF": f"{max(d_b, key=abs):+.2f}",
            "N_DIFFER": f"{sum(1 for r in c.rows if r['b_rounded'] != r['a_rounded'])} of {n}",
            "B0_MEAN_ABS_DIFF": f"{sum(abs(x) for x in d_0) / n:.2f}", "B0_MAX_DIFF": f"{max(d_0, key=abs):+.2f}",
            "B0_N_DIFFER": f"{sum(1 for r in c.rows if r['b0_rounded'] != r['a_rounded'])} of {n}",
            "R5_GAMES": f"{c.compensated_games}", "R5_DIFF": f"{c.opponents_diff:+.2f}"}


def main() -> int:
    y = v3.run(Y2025)
    o, w = v3.run(OPEN), v3.run(WOMEN)
    complete = {name: c.counted == c.scheduled for name, c in (("open", o), ("women", w))}
    P = print
    P("# E13 — The 2026 U.S. Championships under Freeze 3: columns (a), (b), (b0) and the PILOT table\n")
    P("Status: DRAFT — not for publication; the events are in progress (session ELO-6, Phase 4; Freeze 3 recorded in "
      f"`{FREEZE_RECORD}`, part B). Generated by `analysis/e13_us_championships_freeze3.py` with "
      "`tools/compare_event_v3.py` from the event files in `tools/events/`, `params/table_fit_2026-10b.yaml`, "
      "`params/guard_2026-10b.yaml`, `params/table_fit_2026-10.yaml` and `params/rung5_us2026.json`; do not edit by hand. "
      "Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). For the comparison it supersedes the tables that "
      "`docs/evidence/E3_us-championship-2026.md` prints under Freeze 2, whose script is kept unchanged.\n")
    P("## What is compared (D-0011, part B)\n")
    P("- **(a)** the event's change under FIDE's rules, computed by the ratified Layer-0 engine (`src/layer0/`, Freeze 1).")
    P("- **(b)** rung 2 v2, RECOMMENDED NOW in standard, as session ELO-6 left it: the table calibrated by level "
      "(`params/table_fit_2026-10b.yaml`, [E11]), the narrowed guard (`params/guard_2026-10b.yaml`, R24, [E12]) and each "
      "game's K multiplied by the table's printed slope ratio m(L) of the game's level band (R32, [E12]).")
    P("- **(b0)** rung 2 exactly as Freeze 2 pre-registered it (`tools/compare_event.py` with "
      "`params/table_fit_2026-10.yaml`, Freeze 1): the **first pre-registration, superseded**, printed beside (b) so that "
      "both pre-registrations are visible.")
    P("- **PILOT**, printed separately: rung 5 on top of (b), with the frozen rung-5 inputs (`params/rung5_us2026.json`, "
      "D-0010).")
    P("- Nothing else: rungs 3, 4, 6 and 7, and any other column, statistic, subset or event, are not computed on the "
      "event.\n")
    P("## The check: the 2025 U.S. Championship\n")
    P(f"Column (a) must equal FIDE's per-event calculation (SPEC-COMPARE §4): `tests/test_compare_event_v3.py` asserts it "
      f"for all {len(y.rows)} players against `tests/fixtures/validation/us_championship_2025.json`, the fixture of E0, and "
      "that (b0) equals Freeze 2's column (b).\n")
    P(v3.to_markdown(y))
    db = [r["b_minus_a"] for r in y.rows]
    d0 = [r["b0_minus_a"] for r in y.rows]
    P(f"In 2025, with the same results, rung 2 v2 would have changed the twelve players' gains by {min(db):+.2f} to "
      f"{max(db):+.2f} points against FIDE's rules, and Freeze 2's rung 2 by {min(d0):+.2f} to {max(d0):+.2f}.\n")
    P("## 2026 U.S. Championship and U.S. Women's Championship\n")
    P(f"**{PENDING}.**\n")
    P("By the operator's decision of 2026-10-09, no game of either 2026 championship is processed while the event runs. "
      "The comparison runs once, after the last round (21 October; the playoff of 22 October is not part of it), on all "
      "games at once.\n")
    for name, c in (("U.S. Championship", o), ("U.S. Women's Championship", w)):
        if c.counted == c.scheduled:
            P(f"### {name}\n")
            P(v3.to_markdown(c))
            P(f"### {name}, PILOT\n")
            P(v3.pilot_markdown(c))
        else:
            P(f"- {name}: {c.counted} of {c.scheduled} results recorded; {PENDING}.")
    P("\n## The blanks of the proposal's §10 (D-0011, part B)\n")
    if not all(complete.values()):
        P(f"**{PENDING}.** Each blank is computed here, from the tables above, once both events are complete: "
          "`{{US26_*_GAMES}}`; for (b), `{{US26_*_MEAN_ABS_DIFF}}`, `{{US26_*_MAX_DIFF}}`, `{{US26_*_N_DIFFER}}`; for "
          "(b0), `{{US26_*_B0_MEAN_ABS_DIFF}}`, `{{US26_*_B0_MAX_DIFF}}`, `{{US26_*_B0_N_DIFFER}}`; for the PILOT, "
          "`{{US26_*_R5_GAMES}}` and `{{US26_*_R5_DIFF}}`. `{{US26_*_L0_MATCH}}` follows the 1 November 2026 list, from "
          "FIDE's published calculations, and `{{US26_READING}}` is written by hand; D-0011 part B defines each.\n")
    else:
        vals = {"OPEN": blanks(o), "WOMEN": blanks(w)}
        P("| blank | U.S. Championship | U.S. Women's Championship |")
        P("|---|---|---|")
        for k in BLANKS:
            P(f"| `{{{{US26_*_{k}}}}}` | {vals['OPEN'][k]} | {vals['WOMEN'][k]} |")
        P("\n`{{US26_*_L0_MATCH}}` waits for FIDE's published calculations after the 1 November 2026 list; "
          "`{{US26_READING}}` is written by hand (D-0011, part B).\n")
    P("## The guard and the two fields\n")
    P("| event | games | largest gap | lowest game level | pairings in the narrowed guard's region | guard binds in (b) |")
    P("|---|---|---|---|---|---|")
    for name, c in (("U.S. Championship", o), ("U.S. Women's Championship", w)):
        r = {pl["fide_id"]: pl["rating"] for pl in c.event["players"]}
        gaps = [abs(r[g["white"]] - r[g["black"]]) for g in c.event["games"]]
        lv = [(r[g["white"]] + r[g["black"]]) / 2 for g in c.event["games"]]
        inside = sum(1 for g in c.event["games"] if gv2.in_region(r[g["white"]], r[g["black"]]))
        P(f"| {name} | {len(c.event['games'])} | {max(gaps)} | {min(lv):g} | {inside} | {c.guard_games} |")
    P("\nThe official pairings of all eleven rounds with the ratings of FIDE's October 2026 list, as the event files "
      "record them; no result is read. No pairing lies in the region of the guard, so in both events (b) differs from "
      "(b0) through the v2 table and the scaled K only.\n")
    P("## Freeze 3 (D-0011, part B)\n")
    P("Recorded in `docs/decisions/D-0011_rulings-and-freeze-3.md`, part B, before any result of either event was read, "
      "and tagged `freeze-3`. Every fit behind these numbers uses games up to 30 September 2026, a cutoff enforced in code "
      "(`analysis/e10_guard_extract.py`, `src/layer1/data.py`, `src/layer1/fit.py`); no game of either event was read. "
      "SHA-256 of every file the comparison depends on (Freeze 1's and Freeze 2's among them, unchanged), and of the two "
      "event files with their results removed:\n")
    P("| File | SHA-256 |")
    P("|---|---|")
    lines = freeze3_lines()
    for f, h in lines:
        tail = " (without results)" if f.endswith("(without results)") else ""
        P(f"| `{f.replace(' (without results)', '')}`{tail} | `{h}` |")
    P(f"\nManifest (SHA-256 of the {len(lines)} lines \"hash  file\" above): `{freeze3_manifest(lines)}`.\n")
    P("Check (a) reruns this page on every pull request and compares this manifest with the one D-0011 records, so a "
      "change to any of these files, or to the pairings, ratings or K of either event file, fails the check until a new "
      "decision record supersedes D-0011. Entering the results after the event changes no value here. Proposal numbers "
      "drawn from history and the simulator may still change until submission, provided no event game is read "
      "(D-0011, part B).\n")
    P("## Running the comparison after the event\n")
    P(f"Enter each round's results from the official page ({PAGE}), board by board, then regenerate this page once "
      "(`tools/README.md`); boards 7–12 go into the women's event file:\n")
    P("```")
    P("python3 tools/set_results.py tools/events/us_championship_2026.json ROUND R1 R2 R3 R4 R5 R6")
    P("python3 analysis/e13_us_championships_freeze3.py > docs/evidence/E13_us-championship-2026-freeze-3.md")
    P("```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
