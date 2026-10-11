#!/usr/bin/env python3
"""E17 extraction: the October 2026 top 100 replayed from January 2020 under Layer 0 and under rung 2 (SPEC-TOP100).

Needs data/ (never committed): FIDE's monthly standard lists January 2020 to October 2026 (data/interim/fide/standard/
and, for names, data/raw/fide/standard/), FIDE's per-player calculations of the top 100 (data/raw/fide_calculations/,
fetched by tools/data/fetch_top100_calculations.py) and the Lichess broadcast archive (data/interim/broadcast/). Nothing
from the November 2026 rating period is read. It replays the 100 together, month by month, from their January 2020
ratings: under Layer 0 with the rules in force at each date (src/layer0_history/), validated against FIDE's published
calculations and lists first; and under rung 2, the v2 table of Freeze 3 with the narrowed guard at today's K (R44), with
and without the colour term, colours matched from the broadcast archive (SPEC-TOP100 §6). Writes
analysis/aggregates/E17_top100.json: aggregates and the per-player figures SPEC-TOP100 §7 defines, identified by FIDE
ID; no name, page or monthly per-player series. With --feed PATH it also writes the operator's monthly series of both
systems' ratings (names included) to PATH, outside the repository, never committed. Python standard library only.

Usage: python3 analysis/e17_top100_extract.py > analysis/aggregates/E17_top100.json [--feed ~/Downloads/FILE.csv]
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "data"))
sys.path.insert(0, str(ROOT / "src"))
import convert_fide_lists as cfl  # noqa: E402  (the lists' fixed-width columns)
import e2_broadcast_extract as e2  # noqa: E402  (E2's time-control classifier, unchanged)
import fetch_top100_calculations as ft  # noqa: E402  (the players and the pages: one rule for fetch and replay)
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402
from layer2 import guard_v2 as gv2  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

LISTS = ROOT / "data" / "interim" / "fide" / "standard"
RAW_LISTS = ROOT / "data" / "raw" / "fide" / "standard"
PAGES = ROOT / "data" / "raw" / "fide_calculations"
BROADCAST = ROOT / "data" / "interim" / "broadcast"
START, FIRST, LAST = "2020-01", "2020-02", "2026-10"
MONTHS = ft.months(START, LAST)
LOOKUP = ft.months("2019-01", LAST)     # lists a tournament rated from February 2020 may have started under
V2 = t2.load((ROOT / "params" / "table_fit_2026-10b.yaml").read_text(encoding="utf-8"), "standard")
PAR = V2["par"]
ETA = t2.eta_whole(PAR[2])
GUARD = re.search(r"^standard:\n((?:  .*\n?)+)", (ROOT / "params" / "guard_2026-10b.yaml").read_text(encoding="utf-8"), re.M)
GUARD_APPLIES = re.search(r"^  applies: (\w+)$", GUARD.group(1), re.M).group(1) == "true"
FIT_FROM = "2023-10"          # the v2 table's fit window starts here: games of lists from 2023-11 are in sample
SCORE = {"1.00": Decimal(1), "0.50": Decimal("0.5"), "0.00": Decimal(0)}


# ------------------------------------------------------------------ lists
def load_lists() -> dict[str, dict[str, tuple]]:
    out = {}
    for m in LOOKUP:
        d = {}
        with (LISTS / f"{m}.tsv").open(encoding="utf-8") as fh:
            rows = csv.reader(fh, delimiter="\t")
            next(rows)
            for pid, rating, games, k, by, _sex, fed, flag, title in rows:
                if rating.isdigit():
                    d[pid] = (int(rating), int(games) if games.isdigit() else 0, int(k) if k.isdigit() else 0, fed, flag)
        out[m] = d
    return out


def norm(name: str) -> str:
    """A name's key: accents, case and punctuation removed and the words sorted, so that "Surname, Given" and
    "Given Surname" meet."""
    s = unicodedata.normalize("NFKD", html.unescape(name)).encode("ascii", "ignore").decode("ascii").casefold()
    return " ".join(sorted(re.sub(r"[^a-z]+", " ", s).split()))


def load_names() -> tuple[dict[str, str], dict]:
    """FIDE ID -> name (the latest list that carries it), and the index: (name key, federation) -> IDs and, under the
    key (name key, None), the IDs of every federation, over every list."""
    by_id: dict[str, str] = {}
    index: dict = defaultdict(set)
    for m in LOOKUP:
        y, mo = m.split("-")
        tag = f"{cfl.MONTHS[int(mo) - 1]}{y[2:]}"
        z = RAW_LISTS / f"standard_{tag}frl.zip"
        with zipfile.ZipFile(z) as zf:
            raw = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
        sp = cfl.spans(raw[0], tag.upper())
        (ia, ib), (na, nb), (fa, fb) = sp["ID Number"], sp["Name"], sp["Fed"]
        for line in raw[1:]:
            pid = line[ia:ib].strip()
            if not pid.isdigit():
                continue
            name = line[na:nb].strip()
            by_id[pid] = name
            key = norm(name)
            index[(key, line[fa:fb].strip())].add(pid)
            index[(key, None)].add(pid)
    return by_id, index


# ------------------------------------------------------------------ pages
def cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]


def parse_page(text: str) -> dict:
    """FIDE's calculation page: per tournament its fields and games, the opponent's name kept for identification only."""
    total = re.search(r"Total change:&nbsp;<b>([^<]*)</b>", text)
    out = []
    for b in re.split(r'<div class="rtng_line01"><a href=/report\.phtml\?event=', text)[1:]:
        event = int(re.match(r"(\d+)", b).group(1))
        dates = re.findall(r'<span class="dates_span">([0-9-]+)</span>', b)
        summary, games = None, []
        for r in re.findall(r"(<tr[^>]*>.*?</tr>)", b, re.S):
            c = cells(r)
            if "bgcolor=#e6e6e6" in r and len(c) >= 10:
                summary = c
            elif ("white_note" in r or "black_note" in r) and len(c) >= 10:
                games.append({"mark": "white" if "white_note" in r else "black", "name": c[0], "title": c[1],
                              "rating": int(c[3].replace("*", "").strip()), "capped": "*" in c[3], "fed": c[4],
                              "score": SCORE[c[5]], "chg": Decimal(c[7]), "k": int(c[8]), "k_chg": Decimal(c[9])})
        if summary is None:
            raise ValueError(f"event {event}: no summary row")
        out.append({"event": event, "start": dates[0] if dates else None, "end": dates[1] if len(dates) > 1 else None,
                    "rc": int(summary[0]), "ro": int(summary[1]), "w": Decimal(summary[5]), "n": int(summary[6]),
                    "chg": Decimal(summary[7]), "k": int(summary[8]), "k_chg": Decimal(summary[9]), "games": games})
    return {"total": Decimal(total.group(1).strip()) if total and total.group(1).strip() else None, "tournaments": out}


# ------------------------------------------------------------------ broadcasts
def load_broadcasts() -> list[tuple]:
    """(date, white id, black id, white name, black name, result) of every standard or unclassified broadcast game."""
    rows = []
    for f in sorted(BROADCAST.glob("*.tsv")):
        if f.stem > "2026-09":
            continue
        with f.open(encoding="utf-8") as fh:
            cols = fh.readline().rstrip("\n").split("\t")
            ix = {c: i for i, c in enumerate(cols)}
            for line in fh:
                v = line.rstrip("\n").split("\t")
                if len(v) < len(cols) or v[ix["variant"]] not in ("", "Standard"):
                    continue
                if e2.classify(v[ix["time_control"]], v[ix["clk_white"]], v[ix["clk_black"]]) not in ("standard", None):
                    continue
                d = e2.to_date(v[ix["date"]]) or e2.to_date(v[ix["utc_date"]])
                if d is None or v[ix["result"]] not in ("1-0", "0-1", "1/2-1/2"):
                    continue
                rows.append((d, v[ix["white_fide_id"]], v[ix["black_fide_id"]], norm(v[ix["white"]]),
                             norm(v[ix["black"]]), v[ix["result"]]))
    return rows


# ------------------------------------------------------------------ helpers
def d_of(s: str) -> date:
    return date.fromisoformat(s)


def month_of(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def list_used(start: str | None, rated_on: str) -> str:
    """The list whose ratings a tournament uses: the one in force at its start (SPEC-L0 R-11a), at most the list
    before the one that rates it."""
    prev = layer0.month_add(rated_on, -1)
    if not start:
        return prev
    m = month_of(d_of(start))
    return m if m <= prev else prev


def list_for_ro(lists: dict, pid: str, ro: int, start: str | None, rated_on: str) -> str:
    """The list whose ratings FIDE used for a tournament: the list in force at its start, or, where the player's rating
    there is not FIDE's Ro (a tournament longer than 30 days uses the rating when each game was played, SPEC-L0 R-11a),
    the latest later list before the one rating it on which the player is rated Ro; if none, the list in force at the
    start (FIDE corrected the base, R-11b)."""
    m = list_used(start, rated_on)
    if pid in lists.get(m, {}) and lists[m][pid][0] == ro:
        return m
    q = layer0.month_add(rated_on, -1)
    while q > m:
        if pid in lists.get(q, {}) and lists[q][pid][0] == ro:
            return q
        q = layer0.month_add(q, -1)
    return m


def resolve(game: dict, own: int, lst: dict, index: dict) -> str | None:
    """The opponent's FIDE ID from the name FIDE prints, against every list's names (the name's key, with the
    federation FIDE prints, else with any federation), kept only if consistent with the rating FIDE used on the list
    the tournament used: equal to it, or, where FIDE marks the 400-point rule, more than 400 points from the player's
    own rating on the same side (or equal to it: FIDE once marks a rating that is not beyond 400, section 2 of E17). A
    unique consistent candidate is the opponent; otherwise none."""
    key = norm(game["name"])
    shown = game["rating"]

    def consistent(i: str) -> bool:
        if i not in lst:
            return False
        r = lst[i][0]
        if not game["capped"]:
            return r == shown
        return r == shown or ((r < own - 400) if shown < own else (r > own + 400))
    for k in ((key, game["fed"]), (key, None)):
        ids = [i for i in index.get(k, ()) if consistent(i)]
        if len(ids) == 1:
            return ids[0]
        if len(ids) > 1:
            return None
    return None


def match_colour(pid: str, pname: str, opp: str | None, oname: str, score: Decimal, start: str | None,
                 end: str | None, bc_by_day: dict) -> str | None:
    """White or Black from a unique broadcast game: the two players (FIDE ID, or the normalised name where the
    broadcast has no ID), a date within the tournament's dates with a day's tolerance, the same result."""
    if not start:
        return None
    a, b = d_of(start) - timedelta(days=1), d_of(end or start) + timedelta(days=1)
    found = set()
    day = a
    while day <= b:
        for (wid, bid, wn, bn, res) in bc_by_day.get(day, ()):
            p_white = wid == pid or (not wid and wn == pname)
            p_black = bid == pid or (not bid and bn == pname)
            o_white = (opp is not None and wid == opp) or ((not wid or opp is None) and wn == oname)
            o_black = (opp is not None and bid == opp) or ((not bid or opp is None) and bn == oname)
            if p_white and o_black:
                s = {"1-0": Decimal(1), "0-1": Decimal(0), "1/2-1/2": Decimal("0.5")}[res]
                if s == score:
                    found.add(("white", day, wid, bid, res))
            elif p_black and o_white:
                s = {"1-0": Decimal(0), "0-1": Decimal(1), "1/2-1/2": Decimal("0.5")}[res]
                if s == score:
                    found.add(("black", day, wid, bid, res))
        day += timedelta(days=1)
    days, colours = {f[1] for f in found}, {f[0] for f in found}
    return colours.pop() if len(days) == 1 and len(colours) == 1 else None      # duplicates of one game agree


def diff(r2: dict, l0: dict, p: str, m: str) -> int:
    """A player's rung-2 difference on list m: the rung-2 replay minus the Layer 0 replay, nil before the replay starts."""
    return r2[p][m] - l0[p][m] if m >= START else 0


def e_rung2(own: int, opp: int, w: int) -> Decimal:
    """Rung 2's expectation for `own` against `opp`: the published v2 entry at the game's level band and the effective
    gap (w = +1 White, -1 Black, 0 no colour term), with the narrowed guard on these two ratings."""
    x = own - opp + w * ETA
    mid = t2.band_mid((own + opp) // 2)
    e = t2.published(x, mid, PAR)
    if GUARD_APPLIES:
        e, _ = gv2.guard_own(e, x, own > opp, gv2.weight(own, opp))
    return e


# ------------------------------------------------------------------ the replay
VARIANTS = ("r2", "r2nc", "r2fide")     # rung 2 with matched colours (the method), without colour, with FIDE's marks
GAP_BANDS = ((-10000, -100, "below −100"), (-100, 0, "−100 to −1"), (0, 100, "0 to 99"), (100, 200, "100 to 199"),
             (200, 300, "200 to 299"), (300, 400, "300 to 399"), (400, 10000, "400 or more"))


def gap_band(gap: int) -> str:
    """The band of a game's gap: the player's rating minus the opponent's, as FIDE used them."""
    return next(lab for lo, hi, lab in GAP_BANDS if lo <= gap < hi)


def replay(lists, ids, pages, names, index, bc_by_day) -> dict:
    top = set(ids)
    top_names = {p: names.get(p, "") for p in ids}
    pnorm = {p: norm(top_names[p]) for p in ids}
    L0 = {p: {START: lists[START][p][0]} for p in ids}
    R2 = {v: {p: {START: lists[START][p][0]} for p in ids} for v in VARIANTS}
    val = {"games": 0, "game_delta_differs": [], "tournaments": 0, "tournament_k_chg_differs": [], "k_differs": [],
           "periods": 0, "period_change_differs": [], "carried_differs": [], "missing_pages": [],
           "change_without_games": [], "total_shown_differs": [], "capped_unresolved": 0, "opp_unresolved": 0,
           "negative_half_periods": [], "several_beyond_400": defaultdict(Counter), "cap_marks": 0, "mark_not_at_400": []}
    colour = Counter()
    per_year_colour = defaultdict(Counter)
    stats = {p: Counter() for p in ids}
    gaps = {p: [] for p in ids}
    by_gap = defaultdict(lambda: {"games": 0, "e_gap": Decimal(0), "k_e_gap": Decimal(0)})
    by_opp = defaultdict(lambda: {"games": 0, "e_gap": Decimal(0), "k_e_gap": Decimal(0)})
    for t in MONTHS[1:]:
        prev = layer0.month_add(t, -1)
        for p in ids:
            cur = lists[t].get(p)
            pub_prev, pub_t = lists[prev][p][0], cur[0]
            games_t = cur[1]
            page = pages.get((p, t))
            if games_t and page is None:
                val["missing_pages"].append((p, t))
            if not games_t or page is None:
                L0[p][t] = L0[p][prev]
                for v in VARIANTS:
                    R2[v][p][t] = R2[v][p][prev]
                if pub_t != pub_prev and not games_t:
                    val["change_without_games"].append((p, t, pub_t - pub_prev))
                if L0[p][t] != pub_t:
                    val["carried_differs"].append((p, t, pub_t, L0[p][t]))
                continue
            val["periods"] += 1
            n_game_mismatch = len(val["game_delta_differs"])
            k_list = layer0.k_for_period(lists[prev][p][2], games_t)
            sum0 = Decimal(0)
            per_t0 = []
            sums = {v: Decimal(0) for v in VARIANTS}
            for tr in page["tournaments"]:
                val["tournaments"] += 1
                start = d_of(tr["start"]) if tr["start"] else date.fromisoformat(f"{prev}-01")
                m = list_for_ro(lists, p, tr["ro"], tr["start"], t)
                if tr["k"] != k_list:
                    k_start = layer0.k_for_period(lists[m][p][2], games_t) if p in lists[m] else None
                    val["k_differs"].append((p, t, tr["event"], tr["k"], k_list, m, k_start,
                                             f"the K of the list in force at the tournament's start ({m})"
                                             if k_start == tr["k"] and m != prev else "unexplained"))
                opp_actual, opp_l0, opp_ids = [], [], []
                for g in tr["games"]:
                    oid = resolve(g, tr["ro"], lists[m], index)
                    if oid is None:
                        val["opp_unresolved"] += 1
                    actual = l0_rating = g["rating"]
                    val["cap_marks"] += g["capped"]
                    if g["capped"] and abs(tr["ro"] - g["rating"]) != 400:
                        # FIDE's mark on a rating that is not 400 points from Ro: no cap was applied (the gap is not
                        # beyond 400), and the rating shown is the one FIDE used; counted.
                        val["mark_not_at_400"].append((p, t, tr["event"], tr["ro"] - g["rating"], str(g["chg"]),
                                                       oid is not None and lists[m][oid][0] == g["rating"]))
                    elif g["capped"]:
                        if oid is not None:
                            actual = l0_rating = lists[m][oid][0]
                        else:
                            # The actual rating is hidden: FIDE prints the capped value. For Layer 0 the game is taken as
                            # beyond the cap and, under the 2022 rule, as the one that keeps the upgrade (FIDE's choice);
                            # rung 2 reads the capped value, the closest consistent rating, and the case is counted.
                            val["capped_unresolved"] += 1
                            l0_rating = g["rating"] + (-1000 if g["rating"] < tr["ro"] else 1000)
                    opp_actual.append(actual)
                    opp_l0.append(l0_rating)
                    opp_ids.append(oid)
                d0 = lh.deltas(tr["ro"], list(zip(opp_l0, [g["score"] for g in tr["games"]])), start)
                # How FIDE applied the 400-point rule where a favourite has two or more differences beyond 400 (the
                # 2022 clause; and the reading of 1 March 2024 to 30 September 2025): which games FIDE marked capped.
                ups = [(tr["ro"] - r, g["capped"]) for g, r, oid in zip(tr["games"], opp_actual, opp_ids)
                       if tr["ro"] - r > 400 and (oid is not None or not g["capped"])]
                n_beyond = sum(1 for r in opp_l0 if tr["ro"] - r > 400)
                if n_beyond >= 2 and len(ups) < n_beyond:            # a capped opponent unidentified: left out
                    ver = lh.version(start)
                    if ver == "2025-10":
                        ver += ", from 2650" if tr["ro"] >= 2650 else ", below 2650"
                    val["several_beyond_400"][ver]["left out: an opponent unidentified"] += 1
                if len(ups) >= 2 and len(ups) == n_beyond:
                    marks = [c for _gap, c in ups]
                    greatest = max(range(len(ups)), key=lambda i: (ups[i][0], -i))
                    kind = ("none" if not any(marks) else "all" if all(marks) else
                            "one, the greatest" if sum(marks) == 1 and marks[greatest] else
                            "one, not the greatest" if sum(marks) == 1 else "some")
                    ver = lh.version(start)
                    if ver == "2025-10":
                        ver += ", from 2650" if tr["ro"] >= 2650 else ", below 2650"
                    val["several_beyond_400"][ver][kind] += 1
                kt = Decimal(tr["k"])
                tsum0 = Decimal(0)
                fav_marks = sum(1 for g in tr["games"] if g["capped"] and g["rating"] < tr["ro"])
                for g, dlt, actual in zip(tr["games"], d0, opp_actual):
                    val["games"] += 1
                    if dlt != g["chg"]:
                        cause = (f"FIDE marked {fav_marks} of the favourite's games capped in the tournament; the 2022 "
                                 "text allows one upgrade" if lh.version(start) == "2022" and fav_marks >= 2 else
                                 "unexplained")
                        val["game_delta_differs"].append((p, t, tr["event"], str(g["chg"]), str(dlt), g["capped"],
                                                          tr["ro"] - actual, lh.version(start), cause))
                    tsum0 += dlt
                if kt * tsum0 != tr["k_chg"]:
                    val["tournament_k_chg_differs"].append((p, t, tr["event"], str(tr["k_chg"]), str(kt * tsum0)))
                sum0 += kt * tsum0
                per_t0.append(kt * tsum0)
                # rung 2, the three variants, and the per-player descriptive figures
                for g, oid, actual, dlt in zip(tr["games"], opp_ids, opp_actual, d0):
                    w_fide = 1 if g["mark"] == "white" else -1
                    c = match_colour(p, pnorm[p], oid, norm(g["name"]), g["score"], tr["start"], tr["end"], bc_by_day)
                    w_match = 0 if c is None else (1 if c == "white" else -1)
                    yr = t[:4]
                    colour["games"] += 1
                    per_year_colour[yr]["games"] += 1
                    if c is not None:
                        colour["matched"] += 1
                        per_year_colour[yr]["matched"] += 1
                        colour["agree_fide_mark" if w_match == w_fide else "disagree_fide_mark"] += 1
                        stats[p]["white" if w_match > 0 else "black"] += 1
                    stats[p]["games"] += 1
                    stats[p]["fav"] += tr["ro"] > actual
                    gaps[p].append(tr["ro"] - actual)
                    for v, w in (("r2", w_match), ("r2nc", 0), ("r2fide", w_fide)):
                        own2 = tr["ro"] + diff(R2[v], L0, p, m)
                        opp2 = actual + (diff(R2[v], L0, oid, m) if oid in top else 0)
                        e2 = e_rung2(own2, opp2, w)
                        sums[v] += kt * (g["score"] - e2)
                        if v == "r2nc":     # where the table's effect comes from: FIDE's expectation minus rung 2's
                            for b in (by_gap[gap_band(tr["ro"] - actual)],
                                      by_opp["in the 100" if oid in top else "outside the 100"]):
                                b["games"] += 1
                                b["e_gap"] += (g["score"] - dlt) - e2
                                b["k_e_gap"] += kt * ((g["score"] - dlt) - e2)
            ch0 = lh.round_change(sum0, t)
            ch0_tourn = sum(lh.round_change(x, t) for x in per_t0)
            if sum0 < 0 and abs(sum0) % 1 == Decimal("0.5"):          # the rounding of a negative half-point
                val["negative_half_periods"].append((p, t, pub_t - pub_prev, ch0, lh.round_change_literal_2017(sum0),
                                                     t < lh.ROUNDING_2022_LIST))
            if page["total"] is not None and page["total"] != sum0:
                val["total_shown_differs"].append((p, t, str(page["total"]), str(sum0)))
            if pub_prev + ch0 != pub_t:
                pc = pub_t - pub_prev
                shown = lh.round_change(page["total"], t) if page["total"] is not None else None
                if ch0_tourn == pc:
                    cause = "rounded per tournament, not once per period"
                elif shown is not None and shown != pc and sum0 == page["total"]:
                    cause = "the list differs from FIDE's own published calculation of the period"
                elif len(val["game_delta_differs"]) > n_game_mismatch:
                    cause = "FIDE applied the 400-point rule otherwise in a game of the period"
                else:
                    cause = "unexplained"
                val["period_change_differs"].append((p, t, pc, ch0, ch0_tourn, str(sum0), str(page["total"]), cause))
            L0[p][t] = L0[p][prev] + ch0
            if L0[p][t] != pub_t:
                val["carried_differs"].append((p, t, pub_t, L0[p][t]))
            for v in VARIANTS:
                R2[v][p][t] = R2[v][p][prev] + lh.round_change(sums[v], t)
    return {"L0": L0, "R2": R2, "val": val, "colour": colour, "per_year_colour": per_year_colour, "stats": stats,
            "gaps": gaps, "by_gap": by_gap, "by_opp": by_opp}


# ------------------------------------------------------------------ summaries
def year_ends() -> list[str]:
    return [m for m in MONTHS if m.endswith("-12")] + [LAST]


def summarise(lists, ids, res) -> dict:
    L0, R2, val = res["L0"], res["R2"], res["val"]
    pub = {p: {m: lists[m][p][0] for m in MONTHS} for p in ids}
    out_players = []
    for p in ids:
        d = {v: R2[v][p][LAST] - L0[p][LAST] for v in VARIANTS}
        st, g = res["stats"][p], res["gaps"][p]
        out_players.append({
            "fide_id": int(p), "oct_2026": pub[p][LAST],
            "layer0_replay": L0[p][LAST], "rung2": pub[p][LAST] + d["r2"], "difference": d["r2"],
            "table_effect": d["r2nc"], "colour_effect": d["r2"] - d["r2nc"], "difference_fide_marks": d["r2fide"],
            "games": st["games"], "favourite_share": round(st["fav"] / st["games"], 3) if st["games"] else None,
            "mean_gap": round(sum(g) / len(g), 1) if g else None,
            "colour_balance": st["white"] - st["black"], "colour_matched": st["white"] + st["black"],
            "cumulative": {m: R2["r2"][p][m] - L0[p][m] for m in year_ends()}})
    rank_pub = {r["fide_id"]: i + 1 for i, r in enumerate(sorted(out_players, key=lambda r: (-r["oct_2026"], r["fide_id"])))}
    rank_r2 = {r["fide_id"]: i + 1 for i, r in enumerate(sorted(out_players, key=lambda r: (-r["rung2"], r["fide_id"])))}
    for r in out_players:
        r["rank_oct_2026"], r["rank_rung2"] = rank_pub[r["fide_id"]], rank_r2[r["fide_id"]]
    counts = {}
    for m in MONTHS:
        row = {}
        for lab, series in (("published", {p: pub[p][m] for p in ids}), ("layer0", {p: L0[p][m] for p in ids}),
                            ("rung2", {p: pub[p][m] + R2["r2"][p][m] - L0[p][m] for p in ids}),
                            ("rung2_no_colour", {p: pub[p][m] + R2["r2nc"][p][m] - L0[p][m] for p in ids})):
            row[lab] = {"2700": sum(1 for v in series.values() if v >= 2700), "2800": sum(1 for v in series.values() if v >= 2800)}
        row["mean_difference"] = round(sum(R2["r2"][p][m] - L0[p][m] for p in ids) / len(ids), 2)
        row["mean_table_effect"] = round(sum(R2["r2nc"][p][m] - L0[p][m] for p in ids) / len(ids), 2)
        counts[m] = row
    years = {}
    ends = [START] + year_ends()
    for a, b in zip(ends, ends[1:]):
        tab = [(R2["r2nc"][p][b] - L0[p][b]) - (R2["r2nc"][p][a] - L0[p][a]) for p in ids]
        col = [(R2["r2"][p][b] - R2["r2nc"][p][b]) - (R2["r2"][p][a] - R2["r2nc"][p][a]) for p in ids]
        years[b[:4]] = {"from": a, "to": b, "mean_table_effect": round(sum(tab) / len(tab), 2),
                        "mean_colour_effect": round(sum(col) / len(col), 2),
                        "players_table_up": sum(1 for x in tab if x > 0), "players_table_down": sum(1 for x in tab if x < 0)}
    carried = defaultdict(list)
    for (p, t, pb, l0) in val["carried_differs"]:
        carried[p].append(t)
    runs = {}
    for p in carried:                       # the runs of lists on which the carried replay is off by one same amount
        rr = []
        for m in MONTHS[1:]:
            off = L0[p][m] - pub[p][m]
            if off and rr and rr[-1]["offset"] == off and rr[-1]["to"] == layer0.month_add(m, -1):
                rr[-1]["to"] = m
            elif off:
                rr.append({"from": m, "to": m, "offset": off})
        runs[p] = rr
    carried_out = {"players_exact_on_every_list": len(ids) - len(carried),
                   "players": {p: {"first_list": ts[0], "lists": len(ts), "oct_2026_offset": L0[p][LAST] - pub[p][LAST],
                                   "runs": runs[p]}
                               for p, ts in sorted(carried.items())}}
    recent = ft.months(layer0.month_add(LAST, -11), LAST)
    active_e5 = sum(1 for p in ids if any(lists[m][p][1] > 0 for m in recent))
    return {
        "carried": carried_out,
        "spec": "docs/specs/SPEC-TOP100_v1_0.md", "window": {"start_list": START, "first": FIRST, "last": LAST},
        "players": len(ids), "rank_100_rating": min(pub[p][LAST] for p in ids), "active_e5": active_e5,
        "fit_window_from": FIT_FROM, "eta": ETA, "guard_applies": GUARD_APPLIES,
        "validation": {k: (val[k] if isinstance(val[k], int) else len(val[k]) if isinstance(val[k], list) else
                           {kk: dict(vv) for kk, vv in sorted(val[k].items())}) for k in val},
        # the details of every mismatch; for the carried replay only the offset, so that no player's monthly series of
        # published ratings is committed (SPEC-TOP100 §8)
        "validation_detail": {k: ([[p, t, str(l0 - pb)] for (p, t, pb, l0) in val[k]] if k == "carried_differs" else
                                  [list(map(str, x)) for x in val[k]]) for k in val if isinstance(val[k], list)},
        "colour": dict(res["colour"]), "colour_by_year": {y: dict(c) for y, c in sorted(res["per_year_colour"].items())},
        "players_table": out_players, "by_list": counts, "by_year": years,
        "by_gap": {lab: effect_source(res["by_gap"][lab], len(ids)) for _lo, _hi, lab in GAP_BANDS},
        "by_opponent": {lab: effect_source(res["by_opp"][lab], len(ids)) for lab in ("in the 100", "outside the 100")}}


def effect_source(b: dict, n: int) -> dict:
    """Games, the mean of FIDE's expectation minus rung 2's (no colour), and K times it summed, per player."""
    return {"games": b["games"],
            "mean_expectation_gap": round(float(b["e_gap"] / b["games"]), 4) + 0.0 if b["games"] else None,  # no -0.0
            "points_per_player": round(float(b["k_e_gap"]) / n, 2) + 0.0}


def main() -> int:
    lists = load_lists()
    ids = ft.top100()
    plan = set(ft.plan())
    pages = {}
    for pair in sorted(plan):
        pid, period = pair.split(":")
        f = PAGES / f"{pid}_{period}.html"
        if f.exists():
            pages[(pid, period)] = parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
    names, index = load_names()
    bc_by_day = defaultdict(list)
    for (d, wid, bid, wn, bn, res) in load_broadcasts():
        bc_by_day[d].append((wid, bid, wn, bn, res))
    res = replay(lists, ids, pages, names, index, bc_by_day)
    out = summarise(lists, ids, res)
    out["pages"] = {"planned": len(plan), "read": len(pages)}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    if "--feed" in sys.argv:
        path = Path(sys.argv[sys.argv.index("--feed") + 1]).expanduser()
        write_feed(path, lists, ids, names, res)
    return 0


def write_feed(path: Path, lists, ids, names, res) -> None:
    """The operator's monthly series, outside the repository: both systems' ratings for every player and list."""
    L0, R2 = res["L0"], res["R2"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["list", "fide_id", "name", "federation", "FIDE_official", "Layer0_replay", "Layer0_matches_official",
                    "Zugzwang_table", "Zugzwang_table_no_colour", "rank_official_in_100", "rank_zugzwang_in_100"])
        for m in MONTHS:
            pub = {p: lists[m][p][0] for p in ids}
            z = {p: pub[p] + R2["r2"][p][m] - L0[p][m] for p in ids}
            znc = {p: pub[p] + R2["r2nc"][p][m] - L0[p][m] for p in ids}
            rp = {p: i + 1 for i, p in enumerate(sorted(ids, key=lambda q: (-pub[q], int(q))))}
            rz = {p: i + 1 for i, p in enumerate(sorted(ids, key=lambda q: (-z[q], int(q))))}
            for p in sorted(ids, key=lambda q: rp[q]):
                w.writerow([m, p, names.get(p, ""), lists[m][p][3], pub[p], L0[p][m], L0[p][m] == pub[p], z[p], znc[p],
                            rp[p], rz[p]])


if __name__ == "__main__":
    sys.exit(main())
