#!/usr/bin/env python3
"""E20 report: the greats on FIDE's own data; writes docs/evidence/E20_greats.md from analysis/aggregates/
GREATS_players.json, E20_greats_lists.json and E20_greats_replay.json (analysis/greats_select.py,
analysis/e20_greats_lists_extract.py and analysis/e20_greats_replay_extract.py, which need data/), under
docs/specs/SPEC-GREATS_v1_0.md, with the rulings R74 to R79 (docs/decisions/D-0017_rulings-on-the-greats.md); the
OlimpBase page it credits is read from analysis/aggregates/PROBE_greats.json. Every table carries the fixed wording of
SPEC-GREATS §1, the era caveat included, and every table that uses OlimpBase's lists a line crediting it (R77).
Session ELO-9, Phase 3. Python standard library only; deterministic.

Usage: python3 analysis/e20_greats_report.py > docs/evidence/E20_greats.md
       python3 analysis/e20_greats_report.py --appendix > analysis/OUTPUT_E20_appendix.md (the proposal's appendix
       "The greats, on FIDE's own data", from the same aggregates, carried verbatim)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates"
FIXED = ("*Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's "
         "own era.*")
NO_ID = "no FIDE ID on OlimpBase's lists"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
EARLY = "lists to June 2014 (no clause)"
ERAS = (EARLY, "lists of July 2014 to June 2017 (the 2014 clause)", "lists from July 2017 (the 2017 clause)")
READING_NAMES = {"R74": "R74, adopted: 0.5 towards +∞ on the lists before July 2014, away from zero from July 2014",
                 "rules record": "the rules record's first reading: 0.5 away from zero on every list",
                 "towards +infinity throughout": "for the architect, beyond R74: 0.5 towards +∞ on every list to "
                                                 "December 2019"}
MARK = "FIDE's mark"


def sgn(x: float | int, d: int = 0) -> str:
    s = f"{x:+.{d}f}"
    return ("+" + s[1:] if float(s) == 0 else s).replace("-", "−")      # a zero carries no minus sign


def num(x: float | int, d: int = 1) -> str:
    return f"{x:.{d}f}".replace("-", "−")


def month(m: str) -> str:
    return f"{MONTHS[int(m[5:7]) - 1]} {m[:4]}"


def day(d: str) -> str:
    return f"{int(d[8:10])} {MONTHS[int(d[5:7]) - 1]} {d[:4]}"


def words(n: int) -> str:
    return WORDS.get(n, str(n))


def surnames(names: list[str]) -> str:
    """'Petrosian, Polugaevsky and Tal' from FIDE's 'Surname, Given' forms."""
    s = [n.split(",")[0] for n in names]
    return s[0] if len(s) == 1 else ", ".join(s[:-1]) + " and " + s[-1]


def load() -> tuple[dict, dict, dict, dict]:
    sel = json.loads((AGG / "GREATS_players.json").read_text(encoding="utf-8"))
    lists = json.loads((AGG / "E20_greats_lists.json").read_text(encoding="utf-8"))
    rep = json.loads((AGG / "E20_greats_replay.json").read_text(encoding="utf-8"))
    probe = json.loads((AGG / "PROBE_greats.json").read_text(encoding="utf-8"))
    return sel, lists, rep, probe


def credit(probe: dict) -> str:
    """R77: the line under every table that uses OlimpBase's lists."""
    return (f"Lists to 2000: OlimpBase's transcription of FIDE's lists, by Wojciech Bartelski "
            f"({probe['olimpbase_lists']['summary']['url']}), used under its terms: free of charge, citing the source, "
            "non-commercial use only (DATA-PROBE §3); only figures derived from it are kept here (R77).")


def facts(sel: dict, lists: dict, rep: dict) -> dict:
    """The figures the report and the appendix both state, from the aggregates."""
    ch = lists["checks"]
    ob = ch["olimpbase_vs_fide_2001"]
    players = lists["players"]
    by_gap2 = sorted((p for p in players if p["best_by_gap2"]), key=lambda p: (-p["best_by_gap2"]["mean_gap2"], p["name"]))
    replayed = {r["fide_id"]: r for r in rep["players"]}
    half = {}
    for era, c in rep["rounding"].items():
        h = {"n": c.get("half_negative", 0) + c.get("half_positive", 0)}
        for k in ("away_from_zero", "towards_plus_infinity"):
            h[k] = c.get(f"half_negative_{k}", 0) + c.get(f"half_positive_{k}", 0)
        half[era] = h
    return {
        "n_players": len(sel["players"]), "no_id": [p["name"] for p in sel["players"] if not p["fide_id"]],
        "ob_equal": sum(x["rating_equal"] for x in ob), "ob_common": sum(x["common"] for x in ob),
        "hist_points": ch["fide_files_vs_histories"]["points"] + len(ch["fide_files_vs_histories"]["differ"]),
        "hist_equal": ch["fide_files_vs_histories"]["points"],
        "top3_equal": ch["printed_vs_computed_top3"]["equal"], "top3_dates": ch["printed_vs_computed_top3"]["dates"],
        "by_gap2": by_gap2, "replayed": replayed,
        "not_replayed": [p for p in sel["players"] if p["fide_id"] and p["fide_id"] not in replayed],
        "half": half, "politeness": ch["session_politeness"],
        "window_lists": (min(p["best_by_gap2"]["lists"] for p in by_gap2 if p["best_by_gap2"]["first"] < "1980"),
                         max(p["best_by_gap2"]["lists"] for p in by_gap2 if p["best_by_gap2"]["first"] >= "2010"))}


def slips(host: dict) -> str:
    by_tool: dict[str, list] = {}
    for g in host["gaps_under_2s"]:
        by_tool.setdefault(g["tool"], []).append(g["at"][11:19])
    return "; ".join(f"{len(v)} by the {tool} ({', '.join(v)} UTC)" for tool, v in by_tool.items())


# ------------------------------------------------------------------ the report
def report(sel: dict, lists: dict, rep: dict, probe: dict) -> list[str]:
    f = facts(sel, lists, rep)
    v, rd, s, rdg = rep["validation"], rep["rule_difference"], rep["summary"], rep["readings"]
    fide, ia = f["politeness"]["ratings.fide.com"], f["politeness"]["web.archive.org"]
    early, h_early = rep["rounding"][EARLY], f["half"][EARLY]
    later = [era for era in rep["rounding"] if era != EARLY]
    neg_later_up = sum(rep["rounding"][e].get("half_negative_towards_plus_infinity", 0) for e in later)
    neg_later_away = sum(rep["rounding"][e].get("half_negative_away_from_zero", 0) for e in later)
    nh = rep["negative_half_points"]["from_july_2014"]
    exc, exc_exact = early.get("half_not_towards_plus_infinity", 0), early.get("half_not_towards_plus_infinity_float_exact", 0)
    clean = nh["away_from_zero_before_last_up"] == 0 and nh["towards_plus_infinity_after_first_away"] == 0
    switch = (f"every negative half point towards +∞ up to the list of {month(nh['last_list_towards_plus_infinity'])} "
              f"({neg_later_up}) and every one away from zero from the list of "
              f"{month(nh['first_list_away_from_zero'])} ({neg_later_away})" if clean else
              f"{neg_later_up} negative half points towards +∞ and {neg_later_away} away from zero")
    out: list[str] = []
    p = out.append
    p("# E20 — The greats on FIDE's own data: their lists, their lead over their own era, and a replay where FIDE's "
      "calculations give every game")
    p("")
    p("Status: REVIEW — evidence for the proposal, session ELO-9, Phase 3, under `docs/specs/SPEC-GREATS_v1_0.md` (fixed "
      "before any analysis) and the rulings R74 to R79 (`docs/decisions/D-0017_rulings-on-the-greats.md`). Generated by "
      "`analysis/e20_greats_report.py` from `analysis/aggregates/GREATS_players.json`, "
      "`analysis/aggregates/E20_greats_lists.json` and `analysis/aggregates/E20_greats_replay.json`, which "
      "`analysis/greats_select.py`, `analysis/e20_greats_lists_extract.py` and `analysis/e20_greats_replay_extract.py` "
      "write from `data/`; do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). Data, as the probe found "
      "them legitimately available (`docs/research/DATA-PROBE_greats.md`): OlimpBase's transcription of FIDE's lists, "
      "July 1971 to 2000, of which only derived figures are kept (R77); FIDE's own list files from January 2001; FIDE's "
      "printed top-100 lists of July 2000 to December 2019 as the Internet Archive keeps them; FIDE's per-player rating "
      "calculations from the list of April 2008, whose full reproduction runs locally and of which only counts are "
      "committed (R79); the rules in force as transcribed in `docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md` "
      "and `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`. Not used: TWIC, ChessBase, Chessmetrics or any "
      "other source the probe marked as needing permission. The table applied in §5 is E18's 2025 table, "
      "PROVISIONAL-FITTED, **applied backwards, not fitted on that era**; every other parameter met here is PROVISIONAL. "
      "Every published rating committed here is a single value named by SPEC-GREATS §4 and §6 (a peak); no list and no "
      "series is committed (R72, R77).")
    p("")
    p(FIXED)
    p("")
    p("**In brief.**")
    p("")
    p(f"- **Who** (SPEC-GREATS §2, fixed before any analysis): the {f['n_players']} players ranked 1st to 3rd on any "
      f"FIDE list from July 1971 to December 2019. {words(len(f['no_id'])).capitalize()} of them "
      f"({surnames(f['no_id'])}) have {NO_ID} and are followed by name.")
    p(f"- **The sources, checked before use (§1).** OlimpBase's transcription equals FIDE's own four files of 2001 in "
      f"{f['ob_equal']:,} of {f['ob_common']:,} ratings; FIDE's old files, as converted, equal FIDE's per-player histories "
      f"in {f['hist_equal']} of {f['hist_points']} points; the top three by §2's rule equal FIDE's printed top three on "
      f"{f['top3_equal']} of {f['top3_dates']} dates.")
    p(f"- **Politeness (§1, R75).** Two slips, both recorded when they happened and fixed: gaps under two seconds "
      f"between requests to ratings.fide.com, {slips(fide)}. Since {fide['fixed_after'][11:19]} UTC every one of the "
      f"session's requests to ratings.fide.com came at least {fide['smallest_gap_after_fix']:.0f} s after the one "
      f"before, as logged; to the Internet Archive, which refused connections at one request every four seconds, at "
      f"least {ia['smallest_gap_after_fix']:.0f} s since {ia['fixed_after'][11:19]} UTC.")
    top = f["by_gap2"][:4]
    p("- **The lead over one's own era (§3)**, the best three consecutive years by the mean gap to the list's #2: "
      + "; ".join(f"{x['name']} {sgn(x['best_by_gap2']['mean_gap2'], 1)} ({month(x['best_by_gap2']['first'])} to "
                  f"{month(x['best_by_gap2']['last'])}, {x['best_by_gap2']['lists']} lists)" for x in top)
      + f". A best window holds {f['window_lists'][0]} lists in the 1970s and up to {f['window_lists'][1]} in the "
      "2010s: the lists' frequency differs by era, and so does what a gap means.")
    p(f"- **The replay (§4, §5)**: {rep['players_replayed']} players, April 2008 to December 2019. Layer 0 with the rules "
      f"in force reproduces FIDE's printed change in {v['games'] - v['game_delta_differs']:,} of {v['games']:,} games "
      f"and the published change in {s['periods_replayed']:,} of {v['periods_with_page']:,} player-periods with a "
      f"page; {s['thin_periods']:,} periods are thin (§4.3) and carry FIDE's change for both systems. FIDE's pages "
      f"show the 350-point rule on tournaments that started up to {day(rd['last_start_with_350'])} and the 400-point "
      f"rule from {day(rd['first_start_beyond_350'])}, consistent with the rules record's reading of 1 July 2009.")
    p(f"- **Rounding (§4.2, R74).** On the lists before July 2014, of {h_early['n']} periods whose sum ended in a half "
      f"point, 0.5 towards +∞ reproduces {h_early['towards_plus_infinity']} and 0.5 away from zero "
      f"{h_early['away_from_zero']} (the two differ on negative half points only: "
      f"{early.get('half_negative_towards_plus_infinity', 0)} of {early.get('half_negative', 0)} went up, "
      f"{early.get('half_negative_away_from_zero', 0)} away); Layer 0 adopts towards +∞ there (R74), a reading changed "
      "after partial pages had been seen and before the full replay. Thin periods: {rdg['R74']['thin_periods']:,} under R74's reading, "
      f"{rdg['rules record']['thin_periods']:,} under the rules record's first one. From the list of July 2014, outside "
      f"R74, FIDE's lists rounded {switch}; the reading kept from July 2014, away from zero, leaves the first group "
      "thin: left to the architect.")
    p(f"- **Under the 2025 table applied backwards** (December 2019, the table minus FIDE's rules): "
      f"{sgn(s['mean_difference'], 1)} points on average over the {rep['players_replayed']} players, from "
      f"{sgn(s['min_difference'])} to {sgn(s['max_difference'])}; the table's effect {sgn(s['mean_table_effect'], 1)}, "
      f"colour's {sgn(s['mean_colour_effect'], 1)}; {s['higher']} higher, {s['lower']} lower, {s['equal']} unchanged. "
      f"Under the rules record's first reading of the rounding the mean is "
      f"{sgn(rdg['rules record']['mean_difference'], 1)}.")
    p("- **The cross-era head-to-head (§6) is not attempted**: no legitimately usable game data link the eras.")
    p("")
    # ------------------------------------------------------------------ §1
    p("## 1 The sources, checked before use")
    p("")
    p(FIXED)
    p("")
    p("| check | result |")
    p("|---|---|")
    for x in lists["checks"]["olimpbase_vs_fide_2001"]:
        p(f"| OlimpBase's list of {month(x['list'])} against FIDE's own file of the same date | {x['common']:,} players "
          f"in both (FIDE's file: {x['fide']:,}); ratings equal {x['rating_equal']:,}; inactivity flags equal "
          f"{x['flag_equal']:,} |")
    hd = lists["checks"]["fide_files_vs_histories"]
    p(f"| FIDE's old files (2001–2015), as converted, against FIDE's per-player histories (chart data, from April 2003) "
      f"| {hd['points']} of {hd['points'] + len(hd['differ'])} points equal; "
      + "; ".join(f"{month(d['list'])}: file {d['file']}, history {d['history']} (FIDE ID {d['id']})" for d in hd["differ"])
      + " |")
    pc = lists["checks"]["printed_vs_computed_top3"]
    p(f"| The top three computed by SPEC-GREATS §2's rule against FIDE's printed top three, on the dates with both | "
      f"equal on {pc['equal']} of {pc['dates']} dates; unequal on " + ", ".join(month(d) for d in pc["unequal"]) + " |")
    p(f"| Requests to ratings.fide.com, every tool of the session (the brief: two seconds apart; R75: four, across "
      f"runs) | {fide['requests']:,} from {fide['first'][11:19]} to {fide['last'][11:19]} UTC, 11 October 2026 ("
      + ", ".join(f"{tool} {n:,}" for tool, n in fide["by_tool"].items())
      + f"); gaps under two seconds, the two slips: {slips(fide)}, the old lists' send times reconstructed from a log "
        f"written before each wait; since {fide['fixed_after'][11:19]} UTC the smallest gap "
        f"{fide['smallest_gap_after_fix']:.0f} s as logged, {fide['gaps_under_asked_after_fix']} under four |")
    p(f"| Requests to the Internet Archive (R75: eight seconds, across runs) | {ia['requests']} from "
      f"{ia['first'][11:19]} to {ia['last'][11:19]} UTC; at one every four seconds it refused connections, the run was "
      f"stopped and the gap raised; since {ia['fixed_after'][11:19]} UTC the smallest gap "
      f"{ia['smallest_gap_after_fix']:.0f} s, {ia['gaps_under_asked_after_fix']} under eight |")
    p("")
    p(credit(probe))
    p("")
    p("Where the computed and printed top three differ, the printed list decides (SPEC-GREATS §2).")
    p("")
    # ------------------------------------------------------------------ (i)
    p("## 2 (i) FIDE's published series")
    p("")
    p("For each player, from the first to the last list on which the player appears (to October 2026): the number of "
      "lists, the peak published rating and the lists on which it stood, and the lists on which §2's rule ranks the "
      "player 1st, 1st to 3rd and 1st to 10th (July 1971 to December 2019). The series themselves stay in the local "
      "cache (R72, R77).")
    p("")
    p(FIXED)
    p("")
    p("| # | name | FIDE ID | federation | on the lists | lists | peak | at the peak | ranked 1st | 1st–3rd | 1st–10th |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, x in enumerate(lists["players"], 1):
        at = ", ".join(month(m) for m in x["peak_lists"][:3]) + (f" and {len(x['peak_lists']) - 3} more"
                                                                if len(x["peak_lists"]) > 3 else "")
        p(f"| {i} | {x['name']} | {x['fide_id'] or '—'} | {x['federation']} | {month(x['first_list'])} – "
          f"{month(x['last_list'])} | {x['lists']} | {x['peak']} | {at} | {x['lists_rank1']} | {x['lists_top3']} | "
          f"{x['lists_top10']} |")
    p("")
    p(credit(probe))
    p("")
    # ------------------------------------------------------------------ (ii)
    p("## 3 (ii) The lead over one's own era: the best three consecutive years")
    p("")
    p("On each list the gap to #2 is the player's rating minus the list's #2 (for the #1, the lead; for any other player "
      "zero or less) and the gap to #10 the rating minus the list's #10, #2 and #10 from the same source as the ranks "
      "(SPEC-GREATS §5). A window holds every list from its first to before 36 months later and counts only if the player "
      "is ranked on each; windows reaching past December 2019 do not count. Sorted by the mean gap to #2 in the best "
      "window.")
    p("")
    p(FIXED)
    p("")
    p("| # | name | best window by the gap to #2 | lists | mean gap to #2 | mean gap to #10 | at #1 | best window by the gap "
      "to #10 | its mean gap to #10 |")
    p("|---|---|---|---|---|---|---|---|---|")
    for i, x in enumerate(f["by_gap2"], 1):
        b, c = x["best_by_gap2"], x["best_by_gap10"]
        p(f"| {i} | {x['name']} | {month(b['first'])} – {month(b['last'])} | {b['lists']} | {sgn(b['mean_gap2'], 1)} | "
          f"{sgn(b['mean_gap10'], 1)} | {b['lists_at_1']} | {month(c['first'])} – {month(c['last'])} | "
          f"{sgn(c['mean_gap10'], 1)} |")
    p("")
    p(credit(probe))
    p("")
    p("A mean gap measures a lead over contemporaries only. A window of the 1970s holds three or four lists, one of the "
      "2010s thirty-six; the spread of the top ten changes with the era and with the size of the list. No row is a "
      "comparison across eras (§6).")
    p("")
    # ------------------------------------------------------------------ (iii)
    p("## 4 (iii) The replay, April 2008 to December 2019: validation first")
    p("")
    p(f"**What is replayed** (SPEC-GREATS §6). The {rep['players_replayed']} players of §2 with a standard rating period "
      "on FIDE's calculations index between the lists of April 2008, the first whose calculations give every game "
      "(DATA-PROBE §2.4), and December 2019, replayed together list by list from their published ratings of January 2008; "
      f"{rep['pages']['read']:,} of FIDE's per-player pages, {v['games']:,} games in {v['tournaments']:,} tournaments. "
      f"Not replayed: {surnames([x['name'] for x in f['not_replayed']])}, who have no standard rating period on FIDE's "
      f"calculations index in the window, and {surnames(f['no_id'])}, who have no FIDE ID. Opponents outside the set at "
      "the ratings FIDE's pages print, or, where a page prints a capped value, at the rating of the same name on the list "
      "in force (R58's approximation); opponents inside the set at their replayed ratings. The reproduction runs locally "
      "from the cached pages; only its counts are committed (R79), and a sample of fourteen cases chosen by a fixed rule "
      "is kept as test fixtures (`tests/fixtures/fide_greats/`).")
    p("")
    p("### 4.1 Layer 0 against FIDE")
    p("")
    p(FIXED)
    p("")
    per_page = v["periods_with_page"]
    p("| check | reproduced |")
    p("|---|---|")
    p(f"| each game's ΔR (score − PD, the rating-difference rule in force at the tournament's start) | "
      f"{v['games'] - v['game_delta_differs']:,} of {v['games']:,} |")
    p(f"| each tournament's ΣΔR and K × ΣΔR | {v['tournaments'] - v['tournament_sum_differs']:,} and "
      f"{v['tournaments'] - v['tournament_k_chg_differs']:,} of {v['tournaments']:,} |")
    p(f"| K: FIDE's K rules of the version in force on FIDE's own ratings against FIDE's printed K | "
      f"{v['tournaments'] - v.get('k_rule_differs', 0):,} of {v['tournaments']:,} tournaments (K printed: "
      + ", ".join(f"{k} in {n:,}" for k, n in rep["k_printed"].items()) + ") |")
    p(f"| each period's published change, with a page | {s['periods_replayed']:,} player-periods reproduced, the "
      f"rest thin (§4.3), of {per_page:,} pages |")
    p(f"| the page's own total against the sum of its tournaments | {per_page - v['total_shown_differs']:,} of "
      f"{per_page:,} |")
    p(f"| games whose page may print a capped rating (a gap of exactly 350 or 400 points, or FIDE's mark) | "
      f"{v['cap_candidates']:,}: the opponent's rating found on the list in force for {v['cap_resolved']:,}; "
      f"{v['cap_unresolved']:,} not found, read at the value printed |")
    p(f"| games against another of the set | {v['set_games']:,}, of which {v['set_name_unconfirmed']:,} whose rating does "
      "not confirm the name, replayed as games against an outside opponent |")
    p("")
    p("### 4.2 What the texts leave open, read from FIDE's pages")
    p("")
    p("**The 350- and 400-point rules.** On every game whose gap exceeds 350 points and whose opponent's rating is known "
      "(the rating FIDE printed, or the one found on the list in force where FIDE printed a capped value), the rule FIDE "
      "applied, by the version in force at the tournament's start as `src/layer0_greats/` reads it:")
    p("")
    p(FIXED)
    p("")
    p("| version (tournaments starting) | capped at 350 (unmarked / marked) | capped at 400 (unmarked / marked) | the "
      "full gap used | other |")
    p("|---|---|---|---|---|")
    lab = {"2007": "to 30 June 2009 (350 points)", "2009": "1 July 2009 to 30 June 2014 (400)",
           "2014": "1 July 2014 to 30 June 2017 (400)", "2017": "from 1 July 2017 (400)"}
    for ver, c in rd["by_version"].items():
        p(f"| {lab.get(ver, ver)} | {c.get('350', 0):,} ({c.get('350, no mark', 0):,} / {c.get('350, ' + MARK, 0):,}) | "
          f"{c.get('400', 0):,} ({c.get('400, no mark', 0):,} / {c.get('400, ' + MARK, 0):,}) | {c.get('none', 0):,} | "
          f"{c.get('other', 0):,} |")
    p("")
    p(f"The last tournament FIDE capped at 350 points started on {day(rd['last_start_with_350'])}; the first in which "
      f"it used a gap beyond 350 started on {day(rd['first_start_beyond_350'])}. The reading of the rules record "
      "(tournaments starting from 1 July 2009) agrees with FIDE's pages to within those dates, and the marks show how "
      "the pages print a capped rating: as the player's own minus 350, unmarked, before July 2009, and with FIDE's "
      "asterisk after it.")
    p("")
    p("**Rounding (R74).** The 2007 and 2010 texts have no rounding clause. The rules record, written before FIDE's "
      "pages were seen, read them as the 2014 clause applied as E17 found the same words of 2017 applied, 0.5 away from "
      "zero. FIDE's pages contradicted it: on the pages then fetched, 0.5 towards +∞ reproduced 44 of 49 half-point "
      "periods and away from zero 27. Ruling R74 (`docs/decisions/D-0017_rulings-on-the-greats.md`) adopts towards +∞, "
      "the 2014 words read literally, for every list published before July 2014 (SPEC-L0 v1.3 §11, finding F-H09); "
      "the switch was made after those partial pages and before the full replay. On every period with a page and no "
      "gap in FIDE's files, by the clause in force when the list was published:")
    p("")
    p(FIXED)
    p("")
    p("| lists | periods | reproduced as Layer 0 rounds (R74) | rounding 0.5 away from zero | rounding 0.5 towards +∞ "
      "| rounding once per tournament | negative half points: towards +∞ / away from zero | positive half points: "
      "towards +∞ / towards zero |")
    p("|---|---|---|---|---|---|---|---|")
    for era in ERAS:
        c = rep["rounding"][era]
        p(f"| {era} | {c['periods']:,} | {c['reproduced']:,} | {c['reproduced_away_from_zero']:,} | "
          f"{c['reproduced_towards_plus_infinity']:,} | {c['reproduced_once_per_tournament']:,} | "
          f"{c.get('half_negative_towards_plus_infinity', 0)} / {c.get('half_negative_away_from_zero', 0)} of "
          f"{c.get('half_negative', 0)} | {c.get('half_positive_towards_plus_infinity', 0)} / "
          f"{c.get('half_positive_towards_zero', 0)} of {c.get('half_positive', 0)} |")
    p("")
    p(f"Once per period is the rule FIDE's lists follow. On the lists before July 2014, of {h_early['n']} periods whose "
      f"sum ends in exactly a half point, towards +∞ reproduces {h_early['towards_plus_infinity']} and away from zero "
      f"{h_early['away_from_zero']}; the two readings agree on positive half points and differ on the "
      f"{early.get('half_negative', 0)} negative ones. "
      + (f"Floating-point sums do not explain all of the {exc} exceptions to towards +∞: {exc_exact} of them are half "
         "points that a binary floating-point sum gives exactly, game by game and tournament by tournament, so no "
         "floating-point error can have tipped those. " if exc_exact else
         f"None of the {exc} exceptions to towards +∞ is a half point a binary floating-point sum gives exactly, so the "
         "floating-point sums FIDE's software may use could explain them. ")
      + "From the list of July 2014, outside R74, "
      f"FIDE's lists rounded {switch}, consistent with E17's finding of away from zero on the lists from February 2020 "
      "(SPEC-L0 F-H07): FIDE's arithmetic changed between those two lists. The reading kept from July 2014, away from "
      "zero, leaves the periods before the change thin; which reading those lists follow is left to the architect. By "
      "the year of the list, every period whose sum ended in a negative half point:")
    p("")
    p(FIXED)
    p("")
    p("| year of the list | towards +∞ | away from zero | neither |")
    p("|---|---|---|---|")
    for y, c in rep["negative_half_points"]["by_year"].items():
        p(f"| {y} | {c.get('towards_plus_infinity', 0)} | {c.get('away_from_zero', 0)} | {c.get('neither', 0)} |")
    p("")
    p("**The readings and the thin periods.** The replay under each reading of the rounding (R74 asks for both; the "
      "third is information for the architect):")
    p("")
    p(FIXED)
    p("")
    p("| reading | thin periods | player-periods replayed | games replayed | mean difference, December 2019 | range |")
    p("|---|---|---|---|---|---|")
    for key in ("R74", "rules record", "towards +infinity throughout"):
        x = rdg[key]
        p(f"| {READING_NAMES[key]} | {x['thin_periods']:,} | {x['periods_replayed']:,} | {x['games_replayed']:,} | "
          f"{sgn(x['mean_difference'], 2)} | {sgn(x['min_difference'])} to {sgn(x['max_difference'])} |")
    p("")
    p("Periods that no reading reproduces stay thin and carry FIDE's change (R74). The comparison of §5 uses R74's "
      "reading.")
    p("")
    p("### 4.3 Thin periods")
    p("")
    p("A period is thin when FIDE's page is missing, or when Layer 0 does not reproduce its published change; both "
      "systems then take FIDE's published change, so that the difference between them is carried unchanged through it "
      "(SPEC-GREATS §6). Where FIDE's own list file of a date lacks a player of the set, the periods to the next file "
      "that carries the player are checked together against it. Under R74's reading:")
    p("")
    p(FIXED)
    p("")
    p("| cause | thin periods |")
    p("|---|---|")
    for cause, n in sorted(rep["thin_by_cause"].items(), key=lambda x: (-x[1], x[0])):
        p(f"| {cause} | {n} |")
    p("")
    checked = rep["checked_with_next_file"]
    if checked:
        name = {str(r["fide_id"]): r["name"] for r in rep["players"]}
        p("FIDE's list files that lack a player of the set, and the check against the next file: " + "; ".join(
            f"{name[c[0]]}, absent from " + ", ".join(month(m) for m in c[1].split()) + f", checked with "
            f"{month(c[2])}: {c[3]}" for c in checked) + ".")
        p("")
    p("Every thin period, by player (list, cause):")
    p("")
    for r in rep["players"]:
        if r["thin"]:
            p(f"- {r['name']} ({r['fide_id']}): " + "; ".join(f"{t[0]} {t[1]}" for t in r["thin"]) + ".")
    p("")
    # ------------------------------------------------------------------ the table applied backwards
    p("## 5 (iii) The greats under the 2025 table, applied backwards")
    p("")
    p("Rung 2 applies E18's 2025 table (form E with the draw tail, fitted on games of March to December 2024 [E18 §2]) "
      "to every replayed game: **applied backwards, not fitted on that era**. η(L) whole in each band, the published "
      "entry to three decimals, the narrowed guard as frozen, no 400-point rule; colours from FIDE's colour marks "
      f"(White {rep['colour_marks'].get('white', 0):,}, Black {rep['colour_marks'].get('black', 0):,}: every replayed "
      "game carries one; E17 found them 98.4 % in agreement with the broadcast archive in 2020–2026, and they are "
      "unchecked before 2020); K by FIDE's K rules on each system's own rating (R61: the rules change K in "
      f"{rep['k_departs_from_fide']['r2']} tournaments of the method); each period's change rounded as Layer 0 rounds it. "
      "The difference is rung 2 minus Layer 0 on the last list, December 2019; Layer 0 equals FIDE's published rating "
      "on every list it reproduces.")
    p("")
    p(FIXED)
    p("")
    p("| # | name | FIDE ID | periods replayed | games | thin periods | difference, December 2019 | the table's effect "
      "| colour's effect | outside opponents −10 / +10 | highest under FIDE's rules, 2008–2019 | highest under the "
      "2025 table |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows = sorted(rep["players"], key=lambda r: (-r["highest_layer0"]["rating"], r["name"]))
    for i, r in enumerate(rows, 1):
        h0, h2 = r["highest_layer0"], r["highest_rung2"]
        p(f"| {i} | {r['name']} | {r['fide_id']} | {r['periods_replayed']} | {r['games_replayed']:,} | "
          f"{r['thin_periods']} | {sgn(r['difference'])} | {sgn(r['table_effect'])} | {sgn(r['colour_effect'])} | "
          f"{sgn(r['difference_outside_minus10'])} / {sgn(r['difference_outside_plus10'])} | {h0['rating']} "
          f"({month(h0['lists'][0])}) | {h2['rating']} ({month(h2['lists'][0])}) |")
    p("")
    n = len(rep["players"])
    p(f"On average {sgn(s['mean_difference'], 1)} points (the table's effect {sgn(s['mean_table_effect'], 1)}, colour's "
      f"{sgn(s['mean_colour_effect'], 1)}); with every opponent outside the set 10 points lower or higher, "
      f"{sgn(sum(r['difference_outside_minus10'] for r in rep['players']) / n, 1)} and "
      f"{sgn(sum(r['difference_outside_plus10'] for r in rep['players']) / n, 1)}. The table was fitted on games of "
      "2024, after every game replayed here: it is applied to an era it never saw, and the difference says what today's "
      "table would have made of the same results, not what a table fitted on that era would have.")
    p("")
    p("**The difference at each year end** (rung 2 − Layer 0, the method):")
    p("")
    p(FIXED)
    p("")
    years = sorted({y for r in rep["players"] for y in r["year_end_difference"]})
    p("| name | " + " | ".join(years) + " |")
    p("|---|" + "---|" * len(years))
    for r in sorted(rep["players"], key=lambda r: r["name"]):
        p(f"| {r['name']} | " + " | ".join(sgn(r["year_end_difference"][y]) if y in r["year_end_difference"] else "—"
                                           for y in years) + " |")
    p("")
    # ------------------------------------------------------------------ (iv)
    p("## 6 (iv) The cross-era head-to-head: not attempted")
    p("")
    p("No legitimately usable game data link the eras (DATA-PROBE §5; SPEC-GREATS §7): TWIC, ChessBase, Chessmetrics and "
      "the other game collections need permission; OlimpBase's Olympiad games credit ChessBase's database and TWIC's "
      "editor among their sources; the Lichess broadcast archive starts in 2020; FIDE's calculations give each player's "
      "own games from 2008 only. A comparison of one era's greats with another's would need every game between them and "
      "the players linking them, rated on one scale; the data that would allow it are not ours to use without "
      "permission. With permission from TWIC, ChessBase or Chessmetrics the full study becomes possible.")
    p("")
    p("## 7 Limits")
    p("")
    p("- The lists before 2001 are OlimpBase's transcription of FIDE's lists (checked against FIDE's own files of 2001 "
      "only); the ranks before July 2000 are computed by SPEC-GREATS §2's rule, not printed by FIDE.")
    p("- The replay covers the lists of April 2008 to December 2019 only, the window in which FIDE's calculations give "
      "every game; most of the greats' careers lie outside it, and the greats of the 1970s and 1980s are not replayed.")
    p("- Opponents outside the set keep FIDE's ratings (R58's approximation); ±10 points around them is shown in §5.")
    p("- The colour term uses FIDE's colour marks, unchecked before 2020.")
    p("- The 2025 table is applied backwards to an era it was not fitted on: the replay shows the rule's effect on the "
      "same results, not a measure of anyone's strength, and not a comparison across eras.")
    p("- The rounding before July 2014 is read from FIDE's pages (R74), a reading changed after partial pages were seen; "
      "the rounding of July 2014 to December 2019 keeps a reading FIDE's pages contradict for negative half points, and "
      "those periods are thin (§4.2).")
    return out


# ------------------------------------------------------------------ the proposal's appendix
def appendix(sel: dict, lists: dict, rep: dict, probe: dict) -> list[str]:
    """The proposal's appendix 'The greats, on FIDE's own data': E20 in one page, every number from the aggregates."""
    f = facts(sel, lists, rep)
    v, rd, s, rdg = rep["validation"], rep["rule_difference"], rep["summary"], rep["readings"]
    out: list[str] = []
    q = out.append
    q("## Appendix I The greats, on FIDE's own data")
    q("")
    q("Outside the body's word count. From E20 (`docs/evidence/E20_greats.md`), under SPEC-GREATS v1.0, fixed before "
      "any analysis, and the rulings R74 to R79. Every table here, as in E20, reads:")
    q("")
    q(FIXED)
    q("")
    q("**The data, and their limits.** The study uses only what the data probe found legitimately available "
      "(`docs/research/DATA-PROBE_greats.md`): FIDE's lists (as OlimpBase transcribes them to 2000, FIDE's own files "
      "since 2001), FIDE's printed top lists of 2000–2019 as the Internet Archive keeps them, and FIDE's per-player "
      "rating calculations, which give every game only from the list of April 2008. **TWIC and Chessmetrics were not "
      "used**, nor ChessBase or any other game collection whose terms need permission. So the greats' lists and their "
      "lead over their own era can be shown from 1971, but their games can be replayed only from 2008, and no "
      "comparison across eras is possible.")
    q("")
    first_list = min(x["first_top3"] for x in sel["players"])
    last_join = max(x["first_top3"] for x in sel["players"])
    q(f"**Who.** The {f['n_players']} players ranked 1st to 3rd on any FIDE list from July 1971 to December 2019 "
      f"[E20 §2], from {surnames([x['name'] for x in sel['players'] if x['first_top3'] == first_list])} on the first "
      f"list ({month(first_list)}) to "
      f"{surnames([x['name'] for x in sel['players'] if x['first_top3'] == last_join])}, the last to join "
      f"({month(last_join)}).")
    q("")
    q("**Their lead over their own era** [E20 §3]: the best three consecutive years by the mean gap to the list's #2, "
      "the six largest.")
    q("")
    q(FIXED)
    q("")
    q("| name | best three years | lists | mean gap to #2 | mean gap to #10 |")
    q("|---|---|---|---|---|")
    for x in f["by_gap2"][:6]:
        b = x["best_by_gap2"]
        q(f"| {x['name']} | {month(b['first'])} – {month(b['last'])} | {b['lists']} | {sgn(b['mean_gap2'], 1)} | "
          f"{sgn(b['mean_gap10'], 1)} |")
    q("")
    q(credit(probe))
    q("")
    q("A lead over one's contemporaries, on lists whose frequency and spread change with the era: not a ranking "
      "across eras.")
    q("")
    q(f"**The replay, 2008–2019** [E20 §4–§5]. Of the {f['n_players']}, {rep['players_replayed']} have rated games in "
      "the window. Layer 0, with the rules in force at each date, reproduces FIDE's printed change in "
      f"{v['games'] - v['game_delta_differs']:,} of {v['games']:,} games; {s['thin_periods']:,} player-periods are thin "
      "and carry FIDE's change. FIDE's pages date the end of the 350-point rule: last applied to a tournament starting "
      f"{day(rd['last_start_with_350'])}, the 400-point rule from {day(rd['first_start_beyond_350'])}. Before July "
      "2014 FIDE rounded a half point towards +∞, which Layer 0 adopts (R74), a reading changed after partial pages "
      f"had been seen ({rdg['rules record']['thin_periods']:,} thin periods under the reading first recorded). Under "
      "the 2025 table, **applied backwards, not fitted on that era**, the greats end 2019 "
      f"{num(abs(s['mean_difference']))} points {'above' if s['mean_difference'] > 0 else 'below'} FIDE's ratings on "
      f"average (from {sgn(s['min_difference'])} to {sgn(s['max_difference'])}):")
    q("")
    q(FIXED)
    q("")
    q("| name | games | highest under FIDE's rules, 2008–2019 | highest under the 2025 table | difference, December 2019 |")
    q("|---|---|---|---|---|")
    for r in sorted(rep["players"], key=lambda r: (-r["highest_layer0"]["rating"], r["name"]))[:10]:
        h0, h2 = r["highest_layer0"], r["highest_rung2"]
        q(f"| {r['name']} | {r['games_replayed']:,} | {h0['rating']} ({month(h0['lists'][0])}) | {h2['rating']} "
          f"({month(h2['lists'][0])}) | {sgn(r['difference'])} |")
    q("")
    q("**What permission would add.** With written permission from TWIC, ChessBase or Chessmetrics, the full study "
      "becomes possible: every game of the greats' careers replayed under both systems, not only those of 2008–2019, "
      "and the games that link one era's players to the next. Permission has not been sought.")
    q("")
    return out


def main() -> int:
    sel, lists, rep, probe = load()
    lines = appendix(sel, lists, rep, probe) if "--appendix" in sys.argv[1:] else report(sel, lists, rep, probe)
    sys.stdout.write("\n".join(lines).rstrip("\n") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
