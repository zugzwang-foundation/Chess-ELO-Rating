#!/usr/bin/env python3
"""E20, part 2: the greats replayed under FIDE's rules and under the 2025 table applied backwards, from the list of
April 2008 to December 2019 (SPEC-GREATS v1.0 §6; session ELO-9, Phase 3; needs data/).

The players are SPEC-GREATS §2's (analysis/aggregates/GREATS_players.json) with at least one standard rating period of
the window on FIDE's calculations index; the pages are FIDE's per-player calculations (data/raw/fide_calculations_greats/,
fetched once each by tools/data/fetch_greats_calculations.py, whose plan is read here: one rule for fetch and replay),
read by E17's parser, unchanged; the lists are FIDE's own files (data/interim/fide_old/standard/ to January 2015;
data/interim/fide/standard/ and, for names, data/raw/fide/standard/ from February 2015). As E17 and E19:

- the players are replayed together, list by list, each from the published rating of January 2008, the list before the
  first replayed period;
- **Layer 0** applies the rules in force at each tournament's start (src/layer0_greats/: the 350- and 400-point rules,
  K and rounding of the versions transcribed in docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md, and from
  July 2017 src/layer0_history/), checked against FIDE's pages and lists: each game's change, each tournament's
  K x sum and each period's change. A period whose page is missing, or whose change Layer 0 does not reproduce, is
  thin: both systems take FIDE's published change through it, so that the difference between them is carried
  unchanged (SPEC-GREATS §6);
- **rung 2** applies E18's 2025 table (form E with the draw tail), applied backwards, not fitted on that era, through
  E19's own function (eta(L) whole in each band, the published entry to three decimals, the narrowed guard as frozen;
  no 400-point rule); colours from FIDE's colour marks; K by FIDE's K rules in force applied to each system's own rating
  (R61) where the rules reproduce FIDE's printed K on FIDE's ratings, FIDE's K otherwise;
- opponents outside the set at the ratings FIDE's pages print, or, where a page may print a capped value (a gap of
  exactly 350 or 400 points, or FIDE's mark), at the rating of the same name on the list in force when one player of
  that name is consistent with it (R58's approximation); opponents inside the set at their replayed ratings;
- beside the method: without colour, and with every opponent outside the set 10 points lower and higher (R58).

The readings the rules record leaves open are tested on FIDE's own pages: the date the 350-point rule became the
400-point rule (on every game whose gap exceeds 350 points and whose opponent's rating is known), and the rounding
(once per period against once per tournament, and every period whose sum ends in a half point, by the list's date).
Ruling R74 (docs/decisions/D-0017_rulings-on-the-greats.md) adopts 0.5 towards +infinity on the lists before July 2014,
and ruling R80 (docs/decisions/D-0018_rulings-on-elo-9-questions.md) on every list to October 2018, away from zero from
the list of November 2018; the replay runs under R80's reading, under D-0017's (towards +infinity before July 2014, away
from zero from it) as R80 asks, under the rules record's first reading (away from zero on every list) as R74 asks, and,
for information only (D-0017 reading 2), with 0.5 towards +infinity on every list of the window, and reports the thin
periods and the difference under each, with the lists between FIDE's last negative half point rounded towards +infinity
and its first rounded away from zero. Writes analysis/aggregates/E20_greats_replay.json: the validation as counts (R79: the full
reproduction runs locally from the cache), and per player the games and periods replayed, the lists of the thin
periods with their causes, the difference rung 2 - Layer 0 at each year end and on the last list, split into the
table's effect and colour's, and the highest rating within the window under each system with its lists; no page, no
list and no series of published ratings (R72). Python standard library only.

Usage: python3 analysis/e20_greats_replay_extract.py > analysis/aggregates/E20_greats_replay.json
"""
from __future__ import annotations

import csv
import json
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _sub in ("analysis", "tools", "tools/data", "src"):
    sys.path.insert(0, str(ROOT / _sub))
import convert_fide_lists as cfl  # noqa: E402  (the lists' fixed-width columns from February 2015)
import e17_top100_extract as ex  # noqa: E402  (FIDE's page parser and the name key, unchanged)
import e19_top100_selfcal_extract as e19  # noqa: E402  (the self-calibrating expectation, unchanged)
import fetch_greats_calculations as fg  # noqa: E402  (the players' periods: one rule for fetch and replay)
import layer0  # noqa: E402
import layer0_greats as lg  # noqa: E402

OLD = ROOT / "data" / "interim" / "fide_old" / "standard"
NEW = ROOT / "data" / "interim" / "fide" / "standard"
RAW_NEW = ROOT / "data" / "raw" / "fide" / "standard"
PAGES = fg.RAW
SERIES = ROOT / "data" / "interim" / "greats" / "series.json"     # E20 part 1's cache of the published series
SELECTED = fg.SELECTED
LOOKUP_FROM, START, LAST = "2006-01", "2008-01", "2019-12"
TABLE = e19.TABLES[2025]
VARIANTS = ("r2", "r2nc", "r2_outside-10", "r2_outside+10")
SHIFT = {"r2_outside-10": -10, "r2_outside+10": 10}
CAPS = (350, 400)


# ------------------------------------------------------------------ lists
def list_dates() -> list[str]:
    old = [p.stem for p in sorted(OLD.glob("*.tsv")) if LOOKUP_FROM <= p.stem <= "2015-01"]
    return old + [p.stem for p in sorted(NEW.glob("*.tsv")) if "2015-02" <= p.stem <= LAST]


def load_lists(dates: list[str], want: set[str]) -> tuple[dict, dict]:
    """For every list date, the set's players: (rating, games, federation, flag, birth year or None); and each set
    player's name keys on the lists that carry names (to January 2015)."""
    lists: dict[str, dict] = {}
    keys: dict[str, set] = defaultdict(set)
    for m in dates:
        d = {}
        if m <= "2015-01":
            with (OLD / f"{m}.tsv").open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh, delimiter="\t"):
                    if r["id"] in want and r["rating"].isdigit():
                        d[r["id"]] = (int(r["rating"]), int(r["games"]) if r["games"].isdigit() else 0, r["fed"],
                                      r["flag"], None)
                        keys[r["id"]].add(ex.norm(r["name"]))
        else:
            with (NEW / f"{m}.tsv").open(encoding="utf-8") as fh:
                rows = csv.reader(fh, delimiter="\t")
                next(rows)
                for pid, rating, games, _k, by, _sex, fed, flag, _title in rows:
                    if pid in want and rating.isdigit():
                        d[pid] = (int(rating), int(games) if games.isdigit() else 0, fed, flag,
                                  int(by) if by.isdigit() and int(by) > 1900 else None)
        lists[m] = d
    return lists, keys


def full_list(m: str):
    """(id, name, federation, rating) of every rated player on FIDE's list of the date m."""
    if m <= "2015-01":
        with (OLD / f"{m}.tsv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if r["rating"].isdigit():
                    yield r["id"], r["name"], r["fed"], int(r["rating"])
        return
    ratings = {}
    with (NEW / f"{m}.tsv").open(encoding="utf-8") as fh:
        rows = csv.reader(fh, delimiter="\t")
        next(rows)
        for pid, rating, *_rest in rows:
            if rating.isdigit():
                ratings[pid] = int(rating)
    tag = f"{cfl.MONTHS[int(m[5:]) - 1]}{m[2:4]}"
    with zipfile.ZipFile(RAW_NEW / f"standard_{tag}frl.zip") as zf:
        raw = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
    sp = cfl.spans(raw[0], tag.upper())
    (ia, ib), (na, nb), (fa, fb) = sp["ID Number"], sp["Name"], sp["Fed"]
    for line in raw[1:]:
        pid = line[ia:ib].strip()
        if pid in ratings:
            yield pid, line[na:nb].strip(), line[fa:fb].strip(), ratings[pid]


def name_index(needed: dict[str, set]) -> dict[str, dict]:
    """For each list date m with games to resolve, name key -> [(id, federation, rating)] of the players whose name
    key is wanted on m."""
    memo: dict[str, str] = {}
    out: dict[str, dict] = {}
    for m, want in sorted(needed.items()):
        idx = defaultdict(list)
        for pid, name, fed, rating in full_list(m):
            k = memo.get(name)
            if k is None:
                k = memo[name] = ex.norm(name)
            if k in want:
                idx[k].append((pid, fed, rating))
        out[m] = idx
    return out


# ------------------------------------------------------------------ helpers
def prev_of(dates: list[str], t: str) -> str:
    return dates[dates.index(t) - 1]


def list_in_force(dates: list[str], start: str | None, t: str) -> str:
    """The list in force at a tournament's start: the latest list dated in or before the start's month, at most the
    list before the one that rates it (SPEC-L0 R-11a, on the lists of the period: quarterly to July 2009, every two
    months to July 2012, monthly since)."""
    prev = prev_of(dates, t)
    if not start:
        return prev
    before = [d for d in dates if d <= start[:7]]
    m = before[-1] if before else dates[0]
    return min(m, prev)


def list_for_ro(lists: dict, dates: list[str], pid: str, ro: int, start: str | None, t: str) -> str:
    """As E17's: the list in force at the start, or, where the player's rating there is not FIDE's Ro, the latest later
    list before the one rating it on which the player is rated Ro; if none, the list in force at the start."""
    m = list_in_force(dates, start, t)
    if pid in lists[m] and lists[m][pid][0] == ro:
        return m
    i = dates.index(prev_of(dates, t))
    while dates[i] > m:
        if pid in lists[dates[i]] and lists[dates[i]][pid][0] == ro:
            return dates[i]
        i -= 1
    return m


def maybe_capped(g: dict, ro: int) -> bool:
    """A page may print a capped value: FIDE's mark, or a gap of exactly 350 or 400 points (the pages before the mark)."""
    return g["capped"] or abs(ro - g["rating"]) in CAPS


def consistent(r: int, shown: int, ro: int, capped: bool) -> bool:
    if r == shown:
        return True
    return capped and ((r < shown) if shown < ro else (r > shown))


def resolve(g: dict, ro: int, idx: dict) -> int | None:
    """The opponent's rating on the list in force, where the page may print a capped value: the one player of the same
    name key (with the federation printed, else any) whose rating equals the printed one or lies beyond it on the
    same side; otherwise none."""
    cands = idx.get(ex.norm(g["name"]), [])
    for pool in ([c for c in cands if c[1] == g["fed"]], cands):
        ok = {(pid, r) for pid, _f, r in pool if consistent(r, g["rating"], ro, True)}
        if len(ok) == 1:
            return next(iter(ok))[1]
        if len(ok) > 1:
            return None
    return None


def rounding_era(t: str) -> str:
    """The rounding clause of the regulations in force when the list t was published, the 2017 clause split at the list
    from which FIDE's lists round 0.5 away from zero (R80)."""
    if t < lg.ROUNDING_2014_LIST:
        return "lists to June 2014 (the 2007 and 2010 texts)"
    if t < "2017-07":
        return "lists of July 2014 to June 2017 (the 2014 clause)"
    if t < lg.ROUNDING_2018_LIST:
        return "lists of July 2017 to October 2018 (the 2017 clause)"
    return "lists from November 2018 (the 2017 clause)"


def k_rule(ver: str, rating: int, ever2400: bool, ever2300: bool, list_month: str, birth: int | None) -> int:
    """FIDE's K rules of the version in force, for a player with 30 games or more."""
    if ver in ("2007", "2009", "2014"):
        return lg.k_rule(ver, rating, ever2400, 30)
    return layer0.published_k(rating, 30, ever2400, ever2300, list_month, birth)


# ------------------------------------------------------------------ the replay
VAL_KEYS = ("games", "game_delta_differs", "games_not_n", "tournaments", "tournament_sum_differs",
            "tournament_k_chg_differs", "k_rule_differs", "periods_with_page", "period_change_differs",
            "total_shown_differs", "no_page", "cap_candidates", "cap_resolved", "cap_unresolved", "cap_marks",
            "set_games", "set_name_unconfirmed")
READINGS = {                                             # how a period's change on the list t is rounded
    "R80": lambda x, t: lg.round_change(x, t),           # 0.5 towards +infinity to October 2018 (R74, R80), away from it after
    "D-0017": lambda x, t: lg.round_change_d0017(x, t),  # D-0017's: towards +infinity before July 2014, away from it after
    "rules record": lambda x, t: lg.round_change_away(x),    # the rules record's first reading: away from zero throughout
    "towards +infinity throughout": lambda x, t: lg.round_change_up(x),   # for information (D-0017 reading 2)
}


def prepare() -> dict:
    """The lists, pages and look-ups that the replays under both readings share."""
    selected = {str(p["fide_id"]): p["name"] for p in json.loads(SELECTED.read_text(encoding="utf-8"))["players"]
                if p["fide_id"]}
    plan = fg.plan()
    ids = sorted({x.split(":")[0] for x in plan}, key=int)
    dates = list_dates()
    lists, keys = load_lists(dates, set(ids))
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    pages, missing = {}, []
    for pair in plan:
        pid, period = pair.split(":")
        f = PAGES / f"{pid}_{period}.html"
        if f.exists():
            pages[(pid, period)] = ex.parse_page(f.read_text(encoding="utf-8-sig", errors="replace"))
        else:
            missing.append(pair)
    # the opponents whose rating a page may print capped, by the list in force: resolved against that list's names
    needed: dict[str, set] = defaultdict(set)
    for (pid, t), page in pages.items():
        for tr in page["tournaments"]:
            m = list_for_ro(lists, dates, pid, tr["ro"], tr["start"], t)
            for g in tr["games"]:
                if maybe_capped(g, tr["ro"]):
                    needed[m].add(ex.norm(g["name"]))
    first = {p: next((m for m in dates if m >= START and p in lists[m]), None) for p in ids}
    return {
        "selected": selected, "plan": plan, "ids": ids, "dates": dates, "window": [d for d in dates if START < d <= LAST],
        "lists": lists, "key_to_id": {k: p for p in ids for k in keys[p]}, "series": series, "pages": pages,
        "missing": missing, "index": name_index(needed), "first": first,
        "pub": {p: {m: lists[m][p][0] for m in dates if p in lists[m]} for p in ids},
        "birth": {p: next((lists[m][p][4] for m in reversed(dates) if p in lists[m] and lists[m][p][4]), None)
                  for p in ids},
        "reached": {(p, level, pre): min((m for m, r in series[p].items() if r >= level and (not pre or m < START)),
                                         default=None) for p in ids for level in (2300, 2400) for pre in (False, True)}}


def run(c: dict, rnd) -> dict:
    """The replay of every player and list under one reading of the rounding: rnd(x, t) rounds a period's change on
    the list t, for Layer 0 and rung 2 alike."""
    ids, dates, lists, pages, index = c["ids"], c["dates"], c["lists"], c["pages"], c["index"]
    first, pub, birth, reached, key_to_id = c["first"], c["pub"], c["birth"], c["reached"], c["key_to_id"]
    L0 = {p: {first[p]: pub[p][first[p]]} for p in ids if first[p]}
    R2 = {v: {p: {first[p]: pub[p][first[p]]} for p in ids if first[p]} for v in VARIANTS}

    def diff(v: str, p: str, m: str) -> int:
        """A set player's rung-2 rating minus Layer 0's on list m; nil before the replay starts."""
        if m < START or m not in R2[v][p]:
            return 0
        return R2[v][p][m] - L0[p][m]

    def ever(p: str, upto: str, level: int, v: str | None) -> bool:
        """Whether the player's rating had reached `level` on a list up to `upto`: FIDE's published ratings, or, for a
        variant v, the published ratings before the replay and the variant's own from its start (R61)."""
        first_m = reached[(p, level, v is not None)]
        if first_m is not None and first_m <= upto:
            return True
        if v is None:
            return False
        return any(r >= level for m, r in R2[v][p].items() if m <= upto)

    def rating_on(q: str, m: str) -> int | None:
        """A set player's published rating on list m, or Layer 0's where FIDE's file of m lacks the player."""
        return lists[m][q][0] if q in lists[m] else L0[q].get(m)

    val = Counter({k: 0 for k in VAL_KEYS})
    k_printed, by_cause = Counter(), Counter()
    neg_halves: list[tuple[str, str]] = []     # (list, how FIDE rounded a negative half point) in ordinary periods
    periods_by_list: Counter = Counter()       # ordinary periods (a page, no gap in FIDE's files) by list
    cap_evidence: dict[str, Counter] = defaultdict(Counter)       # month of the start -> what FIDE applied
    cap_by_version: dict[str, Counter] = defaultdict(Counter)
    cap_dates = {"last_350": "", "first_beyond_350": "9999"}      # tournament starts
    rounding: dict[str, Counter] = defaultdict(Counter)
    k_departs, colour = Counter(), Counter()
    stats = {p: Counter() for p in ids}
    thin = {p: [] for p in ids}
    checked = []
    anchor = {p: first[p] for p in ids}     # the last list whose file carries the player
    pending = {p: [] for p in ids}          # the periods since, which no file has checked yet

    def replay_page(p: str, t: str, prev: str, page: dict) -> dict:
        """One player's period: Layer 0's change and each variant's rung-2 change, with the validation of its games
        and tournaments."""
        sum0, per_t0 = Decimal(0), []
        sums = {v: Decimal(0) for v in VARIANTS}
        n_games, game_mismatch = 0, False
        f_games = f_tourn = 0.0                   # the same sum in binary floating point, game by game and by tournament
        for tr in page["tournaments"]:
            val["tournaments"] += 1
            k_printed[tr["k"]] += 1
            val["games_not_n"] += tr["n"] != len(tr["games"])
            start = ex.d_of(tr["start"]) if tr["start"] else date.fromisoformat(f"{prev}-01")
            ver = lg.version(start)
            m = list_for_ro(lists, dates, p, tr["ro"], tr["start"], t)
            opp_actual, opp_ids = [], []
            for g in tr["games"]:
                actual, known = g["rating"], not maybe_capped(g, tr["ro"])
                val["cap_marks"] += g["capped"]
                if not known:
                    val["cap_candidates"] += 1
                    r = resolve(g, tr["ro"], index.get(m, {}))
                    if r is None:
                        val["cap_unresolved"] += 1
                    else:
                        val["cap_resolved"] += 1
                        actual, known = r, True
                oid = key_to_id.get(ex.norm(g["name"]))
                if oid is not None and oid != p:
                    val["set_games"] += 1
                    r = rating_on(oid, m)
                    if r is None or not consistent(r, g["rating"], tr["ro"], maybe_capped(g, tr["ro"])):
                        val["set_name_unconfirmed"] += 1
                        oid = None
                else:
                    oid = None
                # which rating-difference rule FIDE applied, where the opponent's rating is known
                gap_shown, gap_actual = abs(tr["ro"] - g["rating"]), abs(tr["ro"] - actual)
                if known and gap_actual > 350:
                    applied = ("350" if gap_shown == 350 < gap_actual else "400" if gap_shown == 400 < gap_actual
                               else "none" if gap_shown == gap_actual else "other")
                    cap_evidence[tr["start"][:7] if tr["start"] else prev][applied] += 1
                    cap_by_version[ver][applied] += 1
                    if applied in ("350", "400"):
                        cap_by_version[ver][f"{applied}, FIDE's mark" if g["capped"] else f"{applied}, no mark"] += 1
                    if tr["start"] and applied == "350":
                        cap_dates["last_350"] = max(cap_dates["last_350"], tr["start"])
                    elif tr["start"] and applied in ("400", "none"):
                        cap_dates["first_beyond_350"] = min(cap_dates["first_beyond_350"], tr["start"])
                opp_actual.append(actual)
                opp_ids.append(oid)
            d0 = lg.deltas(tr["ro"], list(zip(opp_actual, [g["score"] for g in tr["games"]])), start)
            kt = Decimal(tr["k"])
            for g, dl in zip(tr["games"], d0):
                val["games"] += 1
                n_games += 1
                if dl != g["chg"]:
                    game_mismatch = True
                    val["game_delta_differs"] += 1
            tsum = sum(d0, Decimal(0))
            val["tournament_sum_differs"] += tsum != tr["chg"]
            val["tournament_k_chg_differs"] += kt * tsum != tr["k_chg"]
            sum0 += kt * tsum
            per_t0.append(kt * tsum)
            for g in tr["games"]:
                f_games += float(tr["k"]) * float(g["chg"])
            f_tourn += float(tr["k_chg"])
            # K under each system (R61): FIDE's K rules on the system's own rating, where they give FIDE's K
            k_v = {}
            for lst in (prev, m):
                own = rating_on(p, lst) or tr["ro"]
                if k_rule(ver, own, ever(p, lst, 2400, None), ever(p, lst, 2300, None), lst, birth[p]) == tr["k"]:
                    for v in VARIANTS:
                        k_v[v] = k_rule(ver, own + diff(v, p, lst), ever(p, lst, 2400, v), ever(p, lst, 2300, v), lst,
                                        birth[p])
                    break
            else:
                val["k_rule_differs"] += 1
                k_v = {v: tr["k"] for v in VARIANTS}
            for v in VARIANTS:
                k_departs[v] += k_v[v] != tr["k"]
                own2 = tr["ro"] + diff(v, p, m)
                tot = Decimal(0)
                for g, oid, actual in zip(tr["games"], opp_ids, opp_actual):
                    w = 0 if v == "r2nc" else (1 if g["mark"] == "white" else -1)
                    opp2 = actual + (diff(v, oid, m) if oid is not None else SHIFT.get(v, 0))
                    tot += g["score"] - e19.sc_expectation(TABLE, own2, opp2, w)
                sums[v] += Decimal(k_v[v]) * tot
            for g in tr["games"]:
                colour[g["mark"]] += 1
        return {"sum0": sum0, "ch0": rnd(sum0, t), "ch_t": sum(rnd(x, t) for x in per_t0),
                "add": {v: rnd(sums[v], t) for v in VARIANTS}, "games": n_games, "game_mismatch": game_mismatch,
                "total": page["total"], "float_exact": f_games == float(sum0) == f_tourn}

    for t in c["window"]:
        prev = prev_of(dates, t)
        for p in ids:
            if first[p] is None or first[p] > prev:
                continue
            cur, page = lists[t].get(p), pages.get((p, t))
            res = replay_page(p, t, prev, page) if page is not None else None
            val["periods_with_page"] += res is not None
            ch0 = res["ch0"] if res else 0
            if cur is None:                       # FIDE's file of t lacks the player: checked with the next that has
                L0[p][t] = L0[p][prev] + ch0
                for v in VARIANTS:
                    R2[v][p][t] = R2[v][p][prev] + (res["add"][v] if res else 0)
                pending[p].append((t, res))
                continue
            a = anchor[p]
            pc = cur[0] - pub[p][a]               # FIDE's change since the last file that carries the player
            if res is None and not pending[p]:
                if cur[1] or pc:
                    val["no_page"] += 1
                    thin[p].append([t, "no page"])
                L0[p][t] = L0[p][prev] + pc
                for v in VARIANTS:
                    R2[v][p][t] = R2[v][p][prev] + pc
                anchor[p] = t
                continue
            if res is not None and not pending[p]:     # an ordinary period: the readings of the rounding tested
                era = rounding_era(t)
                s0 = res["sum0"]
                rounding[era]["periods"] += 1
                periods_by_list[t] += 1
                rounding[era]["reproduced"] += res["ch0"] == pc
                rounding[era]["reproduced_away_from_zero"] += lg.round_change_away(s0) == pc
                rounding[era]["reproduced_towards_plus_infinity"] += lg.round_change_up(s0) == pc
                rounding[era]["reproduced_once_per_tournament"] += res["ch_t"] == pc
                if abs(s0) % 1 == Decimal("0.5"):
                    sign = "negative" if s0 < 0 else "positive"
                    if s0 < 0:
                        neg_halves.append((t, "towards_plus_infinity" if lg.round_change_up(s0) == pc else
                                           "away_from_zero" if lg.round_change_away(s0) == pc else "neither"))
                    rounding[era][f"half_{sign}"] += 1
                    rounding[era][f"half_{sign}_away_from_zero"] += lg.round_change_away(s0) == pc
                    rounding[era][f"half_{sign}_towards_plus_infinity"] += lg.round_change_up(s0) == pc
                    rounding[era][f"half_{sign}_towards_zero"] += int(s0) == pc
                    if res["float_exact"]:              # a half point exact in floating point, summed either way
                        rounding[era]["half_float_exact"] += 1
                        rounding[era]["half_float_exact_away_from_zero"] += lg.round_change_away(s0) == pc
                        rounding[era]["half_float_exact_towards_zero"] += int(s0) == pc
                    if lg.round_change_up(s0) != pc:      # an exception to 0.5 towards +infinity
                        rounding[era]["half_not_towards_plus_infinity"] += 1
                        rounding[era]["half_not_towards_plus_infinity_float_exact"] += res["float_exact"]
                val["total_shown_differs"] += res["total"] is not None and res["total"] != s0
            stretch = pending[p] + [(t, res)]
            if L0[p][prev] - L0[p][a] + ch0 == pc:
                L0[p][t] = L0[p][prev] + ch0
                for v in VARIANTS:
                    R2[v][p][t] = R2[v][p][prev] + (res["add"][v] if res else 0)
                for _tt, rr in stretch:
                    if rr is not None:
                        stats[p]["periods"] += 1
                        stats[p]["games"] += rr["games"]
                if pending[p]:
                    checked.append([p, " ".join(tt for tt, _r in pending[p]), t, "reproduced"])
            else:
                if pending[p]:
                    cause = "not on FIDE's file, and the stretch to the next file is not reproduced"
                    checked.append([p, " ".join(tt for tt, _r in pending[p]), t, "not reproduced"])
                else:
                    s0 = res["sum0"]
                    half = abs(s0) % 1 == Decimal("0.5")
                    cause = ("a half point, rounded the other way" if half and
                             pc in (lg.round_change_away(s0), lg.round_change_up(s0)) else
                             "a positive half point rounded down" if half and s0 > 0 and pc == int(s0) else
                             "rounded once per tournament" if res["ch_t"] == pc else
                             "a game's change differs" if res["game_mismatch"] else
                             "the list's change is not a rounding of the page's sum" if abs(pc - s0) >= 1 else
                             "unexplained")
                    val["period_change_differs"] += 1
                by_cause[cause] += 1
                for tt, rr in stretch:
                    thin[p].append([tt, cause])
                    stats[p]["games_thin"] += rr["games"] if rr else 0
                for tt, _rr in pending[p]:            # no file and no reproduction: the anchor's values carried
                    L0[p][tt] = L0[p][a]
                    for v in VARIANTS:
                        R2[v][p][tt] = R2[v][p][a]
                L0[p][t] = L0[p][a] + pc
                for v in VARIANTS:
                    R2[v][p][t] = R2[v][p][a] + pc
            anchor[p], pending[p] = t, []
    for p in ids:                                 # periods after the last file that carries the player: carried
        for tt, rr in pending[p]:
            if rr is not None:
                thin[p].append([tt, "after the last file that carries the player"])
                stats[p]["games_thin"] += rr["games"]
            L0[p][tt] = L0[p][anchor[p]]
            for v in VARIANTS:
                R2[v][p][tt] = R2[v][p][anchor[p]]
    return {"L0": L0, "R2": R2, "val": val, "k_printed": k_printed, "by_cause": by_cause, "cap_evidence": cap_evidence,
            "cap_by_version": cap_by_version, "cap_dates": cap_dates, "rounding": rounding, "k_departs": k_departs,
            "colour": colour, "stats": stats, "thin": thin, "checked": checked, "neg_halves": neg_halves,
            "periods_by_list": periods_by_list}


# ------------------------------------------------------------------ the aggregate
def players_of(c: dict, r: dict) -> list[dict]:
    def peak(s: dict) -> dict:
        vals = {m: x for m, x in s.items() if START < m <= LAST}
        top = max(vals.values())
        return {"rating": top, "lists": [m for m, x in sorted(vals.items()) if x == top]}

    out = []
    for p in c["ids"]:
        if c["first"][p] is None:
            continue
        L0, R2, st = r["L0"][p], {v: r["R2"][v][p] for v in VARIANTS}, r["stats"][p]
        last = max(m for m in L0 if m <= LAST)
        on_file = max(m for m in c["window"] if p in c["lists"][m])
        d = {v: R2[v][last] - L0[last] for v in VARIANTS}
        played = [x.split(":")[1] for x in c["plan"] if x.split(":")[0] == p]
        out.append({
            "fide_id": int(p), "name": c["selected"].get(p, ""), "periods_on_index": len(played),
            "last_list_on_fide": on_file,
            "first_period": min(played), "last_period": max(played),
            "periods_replayed": st["periods"], "games_replayed": st["games"],
            "thin_periods": len(r["thin"][p]), "games_in_thin_periods": st["games_thin"], "thin": r["thin"][p],
            "difference": d["r2"], "table_effect": d["r2nc"], "colour_effect": d["r2"] - d["r2nc"],
            "difference_outside_minus10": d["r2_outside-10"], "difference_outside_plus10": d["r2_outside+10"],
            "year_end_difference": {m[:4]: R2["r2"][m] - L0[m] for m in c["window"] if m.endswith("-12") and m in L0},
            "highest_layer0": peak(L0), "highest_rung2": peak(R2["r2"]), "highest_rung2_no_colour": peak(R2["r2nc"])})
    return out


def calibration(c: dict) -> dict:
    """ELO9-STAT-1's check, at FIDE's own ratings: on every replayed game in which the player of the set is the
    favourite by 50 to 399 points (the rating FIDE used, or the opponent's rating on the list in force where FIDE
    printed a capped value), the favourite's residual, score minus expectation, under table 8.1.2 and under the 2025
    table (FIDE's colour mark, as the method applies it), by level band and overall, with 95 % intervals clustered over
    the players of the set; and every game row's level band, overall and per player."""
    res: dict[int, list] = defaultdict(list)
    rows_by_band: Counter = Counter()
    per_player: dict[str, Counter] = defaultdict(Counter)
    for (p, t), page in c["pages"].items():
        for tr in page["tournaments"]:
            m = list_for_ro(c["lists"], c["dates"], p, tr["ro"], tr["start"], t)
            for g in tr["games"]:
                opp = g["rating"]
                if maybe_capped(g, tr["ro"]):
                    r = resolve(g, tr["ro"], c["index"].get(m, {}))
                    opp = r if r is not None else opp
                own = tr["ro"]
                mid = ex.t2.band_mid((own + opp) // 2)
                rows_by_band[mid] += 1
                per_player[p]["rows"] += 1
                per_player[p]["rows_2800"] += mid >= 2850
                if 50 <= own - opp < 400:
                    w = 1 if g["mark"] == "white" else -1
                    e812 = layer0.expected_score(own - opp)
                    e25 = e19.sc_expectation(TABLE, own, opp, w)
                    res[mid].append((p, float(g["score"] - e812), float(g["score"] - e25)))

    def summarise(rows: list) -> dict:
        n = len(rows)
        out = {"games": n, "players": len({p for p, _a, _b in rows})}
        for k, i in (("table_812", 1), ("table_2025", 2)):
            mean = sum(r[i] for r in rows) / n
            by: dict[str, float] = defaultdict(float)
            for r in rows:
                by[r[0]] += r[i] - mean
            g = len(by)
            se = (sum(v * v for v in by.values()) * g / (g - 1)) ** 0.5 / n if g > 1 else 0.0
            out[k] = {"mean": round(mean, 4), "lo": round(mean - 1.96 * se, 4), "hi": round(mean + 1.96 * se, 4)}
        return out

    every = [r for v in res.values() for r in v]
    return {"gaps": [50, 399], "colour": "FIDE's marks", "overall": summarise(every),
            "by_band": {str(mid): summarise(v) for mid, v in sorted(res.items()) if len(v) >= 30},
            "game_rows_by_band": {str(k): n for k, n in sorted(rows_by_band.items())},
            "per_player_rows": {p: [x["rows"], x["rows_2800"]] for p, x in per_player.items()}}


def negative_halves(rows: list[tuple[str, str]], periods_by_list: Counter | None = None,
                    window: list[str] | None = None) -> dict:
    """How FIDE's lists rounded a period's sum ending in a negative half point, by year of the list, and the lists from
    July 2014 on which the direction last went up and first went away from zero, with every list of the window between
    them, its ordinary periods and their negative half points (counts and list dates only)."""
    by_year: dict[str, Counter] = defaultdict(Counter)
    for t, how in rows:
        by_year[t[:4]][how] += 1
    after = [(t, how) for t, how in rows if t >= lg.ROUNDING_2014_LIST]
    early = defaultdict(Counter)
    for t, how in rows:
        if t < lg.ROUNDING_2014_LIST:
            early[t][how] += 1
    last_up = max((t for t, h in after if h == "towards_plus_infinity"), default=None)
    first_away = min((t for t, h in after if h == "away_from_zero"), default=None)
    between = [{"list": t, "periods": (periods_by_list or {}).get(t, 0),
                "negative_half_points": sum(1 for x, _h in rows if x == t)}
               for t in (window or []) if last_up and first_away and last_up < t < first_away]
    return {"by_year": {y: dict(sorted(c.items())) for y, c in sorted(by_year.items())},
            "lists_between_the_last_up_and_the_first_away": between,
            "before_july_2014_lists_with_away_from_zero": {t: dict(sorted(c.items())) for t, c in sorted(early.items())
                                                           if c.get("away_from_zero")},
            "before_july_2014_lists": len(early),
            "from_july_2014": {"last_list_towards_plus_infinity": max((t for t, h in after if h == "towards_plus_infinity"),
                                                                       default=None),
                               "first_list_away_from_zero": min((t for t, h in after if h == "away_from_zero"),
                                                                default=None),
                               "away_from_zero_before_last_up": sum(
                                   1 for t, h in after if h == "away_from_zero" and t < max(
                                       (x for x, y in after if y == "towards_plus_infinity"), default="")),
                               "towards_plus_infinity_after_first_away": sum(
                                   1 for t, h in after if h == "towards_plus_infinity" and t > min(
                                       (x for x, y in after if y == "away_from_zero"), default="9999"))}}


def summary(players: list[dict]) -> dict:
    n = len(players)
    return {"mean_difference": round(sum(r["difference"] for r in players) / n, 2),
            "mean_table_effect": round(sum(r["table_effect"] for r in players) / n, 2),
            "mean_colour_effect": round(sum(r["colour_effect"] for r in players) / n, 2),
            "min_difference": min(r["difference"] for r in players),
            "max_difference": max(r["difference"] for r in players),
            "higher": sum(1 for r in players if r["difference"] > 0),
            "lower": sum(1 for r in players if r["difference"] < 0),
            "equal": sum(1 for r in players if r["difference"] == 0),
            "thin_periods": sum(r["thin_periods"] for r in players),
            "periods_replayed": sum(r["periods_replayed"] for r in players),
            "games_replayed": sum(r["games_replayed"] for r in players)}


def main() -> int:
    c = prepare()
    r = run(c, READINGS["R80"])
    d17 = run(c, READINGS["D-0017"])
    alt = run(c, READINGS["rules record"])
    up = run(c, READINGS["towards +infinity throughout"])
    players, players_d17 = players_of(c, r), players_of(c, d17)
    players_alt, players_up = players_of(c, alt), players_of(c, up)
    evidence = {k: dict(x) for k, x in sorted(r["cap_evidence"].items())}
    cal = calibration(c)
    for pl in players:
        pl["game_rows"], pl["game_rows_at_2800_or_more"] = cal["per_player_rows"].get(str(pl["fide_id"]), [0, 0])
    del cal["per_player_rows"]
    out = {
        "spec": "docs/specs/SPEC-GREATS_v1_0.md", "rules": "docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md",
        "calibration": cal,
        "window": {"start_list": START, "first": c["window"][0], "last": LAST, "lists": len(c["window"])},
        "table": {"year": 2025, "form": TABLE["form"], "label": "applied backwards, not fitted on that era"},
        "pages": {"planned": len(c["plan"]), "read": len(c["pages"]), "missing": c["missing"],
                  "periods_not_list_dates": sorted({x.split(":")[1] for x in c["plan"]} - set(c["dates"]))},
        "players_replayed": len(players),
        # R79: the reproduction runs locally from the cache; only its counts are committed
        "validation": dict(sorted(r["val"].items())), "k_printed": dict(sorted(r["k_printed"].items())),
        "thin_by_cause": dict(sorted(r["by_cause"].items())), "checked_with_next_file": r["checked"],
        "rule_difference": {"by_version": {k: dict(x) for k, x in sorted(r["cap_by_version"].items())},
                            "by_start_month": evidence,
                            "last_start_with_350": r["cap_dates"]["last_350"] or None,
                            "first_start_beyond_350": None if r["cap_dates"]["first_beyond_350"] == "9999" else
                            r["cap_dates"]["first_beyond_350"]},
        "rounding": {k: dict(sorted(x.items())) for k, x in sorted(r["rounding"].items())},
        "negative_half_points": negative_halves(r["neg_halves"], r["periods_by_list"], c["window"]),
        "readings": {  # R80 adopted, D-0017's beside it (R80), the rules record's first (R74), and one for information
            "R80": {"rule": "0.5 towards +infinity on every list to October 2018, away from zero from November 2018",
                    **summary(players), "thin_by_cause": dict(sorted(r["by_cause"].items()))},
            "D-0017": {"rule": "0.5 towards +infinity on the lists before July 2014, away from zero from July 2014",
                       **summary(players_d17), "thin_by_cause": dict(sorted(d17["by_cause"].items()))},
            "rules record": {"rule": "0.5 away from zero on every list", **summary(players_alt),
                             "thin_by_cause": dict(sorted(alt["by_cause"].items()))},
            "towards +infinity throughout": {  # for information only (D-0017 reading 2): the 2014 and 2017 words literally
                "rule": "0.5 towards +infinity on every list of the window, to December 2019", **summary(players_up),
                "thin_by_cause": dict(sorted(up["by_cause"].items()))}},
        "k_departs_from_fide": dict(r["k_departs"]),
        "colour_marks": dict(r["colour"]),
        "players": players,
        "summary": summary(players)}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
