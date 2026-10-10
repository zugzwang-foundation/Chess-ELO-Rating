#!/usr/bin/env python3
"""SPEC-L0 evidence: recompute every fixture in tests/fixtures/fide_calculator/ from the transcribed tables.

The fixtures record what FIDE's online calculator and FIDE's published per-player
calculations returned on 2026-10-09. This script reads them, reads tables 8.1.1
and 8.1.2 as transcribed in docs/research/VERIFICATION_2026-10-09.md [V 1] and
table 1.4.9 as transcribed in docs/research/VERIFICATION_TITLES.md [VT 1],
recomputes each case under the readings that SPEC-L0 names, and prints which
reading FIDE's output follows. Every derived value stored in a fixture is
recomputed and compared. It checks the fixtures; it is not the rating engine
(CLAUDE.md, hard rule 1). Exact decimal arithmetic, Python standard library only.

Usage: python3 analysis/l0_fixtures_report.py > analysis/OUTPUT_L0_fixtures.md
"""
from __future__ import annotations

import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "fide_calculator"
SWEEP = ROOT / "docs" / "research" / "VERIFICATION_2026-10-09.md"
TITLES = ROOT / "docs" / "research" / "VERIFICATION_TITLES.md"
ONE = Decimal(1)
stored_compared = 0
stored_differ: list[str] = []


def table_after(text: str, marker: str) -> list[list[str]]:
    """Body rows of the first Markdown table after the line containing marker."""
    lines = text[text.index(marker):].split("\n")[1:]
    rows: list[list[str]] = []
    for line in lines:
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    return rows[2:]


def dec(s: str) -> Decimal:
    return Decimal("0" + s if s.startswith(".") else s)


def p_dp_table(rows: list[list[str]]) -> dict[Decimal, int]:
    out = {}
    for r in rows:
        for i in range(0, len(r) - 1, 2):
            if r[i]:
                out[dec(r[i])] = int(r[i + 1])
    return out


def d_pd_table(rows: list[list[str]]) -> list[tuple[int, int | None, Decimal, Decimal]]:
    out = []
    for r in rows:
        for i in range(0, len(r) - 2, 3):
            if not r[i]:
                continue
            if r[i].startswith(">"):
                lo, hi = int(r[i][1:].strip()) + 1, None
            else:
                a, b = r[i].split("-")
                lo, hi = int(a), int(b)
            out.append((lo, hi, dec(r[i + 1]), dec(r[i + 2])))
    return sorted(out, key=lambda t: t[0])


sweep = SWEEP.read_text(encoding="utf-8")
T811 = p_dp_table(table_after(sweep, "**Table 8.1.1 (verbatim layout"))
T812 = d_pd_table(table_after(sweep, "**Table 8.1.2 (verbatim layout"))
T149 = p_dp_table(table_after(TITLES.read_text(encoding="utf-8"), "> 1.4.9 Table"))


def pd(d: int) -> Decimal:
    """Table 8.1.2: PD for a player whose (possibly capped) difference is d = own - opponent."""
    a = abs(d)
    for lo, hi, h, low in T812:
        if lo <= a and (hi is None or a <= hi):
            return h if d >= 0 else low
    raise ValueError(d)


def p2(p: Decimal) -> Decimal:
    """p to two decimals, 0.005 rounded up (SPEC-L0 R-30 reading, NOT VERIFIED for §8.2.3)."""
    return p.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dp(p: Decimal) -> int:
    return T811[p2(p)]


def round_half_away(x: Decimal) -> int:
    """§8.3.4 [V 1]: nearest whole number, 0.5 away from zero."""
    q = abs(x).quantize(ONE, rounding=ROUND_HALF_UP)
    return int(q if x >= 0 else -q)


def capped_d(own: int, opp: int, exempt_2650: bool) -> int:
    d = own - opp
    if abs(d) > 400 and not (exempt_2650 and own >= 2650):
        d = 400 if d > 0 else -400
    return d


def compare(label: str, stored, recomputed) -> None:
    global stored_compared
    stored_compared += 1
    if stored != recomputed:
        stored_differ.append(f"{label}: stored {stored!r}, recomputed {recomputed!r}")


def fmt(x: Decimal) -> str:
    return format(x.normalize(), "f")


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def section_tables() -> None:
    print("## 1 Tables read from the transcriptions\n")
    mirror = all(h + low == ONE for _, _, h, low in T812)
    sym = all(T811[p] == -T811[ONE - p] for p in T811)
    same = sum(1 for p in T811 if T149.get(p) == T811[p])
    print(f"- Table 8.1.1 [V 1]: {len(T811)} entries (p from {min(T811)} to {max(T811)}); "
          f"dp(p) = -dp(1 - p) for every p: {sym}.")
    print(f"- Table 8.1.2 [V 1]: {len(T812)} rows; H + L = 1 in every row: {mirror}; rows contiguous from 0: "
          f"{all(T812[i + 1][0] == T812[i][1] + 1 for i in range(len(T812) - 1)) and T812[0][0] == 0}.")
    print(f"- Table 1.4.9 [VT 1]: {len(T149)} entries; equal to table 8.1.1 entry by entry: {same} of {len(T811)}.\n")


def section_calculator_change() -> None:
    fx = load("calculator_rating_change.json")
    print("## 2 Online calculator, rating change (`calculator_rating_change.json`)\n")
    print("Readings: (a) §8.3.1 as written from 1 October 2025 [V 1] (cap at 400 for players rated below 2650, "
          "full difference from 2650); (b) the plain 400-point cap for everyone.\n")
    print("| id | own | opponent | score | K | D | calculator | (a) as written | (b) plain cap | follows |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    n_a = n_b = 0
    for c in fx["cases"]:
        i = c["inputs"]
        own, opp, score, k = i["own_rating"], i["opponent_rating"], Decimal(str(i["score"])), i["K"]
        a = k * (score - pd(capped_d(own, opp, True)))
        b = k * (score - pd(capped_d(own, opp, False)))
        calc = Decimal(str(c["calculator_change"]))
        n_a += calc == a
        n_b += calc == b
        follows = "both" if calc == a == b else "(a)" if calc == a else "(b)" if calc == b else "neither"
        compare(f"{c['id']} current_rules_change", Decimal(str(c["current_rules_change"])), a)
        compare(f"{c['id']} agrees_with_current_rules", c["agrees_with_current_rules"], calc == a)
        compare(f"{c['id']} agrees_with_plain_400_cap", c["agrees_with_plain_400_cap"], calc == b)
        print(f"| {c['id']} | {own} | {opp} | {fmt(score)} | {k} | {own - opp} | {fmt(calc)} | {fmt(a)} | {fmt(b)} | {follows} |")
    m = len(fx["cases"])
    print(f"\nAgreement: (a) {n_a} of {m}; (b) {n_b} of {m}. The calculator differs from (a) only where the player "
          f"is rated 2650 or above and |D| > 400.\n")


def initial_2022(rc: Decimal, w: Decimal, n: int) -> int:
    half = Decimal(n) / 2
    ru = rc + 40 * (w - half) if w >= half else rc + dp(w / n)
    return int(ru.quantize(ONE, rounding=ROUND_HALF_UP))


def initial_2024(ra_opp: Decimal, w: Decimal, n: int) -> tuple[Decimal, Decimal, int, int]:
    ra = (n * ra_opp + 3600) / (n + 2)
    p = (w + 1) / (n + 2)
    ru = int((ra + dp(p)).quantize(ONE, rounding=ROUND_HALF_UP))
    return ra, p, dp(p), min(ru, 2200)


def section_calculator_initial() -> None:
    fx = load("calculator_initial_rating.json")
    print("## 3 Online calculator, initial rating (`calculator_initial_rating.json`)\n")
    print("Readings: (c) the archived rule of 1 January 2022 till 29 February 2024 [VT 2] (Ru = Ra + 20 for each "
          "half point over 50 %, Ra + dp below 50 %, Ra the average of the rated opponents); (d) the current rule "
          "[V 1] §8.2.2-8.2.3 (two hypothetical opponents rated 1800 scored as draws, maximum 2200), p to two "
          "decimals with 0.005 rounded up.\n")
    print("| id | Rc | W | N | calculator | (c) archived | (d) current |")
    print("|---|---|---|---|---|---|---|")
    n_c = n_d = 0
    for c in fx["cases"]:
        i = c["inputs"]
        rc, w, n = Decimal(i["Rc"]), Decimal(str(i["W"])), i["N"]
        cc = initial_2022(rc, w, n)
        ra, p, d, ru = initial_2024(rc, w, n)
        calc = c["calculator_initial_rating"]
        n_c += calc == cc
        n_d += calc == ru
        compare(f"{c['id']} rule_2022_initial_rating", c["rule_2022_initial_rating"], cc)
        compare(f"{c['id']} rule_2024", c["rule_2024"],
                {"Ra": str(ra.quantize(Decimal("0.01"))), "p": str(p.quantize(Decimal("0.0001"))), "dp": d,
                 "Ru": ru, "published": ru >= 1400})
        print(f"| {c['id']} | {rc} | {fmt(w)} | {n} | {calc} | {cc} | {ru} |")
    m = len(fx["cases"])
    print(f"\nAgreement: (c) {n_c} of {m}; (d) {n_d} of {m}. F-I04 agrees with both only because 2100 + 100 under "
          f"(c) equals the 2200 maximum under (d).\n")


def month_before(period: str) -> str:
    y, m = int(period[:4]), int(period[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def section_published() -> None:
    fx = load("published_calculations.json")
    print("## 4 FIDE's published per-player calculations (`published_calculations.json`)\n")
    print("Each game is recomputed from the rating FIDE printed for the opponent (the capped value where FIDE "
          "marks the game with '*') and table 8.1.2; tournament sums are compared with FIDE's printed sums.\n")
    print("| id | event | start | Ro | K | games | per-game chg equal | sum equal | K x sum equal | "
          "'*' games with abs(D) = 400 and own < 2650 | of which the opponent is above 2650 | "
          "abs(D) > 400 uncapped with own >= 2650 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    lists = []
    games_all = games_eq = events = sums_eq = ksums_eq = 0
    for c in fx["cases"]:
        total = Decimal(0)
        per_t = 0
        for t in c["tournaments"]:
            ro, k = int(t["Ro"]), int(t["K"])
            eq = 0
            s = Decimal(0)
            star_ok = star = star_hi = unc = unc_ok = 0
            for g in t["games"]:
                opp = int(g["opponent_rating_used"])
                d = ro - opp
                chg = Decimal(g["score"]) - pd(d)
                eq += chg == Decimal(g["chg"])
                s += chg
                if g["capped_marker"]:
                    star += 1
                    star_ok += abs(d) == 400 and ro < 2650
                    star_hi += opp > ro and opp >= 2650      # the real opponent is rated above the printed cap
                elif abs(d) > 400:
                    unc += 1
                    unc_ok += ro >= 2650
            ks = k * s
            events += 1
            games_all += len(t["games"])
            games_eq += eq
            sums_eq += s == Decimal(t["chg"])
            ksums_eq += ks == Decimal(t["K_chg"])
            total += Decimal(t["K_chg"])
            per_t += round_half_away(Decimal(t["K_chg"]))
            print(f"| {c['id']} | {t['event_id']} | {t['start']} | {ro} | {k} | {len(t['games'])} | "
                  f"{eq} of {len(t['games'])} | {s == Decimal(t['chg'])} | {ks == Decimal(t['K_chg'])} | "
                  f"{star_ok} of {star} | {star_hi} | {unc_ok} of {unc} |")
        lists.append((c, total, per_t))
    print(f"\nTotals: {len(fx['cases'])} players, {events} tournament calculations, {games_all} games; Delta R reproduced "
          f"in {games_eq} of {games_all} games, the tournament sum in {sums_eq} of {events}, K x sum in {ksums_eq} of "
          f"{events}.")
    print("\n**K (R-22, R-23).** The K FIDE used against the K published on the previous list, reduced to the "
          "largest whole number with K x n <= 700 where needed; n is the period's games, also printed on the new "
          "list:\n")
    print("| id | previous list K | n (sum over events) | games on the new list | K used | expected | equal |")
    print("|---|---|---|---|---|---|---|")
    for c in fx["cases"]:
        n = sum(int(t["n"]) for t in c["tournaments"])
        used = sorted({int(t["K"]) for t in c["tournaments"]})
        prev_k = c["published_list_k"][month_before(c["rating_period"])]
        expected = prev_k if prev_k * n <= 700 else 700 // n
        print(f"| {c['id']} | {prev_k} | {n} | {c['published_list_games'][c['rating_period']]} | "
              f"{', '.join(map(str, used))} | {expected} | {used == [expected]} |")
    print("\n**R-25 and the base.** The new rating predicted from the previous published list by rounding the "
          "period's change once (§8.3.4 as written) and by rounding each tournament's change separately:\n")
    print("| id | period | previous list | Ro of events starting on or after the previous list | sum of K x chg | "
          "per period | per tournament | published | per-period fits | per-tournament fits |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for c, total, per_t in lists:
        prev = month_before(c["rating_period"])
        base = c["published_list_ratings"][prev]
        ros = sorted({int(t["Ro"]) for t in c["tournaments"] if t["start"][:7] >= prev})
        pub = c["published_list_ratings"][c["rating_period"]]
        b = ros[0] if len(ros) == 1 else base
        a1, a2 = b + round_half_away(total), b + per_t
        print(f"| {c['id']} | {c['rating_period']} | {base} | {', '.join(map(str, ros)) or '-'} | {fmt(total)} | "
              f"{a1} | {a2} | {pub} | {a1 == pub} | {a2 == pub} |")
        compare(f"{c['id']} total_change_shown", Decimal(c["total_change_shown"]), total)
    print("\nWhere FIDE's Ro for an event that started on or after the previous list differs from that published "
          "list, the predictions start from FIDE's Ro (a base correction).\n")


def section_newcomer() -> None:
    fx = load("published_initial_rating.json")
    print("## 5 A first published rating (`published_initial_rating.json`)\n")
    for c in fx["cases"]:
        opp = [int(g["opponent_rating_used"]) for g in c["games"]]
        w = sum(Decimal(g["score"]) for g in c["games"])
        n = len(opp)
        avg = Decimal(sum(opp)) / n
        ra, p, d, ru = initial_2024(avg, w, n)
        cc = initial_2022(avg, w, n)
        pub = c["published_list"][c["rating_period"]]["rating"]
        rp = int(c["calculation_summary"]["Rp"])
        print(f"- {c['id']}: {n} games, score {fmt(w)}, opponents' ratings summing to {sum(opp)} "
              f"(average {fmt(avg)}, printed Rc {c['calculation_summary']['Rc']}).")
        print(f"- Current rule [V 1]: Ra = ({sum(opp)} + 3600) / {n + 2} = {ra.quantize(Decimal('0.0001'))}; "
              f"p = {fmt(w + 1)} / {n + 2} = {p.quantize(Decimal('0.0001'))} -> {p2(p)}; dp = {d}; "
              f"Ru = {(ra + d).quantize(Decimal('0.0001'))} -> {ru}. Published on the {c['rating_period']} list: "
              f"{pub} (equal: {ru == pub}).")
        print(f"- Archived rule [VT 2]: Ra = {fmt(avg)}; Ru = {cc}. FIDE's printed 'Rp': {rp} (equal: {cc == rp}).\n")
        der = c["derived"]
        compare(f"{c['id']} rule_2024.Ru_rounded", der["rule_2024"]["Ru_rounded"], ru)
        compare(f"{c['id']} rule_2022.Ru_rounded", der["rule_2022"]["Ru_rounded"], cc)
        compare(f"{c['id']} sum_of_opponent_ratings", der["sum_of_opponent_ratings"], sum(opp))


def main() -> int:
    print("# SPEC-L0 fixtures, recomputed\n")
    print("Status: generated by `analysis/l0_fixtures_report.py` from `tests/fixtures/fide_calculator/` "
          "(recorded 2026-10-09); do not edit by hand. Cited by "
          "`docs/specs/SPEC-L0_fide-reference-engine_v1_1.md`.\n")
    section_tables()
    section_calculator_change()
    section_calculator_initial()
    section_published()
    section_newcomer()
    print("## 6 Stored derived values\n")
    print(f"{stored_compared} derived values stored in the fixtures were recomputed; {len(stored_differ)} differ.")
    for s in stored_differ:
        print(f"- {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
