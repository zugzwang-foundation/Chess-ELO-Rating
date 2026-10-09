"""Layer 0: an exact, deterministic implementation of the FIDE Rating Regulations (SPEC-L0 v1.0, ratified in D-0006).

Standard, rapid and blitz; exact decimal arithmetic; pure functions only. The interfaces are those of
docs/specs/SPEC-L0_fide-reference-engine_v1_0.md §4; each function names the rules it implements.
"""
from .lists import next_list, state_from_entry
from .records import (Game, GameRow, ListEntry, NextList, PeriodChange, PlayerPeriod, PlayerState, PoolEvent,
                      TimeControl, Tournament, TournamentChange)
from .rules import (classify, earliest_rating_period, effective_difference, game_delta, initial_rating, k_for_period,
                    latest_rating_period, list_in_force, month_add, months_between, period_change, published_k,
                    rateable, rated_match_games, round_change, round_initial)
from .tables import TABLE_811, TABLE_812, dp_from_p, expected_score

__all__ = [
    "TABLE_811", "TABLE_812", "Game", "GameRow", "ListEntry", "NextList", "PeriodChange", "PlayerPeriod", "PlayerState",
    "PoolEvent", "TimeControl", "Tournament", "TournamentChange", "classify", "dp_from_p", "earliest_rating_period",
    "effective_difference", "expected_score", "game_delta", "initial_rating", "k_for_period", "latest_rating_period",
    "list_in_force", "month_add", "months_between", "next_list", "period_change", "published_k", "rateable",
    "rated_match_games", "round_change", "round_initial", "state_from_entry",
]
__version__ = "1.0.0"
