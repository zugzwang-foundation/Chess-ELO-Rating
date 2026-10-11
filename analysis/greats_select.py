#!/usr/bin/env python3
"""The greats: who is studied (SPEC-GREATS v1.0 §2; session ELO-9, Phase 2; needs data/). Run after the selection rule
was written and before any other computation on these players.

The rule (the founder default of the ELO-9 brief): everyone ranked 1st to 3rd on any FIDE standard list from July 1971
to December 2019 that the data probe found legitimately available (docs/research/DATA-PROBE_greats.md):
- **July 1971 to April 2000**: FIDE's official lists as OlimpBase transcribes them, without the supplementary lists of
  July 1978, 1979 and 1980, which carry only a few players. A player's rank is 1 + the number of ranked players with a
  higher rating (players tied share a rank); ranked are the players with a rating who are not flagged inactive and,
  from the January 1999 list, are active by FIDE's rule for the top list (FIDE Handbook, B.02 §9.2.3a and §9.2.3d,
  GA '98: fewer than four rated games in a one-year period make a player inactive, and an inactive player no longer
  appears on the top list), counted on the games of the lists dated in the twelve months up to the list.
- **July 2000 to December 2019**: FIDE's own printed top-100 list of the date (FIDE's top-list archive, as the Internet
  Archive keeps it), the rank as FIDE printed it. Where no copy survives, the rank is computed as above from FIDE's full
  list of the date (OlimpBase's for 2000), with the activity rule in force: fewer than four rated games in the twelve
  months to June 2009, no rated game from the list of July 2009 (B.02 §7.23a and §7.24 of the version FIDE's handbook
  carried in 2010; the date of the change is read as July 2009, NOT VERIFIED).
- **The player**: on OlimpBase's lists, OlimpBase's standard form of the name (FIDE's IDs start in 1990, changed format
  in July 1990, changed again with some federations, and were reassigned: Shirov's Latvian ID of 1994 belongs to another
  player on FIDE's later lists), joined to the FIDE ID that the same name carries on OlimpBase's lists of 2001, which
  equal FIDE's own files of 2001 rating for rating (E20); on FIDE's files, the FIDE ID; on a printed top list, the ID
  that FIDE's full list of the date gives the same name and federation.
Writes analysis/aggregates/GREATS_players.json: for each player selected, the ID, the name, the federation, the lists on
which the player ranked 1st and 1st to 3rd, the first and last such list and the best rank; for each list date, the
rank's source; and, on the dates with both a printed top list and a full list, whether the computed top three equal
the printed ones. No rating is written. `--table` prints, from that aggregate (no data needed), the table SPEC-GREATS
§2 carries (tests/test_greats_spec.py checks the two agree). Python standard library only.

Usage: python3 analysis/greats_select.py > analysis/aggregates/GREATS_players.json
       python3 analysis/greats_select.py --table
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates" / "GREATS_players.json"
OB = ROOT / "data" / "interim" / "olimpbase"
OLD = ROOT / "data" / "interim" / "fide_old" / "standard"
NEW = ROOT / "data" / "interim" / "fide" / "standard"
TOP = ROOT / "data" / "interim" / "fide_toparc"
FIRST, LAST = "1971-07", "2019-12"
PRINTED_FROM = "2000-07"
SUPPLEMENTARY = ("1978-07", "1979-07", "1980-07")
INACTIVE = ("i", "wi")
TOP_RULE_FROM, ONE_GAME_FROM = "1999-01", "2009-07"


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:]) - int(a[5:])


def full_lists() -> list[tuple[str, str, Path]]:
    """Every full list of the period, in date order: OlimpBase's to October 2000, FIDE's own from January 2001."""
    out = [(p.stem, "OlimpBase", p) for p in sorted(OB.glob("*.tsv"))
           if FIRST <= p.stem <= "2000-12" and p.stem not in SUPPLEMENTARY]
    out += [(p.stem, "FIDE", p) for p in sorted(OLD.glob("*.tsv")) if "2001-01" <= p.stem <= "2015-01"]
    out += [(p.stem, "FIDE", p) for p in sorted(NEW.glob("*.tsv")) if "2015-02" <= p.stem <= LAST]
    return out


def main() -> int:
    lists = full_lists()
    link: dict[str, str] = {}                        # OlimpBase's standard name -> its FIDE ID on the lists of 2001
    for path in sorted(OB.glob("2001-*.tsv")):
        for r in rows(path):
            if r["id"]:
                link[r["name"]] = r["id"]
    names_by_id: dict[str, dict] = defaultdict(dict)
    games: dict[str, dict[str, int]] = defaultdict(dict)   # key -> list date -> games rated on that list
    entries: dict[str, list[tuple]] = {}
    for period, src, path in lists:
        es = []
        for r in rows(path):
            key = (link.get(r["name"]) or f"name:{r['name']}") if src == "OlimpBase" else r["id"]
            names_by_id[key][period] = (r.get("name", ""), r.get("fed", ""))
            g = r.get("games", "")
            games[key][period] = int(g) if g.isdigit() else 0
            rating = r.get("rating", "")
            if rating.isdigit() and int(rating) > 0:
                es.append((key, int(rating), r.get("flag", "")))
        entries[period] = es
    dates = [p for p, _s, _f in lists]

    def computed(period: str) -> list[tuple[str, int]]:
        """(key, rank) of the players ranked 1st to 3rd on a full list, by the rule of §2."""
        recent = [d for d in dates if 0 <= months_between(d, period) < 12]
        need = 0 if period < TOP_RULE_FROM else (4 if period < ONE_GAME_FROM else 1)
        ranked = [(k, r) for k, r, fl in entries[period] if fl not in INACTIVE
                  and (need == 0 or sum(games[k].get(d, 0) for d in recent) >= need)]
        ratings = sorted((r for _k, r in ranked), reverse=True)
        third = ratings[2]
        return [(k, 1 + sum(1 for x in ratings[:3] if x > r)) for k, r in ranked if r >= third]

    printed: dict[str, list[tuple[str, int]]] = {}
    for p in sorted(TOP.glob("*.tsv")):
        if PRINTED_FROM <= p.stem <= LAST:
            top = rows(p)
            printed[p.stem] = [(r["id"] or f"name:{r['name']}", int(r["rank"])) for r in top if int(r["rank"]) <= 3]
            for r in top:
                if r["id"]:
                    names_by_id[r["id"]].setdefault(p.stem, (r["name"], r["fed"]))
    all_dates = sorted(set(dates) | set(printed))
    source, agreement = {}, []
    sel: dict[str, dict] = {}
    for period in all_dates:
        if period in printed:
            top3, source[period] = printed[period], "printed top list"
            if period in entries:
                comp = computed(period)
                agreement.append({"list": period, "printed": sorted(k for k, _r in top3),
                                  "computed": sorted(k for k, _r in comp),
                                  "equal": sorted(k for k, _r in top3) == sorted(k for k, _r in comp)})
        else:
            top3 = computed(period)
            source[period] = "computed from OlimpBase's list" if period < "2001-01" else "computed from FIDE's list"
        for key, rank in top3:
            s = sel.setdefault(key, {"lists_rank1": 0, "lists_top3": 0, "first_top3": period, "best_rank": rank})
            s["lists_rank1"] += rank == 1
            s["lists_top3"] += 1
            s["last_top3"] = period
            s["best_rank"] = min(s["best_rank"], rank)
    players = []
    for key, s in sel.items():
        seen = names_by_id.get(key, {})
        names = [(p, n) for p, (n, _f) in seen.items() if n]
        feds = [(p, f) for p, (_n, f) in seen.items() if f]
        players.append({"key": key, "fide_id": None if key.startswith("name:") else int(key),
                        "name": max(names)[1] if names else key[5:], "federation": max(feds)[1] if feds else "",
                        "lists_rank1": s["lists_rank1"], "lists_top3": s["lists_top3"],
                        "first_top3": s["first_top3"], "last_top3": s["last_top3"], "best_rank": s["best_rank"]})
    players.sort(key=lambda x: (x["first_top3"], x["name"]))
    by_source: dict[str, int] = defaultdict(int)
    for v in source.values():
        by_source[v] += 1
    out = {"rule": "ranked 1st to 3rd on any FIDE standard list from July 1971 to December 2019: OlimpBase's "
                   "transcription of FIDE's lists to April 2000, ranks computed; FIDE's printed top lists from July "
                   "2000 where the Internet Archive keeps them, otherwise ranks computed from FIDE's full list; "
                   "inactive players are not ranked (FIDE's flags and, from January 1999, FIDE's top-list rule)",
           "lists": {"dates": len(all_dates), "first": all_dates[0], "last": all_dates[-1],
                     "by_source": dict(sorted(by_source.items())),
                     "computed_dates_from_2000_07": [p for p in all_dates if p >= PRINTED_FROM and p not in printed],
                     "excluded_supplementary": list(SUPPLEMENTARY)},
           "printed_vs_computed": {"dates": len(agreement), "equal": sum(1 for a in agreement if a["equal"]),
                                   "unequal": [a for a in agreement if not a["equal"]]},
           "players": players}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def table(out: dict) -> list[str]:
    t = ["| # | name | FIDE ID | federation | first list ranked 1–3 | last | lists ranked 1–3 | lists ranked 1st | best "
         "rank |", "|---|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(out["players"], 1):
        t.append(f"| {i} | {p['name']} | {p['fide_id'] or '—'} | {p['federation']} | {p['first_top3']} | "
                 f"{p['last_top3']} | {p['lists_top3']} | {p['lists_rank1']} | {p['best_rank']} |")
    return t


if __name__ == "__main__":
    if "--table" in sys.argv[1:]:                    # from the committed aggregate; needs no data
        sys.stdout.write("\n".join(table(json.loads(AGG.read_text(encoding="utf-8")))) + "\n")
        sys.exit(0)
    sys.exit(main())
