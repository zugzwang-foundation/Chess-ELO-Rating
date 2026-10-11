#!/usr/bin/env python3
"""E18 report: the self-calibrating tables (SPEC-SELFCAL v1.0); writes docs/evidence/E18_self-calibration.md.

Reads analysis/aggregates/E18_coverage.json (analysis/e18_coverage_extract.py, needs data/) and, once Phase 3 has run,
analysis/aggregates/E18_selfcal.json (the yearly tables, the three-way test, the parameters over time). Python standard
library only; deterministic.

Usage: python3 analysis/e18_selfcal_report.py > docs/evidence/E18_self-calibration.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates"
P: list[str] = []
p = P.append


def coverage(c: dict) -> None:
    years = sorted(y for y in c["sample_by_year"]["standard"] if y >= "2020")
    arch = c["archive_by_year"]
    p("## 1 The games")
    p("")
    p("**2016 to 2019.** No free historical database could be used legitimately: The Week in Chess is \"free for personal "
      "use only\", with all rights reserved; PGN Mentor's files carry a copyright notice and no licence; KingBase states "
      "none (SPEC-SELFCAL §2, checked on 2026-10-11). The data therefore start with the Lichess broadcast archive's first "
      "file, January 2020.")
    p("")
    p("**FIDE IDs.** E2's sample needs both players' FIDE IDs, to read their ratings on the list in force; the archive's "
      "games carry them only from 2023, and in numbers only from March 2024:")
    p("")
    p("| year | games with a result, standard variant | both FIDE IDs | sample: standard | rapid | blitz |")
    p("|---|---|---|---|---|---|")
    for y in years:
        s = {tc: c["sample_by_year"][tc].get(y, 0) for tc in ("standard", "rapid", "blitz")}
        p(f"| {y}{' (to September)' if y == '2026' else ''} | {arch['with_result_standard_variant'].get(y, 0):,} | "
          f"{arch['both_fide_ids'].get(y, 0):,} | {s['standard']:,} | {s['rapid']:,} | {s['blitz']:,} |")
    p("")
    p(f"Games dated after 30 September 2026 dropped: {c['cutoff'].get('dropped_after_cutoff', 0)}. The sample is E2's, "
      "built with E2's functions through E10's builder over every archive file on disk (2020-01 to 2026-09).")
    p("")
    p("The standard sample by year and 100-point level band (the band of the two players' mean rating on the list in "
      "force):")
    p("")
    bands = sorted({int(b) for yy in c["standard_by_year_band"].values() for b in yy})
    yrs = [y for y in years if c["standard_by_year_band"].get(y)]
    p("| level band | " + " | ".join(yrs) + " |")
    p("|---|" + "---|" * len(yrs))
    for b in bands:
        lab = "below 1500" if b == 1450 else "2800 and above" if b == 2850 else f"{b - 50}–{b + 49}"
        p(f"| {lab} | " + " | ".join(f"{c['standard_by_year_band'][y].get(str(b), 0):,}" for y in yrs) + " |")
    p("")
    p("**Each year's window** (SPEC-SELFCAL §4: the 36 months before the year, which the data must cover; cut at the "
      "March 2024 compression; lengthened while a calendar year inside it has fewer than "
      f"{c['rule']['games_a_year']:,} standard games, pro rata for a part year; no table otherwise):")
    p("")
    p("| table of | window | months | standard games | cut at the compression | lengthened by | the years inside it | "
      "table |")
    p("|---|---|---|---|---|---|---|---|")
    for y, w in sorted(c["windows"].items()):
        per = "; ".join(f"{yy}: {v['games']:,} in {v['months']} months" for yy, v in w.get("per_year", {}).items()) or "—"
        p(f"| {y} | {w['from']} to {w['to']} | {w.get('months', '—')} | "
          f"{format(w['games'], ',') if 'games' in w else '—'} | {'yes' if w['cut_at_compression'] else 'no'} | "
          f"{w['extended_months']} months | {per} | {'yes' if w['table'] else 'no: ' + w['reason']} |")
    p("")
    first = c["first_table_year"]
    p(f"**The first table is {first}'s**, fitted on the games of its window, so the three-way test (§3) and the "
      f"self-calibrating replay of today's top 100 (E19) start in {first}: before it the self-calibrating system has no "
      "table of its own and uses table 8.1.2 as FIDE applies it (SPEC-SELFCAL W4). As the brief asks, this is said "
      "plainly: 2016 to 2019 could not be sourced legitimately, and the archive's games before 2023, and most before "
      "March 2024, carry no FIDE ID.")
    p("")


FORM_WORDS = {"E": "form E, kappa exp(lambda l)", "P": "form P, piecewise-linear kappa by 200-point knot"}
LEVELS = (("2050", "2000–2099"), ("2450", "2400–2499"), ("2750", "2700–2799"))
F_NAMES = {"l0": "(1) table 8.1.2 as FIDE applied it", "first": "(2) the first table, kept frozen",
           "year": "(3) the year's table"}


def sg(x: float, d: int = 4) -> str:
    s = f"{x:+.{d}f}"
    return ("+" + s[1:] if float(s) == 0 else s).replace("-", "−")


def num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace("-", "−")


def iv(b: dict, d: int = 4) -> str:
    return f"{sg(b['mean'], d)} ({sg(b['lo'], d)} to {sg(b['hi'], d)})"


def form_text(f: dict) -> str:
    return (FORM_WORDS[f["slope"]] + ("; colour term by level, eta + zeta l" if f["colour_by_level"] else
                                      "; one colour term eta")
            + ("; with the draw tail, gamma exp(mu l)" if f["tail"] else "; no draw tail"))


def tables(s: dict) -> None:
    p("## 2 The yearly tables")
    p("")
    years = s["table_years"]
    p(f"Tables were fitted for {', '.join(years)} (§1: no earlier year has a window). Each fit starts from Freeze 3's "
      "standard table; the first is fitted without caps, each later one within annex T7.1's yearly caps relative to the "
      "table before it (SPEC-SELFCAL §6).")
    p("")
    p("| table of | window | months | games | form | how the form was set |")
    p("|---|---|---|---|---|---|")
    for y in years:
        tb, ch = s["tables"][y], s["choice"][y]
        how = ("chosen on the selection months " + ", ".join(ch["selection"][:1] + ["…"] + ch["selection"][-1:])
               if ch.get("made") else ch["reason"])
        p(f"| {y} | {tb['window'][0]} to {tb['window'][1]} | {tb['months']} | {tb['games']:,} | {form_text(tb['form'])} | "
          f"{how} |")
    p("")
    for y in years:
        ch = s["choice"][y]
        if not ch.get("made"):
            continue
        st, ct, lp = ch["slope_test"], ch["colour_test"], ch["tail_condition"]
        p(f"**The rule of choice for {y}** (SPEC-TABLE-FIT v1.2 §3), on the selection months {ch['selection'][0]} to "
          f"{ch['selection'][-1]}, each forecast by a fit on the window's months before it; the log-loss difference, nats "
          "a game, with its month-block 95 % interval; a more flexible form replaces the simpler only when the interval "
          "lies below zero:")
        p("")
        p("| step | candidate minus the simpler | chosen |")
        p("|---|---|---|")
        p(f"| slope by level: form P against form E | {iv(st, 5)} | form {ch['slope']} |")
        p(f"| colour by level: with zeta against without | {iv(ct, 5)} | "
          f"{'with zeta' if ch['colour'] else 'without zeta'} |")
        bt = lp["bands_tested"]
        out_b = [str(r["band"] - 50) + "–" + str(r["band"] + 49) for r in bt if r.get("outside")]
        p(f"| the draw tail (v1.1 §4.6: a level band of at least 1,000 games outside ±0.01) | {len(bt)} bands tested, "
          f"{len(out_b)} outside{': ' + ', '.join(out_b) if out_b else ''} | "
          f"{'with the tail' if ch['chosen']['tail'] else 'no tail'} |")
        p("")
        c = s["confirmation"].get(y, {})
        if c.get("differences"):
            p(f"On the confirmation months {c['months'][0]} to {c['months'][-1]}, not used to choose, the chosen form's "
              "rolling fits score (log-loss difference, nats a game): against Layer 0 "
              f"{iv(c['differences']['chosen-l0'], 5)}"
              + (f"; against the table in force, {years[years.index(y) - 1]}'s, "
                 f"{iv(c['differences']['chosen-in_force'], 5)}" if "chosen-in_force" in c["differences"] else "")
              + ".")
            p("")
    p("The parameters of each table, with standard errors from the inverse observed information and 95 % intervals from "
      "2,000 parametric draws; a parameter on a cap's bound has none:")
    p("")
    names = []
    for y in years:
        for k in s["tables"][y]["par"]:
            if k not in names:
                names.append(k)
    p("| parameter | " + " | ".join(years) + " |")
    p("|---|" + "---|" * len(years))
    for k in names:
        cells = []
        for y in years:
            tb = s["tables"][y]
            if k not in tb["par"]:
                cells.append("—")
                continue
            pr = tb["parameters"][k]
            if k not in tb["free"]:
                fixed = "fixed" if pr["on_bound"] is None else f"on the cap's {pr['on_bound']} bound"
                cells.append(f"{num(pr['value'])} ({fixed})")
            else:
                cells.append(f"{num(pr['value'])} (SE {pr['se']:.4f}; {num(pr['low'])} to {num(pr['high'])})")
        p(f"| {k} | " + " | ".join(cells) + " |")
    p("")


def three_way(s: dict) -> None:
    years = s["table_years"]
    first = years[0]
    p("## 3 The three-way test")
    p("")
    p("Every standard sample game of each year (2026: January to September), forecast by (1) table 8.1.2 as FIDE "
      "applied it (Layer 0 with the rules in force, three outcomes by E2's split with the window's draw rates), (2) the "
      f"first table, {first}'s, kept frozen, and (3) the year's own table; three-outcome log-loss and the expected-score "
      "Brier score, means per game; differences with month-block 95 % intervals over the year's months (blocks of 3, "
      "2,000 resamples, seed 20261009). Self-calibration earns its name in a year when (3) beats (2) with the interval "
      "below zero and both beat (1) likewise (SPEC-SELFCAL §7); in the first year (2) and (3) are one table.")
    p("")
    p("| year | games | log-loss (1) | (2) | (3) | Brier (1) | (2) | (3) | (3) − (2) | (3) − (1) | (2) − (1) | verdict |")
    p("|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows = [(y, s["three_way"][y]) for y in years] + [("pooled", s["three_way_pooled"])]
    for y, r in rows:
        mn, df = r["means"], r["differences"]
        n = mn["year"]["n"]
        d32, d31, d21 = df.get("year-first"), df["year-l0"], df["first-l0"]
        beats = lambda b: b["hi"] < 0
        if y == first:
            verdict = ("first year: (2) = (3); " + ("both beat (1)" if beats(d31) else "(3) does not beat (1)"))
        elif y == "pooled":
            verdict = "—"
        else:
            ok = beats(d32) and beats(d31) and beats(d21)
            verdict = ("earns its name" if ok else "does not: " + "; ".join(
                w for w, c in (("(3) does not beat (2)", not beats(d32)), ("(3) does not beat (1)", not beats(d31)),
                               ("(2) does not beat (1)", not beats(d21))) if c))
        p(f"| {y} | {n:,} | {mn['l0']['ll']:.5f} | {mn['first']['ll']:.5f} | {mn['year']['ll']:.5f} | "
          f"{mn['l0']['brier']:.5f} | {mn['first']['brier']:.5f} | {mn['year']['brier']:.5f} | "
          f"{iv(d32, 5) if d32 and y != first else '—'} | {iv(d31, 5)} | {iv(d21, 5)} | {verdict} |")
    p("")
    for y in years:
        r = s["three_way"][y]
        p(f"**{y}, by level band**: the log-loss difference, nats a game, with its month-block interval:")
        p("")
        p("| level band | games | (3) − (1) | (3) − (2) |")
        p("|---|---|---|---|")
        for mid, b in sorted(r["by_band_differences"]["year-l0"].items(), key=lambda kv: int(kv[0])):
            lab = "below 1500" if mid == "1450" else "2800 and above" if mid == "2850" else f"{int(mid) - 50}–{int(mid) + 49}"
            b2 = r["by_band_differences"].get("year-first", {}).get(mid)
            p(f"| {lab} | {b['n']:,} | {iv(b, 4)} | {iv(b2, 4) if b2 and y != first else '—'} |")
        p("")
        p(f"**{y}, calibration**: the favourite's residual S − E by level band, pooled over gaps, with its "
          "cluster-robust standard error over favourites; and rule (a) by level band and 50-point gap (cells of at least "
          "1,000 games tested against ±0.01, Holm–Bonferroni at a familywise 5 %):")
        p("")
        p("| level band | games | " + " | ".join(F_NAMES[f] for f in ("l0", "first", "year")) + " |")
        p("|---|---|---|---|---|")
        for mid in sorted(r["bands"]["year"], key=int):
            cells = []
            for f in ("l0", "first", "year"):
                st = r["bands"][f][mid]
                cells.append(f"{sg(st['mean'])} ({st['se']:.4f})" if st.get("se") else f"{sg(st['mean'])}")
            lab = "below 1500" if mid == "1450" else "2800 and above" if mid == "2850" else f"{int(mid) - 50}–{int(mid) + 49}"
            p(f"| {lab} | {r['bands']['year'][mid]['n']:,} | " + " | ".join(cells) + " |")
        p("")
        p("| forecast | cells shown (at least 200 games) | tested (at least 1,000) | outside ±0.01 | level bands "
          "significantly outside ±0.01 |")
        p("|---|---|---|---|---|")
        for f in ("l0", "first", "year"):
            c = r["cells"][f]
            lp = r["level_pattern"][f]
            bands_out = [str(x["band"] - 50) + "–" + str(x["band"] + 49) for x in lp["bands_tested"] if x.get("outside")]
            p(f"| {F_NAMES[f]} | {len(c['shown'])} | {c['tested']} | {c['outside']} | "
              f"{', '.join(bands_out) if bands_out else 'none'} |")
        p("")


def parameters(s: dict) -> None:
    years = s["table_years"]
    t812, ref = s["table_812"], s["freeze3_reference"]
    p("## 4 The parameters over time")
    p("")
    p("Each year's table beside table 8.1.2's constant values and, for reference, Freeze 3's table (fitted on games of "
      "2023-10 to 2026-09, the championship's table, not part of the self-calibrating series); 95 % intervals from "
      "2,000 parametric draws of each fit (SPEC-SELFCAL §8):")
    p("")
    p("| quantity | table 8.1.2 | Freeze 3's table | " + " | ".join(years) + " |")
    p("|---|---|---|" + "---|" * len(years))

    def cell(y, path, d, scale=1.0):
        x = s["tables"][y]["derived"]
        for k in path:
            x = x[k]
        return f"{x['value'] * scale:.{d}f} ({x['low'] * scale:.{d}f} to {x['high'] * scale:.{d}f})"
    for mid, lab in LEVELS:
        p(f"| White's edge at {lab}, rating points | 0 | {ref['white_edge_points'][mid]:.1f} | "
          + " | ".join(cell(y, ['white_edge_points', mid], 1) for y in years) + " |")
    for mid, lab in LEVELS:
        p(f"| White's expected score at equal ratings, {lab} | 0.500 | {ref['white_score_equal'][mid]:.3f} | "
          + " | ".join(cell(y, ['white_score_equal', mid], 3) for y in years) + " |")
    for mid, lab in LEVELS:
        p(f"| draw rate at equal ratings, {lab} | none (no draw model) | {ref['draw_rate_equal'][mid]:.3f} | "
          + " | ".join(cell(y, ['draw_rate_equal', mid], 3) for y in years) + " |")
    for mid, lab in LEVELS:
        p(f"| slope at an even gap, {lab}, expected score per 100 points | {t812['slope_even'] * 100:.4f} | "
          f"{ref['slope_even'][mid] * 100:.4f} | " + " | ".join(cell(y, ['slope_even', mid], 4, 100.0) for y in years)
          + " |")
    p(f"| a 100-point favourite's expected score at 2700–2799, no colour | {t812['favourite_100_at_2700']:.3f} | "
      f"{ref['favourite_100_at_2700']:.3f} | " + " | ".join(cell(y, ['favourite_100_at_2700'], 3) for y in years) + " |")
    p("")
    p("The draw rate at equal ratings by level band, every band:")
    p("")
    p("| level band | Freeze 3's table | " + " | ".join(years) + " |")
    p("|---|---|" + "---|" * len(years))
    for mid in sorted(ref["draw_rate_equal"], key=int):
        lab = "below 1500" if mid == "1450" else "2800 and above" if mid == "2850" else f"{int(mid) - 50}–{int(mid) + 49}"
        p(f"| {lab} | {ref['draw_rate_equal'][mid]:.3f} | " + " | ".join(cell(y, ['draw_rate_equal', mid], 3) for y in years)
          + " |")
    p("")


def limits(s: dict) -> None:
    years = s["table_years"]
    p("## 5 Limits")
    p("")
    p(f"- **Two tables, not seven.** The data allow tables for {', '.join(years)} only (§1); the test of "
      "self-calibration rests on one year in which the year's table and the frozen first table differ.")
    p("- **Short windows.** The first table's window is ten months, cut at the March 2024 compression; the second's is "
      "22. A window under 22 months makes no choice of form (SPEC-SELFCAL §5).")
    p("- **The caps** bind the second table to within annex T7.1's yearly changes of the first, whatever the data say; "
      "a parameter on a cap's bound is shown as such (§2), and the intervals of §4 treat it as fixed, so they understate "
      "that table's uncertainty.")
    conf = [c["differences"].get("chosen-in_force") for c in s["confirmation"].values()]
    agree = all(d is not None and d["mean"] < 0 for d in conf) and conf
    p("- **Six selection months.** The rule of choice compares candidates on six months with blocks of three, so its "
      "bootstrap interval rests on few distinct resamples; on the confirmation months, not used to choose, the chosen "
      + ("form scores better than the table in force (§2)." if agree else
         "form does not score better than the table in force (§2)."))
    p("- **The broadcast population.** Broadcast events are stronger and more international than the rated pool; the "
      "tables describe that population until FIDE's tournament reports test the method (annex T8.6).")
    p("- **Standard only.** Rapid and blitz are not fitted: their earlier rules are not transcribed.")
    p("")


def main() -> int:
    c = json.loads((AGG / "E18_coverage.json").read_text(encoding="utf-8"))
    s_path = AGG / "E18_selfcal.json"
    p("# E18 — Self-calibrating tables: one table a year, each fitted only on the games before it")
    p("")
    p("Status: DRAFT — evidence for the proposal, session ELO-8, under `docs/specs/SPEC-SELFCAL_v1_0.md` (written before "
      "any yearly table was fitted). Generated by `analysis/e18_selfcal_report.py` from "
      "`analysis/aggregates/E18_coverage.json`" + (" and `analysis/aggregates/E18_selfcal.json`" if s_path.exists() else "")
      + ", written from `data/` by the extraction scripts named there; do not edit by hand. Licence: CC BY 4.0 "
      "(`docs/LICENSE-docs.md`). Games: the Lichess broadcast archive (https://database.lichess.org/broadcast/), CC "
      "BY-SA 4.0, attributed; aggregates only [V 4]. Ratings: FIDE's monthly standard lists, analysed and never "
      "redistributed [V 3]. Every parameter is PROVISIONAL-FITTED.")
    p("")
    coverage(c)
    if not s_path.exists():
        p("## 2 The yearly tables, the three-way test and the parameters over time")
        p("")
        p("To follow in this session's Phase 3, under SPEC-SELFCAL §5 to §8.")
    else:
        s = json.loads(s_path.read_text(encoding="utf-8"))
        tables(s)
        three_way(s)
        parameters(s)
        limits(s)
    sys.stdout.write("\n".join(P) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
