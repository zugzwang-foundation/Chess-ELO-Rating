#!/usr/bin/env python3
"""E21, Tier 0 (session ELO-D2, step 4; needs data/): the parser fix and the list-change puzzle, on the pilot's 2,000
pages already held (docs/specs/SPEC-SOURCING_v1_1.md §8), totals only.

1. **The parser fix.** The pilot's pages read by the extended parser (analysis/e21_club_common.py) against E17's: the
   tournaments FIDE prints with Ro 0 and without K, their game rows, and the game rows printed without a colour mark;
   for the pages that hold them, the published list change against the page.
2. **The puzzle.** Every page the pilot read is classified as E21 §5.2 classifies it, by FIDE's own inputs (the page's Ro,
   the opponent's rating as printed, K as printed, the rules in force at each tournament's start, src/layer0_history/):
   the published change (the period's list minus the list before) equals the page's total rounded once; else a
   tournament's Ro is not the list before's; else the page holds more or fewer games than the list counts; else
   unexplained. On the unexplained pages the known rules are tested first, each by recomputing the period's change as the
   rule would have it and asking whether it then equals the published change exactly:
   - R-23, the cap on K times the games of a period, with n the games the list counts and K the list before's;
   - R-22b, the K published on the list before instead of the K printed;
   - R-32, the rating floor: a change that would take the player below 1400;
   - R-09 and R-10, the periods a tournament may be rated in: a tournament outside them left out;
   - R-12, games against a player unrated when the event began (an opponent not on the list in force) left out;
   - R-25, rounding per tournament instead of once per period (SPEC-L0's alternative, Q-1);
   beside them rounding towards zero, which no rule states, for the record of E21's note; then, decided after seeing the
   pilot (SPEC-SOURCING v1.1 §4: FIDE's pages print ratings that often differ from the
   lists as published): the opponents' ratings as published on the list in force instead of as printed. How many pages
   each explains, how many of the pages that already match it would break (its control), how many a known rule or the
   published ratings explain, and what remains. Nothing here is a claim about how FIDE computes: what stays
   unexplained is NOT VERIFIED.

The regulations are cited as SPEC-L0 v1.5 §3 transcribes them [V 1]. No player's name, FIDE ID or row leaves data/.
Python standard library only.

Usage: python3 analysis/e21_tier0_extract.py > analysis/aggregates/E21_tier0.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e21_club_common as cc  # noqa: E402  (the extended parser, the resolver, the groups)
import e17_top100_extract as ex  # noqa: E402  (E17's parser, to compare)
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402

fs = cc.fs
FLOOR = 1400                      # R-32: "Players whose ratings drop below 1400 are shown as unrated on the next list."
CAP = 700                         # R-23: K x n may not exceed 700


def start_of(t: dict, period: str) -> date:
    return date.fromisoformat(t["start"]) if t["start"] else date.fromisoformat(f"{fs.month_add(period, -1)}-01")


def change(ro: int, games: list[dict], start: date) -> Decimal:
    """The sum of Delta R over a tournament's games, as Layer 0 computes it from the given inputs."""
    return sum(lh.deltas(ro, [(g["rating"], g["score"]) for g in games], start), Decimal(0))


def round_down(x: Decimal) -> int:
    return int(x.to_integral_value(rounding=ROUND_DOWN))


def published_total(key: tuple, pg: dict, ids: dict, lists: dict, own: bool) -> tuple[Decimal, int, int]:
    """The period's change with the opponents' ratings as published on the list in force at each tournament's start
    (and, with own, the player's too), where FIDE's page prints another; the games and tournaments so changed."""
    pid, period = key
    total, moved, moved_own = Decimal(0), 0, 0
    for ti, t in enumerate(pg["tournaments"]):
        if t["unrated"]:
            continue
        m0 = cc.list_in_force(t["start"], period)
        ro = t["ro"]
        if own and pid in lists.get(m0, {}) and lists[m0][pid][0] != ro:
            ro, moved_own = lists[m0][pid][0], moved_own + 1
        rows = []
        for gi, g in enumerate(t["games"]):
            oid = ids[(key, ti, gi)]
            pub = lists.get(m0, {}).get(oid, (None,))[0] if oid else None
            if pub is not None and not g["capped"] and pub != g["rating"]:
                moved += 1
                rows.append({**g, "rating": pub})
            else:
                rows.append(g)
        total += Decimal(t["k"]) * change(ro, rows, start_of(t, period))
    return total, moved, moved_own


R23, R22B, R32, R0910, R12, R25 = ("R-23: K × games capped at 700", "R-22b: the K of the list before",
                                   "R-32: the floor of 1400", "R-09, R-10: the periods a tournament may be rated in",
                                   "R-12: games against a player unrated when the event began",
                                   "R-25: rounding per tournament")
KNOWN = (R23, R22B, R32, R0910, R12, R25)
TRUNC = "rounding towards zero (no rule states it)"
PUBLISHED_OPP = "the opponents' ratings as published (after seeing the pilot)"
PUBLISHED_ALL = "the player's and the opponents' ratings as published (after seeing the pilot)"


def variants(key: tuple, pg: dict, prev: tuple, cur: tuple, per_t: list, total: Decimal, ids: dict,
             lists: dict) -> tuple[dict, Counter]:
    """The period's change, rounded, as each rule would have it on this page; None where the rule changes nothing."""
    pid, period = key
    n, k_prev = cur[1], prev[2]
    notes = Counter()
    v: dict = {}
    k_cap = CAP // n if n and k_prev * n > CAP else k_prev
    notes["R-23 would cap K"] += k_prev * n > CAP
    notes["printed K below the list before's"] += any(t["k"] < k_prev for t, _x in per_t)
    t23 = sum((Decimal(min(t["k"], k_cap)) * x for t, x in per_t), Decimal(0))
    v[R23] = layer0.round_change(t23) if t23 != total else None
    notes["printed K not the list before's"] += any(t["k"] != k_cap for t, _x in per_t)
    t22 = sum((Decimal(k_cap) * x for t, x in per_t), Decimal(0))
    v[R22B] = layer0.round_change(t22) if t22 != total else None
    below = prev[0] + layer0.round_change(total) < FLOOR
    notes["the change would take the player below 1400"] += below
    v[R32] = FLOOR - prev[0] if below else None
    keep = []
    for t, x in per_t:
        end = date.fromisoformat(t["end"]) if t["end"] else start_of(t, period)
        if layer0.rules.earliest_rating_period(end) <= period <= layer0.rules.latest_rating_period(end):
            keep.append((t, x))
        else:
            notes["tournaments outside the periods that may rate them"] += 1
    v[R0910] = layer0.round_change(sum((Decimal(t["k"]) * x for t, x in keep), Decimal(0))) \
        if len(keep) < len(per_t) else None
    alt, dropped, unidentified = Decimal(0), 0, 0
    for ti, t in enumerate(pg["tournaments"]):
        if t["unrated"]:
            continue
        m0 = cc.list_in_force(t["start"], period)
        kept = []
        for gi, g in enumerate(t["games"]):
            oid = ids[(key, ti, gi)]
            unidentified += oid is None
            if oid is not None and oid not in lists.get(m0, {}):
                dropped += 1
            else:
                kept.append(g)
        alt += Decimal(t["k"]) * change(t["ro"], kept, start_of(t, period))
    notes["games against an opponent not on the list in force"] += dropped
    notes["unidentified"] += unidentified
    v[R12] = layer0.round_change(alt) if dropped else None
    v[R25] = sum(layer0.round_change(Decimal(t["k"]) * x) for t, x in per_t) if len(per_t) > 1 else None
    v[TRUNC] = round_down(total)
    p_opp, moved, _o = published_total(key, pg, ids, lists, own=False)
    notes["games whose opponent's published rating differs"] += moved
    notes["pages with such a game"] += moved > 0
    v[PUBLISHED_OPP] = layer0.round_change(p_opp) if moved else None
    p_all, moved_all, own_moved = published_total(key, pg, ids, lists, own=True)
    notes["own_moved"] += own_moved
    v[PUBLISHED_ALL] = layer0.round_change(p_all) if (moved_all or own_moved) else None
    return v, notes


def main() -> int:
    plan = json.loads(fs.PLAN.read_text(encoding="utf-8"))
    sample = {(s["id"], s["period"]): s for s in plan["sample"]}
    pages, e17_read = {}, set()
    for key in sample:
        f = fs.CALCS / f"{key[0]}_{key[1]}.html"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8-sig", errors="replace")
        pages[key] = cc.parse_page_club(text)
        try:
            ex.parse_page(text)
            e17_read.add(key)
        except Exception:
            pass
    months = sorted({fs.month_add("2025-12", -k) for k in range(0, 24)} | {fs.month_add("2025-01", 1 - k)
                                                                          for k in range(1, 4)})
    lists = cc.read_lists(months)
    ids, how = cc.resolve_all(pages)
    first = fs.first_rated()
    births = cc.births_of({k[0] for k in pages}, [fs.FRAME_LIST])
    out: dict = {"label": "Tier 0, on the pilot's pages already held; the last test was decided after seeing the pilot",
                 "pages": len(pages), "read_by_e17": len(e17_read), "opponents": how}

    # 1. the parser fix
    fix = Counter()
    for key, pg in pages.items():
        unr = [t for t in pg["tournaments"] if t["unrated"]]
        rows = [g for t in pg["tournaments"] for g in t["games"]]
        fix["game_rows"] += len(rows)
        fix["game_rows_unmarked"] += sum(1 for g in rows if g["mark"] is None)
        fix["pages_with_an_unmarked_row"] += any(g["mark"] is None for g in rows)
        fix["game_rows_printed_without_k"] += sum(1 for g in rows if g["k"] is None)
        if unr:
            fix["pages_with_a_tournament_printed_without_k"] += 1
            fix["tournaments_printed_without_k"] += len(unr)
            fix["of_them_ro_0"] += sum(1 for t in unr if t["ro"] == 0)
            fix["of_them_every_change_0"] += sum(1 for t in unr if all(g["chg"] == 0 for g in t["games"]))
            fix["of_them_rp_printed"] += sum(1 for t in unr if t["rp"])
            fix["their_pages_not_read_by_e17"] += key not in e17_read
            prev, cur = lists[fs.month_add(key[1], -1)].get(key[0]), lists[key[1]].get(key[0])
            others = [t for t in pg["tournaments"] if not t["unrated"]]
            if prev and cur:
                fix["their_pages_on_both_lists"] += 1
                rest = sum((Decimal(t["k"]) * change(t["ro"], t["games"], start_of(t, key[1])) for t in others),
                           Decimal(0))
                fix["their_list_change_equals_the_other_tournaments"] += cur[0] - prev[0] == layer0.round_change(rest)
                fix["their_list_games_equal_the_rated_rows"] += cur[1] == sum(len(t["games"]) for t in others)
                fix["their_list_games_equal_every_row"] += cur[1] == sum(len(t["games"]) for t in pg["tournaments"])
                fix["their_players_first_rated_on_the_list_before"] += first.get(key[0]) == fs.month_add(key[1], -1)
                # R-12 as SPEC-L0 v1.5 reads it (Q-12): rated as a rated player with the rating of the list before
                r12 = rest + sum((Decimal(prev[2]) * change(prev[0], t["games"], start_of(t, key[1])) for t in unr),
                                 Decimal(0))
                fix["their_list_change_reproduced_as_rated_with_the_list_befores_rating"] += (
                    cur[0] - prev[0] == layer0.round_change(r12))
                fix["their_list_change_within_7_points_so"] += abs(cur[0] - prev[0] - layer0.round_change(r12)) <= 7
                fix["their_list_change_not_zero"] += cur[0] != prev[0]
    out["parser_fix"] = dict(fix)

    # the ratings the pages print against the lists as published (every page read)
    pr = Counter()
    for key, pg in pages.items():
        pid, period = key
        for ti, t in enumerate(pg["tournaments"]):
            if t["unrated"]:
                continue
            m0 = cc.list_in_force(t["start"], period)
            own = lists.get(m0, {}).get(pid)
            pr["tournaments"] += 1
            if own:
                pr["tournaments: Ro equals the player's rating on the list in force"] += own[0] == t["ro"]
                pr["tournaments: Ro within 5 points of it"] += 0 < abs(own[0] - t["ro"]) <= 5
                pr["tournaments: Ro 6 points or more from it"] += abs(own[0] - t["ro"]) > 5
            else:
                pr["tournaments: the player not on the list in force"] += 1
            for gi, g in enumerate(t["games"]):
                oid = ids[(key, ti, gi)]
                pub = lists.get(m0, {}).get(oid, (None,))[0] if oid else None
                if g["capped"] or pub is None:
                    continue
                pr["games: opponent identified on the list in force, uncapped"] += 1
                pr["games: the opponent's printed rating equals the list in force"] += pub == g["rating"]
                pr["games: within 5 points of it"] += 0 < abs(pub - g["rating"]) <= 5
                pr["games: 6 points or more from it"] += abs(pub - g["rating"]) > 5
    out["printed_against_published"] = dict(pr)

    # 2. the puzzle: every rule's period change on every page, and the class it is tested on
    cls, tests, remain, controls = Counter(), Counter(), Counter(), Counter()
    other_counts = Counter()
    for key, pg in sorted(pages.items()):
        pid, period = key
        prev, cur = lists[fs.month_add(period, -1)].get(pid), lists[period].get(pid)
        tours = [t for t in pg["tournaments"] if not t["unrated"]]
        if not (prev and cur) or len(tours) < len(pg["tournaments"]):
            cls["not on both lists, or a tournament printed without K"] += 1
            continue
        per_t = [(t, change(t["ro"], t["games"], start_of(t, period))) for t in tours]
        total = sum((Decimal(t["k"]) * x for t, x in per_t), Decimal(0))
        published = cur[0] - prev[0]
        games = sum(len(t["games"]) for t in tours)
        if layer0.round_change(total) == published:
            c = "equal"
        elif any(t["ro"] != prev[0] for t in tours):
            c = "a tournament's Ro is not the list before's"
        elif games != cur[1]:
            c = "the page's games are not the list's"
        else:
            c = "unexplained"
        cls[c] += 1
        v, notes = variants(key, pg, prev, cur, per_t, total, ids, lists)
        for rule, x in v.items():
            if x is None:
                continue
            controls[f"{c}|{rule}|applies"] += 1
            controls[f"{c}|{rule}|reproduced"] += x == published
        if c == "a tournament's Ro is not the list before's":
            base = {t["ro"] for t in tours}
            if len(base) == 1:
                other_counts["Ro: one base for the page"] += 1
                other_counts["Ro: published list equals FIDE's Ro plus the page's rounded total"] += (
                    cur[0] == next(iter(base)) + layer0.round_change(total))
            other_counts["Ro: pages where the player's published rating differs from the page's Ro"] += \
                notes["own_moved"] > 0
        if c == "the page's games are not the list's":
            other_counts["games: page more than list"] += games > cur[1]
            other_counts["games: page fewer than list"] += games < cur[1]
        if c != "unexplained":
            continue
        diff = published - layer0.round_change(total)
        junior = cc.is_junior(births.get(pid))
        newcomer = (first.get(pid) or "") >= fs.CLUB_NEWCOMER_FROM
        tests["pages"] += 1
        tests["by_one_point"] += abs(diff) == 1
        tests["k_40"] += prev[2] == 40
        tests["juniors_or_newcomers"] += junior or newcomer
        tests["published_above_the_page"] += diff > 0
        tests["several_tournaments"] += len(tours) > 1
        for k, x in notes.items():
            tests[f"note: {k}"] += x
        explained = {rule for rule, x in v.items() if x is not None and x == published}
        for r in sorted(explained):
            tests[f"explains: {r}"] += 1
        known = explained & set(KNOWN)
        tests["explained by a known rule"] += bool(known)
        either = known | (explained & {PUBLISHED_OPP})
        tests["explained by a known rule or the published ratings"] += bool(either)
        if not either:
            remain["pages"] += 1
            remain["by_one_point"] += abs(diff) == 1
            remain["k_40"] += prev[2] == 40
            remain["juniors_or_newcomers"] += junior or newcomer
            remain["published_above_the_page"] += diff > 0
            remain["with an opponent not identified"] += notes["unidentified"] > 0
            remain["matched by rounding towards zero"] += TRUNC in explained
    out["classes"] = dict(cls)
    out["other_classes"] = dict(other_counts)
    out["unexplained_tests"] = dict(tests)
    out["remaining"] = dict(remain)
    out["controls"] = dict(controls)
    out["rules"] = {"known": list(KNOWN), "truncation": TRUNC, "published_opponents": PUBLISHED_OPP,
                    "published_all": PUBLISHED_ALL}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
