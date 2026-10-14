#!/usr/bin/env python3
"""E20's replay of the greats, list by list (session ELO-D1, step 3; needs data/).

E20's replay (analysis/e20_greats_replay_extract.py, imported unchanged) is rerun from the cached pages, April 2008 to
December 2019, under the method E20 reports: E18's 2025 table applied backwards, not fitted on that era, with FIDE's
colour marks, and Layer 0 rounding as ruling R80 reads FIDE's lists. For each replayed great it writes the difference,
rung 2 minus Layer 0, on every list of the window on which the replay carries the player, and, beside it, the table's
effect (the replay without colour). No published rating, page or list is written (R72): differences only.

Before writing, the year-end differences are checked against E20's committed aggregate
(analysis/aggregates/E20_greats_replay.json, "year_end_difference", and "difference" on each player's last list): they
must be equal exactly, or the script stops and says where they differ. Python standard library only.

Usage: python3 analysis/e20_greats_replay_by_list_extract.py > analysis/aggregates/E20_greats_replay_by_list.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e20_greats_replay_extract as e20  # noqa: E402  (E20's replay, unchanged; it sets the paths it needs)

COMMITTED = ROOT / "analysis" / "aggregates" / "E20_greats_replay.json"


def main() -> int:
    c = e20.prepare()
    r = e20.run(c, e20.READINGS["R80"])
    committed = {p["fide_id"]: p for p in json.loads(COMMITTED.read_text(encoding="utf-8"))["players"]}
    players, differs, compared = [], [], 0
    for p in c["ids"]:
        if c["first"][p] is None:
            continue
        L0, R2, R2nc = r["L0"][p], r["R2"]["r2"][p], r["R2"]["r2nc"][p]
        lists = [m for m in c["window"] if m in L0]
        by_list = {m: R2[m] - L0[m] for m in lists}
        table = {m: R2nc[m] - L0[m] for m in lists}
        # the check: every year end and the last list, against E20's committed values
        old = committed[int(p)]
        for year, v in old["year_end_difference"].items():
            compared += 1
            if by_list.get(f"{year}-12") != v:
                differs.append((p, f"{year}-12", v, by_list.get(f"{year}-12")))
        compared += 1
        if by_list[lists[-1]] != old["difference"]:
            differs.append((p, lists[-1], old["difference"], by_list[lists[-1]]))
        on_file = max(m for m in c["window"] if p in c["lists"][m])     # after it the difference is carried (E20 §5)
        players.append({"fide_id": int(p), "name": c["selected"].get(p, ""), "first_list": lists[0],
                        "last_list": lists[-1], "last_list_on_fide": on_file, "lists": len(lists),
                        "difference_by_list": by_list, "table_effect_by_list": table})
    if differs:
        sys.stderr.write(f"STOP: {len(differs)} of {compared} year-end values differ from E20's committed ones:\n")
        for d in differs[:20]:
            sys.stderr.write(f"  player {d[0]}, list {d[1]}: E20 {d[2]}, rerun {d[3]}\n")
        return 1
    window = c["window"]
    mean = {m: round(sum(pl["difference_by_list"][m] for pl in players if m in pl["difference_by_list"]) /
                     sum(1 for pl in players if m in pl["difference_by_list"]), 2) for m in window}
    out = {"spec": "docs/specs/SPEC-GREATS_v1_0.md", "source": "analysis/e20_greats_replay_extract.py, imported unchanged",
           "method": "R80's rounding; E18's 2025 table applied backwards, not fitted on that era; FIDE's colour marks",
           "label": "Under this rule, with the same results — not anyone's true strength.",
           "window": {"first": window[0], "last": window[-1], "lists": len(window)},
           "check": {"year_end_and_last_list_values_compared": compared, "equal": compared - len(differs),
                     "against": "analysis/aggregates/E20_greats_replay.json"},
           "players_replayed": len(players), "mean_difference_by_list": mean, "players": players}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
