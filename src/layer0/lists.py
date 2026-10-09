"""next_list: one rating period, from the previous list and the period's tournaments to the new list (SPEC-L0 §4).

Implements R-08 to R-12 and R-27 to R-34 on top of the rules in rules.py. Pure: no I/O, no
clock; every mapping it returns is built in sorted order, and the input order of records
does not change the result (SPEC-L0 §5).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal

from .records import Game, GameRow, ListEntry, NextList, PlayerPeriod, PlayerState, PoolEvent, Tournament, TournamentChange
from .rules import (SCORES, earliest_rating_period, effective_difference, expected_score, initial_rating, k_for_period,
                    latest_rating_period, list_in_force, month_add, months_between, published_k, rateable, round_change)

POOL_PERIODS = 26        # R-27: "consecutive rating periods of not more than 26 months"
INACTIVE_AFTER = 12      # R-33: "no rated games in a one-year period"
FLOOR = 1400             # R-27, R-32


@dataclass(frozen=True)
class _Status:
    """How one player stands in one tournament."""
    kind: str                      # "listed", "r12" (§8.2.4), "r31" (standard seed), "unrated"
    own: int | None                # the rating used for the player's own change
    visible: int | None            # the rating the opponents use; None counts as unrated


def state_from_entry(entry: ListEntry, month: str) -> PlayerState:
    """Bootstrap (SPEC-L0 §4.3) when no history is given: what one list entry implies.
    K 40 is read as fewer than 30 games, any other K as 30 or more; K 10 as a published 2400."""
    junior = entry.birth_year is not None and int(month[:4]) - entry.birth_year <= 18
    ever_2400 = entry.k == 10 or entry.rating >= 2400
    return PlayerState(games_count=0 if entry.k == 40 else 30, ever_2400=ever_2400,
                       ever_2300=ever_2400 or entry.rating >= 2300 or (junior and entry.k == 20),
                       first_event_seen=True, last_game_period=month if entry.games > 0 else None)


def _corrected(lists: Mapping[str, Mapping[int, ListEntry]],
               corrections: Mapping[tuple[str, int], int]) -> dict[str, dict[int, ListEntry]]:
    out = {m: dict(entries) for m, entries in lists.items()}
    for (month, pid), rating in sorted(corrections.items()):
        if month not in out or pid not in out[month]:
            raise ValueError(f"correction for a player not on the {month} list: {pid}")
        out[month][pid] = replace(out[month][pid], rating=rating)
    return out


def _status(pid: int, t: Tournament, in_force: Mapping[int, ListEntry], previous: Mapping[int, ListEntry],
            standard: Mapping[int, ListEntry]) -> _Status:
    if pid in in_force:
        return _Status("listed", in_force[pid].rating, in_force[pid].rating)
    if pid in previous:                                          # R-12: rated since the tournament started
        return _Status("r12", previous[pid].rating, None)
    if t.chapter in ("rapid", "blitz") and pid in standard:     # R-31
        return _Status("r31", standard[pid].rating, standard[pid].rating)
    return _Status("unrated", None, None)


def next_list(period: str, lists: Mapping[str, Mapping[int, ListEntry]], tournaments: Sequence[Tournament],
              games: Sequence[Game], state: Mapping[int, PlayerState] | None = None,
              corrections: Mapping[tuple[str, int], int] | None = None,
              birth_years: Mapping[int, int] | None = None,
              standard_lists: Mapping[str, Mapping[int, ListEntry]] | None = None) -> NextList:
    """Rate one period: the list of `period` from the previous list, the lists in force and the period's games.

    `lists` maps months to lists of this chapter and must hold the previous list and the list in force at the
    start of every tournament; `corrections` maps (month, player) to a corrected rating (R-11b); `state` carries
    what the lists do not show (bootstrapped from the previous list where missing); `birth_years` gives newcomers'
    years of birth; `standard_lists` supplies R-31 for rapid and blitz. Matches (R-06) are filtered by the
    caller with rated_match_games.
    """
    prev_month = month_add(period, -1)
    all_lists = _corrected(lists, corrections or {})
    previous = all_lists.get(prev_month, {})
    standard_all = standard_lists or {}
    birth_years = birth_years or {}
    tours = {t.tournament_id: t for t in tournaments}
    for t in sorted(tours.values(), key=lambda t: t.tournament_id):
        if t.rating_period != period:
            raise ValueError(f"{t.tournament_id} is rated on {t.rating_period}, not {period}")
        if not earliest_rating_period(t.end, t.official_fide_event) <= period <= latest_rating_period(t.end):
            raise ValueError(f"{t.tournament_id} ends {t.end} and cannot be rated on the {period} list (R-09, R-10)")

    states: dict[int, PlayerState] = {}
    for pid in sorted(set(previous) | set(state or {})):
        states[pid] = (state or {}).get(pid) or state_from_entry(previous[pid], prev_month)

    rows: dict[int, list[tuple[Tournament, GameRow]]] = {}
    pools: dict[int, dict[str, list[tuple[int, Decimal]]]] = {}
    kinds: dict[int, _Status] = {}
    ordered = sorted(games, key=lambda g: (tours[g.tournament_id].start, g.tournament_id, g.round, g.white, g.black,
                                           g.result, g.played, g.excluded))
    for g in ordered:
        t = tours[g.tournament_id]
        month = list_in_force(t.start)
        in_force = all_lists.get(month, {})
        standard = standard_all.get(month, {})
        sides = {g.white: _status(g.white, t, in_force, previous, standard),
                 g.black: _status(g.black, t, in_force, previous, standard)}
        if not rateable(g, t, sides[g.white].visible, sides[g.black].visible):
            continue
        score = dict(zip((g.white, g.black), SCORES[g.result]))
        for me, opp, colour in ((g.white, g.black, "white"), (g.black, g.white, "black")):
            s, o = sides[me], sides[opp]
            if o.visible is None:
                continue                                         # a game against an unrated player
            if s.kind == "unrated":
                pools.setdefault(me, {}).setdefault(t.tournament_id, []).append((o.visible, score[me]))
                continue
            d_used = effective_difference(s.own, o.visible, t.chapter, t.start)
            pd = expected_score(d_used)
            rows.setdefault(me, []).append((t, GameRow(t.tournament_id, g.round, opp, colour, s.own, o.visible,
                                                       s.own - o.visible, d_used, pd, score[me], score[me] - pd)))
            if s.kind != "listed" and me not in kinds:
                kinds[me] = s

    entries: dict[int, ListEntry] = {}
    players: dict[int, PlayerPeriod] = {}
    rated_now = sorted(set(previous) | {p for p, s in kinds.items() if s.kind == "r31"})
    for pid in sorted(set(rated_now) | set(rows)):
        st = states.get(pid, PlayerState(first_event_seen=True))
        my_rows = rows.get(pid, [])
        n = len(my_rows)
        notes = []
        if pid in previous:
            base, prev_k, birth_year = previous[pid].rating, previous[pid].k, previous[pid].birth_year
            if (prev_month, pid) in (corrections or {}):
                notes.append(f"base corrected on the {prev_month} list (R-11b)")
            if pid in kinds:
                notes.append("rated before this tournament was rated (R-12)")
        elif pid in kinds:                                       # R-31: seeded from the standard list
            base, birth_year = kinds[pid].own, birth_years.get(pid)
            prev_k = published_k(base, st.games_count, st.ever_2400, st.ever_2300, prev_month, birth_year)
            notes.append("standard rating used (R-31)")
        else:                                                    # rated on an older list, unrated now: no base
            players[pid] = PlayerPeriod(pid, None, None, n, (), Decimal(0), 0, 0, None, tuple(r for _, r in my_rows),
                                        ("rated on the list in force, unrated on the previous list: no base",))
            continue
        k = k_for_period(prev_k, n)
        by_tournament: dict[str, list[GameRow]] = {}
        lists_used: dict[str, str] = {}
        for t, r in my_rows:
            by_tournament.setdefault(t.tournament_id, []).append(r)
            lists_used[t.tournament_id] = list_in_force(t.start)
        changes = tuple(TournamentChange(tid, len(rs), sum((r.delta for r in rs), Decimal(0)),
                                         k * sum((r.delta for r in rs), Decimal(0)), rs[0].own_rating, lists_used[tid])
                        for tid, rs in by_tournament.items())
        total = sum((c.change for c in changes), Decimal(0))
        new = base + round_change(total)
        if n:
            players[pid] = PlayerPeriod(pid, base, k, n, changes, total, round_change(total),
                                        sum(round_change(c.change) for c in changes), new, tuple(r for _, r in my_rows),
                                        tuple(notes))
        st = replace(st, games_count=st.games_count + n, last_game_period=period if n else st.last_game_period)
        if new < FLOOR:                                          # R-32
            states[pid] = replace(st, pool=())
            if n:
                players[pid] = replace(players[pid], notes=players[pid].notes + ("below 1400: shown as unrated (R-32)",))
            continue
        st = replace(st, ever_2400=st.ever_2400 or new >= 2400, ever_2300=st.ever_2300 or new >= 2300)
        states[pid] = st
        if st.last_game_period is None:                          # no history: keep the previous flag (R-33)
            inactive = previous[pid].inactive if pid in previous else False
        else:
            inactive = months_between(st.last_game_period, period) >= INACTIVE_AFTER
        entries[pid] = ListEntry(new, published_k(new, st.games_count, st.ever_2400, st.ever_2300, period, birth_year),
                                 n, birth_year, inactive)

    for pid in sorted(set(pools) | {p for p, s in states.items() if s.pool and p not in entries}):
        if pid in entries:
            continue
        st = states.get(pid, PlayerState())
        pool = [ev for ev in st.pool if months_between(ev.period, period) < POOL_PERIODS]
        n = 0
        for tid, results in sorted(pools.get(pid, {}).items(), key=lambda kv: (tours[kv[0]].start, kv[0])):
            pool.append(PoolEvent(period, tuple(results), first_event=not st.first_event_seen))
            st = replace(st, first_event_seen=True)
            n += len(results)
        ru = initial_rating(pool)
        st = replace(st, games_count=st.games_count + n, last_game_period=period if n else st.last_game_period)
        if n:
            players[pid] = PlayerPeriod(pid, None, None, n, (), Decimal(0), 0, 0, ru, (),
                                        (f"newcomer: {sum(len(ev.results) for ev in pool)} games in the pool",
                                         "published" if ru is not None else "not published"))
        if ru is None:                                           # R-27: not yet, or below 1400
            states[pid] = replace(st, pool=tuple(pool))
            continue
        st = replace(st, pool=(), ever_2400=ru >= 2400, ever_2300=ru >= 2300)
        states[pid] = st
        birth_year = birth_years.get(pid)
        entries[pid] = ListEntry(ru, published_k(ru, st.games_count, st.ever_2400, st.ever_2300, period, birth_year),
                                 n, birth_year, False)

    return NextList(period, dict(sorted(entries.items())), dict(sorted(states.items())), dict(sorted(players.items())))
