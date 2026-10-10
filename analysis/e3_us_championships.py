#!/usr/bin/env python3
"""E3: the 2026 U.S. Championships under FIDE's rules and under rung 2; prints docs/evidence/E3_us-championship-2026.md.

Runs tools/compare_event.py (docs/specs/SPEC-COMPARE_v1_0.md) on the committed event
files (tools/events/) with params/table_fit_2026-10.yaml, and, labelled PILOT,
tools/compare_pilot.py with params/rung5_us2026.json, and prints the evidence page.
By the operator's decision of 2026-10-09 the 2026 comparison runs once, after the event
ends, with the model frozen beforehand: an event's tables are printed only when all its
games have results. The page prints the SHA-256 of Freeze 1's files and of Freeze 2's
(docs/decisions/D-0010_freeze-2.md: every tracked file that produces a number in the
comparison or the proposal, and the event files without their results), so that check
(a) fails if any of them changes before the run; and, once both events are complete, the
values of the blanks of the proposal's §10. Python standard library only.

Usage: python3 analysis/e3_us_championships.py > docs/evidence/E3_us-championship-2026.md
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event  # noqa: E402
import compare_pilot  # noqa: E402
from layer2 import guard  # noqa: E402

OPEN, WOMEN, Y2025 = ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json",
                      "tools/events/us_championship_2025.json")
PAGE = "https://saintlouischessclub.org/event/2026-us-chess-championships/"
FROZEN = ["params/table_fit_2026-10.yaml", "tools/compare_event.py", "src/layer0/__init__.py", "src/layer0/lists.py",
          "src/layer0/records.py", "src/layer0/rules.py", "src/layer0/tables.py"]
PENDING = "pending: runs after the event ends, with the model frozen beforehand"
RUNG5 = "params/rung5_us2026.json"
FREEZE_RECORD = "docs/decisions/D-0010_freeze-2.md"


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def freeze2_files() -> list[str]:
    """Freeze 2 (D-0010): every tracked file that produces a number in the comparison or the proposal, sorted: the
    parameter files, src/, tools/ (its documentation aside; the two 2026 event files are hashed without their results,
    below), and the analysis scripts with the aggregates and outputs they produce (analysis/*.py, analysis/aggregates/,
    analysis/OUTPUT_*.md)."""
    out = subprocess.run(["git", "ls-files", "-z", "--", "params", "src", "tools", "analysis"], cwd=ROOT,
                         capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    keep = []
    for f in out:
        if not f or "__pycache__" in f or f in (OPEN, WOMEN):
            continue
        if f.startswith("analysis/"):
            top = f.count("/") == 1
            if f.startswith("analysis/aggregates/") or (top and f.endswith(".py")) or (top and f.startswith("analysis/OUTPUT_")):
                keep.append(f)
            continue
        if not f.endswith(".md"):
            keep.append(f)
    return sorted(keep)


def freeze2_lines() -> list[tuple[str, str]]:
    """(file, SHA-256) for every frozen file, and the 2026 event files with their results removed."""
    return [(f, sha(f)) for f in freeze2_files()] + [(f + " (without results)", event_sha_without_results(f))
                                                      for f in (OPEN, WOMEN)]


def freeze2_manifest(lines: list[tuple[str, str]] | None = None) -> str:
    """SHA-256 of the lines "hash  file", one per frozen file: the value D-0010 records."""
    lines = freeze2_lines() if lines is None else lines
    return hashlib.sha256("".join(f"{h}  {f}\n" for f, h in lines).encode("utf-8")).hexdigest()


def event_sha_without_results(path: str) -> str:
    """The event file's SHA-256 with every result, the results log and the results' source removed: the pairings,
    the ratings and the K are frozen; entering the results after the event leaves this value unchanged."""
    ev = json.loads((ROOT / path).read_text(encoding="utf-8"))
    ev.pop("results_read", None)
    ev["event"].pop("results_source", None)
    for g in ev["games"]:
        g["result"] = None
    return hashlib.sha256(json.dumps(ev, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def pilot(path: str) -> compare_pilot.Pilot:
    event = compare_event.load_event(path)
    params = compare_event.load_params(compare_event.DEFAULT_PARAMS, event["event"]["chapter"])
    return compare_pilot.compare(event, params, compare_pilot.load_rung5(RUNG5, path), RUNG5)


def is_round_robin(event: dict) -> bool:
    ids = sorted(p["fide_id"] for p in event["players"])
    games = event["games"]
    pairs = Counter(frozenset((g["white"], g["black"])) for g in games)
    once = set(pairs) == {frozenset(c) for c in combinations(ids, 2)} and set(pairs.values()) == {1}
    rounds = sorted({g["round"] for g in games})
    per_round = all(sorted(p for g in games if g["round"] == r for p in (g["white"], g["black"])) == ids for r in rounds)
    whites = Counter(g["white"] for g in games)
    return once and per_round and set(whites.values()) <= {5, 6}


def status(event: dict) -> tuple[int, list[int]]:
    done = sum(1 for g in event["games"] if g["result"])
    complete = [r for r in sorted({g["round"] for g in event["games"]})
                if all(g["result"] for g in event["games"] if g["round"] == r)]
    return done, complete


def table(path: str) -> tuple[str, compare_event.Comparison]:
    event = compare_event.load_event(path)
    c = compare_event.compare(event, compare_event.load_params(compare_event.DEFAULT_PARAMS, event["event"]["chapter"]))
    return compare_event.to_markdown(c), c


def main() -> int:
    o_md, o = table(OPEN)
    w_md, w = table(WOMEN)
    y_md, y = table(Y2025)
    print("# E3 — The 2026 U.S. Championships under FIDE's rules and under rung 2\n")
    print("Status: DRAFT — not for publication; the event is in progress (session ELO-3, Phase 5.3; Freeze 2 recorded in "
          "session ELO-5, Phase 6, `docs/decisions/D-0010_freeze-2.md`). Generated by `analysis/e3_us_championships.py` "
          "with `tools/compare_event.py` (`docs/specs/SPEC-COMPARE_v1_0.md`) and `tools/compare_pilot.py` from the event "
          "files in `tools/events/`, `params/table_fit_2026-10.yaml` and `params/rung5_us2026.json`; do not edit by hand. "
          "Licence: CC BY 4.0 (`docs/LICENSE-docs.md`).\n")
    print("## The event, confirmed\n")
    print(f"- Source: the Saint Louis Chess Club's official event page ({PAGE}), read on 2026-10-09 at about 19:53 UTC "
          "through a web reader; a direct download was refused with HTTP 403. Published sources disagreed on the "
          "dates (8–23, 9–22 and 10–24 October, per the ELO-3 brief).")
    print("- Dates on the official page: 7 to 23 October 2026 in all; rounds 1–4 on 9–12 October, a rest day on 13 "
          "October, rounds 5–8 on 14–17 October, a rest day on 18 October, rounds 9–11 on 19–21 October, a playoff on "
          "22 October if necessary.")
    for name, c in (("U.S. Championship", o), ("U.S. Women's Championship", w)):
        print(f"- {name}: {len(c.event['players'])} players, 11 rounds; the official pairings form a complete round "
              f"robin (each pair once, every player once a round, 5 or 6 Whites each): {is_round_robin(c.event)}.")
    print("- Players are identified by FIDE ID, with the rating and K of FIDE's October 2026 standard list, the list in "
          "force at the start (SPEC-L0 R-11a). Their names are on the official page; the repository does not store "
          "them. Both events end by 22 October and are rated on the November 2026 list (R-09).\n")
    print("## The check: the 2025 U.S. Championship\n")
    print(f"Column (a) must equal FIDE's per-event calculation (SPEC-COMPARE §4); `tests/test_compare_event.py` asserts "
          f"it for all {len(y.rows)} players against `tests/fixtures/validation/us_championship_2025.json`, the "
          "fixture of E0.\n")
    print(y_md)
    diffs = [r["difference"] for r in y.rows]
    print(f"In 2025, rung 2 would have changed the twelve players' gains from the event by {min(diffs):+.2f} to "
          f"{max(diffs):+.2f} points against FIDE's rules, with the same K and the same results.\n")
    print("## 2026 U.S. Championship and U.S. Women's Championship\n")
    print(f"**{PENDING}.**\n")
    print("By the operator's decision of 2026-10-09, no game of either 2026 championship is processed while the event "
          "runs. The comparison runs once, after the last round (21 October, or the playoff of 22 October), on all "
          "games at once.\n")
    for name, md, c in (("U.S. Championship", o_md, o), ("U.S. Women's Championship", w_md, w)):
        done, complete = status(c.event)
        if done == len(c.event["games"]):
            print(f"### {name}\n")
            print(md)
        else:
            print(f"- {name}: {done} of {len(c.event['games'])} results recorded; {PENDING}.")
    po, pw = pilot(OPEN), pilot(WOMEN)
    complete = all(status(c.event)[0] == len(c.event["games"]) for c in (o, w))
    print("\n## PILOT: rung 5 on top of rung 2 with its guard (labelled; not part of the main table)\n")
    print("Rung 5 is a PILOT rung (R22): it is printed here, separately, and never in the main table. Its inputs were "
          f"frozen before any result was read (`{RUNG5}`, from `analysis/us26_rung5_extract.py`: a Layer 1 fit on "
          "broadcast games of 2023-10 to 2026-09 for the October 2026 list, annex T4.6's gates and R5's information share): "
          "per player the eligibility flag and the compensation c_j only.\n")
    print("| event | players aged 19 or less | eligible | with c_j > 0 | c_j of the eligible |")
    print("|---|---|---|---|---|")
    r5 = json.loads((ROOT / RUNG5).read_text(encoding="utf-8"))
    for name, path in (("U.S. Championship", OPEN), ("U.S. Women's Championship", WOMEN)):
        rows = [r for r in r5["players"] if r["event"] == path]
        el = [r for r in rows if r["eligible"]]
        print(f"| {name} | {sum(r['age_at_most_19'] for r in rows)} | {len(el)} | {sum(r['c_j'] > 0 for r in el)} | "
              f"{', '.join(str(r['c_j']) for r in sorted(el, key=lambda r: -r['c_j'])) or '—'} |")
    print("")
    for name, c, p in (("U.S. Championship", o, po), ("U.S. Women's Championship", w, pw)):
        if status(c.event)[0] == len(c.event["games"]):
            same = all(a["b"] == b["b"] for a, b in zip(c.rows, p.rows))
            print(f"### {name}, PILOT\n")
            print(compare_pilot.to_markdown(p))
            print(f"Column (b) here equals the main table's column (b) for every player: {same}.\n")
        else:
            print(f"- {name}, PILOT: {PENDING}.")
    print("\n## The blanks of the proposal's §10 (D-0010)\n")
    if not complete:
        print(f"**{PENDING}.** Each blank is computed here, from the two tables above, once both events are complete; "
              "`{{US26_*_L0_MATCH}}` after the 1 November 2026 list, from FIDE's published calculations, and "
              "`{{US26_READING}}` by hand (D-0010).\n")
    else:
        print("| blank | U.S. Championship | U.S. Women's Championship |")
        print("|---|---|---|")
        vals = {}
        for key, c, p in (("OPEN", o, po), ("WOMEN", w, pw)):
            diffs = [r["difference"] for r in c.rows]
            vals[key] = {"GAMES": f"{c.counted}",
                         "MEAN_ABS_DIFF": f"{sum(abs(d) for d in diffs) / len(diffs):.2f}",
                         "MAX_DIFF": f"{max(diffs, key=abs):+.2f}",
                         "N_DIFFER": f"{sum(1 for r in c.rows if r['b_rounded'] != r['a_rounded'])} of {len(c.rows)}",
                         "R5_GAMES": f"{p.compensated_games}", "R5_DIFF": f"{p.opponents_diff:+.2f}"}
        for k in ("GAMES", "MEAN_ABS_DIFF", "MAX_DIFF", "N_DIFFER", "R5_GAMES", "R5_DIFF"):
            print(f"| `{{{{US26_*_{k}}}}}` | {vals['OPEN'][k]} | {vals['WOMEN'][k]} |")
        print("\n`{{US26_*_L0_MATCH}}` waits for FIDE's published calculations after the 1 November 2026 list; "
              "`{{US26_READING}}` is written by hand (D-0010).\n")
    print("\n## The farming guard (R17)\n")
    print("Ruling R17 (`docs/decisions/D-0009_architect-rulings-elo-5.md`) guards rung 2 where the gap is 400 or more and the "
          "favourite is rated 2300 or more (`src/layer2/guard.py`; evidence in E10). Checked against both fields with their "
          "official pairings and the ratings of the October 2026 list:\n")
    print("| event | games | largest gap | pairings in the guard's region |")
    print("|---|---|---|---|")
    inside_total = 0
    for name, c in (("U.S. Championship", o), ("U.S. Women's Championship", w)):
        r = {pl["fide_id"]: pl["rating"] for pl in c.event["players"]}
        gaps = [abs(r[g["white"]] - r[g["black"]]) for g in c.event["games"]]
        inside = sum(1 for g in c.event["games"]
                     if guard.in_region(max(r[g["white"]], r[g["black"]]), min(r[g["white"]], r[g["black"]])))
        inside_total += inside
        print(f"| {name} | {len(c.event['games'])} | {max(gaps)} | {inside} |")
    print("\n" + ("No pairing falls in the guard's region, so the guard cannot change any expectation in either event: "
                  "Freeze 1's rung-2 column, computed by `tools/compare_event.py`, stands for the comparison."
                  if inside_total == 0 else "Pairings fall in the guard's region: the comparison uses the guarded tool "
                  "frozen in Freeze 2."))
    print("\nFrozen beforehand: the model and the code that will run, fitted and written before the event. The table's "
          "parameters were fitted on games up to September 2026. SHA-256 of each file:\n")
    print("| File | SHA-256 |")
    print("|---|---|")
    for f in FROZEN:
        print(f"| `{f}` | `{hashlib.sha256((ROOT / f).read_bytes()).hexdigest()}` |")
    print("\nThis page is rerun by check (a) on every pull request. A change to any of these files changes the page and "
          "fails the check until the page is regenerated, so an unfreezing would be visible.\n")
    print("## Freeze 2 (D-0010)\n")
    print("Recorded in `docs/decisions/D-0010_freeze-2.md` before any result of either event was read, as ruling R23 "
          "orders, and tagged `freeze-2`. The decision states what will be computed after the event: the main table above "
          "(rungs 1 and 2 with R17's guard, RECOMMENDED NOW), the PILOT table (rung 5, labelled), and the blanks of the "
          "proposal's §10; nothing else. Every fit behind these numbers uses games up to 30 September 2026, a cutoff "
          "enforced in code (`src/layer1/data.py`, `src/layer1/fit.py`); no game of either event was read. SHA-256 of "
          "every tracked file that produces a number in the comparison or in the proposal (Freeze 1's files among them), "
          "and of the two event files with their results removed:\n")
    print("| File | SHA-256 |")
    print("|---|---|")
    lines = freeze2_lines()
    for f, h in lines:
        print(f"| `{f.replace(' (without results)', '')}`{' (without results)' if f.endswith('(without results)') else ''} | `{h}` |")
    manifest = freeze2_manifest(lines)
    print(f"\nManifest (SHA-256 of the {len(lines)} lines \"hash  file\" above): `{manifest}`.\n")
    print("Check (a) reruns this page on every pull request, so a change to any of these files, or to the pairings, "
          "ratings or K of either event file, changes the page; and it compares this manifest with the one D-0010 "
          "records, so the check keeps failing even if the page is regenerated, until a new decision record supersedes "
          "D-0010. Entering the results after the event changes no value here.\n")
    print("## Reminder\n")
    print("FIDE's official changes for both events will appear on the 1 November 2026 standard list. Layer 0, column "
          "(a), must match them for every player once the players' other events in the October period are added, as "
          "E0 does for 2025 (`docs/evidence/E0_l0-validation.md`). A mismatch is a finding about Layer 0 or about "
          "FIDE's data (SPEC-L0 §8), never a reason to edit column (a).\n")
    print("## Running the comparison after the event\n")
    print("Enter each round's results from the official page, board by board, then regenerate this page once "
          "(`tools/README.md`). For the women's championship, use boards 7–12 and its own event file:\n")
    print("```")
    print("python3 tools/set_results.py tools/events/us_championship_2026.json ROUND R1 R2 R3 R4 R5 R6")
    print("python3 analysis/e3_us_championships.py > docs/evidence/E3_us-championship-2026.md")
    print("```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
