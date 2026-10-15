#!/usr/bin/env python3
"""E21, the club-level sample's plan (session ELO-D2, step 2; needs data/): the frame by stratum, the pilot's rates,
the allocation and what it should bring, totals only; written before the main fetch, which draws its sample with this
allocation (tools/data/fetch_sourcing.py, mode club-plan) and renders as docs/specs/SPEC-SOURCING_v1_1.md.

1. **The frame** (SPEC-SOURCING v1.1 §2): the pilot's, the October 2025 list's active players of 75 federations with
   their 2025 periods with games (tools/data/fetch_sourcing.py, club_frame), by stratum: level band of the October 2025
   list (1400-1599, 1600-1799, 1800-1999, 2000-2199, 2200 or more) x group (juniors as E6 defines them, newcomers first
   rated from January 2023, others; at 2200 or more newcomers go with the others). FIDE's own counts: players, pages,
   player-games.
2. **The pilot's rates** (pilot-informed, decided after seeing the pilot): on the pilot's 2,000 pages, read by the
   extended parser and with opponents identified by name, federation and rating within 50 points
   (analysis/e21_club_common.py), the share of a stratum's game rows that are games of an adult against a junior, by
   the adult's level band, counted from the adult's side on either player's page; the pilot's rows are not weighted.
3. **The allocation**: 300 pages at 2200 or more, the anchor; 5,190 in the four bands from 1400 to 2199; within each
   band the groups drawn in proportion to their players, juniors and newcomers counted three times (the pilot's
   factor); the four bands' totals set one page at a time, each to the band that adds most to the threshold furthest
   from being met, the seven thresholds being 5,000 games in each band from 1400 to 2199 and 1,000 games of adults
   against juniors in each band below 2000, at FIDE's games per page in each stratum and the pilot's shares. In all
   5,490 pages, so that with robots.txt and any retry the session stays within the hard cap of 5,500 requests.
4. **What it should bring**, at those rates: games by band; games of adults against juniors by the adult's band;
   newcomers' first-year games by age when first rated.

No player's name, FIDE ID or row leaves data/. Python standard library only.

Usage: python3 analysis/e21_club_plan_extract.py > analysis/aggregates/E21_club_plan.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e21_club_common as cc  # noqa: E402  (the extended parser, the resolver, the groups)

fs = cc.fs
BANDS4 = ("1400-1599", "1600-1799", "1800-1999", "2000-2199")
BELOW_2000 = BANDS4[:3]
STRATA = tuple(f"{b}|{g}" for b in BANDS4 for g in fs.CLUB_GROUPS) + ("2200+|junior", "2200+|other")
TOTAL_PAGES = 5490
ANCHOR_PAGES = 300
OVERSAMPLE = 3                      # juniors and newcomers counted three times, the pilot's factor
TARGET_GAMES = 5000                 # games on the pages of each band from 1400 to 2199
TARGET_ADULT_JUNIOR = 1000          # games of adults against juniors in each band below 2000, by the adult's band
NEWCOMER_FIRST = "2024-04"          # the newcomer analysis: first rated from April 2024 (E21 §3.3)


def largest_remainder(total: int, weights: dict[str, float]) -> dict[str, int]:
    tot = sum(weights.values())
    raw = {k: total * w / tot for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (-(raw[k] - out[k]), k))[:total - sum(out.values())]:
        out[k] += 1
    return out


def pilot_rates() -> dict:
    """The pilot's game rows by D2 stratum: rows, adult-junior rows by the adult's band, first-year rows of newcomers
    first rated from April 2024 by age when first rated, near-equal rows (at most 25 points apart) by the game's level."""
    plan = json.loads(fs.PLAN.read_text(encoding="utf-8"))
    pages = {}
    for s in plan["sample"]:
        f = fs.CALCS / f"{s['id']}_{s['period']}.html"
        if f.exists():
            pages[(s["id"], s["period"])] = cc.parse_page_club(f.read_text(encoding="utf-8-sig", errors="replace"))
    first = fs.first_rated()
    oct25 = fs.read_list(fs.FRAME_LIST)
    ids, how = cc.resolve_all(pages)
    months = sorted({fs.month_add("2025-12", -k) for k in range(0, 36)})
    births = cc.births_of({i for i in ids.values() if i} | {k[0] for k in pages}, [fs.FRAME_LIST] + months[::-1])
    rows: dict[str, Counter] = defaultdict(Counter)
    for key, pg in pages.items():
        pid, period = key
        r, _g, _k, by, _fed, _flag = oct25[pid]
        band = fs.club_band(r)
        st = f"{band}|{fs.club_group(by, first.get(pid), band)}"
        c = rows[st]
        c["pages"] += 1
        me_junior = cc.is_junior(births.get(pid))
        fy = (first.get(pid) or "") >= NEWCOMER_FIRST and 0 < cc.months_after(first[pid], period) <= 12
        if fy:
            c["first_year_pages"] += 1
        for ti, t in enumerate(pg["tournaments"]):
            for gi, g in enumerate(t["games"]):
                c["rows"] += 1
                if fy and births.get(pid):
                    c[f"first_year|{cc.age_band(int(first[pid][:4]) - births[pid])}"] += 1
                if g["mark"] and not g["capped"] and abs(t["ro"] - g["rating"]) <= 25 and t["ro"]:
                    lv = fs.club_band(int((t["ro"] + g["rating"]) / 2)) or "below 1400"
                    c[f"near_equal|{lv}"] += 1
                oid = ids[(key, ti, gi)]
                if oid is None or g["capped"] or not t["ro"]:
                    continue
                them_junior = cc.is_junior(births.get(oid))
                if not me_junior and them_junior:
                    c[f"adult_junior|{fs.club_band(t['ro']) or 'below 1400'}"] += 1
                elif me_junior and not them_junior:
                    c[f"adult_junior|{fs.club_band(g['rating']) or 'below 1400'}"] += 1
    return {"pages": len(pages), "opponents": how, "by_stratum": {k: dict(v) for k, v in sorted(rows.items())}}


def allocate(frame: dict, rates: dict) -> dict:
    gpp = {s: frame[s]["player_games"] / frame[s]["pages"] for s in STRATA}
    share = {s: {k: v / rates[s]["rows"] for k, v in rates[s].items() if k.startswith(("adult_junior|", "first_year|",
                                                                                      "near_equal|"))}
             for s in STRATA}
    mix = {}
    for b in BANDS4:
        w = {f"{b}|{g}": frame[f"{b}|{g}"]["players"] * (1 if g == "other" else OVERSAMPLE) for g in fs.CLUB_GROUPS}
        tot = sum(w.values())
        mix[b] = {s: x / tot for s, x in w.items()}

    def per_page(b: str, what: str) -> float:
        """A page of band b's mix: its games (what = 'games|band'), or its adult-junior games at an adult band."""
        kind, lv = what.split("|", 1)
        if kind == "games":
            return sum(m * gpp[s] for s, m in mix[b].items()) if lv == b else 0.0
        return sum(m * gpp[s] * share[s].get(f"adult_junior|{lv}", 0.0) for s, m in mix[b].items())
    targets = {**{f"games|{b}": TARGET_GAMES for b in BANDS4}, **{f"adult_junior|{b}": TARGET_ADULT_JUNIOR
                                                                  for b in BELOW_2000}}
    n = {b: 0 for b in BANDS4}
    while sum(n.values()) < TOTAL_PAGES - ANCHOR_PAGES:
        got = {t: sum(n[b] * per_page(b, t) for b in BANDS4) / v for t, v in targets.items()}
        worst = min(got, key=lambda t: (got[t], t))
        n[max(BANDS4, key=lambda b: (per_page(b, worst), -BANDS4.index(b)))] += 1
    pages = {}
    for b in BANDS4:
        pages.update(largest_remainder(n[b], {s: frame[s]["players"] * (1 if s.endswith("|other") else OVERSAMPLE)
                                              for s in mix[b]}))
    pages.update(largest_remainder(ANCHOR_PAGES, {"2200+|junior": frame["2200+|junior"]["players"] * OVERSAMPLE,
                                                  "2200+|other": frame["2200+|other"]["players"]}))
    for s, k in pages.items():
        if k > frame[s]["players"]:
            raise SystemExit(f"{s}: {k} pages for {frame[s]['players']} players")
    # what it should bring, stratum by stratum at FIDE's games per page and the pilot's shares
    expect: dict[str, float] = defaultdict(float)
    for s, k in pages.items():
        expect[f"games|{s.split('|')[0]}"] += k * gpp[s]
        for what, sh in share[s].items():
            expect[what] += k * gpp[s] * sh
    return {"pages": pages, "band_totals": n, "games_per_page": {s: round(gpp[s], 3) for s in STRATA},
            "shares": {s: {k: round(v, 4) for k, v in sorted(share[s].items())} for s in STRATA},
            "expected": {k: round(v) for k, v in sorted(expect.items())},
            "thresholds_met": {t: round(expect[t]) >= v for t, v in targets.items()}}


def main() -> int:
    fr = fs.club_frame()
    first = fs.first_rated()
    frame = {}
    for st, pool in sorted(fr["strata"].items()):
        frame[st] = {"players": len(pool), "pages": sum(len(p["periods"]) for p in pool),
                     "player_games": sum(sum(p["games"]) for p in pool),
                     "first_rated_from_april_2024": sum(1 for p in pool if (first.get(p["id"]) or "") >= NEWCOMER_FIRST)}
    rates = pilot_rates()
    out = {"label": "plan, written before the main fetch; the shares are the pilot's, decided after seeing the pilot",
           "frame_list": fs.FRAME_LIST, "federations": len(fr["federations"]), "frame": frame,
           "frame_total": {k: sum(v[k] for v in frame.values()) for k in ("players", "pages", "player_games")},
           "newcomers_at_2200_or_more": sum(1 for p in fr["strata"]["2200+|other"]
                                            if (p["first"] or "") >= fs.CLUB_NEWCOMER_FROM),
           "pilot": rates,
           "rule": {"total_pages": TOTAL_PAGES, "anchor_pages": ANCHOR_PAGES, "oversample": OVERSAMPLE,
                    "target_games": TARGET_GAMES, "target_adult_junior": TARGET_ADULT_JUNIOR,
                    "cap_requests": fs.CLUB_CAP, "seed": fs.CLUB_SEED, "newcomer_first": NEWCOMER_FIRST,
                    "junior_max_age": fs.CLUB_JUNIOR_MAX_AGE, "newcomer_from": fs.CLUB_NEWCOMER_FROM,
                    "tolerance": cc.TOLERANCE},
           "allocation": allocate(frame, rates["by_stratum"])}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
