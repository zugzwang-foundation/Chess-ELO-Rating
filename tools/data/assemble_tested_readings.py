#!/usr/bin/env python3
"""Assemble tests/fixtures/fide_history/tested_readings.json: the readings of the rating regulations that the replay of
today's top 100 (E17) tested on FIDE's output, recorded as fixtures (ruling R63, docs/decisions/
D-0014_forecast-test-and-rulings.md, part B; docs/specs/SPEC-L0_fide-reference-engine_v1_2.md §11).

Needs data/ (the calculations cached by tools/data/fetch_top100_calculations.py and FIDE's lists). Over every period of
the replay, in the order of (list, FIDE ID), with E17's own functions (analysis/e17_top100_extract.py):
  F-H06  the 400-point rule of 1 March 2024 to 30 September 2025, read as the plain cap (NOT VERIFIED as text): every
         tournament of that version in which a favourite among the 100 had two or more differences beyond 400 points,
         every such opponent identified; per tournament the differences beyond 400 (the favourite's Ro minus the
         opponent's actual rating, greatest first) and FIDE's cap mark on each;
  F-H07  the rounding text of 2017, "0.5 is rounded up (whether the change is positive or negative)", read as away from
         zero: every period on a list to December 2021 whose sum, the tournaments' K x Sigma Delta R as FIDE prints them,
         ends in a negative half point; per period the list, the sum and the published change of the list;
  F-H08  SPEC-L0 R-22b where K changes inside a period: every tournament whose K as FIDE prints it differs from the K of
         the list before the one rating it, reduced under K x n <= 700; per tournament the list rating it, n, the
         previous list's published K, the published K of the list in force at the tournament's start and FIDE's K.
No name, FIDE ID or event is recorded (SPEC-TOP100 §8); the values are single figures quoted from FIDE's calculations
and lists for verification, as in tests/fixtures/fide_calculator/. Python standard library only.

Usage: python3 tools/data/assemble_tested_readings.py > tests/fixtures/fide_history/tested_readings.json
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e17_top100_extract as ex  # noqa: E402
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402


def main() -> int:
    lists = ex.load_lists()
    _names, index = ex.load_names()
    caps, halves, ks = [], [], []
    for pair in sorted(ex.ft.plan(), key=lambda s: (s.split(":")[1], int(s.split(":")[0]))):
        pid, t = pair.split(":")
        f = ex.PAGES / f"{pid}_{t}.html"
        prev = layer0.month_add(t, -1)
        if not f.exists() or pid not in lists[t] or pid not in lists[prev]:
            continue
        page = ex.parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
        games_t = lists[t][pid][1]
        k_list = layer0.k_for_period(lists[prev][pid][2], games_t)
        total = Decimal(0)
        for tr in page["tournaments"]:
            total += tr["k_chg"]
            start = date.fromisoformat(tr["start"]) if tr["start"] else date.fromisoformat(f"{prev}-01")
            m = ex.list_for_ro(lists, pid, tr["ro"], tr["start"], t)
            if tr["k"] != k_list and pid in lists[m]:
                ks.append({"list": t, "n": games_t, "k_previous_list": lists[prev][pid][2],
                           "k_start_list": lists[m][pid][2], "start_list_is_earlier": m != prev, "k_fide": tr["k"]})
            if lh.version(start) != "2024":
                continue
            ups, beyond = [], 0
            for g in tr["games"]:            # as E17 reads FIDE's cap mark (analysis/e17_top100_extract.py, replay)
                oid = ex.resolve(g, tr["ro"], lists[m], index)
                actual = l0_rating = g["rating"]
                if g["capped"] and abs(tr["ro"] - g["rating"]) == 400:
                    if oid is not None:
                        actual = l0_rating = lists[m][oid][0]
                    else:                    # the actual rating hidden: beyond the cap, and left out of the case
                        l0_rating = g["rating"] + (-1000 if g["rating"] < tr["ro"] else 1000)
                beyond += tr["ro"] - l0_rating > 400
                if tr["ro"] - actual > 400 and (oid is not None or not g["capped"]):
                    ups.append((tr["ro"] - actual, bool(g["capped"])))
            if len(ups) >= 2 and len(ups) == beyond:
                ups.sort(key=lambda u: -u[0])
                caps.append({"differences": [d for d, _c in ups], "fide_capped": [c for _d, c in ups]})
        if t < lh.ROUNDING_2022_LIST and total < 0 and abs(total) % 1 == Decimal("0.5"):
            halves.append({"list": t, "sum": str(total), "published_change": lists[t][pid][0] - lists[prev][pid][0]})
    out = {"source": "FIDE's published per-player rating calculations (ratings.fide.com/calculations.phtml), cached by "
                     "tools/data/fetch_top100_calculations.py, and FIDE's monthly standard lists, for the October 2026 "
                     "top 100 over the lists 2020-02 to 2026-10 (E17)",
           "written_by": "tools/data/assemble_tested_readings.py (ruling R63, D-0014)",
           "list_values_note": "the values are single figures quoted from FIDE's calculations and lists for verification; "
                               "no name, FIDE ID or event is recorded and the lists are not redistributed",
           "cases": [
               {"id": "F-H06", "reading": "the 400-point rule of 1 March 2024 to 30 September 2025 read as the plain "
                                          "cap: every difference beyond 400 is capped", "tournaments": caps},
               {"id": "F-H07", "reading": "the 2017 text '0.5 is rounded up (whether the change is positive or negative)' "
                                          "read as away from zero", "periods": halves},
               {"id": "F-H08", "reading": "SPEC-L0 R-22b where K changes inside a period: FIDE's K against the previous "
                                          "list's and the start list's", "tournaments": ks}]}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
