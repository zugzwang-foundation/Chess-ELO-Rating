#!/usr/bin/env python3
"""E18, coverage: the games behind the self-calibrating tables, by year, level band and time control, and each year's
window under SPEC-SELFCAL §4 (session ELO-8, Phase 2; needs data/).

Builds E2's sample with E2's functions through E10's builder (analysis/e10_guard_extract.py: no archive file after
2026-09, no game dated after 2026-09-30), over every file of the Lichess broadcast archive on disk (2020-01 to 2026-09;
the archive holds none earlier, SPEC-SELFCAL §2), and counts: the archive's games by year through E2's steps (a result,
the standard variant, both FIDE IDs, a time-control class, both players rated on the list in force); the sample's games
by year and time control; the standard sample by year and 100-point level band; and, for every year from 2020 to 2026,
the window the rule W1 to W5 gives (the 36 months before the year, cut at the March 2024 compression, lengthened when a
year inside it has fewer than 20,000 standard games until it holds 20,000 a year, never before 2020-01; SPEC-SELFCAL v1.1), so that the first table's year is fixed
before any table is fitted. Counts only. Python standard library only.

Usage: python3 analysis/e18_coverage_extract.py > analysis/aggregates/E18_coverage.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's helpers, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import layer0  # noqa: E402

FIRST_DATA, LAST_DATA = "2020-01", "2026-09"
YEARS = list(range(2020, 2027))
CUT = "2024-03"                 # the first list on the compressed scale [E5]: SPEC-SELFCAL W2
G = 20000                       # SPEC-SELFCAL W3: standard sample games a calendar year needs, pro rata for a part year


def months(a: str, b: str) -> list[str]:
    out, m = [], a
    while m <= b:
        out.append(m)
        m = layer0.month_add(m, 1)
    return out


def window(y: int, by_month: Counter) -> dict:
    """SPEC-SELFCAL §4 (v1.1) for the table of year y: W1 the 36 months before y, which the data must cover; W2 cut at
    the compression; W3 if a calendar year inside it has fewer than G games (pro rata), lengthened by 12 months at a time
    until it holds G games for every 12 of the months W1 and W2 gave it, never before the data or across the cut; W4 no
    table if the data do not cover the window or it still holds too few."""
    w1_lo, hi = f"{y - 3}-01", f"{y - 1}-12"
    cut = hi >= CUT and w1_lo < CUT                     # W2
    lo = CUT if cut else w1_lo
    floor = CUT if cut else FIRST_DATA
    if lo < FIRST_DATA:                                 # W1: a window reaching before the data is not shortened
        return {"from": w1_lo, "to": hi, "table": False, "reason": "the window reaches before the first month of data",
                "cut_at_compression": False, "extended_months": 0}
    need = G * len(months(lo, hi)) / 12                 # W3: G games for every 12 months W1 and W2 gave it
    extended = 0
    while True:
        ms = months(lo, hi)
        per_year = {}
        for m in ms:
            per_year.setdefault(m[:4], [0, 0])
            per_year[m[:4]][0] += by_month[m]
            per_year[m[:4]][1] += 1
        short = sorted(yy for yy, (n, k) in per_year.items() if n < G * k / 12)
        total = sum(by_month[m] for m in ms)
        ok = not short or total >= need
        nxt = layer0.month_add(lo, -12)
        if ok or nxt < floor:
            break
        lo, extended = nxt, extended + 12
    return {"from": lo, "to": hi, "months": len(ms), "games": total, "games_needed": round(need),
            "cut_at_compression": cut, "extended_months": extended,
            "per_year": {yy: {"games": n, "months": k} for yy, (n, k) in sorted(per_year.items())},
            "years_too_few": short, "table": ok,
            "reason": "" if ok else "a year inside the window has too few games and the window cannot lengthen to enough"}


def main() -> int:
    games, raw = e2x.load_games()
    by_year = {k: Counter() for k in ("games", "with_result_standard_variant", "both_fide_ids")}
    for g in games:
        y = e2x.month_of(g.date_used)[:4]
        by_year["with_result_standard_variant"][y] += 1
        by_year["both_fide_ids"][y] += g.white_fide_id.isdigit() and g.black_fide_id.isdigit()
    del games
    smp, meta = e10.sample()
    sample = {tc: Counter() for tc in e2x.TCS}
    std_band = {}
    std_month = Counter()
    for tc in e2x.TCS:
        for m, _tour, _w, _b, rw, rb, _s, _e0 in smp[tc]:
            sample[tc][m[:4]] += 1
            if tc == "standard":
                std_month[m] += 1
                std_band.setdefault(m[:4], Counter())[e2x.band100_mid((rw + rb) // 2)] += 1
    wins = {str(y): window(y, std_month) for y in YEARS}
    first = next((y for y in YEARS if wins[str(y)]["table"]), None)
    out = {"source": "Lichess broadcast archive (https://database.lichess.org/broadcast/, CC BY-SA 4.0), every monthly "
                     f"file on disk, {FIRST_DATA} to {LAST_DATA}; E2's sample rules through E10's builder",
           "spec": "docs/specs/SPEC-SELFCAL_v1_2.md", "cutoff": meta, "raw_counts": raw,
           "archive_by_year": {k: dict(sorted(v.items())) for k, v in by_year.items()},
           "sample_by_year": {tc: dict(sorted(v.items())) for tc, v in sample.items()},
           "standard_by_year_band": {y: {str(b): n for b, n in sorted(c.items())} for y, c in sorted(std_band.items())},
           "standard_by_month": dict(sorted(std_month.items())),
           "rule": {"window_months": 36, "cut": CUT, "games_a_year": G, "first_data": FIRST_DATA},
           "windows": wins, "first_table_year": first}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
