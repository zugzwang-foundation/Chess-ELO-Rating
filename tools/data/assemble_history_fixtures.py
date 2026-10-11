#!/usr/bin/env python3
"""Assemble tests/fixtures/fide_history/published_periods.json: FIDE's published calculations of a few periods of the
October 2026 top 100, one for each rule that changed between February 2020 and October 2026 (SPEC-TOP100 §5.1).

Needs data/ (the cached calculations of tools/data/fetch_top100_calculations.py and FIDE's lists). The cases are chosen
by fixed rules, the first in the order of (list, FIDE ID) that shows each rule at work, in a tournament whose published
calculation the neighbouring reading does not reproduce (so that the case tells the readings apart):
  F-H01  under the 2017 regulations, a period with a game FIDE capped under the 400-point rule (not reproduced without
         the cap);
  F-H02  under the 2017 regulations, a period whose sum ends in a negative half point (the rounding of §8.57);
  F-H03  under the 2022 regulations, a tournament in which a favourite has two or more differences beyond 400 and
         FIDE capped exactly one, the one-upgrade clause (not reproduced by the plain cap of 2017);
  F-H04  from 1 March 2024 to 30 September 2025, a tournament in which FIDE capped two or more of a favourite's games
         (not reproduced by the one-upgrade clause of 2022);
  F-H05  from 1 October 2025, a game of a player rated 2650 or more beyond 400 points that FIDE did not cap (not
         reproduced by the plain cap of 1 March 2024).
Each case records, per tournament, its start, the player's Ro, K and K x sum, and per game the opponent's actual
rating (the rating FIDE used, or, where FIDE printed the capped value, the opponent's rating on the list the
tournament used, identified as analysis/e17_top100_extract.py identifies it), FIDE's cap mark, the score and FIDE's
chg; and the published change of the list. Opponents' names are never recorded; the cases are single values quoted
for verification, as in tests/fixtures/fide_calculator/. Python standard library only.

Usage: python3 tools/data/assemble_history_fixtures.py > tests/fixtures/fide_history/published_periods.json
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


def reproduced(ro: int, games: list[dict], as_of: date | None) -> bool:
    """Whether FIDE's chg of every game is reproduced under the rules in force at `as_of`, or with no cap if None."""
    pairs = [(x["opponent_rating"], Decimal(x["score"])) for x in games]
    ds = (lh.deltas(ro, pairs, as_of) if as_of else [s - layer0.expected_score(ro - r) for r, s in pairs])
    return [str(d) for d in ds] == [x["chg"] for x in games]


def main() -> int:
    lists = ex.load_lists()
    _names, index = ex.load_names()
    found: dict[str, dict] = {}
    for pair in sorted(ex.ft.plan(), key=lambda s: (s.split(":")[1], int(s.split(":")[0]))):
        pid, t = pair.split(":")
        f = ex.PAGES / f"{pid}_{t}.html"
        if not f.exists():
            continue
        page = ex.parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
        prev = layer0.month_add(t, -1)
        tours, flags = [], set()
        ok = True
        total = Decimal(0)
        for tr in page["tournaments"]:
            if not tr["start"]:
                ok = False
                break
            m = ex.list_for_ro(lists, pid, tr["ro"], tr["start"], t)
            start = date.fromisoformat(tr["start"])
            games = []
            for g in tr["games"]:
                actual = g["rating"]
                if g["capped"]:
                    oid = ex.resolve(g, tr["ro"], lists[m], index)
                    if oid is None:
                        ok = False
                        break
                    actual = lists[m][oid][0]
                games.append({"opponent_rating": actual, "capped_mark": g["capped"], "score": str(g["score"]),
                              "chg": str(g["chg"])})
            if not ok:
                break
            ds = lh.deltas(tr["ro"], [(x["opponent_rating"], Decimal(x["score"])) for x in games], start)
            if [str(d) for d in ds] != [x["chg"] for x in games]:
                ok = False
                break
            total += Decimal(tr["k"]) * sum(ds, Decimal(0))
            v = lh.version(start)
            fav = [x for x in games if tr["ro"] - x["opponent_rating"] > 400]
            capped_fav = [x for x in fav if x["capped_mark"]]
            if v == "2017" and any(x["capped_mark"] for x in games) and not reproduced(tr["ro"], games, None):
                flags.add("F-H01")
            if (v == "2022" and len(fav) >= 2 and len(capped_fav) == 1
                    and not reproduced(tr["ro"], games, date(2021, 6, 1))):
                flags.add("F-H03")
            if v == "2024" and len(capped_fav) >= 2 and not reproduced(tr["ro"], games, date(2023, 6, 1)):
                flags.add("F-H04")
            if (v == "2025-10" and tr["ro"] >= 2650 and any(not x["capped_mark"] for x in fav)
                    and not reproduced(tr["ro"], games, date(2024, 9, 1))):
                flags.add("F-H05")
            tours.append({"event": tr["event"], "start": tr["start"], "ro": tr["ro"], "k": tr["k"],
                          "k_chg": str(tr["k_chg"]), "games": games})
        if not ok or pid not in lists[t] or pid not in lists[prev]:
            continue
        change = lists[t][pid][0] - lists[prev][pid][0]
        if lh.round_change(total, t) != change:
            continue
        if t < lh.ROUNDING_2022_LIST and total < 0 and abs(total) % 1 == Decimal("0.5"):
            flags.add("F-H02")
        for fid in sorted(flags):
            if fid not in found:
                found[fid] = {"id": fid, "fide_id": int(pid), "list": t, "published_change": change,
                              "sum": str(total), "tournaments": tours}
    out = {"source": "FIDE's published per-player rating calculations (ratings.fide.com/calculations.phtml, data endpoint "
                     "/a_indv_calculation.php), cached by tools/data/fetch_top100_calculations.py; FIDE's monthly "
                     "standard lists for the published change and the opponents' actual ratings",
           "selection": "tools/data/assemble_history_fixtures.py: for each rule, the first period in the order of (list, "
                        "FIDE ID) that shows it in a tournament the neighbouring reading does not reproduce, among periods "
                        "Layer 0 with the rules in force reproduces",
           "list_values_note": "published_change and opponent_rating are single values quoted from FIDE's lists and "
                               "calculations for verification; the lists themselves are not redistributed",
           "missing": [f for f in ("F-H01", "F-H02", "F-H03", "F-H04", "F-H05") if f not in found],
           "cases": [found[k] for k in sorted(found)]}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
