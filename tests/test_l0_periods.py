"""A-8: periods, the ratings used and list status (SPEC-L0 R-08 to R-14a, R-22b, R-27, R-31 to R-34)."""
from datetime import date
from decimal import Decimal

import pytest

from l0_helpers import require_layer0

layer0 = require_layer0()


def entry(rating, k=20, birth_year=1990, games=0, inactive=False):
    return layer0.ListEntry(rating=rating, k=k, games=games, birth_year=birth_year, inactive=inactive)


def tournament(tid, start, end, period, chapter="standard", official=False):
    return layer0.Tournament(tid, start, end, period, chapter, official_fide_event=official)


def test_r11a_list_in_force():
    assert layer0.list_in_force(date(2025, 10, 31)) == "2025-10"
    assert layer0.list_in_force(date(2025, 11, 1)) == "2025-11"


@pytest.mark.parametrize("end,official,expected", [
    (date(2025, 10, 29), False, "2025-11"),     # R-09: the closing date is 3 days before the list
    (date(2025, 10, 30), False, "2025-12"),
    (date(2025, 10, 31), True, "2025-11"),      # official FIDE events: up to the last day before the list
    (date(2025, 11, 1), True, "2025-12"),
])
def test_r09_earliest_list(end, official, expected):
    assert layer0.earliest_rating_period(end, official) == expected


@pytest.mark.parametrize("end,expected", [
    (date(2025, 10, 24), "2026-01"), (date(2025, 10, 31), "2026-01"), (date(2025, 11, 1), "2026-02"),
])
def test_r10_third_list_after_the_end(end, expected):
    assert layer0.latest_rating_period(end) == expected


def test_r09_r10_records_outside_the_limits_are_rejected():
    lists = {"2025-10": {1: entry(2000), 2: entry(2000)}}
    g = layer0.Game("x", 1, 1, 2, "1-0")
    with pytest.raises(ValueError):
        layer0.next_list("2025-11", lists, [tournament("x", date(2025, 10, 27), date(2025, 10, 30), "2025-11")], [g])
    lists["2026-01"] = lists["2025-10"]
    with pytest.raises(ValueError):
        layer0.next_list("2026-02", lists, [tournament("x", date(2025, 10, 20), date(2025, 10, 24), "2026-02")], [g])


TWO_LISTS = {"2025-10": {1: entry(2000), 2: entry(2000)}, "2025-11": {1: entry(2100), 2: entry(1900)}}
LATE = tournament("t1", date(2025, 10, 31), date(2025, 11, 2), "2025-12")


def test_r11a_a_tournament_uses_the_list_in_force_at_its_start():
    res = layer0.next_list("2025-12", TWO_LISTS, [LATE], [layer0.Game("t1", 1, 1, 2, "1-0")])
    row = res.players[1].games[0]
    assert (row.own_rating, row.opponent_rating, row.delta) == (2000, 2000, Decimal("0.50"))
    assert res.players[1].k == 20                                   # R-22b: K from the previous list
    assert res.players[1].change == Decimal("10.00")
    assert res.entries[1] == entry(2110, games=1)                    # R-11, R-34: the previous list plus the change
    assert res.entries[2] == entry(1890, games=1)


def test_r11b_corrections_replace_the_list_value():
    res = layer0.next_list("2025-12", TWO_LISTS, [LATE], [layer0.Game("t1", 1, 1, 2, "1-0")],
                           corrections={("2025-10", 1): 2010, ("2025-11", 1): 2101})
    assert res.players[1].games[0].own_rating == 2010
    assert res.players[1].base == 2101
    assert res.entries[1].rating == 2101 + 10                        # 20 x (1 - .51) = 9.8 -> 10
    assert res.entries[2].rating == 1900 - 10


def test_r12_rated_before_an_earlier_event_is_rated():
    lists = {"2025-10": {1: entry(2000)}, "2025-11": {1: entry(2000), 3: entry(1800, k=40)}}
    res = layer0.next_list("2025-12", lists, [LATE], [layer0.Game("t1", 1, 3, 1, "1-0")])
    row = res.players[3].games[0]
    assert (row.own_rating, row.opponent_rating, row.delta) == (1800, 2000, Decimal("0.76"))
    assert res.entries[3].rating == 1830                             # 40 x .76 = 30.4 -> 30
    assert res.entries[1] == entry(2000)                             # counted as unrated for the opponent


def test_r13_r14a_difference_and_the_amendment_boundary():
    assert layer0.effective_difference(1500, 2000, "standard", date(2025, 10, 1)) == -400
    assert layer0.effective_difference(2000, 2000, "standard", date(2025, 10, 1)) == 0
    assert layer0.effective_difference(2700, 2200, "standard", date(2025, 9, 30)) == 400
    assert layer0.effective_difference(2700, 2200, "standard", date(2025, 10, 1)) == 500
    assert layer0.effective_difference(2700, 2200, "rapid", date(2025, 10, 1)) == 400
    assert layer0.effective_difference(2649, 2149, "standard", date(2025, 10, 1)) == 400


def test_r08_every_listed_player_is_carried_to_the_next_list():
    lists = {"2025-10": {1: entry(2000), 2: entry(2000), 9: entry(1700, k=40, birth_year=2012)}}
    t = tournament("t", date(2025, 10, 5), date(2025, 10, 6), "2025-11")
    res = layer0.next_list("2025-11", lists, [t], [layer0.Game("t", 1, 1, 2, "1/2-1/2")])
    assert sorted(res.entries) == [1, 2, 9]
    assert res.entries[9] == entry(1700, k=40, birth_year=2012)


def test_r32_below_1400_is_shown_as_unrated():
    lists = {"2025-11": {4: entry(1401, k=40), 5: entry(1800)}}
    t = tournament("t", date(2025, 11, 5), date(2025, 11, 6), "2025-12")
    res = layer0.next_list("2025-12", lists, [t], [layer0.Game("t", 1, 4, 5, "0-1")])
    assert 4 not in res.entries                                      # 1401 - 3.2 -> 1398
    assert res.state[4].pool == ()
    assert res.entries[5].rating == 1802                             # 20 x (1 - .92) = 1.6 -> 2


@pytest.mark.parametrize("last,expected", [("2024-11", True), ("2024-12", False)])
def test_r33_inactive_after_a_year_without_games(last, expected):
    lists = {"2025-10": {6: entry(1900)}}
    res = layer0.next_list("2025-11", lists, [], [], state={6: layer0.PlayerState(games_count=50, last_game_period=last)})
    assert res.entries[6].inactive is expected


def test_r33_one_game_restores_activity():
    lists = {"2025-10": {6: entry(1900, inactive=True), 7: entry(1900)}}
    t = tournament("t", date(2025, 10, 5), date(2025, 10, 6), "2025-11")
    res = layer0.next_list("2025-11", lists, [t], [layer0.Game("t", 1, 6, 7, "1/2-1/2")],
                           state={6: layer0.PlayerState(games_count=50, last_game_period="2024-01")})
    assert res.entries[6].inactive is False


def newcomer_games(scores):
    out = []
    for r, s in enumerate(scores, 1):
        out.append(layer0.Game("n", r, 20, 10 + r, {1: "1-0", 0.5: "1/2-1/2", 0: "0-1"}[s]))
    return out


def test_r27_r30_a_newcomer_is_published_with_k_40():
    lists = {"2025-10": {i: entry(1800) for i in range(11, 16)}}
    t = tournament("n", date(2025, 10, 5), date(2025, 10, 10), "2025-11")
    res = layer0.next_list("2025-11", lists, [t], newcomer_games([1, 1, 0.5, 0, 0]), birth_years={20: 1995})
    assert res.entries[20] == entry(1800, k=40, birth_year=1995, games=5)
    assert all(res.entries[i] == entry(1800) for i in range(11, 16))    # games against an unrated player are not rated


def test_r27_four_games_are_kept_in_the_pool():
    lists = {"2025-10": {i: entry(1800) for i in range(11, 15)}}
    t = tournament("n", date(2025, 10, 5), date(2025, 10, 10), "2025-11")
    res = layer0.next_list("2025-11", lists, [t], newcomer_games([1, 1, 0.5, 0]), birth_years={20: 1995})
    assert 20 not in res.entries
    assert len(res.state[20].pool) == 1 and len(res.state[20].pool[0].results) == 4


def test_r31_rapid_uses_the_standard_rating_of_an_unrated_player():
    rapid = {"2025-10": {8: entry(2000)}}
    standard = {"2025-10": {7: entry(2000)}}
    t = tournament("r", date(2025, 10, 5), date(2025, 10, 5), "2025-11", chapter="rapid")
    res = layer0.next_list("2025-11", rapid, [t], [layer0.Game("r", 1, 7, 8, "1-0")], birth_years={7: 1990},
                           standard_lists=standard)
    assert res.players[7].games[0].own_rating == 2000
    assert res.entries[7] == entry(2020, k=40, games=1)              # reading: K 40 as new to the rapid list
    assert res.entries[8].rating == 1990
