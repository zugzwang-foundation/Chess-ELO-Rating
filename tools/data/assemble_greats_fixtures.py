#!/usr/bin/env python3
"""Assemble tests/fixtures/fide_greats/published_periods.json: a small sample of FIDE's published calculations of the
greats' periods (ruling R79, docs/decisions/D-0017_rulings-on-the-greats.md: at most 30 player-periods, chosen by a
fixed rule), for the rules src/layer0_greats/ transcribes from the texts in force before July 2017 (SPEC-GREATS v1.0 §6;
docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md) and the rounding the rulings R74 and R80 adopt (SPEC-L0 §11,
F-H09 and F-H10; R80, docs/decisions/D-0018_rulings-on-elo-9-questions.md, adds F-G15 and F-G16 within R79's cap). The
full reproduction runs locally from the gitignored cache (analysis/e20_greats_replay_extract.py), and only its counts
are committed.

Needs data/ (the calculations cached by tools/data/fetch_greats_calculations.py and FIDE's lists). Every case is
chosen among the periods Layer 0 with the rules in force reproduces (every game, every tournament and the published
change), in the order of (list, FIDE ID) unless stated otherwise:
  F-G01  the first with a tournament starting before 1 July 2009 and a game FIDE printed at the 350-point cap, the
         opponent's rating on the list in force beyond it, not reproduced by the 400-point rule;
  F-G02  the first with a tournament starting from 1 July 2009 to 30 June 2014 and a game FIDE marked as capped at
         400 points, not reproduced without the cap;
  F-G03  the first with a tournament of the same version and a gap of 351 to 400 points counted in full, not
         reproduced by the 350-point rule;
  F-G04  the first with a tournament starting before 1 July 2009 whose printed K is 15, the player's published rating
         never 2400 before (K of §10.52 of the October 2007 text);
  F-G05  the first with a tournament starting from 1 July 2014 to 30 June 2017 and a game FIDE marked as capped at 400
         points, not reproduced without the cap;
  F-G06  the first on a list before July 2014 whose sum ends in a negative half point, the published change rounded
         towards +infinity (R74), not reproduced by rounding away from zero;
  F-G07 to F-G10  the first period with a tournament of each version: 2007 (starting before 1 July 2009), 2009, 2014
         and 2017 (from 1 July 2017, layer0_history's);
  F-G11, F-G12  either side of 1 July 2009: the period holding the tournament with the latest start before it, and
         the one holding the earliest start on or after it (ties in the order of list and FIDE ID);
  F-G13, F-G14  the same either side of 1 July 2014;
  F-G15  R80's last period before the switch: on the latest list published before November 2018 that holds one, the
         first period whose sum ends in a negative half point, the published change rounded towards +infinity, not
         reproduced by rounding away from zero;
  F-G16  R80's first period after it: the first period on a list published from November 2018 whose sum ends in a
         negative half point, the published change rounded away from zero, not reproduced by rounding towards
         +infinity.
Each case records, per tournament, its start, the player's Ro, K and K x sum, and per game the opponent's rating (the
rating FIDE used, or, where FIDE printed the capped value, the opponent's rating on the list in force, found as
analysis/e20_greats_replay_extract.py finds it), the rating FIDE printed, FIDE's cap mark, the score and FIDE's chg;
and the published change of the list. No name, FIDE ID or event is recorded: the cases are single values quoted for
verification, as in tests/fixtures/fide_history/. Python standard library only.

Usage: python3 tools/data/assemble_greats_fixtures.py > tests/fixtures/fide_greats/published_periods.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e20_greats_replay_extract as rx  # noqa: E402  (the replay's lists, pages and look-ups, one rule for both)
import layer0  # noqa: E402
import layer0_greats as lg  # noqa: E402

IDS = tuple(f"F-G{i:02d}" for i in range(1, 17))
MAX_PERIODS = 30                # R79


def reproduced(ro: int, games: list[dict], as_of: date | None) -> bool:
    """Whether FIDE's chg of every game is reproduced under the rules in force at `as_of`, or with no cap if None."""
    pairs = [(x["opponent_rating"], Decimal(x["score"])) for x in games]
    ds = (lg.deltas(ro, pairs, as_of) if as_of else [s - layer0.expected_score(ro - r) for r, s in pairs])
    return [str(d) for d in ds] == [x["chg"] for x in games]


def main() -> int:
    plan = rx.fg.plan()
    ids = sorted({x.split(":")[0] for x in plan}, key=int)
    dates = rx.list_dates()
    lists, _keys = rx.load_lists(dates, set(ids))
    series = json.loads(rx.SERIES.read_text(encoding="utf-8"))
    pages = {}
    for pair in plan:
        pid, t = pair.split(":")
        f = rx.PAGES / f"{pid}_{t}.html"
        if f.exists():
            pages[(pid, t)] = rx.ex.parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
    needed: dict[str, set] = defaultdict(set)
    for (pid, t), page in pages.items():
        for tr in page["tournaments"]:
            m = rx.list_for_ro(lists, dates, pid, tr["ro"], tr["start"], t)
            for g in tr["games"]:
                if rx.maybe_capped(g, tr["ro"]):
                    needed[m].add(rx.ex.norm(g["name"]))
    index = rx.name_index(needed)
    found: dict[str, dict] = {}
    edge: dict[str, tuple] = {}             # either side of a date: (start, list, FIDE ID) and the case
    switch: dict[str, tuple] = {}           # R80: the last period before the switch (list, case), the first after it
    for (pid, t), page in sorted(pages.items(), key=lambda x: (x[0][1], int(x[0][0]))):
        if t not in dates or t <= rx.START:
            continue
        prev = rx.prev_of(dates, t)
        if pid not in lists[t] or pid not in lists[prev]:
            continue
        tours, flags, ok, total = [], set(), True, Decimal(0)
        starts = []
        for tr in page["tournaments"]:
            if not tr["start"]:
                ok = False
                break
            start = date.fromisoformat(tr["start"])
            m = rx.list_for_ro(lists, dates, pid, tr["ro"], tr["start"], t)
            games = []
            for g in tr["games"]:
                actual = g["rating"]
                if rx.maybe_capped(g, tr["ro"]):
                    r = rx.resolve(g, tr["ro"], index.get(m, {}))
                    if r is None:
                        ok = False
                        break
                    actual = r
                games.append({"opponent_rating": actual, "printed_rating": g["rating"], "capped_mark": g["capped"],
                              "score": str(g["score"]), "chg": str(g["chg"])})
            if not ok or not reproduced(tr["ro"], games, start):
                ok = False
                break
            ds = lg.deltas(tr["ro"], [(x["opponent_rating"], Decimal(x["score"])) for x in games], start)
            if Decimal(tr["k"]) * sum(ds, Decimal(0)) != tr["k_chg"]:
                ok = False
                break
            total += tr["k_chg"]
            ver = lg.version(start)
            starts.append(tr["start"])
            gaps = [(tr["ro"] - x["opponent_rating"], tr["ro"] - x["printed_rating"], x["capped_mark"]) for x in games]
            if ver == "2007" and any(abs(gs) == 350 < abs(ga) for ga, gs, _c in gaps) and \
                    not reproduced(tr["ro"], games, date(2009, 7, 1)):
                flags.add("F-G01")
            if ver == "2009" and any(c and abs(ga) > 400 for ga, _gs, c in gaps) and not reproduced(tr["ro"], games, None):
                flags.add("F-G02")
            if ver == "2009" and any(350 < abs(ga) <= 400 and ga == gs for ga, gs, _c in gaps) and \
                    not reproduced(tr["ro"], games, date(2009, 6, 30)):
                flags.add("F-G03")
            if ver == "2007" and tr["k"] == 15 and not any(r >= 2400 for mm, r in series[pid].items() if mm <= prev):
                flags.add("F-G04")
            if ver == "2014" and any(c and abs(ga) > 400 for ga, _gs, c in gaps) and not reproduced(tr["ro"], games, None):
                flags.add("F-G05")
            flags.add({"2007": "F-G07", "2009": "F-G08", "2014": "F-G09"}.get(ver, "F-G10"))
            tours.append({"start": tr["start"], "ro": tr["ro"], "k": tr["k"], "k_chg": str(tr["k_chg"]),
                          "games": games})
        if not ok:
            continue
        change = lists[t][pid][0] - lists[prev][pid][0]
        if lg.round_change(total, t) != change:
            continue
        negative_half = total < 0 and abs(total) % 1 == Decimal("0.5")
        if t < lg.ROUNDING_2014_LIST and negative_half and lg.round_change_away(total) != change:
            flags.add("F-G06")
        case = {"list": t, "published_change": change, "sum": str(total),
                "ever_2400_before": any(r >= 2400 for mm, r in series[pid].items() if mm <= prev), "tournaments": tours}
        for fid in sorted(flags):
            if fid not in found:
                found[fid] = {"id": fid, **case}
        if negative_half and t < lg.ROUNDING_2018_LIST and lg.round_change_away(total) != change and \
                ("F-G15" not in switch or t > switch["F-G15"][0]):
            switch["F-G15"] = (t, {"id": "F-G15", **case})
        if negative_half and t >= lg.ROUNDING_2018_LIST and lg.round_change_up(total) != change and "F-G16" not in switch:
            switch["F-G16"] = (t, {"id": "F-G16", **case})
        for d0, before, after in (("2009-07-01", "F-G11", "F-G12"), ("2014-07-01", "F-G13", "F-G14")):
            lo = max((x for x in starts if x < d0), default=None)
            hi = min((x for x in starts if x >= d0), default=None)
            if lo is not None and (before not in edge or lo > edge[before][0]):
                edge[before] = (lo, {"id": before, **case})
            if hi is not None and (after not in edge or hi < edge[after][0]):
                edge[after] = (hi, {"id": after, **case})
    found.update({k: v for k, (_s, v) in edge.items()})
    found.update({k: v for k, (_t, v) in switch.items()})
    out = {"source": "FIDE's published per-player rating calculations (ratings.fide.com/calculations.phtml, data endpoint "
                     "/a_indv_calculation.php), cached by tools/data/fetch_greats_calculations.py; FIDE's standard lists "
                     "for the published change and the opponents' ratings",
           "selection": "tools/data/assemble_greats_fixtures.py (R79: at most 30 player-periods, a fixed rule): for each "
                        "rule, the first period in the order of (list, FIDE ID) that shows it in a tournament the "
                        "neighbouring reading does not reproduce, the first period of each version, the periods either "
                        "side of 1 July 2009 and of 1 July 2014, and R80's periods either side of the switch of rounding "
                        "(the last before November 2018 and the first from it whose sum ends in a negative half point), "
                        "among periods Layer 0 with the rules in force reproduces",
           "list_values_note": "published_change, opponent_rating and printed_rating are single values quoted from FIDE's "
                               "lists and calculations for verification; the lists themselves are not redistributed",
           "missing": [f for f in IDS if f not in found],
           "cases": [found[k] for k in sorted(found)]}
    periods = {(c["list"], c["sum"], json.dumps(c["tournaments"], sort_keys=True)) for c in out["cases"]}
    if len(periods) > MAX_PERIODS:
        raise SystemExit(f"{len(periods)} player-periods: more than R79's {MAX_PERIODS}")
    out["player_periods"] = len(periods)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
