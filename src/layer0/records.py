"""Records of the Layer-0 engine (SPEC-L0 §2, §4): inputs, state and results, all immutable."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TimeControl:
    """A player's time control: base minutes, increment in seconds, moves in the first control if any (R-01 to R-03)."""
    base_minutes: Decimal | int
    increment_seconds: Decimal | int = 0
    moves_first_control: int | None = None


@dataclass(frozen=True)
class Tournament:
    """A FIDE-rated tournament (SPEC-L0 §2.1); `rating_period` is the list, YYYY-MM, on which FIDE rates it."""
    tournament_id: str
    start: date
    end: date
    rating_period: str
    chapter: str = "standard"
    official_fide_event: bool = False


@dataclass(frozen=True)
class Game:
    """One game; `result` is "1-0", "1/2-1/2" or "0-1"; `played` and `excluded` implement R-05."""
    tournament_id: str
    round: int
    white: int
    black: int
    result: str
    played: bool = True
    excluded: bool = False


@dataclass(frozen=True)
class ListEntry:
    """A player's entry on a monthly list (R-34): the fields the rules use."""
    rating: int
    k: int
    games: int = 0
    birth_year: int | None = None
    inactive: bool = False


@dataclass(frozen=True)
class PoolEvent:
    """An unrated player's results against rated opponents in one event (R-27, R-28): (opponent rating, score)."""
    period: str
    results: tuple[tuple[int, Decimal], ...]
    first_event: bool = False


@dataclass(frozen=True)
class PlayerState:
    """What the engine carries from list to list that the list does not show (SPEC-L0 §2.3, §4.3)."""
    games_count: int = 0
    ever_2400: bool = False
    ever_2300: bool = False
    pool: tuple[PoolEvent, ...] = ()
    first_event_seen: bool = False
    last_game_period: str | None = None


@dataclass(frozen=True)
class GameRow:
    """One rated game of one player, with every intermediate value (SPEC-L0 §4)."""
    tournament_id: str
    round: int
    opponent: int
    colour: str
    own_rating: int
    opponent_rating: int
    d: int
    d_used: int
    pd: Decimal
    score: Decimal
    delta: Decimal


@dataclass(frozen=True)
class TournamentChange:
    """One player's change in one tournament: K x the sum of Delta R (R-11, R-24)."""
    tournament_id: str
    n: int
    sum_delta: Decimal
    change: Decimal
    own_rating: int | None = None
    list_used: str | None = None


@dataclass(frozen=True)
class PeriodChange:
    """A player's change for a rating period: once rounded (R-25) and, for comparison, rounded per tournament."""
    k: int
    n: int
    tournaments: tuple[TournamentChange, ...]
    change: Decimal
    rounded: int
    rounded_per_tournament: int


@dataclass(frozen=True)
class PlayerPeriod:
    """The breakdown of one player's period: base, K, games, changes and the new rating before the floor."""
    player: int
    base: int | None
    k: int | None
    n: int
    tournaments: tuple[TournamentChange, ...]
    change: Decimal
    rounded: int
    rounded_per_tournament: int
    new_rating: int | None
    games: tuple[GameRow, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class NextList:
    """The result of next_list: the new list, the new state and the breakdown of every player who played."""
    period: str
    entries: dict[int, ListEntry] = field(default_factory=dict)
    state: dict[int, PlayerState] = field(default_factory=dict)
    players: dict[int, PlayerPeriod] = field(default_factory=dict)
