#!/usr/bin/env python3
"""E19 report: today's top 100 under FIDE's rules and under the self-calibrating system; writes
docs/evidence/E19_top100-selfcal.md from analysis/aggregates/E19_top100_selfcal.json (analysis/e19_top100_selfcal_extract.py,
needs data/, under docs/specs/SPEC-SELFCAL_v1_2.md §9 and §10). Every table carries the fixed wording; the per-player table
gives names beside FIDE IDs (R60). Session ELO-9 (D-0016): R59's two estimates, the headline sentence using the one by
level band (R71); the replay with the 2026 table in the form R68 keeps, beside the headline; the aggregate keeps each
player's difference only (R72). Python standard library only; deterministic.

Usage: python3 analysis/e19_top100_selfcal_report.py > docs/evidence/E19_top100-selfcal.md
       python3 analysis/e19_top100_selfcal_report.py --appendix > analysis/OUTPUT_E19_appendix.md (the proposal's
       Appendix H, from E18's and E19's aggregates, carried verbatim; tests/test_e19_appendix.py)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e17_top100_report as r17  # noqa: E402  (the fixed wording and its placement, E17's)

AGG = ROOT / "analysis" / "aggregates" / "E19_top100_selfcal.json"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
FIXED = r17.FIXED
sgn = r17.sgn
P: list[str] = []
p = P.append


def with_ties(rows: list[dict], n: int, key: str) -> list[dict]:
    """The first n rows of a sorted list and every row tied with the n-th on `key` (review finding ELO8-QC-4)."""
    if len(rows) <= n:
        return rows
    cut = rows[n - 1][key]
    return rows[:n] + [r for r in rows[n:] if r[key] == cut]


def band(mid: str) -> str:
    m = int(mid)
    return "below 1500" if m == 1450 else "2800 and above" if m == 2850 else f"{m - 50}–{m + 49}"


def appendix(a: dict, s: dict) -> list[str]:
    """Appendix H of the proposal: E18 and E19 in one page, every number from the two aggregates."""
    out: list[str] = []
    q = out.append
    first, years = a["first_table_year"], s["table_years"]
    t25, t26 = (s["tables"][y] for y in years[:2])
    tw = {y: s["three_way"][y]["differences"] for y in years}
    last_y = years[-1]
    d32 = tw[last_y]["year-first"]
    held = sorted(k for k in t26["on_bound"])
    mt, sh, bd, e17 = a["method"], a["outside_shift"], a["bound"], a["e17_method"]
    t812, d25, d26 = s["table_812"], t25["derived"], t26["derived"]
    rows = a["players_table"]
    bl = a["by_list"][a["window"]["last"]]
    verdict = d32["hi"] < 0 and tw[last_y]["year-l0"]["hi"] < 0 and tw[last_y]["first-l0"]["hi"] < 0
    form26 = s["choice"][last_y]["chosen"]
    q("## Appendix H Self-calibrating: one table a year, and today's top 100 under it")
    q("")
    q(FIXED)
    q("")
    q("Rung 2 as recommended is self-calibrating (R65): each year's table is refitted by SPEC-TABLE-FIT v1.2's rules on "
      "the games played before that year only, within annex T7.1's yearly caps, by a method fixed before any table was "
      "fitted (`docs/specs/SPEC-SELFCAL_v1_2.md`). Run back in time on the broadcast archive, the data allow "
      f"{WORDS.get(len(years), len(years))} tables: 2016–2019 could not be sourced legitimately, and the archive's games before 2023 carry no "
      f"FIDE IDs, so the first window is {t25['window'][0]} to {t25['window'][1]}, after the March 2024 compression "
      f"[E18 §1]. The {years[0]} table keeps v1.1's form; for {last_y} the rule of choice picked "
      + ("a piecewise-linear slope by level" if form26["slope"] == "P" else "v1.1's exponential slope")
      + (" and a colour term rising with the level" if form26["colour_by_level"] else "")
      + f", and the yearly caps held {WORDS.get(len(held), len(held))} of its parameters at their bounds [E18 §2].")
    q("")
    q(f"Forecasting each year's games, the year's table beat table 8.1.2 as FIDE applied it in every year (log-loss "
      + ", ".join(f"{sgn(tw[y]['year-l0']['mean'], 4)} in {y}" for y in years)
      + f", nats a game, intervals below zero), and in {last_y} it beat the first table kept frozen "
      f"({sgn(d32['mean'], 5)}; {sgn(d32['lo'], 5)} to {sgn(d32['hi'], 5)}): self-calibration "
      + ("earns its name" if verdict else "does not earn its name")
      + f" in {last_y}, the one year that can tell. The size is small: {abs(d32['mean']):.4f} nats a game, against "
      f"{abs(tw[last_y]['year-l0']['mean']):.3f} over table 8.1.2"
      + (f", and {abs(tw[last_y]['year_prevform-first']['mean']):.4f} in the form ruling R68 keeps (a choice of form "
         "needs 24 months of games after the last rule change; R68 applies from 2027, and the 10-month figure that "
         "allowed the 2026 choice was set after the counts were known)" if "year_prevform-first" in tw[last_y] else "")
      + f"; and with one year, against a frozen table fitted on {t25['months']} months to the year's {t26['months']}, "
      "the result is consistent with self-calibration and cannot establish it [E18 §3]. Table 8.1.2 expects a 100-point "
      "favourite at 2700 to score "
      f"{t812['favourite_100_at_2700']:.3f}; the tables, {d25['favourite_100_at_2700']['value']:.3f} and "
      f"{d26['favourite_100_at_2700']['value']:.3f}; White's edge at 2700–2799 is "
      f"{d25['white_edge_points']['2750']['value']:.0f} and {d26['white_edge_points']['2750']['value']:.0f} rating points "
      f"({t26['uncapped']['derived']['white_edge_points']['2750']:.0f} without the caps), against none in table 8.1.2 "
      "[E18 §4].")
    q("")
    q(f"Today's top 100 replayed with these tables, FIDE's rules before {first}, and K by FIDE's rules on each system's "
      "own rating (R61"
      + (", which changes no K here" if not a["k_departs_from_fide"] else "")
      + f"): in October 2026 the self-calibrating system rates them {sgn(mt['mean_difference'], 1)} points higher on "
      f"average than FIDE's rules ({sgn(mt['min'])} to {sgn(mt['max'])}); {sgn(sh['-10']['mean_difference'], 1)} to "
      f"{sgn(sh['10']['mean_difference'], 1)} with the opponents outside the 100 rated 10 points lower or higher from "
      f"{first} (R58); {sgn(bd['mean_difference'], 1)} with each table's own residual at levels of 2300 or more "
      f"removed by level band, and {sgn(a['bound_cells']['mean_difference'], 1)} by band and gap (R59's two "
      f"estimates, neither a bound, R71); {sgn(a['r68_2026']['mean_difference'], 1)} with the {last_y} table in the "
      f"form R68 keeps; {bl['selfcal']['2700']} and {bl['selfcal']['2800']} of the 100 at 2700 and 2800, against "
      f"{bl['published']['2700']} and {bl['published']['2800']} [E19]. E17's frozen table gave "
      f"{sgn(e17['mean_difference'], 1)} over 2020–2026 (Appendix G); E19 supersedes it (R59).")
    q("")
    q("The five largest differences and the five smallest, with every player tied at the cut, names beside FIDE IDs "
      "(R60):")
    q("")
    q(FIXED)
    q("")
    q("| | name | FIDE ID | FIDE's rules, October 2026 | self-calibrating | difference |")
    q("|---|---|---|---|---|---|")
    up = sorted(rows, key=lambda r: (-r["difference"], r["fide_id"]))
    down = sorted(rows, key=lambda r: (r["difference"], r["fide_id"]))
    for lab, lst in (("largest", with_ties(up, 5, "difference")), ("smallest", with_ties(down, 5, "difference"))):
        for r in lst:
            q(f"| {lab} | {r['name']} | {r['fide_id']} | {r['oct_2026']} | {r['selfcal']} | {sgn(r['difference'])} |")
    q("")
    q("Read with these caveats [E18 §5] [E19 §8]:")
    q("")
    q(f"- Two tables only, so the test of self-calibration rests on {last_y}; the replay differs from FIDE's rules over "
      f"{sum(1 for m in a['by_list'] if m >= f'{first}-01')} lists, not E17's "
      f"{sum(1 for m in a['by_list'] if m > a['window']['start_list'])}.")
    q("- Opponents outside the 100 keep their published ratings (R58's range above); a replay of the whole pool needs "
      "FIDE's tournament reports (section 9, stage 2).")
    q("- The tables' own error at the top is estimated, not removed (R59's two estimates above, R71).")
    q("- A flatter table spreads ratings further apart at the top (annex T3.5): counts above 2700 and 2800 compare two "
      "scales as well as two rules.")
    q("- The tables are fitted on broadcast games, stronger and more international than the rated pool.")
    q("- Layer 0 reads the 400-point rule of March 2024 to September 2025 as the plain cap, NOT VERIFIED against the "
      "handbook; FIDE's calculations agree in every tournament that can tell [E17 §2].")
    q("- The figures describe the rule, not the players: who is stronger is not their question.")
    q("")
    q(FIXED)
    return out


def main() -> int:
    if "--appendix" in sys.argv[1:]:
        a = json.loads(AGG.read_text(encoding="utf-8"))
        s = json.loads((ROOT / "analysis" / "aggregates" / "E18_selfcal.json").read_text(encoding="utf-8"))
        sys.stdout.write("\n".join(appendix(a, s)) + "\n")
        return 0
    a = json.loads(AGG.read_text(encoding="utf-8"))
    rows, v = a["players_table"], a["validation"]
    n = len(rows)
    mt, nc, bd, e17 = a["method"], a["no_colour"], a["bound"], a["e17_method"]
    sh = a["outside_shift"]
    first = a["first_table_year"]
    last = a["window"]["last"]
    bl = a["by_list"]
    up = sorted(rows, key=lambda r: (-r["difference"], r["fide_id"]))
    down = sorted(rows, key=lambda r: (r["difference"], r["fide_id"]))
    moved = [r for r in rows if r["rank_selfcal"] != r["rank_oct_2026"]]
    kc = a["k_check"]
    mean_t = sum(r["table_effect"] for r in rows) / n
    mean_c = sum(r["colour_effect"] for r in rows) / n
    p("# E19 — Today's top 100, self-calibrating: FIDE's rules against a table refitted each year on earlier games")
    p("")
    p("Status: REVIEW — evidence for the proposal, session ELO-8, Phase 4, under `docs/specs/SPEC-SELFCAL_v1_2.md` §9 and "
      "§10 (written before any replay ran; v1.2, session ELO-9, applies rulings R68, R71 and R72 of "
      "`docs/decisions/D-0016_rulings-on-elo-8-questions.md`). Generated by `analysis/e19_top100_selfcal_report.py` from "
      "`analysis/aggregates/E19_top100_selfcal.json`, which `analysis/e19_top100_selfcal_extract.py` writes from `data/` "
      "with E18's tables; do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). Data: FIDE's monthly standard "
      "lists and FIDE's published per-player calculations, analysed and never redistributed in bulk [V 3]; the figures "
      "below are the per-player figures SPEC-SELFCAL §10 defines, with names beside FIDE IDs (R60). Colours: the Lichess "
      "broadcast archive (https://database.lichess.org/broadcast/), CC BY-SA 4.0, attributed [V 4]. The self-calibrating "
      "tables are PROVISIONAL-FITTED, each on broadcast games played before its year [E18]. It supersedes E17's figures "
      "(R59) [E17].")
    p("")
    p(FIXED)
    p("")
    p("**In brief.**")
    p("")
    p(f"- **Validation first.** Layer 0 is E17's, unchanged, and so is its validation: given FIDE's own inputs it "
      f"reproduces FIDE's published Delta R in {v['games'] - v['game_delta_differs']:,} of {v['games']:,} games and the "
      f"published change in {v['periods'] - v['period_change_differs']:,} of {v['periods']:,} player-periods [E17 §2].")
    p(f"- **The self-calibrating system starts in {first}.** Its first table is {first}'s (E18 §1: no earlier year has a "
      f"window of games with FIDE IDs); before it the system uses FIDE's rules, so the two systems agree on every list "
      f"to December {first - 1} and differ only through tournaments rated with the {', '.join(map(str, a['tables_used']))} "
      "tables.")
    p(f"- **The average difference** (the self-calibrating system minus FIDE's rules, October 2026): "
      f"{sgn(mt['mean_difference'], 1)} points, from {sgn(mt['min'])} to {sgn(mt['max'])}; the table's effect "
      f"{sgn(mean_t, 1)}, colour's {sgn(mean_c, 1)}. With every opponent outside the 100 rated 10 points lower or higher "
      f"from {first} (R58): {sgn(sh['-10']['mean_difference'], 1)} to {sgn(sh['10']['mean_difference'], 1)}. With each "
      f"year's table corrected at levels of 2300 or more by its own residual on that year's games, R59's estimate of "
      f"the tables' own error at the top: {sgn(bd['mean_difference'], 1)} by level band, the reading the headline uses; "
      f"{sgn(a['bound_cells']['mean_difference'], 1)} by band and gap; both estimates, not bounds (R71). With the 2026 "
      f"table in the form R68 keeps (beside the headline; R68 applies from 2027): "
      f"{sgn(a['r68_2026']['mean_difference'], 1)}. E17's frozen table, superseded, gave "
      f"{sgn(e17['mean_difference'], 1)} over 2020–2026.")
    p("- **Largest risers** (with every player tied at the cut): " + "; ".join(
        f"{r['name']} ({r['fide_id']}) {sgn(r['difference'])}" for r in with_ties(up, 3, "difference"))
      + ". **At the other end:** " + "; ".join(f"{r['name']} ({r['fide_id']}) {sgn(r['difference'])}"
                                              for r in with_ties(down, 3, "difference")) + ".")
    p(f"- **Ranks within the 100:** {len(moved)} players change rank; the largest move is "
      f"{max(abs(r['rank_selfcal'] - r['rank_oct_2026']) for r in rows)} places.")
    p(f"- **2700 and 2800 in October 2026:** {bl[last]['published']['2700']} and {bl[last]['published']['2800']} of the "
      f"100 under FIDE's rules; {bl[last]['selfcal']['2700']} and {bl[last]['selfcal']['2800']} under the self-calibrating "
      f"system (E17's frozen table: {e17['2700']} and {e17['2800']}).")
    p(f"- **K (R61).** FIDE's K rules reproduce FIDE's printed K on {kc['reproduced']:,} of {kc['player_lists']:,} "
      f"player-lists; applied to the self-calibrating ratings they change K in "
      f"{a['k_departs_from_fide'].get('sc', 0)} tournaments of the method.")
    p("")
    p("## 1 What is replayed")
    p("")
    p("As E17 (`docs/specs/SPEC-TOP100_v1_0.md`): the 100 highest-rated active players of FIDE's October 2026 standard "
      f"list (rank 100 at {a['rank_100_rating']}), each from the January 2020 list, every standard game FIDE rated for them "
      "on the lists of February 2020 to October 2026 from FIDE's published per-player calculations, the 100 replayed "
      "together month by month, the opponents outside the 100 at their published ratings (the approximation R58 tests), "
      "and the difference the self-calibrating replay minus Layer 0's. With these changes (SPEC-SELFCAL §10):")
    p("")
    p(f"- **the table**: each tournament uses the table of the year of the list in force at its start [E18 §2]: the "
      f"{first} table for lists of {first}, and so on; η(L) rounded to whole points in each band, the published entry to "
      "three decimals, the narrowed guard as frozen (applies: "
      f"{a['guard_applies']}), no 400-point rule; before {first}, table 8.1.2 as FIDE applies it;")
    p("- **K**: FIDE's K rules applied to each system's own rating (R61, SPEC-SELFCAL §9);")
    p("- **colours** as E17, from the broadcast archive; a game without a matched colour carries no colour term.")
    p("")
    p("## 2 Today's top 100 under the self-calibrating system")
    p("")
    p("| rank | name | FIDE ID | federation | FIDE's rules, October 2026 | self-calibrating | difference | the table's "
      "effect | colour's effect | games under a table | share as favourite | E17's frozen table, difference | rank, "
      "self-calibrating |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: r["rank_oct_2026"]):
        fav = "—" if r["favourite_share_under_a_table"] is None else f"{r['favourite_share_under_a_table']:.2f}"
        p(f"| {r['rank_oct_2026']} | {r['name']} | {r['fide_id']} | {r['federation']} | {r['oct_2026']} | {r['selfcal']} | "
          f"{sgn(r['difference'])} | {sgn(r['table_effect'])} | {sgn(r['colour_effect'])} | {r['games_under_a_table']} | "
          f"{fav} | {sgn(r['e17_difference'])} | {r['rank_selfcal']} |")
    p("")
    p("Games under a table: the player's games in tournaments that used a self-calibrating table (lists from "
      f"{first}); share as favourite: of those games, the share against a lower-rated opponent.")
    p("")
    p("## 3 The headline, its range and R59's estimates")
    p("")
    p("| run | mean difference, October 2026 | range | higher / lower | 2700+ | 2800+ |")
    p("|---|---|---|---|---|---|")
    for lab, x in ([("the method: opponents outside the 100 as published", mt)]
                   + [(f"opponents outside the 100 rated {sgn(int(s))} points from {first} (R58)", sh[s])
                      for s in ("-10", "-5", "5", "10")]
                   + [("each year's table corrected at levels of 2300 or more by its own residual by level band "
                       "(R59's estimate, the reading the headline uses; R71)", bd),
                      ("the same by level band and 50-point gap (cells of 200 games or more; the band's value "
                       "elsewhere; R59's other estimate)", a["bound_cells"]),
                      ("without the colour term", nc),
                      ("the 2026 table in the form R68 keeps, form E with the draw tail within the caps (R68 applied "
                       "to 2026; D-0016, reading 6)", a["r68_2026"])]):
        p(f"| {lab} | {sgn(x['mean_difference'], 2)} | {sgn(x['min'])} to {sgn(x['max'])} | {x['higher']} / "
          f"{x['lower']} | {x['2700']} | {x['2800']} |")
    p(f"| E17's frozen table, 2020–2026 (superseded) | {sgn(e17['mean_difference'], 2)} | — | — | {e17['2700']} | "
      f"{e17['2800']} |")
    p("")
    br = a["bound_residuals"]
    p("R59's estimate by level band uses each table's favourite residual by 100-point level band at 2300 or more, pooled "
      "over gaps, on its own year's games (E18 §3; E16 §5's measure): " + "; ".join(
          f"{y}: " + ", ".join(f"{band(mid)} {sgn(r, 4)}" for mid, r in sorted(v_.items(), key=lambda kv: int(kv[0])))
          for y, v_ in sorted(br.items())) + ". R59 called the rerun a bound; R71 calls both readings estimates, not "
      "bounds, and the headline sentence uses the one by level band: a band's residual is pooled over gaps, while the "
      "gain arises at gaps of 100 to 399, where the residual is larger (review finding ELO8-STAT-5). Corrected by band "
      f"and gap instead, the mean is {sgn(a['bound_cells']['mean_difference'], 1)}. "
      f"Against the method's {sgn(mt['mean_difference'], 1)}, the tables' own error at the top could account for about "
      f"{mt['mean_difference'] - bd['mean_difference']:.1f} to "
      f"{mt['mean_difference'] - a['bound_cells']['mean_difference']:.1f} points of the headline; the rest is FIDE's "
      "table against the self-calibrating one. The band of 2800 and above holds a handful of games a year (E18 §1), so "
      "its residual is noise; it moves few games.")
    p("")
    p("## 4 Risers, fallers and ranks")
    p("")
    p("| | name | FIDE ID | FIDE's rules | self-calibrating | difference | E17's frozen table |")
    p("|---|---|---|---|---|---|---|")
    for lab, lst in (("largest", with_ties(up, 10, "difference")), ("smallest", with_ties(down, 10, "difference"))):
        for r in lst:
            p(f"| {lab} | {r['name']} | {r['fide_id']} | {r['oct_2026']} | {r['selfcal']} | {sgn(r['difference'])} | "
              f"{sgn(r['e17_difference'])} |")
    p("")
    big = sorted(rows, key=lambda r: (-abs(r["rank_selfcal"] - r["rank_oct_2026"]), r["fide_id"]))[:10]
    p("| name | FIDE ID | rank under FIDE's rules | rank, self-calibrating | places |")
    p("|---|---|---|---|---|")
    for r in big:
        p(f"| {r['name']} | {r['fide_id']} | {r['rank_oct_2026']} | {r['rank_selfcal']} | "
          f"{sgn(r['rank_oct_2026'] - r['rank_selfcal'])} |")
    p("")
    bo = a["by_opponent"]
    p("Where the table's effect comes from, in the games rated with a self-calibrating table: FIDE's expectation minus "
      "the table's, times K, summed per player (no colour term): " + "; ".join(
          f"against opponents {k}, {b['games']:,} games, {sgn(b['points_per_player'], 2)} points per player"
          for k, b in bo.items()) + ".")
    p("")
    p("## 5 2700 and 2800 on every list since the first table")
    p("")
    p("| list | 2700+: FIDE's rules | self-calibrating | 2800+: FIDE's rules | self-calibrating | mean difference | of "
      "which the table |")
    p("|---|---|---|---|---|---|---|")
    for m, row in sorted(bl.items()):
        if m < f"{first - 1}-12":
            continue
        p(f"| {m} | {row['published']['2700']} | {row['selfcal']['2700']} | {row['published']['2800']} | "
          f"{row['selfcal']['2800']} | {sgn(row['mean_difference'], 2)} | {sgn(row['mean_table_effect'], 2)} |")
    p("")
    p("Before these lists the two systems agree (§1). This report's aggregate keeps, for every list from January 2020, "
      "each player's difference between the two systems, by FIDE ID and name, and the October 2026 ratings of §2 (R72); "
      "both systems' ratings on every list, which hold FIDE's published ratings, stay in the local cache under `data/` "
      "(gitignored), where the deferred video session reads them without a refit.")
    p("")
    p("## 6 Each year: the table's effect and colour's effect")
    p("")
    p("| year | from | to | the table's effect, mean | colour's effect, mean | players the table moved up | down |")
    p("|---|---|---|---|---|---|---|")
    for y, r in sorted(a["by_year"].items()):
        p(f"| {y} | {r['from']} | {r['to']} | {sgn(r['mean_table_effect'], 2)} | {sgn(r['mean_colour_effect'], 2)} | "
          f"{r['players_table_up']} | {r['players_table_down']} |")
    p("")
    p("## 7 K (R61)")
    p("")
    dep = a["k_departs_from_fide"]
    tail = ("Applied to the self-calibrating ratings, the rules change K in "
            + ", ".join(f"{c} tournaments ({k})" for k, c in sorted(dep.items())) + "." if dep else
            "Applied to the self-calibrating ratings, the rules change no tournament's K: every player of the 100 crosses "
            "the same thresholds at the same lists under both systems.")
    p(f"FIDE's K rules in the order SPEC-L0 R-22 settles, applied to FIDE's own published ratings (with each player's "
      f"history from the February 2015 list, 30 games or more), reproduce FIDE's printed K on {kc['reproduced']:,} of "
      f"{kc['player_lists']:,} player-lists; where they do not ({len(kc['differs'])}), the self-calibrating K is FIDE's. "
      + tail)
    p("")
    p("## 8 Limits")
    p("")
    n_sc = sum(1 for m in bl if m >= f"{first}-01")
    n_all = sum(1 for m in bl if m > a["window"]["start_list"])
    p(f"- **Two years of tables.** The self-calibrating system has tables for {', '.join(map(str, a['tables_used']))} "
      f"only [E18 §1]; the difference accumulates over the {n_sc} lists rated with them, not E17's {n_all}.")
    p("- **Opponents outside the 100** keep their published ratings (R58's range in §3); a replay of the whole pool needs "
      "FIDE's tournament reports (proposal section 9, stage 2).")
    p("- **The table's own error** at the top is estimated, not removed: two estimates, neither a bound (§3, R59, R71).")
    p("- **The 2026 table's form** was chosen under SPEC-SELFCAL v1.1's rule, before R68 asked 24 months of games after "
      "the last rule change for a choice; R68 applies from 2027, and §3 gives the replay with the 2026 table in the form "
      "R68 keeps.")
    p("- **Two scales.** A flatter table spreads ratings further apart at the top (annex T3.5), so counts above 2700 and "
      "2800 compare two scales as well as two rules.")
    p("- **Colours** come from broadcasts; a game without a matched colour carries no colour term [E17 §8].")
    p("- **The rules** of 1 March 2024 to 30 September 2025 for the 400-point rule are read as the plain cap, NOT VERIFIED "
      "against the handbook; FIDE's calculations agree in every tournament that can tell [E17 §2] (SPEC-L0 §11).")
    p("- **Not anyone's true strength.** The figures show what the rule does to ratings with the same results.")
    sys.stdout.write("\n".join(r17.with_fixed_wording(P)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
