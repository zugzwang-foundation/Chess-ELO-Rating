"""A-10: the 2025 US Championship reproduced player by player (SPEC-L0 §6.4; tests/fixtures/validation/)."""
from datetime import date
from decimal import Decimal

import pytest

from l0_helpers import fixture, require_layer0, uscc_2025_inputs

layer0 = require_layer0()
FX = fixture("validation", "us_championship_2025.json")
PLAYERS = {p["fide_id"]: p for p in FX["players"]}
START = date.fromisoformat(FX["event"]["start"])
SCORE = {"1-0": (Decimal(1), Decimal(0)), "1/2-1/2": (Decimal("0.5"), Decimal("0.5")), "0-1": (Decimal(0), Decimal(1))}


def october(pid: int) -> int:
    return PLAYERS[pid]["list_2025_10"]["rating"]


@pytest.fixture(scope="module")
def result():
    return layer0.next_list(*uscc_2025_inputs(layer0))


def test_every_game_matches_fides_calculation():
    for g in FX["games"]:
        sw, sb = SCORE[g["result"]]
        assert g["fide_white"]["opponent_rating_used"] == october(g["black"])     # R-11a: the October list
        assert g["fide_black"]["opponent_rating_used"] == october(g["white"])
        assert layer0.game_delta(october(g["white"]), october(g["black"]), sw, "standard", START) == Decimal(g["fide_white"]["chg"])
        assert layer0.game_delta(october(g["black"]), october(g["white"]), sb, "standard", START) == Decimal(g["fide_black"]["chg"])


@pytest.mark.parametrize("pid", sorted(PLAYERS))
def test_every_player_matches_fides_tournament_calculation(result, pid):
    fide = PLAYERS[pid]["fide_tournament"]
    mine = result.players[pid]
    assert int(fide["Ro"]) == october(pid)
    assert len(mine.games) == int(fide["n"])
    assert sum(r.score for r in mine.games) == Decimal(fide["w"])
    assert mine.tournaments[0].sum_delta == Decimal(fide["chg"])
    assert mine.k == int(fide["K"])
    assert mine.tournaments[0].change == Decimal(fide["K_chg"])


@pytest.mark.parametrize("pid", sorted(PLAYERS))
def test_every_player_matches_the_november_list(result, pid):
    p = PLAYERS[pid]
    other = [Decimal(e["K_chg"]) for e in p["fide_other_events_in_period"]]
    if not other:                                   # the championship was the player's only event in the period
        assert result.entries[pid].rating == p["list_2025_11"]["rating"]
        assert result.entries[pid].games == p["list_2025_11"]["games"]
    total = result.players[pid].change + sum(other)
    assert total == Decimal(p["fide_total_change_shown"])
    assert october(pid) + layer0.round_change(total) == p["list_2025_11"]["rating"]   # R-25, once per period


def test_q1_per_tournament_rounding_fails_for_one_player(result):
    """SPEC-L0 §8 Q-1: 2020009 is reproduced only by rounding the period's change once."""
    p = PLAYERS[2020009]
    per_tournament = layer0.round_change(result.players[2020009].change) + \
        sum(layer0.round_change(Decimal(e["K_chg"])) for e in p["fide_other_events_in_period"])
    assert october(2020009) + per_tournament != p["list_2025_11"]["rating"]
