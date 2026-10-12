#!/usr/bin/env python3
"""E20 report: the greats on FIDE's own data; writes docs/evidence/E20_greats.md from analysis/aggregates/
GREATS_players.json, E20_greats_lists.json and E20_greats_replay.json (analysis/greats_select.py,
analysis/e20_greats_lists_extract.py and analysis/e20_greats_replay_extract.py, which need data/), under
docs/specs/SPEC-GREATS_v1_0.md, with the rulings R74 to R79 (docs/decisions/D-0017_rulings-on-the-greats.md), the
fixes of the ELO-9 review (docs/review/REDTEAM_v1_0.md) and ruling R80 (docs/decisions/D-0018_rulings-on-elo-9-
questions.md), with §5's reading of the calibration check corrected on 12 October 2026 (docs/DECISIONS.md, item 9);
the OlimpBase page it credits is read from
analysis/aggregates/PROBE_greats.json, and the 2025 table's fit window by level from analysis/aggregates/
E18_coverage.json. Every table carries the fixed wording of SPEC-GREATS §1, the era caveat included, and every table
that uses OlimpBase's lists a line crediting it (R77). Sessions ELO-9, Phases 3 and 5, and ELO-10, Phase 2. Python
standard library only; deterministic.

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
FIXTURES = ROOT / "tests" / "fixtures" / "fide_greats" / "published_periods.json"   # the sample R79 keeps
FIXED = ("*Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's "
         "own era.*")
NO_ID = "no FIDE ID on OlimpBase's lists"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
         14: "fourteen", 16: "sixteen"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
EARLY = "lists to June 2014 (the 2007 and 2010 texts)"
ERAS = (EARLY, "lists of July 2014 to June 2017 (the 2014 clause)", "lists of July 2017 to October 2018 (the 2017 clause)",
        "lists from November 2018 (the 2017 clause)")
READINGS = ("R80", "D-0017", "rules record", "towards +infinity throughout")
READING_NAMES = {"R80": "R80, adopted: 0.5 towards +∞ on every list to October 2018, away from zero from November 2018",
                 "D-0017": "D-0017's reading, superseded by R80 from July 2014: 0.5 towards +∞ on the lists before July "
                           "2014, away from zero from July 2014",
                 "rules record": "the rules record's first reading: 0.5 away from zero on every list",
                 "towards +infinity throughout": "for information (D-0017 reading 2): 0.5 towards +∞ on every list to "
                                                 "December 2019"}
MARK = "FIDE's mark"
OTHER_WAY = "a half point, rounded the other way"
NOT_ROUNDING = "the list's change is not a rounding of the page's sum"
BAND = {"2350": "2300–2399", "2450": "2400–2499", "2550": "2500–2599", "2650": "2600–2699", "2750": "2700–2799",
        "2850": "2800 and above"}


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


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def surnames(names: list[str]) -> str:
    """'Aa, Bb and Cc' from FIDE's 'Aa, X', 'Bb, Y', 'Cc, Z' ('Surname, Given') forms."""
    s = [n.split(",")[0] for n in names]
    return s[0] if len(s) == 1 else ", ".join(s[:-1]) + " and " + s[-1]


def ci(x: dict) -> str:
    return f"{sgn(x['mean'], 3)} ({sgn(x['lo'], 3)} to {sgn(x['hi'], 3)})"


def load() -> tuple[dict, dict, dict, dict, dict]:
    sel = json.loads((AGG / "GREATS_players.json").read_text(encoding="utf-8"))
    lists = json.loads((AGG / "E20_greats_lists.json").read_text(encoding="utf-8"))
    rep = json.loads((AGG / "E20_greats_replay.json").read_text(encoding="utf-8"))
    probe = json.loads((AGG / "PROBE_greats.json").read_text(encoding="utf-8"))
    e18 = json.loads((AGG / "E18_coverage.json").read_text(encoding="utf-8"))
    return sel, lists, rep, probe, e18


def credit(probe: dict, terms: str, plain: bool = False) -> str:
    """R77's credit and R83's label (D-0018): the line under every table that uses OlimpBase's lists; with plain, the
    same without the rulings' numbers, for the proposal's appendix (session ELO-12)."""
    return (f"Lists to 2000: OlimpBase's transcription of FIDE's lists, by Wojciech Bartelski "
            f"({probe['olimpbase_lists']['summary']['url']}), used under its terms: free of charge, citing the source, "
            "non-commercial use only (DATA-PROBE §3); only figures derived from it are kept here"
            + (". For" if plain else " (R77). Under ruling R83, for")
            + f" the figures resting on those lists: {terms}")


def facts(sel: dict, lists: dict, rep: dict, e18: dict) -> dict:
    """The figures the report and the appendix both state, from the aggregates."""
    ch = lists["checks"]
    ob = ch["olimpbase_vs_fide_2001"]
    players = lists["players"]
    by_gap2 = sorted((p for p in players if p["best_by_gap2"]), key=lambda p: (-p["best_by_gap2"]["mean_gap2"], p["name"]))
    replayed = {r["fide_id"]: r for r in rep["players"]}
    rnd = rep["rounding"]
    early = rnd[EARLY]
    later = [e for e in ERAS if e != EARLY]
    nh = rep["negative_half_points"]
    away_lists = nh["before_july_2014_lists_with_away_from_zero"]
    thin = [(r["name"], t, cause) for r in rep["players"] for t, cause in r["thin"]]
    cal = rep["calibration"]
    shift = {k: sum(r[f"difference_outside_{k}10"] for r in rep["players"]) / len(rep["players"])
             for k in ("minus", "plus")}
    fit_year = str(int(rep["table"]["year"]) - 1)
    return {
        "n_players": len(sel["players"]), "no_id": [p["name"] for p in sel["players"] if not p["fide_id"]],
        "ob_equal": sum(x["rating_equal"] for x in ob), "ob_common": sum(x["common"] for x in ob),
        "hist_points": ch["fide_files_vs_histories"]["points"] + len(ch["fide_files_vs_histories"]["differ"]),
        "hist_equal": ch["fide_files_vs_histories"]["points"],
        "top3_equal": ch["printed_vs_computed_top3"]["equal"], "top3_dates": ch["printed_vs_computed_top3"]["dates"],
        "by_gap2": by_gap2, "replayed": replayed,
        "not_replayed": [p for p in sel["players"] if p["fide_id"] and p["fide_id"] not in replayed],
        "politeness": ch["session_politeness"],
        "window_lists": (min(p["best_by_gap2"]["lists"] for p in by_gap2 if p["best_by_gap2"]["first"] < "1980"),
                         max(p["best_by_gap2"]["lists"] for p in by_gap2 if p["best_by_gap2"]["first"] >= "2010")),
        "tie_only": [p for p in players if p["top3_only_by_a_shared_third"]],
        "printed_ties": lists["printed_ties_at_third"],
        "missing_top3": lists["lists_missing_a_top3_player"],
        "early": early, "half_n": early.get("half_negative", 0) + early.get("half_positive", 0),
        "half_up": early.get("half_negative_towards_plus_infinity", 0) + early.get("half_positive_towards_plus_infinity", 0),
        "half_away": early.get("half_negative_away_from_zero", 0) + early.get("half_positive_away_from_zero", 0),
        "neg_later_up": sum(rnd[e].get("half_negative_towards_plus_infinity", 0) for e in later),
        "neg_later_away": sum(rnd[e].get("half_negative_away_from_zero", 0) for e in later),
        "nh": nh["from_july_2014"], "away_lists": away_lists, "early_lists": nh["before_july_2014_lists"],
        "between": nh["lists_between_the_last_up_and_the_first_away"],
        "not_rounding_on": {t: sum(1 for _n, tt, c in thin if tt == t and c == NOT_ROUNDING) for t in away_lists},
        "cal": cal, "shift": shift, "pass_through": (shift["plus"] - shift["minus"]) / 20,
        "fit_year": fit_year, "fit_2750": e18["standard_by_year_band"][fit_year]["2750"],
        "fit_2850": e18["standard_by_year_band"][fit_year]["2850"],
        "rows_2750": cal["game_rows_by_band"].get("2750", 0), "rows_2850": cal["game_rows_by_band"].get("2850", 0),
        "top_2800": sorted(rep["players"], key=lambda r: (-r["game_rows_at_2800_or_more"], r["name"]))[:2],
        "left_lists": [r for r in rep["players"] if r["last_list_on_fide"] != rep["window"]["last"]],
        "fixture_cases": len(json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]),
        "terms": lists["terms"],
        # ELO10-STAT-3: from July 2000 the rank is FIDE's printed one where a copy survives, computed (ties shared) elsewhere
        "printed_from_2000": sel["lists"]["by_source"]["printed top list"],
        "computed_from_2000": len(sel["lists"]["computed_dates_from_2000_07"]),
        "late_shares": sorted({d for x in players for d in x["top3_lists_shared_third"] if d >= "2000-07"}),
        "late_tie_only": [x for x in players if x["top3_only_by_a_shared_third"]
                          and any(d >= "2000-07" for d in x["top3_lists_shared_third"])],
        # ELO10-STAT-1, ELO10-QC-2: the replayed players by how SPEC-GREATS §2 selected them
        "groups": rep["selection_groups"], "cal_groups": rep["calibration"]["by_selection"],
        "early_names": [r["name"] for r in sorted(rep["players"], key=lambda r: r["name"])
                        if r["fide_id"] in rep["selection_groups"]["to_april_2000"]["fide_ids"]]}


def slips(host: dict) -> str:
    by_tool: dict[str, list] = {}
    for g in host["gaps_under_2s"]:
        by_tool.setdefault(g["tool"], []).append(g["at"][11:19])
    return "; ".join(f"{len(v)} by the {tool} ({', '.join(v)} UTC)" for tool, v in by_tool.items())


def by_selection(f: dict) -> str:
    """How to read the calibration check, split by when SPEC-GREATS §2 chose the players (D-0018, R81 (ii), corrected
    2026-10-12: the caveat's premise, that the players' results run ahead of any forecast, held for only part of the
    sample). The words hold only while the 2025 table sits nearer the first group's results and table 8.1.2 nearer
    the others'."""
    g, cg = f["groups"], f["cal_groups"]
    early, late = cg["to_april_2000"], cg["from_july_2000"]
    a1, b1 = early["table_812"]["mean"], early["table_2025"]["mean"]
    a2, b2 = late["table_812"]["mean"], late["table_2025"]["mean"]
    if not (abs(b1) < abs(a1) and abs(a2) < abs(b2)):
        raise SystemExit("the check's reading assumes the 2025 table nearer the players chosen to April 2000 and table "
                         "8.1.2 nearer the others")
    return ("The players were chosen for reaching the top three, and the check depends on when. For the "
            f"{g['to_april_2000']['players']} who reached it only on lists to April 2000, the 2025 table sits nearer "
            f"their results ({sgn(a1, 3)} under table 8.1.2, {sgn(b1, 3)} under the 2025 table); for the "
            f"{g['from_july_2000']['players']} others, FIDE's table does ({sgn(a2, 3)} and {sgn(b2, 3)}). Players "
            "chosen for success can score above any forecast around the years they were chosen, and players past their "
            "peak can score below their ratings; this check cannot separate the two, so it cannot say which table fits "
            "the era. Only an unselected sample of the era, which FIDE's tournament reports would provide, can.")


def pooled_and_split(f: dict) -> str:
    """R81 (iv)'s sentence as corrected on 2026-10-12: the pooled order and its reversal for the players chosen on the
    lists to April 2000."""
    o, early = f["cal"]["overall"], f["cal_groups"]["to_april_2000"]
    if not (abs(o["table_812"]["mean"]) < abs(o["table_2025"]["mean"])
            and abs(early["table_2025"]["mean"]) < abs(early["table_812"]["mean"])):
        raise SystemExit("the pooled sentence assumes table 8.1.2 nearer the pooled results and the order reversed for "
                         "the players chosen to April 2000")
    return (f"Pooled over all {o['players']} players, a table fitted on games of March to December 2024 sits further "
            "from these 2008-2019 results than FIDE's own; split by when the players were chosen, the order reverses for "
            f"the {f['groups']['to_april_2000']['players']}. That is consistent with calibration changing between eras, "
            "with the table's thin support at the top, or with how the players were chosen; it proves none of them.")


def rounding_line(f: dict) -> str:
    """The appendix's and the brief's account of FIDE's rounding of half points, from the counts."""
    nh, al = f["nh"], f["away_lists"]
    exc = "; ".join(f"the list of {month(t)} ({c.get('away_from_zero', 0)} of "
                    f"{c.get('away_from_zero', 0) + c.get('towards_plus_infinity', 0)} away from zero)"
                    for t, c in al.items())
    after = ("every one" if nh["away_from_zero_before_last_up"] == 0 else "most") + \
        f" of the {f['neg_later_up'] + nh['away_from_zero_before_last_up']} negative ones from July 2014"
    later = "every one" if nh["towards_plus_infinity_after_first_away"] == 0 else "most"
    return (f"FIDE's lists rounded a period's half point towards +∞ up to the list of "
            f"{month(nh['last_list_towards_plus_infinity'])} ({f['half_up']} of {f['half_n']} half points before July "
            f"2014, {after}), except on {exc}, and away from zero from the list of "
            f"{month(nh['first_list_away_from_zero'])} ({later} of the {f['neg_later_away']} negative ones)")


# ------------------------------------------------------------------ the report
def report(sel: dict, lists: dict, rep: dict, probe: dict, e18: dict) -> list[str]:
    f = facts(sel, lists, rep, e18)
    v, rd, s, rdg, cal = rep["validation"], rep["rule_difference"], rep["summary"], rep["readings"], f["cal"]
    fide, ia = f["politeness"]["ratings.fide.com"], f["politeness"]["web.archive.org"]
    early = f["early"]
    out: list[str] = []
    p = out.append
    p("# E20 — The greats on FIDE's own data: their lists, their lead over their own era, and a replay where FIDE's "
      "calculations give every game")
    p("")
    p("Status: REVIEW — evidence for the proposal, session ELO-9, Phases 3 and 5, under `docs/specs/SPEC-GREATS_v1_0.md` "
      "(fixed before any analysis), the rulings R74 to R79 (`docs/decisions/D-0017_rulings-on-the-greats.md`) and the "
      "fixes of the session's review (`docs/review/REDTEAM_v1_0.md`, ELO-9 addendum); session ELO-10, Phases 2 and 3, "
      "under the rulings R80 to R84 and R86 (`docs/decisions/D-0018_rulings-on-elo-9-questions.md`). Generated by "
      "`analysis/e20_greats_report.py` from `analysis/aggregates/GREATS_players.json`, "
      "`analysis/aggregates/E20_greats_lists.json` and `analysis/aggregates/E20_greats_replay.json`, which "
      "`analysis/greats_select.py`, `analysis/e20_greats_lists_extract.py` and `analysis/e20_greats_replay_extract.py` "
      "write from `data/`; do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`), except the figures derived "
      "from OlimpBase's transcription of FIDE's lists, which carry ruling R83's label and are named in README's licence "
      "section. Data "
      "(`docs/research/DATA-PROBE_greats.md`): FIDE's own data, FIDE's list files from January 2001, FIDE's printed "
      "top-100 lists of July 2000 to December 2019 as the Internet Archive keeps them and FIDE's per-player rating "
      "calculations from the list of April 2008, used on the brief's instruction for analysis only, cached locally and "
      "not redistributed (FIDE reserves all rights; its written permission is to be requested, and until FIDE answers "
      "nothing changes; R84, DATA-PROBE §3). What is committed of FIDE's material: aggregates and differences, the "
      "single published ratings named by SPEC-GREATS §4 and §6 (R72, R77), and fixed samples of FIDE's calculations "
      "kept as test fixtures, quoted value by value for verification (R79, R80); the "
      "calculations' full reproduction running locally with only counts committed (R79); OlimpBase's transcription of "
      "FIDE's lists, July 1971 to 2000, under its terms, of which only derived figures are kept (R77), each carrying R83's "
      "label, and which is NOT VERIFIED before 2001 (checked against FIDE's own files of 2001 only); the rules in force "
      "as transcribed in `docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md` and "
      "`docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`. Not used: TWIC, ChessBase, Chessmetrics or any "
      "other source the probe marked as needing permission. The table applied in §5 is E18's 2025 table, "
      "PROVISIONAL-FITTED, **applied backwards, not fitted on that era**; every other parameter met here is PROVISIONAL. "
      "Every published rating committed here is a single value named by SPEC-GREATS §4 and §6 (a peak); no list and no "
      "series is committed (R72, R77).")
    p("")
    p("Corrected 2026-10-12 (session ELO-11; `docs/DECISIONS.md`, item 9): §5 reads the check of how the two tables fit "
      "these games by when the players were chosen, in place of a caveat whose premise held for only part of the sample; "
      "§5, the brief below and the proposal's appendix describe the comparison as made on the same results, which FIDE "
      "rated with table 8.1.2.")
    p("")
    p(FIXED)
    p("")
    p("**In brief.** The headlines are the lead over one's own era (§3) and the replay's validation and findings from "
      "FIDE's pages (§4); the backward replay (§5) has none (R81).")
    p("")
    mt = f["missing_top3"]
    not_in = [x for x in f["printed_ties"] if not x["selected"]]
    p(f"- **Who** (SPEC-GREATS §2, fixed before any analysis; the {f['n_players']} stand, with no change after results, "
      f"§9, R82): the {f['n_players']} players ranked 1st to 3rd on any FIDE list from July 1971 to December 2019. "
      f"{words(len(f['no_id'])).capitalize()} of them ({surnames(f['no_id'])}) have {NO_ID} and are followed by name. "
      "The selection treats ties in two ways, as §2's rule does: on the lists to April 2000, ranked by their ratings, "
      "a shared 3rd place counts, and before 1999 the ratings are multiples of five (DATA-PROBE §4), so "
      f"{words(len(f['tie_only']))} players ({surnames([x['name'] for x in f['tie_only']])}) are in only through a share "
      "of 3rd place; from July 2000 FIDE's printed order decides where a printed copy survives "
      f"({f['printed_from_2000']} of the {f['printed_from_2000'] + f['computed_from_2000']} lists), so "
      + "; ".join(f"{x['name'].split(',')[0]}, printed {ordinal(x['printed_rank'])} on the 3rd's rating in "
                  f"{month(x['list'])}, is not among the {f['n_players']}" for x in not_in)
      + f", while on the other {f['computed_from_2000']} the rank is computed and a share counts, as before 2000 ("
      + ", ".join(month(d) for d in f["late_shares"]) + ")"
      + (", though no player is in only that way. " if not f["late_tie_only"] else ". ")
      + (f"{surnames(sorted({x['absent'] for x in mt}))}, ranked 1st on the lists either side, is absent from FIDE's "
         f"lists of {' and '.join(month(x['list']) for x in mt)} as OlimpBase transcribes them (§2)." if mt else ""))
    top = f["by_gap2"][:4]
    p("- **The lead over one's own era (§3)**, the best three consecutive years by the mean gap to the list's #2: "
      + "; ".join(f"{x['name']} {sgn(x['best_by_gap2']['mean_gap2'], 1)} ({month(x['best_by_gap2']['first'])} to "
                  f"{month(x['best_by_gap2']['last'])}, {x['best_by_gap2']['lists']} lists, the best of "
                  f"{x['best_by_gap2']['windows']} windows)" for x in top)
      + f". A best window holds {f['window_lists'][0]} lists in the 1970s and up to {f['window_lists'][1]} in the "
      "2010s: the lists' frequency differs by era, and so does what a gap means.")
    p(f"- **The replay (§4)**: {rep['players_replayed']} players, April 2008 to December 2019. Given FIDE's own inputs "
      f"(the player's rating, the opponents' ratings and K), Layer 0 with the rules in force reproduces FIDE's printed "
      f"change in {v['games'] - v['game_delta_differs']:,} of {v['games']:,} games, and the published change in "
      f"{s['periods_replayed']:,} of {v['periods_with_page']:,} player-periods with a page; {s['thin_periods']:,} periods "
      "are thin (§4.3) and carry FIDE's change for both systems. In the greats' games, FIDE applied the 350-point rule "
      f"to tournaments that started up to {day(rd['last_start_with_350'])} and the 400-point rule from "
      f"{day(rd['first_start_beyond_350'])}, a date no text gives, consistent with the rules record's reading of 1 July "
      "2009.")
    p(f"- **Rounding (§4.2, R74, R80).** The 2003, 2007 and 2010 texts round the rated player's new rating, the old "
      "rating plus the change (§10.66 of 2003; §10.53 of 2007; §8.57 of 2010, which adds \"0.5 is rounded to 1\"); with "
      "0.5 rounded up, that rounds the change with 0.5 towards +∞ (the reading of Rn as the rated player's new rating, "
      "and of the 2007 text's half point, is NOT VERIFIED). " + rounding_line(f) + ". Layer 0 rounds towards +∞ on "
      "every list to October 2018 and away from zero from the list of November 2018 (R74 before July 2014, a reading "
      "changed after partial pages had been seen; R80 from July 2014, set after FIDE's pages had been read in the full "
      "replay): FIDE's own output shows towards +∞ to the list of July 2018, and the lists of August to October 2018 hold "
      "no negative half point, so the list on which FIDE's arithmetic changed, one of August to November 2018, is NOT "
      f"VERIFIED; the list of January 2009 keeps its periods thin (R80). Thin periods: {rdg['R80']['thin_periods']:,} "
      "under R80's reading, "
      f"{rdg['D-0017']['thin_periods']:,} under D-0017's, {rdg['rules record']['thin_periods']:,} under the rules "
      "record's first one.")
    p(f"- **The sources, checked before use (§1).** OlimpBase's transcription equals FIDE's own four files of 2001 in "
      f"{f['ob_equal']:,} of {f['ob_common']:,} ratings, and before 2001 it is NOT VERIFIED (it can be checked against "
      f"FIDE's files of 2001 only); FIDE's old files, as converted, equal FIDE's per-player histories in "
      f"{f['hist_equal']} of {f['hist_points']} points; the top three by §2's rule equal FIDE's printed top three on "
      f"{f['top3_equal']} of {f['top3_dates']} dates.")
    p(f"- **Politeness (§1, R75).** Two slips, both recorded when they happened and fixed: gaps under two seconds "
      f"between requests to ratings.fide.com, {slips(fide)}. Since {fide['fixed_after'][11:19]} UTC every one of the "
      f"session's requests to ratings.fide.com came at least {fide['smallest_gap_after_fix']:.0f} s after the one "
      f"before, as logged; to the Internet Archive, which refused connections at one request every four seconds, at "
      f"least {ia['smallest_gap_after_fix']:.0f} s since {ia['fixed_after'][11:19]} UTC.")
    p("- **The 2025 table applied backwards (§5), without a headline (R81).** §5 replays the same games under E18's 2025 "
      "table, **applied backwards, not fitted on that era**, with the opponents outside the set held at FIDE's ratings "
      "(R58). It measures the distance between that table and table 8.1.2 at these players' gaps, on the same results, "
      "which FIDE rated with table 8.1.2: not a correction found in these games, and not anyone's strength. Its figures, "
      "and the check of how the two tables fit these games, which depends on when the players were chosen and so cannot "
      "say which table fits the era, are in §5 only.")
    p("- **The cross-era head-to-head (§6) is not attempted**: no legitimately usable game data link the eras.")
    p("")
    p(f"For the figures above that rest on the lists to 2000 (who, the lead over one's own era, the sources): "
      f"{f['terms']}")
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
      + "; ".join(f"{month(d['list'])}: the history {d['history_minus_file']} points above the file (FIDE ID {d['id']})"
                  for d in hd["differ"]) + " |")
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
    p(credit(probe, f['terms']))
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
    p(credit(probe, f['terms']))
    p("")
    p("**Notes on the selection** (the review of session ELO-9, ELO9-STAT-3; SPEC-GREATS §2's rule unchanged, §9):")
    p("")
    p(f"- **A share of 3rd place.** {words(len(f['tie_only'])).capitalize()} players are in only because they shared "
      "3rd place, on lists before 1999 whose ratings are multiples of five (DATA-PROBE §4): "
      + "; ".join(f"{x['name']} ({', '.join(month(d) for d in x['top3_lists_shared_third'])})" for x in f["tie_only"])
      + ". From July 2000 FIDE's printed list orders players with equal ratings, and the printed rank decides: "
      + "; ".join(f"{t['name']}, printed {ordinal(t['printed_rank'])} on the rating of the printed 3rd in "
                  f"{month(t['list'])}" + ("" if t["selected"] else f", is therefore not among the {f['n_players']}")
                  for t in f["printed_ties"] if not t["selected"])
      + f"; {sum(1 for t in f['printed_ties'] if t['selected'])} other such cases concern players selected on other "
        "lists. The asymmetry is the rule's own (SPEC-GREATS §2): it ranks the lists to April 2000 by their ratings, so "
        "that a shared place counts, and takes from July 2000 the rank FIDE printed where a printed copy survives "
        f"({f['printed_from_2000']} lists), computing it, a shared place counting, on the other {f['computed_from_2000']} "
        "(shares of 3rd on " + " and ".join(month(d) for d in f["late_shares"])
        + (", though no player is in only through them" if not f["late_tie_only"] else "")
        + f"); the {f['n_players']} stand as SPEC-GREATS fixed them, with no change after results (§9; R82).")
    if mt:
        by_absent: dict[str, list] = {}
        for x in mt:
            by_absent.setdefault(x["absent"], []).append(x)
        p("- **Lists without a player ranked in the top three on the lists either side.** " + "; ".join(
            f"{a}, ranked {ordinal(xs[0]['ranked_before'])} on the list before and "
            f"{ordinal(xs[-1]['ranked_after'])} on the list after, is absent from FIDE's "
            f"list{'s' if len(xs) > 1 else ''} of {' and '.join(month(x['list']) for x in xs)} as OlimpBase transcribes "
            "them; " + "; ".join(f"on the list of {month(x['list'])} " + ", ".join(
                f"{n.split(',')[0]} is {ordinal(r)}" for n, r in x["top3_on_the_list"]) for x in xs)
            for a, xs in by_absent.items())
          + ". These lists count towards the ranks, the lists at #1 and the windows of §3 as FIDE published them.")
    p("")
    p(f"For the figures of these notes: {f['terms']}")
    p("")
    # ------------------------------------------------------------------ (ii)
    p("## 3 (ii) The lead over one's own era: the best three consecutive years")
    p("")
    p("On each list the gap to #2 is the player's rating minus the list's #2 (for the #1, the lead; for any other player "
      "zero or less) and the gap to #10 the rating minus the list's #10, #2 and #10 from the same source as the ranks "
      "(SPEC-GREATS §5). A window holds every list from its first to before 36 months later and counts only if the player "
      "is ranked on each; windows reaching past December 2019 do not count. Sorted by the mean gap to #2 in the best "
      "window; beside it, how many windows the best was chosen from and the median of their means (ELO9-STAT-5).")
    p("")
    p(FIXED)
    p("")
    p("| # | name | best window by the gap to #2 | lists | mean gap to #2 | mean gap to #10 | at #1 | windows | median "
      "window's mean gap to #2 | best window by the gap to #10 | its mean gap to #10 |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, x in enumerate(f["by_gap2"], 1):
        b, c = x["best_by_gap2"], x["best_by_gap10"]
        p(f"| {i} | {x['name']} | {month(b['first'])} – {month(b['last'])} | {b['lists']} | {sgn(b['mean_gap2'], 1)} | "
          f"{sgn(b['mean_gap10'], 1)} | {b['lists_at_1']} | {b['windows']} | {sgn(b['median_window_mean'], 1)} | "
          f"{month(c['first'])} – {month(c['last'])} | {sgn(c['mean_gap10'], 1)} |")
    p("")
    p(credit(probe, f['terms']))
    p("")
    p("A mean gap measures a lead over contemporaries only. A window of the 1970s holds three or four lists, one of the "
      "2010s thirty-six; before 1999 the ratings are multiples of five (DATA-PROBE §4), so one list moves a short "
      "window's mean by a large step; and a best window is a maximum over windows whose number differs by player, a "
      "maximum over many overlapping windows sitting further above their median. The spread of the top ten changes with "
      "the era and with the size of the list. No row is a comparison across eras (§6).")
    p("")
    # ------------------------------------------------------------------ (iii)
    p("## 4 (iii) The replay, April 2008 to December 2019: validation first")
    p("")
    p(f"**What is replayed** (SPEC-GREATS §6). The {rep['players_replayed']} players of §2 with a standard rating period "
      "on FIDE's calculations index between the lists of April 2008, the first whose calculations give every game "
      "(DATA-PROBE §2.4), and December 2019, replayed together list by list from their published ratings of January 2008; "
      f"{rep['pages']['read']:,} of FIDE's per-player pages, {v['games']:,} games in {v['tournaments']:,} tournaments. "
      f"Not replayed: {surnames([x['name'] for x in f['not_replayed']])}, who have no standard rating period on FIDE's "
      f"calculations index in the window, and {surnames(f['no_id'])}, who have {NO_ID}. The replayed set is SPEC-GREATS "
      f"§2's selection, which rests on OlimpBase's transcription for {f['groups']['to_april_2000']['players']} of the "
      f"{rep['players_replayed']}: {surnames(f['early_names'])}, ranked 1st to 3rd only on lists to April 2000, whose "
      "ranks §2 computes on that transcription; they hold "
      f"{f['groups']['to_april_2000']['periods_replayed']:,} of the {s['periods_replayed']:,} player-periods replayed, "
      f"{f['groups']['to_april_2000']['games_replayed']:,} of the {s['games_replayed']:,} games and "
      f"{f['groups']['to_april_2000']['thin_periods']} of the {s['thin_periods']} thin periods, and the other "
      f"{f['groups']['from_july_2000']['players']} ranked 1st to 3rd on a list from July 2000. Opponents outside the set at "
      "the ratings FIDE's pages print, or, where a page prints a capped value, at the rating of the same name on the list "
      "in force (R58's approximation); opponents inside the set at their replayed ratings. The reproduction runs locally "
      f"from the cached pages; only its counts are committed (R79), and a sample of {words(f['fixture_cases'])} cases chosen "
      "by a fixed rule is kept as test fixtures (`tests/fixtures/fide_greats/`; R79, and R80 for two of them).")
    p("")
    p(f"For the selection's figures of this paragraph (who is in the set, and its groups): {f['terms']}")
    p("")
    p("### 4.1 Layer 0 against FIDE")
    p("")
    p("Every check below takes FIDE's own inputs from its pages (the player's rating, the opponents' ratings and K): it "
      "tests the score table, the rating-difference rule, K's rule and the rounding, not the ratings themselves.")
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
    p("**The 350- and 400-point rules.** On every game of the greats whose gap exceeds 350 points and whose opponent's "
      "rating is known (the rating FIDE printed, or the one found on the list in force where FIDE printed a capped "
      "value), the rule FIDE applied, by the version in force at the tournament's start as `src/layer0_greats/` reads "
      "it:")
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
    p(f"In the greats' games, the last tournament FIDE capped at 350 points started on {day(rd['last_start_with_350'])}; "
      f"the first in which it used a gap beyond 350 started on {day(rd['first_start_beyond_350'])}. No text of the "
      "regulations gives the date (the rules record, §5). The reading of the rules record (tournaments starting from 1 "
      "July 2009) agrees with FIDE's pages to within those dates, and the "
      "marks show how the pages print a capped rating: as the player's own minus 350, unmarked, before July 2009, and "
      "with FIDE's asterisk after it.")
    p("")
    p("**Rounding (R74, R80).** The 2003, 2007 and 2010 texts round the rated player's new rating, the old rating plus "
      "the change: \"Rn is rounded off to the nearest 1 or 0\" (§10.66 of 2003; §10.53 of 2007) and \"R n is rounded off "
      "to the nearest 1 or 0, 0.5 is rounded to 1\" (§8.57 of 2010) (the rules record, §5); the reading of Rn as the "
      "rated player's new rating, and of the 2007 text's half point, is NOT VERIFIED. With a whole old rating, a new "
      "rating rounded with 0.5 up rounds the change with 0.5 towards +∞. The 2014 and 2017 texts round the change, in the "
      "same words: \"0.5 is rounded up (whether the change is positive or negative)\" (§8.57 of 2017, "
      "`docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`; §8.57 of 2014, the rules record); the text of 2022 "
      "says \"0.5 is rounded away from zero\" (§8.3.4, the same archive record). The rules record, written before "
      "FIDE's pages were seen, described the clauses of 2007 and 2010 as rounding a new player's rating and read every "
      "list as E17 found the words of 2017 applied, 0.5 away from zero; the review of session ELO-9 corrected the "
      "description (ELO9-QC-1). FIDE's pages contradicted that reading: on the pages then fetched, 0.5 towards +∞ "
      "reproduced 44 of 49 half-point periods and away from zero 27. Ruling R74 "
      "(`docs/decisions/D-0017_rulings-on-the-greats.md`) adopted towards +∞ for every list published before July 2014 "
      "(SPEC-L0 §11, finding F-H09), after those partial pages and before the full replay, and D-0017 kept away from "
      "zero from July 2014. Ruling R80 (`docs/decisions/D-0018_rulings-on-elo-9-questions.md`; SPEC-L0 §11, finding "
      "F-H10) extends towards +∞ to every list to October 2018 and rounds away from zero from the list of November 2018, "
      "as FIDE's lists show below; it was set after FIDE's pages had been read in the full replay. On every period with "
      "a page and no gap in FIDE's files, by the text in force when the list was published, the 2017 clause split at "
      "R80's switch:")
    p("")
    p(FIXED)
    p("")
    p("| lists | periods | reproduced as Layer 0 rounds (R80) | rounding 0.5 away from zero | rounding 0.5 towards +∞ "
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
    exc, exc_exact = early.get("half_not_towards_plus_infinity", 0), early.get("half_not_towards_plus_infinity_float_exact", 0)
    al = f["away_lists"]
    nh = f["nh"]
    p(f"Once per period is the rule FIDE's lists follow. On the lists before July 2014, of {f['half_n']} periods whose "
      f"sum ends in exactly a half point, towards +∞ reproduces {f['half_up']} and away from zero {f['half_away']}; the "
      f"two readings agree on positive half points and differ on the {early.get('half_negative', 0)} negative ones. Of "
      f"the {f['early_lists']} lists before July 2014 that hold a negative half point, every one went towards +∞ on all "
      f"but {words(len(al))}: "
      + "; ".join(f"on the list of {month(t)}, {c.get('away_from_zero', 0)} of "
                  f"{c.get('away_from_zero', 0) + c.get('towards_plus_infinity', 0)} went away from zero, and the same "
                  f"list holds {f['not_rounding_on'][t]} period{'s' if f['not_rounding_on'][t] != 1 else ''} whose "
                  "published change is not a rounding of its sum at all" for t, c in al.items())
      + "; the list gets no exception of its own (R80): those periods stay thin, a finding (§4.3). "
      + (f"Floating-point sums do not explain all of the {exc} exceptions to towards +∞: {exc_exact} of them are half "
         "points that a binary floating-point sum gives exactly, game by game and tournament by tournament, so no "
         "floating-point error can have tipped those. " if exc_exact else
         f"None of the {exc} exceptions to towards +∞ is a half point a binary floating-point sum gives exactly, so the "
         "floating-point sums FIDE's software may use could explain them. ")
      + f"From the list of July 2014 FIDE's lists rounded every negative half point towards +∞ up to the list of "
        f"{month(nh['last_list_towards_plus_infinity'])} ({f['neg_later_up']}) and every one away from zero from the list "
        f"of {month(nh['first_list_away_from_zero'])} ({f['neg_later_away']}), as E17 found on the lists from February "
        "2020 (SPEC-L0 F-H07) and before the text of 2022 said \"away from zero\": the same words of 2014 and 2017 were "
        "applied two ways, FIDE's arithmetic changing between those two lists while the words, as far as the texts "
        "transcribed here show, did not (the text in force in 2018 is NOT VERIFIED: the repository transcribes the 2014 "
        "text and the 2017 text as amended from 1 February 2021). The lists "
        f"between them, {' and '.join(', '.join(month(b['list']) for b in f['between']).rsplit(', ', 1))}, hold "
        f"{sum(b['periods'] for b in f['between'])} replayed periods and "
        + ("none" if not sum(b["negative_half_points"] for b in f["between"]) else
           str(sum(b["negative_half_points"] for b in f["between"])))
        + " whose sum ends in a negative half point, so FIDE's output does not show on which list from "
        f"{month(f['between'][0]['list'])} to {month(nh['first_list_away_from_zero'])} the change took effect: that list "
        "is NOT VERIFIED, and R80's boundary, the list of November 2018, gives the same counts as any of them. Ruling R80 "
        "adopts what FIDE's lists show, towards +∞ to the list of July 2018 and away from zero from November 2018, and "
        "reads the lists of August to October 2018, which hold no such period, as the first, so that Layer 0 reproduces "
        f"all {f['neg_later_up'] + f['neg_later_away']} of these periods. By the year of the list, every period whose "
        "sum ended in a negative half point:")
    p("")
    p(FIXED)
    p("")
    p("| year of the list | towards +∞ | away from zero | neither |")
    p("|---|---|---|---|")
    for y, c in rep["negative_half_points"]["by_year"].items():
        p(f"| {y} | {c.get('towards_plus_infinity', 0)} | {c.get('away_from_zero', 0)} | {c.get('neither', 0)} |")
    p("")
    p("**The readings and the thin periods.** The replay under each reading of the rounding, for Layer 0 and rung 2 "
      "alike: R80's, adopted, which §5 uses; D-0017's beside it, as R80 asks; the rules record's first, as R74 asks; and, "
      "for information only, towards +∞ on every list (D-0017 reading 2). The difference under the 2025 table on the "
      "last list, under each reading, is in §5 (R80 (iv), R81 (iii)):")
    p("")
    p(FIXED)
    p("")
    p("| reading | thin periods | player-periods replayed | games replayed |")
    p("|---|---|---|---|")
    for key in READINGS:
        x = rdg[key]
        p(f"| {READING_NAMES[key]} | {x['thin_periods']:,} | {x['periods_replayed']:,} | {x['games_replayed']:,} |")
    p("")
    p("Periods that no reading reproduces stay thin and carry FIDE's change (R74). The comparison of §5 uses R80's "
      "reading.")
    p("")
    p("### 4.3 Thin periods")
    p("")
    p("A period is thin when FIDE's page is missing, or when Layer 0 does not reproduce its published change; both "
      "systems then take FIDE's published change, so that the difference between them is carried unchanged through it "
      "(SPEC-GREATS §6). Where FIDE's own list file of a date lacks a player of the set, the periods to the next file "
      "that carries the player are checked together against it. Under R80's reading:")
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
      "game carries one; E17 found them 98.4 % in agreement with the broadcast archive in 2020–2026, and before 2020 "
      "they are NOT VERIFIED); K by FIDE's K rules on each system's own rating (R61: the rules change K in "
      f"{rep['k_departs_from_fide']['r2']} tournaments of the method); each period's change rounded as Layer 0 rounds it "
      "(R80). "
      "Opponents outside the set are held at FIDE's ratings (R58); a replay of the whole pool, in which they would move "
      "too, needs FIDE's tournament reports. The difference is rung 2 minus Layer 0 on each player's last list in the "
      "window; Layer 0 equals FIDE's published rating on every list it reproduces. What the comparison measures (R81): "
      "the distance between the 2025 table and table 8.1.2 at these players' gaps, on the same results, which FIDE rated "
      "with table 8.1.2. Its figures appear here only, and no headline of E20 or of the proposal's appendix carries them.")
    p("")
    p(f"**First, how the table fits these games** (the review of session ELO-9, ELO9-STAT-1). On every game of FIDE's "
      f"{rep['pages']['read']:,} pages, the thin periods' included, in which the player of the set was the favourite by "
      f"{cal['gaps'][0]} to {cal['gaps'][1]} points, at FIDE's own "
      "ratings (the opponent's found on the list in force where FIDE printed a capped value), the favourite's mean "
      "residual, score minus expectation, under table 8.1.2 and under the 2025 table with FIDE's colour marks, with 95 % "
      "intervals clustered over the players:")
    p("")
    p(FIXED)
    p("")
    p("| level of the game | games | players | table 8.1.2 | the 2025 table |")
    p("|---|---|---|---|---|")
    for mid, x in cal["by_band"].items():
        p(f"| {BAND.get(mid, mid)} | {x['games']:,} | {x['players']} | {ci(x['table_812'])} | {ci(x['table_2025'])} |")
    o = cal["overall"]
    p(f"| every level | {o['games']:,} | {o['players']} | {ci(o['table_812'])} | {ci(o['table_2025'])} |")
    p("")
    g, cg = f["groups"], f["cal_groups"]
    p("The same check and the difference on the last list, by how SPEC-GREATS §2 selected the players (the review of "
      "session ELO-10, ELO10-STAT-1): ranked 1st to 3rd only on the lists to April 2000, long before the window, or on a "
      "list from July 2000:")
    p("")
    p(FIXED)
    p("")
    p("| players | games | table 8.1.2 | the 2025 table | difference, last list (mean) |")
    p("|---|---|---|---|---|")
    p(f"| the {g['to_april_2000']['players']} ranked 1st to 3rd only on the lists to April 2000 | "
      f"{cg['to_april_2000']['games']:,} | {ci(cg['to_april_2000']['table_812'])} | {ci(cg['to_april_2000']['table_2025'])} "
      f"| {sgn(g['to_april_2000']['mean_difference'], 2)} |")
    p(f"| the {g['from_july_2000']['players']} ranked 1st to 3rd on a list from July 2000 | "
      f"{cg['from_july_2000']['games']:,} | {ci(cg['from_july_2000']['table_812'])} | "
      f"{ci(cg['from_july_2000']['table_2025'])} | {sgn(g['from_july_2000']['mean_difference'], 2)} |")
    p(f"| the {o['players']} together | {o['games']:,} | {ci(o['table_812'])} | {ci(o['table_2025'])} | "
      f"{sgn(s['mean_difference'], 2)} |")
    p("")
    p(by_selection(f))
    p("")
    p(f"For the groups, which rest on the lists to 2000: {f['terms']}")
    p("")
    p("The difference below therefore measures how far the 2025 table sits from table 8.1.2 at the gaps these players "
      "played, applied to the same results, which FIDE rated with table 8.1.2; it is not a correction the table finds in "
      f"these games. {pooled_and_split(f)} The table's fit window lies in {f['fit_year']}, whose standard games "
      f"with both players' FIDE IDs number {f['fit_2750']:,} at levels of 2700–2799 and {f['fit_2850']:,} at 2800 or "
      f"more [E18 §1]; the replay holds {f['rows_2750']:,} and {f['rows_2850']:,} game rows at those levels by FIDE's "
      f"ratings. Of the {f['rows_2850']:,} at 2800 or more, "
      + " and ".join(f"{r['game_rows_at_2800_or_more']} are {r['name']}'s ({r['game_rows']:,} rows in all)"
                     for r in f["top_2800"])
      + ": their rows rest most on the band where the table has least support. No estimate of the table's own error "
        "at the top, such as R59 gave E19, is added: its correction at 2800 and above rests on a handful of games (E19 "
        f"§3) and would move the {f['rows_2850']:,} game rows the replay holds at those levels (R81).")
    p("")
    p(FIXED)
    p("")
    p("| # | name | FIDE ID | periods replayed | games | game rows at 2800 or more | thin periods | difference, last list "
      "| the table's effect | colour's effect | outside opponents −10 / +10 | highest under FIDE's rules, 2008–2019 | "
      "highest under the 2025 table |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows = sorted(rep["players"], key=lambda r: (-r["highest_layer0"]["rating"], r["name"]))
    for i, r in enumerate(rows, 1):
        h0, h2 = r["highest_layer0"], r["highest_rung2"]
        last = "" if r["last_list_on_fide"] == rep["window"]["last"] else f" ({month(r['last_list_on_fide'])})"
        p(f"| {i} | {r['name']} | {r['fide_id']} | {r['periods_replayed']} | {r['games_replayed']:,} | "
          f"{r['game_rows_at_2800_or_more']} | {r['thin_periods']} | {sgn(r['difference'])}{last} | "
          f"{sgn(r['table_effect'])} | {sgn(r['colour_effect'])} | {sgn(r['difference_outside_minus10'])} / "
          f"{sgn(r['difference_outside_plus10'])} | {h0['rating']} ({month(h0['lists'][0])}) | {h2['rating']} "
          f"({month(h2['lists'][0])}) |")
    p("")
    p(f"On average {sgn(s['mean_difference'], 1)} points on each player's last list (the table's effect "
      f"{sgn(s['mean_table_effect'], 1)}, colour's {sgn(s['mean_colour_effect'], 1)}); with every opponent outside the "
      f"set 10 points lower or higher, {sgn(f['shift']['minus'], 1)} and {sgn(f['shift']['plus'], 1)}, "
      f"{num(f['pass_through'], 2)} points of difference per point of the outside opponents' ratings. "
      + (" ".join(f"{r['name']} is on no list of the window after {month(r['last_list_on_fide'])}; the difference "
                  "is the one carried from the player's last period." for r in f["left_lists"]) + " " if f["left_lists"]
         else "")
      + f"In the {v['cap_unresolved']} capped games whose opponent's rating was not found on the list in force, rung 2, "
      "which has no 400-point rule, reads the capped value. The table was fitted on games of 2024, after every game "
      "replayed here: the difference says what today's table would have made of the same results, not what a table "
      "fitted on that era would have.")
    p("")
    p("**The difference under each reading of the rounding** (R80 (iv); the method uses R80's), on each player's last "
      "list:")
    p("")
    p(FIXED)
    p("")
    p("| reading | mean difference, last list | range |")
    p("|---|---|---|")
    for key in READINGS:
        x = rdg[key]
        p(f"| {READING_NAMES[key]} | {sgn(x['mean_difference'], 2)} | {sgn(x['min_difference'])} to "
          f"{sgn(x['max_difference'])} |")
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
      "own games from 2008 only. With permission from TWIC, ChessBase or Chessmetrics the full study becomes possible: "
      "the replay could extend to the games those collections hold. FIDE's own calculations, against which a replay is "
      "checked, exist only from 2008; those collections do not record which games FIDE rated; and any comparison across "
      "eras would rest on a model's assumptions, not on the ratings themselves.")
    p("")
    p("## 7 Limits")
    p("")
    p("- The lists before 2001 are OlimpBase's transcription of FIDE's lists, NOT VERIFIED before 2001 (checked against "
      "FIDE's own files of 2001 only); the ranks before July 2000 are computed by SPEC-GREATS §2's rule, not printed by "
      f"FIDE; before 1999 the ratings are multiples of five, so ties for 3rd bring in {words(len(f['tie_only']))} players "
      "(§2), while from July 2000 FIDE's printed order breaks ties where a printed copy survives (R82), a shared place "
      f"still counting on the {f['computed_from_2000']} lists computed without one; FIDE's lists of 1994, as OlimpBase "
      "transcribes them, lack the player ranked 1st on the lists either side (§2).")
    p("- The replay covers the lists of April 2008 to December 2019 only, the window in which FIDE's calculations give "
      "every game; most of the greats' careers lie outside it, and the greats of the 1970s and 1980s are not replayed.")
    p(f"- Opponents outside the set keep FIDE's ratings (R58's approximation): the mean difference moves by "
      f"{num(f['pass_through'], 2)} points per point of theirs (§5), and a replay of the whole pool would move them too.")
    p("- The colour term uses FIDE's colour marks, NOT VERIFIED before 2020 (E17 checked them against the broadcast "
      "archive from 2020 only).")
    p("- The 2025 table is applied backwards to an era it was not fitted on, and how the two tables fit these games "
      "depends on when the players were chosen: table 8.1.2 sits nearer the results of the "
      f"{f['groups']['from_july_2000']['players']} chosen on a list from July 2000, the 2025 table nearer those of the "
      f"{f['groups']['to_april_2000']['players']} chosen only on the lists to April 2000; the check cannot separate "
      "selection for success from players past their peak, so it cannot say which table fits the era (§5). The replay "
      "shows the rule's effect on the same results, not a measure of anyone's strength, and not a comparison across eras; "
      "its fit window holds few games at the top levels where the greats play.")
    p("- Layer 0's rounding follows FIDE's output, towards +∞ to the list of July 2018, which R80 extends to October "
      "2018, and away from zero from November 2018 (R74 before July 2014, a reading changed after partial pages were "
      "seen; R80 from July 2014, set after the full replay had been read): the reading of the texts' Rn as the rated "
      "player's new rating and of the 2007 text's half point, the text in force in 2018 and the list on which FIDE's "
      "arithmetic changed that year are NOT VERIFIED; the list of January 2009, which rounded its negative half points "
      "away from zero, keeps those periods thin (§4.2, §4.3).")
    p("")
    p(f"For the figures of the first limit: {f['terms']}")
    return out


# ------------------------------------------------------------------ the proposal's appendix
def appendix(sel: dict, lists: dict, rep: dict, probe: dict, e18: dict) -> list[str]:
    """The proposal's appendix 'The greats, on FIDE's own data': E20 in one page, every number from the aggregates."""
    f = facts(sel, lists, rep, e18)
    v, rd, s, rdg, cal = rep["validation"], rep["rule_difference"], rep["summary"], rep["readings"], f["cal"]
    out: list[str] = []
    q = out.append
    q("## Appendix I The greats, on FIDE's own data")
    q("")
    q("Outside the body's word count. From E20 (`docs/evidence/E20_greats.md`), under SPEC-GREATS v1.0, fixed before "
      "any analysis, and the later decisions E20 lists. Its headlines are the lead over one's own era and the replay's "
      "validation and findings from FIDE's pages; the backward replay has none. Every table here, as in E20, reads:")
    q("")
    q(FIXED)
    q("")
    q("**The data, and their limits.** The study uses FIDE's own data, for analysis only and not redistributed (FIDE "
      "reserves all rights; its written permission is to be requested, and until FIDE answers nothing changes; "
      "what is committed of it is aggregates and differences, single published ratings, and fixed samples of FIDE's "
      "calculations kept as test fixtures and quoted value by value for verification), and OlimpBase's transcription "
      "of FIDE's lists under its terms, "
      "NOT VERIFIED before 2001 (checked against FIDE's own files of 2001 only) (`docs/research/DATA-PROBE_greats.md`): "
      "FIDE's lists (as OlimpBase transcribes them to 2000, FIDE's own files since 2001), FIDE's printed top lists of "
      "2000–2019 as the Internet Archive keeps them, and FIDE's per-player rating calculations, which give every game only "
      "from the list of April 2008. **TWIC and Chessmetrics were not used**, nor ChessBase or any other game collection "
      "whose terms need permission. So the greats' lists and their lead over their own era can be shown from 1971, but "
      "their games can be replayed only from 2008, and no comparison across eras is possible.")
    q("")
    first_list = min(x["first_top3"] for x in sel["players"])
    last_join = max(x["first_top3"] for x in sel["players"])
    not_in = [x for x in f["printed_ties"] if not x["selected"]]
    q(f"**Who.** The {f['n_players']} players ranked 1st to 3rd on any FIDE list from July 1971 to December 2019 "
      f"[E20 §2], from {surnames([x['name'] for x in sel['players'] if x['first_top3'] == first_list])} on the first "
      f"list ({month(first_list)}) to "
      f"{surnames([x['name'] for x in sel['players'] if x['first_top3'] == last_join])}, the last to join "
      f"({month(last_join)}); they stand as SPEC-GREATS fixed them, with no change after results. Its rule treats "
      "ties in two ways: on the lists to April 2000, ranked by their ratings, a shared 3rd place counts, and before 1999 "
      f"the ratings are multiples of five, so {words(len(f['tie_only']))} players are in only that way "
      f"({surnames([x['name'] for x in f['tie_only']])}); from July 2000 FIDE's printed order decides where a printed "
      f"copy survives ({f['printed_from_2000']} of the {f['printed_from_2000'] + f['computed_from_2000']} lists), so "
      + "; ".join(f"{x['name'].split(',')[0]}, printed {ordinal(x['printed_rank'])} on the 3rd's rating in "
                  f"{month(x['list'])}, is not among the {f['n_players']}" for x in not_in)
      + f", while on the other {f['computed_from_2000']} the rank is computed and a share counts, as before 2000 ("
      + ", ".join(month(d) for d in f["late_shares"]) + ")"
      + (", though no player is in only that way." if not f["late_tie_only"] else "."))
    q("")
    q(f"For the figures of this paragraph: {f['terms']}")
    q("")
    q("**Their lead over their own era** [E20 §3]: the best three consecutive years by the mean gap to the list's #2, "
      "the six largest, each the best of the player's qualifying windows.")
    q("")
    q(FIXED)
    q("")
    q("| name | best three years | lists | mean gap to #2 | mean gap to #10 | windows |")
    q("|---|---|---|---|---|---|")
    for x in f["by_gap2"][:6]:
        b = x["best_by_gap2"]
        q(f"| {x['name']} | {month(b['first'])} – {month(b['last'])} | {b['lists']} | {sgn(b['mean_gap2'], 1)} | "
          f"{sgn(b['mean_gap10'], 1)} | {b['windows']} |")
    q("")
    q(credit(probe, f['terms'], plain=True))
    q("")
    q("A lead over one's contemporaries, on lists whose frequency and spread change with the era, and a maximum over a "
      "different number of windows for each player: not a ranking across eras.")
    q("")
    q(f"**The replay, 2008–2019** [E20 §4]. Of the {f['n_players']}, {rep['players_replayed']} have a standard rating "
      "period on FIDE's calculations index between the lists of April 2008 and December 2019; "
      f"{f['groups']['to_april_2000']['players']} of them are in the selection only through their ranks on the lists "
      "to April 2000, computed on OlimpBase's transcription. Given FIDE's own inputs, Layer 0 with the rules in force "
      "at each date reproduces FIDE's printed change "
      f"in {v['games'] - v['game_delta_differs']:,} of {v['games']:,} games; {s['thin_periods']:,} player-periods are "
      "thin and carry FIDE's change. In the greats' games FIDE applied the 350-point rule to tournaments starting up to "
      f"{day(rd['last_start_with_350'])} and the 400-point rule from {day(rd['first_start_beyond_350'])}, a date no "
      "regulation text we read gives. " + rounding_line(f) + "; Layer 0 rounds towards +∞ to October 2018 and away from zero from November 2018 "
      "(readings set after FIDE's pages had been seen: FIDE's own output shows towards +∞ to the list of "
      "July 2018, and the list of the change is NOT VERIFIED), and the list of January 2009 keeps its periods thin.")
    q("")
    q(f"For the selection's figures of this paragraph (the {f['n_players']}, the {rep['players_replayed']} and the "
      f"{f['groups']['to_april_2000']['players']}): {f['terms']}")
    q("")
    q("E20 §5 also replays the same games under E18's 2025 table, **applied backwards, not fitted on that era**, with "
      f"every opponent outside the {rep['players_replayed']} held at FIDE's rating. It measures the distance "
      "between that table and table 8.1.2 at these players' gaps, on the same results, which FIDE rated with table "
      "8.1.2, not anyone's strength; its figures, and the check of how the two tables fit these games, which cannot say "
      "which table fits the era, are in E20 §5 only.")
    q("")
    q("**Earlier studies across eras.** Elo, in his book of 1978, estimated past strengths by fitting a smooth curve to "
      "estimates from five-year periods, as TrueSkill Through Time describes it [VP 18] [VP 19]; Sonas's Chessmetrics "
      "carries historical ratings back to 1843 [VP 17]; TrueSkill Through Time smoothed the skills of players over 150 "
      "years of games from ChessBase's database and compared them across time [VP 18]. This appendix adds FIDE's own data "
      "and calculations, replayed: the lists since 1971 and, from 2008, FIDE's own calculation of every game, reproduced "
      "before any other table is applied. It does not attempt what those studies did, a measure of strength across eras.")
    q("")
    q("**What permission would add.** With written permission from TWIC, ChessBase or Chessmetrics, the full study "
      "becomes possible: the replay could extend to the games those collections hold, across the greats' careers. FIDE's "
      "own calculations, against which a replay is checked, exist only from 2008; those collections do not record which "
      "games FIDE rated; and any comparison across eras would rest on a model's assumptions. Permission has not been "
      "sought.")
    q("")
    return out


def main() -> int:
    sel, lists, rep, probe, e18 = load()
    lines = (appendix(sel, lists, rep, probe, e18) if "--appendix" in sys.argv[1:] else
             report(sel, lists, rep, probe, e18))
    sys.stdout.write("\n".join(lines).rstrip("\n") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
