"""A-7: games that count and their chapter (SPEC-L0 R-01 to R-07)."""
from datetime import date

import pytest

from l0_helpers import require_layer0

layer0 = require_layer0()
TC = layer0.TimeControl


@pytest.mark.parametrize("base,inc,moves,rw,rb,expected", [
    (120, 0, None, 2400, 2000, "standard"),        # R-01: 120 minutes when a player is rated 2400 or more
    (119, 0, None, 2400, 2000, None),              # neither standard nor rapid (rapid is less than 60)
    (90, 30, None, 2400, 2000, "standard"),        # R-01 reading: 90 + 60 x 30 s = 120 minutes for 60 moves
    (90, 0, None, 1800, 1500, "standard"),         # 90 minutes when a player is rated 1800 or more
    (89, 0, None, 1800, 1500, None),
    (60, 0, None, 1799, 1500, "standard"),         # 60 minutes when both are below 1800
    (60, 0, None, 1799, None, "standard"),         # an unrated player counts as below 1800
    (120, 0, 29, 2000, 2000, None),                # R-01: a first control must have at least 30 moves
    (120, 0, 30, 2000, 2000, "standard"),
    (59, 0, None, 1799, 1500, "rapid"),            # R-02: more than 10 and less than 60 minutes
    (15, 10, None, 2000, 2000, "rapid"),           # 15 + 60 x 10 s = 25 minutes
    (10, 1, None, 2000, 2000, "rapid"),            # 11 minutes
    (10, 0, None, 2000, 2000, "blitz"),            # R-03: more than 3 and not more than 10 minutes
    (3, 2, None, 2000, 2000, "blitz"),             # 5 minutes
    (3, 0, None, 2000, 2000, None),                # not more than 3
    (1, 2, None, 2000, 2000, None),                # 3 minutes
])
def test_classify(base, inc, moves, rw, rb, expected):
    tc = TC(base_minutes=base, increment_seconds=inc, moves_first_control=moves)
    assert layer0.classify(tc, tc, rw, rb) == expected


def test_r04_unequal_times_are_not_rated_in_rapid_and_blitz():
    assert layer0.classify(TC(15, 10), TC(10, 10), 2000, 2000) is None
    assert layer0.classify(TC(5, 0), TC(4, 0), 2000, 2000) is None


def tournament(chapter: str, start: date) -> "layer0.Tournament":
    return layer0.Tournament("t", start, start, f"{start.year + (start.month == 12):04d}-{start.month % 12 + 1:02d}",
                             chapter)


def test_r05_unplayed_and_excluded_games():
    t = tournament("standard", date(2025, 11, 5))
    assert layer0.rateable(layer0.Game("t", 1, 1, 2, "1-0"), t, 2000, 2000)
    assert not layer0.rateable(layer0.Game("t", 1, 1, 2, "1-0", played=False), t, 2000, 2000)
    assert not layer0.rateable(layer0.Game("t", 1, 1, 2, "1-0", excluded=True), t, 2000, 2000)


@pytest.mark.parametrize("chapter,start,rw,rb,expected", [
    ("rapid", date(2024, 12, 1), 2601, 2001, False),    # 600 points, one player above 2600
    ("blitz", date(2024, 12, 1), 2001, 2601, False),
    ("rapid", date(2024, 12, 1), 2600, 2000, True),     # nobody above 2600
    ("rapid", date(2024, 12, 1), 2601, 2002, True),     # 599 points
    ("rapid", date(2024, 11, 30), 2601, 2001, True),    # before 1 December 2024
    ("standard", date(2025, 11, 5), 2601, 2001, True),  # no such rule in standard
])
def test_r07_600_points(chapter, start, rw, rb, expected):
    assert layer0.rateable(layer0.Game("t", 1, 1, 2, "1-0"), tournament(chapter, start), rw, rb) is expected


def test_rateable_checks_the_chapter_when_time_controls_are_given():
    t = tournament("standard", date(2025, 11, 5))
    g = layer0.Game("t", 1, 1, 2, "1-0")
    assert layer0.rateable(g, t, 2000, 2000, TC(90, 30), TC(90, 30))
    assert not layer0.rateable(g, t, 2000, 2000, TC(15, 10), TC(15, 10))


@pytest.mark.parametrize("scores,scheduled,both_rated,waived,expected", [
    ([1, 1, 1, 0], 4, True, False, (True, True, True, False)),      # R-06: decided after three games
    ([1, 0.5, 1, 0], 4, True, False, (True, True, True, False)),    # 2.5 of 4 decides it
    ([1, 0.5, 0.5, 0], 4, True, False, (True, True, True, True)),   # 2 of 4 does not
    ([1, 1, 1, 0], 4, True, True, (True, True, True, True)),        # waived by prior request
    ([1, 0, 1, 0], 4, False, False, (False, False, False, False)),  # a match with an unrated player
])
def test_r06_matches(scores, scheduled, both_rated, waived, expected):
    assert layer0.rated_match_games(scores, scheduled, both_rated=both_rated, waived=waived) == expected
