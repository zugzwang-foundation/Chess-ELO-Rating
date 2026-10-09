"""The rules of SPEC-L0 §3 as pure functions: chapters, periods, expected score, K, rounding, initial ratings."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .records import Game, PeriodChange, PoolEvent, TimeControl, Tournament, TournamentChange
from .tables import dp_from_p, expected_score

ONE = Decimal(1)
AMENDMENT_2650 = date(2025, 10, 1)      # R-14: "Effective from 1 October 2025"
EXCLUSION_600 = date(2024, 12, 1)       # R-07: "Effective from 1 December 2024"
SCORES = {"1-0": (Decimal(1), Decimal(0)), "1/2-1/2": (Decimal("0.5"), Decimal("0.5")), "0-1": (Decimal(0), Decimal(1))}


# --- months -----------------------------------------------------------------

def month_add(month: str, k: int) -> str:
    y, m = int(month[:4]), int(month[5:7]) - 1 + k
    return f"{y + m // 12:04d}-{m % 12 + 1:02d}"


def months_between(a: str, b: str) -> int:
    """Number of months from a to b (b - a)."""
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])


def list_in_force(d: date) -> str:
    """R-11a: the list dated the first day of the month of d."""
    return f"{d.year:04d}-{d.month:02d}"


def earliest_rating_period(end: date, official_fide_event: bool = False) -> str:
    """R-09: the first list whose closing date (3 days before it; 1 day for official FIDE events) is on or after end."""
    margin = timedelta(days=1 if official_fide_event else 3)
    month = month_add(list_in_force(end), 1)
    while date(int(month[:4]), int(month[5:7]), 1) - margin < end:
        month = month_add(month, 1)
    return month


def latest_rating_period(end: date) -> str:
    """R-10 reading: the third list dated after end."""
    return month_add(list_in_force(end), 3)


# --- games that count -------------------------------------------------------

def _minutes_for_60_moves(tc: TimeControl) -> Decimal:
    """Base time plus 60 times the increment, in minutes (R-02, R-03; R-01 reading)."""
    return Decimal(tc.base_minutes) + Decimal(tc.increment_seconds)


def classify(white_tc: TimeControl, black_tc: TimeControl, rating_white: int | None, rating_black: int | None) -> str | None:
    """R-01 to R-04: the chapter a game's time controls qualify for, or None."""
    rated = [r for r in (rating_white, rating_black) if r is not None]
    top = max(rated) if rated else 0
    need = 120 if top >= 2400 else 90 if top >= 1800 else 60
    first_controls = all(tc.moves_first_control is None or tc.moves_first_control >= 30 for tc in (white_tc, black_tc))
    if first_controls and min(_minutes_for_60_moves(white_tc), _minutes_for_60_moves(black_tc)) >= need:
        return "standard"
    if white_tc != black_tc:                                   # R-04
        return None
    minutes = _minutes_for_60_moves(white_tc)
    if 10 < minutes < 60:
        return "rapid"
    if 3 < minutes <= 10:
        return "blitz"
    return None


def rateable(game: Game, tournament: Tournament, rating_white: int | None, rating_black: int | None,
             white_tc: TimeControl | None = None, black_tc: TimeControl | None = None) -> bool:
    """R-05 (unplayed or excluded), R-07 (600 points in rapid and blitz) and, given time controls, R-01 to R-04."""
    if not game.played or game.excluded:
        return False
    if white_tc is not None and black_tc is not None:
        if classify(white_tc, black_tc, rating_white, rating_black) != tournament.chapter:
            return False
    if tournament.chapter in ("rapid", "blitz") and tournament.start >= EXCLUSION_600 \
            and rating_white is not None and rating_black is not None:
        if abs(rating_white - rating_black) >= 600 and max(rating_white, rating_black) > 2600:
            return False
    return True


def rated_match_games(scores: Iterable, scheduled: int, both_rated: bool = True, waived: bool = False) -> tuple[bool, ...]:
    """R-06: which games of a match are rated, given one player's score in each game."""
    scores = [Decimal(str(s)) for s in scores]
    if not both_rated:
        return tuple(False for _ in scores)
    half = Decimal(scheduled) / 2
    a = b = Decimal(0)
    out = []
    for s in scores:
        out.append(waived or (a <= half and b <= half))
        a += s
        b += ONE - s
    return tuple(out)


# --- expected score and change ----------------------------------------------

def effective_difference(own: int, opponent: int, chapter: str, start: date) -> int:
    """R-13 to R-15, R-14a: D, capped at 400 unless the player is exempt (standard, from 1 October 2025, own >= 2650)."""
    d = own - opponent
    if abs(d) <= 400:
        return d
    if chapter == "standard" and start >= AMENDMENT_2650 and own >= 2650:
        return d
    return 400 if d > 0 else -400


def game_delta(own: int, opponent: int, score: Decimal, chapter: str, start: date) -> Decimal:
    """R-16, R-17: Delta R = score - PD."""
    return Decimal(score) - expected_score(effective_difference(own, opponent, chapter, start))


def published_k(rating: int, games_count: int, ever_2400: bool, ever_2300: bool, list_month: str,
                birth_year: int | None) -> int:
    """R-18 to R-22: the K published with a rating, in the order settled on FIDE's published K."""
    if ever_2400 or rating >= 2400:
        return 10
    junior = birth_year is not None and int(list_month[:4]) - birth_year <= 18
    if junior and not ever_2300 and rating < 2300:
        return 40
    if games_count < 30:
        return 40
    return 20


def k_for_period(previous_list_k: int, n: int) -> int:
    """R-22b, R-23: the previous list's K, reduced to the largest whole number with K x n <= 700."""
    if n > 0 and previous_list_k * n > 700:
        return 700 // n
    return previous_list_k


def round_change(x: Decimal) -> int:
    """R-25: to the nearest whole number, 0.5 away from zero."""
    return int(Decimal(x).quantize(ONE, rounding=ROUND_HALF_UP))


def round_initial(x: Decimal) -> int:
    """R-26 reading (NOT VERIFIED): to the nearest whole number, 0.5 up (initial ratings are positive)."""
    return int(Decimal(x).quantize(ONE, rounding=ROUND_HALF_UP))


def period_change(tournament_deltas: Iterable[tuple[str, Sequence[Decimal]]], k: int) -> PeriodChange:
    """R-11, R-24, R-25: per tournament K x sum of Delta R; the period's change rounded once, and per tournament."""
    changes = []
    for tid, deltas in tournament_deltas:
        ds = [Decimal(x) for x in deltas]
        s = sum(ds, Decimal(0))
        changes.append(TournamentChange(tid, len(ds), s, k * s))
    total = sum((t.change for t in changes), Decimal(0))
    return PeriodChange(k, sum(t.n for t in changes), tuple(changes), total, round_change(total),
                        sum(round_change(t.change) for t in changes))


# --- initial rating ---------------------------------------------------------

def initial_rating(pool: Sequence[PoolEvent]) -> int | None:
    """R-26 to R-30: the initial rating from the pooled results, or None if it is not published."""
    results: list[tuple[int, Decimal]] = []
    for event in pool:
        if event.first_event and sum((s for _, s in event.results), Decimal(0)) == 0:
            continue                                               # R-28
        results.extend(event.results)
    n = len(results)
    if n < 5:                                                      # R-27
        return None
    ra = (Decimal(sum(r for r, _ in results)) + 3600) / (n + 2)    # R-29
    p = (sum((s for _, s in results), Decimal(0)) + 1) / (n + 2)
    ru = min(round_initial(ra + dp_from_p(p)), 2200)               # R-30, R-26
    return ru if ru >= 1400 else None
