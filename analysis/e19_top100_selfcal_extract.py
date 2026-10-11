#!/usr/bin/env python3
"""E19 extraction: today's top 100 replayed under FIDE's rules and under the self-calibrating system (SPEC-SELFCAL v1.0
§9, §10; session ELO-8, Phase 4; needs data/).

The same 100 players, games, pages and validation as E17 (analysis/e17_top100_extract.py, whose replay is run unchanged
for Layer 0 and the validation), and a second replay in which rung 2 is self-calibrating: each tournament uses the table
of the year of the list in force at its start, from E18 (analysis/aggregates/E18_selfcal.json), with eta(L) whole in
each band, the published entry to three decimals and the narrowed guard as frozen; before the first table (2025), table
8.1.2 as FIDE applies it, so that the two systems agree until then. K follows FIDE's K rules applied to each system's own
rating (R61): the rule (SPEC-L0 R-18 to R-22, layer0.published_k) is first checked on FIDE's own ratings against FIDE's
printed K, and the self-calibrating K is the rule on the self-calibrating rating where the check holds, FIDE's K where it
does not. Variants of the self-calibrating replay: the method (colours matched from the broadcast archive); without the
colour term; every opponent outside the 100 rated 10 and 5 points lower and higher from the first table on (R58); each
year's table corrected, at levels of 2300 or more, by its favourite's residual by level band on that year's games (E18
§3; R59's bound). Writes analysis/aggregates/E19_top100_selfcal.json: the per-player figures SPEC-SELFCAL §10 defines,
with names (R60) and each player's rating on every list under both systems (the operator's addendum of 11 October 2026),
and aggregates; no year of birth and no page. Python standard library only.

Usage: python3 analysis/e19_top100_selfcal_extract.py > analysis/aggregates/E19_top100_selfcal.json
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "data"))
sys.path.insert(0, str(ROOT / "src"))
import e17_top100_extract as ex  # noqa: E402  (E17's lists, pages, names, broadcasts and replay, unchanged)
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402
import selfcal_fit as sf  # noqa: E402
from layer2 import guard_v2 as gv2  # noqa: E402

E18 = json.loads((ROOT / "analysis" / "aggregates" / "E18_selfcal.json").read_text(encoding="utf-8"))
TABLES = {int(y): {"form": t["form"], "par": t["par"]} for y, t in E18["tables"].items()}
FIRST_TABLE = min(TABLES)
RESID = {int(y): {int(mid): b["mean"] for mid, b in r["bands"]["year"].items() if int(mid) >= 2350}
         for y, r in E18["three_way"].items()}           # R59: the favourite's residual by band, levels of 2300 or more
RESID_CELLS = {int(y): {(int(c["cell"].split("|")[0]), int(c["cell"].split("|")[1])): c["mean"]
                        for c in r["cells"]["year"]["shown"] if int(c["cell"].split("|")[0]) >= 2350}
               for y, r in E18["three_way"].items()}     # the same by band and 50-point gap, cells of 200 games or more
GAP_BINS = ex.e2.BINS
SHIFTS = ex.SHIFTS
VARIANTS = ("sc", "sc_nc", "sc_bound", "sc_bound_cells") + tuple(f"sc_outside{s:+d}" for s in SHIFTS)
START, LAST, MONTHS = ex.START, ex.LAST, ex.MONTHS
HISTORY = ex.ft.months("2015-02", LAST)                 # FIDE's lists on disk, for "ever 2300 / 2400" before 2020


def load_birth_and_history(ids: list[str]) -> tuple[dict[str, int | None], dict[str, dict[str, int]]]:
    """Each player's year of birth (the latest list that gives it) and published rating on every list since 2015-02."""
    birth: dict[str, int | None] = {p: None for p in ids}
    hist: dict[str, dict[str, int]] = {p: {} for p in ids}
    want = set(ids)
    for m in HISTORY:
        f = ex.LISTS / f"{m}.tsv"
        if not f.exists():
            continue
        with f.open(encoding="utf-8") as fh:
            rows = csv.reader(fh, delimiter="\t")
            next(rows)
            for pid, rating, _games, _k, by, *_rest in rows:
                if pid in want and rating.isdigit():
                    hist[pid][m] = int(rating)
                    if by.isdigit() and int(by) > 1900:
                        birth[pid] = int(by)
    return birth, hist


def k_rule(rating: int, list_month: str, ever2400: bool, ever2300: bool, birth: int | None) -> int:
    """FIDE's K rules in the order SPEC-L0 R-22 settles (layer0.published_k), for a player with 30 games or more."""
    return layer0.published_k(rating, 30, ever2400, ever2300, list_month, birth)


def sc_expectation(tab: dict, own: int, opp: int, w: int, resid: dict[int, float] | None = None,
                   cells: dict[tuple[int, int], float] | None = None) -> Decimal:
    """The self-calibrating table's published entry for `own` against `opp` (colour w = +1, -1 or 0), with R59's
    correction where given (by level band, or by band and 50-point gap where a cell has 200 games, the band's value
    elsewhere), and the narrowed guard on these two ratings."""
    mid = ex.t2.band_mid((own + opp) // 2)
    x = own - opp + w * sf.eta_whole(tab, mid)
    e = sf.published(tab, x, mid)
    if resid is not None and own != opp and mid in resid:
        gap_bin = min(abs(own - opp) // 50, GAP_BINS - 1) * 50
        rv = cells.get((mid, gap_bin), resid[mid]) if cells is not None else resid[mid]
        r = Decimal(repr(rv)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        e = min(max(e + (r if own > opp else -r), Decimal(0)), Decimal(1))
    if ex.GUARD_APPLIES:
        e, _ = gv2.guard_own(e, x, own > opp, gv2.weight(own, opp))
    return e


def main() -> int:
    lists = ex.load_lists()
    ids = ex.ft.top100()
    top = set(ids)
    plan = set(ex.ft.plan())
    pages = {}
    for pair in sorted(plan):
        pid, period = pair.split(":")
        f = ex.PAGES / f"{pid}_{period}.html"
        if f.exists():
            pages[(pid, period)] = ex.parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
    names, index = ex.load_names()
    bc_by_day = defaultdict(list)
    for (d, wid, bid, wn, bn, res) in ex.load_broadcasts():
        bc_by_day[d].append((wid, bid, wn, bn, res))
    e17 = ex.replay(lists, ids, pages, names, index, bc_by_day)        # Layer 0 and the validation, as E17
    agg17 = json.loads((ROOT / "analysis" / "aggregates" / "E17_top100.json").read_text(encoding="utf-8"))
    val = ex.summarise(lists, ids, e17)["validation"]
    assert val == agg17["validation"], "Layer 0's replay is not E17's"
    L0 = e17["L0"]
    birth, hist = load_birth_and_history(ids)
    pnorm = {p: ex.norm(names.get(p, "")) for p in ids}

    # R61: FIDE's K rules checked on FIDE's ratings, then applied to the self-calibrating ones
    def ever(series: dict[str, int], upto: str, level: int) -> bool:
        return any(r >= level for m, r in series.items() if m <= upto)

    k_check = {"player_lists": 0, "reproduced": 0, "differs": []}
    k_ok: dict[tuple[str, str], bool] = {}
    for p in ids:
        for m in MONTHS:
            if p not in lists[m]:
                continue
            kf = lists[m][p][2]
            kr = k_rule(lists[m][p][0], m, ever(hist[p], m, 2400), ever(hist[p], m, 2300), birth[p])
            k_check["player_lists"] += 1
            k_ok[(p, m)] = kr == kf
            if kr == kf:
                k_check["reproduced"] += 1
            else:
                k_check["differs"].append([p, m, kf, kr])
    SC = {v: {p: {START: lists[START][p][0]} for p in ids} for v in VARIANTS}

    def sc_rating(v: str, p: str, m: str) -> int:
        return lists[m][p][0] + SC[v][p][m] - L0[p][m] if m >= START else lists[m][p][0]

    def k_sc(v: str, p: str, m: str) -> int:
        """The self-calibrating K published on list m (R61): the rule on the self-calibrating rating where the rule
        reproduces FIDE's K on m, FIDE's K otherwise."""
        kf = lists[m][p][2]
        if not k_ok.get((p, m)):
            return kf
        series = {mm: r for mm, r in hist[p].items() if mm < START}
        series.update({mm: sc_rating(v, p, mm) for mm in MONTHS if mm <= m and p in lists[mm]})
        return k_rule(sc_rating(v, p, m), m, ever(series, m, 2400), ever(series, m, 2300), birth[p])

    k_departs = Counter()
    stats = {p: Counter() for p in ids}
    by_opp = defaultdict(lambda: {"games": 0, "points": Decimal(0)})
    for t in MONTHS[1:]:
        prev = layer0.month_add(t, -1)
        for p in ids:
            cur = lists[t].get(p)
            games_t = cur[1]
            page = pages.get((p, t))
            if not games_t or page is None:
                for v in VARIANTS:
                    SC[v][p][t] = SC[v][p][prev]
                continue
            sums = {v: Decimal(0) for v in VARIANTS}
            for tr in page["tournaments"]:
                start = ex.d_of(tr["start"]) if tr["start"] else date.fromisoformat(f"{prev}-01")
                m = ex.list_for_ro(lists, p, tr["ro"], tr["start"], t)
                tab = TABLES.get(int(m[:4]))
                opp_actual, opp_l0, opp_ids = [], [], []
                for g in tr["games"]:                 # the opponents exactly as E17's replay reads them
                    oid = ex.resolve(g, tr["ro"], lists[m], index)
                    actual = l0_rating = g["rating"]
                    if g["capped"] and abs(tr["ro"] - g["rating"]) == 400:
                        if oid is not None:
                            actual = l0_rating = lists[m][oid][0]
                        else:
                            l0_rating = g["rating"] + (-1000 if g["rating"] < tr["ro"] else 1000)
                    opp_actual.append(actual)
                    opp_l0.append(l0_rating)
                    opp_ids.append(oid)
                colours = [ex.match_colour(p, pnorm[p], oid, ex.norm(g["name"]), g["score"], tr["start"], tr["end"],
                                           bc_by_day) for g, oid in zip(tr["games"], opp_ids)]
                kf_list = layer0.k_for_period(lists[prev][p][2], games_t)
                kf_start = layer0.k_for_period(lists[m][p][2], games_t) if p in lists[m] else None
                for v in VARIANTS:
                    if tr["k"] == kf_list:
                        kv = layer0.k_for_period(k_sc(v, p, prev), games_t)
                    elif tr["k"] == kf_start:
                        kv = layer0.k_for_period(k_sc(v, p, m), games_t)
                    else:
                        kv = tr["k"]
                    if kv != tr["k"]:
                        k_departs[v] += 1
                    own2 = tr["ro"] + ex.diff(SC[v], L0, p, m)
                    if tab is None:                   # before the first table: FIDE's rules on the system's ratings
                        opps2 = [r + (ex.diff(SC[v], L0, oid, m) if oid in top else 0) for r, oid in zip(opp_l0, opp_ids)]
                        ds = lh.deltas(own2, list(zip(opps2, [g["score"] for g in tr["games"]])), start)
                        sums[v] += Decimal(kv) * sum(ds, Decimal(0))
                        continue
                    shift = int(v[len("sc_outside"):]) if v.startswith("sc_outside") else 0
                    tot = Decimal(0)
                    for g, oid, actual, c in zip(tr["games"], opp_ids, opp_actual, colours):
                        w = 0 if (c is None or v == "sc_nc") else (1 if c == "white" else -1)
                        opp2 = actual + (ex.diff(SC[v], L0, oid, m) if oid in top else shift)
                        yr = int(m[:4])
                        e = sc_expectation(tab, own2, opp2, w,
                                           RESID.get(yr) if v in ("sc_bound", "sc_bound_cells") else None,
                                           RESID_CELLS.get(yr) if v == "sc_bound_cells" else None)
                        tot += g["score"] - e
                        if v == "sc_nc":
                            # where the table's effect comes from: FIDE's expectation minus the table's, in points
                            e_fide = g["score"] - lh.deltas(tr["ro"], [(actual, g["score"])], start)[0]
                            b = by_opp["in the 100" if oid in top else "outside the 100"]
                            b["games"] += 1
                            b["points"] += Decimal(kv) * (e_fide - e)
                        if v == "sc":
                            stats[p]["games_table"] += 1
                            stats[p]["fav_table"] += tr["ro"] > actual
                    sums[v] += Decimal(kv) * tot
            for v in VARIANTS:
                SC[v][p][t] = SC[v][p][prev] + lh.round_change(sums[v], t)

    pub = {p: {m: lists[m][p][0] for m in MONTHS} for p in ids}
    d17 = {str(r["fide_id"]): r for r in agg17["players_table"]}
    players = []
    for p in ids:
        d = {v: SC[v][p][LAST] - L0[p][LAST] for v in VARIANTS}
        st = stats[p]
        players.append({
            "fide_id": int(p), "name": names.get(p, ""), "federation": lists[LAST][p][3], "oct_2026": pub[p][LAST],
            "selfcal": pub[p][LAST] + d["sc"], "difference": d["sc"], "table_effect": d["sc_nc"],
            "colour_effect": d["sc"] - d["sc_nc"], "bound_difference": d["sc_bound"],
            "e17_difference": d17[p]["difference"], "e17_rung2": d17[p]["rung2"],
            "games_under_a_table": st["games_table"],
            "favourite_share_under_a_table": round(st["fav_table"] / st["games_table"], 3) if st["games_table"] else None,
            "series": {m: [pub[p][m], pub[p][m] + SC["sc"][p][m] - L0[p][m]] for m in MONTHS}})
    rank_pub = {r["fide_id"]: i + 1 for i, r in enumerate(sorted(players, key=lambda r: (-r["oct_2026"], r["fide_id"])))}
    rank_sc = {r["fide_id"]: i + 1 for i, r in enumerate(sorted(players, key=lambda r: (-r["selfcal"], r["fide_id"])))}
    for r in players:
        r["rank_oct_2026"], r["rank_selfcal"] = rank_pub[r["fide_id"]], rank_sc[r["fide_id"]]
    by_list = {}
    for m in MONTHS:
        row = {"published": {}, "selfcal": {}}
        for lab, series in (("published", {p: pub[p][m] for p in ids}),
                            ("selfcal", {p: pub[p][m] + SC["sc"][p][m] - L0[p][m] for p in ids})):
            row[lab] = {"2700": sum(1 for x in series.values() if x >= 2700), "2800": sum(1 for x in series.values() if x >= 2800)}
        row["mean_difference"] = round(sum(SC["sc"][p][m] - L0[p][m] for p in ids) / len(ids), 2)
        row["mean_table_effect"] = round(sum(SC["sc_nc"][p][m] - L0[p][m] for p in ids) / len(ids), 2)
        by_list[m] = row
    ends = [START] + ex.year_ends()
    years = {}
    for a, b in zip(ends, ends[1:]):
        tab_ = [(SC["sc_nc"][p][b] - L0[p][b]) - (SC["sc_nc"][p][a] - L0[p][a]) for p in ids]
        col = [(SC["sc"][p][b] - SC["sc_nc"][p][b]) - (SC["sc"][p][a] - SC["sc_nc"][p][a]) for p in ids]
        years[b[:4]] = {"from": a, "to": b, "mean_table_effect": round(sum(tab_) / len(tab_), 2),
                        "mean_colour_effect": round(sum(col) / len(col), 2),
                        "players_table_up": sum(1 for x in tab_ if x > 0), "players_table_down": sum(1 for x in tab_ if x < 0)}

    def summary(v: str) -> dict:
        ds = [SC[v][p][LAST] - L0[p][LAST] for p in ids]
        return {"mean_difference": round(sum(ds) / len(ds), 2), "min": min(ds), "max": max(ds),
                "higher": sum(1 for x in ds if x > 0), "lower": sum(1 for x in ds if x < 0),
                "2700": sum(1 for p in ids if pub[p][LAST] + SC[v][p][LAST] - L0[p][LAST] >= 2700),
                "2800": sum(1 for p in ids if pub[p][LAST] + SC[v][p][LAST] - L0[p][LAST] >= 2800)}
    out = {
        "spec": "docs/specs/SPEC-SELFCAL_v1_1.md", "e18": "analysis/aggregates/E18_selfcal.json",
        "window": {"start_list": START, "last": LAST}, "first_table_year": FIRST_TABLE,
        "tables_used": sorted(TABLES), "players": len(ids), "rank_100_rating": min(pub[p][LAST] for p in ids),
        "validation": val, "validation_equals_e17": True, "guard_applies": ex.GUARD_APPLIES,
        "k_check": {"player_lists": k_check["player_lists"], "reproduced": k_check["reproduced"],
                    "differs": k_check["differs"]},
        "k_departs_from_fide": dict(k_departs),
        "method": summary("sc"), "no_colour": summary("sc_nc"), "bound": summary("sc_bound"),
        "bound_cells": summary("sc_bound_cells"),
        "bound_residuals": {str(y): {str(mid): r for mid, r in sorted(v.items())} for y, v in sorted(RESID.items())},
        "outside_shift": {str(s): summary(f"sc_outside{s:+d}") for s in SHIFTS},
        "e17_method": {"mean_difference": round(sum(r["difference"] for r in agg17["players_table"]) / len(ids), 2),
                       "2700": agg17["by_list"][LAST]["rung2"]["2700"], "2800": agg17["by_list"][LAST]["rung2"]["2800"]},
        "by_opponent": {k: {"games": b["games"], "points_per_player": round(float(b["points"]) / len(ids), 2) + 0.0}
                        for k, b in sorted(by_opp.items())},
        "players_table": players, "by_list": by_list, "by_year": years}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
