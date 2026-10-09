#!/usr/bin/env python3
"""SPEC-L0 R-18..R-22: which K does FIDE publish? Aggregates from the monthly lists (needs data/).

Reads data/interim/fide/standard/YYYY-MM.tsv (tools/data/convert_fide_lists.py)
and prints one JSON document to standard output; the committed copy is
analysis/aggregates/L0_k_rules.json and analysis/l0_k_rules_report.py prints the
summary used in SPEC-L0. Only counts leave this script.

Population: players first listed from February 2016 onwards (so that every
rated game since their first listing is on the lists: the archive starts in
February 2015 and a one-year burn-in separates first listings from returns),
on lists from January 2017 to the last list, with a year of birth.

For each such player and list t the script derives, from the lists alone:
  junior      list year - birth year <= 18 (until the end of the year of the
              18th birthday, §8.3.3 [V 1]);
  games       rated games on all lists since the first listing, up to and
              including list t (two counts: with and without the games shown
              on the first list itself);
  ever2400    a published rating >= 2400 on any list since the first listing;
  ever2300    a published rating >= 2300 on any list since the first listing;
and tabulates the published K by cell (junior, rating band, games >= 30,
ever2400, ever2300). Two rule orders are scored against the published K:
  text order:    1 junior and R < 2300 -> 40; 2 games < 30 -> 40;
                 3 ever2400 -> 10; 4 else 20;
  refined order: 1 ever2400 -> 10; 2 junior and never rated 2300 or more -> 40;
                 3 games < 30 -> 40; 4 else 20.
Disagreements of the refined order are counted by the player's games count
(below 25, 25-34, 35 or more) and, for the largest group (published 20 where
the refined order predicts 40 with fewer than 25 counted games), by list year
and games count, because the lists cannot show the games that produced a first
rating, which FIDE's 30-game counter may include.

Usage: python3 analysis/l0_k_rules_extract.py > analysis/aggregates/L0_k_rules.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    files = sorted((ROOT / "data" / "interim" / "fide" / "standard").glob("*.tsv"))
    first_seen: dict[str, str] = {}
    cum_all: dict[str, int] = {}
    cum_after: dict[str, int] = {}
    ever2400: dict[str, bool] = {}
    ever2300: dict[str, bool] = {}
    was_junior_over: dict[str, bool] = {}
    cells: dict[str, dict[str, int]] = {}
    rule_scores = {"variant_with_first_list_games": [0, 0], "variant_without_first_list_games": [0, 0]}
    refined = [0, 0]
    refined_miss_by_games: dict[str, dict[str, int]] = {}
    k20_lt25_by_year: dict[str, int] = {}
    k20_lt25_by_games: dict[str, int] = {}
    dec_jan: dict[str, dict[str, int]] = {}
    prev_k: dict[str, str] = {}
    for f in files:
        p = f.stem
        year = int(p[:4])
        with f.open() as fh:
            next(fh)
            rows = [line.rstrip("\n").split("\t") for line in fh]
        for pid, r, g, k, by, sex, fed, flag, title in rows:
            if not r.isdigit():
                continue
            R, G = int(r), int(g) if g.isdigit() else 0
            new = pid not in first_seen
            if new:
                first_seen[pid] = p
                cum_all[pid] = G
                cum_after[pid] = 0
            else:
                cum_all[pid] += G
                cum_after[pid] += G
            if R >= 2400:
                ever2400[pid] = True
            if R >= 2300:
                ever2300[pid] = True
            if first_seen[pid] < "2016-02" or p < "2017-01" or not by.isdigit():
                prev_k[pid] = k
                continue
            junior = year - int(by) <= 18
            band = "<2300" if R < 2300 else "2300-2399" if R < 2400 else "2400+"
            for variant, cg in (("variant_with_first_list_games", cum_all[pid]),
                                ("variant_without_first_list_games", cum_after[pid])):
                if junior and R < 2300:
                    pred = "40"
                elif cg < 30:
                    pred = "40"
                elif ever2400.get(pid):
                    pred = "10"
                else:
                    pred = "20"
                rule_scores[variant][0] += pred == k
                rule_scores[variant][1] += 1
            if ever2400.get(pid):
                ref = "10"
            elif junior and not ever2300.get(pid):
                ref = "40"
            elif cum_all[pid] < 30:
                ref = "40"
            else:
                ref = "20"
            refined[0] += ref == k
            refined[1] += 1
            if ref != k:
                gb = "<25" if cum_all[pid] < 25 else "25-34" if cum_all[pid] < 35 else "35+"
                mm = refined_miss_by_games.setdefault(gb, {})
                key = f"predicted {ref}, published {k}"
                mm[key] = mm.get(key, 0) + 1
                if ref == "40" and k == "20" and cum_all[pid] < 25:
                    k20_lt25_by_year[p[:4]] = k20_lt25_by_year.get(p[:4], 0) + 1
                    gk = f"{cum_all[pid] // 5 * 5}-{cum_all[pid] // 5 * 5 + 4}"
                    k20_lt25_by_games[gk] = k20_lt25_by_games.get(gk, 0) + 1
            cell = (f"junior={junior}|band={band}|games30={cum_all[pid] >= 30}|"
                    f"ever2400={bool(ever2400.get(pid))}|ever2300={bool(ever2300.get(pid))}")
            c = cells.setdefault(cell, {})
            c[k] = c.get(k, 0) + 1
            # December -> January transition for players in the year of their 18th birthday
            if p.endswith("-01") and year - int(by) == 19 and R < 2300 and cum_all[pid] >= 30 and not ever2400.get(pid):
                key = f"{year - 1}-12 -> {p}"
                d = dec_jan.setdefault(key, {})
                t = f"{prev_k.get(pid, '-')}->{k}"
                d[t] = d.get(t, 0) + 1
            prev_k[pid] = k
    out = {
        "population": "players first listed from 2016-02, lists 2017-01 onwards, with a year of birth",
        "rule_order": "junior & R<2300 -> 40; games<30 -> 40; ever published >= 2400 -> 10; else 20",
        "agreement": {v: {"agree": a, "n": n, "share": round(a / n, 6) if n else None} for v, (a, n) in rule_scores.items()},
        "refined_order": "ever published >= 2400 -> 10; junior never rated >= 2300 -> 40; games<30 -> 40; else 20",
        "refined_agreement": {"agree": refined[0], "n": refined[1], "share": round(refined[0] / refined[1], 6)},
        "refined_disagreements_by_games": {k: dict(sorted(v.items())) for k, v in sorted(refined_miss_by_games.items())},
        "residual_published20_predicted40_games_lt25_by_list_year": dict(sorted(k20_lt25_by_year.items())),
        "residual_published20_predicted40_games_lt25_by_games": dict(sorted(k20_lt25_by_games.items(), key=lambda kv: int(kv[0].split("-")[0]))),
        "published_k_by_cell": dict(sorted(cells.items())),
        "turning_19_december_to_january": dict(sorted(dec_jan.items())),
    }
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
