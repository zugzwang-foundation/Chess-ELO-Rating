#!/usr/bin/env python3
"""E21 report: sourcing — the cheap sources, and a pilot of FIDE's per-player game pages that decides the big fetch
(session ELO-D1). Writes docs/evidence/E21_sourcing.md from analysis/aggregates/E20_greats_replay_by_list.json,
E21_lists.json and E21_pilot.json (analysis/e20_greats_replay_by_list_extract.py, analysis/e21_lists_extract.py and
analysis/e21_pilot_extract.py, which need data/); with --spec, docs/specs/SPEC-SOURCING_v1_1.md, the plan of session
ELO-D2's club-level sample, from analysis/aggregates/E21_club_plan.json (analysis/e21_club_plan_extract.py). Sonas's findings of §4 are quoted from his reports, by page, as the session read
them (docs/research/SOURCES_v1_0.md); Ghita's book is cited by page and paraphrased. Every analysis here was chosen
after its data had been seen and is labelled so (docs/DECISIONS.md, item 32). Python standard library only;
deterministic.

Usage: python3 analysis/e21_sourcing_report.py > docs/evidence/E21_sourcing.md
       python3 analysis/e21_sourcing_report.py --spec > docs/specs/SPEC-SOURCING_v1_1.md
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates"
FIXED = "*Under this rule, with the same results — not anyone's true strength.*"
AFTER = "Decided after seeing the data (`docs/DECISIONS.md`, item 32)."
PILOT = "**Pilot.**"
LEVELS = ("1400-1599", "1600-1799", "1800-1999", "2000-2199", "2200-2399", "2400+")
AGES = ("<12", "12-15", "16-19", "20-24", "25-45", "46-60", ">60")
AGE_NAME = {"<12": "under 12", "12-15": "12–15", "16-19": "16–19", "20-24": "20–24", "25-45": "25–45",
            "46-60": "46–60", ">60": "over 60"}
GAPS = ("0-49", "50-99", "100-149", "150-199", "200-299", "300-399")
SECONDS_PER_DAY = 86400

# Sonas's reports, as read on 14 October 2026 (docs/research/SOURCES_v1_0.md): the findings that bear on the four
# problems, by page, with at most short quotations; "cited" says whether the proposal already cites the finding.
P23, S23, F24 = "Sonas 2023 (proposal)", "Sonas 2023 (supplemental)", "Sonas 2024 (final)"
FINDINGS = (
    ("Countries priced differently", "—", "—",
     "None of the three reports measures federations. The supplemental report quotes, among community comments, "
     "Ghita's suggestion that FIDE show URS beside each player's rating for 2023–2024 (p. 4).",
     "the comment, as prior work [VP 4]"),
    ("White moves first", "—", "—", "None of the three reports measures colour.", "—"),
    ("The top drains", P23, "p. 6",
     "On more than 13 million standard games of 2008–2023, favourites score below table 8.1.2 at every rating "
     "advantage, and each period's curve is shallower than the one before: \"rating favorites are consistently "
     "underperforming their ratings\".", "yes [VP 3]"),
    ("The top drains", P23, "p. 9",
     "The deflation \"has crept upward through the master level\" and begun to reach grandmasters, who mostly play "
     "each other and so are reached last; players rated 2400–2499 and 2500 or more already under-perform against "
     "opponents near 2000.", "in part [VP 3]"),
    ("The top drains", S23, "pp. 17, 19",
     "Players rated 2200 or more fewer on every January list since 2018; players rated 2600 or more from 269 in "
     "November 2020 to 234 in October 2023, about one a month.", "no"),
    ("The top drains", F24, "p. 2",
     "Over the past five years' standard games, a favourite by 200 points scored 68 % where the table expects 76 %; at "
     "K = 20, ten such games cost 15 to 20 points.", "no"),
    ("The top drains", S23, "pp. 30–42; final pp. 14–17",
     "The 400-point rule: favourites rated below 2400 have scored 92 % or less in games more than 400 points apart, "
     "so the rule should apply to every such game, as before 2022; FIDE's regulations from 1 March 2024 carry the "
     "rule [V 1].",
     "yes [VP 4] [VP 5]"),
    ("Fast improvers rated behind their strength", P23, "p. 3",
     "Lowering the rating floor brought in young players with very low first ratings \"during the stage of their "
     "career when their chess skill is improving most rapidly\", producing a strong deflationary pressure; the higher "
     "K of 2014 was not enough.", "yes [VP 3]"),
    ("Fast improvers rated behind their strength", S23, "pp. 6–8",
     "The compression is not meant to keep up with improving juniors; to separate a spread-out scale from juniors "
     "improving and older players declining, Sonas measures players aged 20 to 38 only.", "no"),
    ("Fast improvers rated behind their strength", S23, "p. 4",
     "Community suggestions quoted: junior additions as Chess Scotland applies them (Bryson); junior K cut to 32 or 30 "
     "(Ghita); K = 5 for adults against players under 18 (Compton); K falling to 10 at 2600 rather than 2400 "
     "(Arkell).", "Bryson's, yes [VP 4]"),
    ("Fast improvers rated behind their strength", F24, "pp. 10–12",
     "Sonas holds that new players are under-rated the moment they are first rated, not only improving: in "
     "2010–2013 a first rating of "
     "1100–1199 gained 22 points over the next 15 games on average, while first ratings of 2000 or more lost points; "
     "\"the very high initial ratings were probably (on average) too high\". Two hypothetical draws pull first "
     "ratings to the centre.", "no"),
    ("Fast improvers rated behind their strength", F24, "p. 14",
     "The weak point left: K = 40 juniors exchanging points mostly with each other; junior additions may be needed.",
     "yes [VP 5]"),
)
# The Qualification Commission's summary of its Congress meeting of 23 September 2026, posted 12 October 2026
# (qc.fide.com), the decisions that bear on the four problems, quoted.
QC_2026 = (("\"Proposal to allow K=40 for non junior players – Rejected\"", "fast improvers"),
           ("\"Proposal to allow federations to create 'starting ratings' through tournaments – Deferred to allow to "
            "further study\"", "fast improvers; countries"),
           ("\"Proposal to have 60m+30s the minimum time control for all games involving players rated above 1800 on "
            "the Standard Rating List (but not valid for norms) – Accepted\"", "who is in the standard pool"),
           ("\"Proposal to change reporting requirements for standard (non team) events from every 30 days to every "
            "60 days – Accepted (subject to agreement from FIDE Ratings Office)\"", "how fast ratings follow"))


def load(name: str) -> dict:
    return json.loads((AGG / name).read_text(encoding="utf-8"))


def n(x: int | float) -> str:
    return f"{x:,.0f}"


def sgn(x: float, d: int = 1) -> str:
    s = f"{x:+.{d}f}"
    return ("+" + s[1:] if float(s) == 0 else s).replace("-", "−")


def num(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace("-", "−")


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f} %"


def ci(s: dict, d: int = 1, scale: float = 1.0) -> str:
    return f"{sgn(s['mean'] * scale, d)} ({sgn(s['lo'] * scale, d)} to {sgn(s['hi'] * scale, d)})"


def lvl(b: str) -> str:
    return b.replace("-", "–").replace("2400+", "2400 or more").replace("below 1400", "below 1400")


def plural(k: int, one: str, many: str) -> str:
    return f"{n(k)} {one if k == 1 else many}"


def days(requests: int, seconds: float) -> float:
    return requests * seconds / SECONDS_PER_DAY


# ------------------------------------------------------------------ shared figures
class Data:
    def __init__(self) -> None:
        self.g = load("E20_greats_replay_by_list.json")
        self.lists = load("E21_lists.json")
        self.p = load("E21_pilot.json")
        p = self.p
        self.pages = p["pages"]
        self.l0 = p["layer0"]
        self.ff = p["full_fetch_2025"]
        self.pace = p["pages"]["requests"]["seconds_per_request"]
        self.frame_pages = self.ff["frame"]["pages"]
        self.every_pages = self.ff["every_rated_player"]["pages"]
        self.small = p["smaller_run"]
        g, rows, l0 = p["pages"]["games"], p["pages"]["game_rows"], p["layer0"]
        self.complete_rows = rows["colour_mark"] == rows["opponent_federation"] == rows["opponent_rating"] == g
        self.unmarked = rows["n_printed"] - rows["colour_mark"]         # game rows printed without a colour mark
        self.exact = (l0["game_change_equal"] == l0["games"]
                      and l0["tournament_k_sum_equal"] + l0.get("tournament_differs_a_row_unmarked", 0) == l0["tournaments"]
                      and l0["page_total_equal"] + l0.get("page_total_differs_a_row_unmarked", 0)
                      == l0["pages_with_a_tournament"])


def in_brief(d: Data) -> list[str]:
    p, l0, ff, ks = d.p, d.l0, d.ff, d.lists["k_shares"]
    k25, k25s = ks["by_k_of_the_list_before"]["2025"], ks["by_k_on_the_same_list"]["2025"]
    jc = d.lists["juniors_climb"]
    std = jc["juniors_minus_adults_25_45_standardised"]["<20"]
    nc12, nc24 = d.lists["newcomers"]["12_same_cohort_as_24"], d.lists["newcomers"]["24"]
    pr = p["probe"]
    return [
        "**In brief.** " + AFTER,
        "",
        f"- **Taken.** The greats' replay rerun list by list from FIDE's pages already cached; three new measures on "
        f"FIDE's standard lists already held; Sonas's three reports for FIDE's Qualification Commission, read and cited; "
        f"a pilot of {n(p['pages']['fetched'])} of FIDE's per-player game pages of 2025; a probe of {pr['reports']} of "
        f"FIDE's tournament reports. Nothing else: the large fetch waits for the founder (§7).",
        f"- **The greats, list by list (§2).** {d.g['players_replayed']} players on {d.g['window']['lists']} lists, "
        f"{month(d.g['window']['first'])} to {month(d.g['window']['last'])}; every year-end and last-list difference "
        f"equals E20's committed value ({d.g['check']['equal']} of {d.g['check']['year_end_and_last_list_values_compared']}).",
        f"- **Who plays the rated games (§3.1).** In 2025, by the K printed on the same list, K = 40 players hold "
        f"{pct(k25s['share K=40'])} of the player-games and K = 10 players {pct(k25s['share K=10'])}, the figures Ghita "
        f"reports (p. 73); by the K that rated the games, the list before, K = 40 holds {pct(k25['share K=40'])} and "
        f"players newly rated that month {pct(k25['share newly rated'])}.",
        f"- **Juniors' climb (§3.2).** From October 2025 to October 2026, among players who played, juniors under 20 "
        f"climbed {sgn(std['difference'])} points more than adults of 25 to 45 at the same level "
        f"({sgn(std['lo'])} to {sgn(std['hi'])}); in {jc['federations']['directions'].get('juniors climb more', 0)} of "
        f"{len(jc['federations']['list'])} federations the interval says juniors climb more, in "
        f"{jc['federations']['directions'].get('juniors climb less', 0)} less. A climb, not proof of under-rating.",
        f"- **Newcomers (§3.3).** Players first rated from April to October 2024 who kept playing were rated, on "
        f"average, {sgn(nc12['all']['mean'])} points against their first rating a year later and "
        f"{sgn(nc24['all']['mean'])} two years later: those under 12 {sgn(nc12['by_age']['<12']['mean'])} and "
        f"{sgn(nc24['by_age']['<12']['mean'])}, adults of 25 to 45 {sgn(nc12['by_age']['25-45']['mean'])} and "
        f"{sgn(nc24['by_age']['25-45']['mean'])}. A climb, not proof of under-rating.",
        "- **Sonas's reports (§4)** measure the drain at the top and the newcomers' first ratings; they measure neither "
        "federations nor colour. Four findings bearing on the problems are not yet cited by the proposal.",
        f"- **The pilot (§5).** {n(p['pages']['fetched'])} pages fetched, {n(p['pages']['parsed'])} parsed by E17's "
        f"parser, {n(p['pages']['games'])} games; "
        + ("every game row carries a colour mark and the opponent's federation and rating; " if d.complete_rows and not
           d.unmarked else
           f"{n(p['pages']['game_rows']['colour_mark'])} of the {n(p['pages']['game_rows']['n_printed'])} games FIDE "
           "counts there carry a colour mark and the opponent's federation and rating; ")
        + f"Layer 0 reproduces FIDE's printed change in {n(l0['game_change_equal'])} of {n(l0['games'])} games "
        f"and the page's total in {n(l0['page_total_equal'])} of {n(l0['pages_with_a_tournament'])}"
        + (" (the other page holds the row without a colour mark)" if l0.get("page_total_differs_a_row_unmarked") else "")
        + "; the published list change in "
        f"{n(l0['list_change_equal'])} of {n(l0['pages_on_both_lists'])}. One page every {num(d.pace, 2)} s.",
        first_looks(d),
        f"- **The probe (§6).** A tournament report gives each player's FIDE ID, federation and totals, and links each "
        f"player's game page: an index of events, with no game and no colour.",
        f"- **The brief (§7).** A full fetch of 2025 is about {n(d.frame_pages)} requests, "
        f"{num(days(d.frame_pages, d.pace), 0)} days at the pilot's pace. The recommendation is a smaller run of about "
        f"{n(d.small['pages'])} pages after FIDE has been asked, set out in SPEC-SOURCING v1.0 (in git history; "
        "`docs/specs/SPEC-SOURCING_v1_1.md` is now the club-level sample's plan).",
    ]


def first_looks(d: Data) -> str:
    """The In brief's line on the pilot's first looks, from the same figures as §5.4."""
    fl = d.p["first_looks"]
    fav = [fl["favourite_minus_table_812"][f"every level|{g}"]["mean"] for g in GAPS]
    edge = [v["edge"] for v in fl["white_edge_every_game"].values() if "edge" in v]
    ra = fl["results_by_age"]
    aj, aa = ra["adult|junior|every level"], ra["adult|adult|every level"]
    return (f"- **First looks (§5.4), a pilot's.** Favourites score {num(-max(fav), 3)} to {num(-min(fav), 3)} a game "
            f"below table 8.1.2 at every gap from 0 to 399; White's edge by level {sgn(min(edge), 3)} to "
            f"{sgn(max(edge), 3)}; adults score {ci(aj, 3)} against FIDE's expectation against juniors and "
            f"{ci(aa, 3)} against adults.")


def month(m: str) -> str:
    names = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December")
    return f"{names[int(m[5:7]) - 1]} {m[:4]}"


# ------------------------------------------------------------------ sections
def fetched(d: Data) -> list[str]:
    pol, lk = d.p["politeness"], d.p["lock"]
    hosts = pol["by_host"]
    rows = ["| host | requests | first – last (UTC) | statuses | smallest gap, as logged | gaps under 4 s |",
            "|---|---|---|---|---|---|"]
    for h in ("ratings.fide.com", "www.fide.com", "fide.com", "qc.fide.com"):
        v = hosts.get(h)
        if not v:
            continue
        st = ", ".join(f"{k}: {n(c)}" for k, c in sorted(v["statuses"].items()))
        gap = "—" if v["smallest_gap"] is None else f"{v['smallest_gap']:.0f} s"
        rows.append(f"| {h} | {n(v['requests'])} | {v['first']} – {v['last']} | {st} | {gap} | {v['gaps_under_4']} |")
    site = pol["fide_site_from_0934"]
    rb = pol["robots"]
    robots_line = (f"none publishes one: HTTP 404 from each of the {len(rb)} hosts" if all(v == "404" for v in rb.values()) else
                   "; ".join(f"{h}: HTTP {v}" for h, v in sorted(rb.items())))
    return [
        "## 1 What was fetched, and how",
        "",
        "Every request went to FIDE's own sites, from one tool, `tools/data/fetch_sourcing.py`, which reuses the "
        "repository's fetcher for FIDE's calculation pages (the endpoint and headers of "
        "`tools/data/fetch_fide_calculations.py`, the parser of E17) and its politeness module (`tools/data/politeness.py`): "
        f"robots.txt first on every host ({robots_line}), at least four seconds between requests, "
        "measured from an upper bound of the last logged request in any run, every file cached once, a doubled gap on "
        "HTTP 429 or 5xx, a stop after three refusals in a row or at once on a page that looks like a block, and the "
        "project's own User-Agent. Every request is logged in `data/fetch_log/ELO-D1.tsv`. The sites' terms, and every "
        "other source with what is taken and what is left, are in `docs/research/SOURCES_v1_0.md`.",
        "",
        *rows,
        "",
        f"- **Requests in all:** {n(pol['requests_in_all'])}, from {pol['first']} to {pol['last']}. To ratings.fide.com "
        f"{n(hosts['ratings.fide.com']['requests'])}, within the session's limit of about 2,100.",
        f"- **One site from 09:34Z.** Over every host of fide.com, counted as one site from 09:34:00Z, "
        f"{n(site['requests'])} requests, smallest gap {site['smallest_gap']:.0f} s, {site['gaps_under_4']} under four.",
        "- **A possible slip, recorded.** Before 09:34Z the gap was kept per host. The request for fide.com's robots.txt "
        "(logged 09:33:57Z) came two seconds after www.fide.com's (09:33:55Z) and returned the same page byte for byte; "
        "if fide.com answers by redirecting to www.fide.com, that host received two requests two seconds apart. Not "
        "verified; from 09:34Z every host of fide.com counted as one site.",
        (f"- **Refusals:** {pol['refusals']}; " + ("no gap was doubled." if not pol["refusals"] else
                                                   "the gap was doubled after each, as the tool does.")),
        f"- **The championship lock.** Latest rating period requested: {month(lk['latest_period_requested'])}; latest "
        f"end of an event whose report was requested: {lk['latest_report_event_end']}; requests naming a 2026 U.S. "
        f"Championship: {lk['urls_naming_a_2026_us_championship']}; cached pages naming one: "
        f"{lk['cached_pages_naming_a_2026_us_championship']} of {n(lk['cached_pages_scanned'])}. Hosts other than FIDE's "
        f"requested: {', '.join(pol['hosts_outside_fide']) or 'none'}, so no broadcast file was fetched; and no result of "
        "either 2026 U.S. Championship was read.",
        "- **What is committed.** Totals by federation, level, age group and colour only: no sampled player's name, FIDE "
        "ID, page or row (the founder, `docs/DECISIONS.md`, item 31). The greats are named, as E20 already names them.",
        "",
    ]


def greats(d: Data) -> list[str]:
    g = d.g
    rows = ["| player | lists | first | last | difference, first list | highest | lowest | last list |",
            "|---|---|---|---|---|---|---|---|"]
    for pl in sorted(g["players"], key=lambda x: x["name"]):
        s = pl["difference_by_list"]
        vals = [s[m] for m in sorted(s)]
        hi_m = min((m for m in sorted(s) if s[m] == max(vals)))
        lo_m = min((m for m in sorted(s) if s[m] == min(vals)))
        last = month(pl["last_list"]) + ("" if pl["last_list_on_fide"] == pl["last_list"] else
                                          f" (carried from {month(pl['last_list_on_fide'])})")
        rows.append(f"| {pl['name']} | {pl['lists']} | {month(pl['first_list'])} | {last} | "
                    f"{sgn(vals[0], 0)} | {sgn(max(vals), 0)} ({month(hi_m)}) | {sgn(min(vals), 0)} ({month(lo_m)}) | "
                    f"{sgn(vals[-1], 0)} |")
    means = g["mean_difference_by_list"]
    jan = [m for m in sorted(means) if m.endswith("-01")] + [g["window"]["last"]]
    mrow = " | ".join(f"{month(m)}: {sgn(means[m], 1)}" for m in jan)
    return [
        "## 2 The greats, list by list",
        "",
        f"E20's replay (`analysis/e20_greats_replay_extract.py`, imported unchanged) rerun from the pages already cached, "
        f"under the method E20 reports: E18's 2025 table **applied backwards, not fitted on that era**, FIDE's colour "
        f"marks, and Layer 0 rounding as ruling R80 reads FIDE's lists. The difference, rung 2 minus Layer 0, on every "
        f"list of the window is written to `analysis/aggregates/E20_greats_replay_by_list.json`, with the table's effect "
        f"beside it; no published rating is committed. **The check:** every year-end and last-list value equals E20's "
        f"committed one, {g['check']['equal']} of {g['check']['year_end_and_last_list_values_compared']}. What the "
        f"difference measures is E20's §5: the distance between the 2025 table and table 8.1.2 at these players' gaps, "
        f"on the same results, which FIDE rated with table 8.1.2.",
        "",
        FIXED,
        "",
        *rows,
        "",
        f"A player absent from FIDE's files after a list carries the difference of the last period, as in E20 §5. The "
        f"mean over the players on each list, each January and on the last list: {mrow}.",
        "",
        "The set of players replayed is SPEC-GREATS §2's selection, which rests on OlimpBase's transcription for the "
        "players ranked 1st to 3rd only on the lists to April 2000; for the set and its count: Derived from OlimpBase's "
        "transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or "
        "Apache-2.0 licences. The differences, computed on FIDE's pages and files, do not carry the label (README's "
        "licence section).",
        "",
    ]


def lists_section(d: Data) -> list[str]:
    ks = d.lists["k_shares"]
    before, same = ks["by_k_of_the_list_before"], ks["by_k_on_the_same_list"]
    rows = ["| year | player-games | K = 40 | K = 20 | K = 10 | newly rated | K = 40, by the K on the same list | "
            "K = 10, by the K on the same list |", "|---|---|---|---|---|---|---|---|"]
    for y in sorted(before):
        b, s = before[y], same[y]
        rows.append(f"| {y} | {n(b['player_games'])} | {pct(b.get('share K=40', 0))} | {pct(b.get('share K=20', 0))} | "
                    f"{pct(b.get('share K=10', 0))} | {pct(b.get('share newly rated', 0))} | {pct(s.get('share K=40', 0))} | "
                    f"{pct(s.get('share K=10', 0))} |")
    jc = d.lists["juniors_climb"]
    arows = ["| age in 2025 | players | mean climb | median |", "|---|---|---|---|"]
    for a in AGES:
        s = jc["by_age"][a]
        arows.append(f"| {AGE_NAME[a]} | {n(s['n'])} | {ci(s)} | {sgn(s['median'], 0)} |")
    lrows = ["| level, October 2025 | " + " | ".join(AGE_NAME[a] for a in AGES) + " |",
             "|---|" + "---|" * len(AGES)]
    for lv in LEVELS:
        cells = []
        for a in AGES:
            s = jc["by_age_level"].get(f"{a}|{lv}")
            cells.append("—" if not s or s["n"] < 30 else f"{sgn(s['mean'])} ({n(s['n'])})")
        lrows.append(f"| {lvl(lv)} | " + " | ".join(cells) + " |")
    std = jc["juniors_minus_adults_25_45_standardised"]
    srows = ["| age in 2025 | juniors | adults 25–45 | juniors' climb minus adults' at the same level |", "|---|---|---|---|"]
    for a in ("<12", "12-15", "16-19", "<20"):
        s = std[a]
        srows.append(f"| {AGE_NAME.get(a, 'under 20')} | {n(s['juniors'])} | {n(s['adults'])} | "
                     f"{sgn(s['difference'])} ({sgn(s['lo'])} to {sgn(s['hi'])}) |")
    feds = jc["federations"]["by_federation"]
    dirs = jc["federations"]["directions"]
    frows = ["| federation | juniors | adults 25–45 | difference (95 % interval) | direction |", "|---|---|---|---|---|"]
    for f in sorted(feds):
        v = feds[f]
        if v is None:
            frows.append(f"| {f} | — | — | too few players | — |")
            continue
        frows.append(f"| {f} | {n(v['juniors'])} | {n(v['adults'])} | {sgn(v['difference'])} ({sgn(v['lo'])} to "
                     f"{sgn(v['hi'])}) | {v['direction']} |")
    nc = d.lists["newcomers"]
    nrows = ["| first rated | later by | newcomers | still listed | played in between | rating then minus first rating |",
             "|---|---|---|---|---|---|"]
    a12, a24, s12 = nc["12"], nc["24"], nc["12_same_cohort_as_24"]
    for first, later, x in (("April 2024 – October 2025", "12 months", a12), ("April 2024 – October 2024", "12 months", s12),
                            ("April 2024 – October 2024", "24 months", a24)):
        nrows.append(f"| {first} | {later} | {n(x['newcomers'])} | {n(x['still_listed'])} | "
                     f"{n(x['played_in_between'])} | {ci(x['all'])} |")
    narows = ["| age when first rated | after 12 months | after 24 months |", "|---|---|---|"]
    for a in AGES:
        x, y = s12["by_age"].get(a), a24["by_age"].get(a)
        if x and y:
            narows.append(f"| {AGE_NAME[a]} | {ci(x)} ({n(x['n'])}) | {ci(y)} ({n(y['n'])}) |")
    nlrows = ["| first rating | after 12 months | after 24 months |", "|---|---|---|"]
    for lv in LEVELS:
        x, y = s12["by_level"].get(lv), a24["by_level"].get(lv)
        if x and y and x["n"] >= 30 and y["n"] >= 30:
            nlrows.append(f"| {lvl(lv)} | {ci(x)} ({n(x['n'])}) | {ci(y)} ({n(y['n'])}) |")
    fd12, fd24 = a12["federation_directions"], a24["federation_directions"]

    def direction(x: dict) -> str:
        if not x or x.get("n", 0) < 5:
            return "too few"
        return "rises" if x["lo"] > 0 else "falls" if x["hi"] < 0 else "not settled"
    nfrows = ["| federation | after 12 months (first rated April 2024 – October 2025) | players | direction | after 24 "
              "months (April – October 2024) | players | direction |", "|---|---|---|---|---|---|---|"]
    for f in sorted(a12["by_federation"]):
        x, y = a12["by_federation"][f]["all"], a24["by_federation"][f]["all"]
        nfrows.append(f"| {f} | {ci(x) if x.get('n', 0) >= 5 else '—'} | {n(x.get('n', 0))} | {direction(x)} | "
                      f"{ci(y) if y.get('n', 0) >= 5 else '—'} | {n(y.get('n', 0))} | {direction(y)} |")
    return [
        "## 3 The lists, revisited",
        "",
        "From FIDE's monthly standard lists already held (February 2015 to October 2026), totals only, by "
        "`analysis/e21_lists_extract.py`. " + AFTER + " A climb is not proof of under-rating: a player who improves "
        "climbs under any rule, and a player who stops playing leaves the measure.",
        "",
        "### 3.1 Who plays the rated games",
        "",
        "Player-games, FIDE's \"games\" column: each rated game counts once for each rated player in it. The K is the "
        "list before's, the K that rated the games (SPEC-L0 R-22b); players not rated on the list before are counted "
        "apart as newly rated. Beside it, by the K printed on the same list, the count Ghita's figure matches. 2015 runs "
        "from March, 2026 to October.",
        "",
        *rows,
        "",
        f"Ghita reports that K = 40 players make up 54.6 % of FIDE's game activity and K = 10 players 4.6 % (p. 73), on "
        f"FIDE's game extract of 2025 [R 5]. Counted by the K on the same list, the lists give the same two figures for "
        f"2025; counted by the K that rated the games, K = 40 holds less, because a player's first rated month is "
        f"counted, mostly, under the K = 40 of the list that first rates the player. Either way more than half of the "
        f"player-games of 2025 are those of players rated with K = 40 or not rated before, while the broadcast games we "
        f"hold sit at a typical 2113 against 1734 for the pool [E2].",
        "",
        "### 3.2 Juniors' climb against adults'",
        "",
        f"Every player rated on the lists of October 2025 and October 2026 who played a rated game between them "
        f"({n(jc['players'])}): the change in rating, by age in 2025 (Layer 1's age bands).",
        "",
        FIXED,
        "",
        *arows,
        "",
        "By level (October 2025) and age, the mean climb and, in brackets, the players (cells of fewer than 30 omitted):",
        "",
        FIXED,
        "",
        *lrows,
        "",
        "Juniors against adults of 25 to 45 at the same level: the difference of the mean climbs in each level band, "
        "averaged over the bands by the juniors' numbers (bands with at least five of each), with its 95 % interval:",
        "",
        FIXED,
        "",
        *srows,
        "",
        f"By federation, the same difference for juniors under 20, as a direction with its interval (the 75 federations "
        f"of the pilot): juniors climb more in {dirs.get('juniors climb more', 0)}, less in "
        f"{dirs.get('juniors climb less', 0)}, not settled in {dirs.get('not settled', 0)}.",
        "",
        FIXED,
        "",
        *frows,
        "",
        "### 3.3 Newcomers: the first rating, and the rating a year and two years later",
        "",
        "Players first rated on a list from April 2024, the first list after the one that carried the reform of 1 March "
        "2024 and its one-time compression (first rated: on no standard list before, from February 2015), who are still "
        "listed and played a rated game in between: their rating minus their first rating.",
        "",
        FIXED,
        "",
        *nrows,
        "",
        "For the players first rated from April to October 2024, by age when first rated and by the level of the first "
        "rating (players in brackets):",
        "",
        FIXED,
        "",
        *narows,
        "",
        FIXED,
        "",
        *nlrows,
        "",
        f"By federation (75), the mean change as a direction with its interval: after 12 months (first rated April 2024 "
        f"to October 2025) {fd12.get('rises', 0)} rise, {fd12.get('falls', 0)} fall, {fd12.get('not settled', 0)} not "
        f"settled; after 24 months (April to October 2024) {fd24.get('rises', 0)} rise, {fd24.get('falls', 0)} fall, "
        f"{fd24.get('not settled', 0)} not settled; under 20 and 20 and over apart, in `analysis/aggregates/E21_lists.json`.",
        "",
        FIXED,
        "",
        *nfrows,
        "",
        "Since the reform a first rating counts two hypothetical draws against players rated 1800 [V 1]. On these lists "
        "the young climb from their first rating within two years while adults fall from theirs, and low first ratings "
        "rise while high ones fall, the pattern Sonas reported for first ratings of 2010–2013 (§4). That is consistent "
        "with first ratings that sit below the young players' later level and above the adults'; the lists alone cannot "
        "separate it from the young improving and adults declining, nor from a regression towards the middle, which is "
        "what a measure on games, such as E6's, is for (§7).",
        "",
    ]


def reports_section() -> list[str]:
    rows = ["| problem | report | page | finding (paraphrased; short quotations in marks) | in the proposal |",
            "|---|---|---|---|---|"]
    for prob, rep, page, text, cited in FINDINGS:
        rows.append(f"| {prob} | {rep} | {page} | {text} | {cited} |")
    qc = [f"- {q} ({why})" for q, why in QC_2026]
    return [
        "## 4 FIDE's published reports",
        "",
        "Jeff Sonas's three reports for FIDE's Qualification Commission, fetched once each on 14 October 2026 (files of "
        "the same sizes, to the byte, as those the sweep of 10 October read [VP 3] [VP 4] [VP 5]): \"Repairing the FIDE "
        "Standard Elo Rating System\" (20 July 2023, 19 pages), \"Compression and Calculation Improvements: Supplemental "
        "Report\" (29 October 2023, 47 pages) and \"Compression and Calculation Improvements: Final Report\" (11 January "
        "2024, 19 pages). The findings that bear on the four problems:",
        "",
        *rows,
        "",
        "Not yet cited by the proposal: the counts of players rated 2200 and 2600 or more (supplemental, pp. 17, 19); "
        "the 200-point example (final, p. 2); the stable age band of 20 to 38 (supplemental, pp. 6–8); the first 15 games "
        "after a first rating (final, pp. 10–12). §8 lists them as proposed edits.",
        "",
        "The Qualification Commission's summary of its Congress meeting of 23 September 2026, posted on 12 October 2026, "
        "records decisions that bear on the problems (the full minutes, on Google Drive, were not fetched):",
        "",
        *qc,
        "",
    ]


def pilot_section(d: Data) -> list[str]:
    p, l0 = d.p, d.l0
    pg, gr, lm = p["pages"], p["pages"]["game_rows"], p["pages"]["page_against_list_games"]
    plan = p["plan"]
    lvrows = ["| level, October 2025 | pages sampled | games per page | cross-border share of game rows |",
              "|---|---|---|---|"]
    for lv in LEVELS:
        xb = p["cross_border"]["by_level"].get(lv)
        lvrows.append(f"| {lvl(lv)} | {plan['sampled_by_level'].get(lv, 0)} | "
                      f"{num(pg['games_per_page_by_level'].get(lv, 0), 2)} | "
                      f"{pct(xb['share']) if xb else '—'} ({n(xb['games']) if xb else 0} rows) |")
    fb = p["cross_border"]["by_federation"]
    shares = sorted(v["share"] for v in fb.values())
    q = lambda x: shares[min(len(shares) - 1, int(x * len(shares)))]
    frows = ["| federation | game rows | cross-border | share |", "|---|---|---|---|"]
    for f in sorted(fb):
        v = fb[f]
        frows.append(f"| {f} | {n(v['games'])} | {n(v['cross'])} | {pct(v['share'], 0)} |")
    fl = p["first_looks"]
    wrows = ["| level of the game | games within 50 points | White's score | White's edge from every game "
             "(sampled player's level) |", "|---|---|---|---|"]
    for lv in LEVELS:
        a, b = fl["white_score_near_equal"].get(lv), fl["white_edge_every_game"].get(lv)
        sa = f"{num(a['mean'], 3)} ({num(a['lo'], 3)} to {num(a['hi'], 3)})" if a else "—"
        sb = f"{sgn(b['edge'], 3)} ({sgn(b['lo'], 3)} to {sgn(b['hi'], 3)})" if b and "edge" in b else "—"
        wrows.append(f"| {lvl(lv)} | {n(a['games']) if a else 0} | {sa} | {sb} |")
    fav = fl["favourite_minus_table_812"]
    hrows = ["| gap | games | the favourite's score minus table 8.1.2 |", "|---|---|---|"]
    for gb in GAPS:
        s = fav.get(f"every level|{gb}")
        if s:
            hrows.append(f"| {gb.replace('-', '–')} | {n(s['games'])} | {ci(s, 3)} |")
    hlrows = ["| level of the game | " + " | ".join(g.replace("-", "–") for g in GAPS) + " |",
              "|---|" + "---|" * len(GAPS)]
    for lv in LEVELS:
        cells = []
        for gb in GAPS:
            s = fav.get(f"{lv}|{gb}")
            cells.append("—" if not s or s["games"] < 30 else f"{sgn(s['mean'], 3)} ({n(s['games'])})")
        hlrows.append(f"| {lvl(lv)} | " + " | ".join(cells) + " |")
    ra = fl["results_by_age"]
    arows = ["| player | opponent | games | pages | score minus FIDE's expectation |", "|---|---|---|---|---|"]
    for me, them in (("adult", "junior"), ("adult", "adult"), ("junior", "adult"), ("junior", "junior")):
        s = ra.get(f"{me}|{them}|every level")
        if s:
            arows.append(f"| {me} | {them} | {n(s['games'])} | {n(s['pages'])} | {ci(s, 3)} |")
    alrows = ["| adult's level | games against juniors | adult's score minus FIDE's expectation | games against adults "
              "| adult's score minus FIDE's expectation |", "|---|---|---|---|---|"]
    for lv in LEVELS:
        a, b = ra.get(f"adult|junior|{lv}"), ra.get(f"adult|adult|{lv}")
        if a and b and a["games"] >= 30:
            alrows.append(f"| {lvl(lv)} | {n(a['games'])} | {ci(a, 3)} | {n(b['games'])} | {ci(b, 3)} |")
    op = p["opponents"]
    exact = d.exact
    return [
        "## 5 The pilot: FIDE's per-player game pages of 2025",
        "",
        f"**The sample** (`tools/data/fetch_sourcing.py`, mode plan; fixed before any page was fetched). From the "
        f"October 2025 standard list's active players with a rated game in a 2025 period (a period's page is drawn at "
        f"random among the player's own), {plan['federations']} federations: every federation with at least 1,000 "
        f"rated players on that list, plus England, Scotland and Wales; {plan['per_federation'][0]} or "
        f"{plan['per_federation'][-1]} pages each, spread over every level band from the floor up in proportion to "
        f"the square root of the band's players, at least one in each; juniors (born 2007 or later) and newcomers "
        f"(first rated 2023 or later) drawn {num(plan['oversample'], 0)} times as often as others. Frame: "
        f"{n(plan['frame_players'])} players, {pct(plan['frame_junior_or_newcomer']/plan['frame_players'], 0)} of them "
        f"juniors or newcomers, holding {n(plan['frame_pages'])} pages; sample: "
        f"{n(plan['sampled_junior_or_newcomer'])} of {n(sum(plan['sampled_by_level'].values()))} juniors or newcomers "
        f"({n(plan['sampled_junior'])} juniors, {n(plan['sampled_newcomer'])} newcomers). " + PILOT + " The measures "
        "below were chosen after the pilot's first pages had been seen (`docs/DECISIONS.md`, item 32).",
        "",
        "### 5.1 What a page gives",
        "",
        f"- **Fetched and read:** {n(pg['fetched'])} of {n(pg['planned'])} pages; E17's parser read "
        f"{n(pg['parsed'])}; it rejects {plural(sum(pg['parse_errors'].values()), 'page', 'pages')} ("
        + "; ".join(f"{k}: {v}" for k, v in sorted(pg["parse_errors"].items())) + "), rows that the top 100's pages "
        f"never print and a larger run's parser must accept; {n(pg['with_a_game'])} of the pages read hold a game.",
        f"- **Games:** {n(pg['games'])} in {n(pg['tournaments'])} tournaments, {num(pg['games_per_page']['mean'], 2)} a "
        f"page (median {pg['games_per_page']['median']}, nine pages in ten at most {pg['games_per_page']['p90']}, "
        f"largest {pg['games_per_page']['max']}).",
        f"- **Colours, opponents' federations and ratings:** of the {n(gr['n_printed'])} games FIDE counts on the pages "
        f"read, {n(gr['colour_mark'])} are printed with a colour mark, the opponent's federation and the opponent's "
        f"rating; {plural(d.unmarked, 'game row is', 'game rows are')} printed without a colour mark, and E17's parser "
        f"leaves such a row out. {n(gr['capped_mark'])} rows carry FIDE's mark of the 400-point rule, so the rating "
        f"printed is the capped one. In {n(gr['tournaments_games_equal_n'])} of {n(pg['tournaments'])} tournaments the "
        f"rows read equal the games FIDE counts.",
        f"- **Against FIDE's list:** the games on the page equal the list's games column for the same player and period "
        f"on {n(lm['equal'])} of {n(lm['pages'])} pages ({n(lm['games_on_pages'])} games against "
        f"{n(lm['games_on_lists'])}).",
        f"- **Opponents:** identified by name, federation and rating on the list in force, as E17 does, in "
        f"{n(op['opponent_identified'])} of {n(op['games'])} games; in {n(op['opponent_in_frame_with_that_period'])} the "
        f"opponent is a frame player with a page for the same period, so a full fetch would see that game twice (§7).",
        f"- **Pace:** one page every {num(d.pace, 2)} s as logged, {n(pg['requests']['bytes_per_page'])} bytes a page.",
        "",
        "### 5.2 Layer 0 against FIDE's printed figures",
        "",
        f"On every page, with FIDE's own inputs (the player's Ro, the opponent's rating as printed, K as printed) and the "
        f"rules in force at each tournament's start (`src/layer0_history/`): each game's change {n(l0['game_change_equal'])} "
        f"of {n(l0['games'])}; each tournament's K × sum {n(l0['tournament_k_sum_equal'])} of {n(l0['tournaments'])}"
        + ((" (the other holds" if l0["tournament_differs_a_row_unmarked"] == 1 else
            f" (the other {n(l0['tournament_differs_a_row_unmarked'])} hold") + " a game row without a colour mark, "
           "which the parser leaves out)" if l0.get("tournament_differs_a_row_unmarked") else "") + "; "
        f"the page's total {n(l0['page_total_equal'])} of the {n(l0['pages_with_a_tournament'])} pages that hold a "
        f"tournament (" + ("the other is that tournament's page; " if l0.get("page_total_differs_a_row_unmarked") else "")
        + f"{plural(l0.get('pages_without_a_tournament', 0), 'page holds', 'pages hold')} none, though FIDE's "
        f"list counts games for the player in that period). " + (
            "FIDE's printed change is reproduced wherever the page prints the game. " if exact else
            "FIDE's printed change is not reproduced everywhere; the counts above say where. ") +
        f"The published change on the list, the rating of the period's list minus the list before, equals "
        f"the page's total rounded once in {n(l0['list_change_equal'])} of {n(l0['pages_on_both_lists'])} pages. Of the "
        f"others, {n(l0.get('list_differs_ro_not_previous_list', 0))} have a tournament whose Ro is not the rating of "
        f"the list before (a tournament that began under an earlier list, SPEC-L0 R-11a, or a base FIDE corrected, "
        f"R-11b); {n(l0.get('list_differs_page_games_not_list_games', 0))} hold fewer or more games than the list "
        f"counts; {n(l0.get('list_differs_unexplained', 0))} are unexplained: "
        f"{n(l0.get('list_differs_unexplained_by_one', 0))} of them by one point, "
        + ("all of them players with K = 40" if l0.get("list_differs_unexplained_k40", 0) ==
           l0.get("list_differs_unexplained", 0) else
           f"{n(l0.get('list_differs_unexplained_k40', 0))} of them players with K = 40") +
        f", {n(l0.get('list_differs_unexplained_junior_or_newcomer', 0))} juniors or newcomers. Why the list departs "
        "from the page is NOT VERIFIED.",
        "",
        "### 5.3 Cross-border games",
        "",
        f"The share of game rows whose opponent's federation differs from the player's. " + PILOT + " Weighted to the "
        f"frame: {pct(p['cross_border']['weighted_share'])}; Ghita finds more than 80 % of FIDE's games domestic (p. 23), "
        f"and 48 % of the broadcast games are cross-border [E7].",
        "",
        *lvrows,
        "",
        f"By federation (26 or 27 pages each, so each share is rough): the median federation "
        f"{pct(q(0.5), 0)}, from {pct(shares[0], 0)} to {pct(shares[-1], 0)}.",
        "",
        *frows,
        "",
        "### 5.4 First looks",
        "",
        PILOT + " " + AFTER + " Each figure is a mean over game rows with a 95 % interval clustered over pages; juniors "
        "and newcomers are drawn three times as often as others, and the figures are not weighted.",
        "",
        "**White moves first.** White's score in games between players at most 50 points apart, by the level of the "
        "game; and White's edge from every game, half the difference between the mean of score minus FIDE's expectation "
        "as White and as Black, by the sampled player's level:",
        "",
        FIXED,
        "",
        *wrows,
        "",
        "**The favourite against table 8.1.2.** The favourite's score minus table 8.1.2's expectation at the gap "
        "(games with FIDE's mark of the 400-point rule left out, their gap being unknown), over every level and by "
        "level (cells of fewer than 30 games omitted):",
        "",
        FIXED,
        "",
        *hrows,
        "",
        FIXED,
        "",
        *hlrows,
        "",
        "**Adults against juniors.** Juniors are players born 2007 or later; the opponent's year of birth from FIDE's "
        "list once the opponent is identified. The score minus FIDE's expectation is the change FIDE prints for each "
        "game before K:",
        "",
        FIXED,
        "",
        *arows,
        "",
        FIXED,
        "",
        *alrows,
        "",
        "E6 measured the adults' residual against eligible juniors on broadcast games [E6]; these are the first such "
        "figures on games of the pool's own levels, and they are a pilot's.",
        "",
    ]


def probe_section(d: Data) -> list[str]:
    pr = d.p["probe"]
    return [
        "## 6 The probe: FIDE's tournament reports",
        "",
        f"{pr['reports']} reports of events whose players appear on the pilot's pages of the January 2025 period, chosen "
        f"by a fixed rule (the SHA-256 order of the event's number), every event ended before 1 October 2026 and none a "
        f"2026 U.S. Championship; {pr['requests']} requests, {', '.join(f'HTTP {k}: {v}' for k, v in pr['statuses'].items())}.",
        "",
        f"- **Individual games: none.** A report lists each player of the event with FIDE ID, name, federation, title, "
        f"the opponents' average (Rc), the score (W), the games (N) and the change, and links each player's game page "
        f"for the period. Colour marks: {pr['colour_marks']}.",
        f"- **Per request:** one event, {pr['players_per_report']['median']} players at the median "
        f"({pr['players_per_report']['min']} to {pr['players_per_report']['max']}), "
        f"{pr['player_games_per_report_median']} player-games at the median, every player with a FIDE ID "
        f"({'yes' if pr['player_ids_given_in_every_report'] else 'no'}), {n(pr['player_pages_linked'])} player pages "
        f"linked in all.",
        "- **What that is worth.** A report is not a source of games; it is an index. With it a fetch can take whole "
        "events (every player's page for the event's period), and can identify every opponent exactly, by the event's "
        "own list of FIDE IDs, instead of by name. Games with colours come only from the players' pages.",
        "",
    ]


# ------------------------------------------------------------------ the brief
def brief(d: Data) -> list[str]:
    ff, sm, p = d.ff, d.small, d.p
    lrows = ["| level, October 2025 | players | pages (requests) | player-games | distinct games | cross-border "
             "player-games |", "|---|---|---|---|---|---|"]
    for lv in LEVELS:
        v = ff["by_level"].get(lv)
        if v:
            lrows.append(f"| {lvl(lv)} | {n(v['players'])} | {n(v['pages'])} | {n(v['player_games'])} | "
                         f"{n(v['distinct_games'])} | {n(v['cross_border_player_games'])} |")
    t = ff["frame"]
    lrows.append(f"| every level | {n(t['players'])} | {n(t['pages'])} | {n(t['player_games'])} | "
                 f"{n(t['distinct_games'])} | {n(t['cross_border_player_games'])} |")
    bf = ff["by_federation"]
    xb = sorted(v["cross_border_player_games"] for v in bf.values())
    over = sum(1 for v in bf.values() if v["cross_border_player_games"] >= 1000)
    over300 = sum(1 for v in bf.values() if v["cross_border_player_games"] >= 300)
    frows = ["| federation | full fetch: pages | player-games | cross-border player-games | smaller run: pages | "
             "cross-border player-games on its own pages |", "|---|---|---|---|---|---|"]
    for f in sorted(bf):
        v, s = bf[f], sm["by_federation"][f]
        frows.append(f"| {f} | {n(v['pages'])} | {n(v['player_games'])} | {n(v['cross_border_player_games'])} | "
                     f"{n(s['pages'])} | {n(s['cross_border_player_games'])} |")
    below2000 = sum(ff["by_level"][lv]["player_games"] for lv in LEVELS[:3] if lv in ff["by_level"])
    pj = p["smaller_run_projection"]
    ajv = [pj["adult_junior_games_by_adult_level"].get(lv, 0) for lv in LEVELS[:3]]
    aj_text = f"{n(ajv[0])}, {n(ajv[1])} and {n(ajv[2])}"
    full_days, full_days4 = days(d.frame_pages, d.pace), days(d.frame_pages, 4.0)
    small_days = days(sm["pages"], d.pace)
    k = d.lists["k_shares"]["by_k_on_the_same_list"]["2025"]
    return [
        "## 7 The brief: go, no-go, or a smaller run",
        "",
        "For the founder, in plain words. " + PILOT + " The yield below is FIDE's own count of games, from its lists, "
        "for the pages a fetch would request, with the pilot's shares applied; it is an extrapolation, labelled so, and "
        "its estimates (distinct and cross-border games) are given to the nearest hundred, the smaller run's to the "
        "nearest ten.",
        "",
        "**What the pilot shows.** FIDE's per-player game pages can be fetched politely and read: "
        f"{n(p['pages']['fetched'])} pages, {plural(p['politeness']['refusals'], 'refusal', 'refusals')}, "
        f"{plural(sum(p['pages']['parse_errors'].values()), 'page', 'pages')} that E17's parser rejects (game rows "
        "printed without K, §5.1). "
        + ("Each game comes with the colour, the opponent's rating and federation, " if d.complete_rows and not
           d.unmarked else
           f"All but {n(d.unmarked)} of the {n(p['pages']['game_rows']['n_printed'])} games on the pages read come "
           "with the colour, the opponent's rating and federation, ")
        + ("and FIDE's own change, which Layer 0 reproduces exactly wherever the page prints the game. " if d.exact else
           "and FIDE's own change, which Layer 0 reproduces in all but the cases §5.2 counts. ")
        + f"The pages hold {pct(ff['page_to_list_games_ratio'], 1)} of the games FIDE's lists count for the same "
        "players and periods. They reach the levels our broadcast games miss: of the player-games a full fetch would "
        f"bring, {pct(below2000 / t['player_games'], 0)} are those of players rated below 2000, and over the whole "
        f"list K = 40 players hold {pct(k['share K=40'], 0)} of the player-games of 2025 (§3.1). Its first looks "
        "(§5.4) are a pilot's, on 2,000 pages and unweighted: they point the way the broadcast games do [E2] [E6], and "
        "settle nothing alone.",
        "",
        "**The big fetch's likely yield**, every frame page of 2025: the 75 federations' active players of October "
        "2025, each period in which they played. The cross-border player-games apply a model of the pilot's rows, "
        f"additive in federation and level band on the log-odds scale: over the frame it gives "
        f"{pct(ff['cross_border_share_model'])}, against {pct(p['cross_border']['weighted_share'])} from the pilot's "
        "own weights.",
        "",
        *lrows,
        "",
        f"Taking every rated player of every federation would add little: {n(ff['every_rated_player']['pages'])} pages and "
        f"{n(ff['every_rated_player']['player_games'])} player-games in 2025. A game between two frame players appears "
        f"on both their pages ({pct(ff['share_rows_with_opponent_also_in_frame'], 0)} of the pilot's rows), so the "
        f"distinct games are fewer than the player-games. By federation: the cross-border player-games of a full fetch "
        f"run from {n(xb[0])} to {n(xb[-1])} (median {n(xb[len(xb) // 2])}); {over} of 75 federations would pass 1,000, "
        f"Ghita's floor (p. 65), and {over300} would pass 300, E7's.",
        "",
        "**What it would settle.** On the pool's own games of 2025, at every level: the federations' offsets as "
        "directions with intervals, with E7's method, for nearly every one of the 75 federations (countries priced "
        "differently); the table's calibration by gap, level and colour with E2's and E11's rules, where broadcast games "
        "are thin (White moves first; the table's error that drains the top, measured at the levels the top's opponents "
        "come from); and E6's measure of adults' results against juniors in the domestic events where juniors play "
        "(fast improvers rated behind their strength).",
        "",
        "**What it would not settle.** It holds one year; it cannot say why federations or juniors differ; the pages "
        "give tournament dates, not a date or round for each game; games against unrated players are not on them; it "
        "is no replay of the whole pool before 2025; and it replaces neither FIDE's tournament-report archive, which the "
        "proposal asks for, nor FIDE's own test of the rungs on its data.",
        "",
        f"**Its cost.** About {n(d.frame_pages)} requests, {num(t['player_games'] / t['pages'], 1)} player-games a "
        f"request on average: {num(full_days, 0)} days without a pause at the pilot's pace "
        f"of one page every {num(d.pace, 2)} s, {num(full_days4, 0)} at four seconds; about "
        f"{num(d.frame_pages * p['pages']['requests']['bytes_per_page'] / 1e9, 1)} GB cached. The risks: FIDE's terms reserve "
        "storing its pages \"in any medium\" to its written permission, which is to be requested; a month of steady "
        "load on FIDE's server, and a block, would close the route and could sour the request the proposal makes of "
        "FIDE; most of the K = 40 players are minors, and a full fetch would hold their game histories in bulk, if "
        "only locally; and a month-long run is fragile (interruptions, page changes).",
        "",
        f"**A smaller run** (pilot-informed). For each federation, pages enough for {sm['target_cross_border_games_per_federation']} "
        f"cross-border player-games on its own players' pages at the pilot's rate for that federation (E7's threshold "
        f"for an estimate), and at least {n(sm['floor_pages'])} pages, the smallest floor, in steps of 100 from 200, at "
        f"which the projected games of adults against juniors reach {n(sm['target_adult_junior_games_per_level_below_2000'])} "
        f"in each level band below 2000; at most {n(sm['cap_pages'])}, never more than the federation's 2025 pages: "
        f"about {n(sm['pages'])} "
        f"requests, {num(small_days, 1)} days at the pilot's pace, {n(sm['player_games'])} player-games of which "
        f"{n(sm['cross_border_player_games'])} cross-border. {sm['federations_reaching_target']} of 75 federations "
        f"reach {sm['target_cross_border_games_per_federation']} on their own pages, and "
        f"{sm['federations_reaching_1000']} reach 1,000; games against a federation's players found on other "
        f"federations' pages add to each. "
        + ("The federations that stay short play at home; their offsets would rest on those games or wait for FIDE's "
           "data. " if sm["federations_reaching_target"] < 75 else
           "Below 1,000, the floor for a headline, an offset gives a direction with its interval, not a ranking. ")
        + f"Drawn as the pilot was (every level band, juniors and newcomers "
        f"oversampled), the run serves the calibration below 2000 and the junior measure too. The plan is "
        f"SPEC-SOURCING v1.0 (in git history; `docs/specs/SPEC-SOURCING_v1_1.md` is now the club-level sample's "
        f"plan); the floors tried: "
        + "; ".join(f"{k} pages, {n(v['pages'])} requests, adults against juniors "
                    + ", ".join(n(x) for x in v["adult_junior_below_2000"])
                    for k, v in sorted(sm["floors_tried"].items(), key=lambda kv: int(kv[0]))) + ".",
        "",
        *frows,
        "",
        f"**Recommendation: a smaller run, after FIDE has been asked; no-go on the full fetch for now.** By the pilot's "
        f"rates the smaller run gives an estimate's worth of cross-border games (300) in "
        f"{sm['federations_reaching_target']} of 75 federations on their own pages, {pj['calibration_cells_with_1000']} "
        f"of the {pj['calibration_cells_below_2000']} calibration cells below 2000 with 1,000 games or more, and "
        f"{aj_text} games of adults against juniors in the three level bands below 2000 (the plan's §7 asks 1,000 in "
        f"each). The full fetch adds precision ({over} of 75 federations past 1,000 cross-border games, against "
        f"{sm['federations_reaching_1000']} in the smaller run) and the thin cells, at "
        f"{num(d.frame_pages / sm['pages'], 0)} times the requests and a month of load, and it would hold minors' game "
        "histories in bulk without FIDE's written permission. Ask FIDE now, with the proposal or before it, for its "
        "tournament-report archive or for permission to store its pages. If FIDE shares the archive, no run is needed; "
        "if it permits storing, run the smaller run and widen it where a federation stays short; if it refuses, fetch "
        "nothing more. If FIDE has not answered within a time the founder sets, the smaller run can go under the "
        "repository's standing practice for FIDE's material (analysed from the local cache, never redistributed, "
        "aggregates only; `docs/research/DATA-PROBE_greats.md` §2.6), in stretches the founder chooses. The founder "
        "decides the time, and whether the smaller run goes at all.",
        "",
    ]


def edits_section() -> list[str]:
    return [
        "## 8 Proposed edits, for after ELO-16 (not made)",
        "",
        "The proposal, the brief and the annex are not edited in this session. Proposed:",
        "",
        "- §2 or the annex: the share of rated games played by K = 40 players, counted on FIDE's lists, beside Ghita's "
        "figure, with the two ways of counting (§3.1).",
        "- §2(b) or annex T4.6: the newcomers' first ratings against their ratings a year and two years later, since the "
        "reform, as a climb and not as proof (§3.3); beside it Sonas's finding on first ratings (final report, pp. "
        "10–12).",
        "- §2(a): the count of players rated 2600 or more falling about one a month in 2020–2023 (Sonas, supplemental "
        "report, p. 19) beside E5's count of active 2600+ players.",
        "- Annex T8.6, on what FIDE is asked for: that FIDE's per-player game pages carry colours and the opponent's "
        "federation, and that the tournament reports give FIDE IDs per event (§5, §6), as the fallback if the archive "
        "cannot be shared.",
        "- Appendix H or E20's report: the greats' difference list by list (§2), if the appendix is to show it.",
        "",
    ]


def limits_section() -> list[str]:
    return [
        "## 9 Limits and not verified",
        "",
        "- Every analysis here was chosen after its data had been seen (`docs/DECISIONS.md`, item 32); none was "
        "registered in advance, and none is a test of a rung.",
        "- The pilot's first looks rest on 2,000 pages, one per player, with juniors and newcomers drawn three times as "
        "often and the figures unweighted; opponents are identified by name, which E17 found reliable on the top 100's "
        "pages but which is NOT VERIFIED on the pool's.",
        "- The yield of a full fetch applies a model of the pilot's cross-border rows, additive in federation and level "
        "band on the log-odds scale, to FIDE's own counts of games; per federation it rests on 26 or 27 pages.",
        "- The list changes that Layer 0 does not reproduce from the page (§5.2) are NOT VERIFIED.",
        "- The climbs of §3 are climbs, not proof of under-rating; players who stop playing leave the measure.",
        "- Whether fide.com redirects to www.fide.com (§1) is NOT VERIFIED.",
        "",
    ]


def e21(d: Data) -> str:
    head = [
        "# E21 — Sourcing: the cheap sources, and a pilot of FIDE's game pages that decides the big fetch",
        "",
        "Status: DRAFT — evidence for the founder's decision on a larger fetch, session ELO-D1 (14 October 2026), under "
        "the founder's decisions of that day (`docs/DECISIONS.md`, items 24 to 32). Not for publication. Generated by "
        "`analysis/e21_sourcing_report.py` from `analysis/aggregates/E20_greats_replay_by_list.json`, "
        "`analysis/aggregates/E21_lists.json` and `analysis/aggregates/E21_pilot.json`, which "
        "`analysis/e20_greats_replay_by_list_extract.py`, `analysis/e21_lists_extract.py` and "
        "`analysis/e21_pilot_extract.py` write from `data/`; do not edit by hand. Licence: CC BY 4.0 "
        "(`docs/LICENSE-docs.md`); quoted third-party text remains its owners'. Data: FIDE's own lists, per-player "
        "calculation pages and tournament reports, used for analysis only, cached locally and never committed; FIDE "
        "reserves all rights and its written permission is to be requested (`docs/research/SOURCES_v1_0.md`; "
        "`docs/DECISIONS.md`, item 6). Ghita's book [R 5] is cited by page and paraphrased; Sonas's reports are quoted "
        "briefly, by page. Every parameter met here is PROVISIONAL.",
        "",
        FIXED,
        "",
        *in_brief(d),
        "",
        *fetched(d),
        *greats(d),
        *lists_section(d),
        *reports_section(),
        *pilot_section(d),
        *probe_section(d),
        *brief(d),
        *edits_section(),
        *limits_section(),
    ]
    return "\n".join(head).rstrip("\n") + "\n"


# ------------------------------------------------------------------ the plan of the club-level sample (SPEC-SOURCING v1.1)
STRATUM_ORDER = ("1400-1599|junior", "1400-1599|newcomer", "1400-1599|other", "1600-1799|junior", "1600-1799|newcomer",
                 "1600-1799|other", "1800-1999|junior", "1800-1999|newcomer", "1800-1999|other", "2000-2199|junior",
                 "2000-2199|newcomer", "2000-2199|other", "2200+|junior", "2200+|other")
GROUP_NAME = {"junior": "juniors", "newcomer": "newcomers", "other": "others"}
CLUB_LEVELS = ("1400-1599", "1600-1799", "1800-1999", "2000-2199", "2200+")


def club_lvl(b: str) -> str:
    return b.replace("-", "–").replace("2200+", "2200 or more")


def spec() -> str:
    cp = load("E21_club_plan.json")
    fr, al, rule = cp["frame"], cp["allocation"], cp["rule"]
    pages, ex_ = al["pages"], al["expected"]
    tot = sum(pages.values())
    opp = cp["pilot"]["opponents"]
    ident = sum(v for k, v in opp.items() if k.startswith("identified"))
    rows = sum(opp.values())
    band_pages = {b: sum(v for s, v in pages.items() if s.startswith(b)) for b in CLUB_LEVELS}
    table = ["| level, October 2025 | group | players | pages (2025 periods) | player-games | FIDE's games a page | "
             "pages drawn |", "|---|---|---|---|---|---|---|"]
    for s in STRATUM_ORDER:
        b, g = s.split("|")
        f = fr[s]
        table.append(f"| {club_lvl(b)} | {GROUP_NAME[g]} | {n(f['players'])} | {n(f['pages'])} | "
                     f"{n(f['player_games'])} | {num(al['games_per_page'][s], 2)} | {n(pages[s])} |")
    ft = cp["frame_total"]
    table.append(f"| every level | every group | {n(ft['players'])} | {n(ft['pages'])} | {n(ft['player_games'])} | "
                 f"{num(ft['player_games'] / ft['pages'], 2)} | {n(tot)} |")
    yld = ["| level band | pages drawn | games on them | threshold | games of adults against juniors, by the adult's band "
           "| threshold |", "|---|---|---|---|---|---|"]
    for b in CLUB_LEVELS:
        aj = ex_.get(f"adult_junior|{b}")
        yld.append(f"| {club_lvl(b)} | {n(band_pages[b])} | {n(ex_[f'games|{b}'])} | "
                   f"{n(rule['target_games']) if b != '2200+' else '—'} | {n(aj) if aj is not None else '—'} | "
                   f"{n(rule['target_adult_junior']) if b in ('1400-1599', '1600-1799', '1800-1999') else '—'} |")
    ages = ("<12", "12-15", "16-19", "20-24", "25-45", "46-60", ">60")
    short = [t for t, ok in al["thresholds_met"].items() if not ok]
    out = [
        "# SPEC-SOURCING — the club-level sample of FIDE's per-player game pages: the plan",
        "",
        "Status: DRAFT — the plan of session ELO-D2 (14 October 2026), under the founder's decisions of that day "
        "(`docs/DECISIONS.md`, items 33 to 36), committed before the main fetch; nothing in it was changed after the "
        "fetch began. Generated by `analysis/e21_sourcing_report.py --spec` from "
        "`analysis/aggregates/E21_club_plan.json`, which `analysis/e21_club_plan_extract.py` writes from FIDE's lists "
        "and the pilot's pages in `data/`; do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). Version "
        "1.0 (session ELO-D1) was the draft plan of a larger fetch, the smaller run of about 33,000 pages that E21 §7 "
        "recommends after FIDE has been asked; the founder ran instead the two tiers below, and no larger fetch and no "
        "request to FIDE (items 33 and 34) [E21]. The pilot's rates and every choice marked **pilot-informed** were "
        "set after the pilot's pages had been seen; the analyses of §7 are fixed here, before the main fetch (item 36). "
        "Every parameter met here is PROVISIONAL.",
        "",
        "## 1 What the sample is for",
        "",
        "Most rated games are played below 2000: of the player-games of 2025 in the frame, "
        f"{pct(sum(fr[s]['player_games'] for s in STRATUM_ORDER if not s.startswith(('2000', '2200'))) / ft['player_games'], 0)} "
        "are those of players rated below 2000 on the October 2025 list, while the broadcast games behind the "
        "proposal's fair expectation table sit at a typical 2113 [E2]. The sample turns the pilot's first looks (E21 "
        "§5.4) into club-level findings on four questions: the fair table (the favourite's score against table 8.1.2, "
        "and against the fitted tables, none fitted on these games), White's edge at equal ratings, adults' results "
        "against juniors, and newcomers' first year. Tier 0, on the pages already held, settles what it can of the "
        "pilot's list-change puzzle (§8).",
        "",
        "## 2 The frame",
        "",
        f"- **Players:** the pilot's frame: the active players (no inactivity flag) of FIDE's October 2025 standard "
        f"list in E21's {cp['federations']} federations (every federation with at least 1,000 rated players on that "
        f"list, plus England, Scotland and Wales): {n(ft['players'])} players.",
        f"- **Pages:** each 2025 standard rating period in which the list shows games for the player and the player was "
        f"rated on the list before: {n(ft['pages'])} pages, {n(ft['player_games'])} player-games by FIDE's lists.",
        "- **Not in the frame:** any period outside 2025; rapid and blitz; a period in which the player was not yet "
        "rated on the list before (the games that make a first rating).",
        "",
        "## 3 Strata",
        "",
        "- **Level:** the rating on the October 2025 list: 1400–1599, 1600–1799, 1800–1999, 2000–2199, and a small "
        "stratum of 2200 or more, the anchor to the broadcast evidence.",
        f"- **Group:** juniors as E6 defines them, list year minus year of birth at most {rule['junior_max_age']} "
        f"(born 2006 or later); newcomers, first rated on a list from January 2023 (on none of FIDE's lists from "
        f"February 2015 to December 2022), who are not juniors; others, adults with an older rating or without a year "
        f"of birth (annex T2.2: no year of birth counts as an adult). At 2200 or more newcomers are too few to stand "
        f"apart ({n(cp['newcomers_at_2200_or_more'])}) and are drawn with the others.",
        "- **The draw:** in each stratum, players drawn without replacement, all with the same chance, across every "
        "federation of the frame (the exponential race on fixed pseudo-random numbers of SHA-256, seed "
        f"{rule['seed']}, as the pilot drew); each player's page a 2025 period drawn at random among the player's own; "
        "one page per player. A page already in the cache (the pilot's) is not fetched again.",
        "",
        "## 4 Pages, the parser and the opponents",
        "",
        "- **The page:** FIDE's per-player calculation page (`/a_indv_calculation.php`, as "
        "`tools/data/fetch_fide_calculations.py` requests it, with the same headers), fetched by "
        "`tools/data/fetch_sourcing.py`, modes club-robots, club-plan and club-run.",
        "- **The parser** (pilot-informed; `analysis/e21_club_common.py`): E17's, extended to read a tournament whose "
        "player FIDE prints with Ro 0 and without K (the pilot's seven pages that E17's parser rejects) and a game row "
        "printed without a colour mark, each counted apart. On every pilot page E17's parser reads, the extended parser "
        "gives the same tournaments and the same marked games. A row without a colour mark counts as a game and is "
        "left out of every measure that uses colour.",
        f"- **The opponent** (pilot-informed): identified on FIDE's list in force at the tournament's start, as E21 "
        f"does, by name and federation, with the rating FIDE prints within {rule['tolerance']} points (beyond it on the "
        f"same side for a row FIDE marks under the 400-point rule), the nearest if several, else on the lists up to "
        f"three months either side. On the pilot's pages it identifies {n(ident)} of {n(rows)} game rows "
        f"({pct(ident / rows)}); E21's rule, which asks the exact rating, identified 8,508 of 11,501, because the "
        "ratings FIDE prints on its pages today often differ by a few points from the lists as published. The "
        "opponent's year of birth is read from FIDE's list.",
        "",
        "## 5 The allocation",
        "",
        f"- **Rule** (pilot-informed): {n(rule['anchor_pages'])} pages at 2200 or more, the anchor; "
        f"{n(rule['total_pages'] - rule['anchor_pages'])} in the four bands from 1400 to 2199. Within each band the "
        f"groups are drawn in proportion to their players, juniors and newcomers counted {rule['oversample']} times "
        f"(the pilot's factor); the four bands' totals are set one page at a time, each to the band that adds most to "
        f"the threshold furthest from being met. The thresholds: at least {n(rule['target_games'])} games on the pages "
        f"of each band from 1400 to 2199, and at least {n(rule['target_adult_junior'])} games of adults against juniors "
        "in each band below 2000, by the adult's band, counted from the adult's side on either player's page. "
        "**At the pilot's rates:** FIDE's own games per page in each stratum (its lists) and the pilot's share of a "
        "stratum's game rows that are games of adults against juniors, unweighted.",
        f"- **Pages:** {n(tot)} in all, so that with one read of robots.txt and any retry the session stays within "
        f"the hard cap of {n(rule['cap_requests'])} requests, which the tool enforces.",
        "",
        *table,
        "",
        "**What it should bring**, at the pilot's rates:",
        "",
        *yld,
        "",
        ("All seven thresholds are met at the pilot's rates within the cap." if not short else
         "Within the cap, the thresholds not met at the pilot's rates: " + ", ".join(short) + ".")
        + " Games of newcomers first rated from April 2024 in their first year, by age when first rated: "
        + "; ".join(f"{AGE_NAME[a]} {n(ex_.get(f'first_year|{a}', 0))}" for a in ages)
        + ". Games between players at most 25 points apart, by the game's level: "
        + "; ".join(f"{club_lvl(b)} {n(ex_.get(f'near_equal|{b}', 0))}" for b in CLUB_LEVELS) + ".",
        "",
        "## 6 Requests and pace",
        "",
        "- One process, the pilot's tool and headers, the project's User-Agent, never disguised; at least four seconds "
        "after the last request to any host of fide.com, all of fide.com counted as one site, measured from an upper "
        "bound of its logged time in this session's log and the pilot's; every page cached once.",
        "- On HTTP 429 or 5xx, or a timeout, the gap doubles; three refusals in a row stop the run, and a page that "
        "looks like a block stops it at once; the stop is recorded and nothing restarts on its own.",
        f"- Every request logged in `data/fetch_log/ELO-D2.tsv` (UTC time, host, path, status, size, SHA-256); the run "
        f"stops at {n(rule['cap_requests'])} requests in it. 2025 rating periods only; nothing whose name refers to a "
        "2026 U.S. Championship; no broadcast file. At the pilot's pace, one page every 5.02 s, the run takes about "
        f"{num(tot * 5.02 / 3600, 1)} hours.",
        "",
        "## 7 The analyses, fixed before the main fetch",
        "",
        "Each on the sample's pages, each figure with a 95 % interval clustered over pages, weighted to the frame "
        "(§7.5) with the unweighted figure beside it; every rating comparison carries the line \"Under this rule, with "
        "the same results — not anyone's true strength.\" A cell is shown from 100 games. None is a test of a rung, "
        "which stays for FIDE's data.",
        "",
        "### 7.1 The fair table at club level",
        "",
        "- **Games:** every game row whose opponent's rating FIDE prints uncapped and whose gap is below 400, the two "
        "ratings as FIDE prints them (the player's Ro and the opponent's rating); the favourite is the higher-rated "
        "player, White at equal ratings (E2's rule); a row is one game from the sampled player's side.",
        "- **Level of the game:** the mean of the two ratings, in E2's 200-point bands: 1400–1599, 1600–1799, "
        "1800–1999, 2000–2199, 2200 or more. **Gap:** 50-point bins from 0–49 to 350–399.",
        "- **E2's measure:** the favourite's score minus table 8.1.2's expectation (FIDE's PD) by gap, every level "
        "pooled, and by level band × gap.",
        "- **The fitted tables, none fitted on these games** (E11's and E18's held-out rules): the 2025 "
        "self-calibrating table [E18], fitted on broadcast games of March to December 2024; and the v2 table [E11], "
        "its rolling fit for the month in which the tournament started, fitted on the 36 months of broadcast games "
        "before it (for a tournament that started before January 2025, January 2025's fit). Each with its colour term, "
        "at the midpoint of the 100-point band of the game's mean rating, as E11 and E18 apply them; rows without a "
        "colour mark left out. The favourite's residual under each by gap, by level band × gap, and pooled by level band.",
        "- **E11's rule (a)**, on the cells of 200-point level band × 50-point gap with at least 1,000 games: a cell is "
        "outside when its residual is significantly outside ±0.01 (one-sided test against the nearer bound, standard "
        "error clustered over pages, Holm–Bonferroni across the cells of each table); the count of cells outside for "
        "each table (E11's 100-point bands would hold too few games here).",
        "",
        "### 7.2 White moves first",
        "",
        "- **E2's measure:** White's score in games between players at most 25 points apart, by the game's level band; "
        "rows without a colour mark left out.",
        "- **The fitted tables' colour term:** at the same games, White's score minus each fitted table's expectation "
        "for White (colour included), by level band; and, over every game of §7.1, White's edge left by each table: "
        "half the difference of the mean residual as White and as Black. The same edge under table 8.1.2 (FIDE's "
        "printed change before K), by level band, as E21 §5.4 measures it.",
        "",
        "### 7.3 Juniors",
        "",
        "- **E6's measure:** adults' score minus FIDE's expectation against juniors, and against adults at the same "
        "gap, by the adult's band below 2000 (1400–1599, 1600–1799, 1800–1999; 2000–2199 and 2200 or more beside "
        "them). Juniors and adults as E6 defines them (§3), the opponent's year of birth from FIDE's list once the "
        "opponent is identified (§4); a game whose opponent is not identified is left out.",
        "- **The adults' games against juniors**, from the adult's side, read on the adult's page or on the junior's: "
        "on the adult's page the residual is FIDE's printed change before K, on the junior's its negative (table 8.1.2's "
        "two columns sum to one), and the adult's band is that of the rating FIDE uses for the adult in the game. Rows "
        "FIDE marks under the 400-point rule, and tournaments printed without K, are left out.",
        "- **The matched control** (E6): every game of an adult against an adult read on an adult's page, from the "
        "sampled adult's side, binned by colour and 50-point gap (own rating minus the opponent's); each game of an "
        "adult against a junior is compared with the control's mean residual in its own bin, and the junior-specific "
        "residual is the difference. Rows without a colour mark stay out of the control and of the difference.",
        "",
        "### 7.4 Newcomers",
        "",
        f"- **Players first rated on a list from April 2024** (E21 §3.3), on the sample's pages of periods within 12 "
        "months after the first rating: score minus FIDE's expectation (the printed change before K), by age when "
        "first rated (under 12, 12–15, 16–19, 20–24, 25–45, 46–60, over 60) and over every age. Positive means the "
        "newcomers score more than FIDE's expectation from their ratings: rated behind their results in that year.",
        "",
        "### 7.5 Weights and intervals",
        "",
        "- **Weights:** a page stands for the frame players of its stratum over the sampled players of the stratum, "
        "times the player's 2025 frame pages (its period was drawn at random among them), as in the pilot; a game row "
        "carries its page's weight. The weighted figure is the frame's; the unweighted, beside it, is the sample's, in "
        "which juniors and newcomers are drawn three times as often.",
        "- **Intervals:** 95 %, the ratio estimator's linearised variance clustered over pages (one page per player); "
        "games on two sampled pages are few and each counts on its own page.",
        "",
        "## 8 Tier 0: the pages already held",
        "",
        "- **The parser fix** (§4), on the pilot's 2,000 pages: the rows printed without K and the row without a "
        "colour mark, counted.",
        "- **The list-change puzzle:** on the pilot's pages whose published list change differs from the page's "
        "rounded total, with the player's Ro equal to the list before and the page's games equal to the list's (E21 "
        "§5.2), the known rules are tested first against the pages and the lists: the cap on K times the games of a "
        "period (R-23), the rating floor (R-32), games rated in a later period (R-09, R-10), games against players "
        "unrated when the event began (R-12), and rounding per tournament or once per period (R-25), each against "
        "SPEC-L0 v1.5's citation of the regulations; then, decided after seeing the pilot, the ratings as published "
        "instead of as FIDE's pages print them today. How many each explains, and what remains; nothing is claimed "
        "about FIDE beyond what the pages and lists show, and what stays unexplained is NOT VERIFIED.",
        "",
        "## 9 Terms, privacy, deletion and the lock",
        "",
        "- FIDE's footer reserves storing its pages to its written permission (`docs/research/SOURCES_v1_0.md`); no "
        "request is made to FIDE or to anyone in this session (item 34). Pages stay in `data/` (gitignored); only "
        "totals by level, age group and colour, with their intervals, are committed: no sampled player's name, FIDE ID "
        "or row. Many sampled players are minors.",
        "- **Deletion** (item 35): once the session's analysis is verified, the raw pages of the pilot and of this run, "
        "and every per-game file derived from them, are deleted; a local manifest, `data/raw/sourcing/MANIFEST`, keeps "
        "each page's link, period and SHA-256, so that anyone can fetch it again. E17's and E20's caches are not "
        "touched.",
        "- **The lock:** 2025 rating periods only; nothing whose name refers to a 2026 U.S. Championship; no "
        "broadcast-archive file; no result of either 2026 U.S. Championship read; the freeze-3d files unchanged.",
        "",
    ]
    return "\n".join(out).rstrip("\n") + "\n"


def main() -> int:
    sys.stdout.write(spec() if "--spec" in sys.argv[1:] else e21(Data()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
