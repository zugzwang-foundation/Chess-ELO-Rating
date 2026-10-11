"""Layer 0 with the rules in force at each date (src/layer0_history/; SPEC-TOP100 §5).

The rules are those transcribed in docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md: the 400-point rule of
2017 (a plain cap), of 2022 (one upgrade per tournament), of 1 March 2024 (read as the plain cap, NOT VERIFIED) and of
1 October 2025 (the 2650 exemption, Layer 0's own); rounding of 2017 ("0.5 is rounded up (whether the change is
positive or negative)", read as away from zero, as FIDE's lists apply it) and of 2022 (away from zero). The fixtures are FIDE's published calculations of a few of the top 100's periods
(tests/fixtures/fide_history/published_periods.json): every game's Delta R, every tournament's K x sum and the list
change, opponents identified by the rating FIDE used, never by name."""
import json
from datetime import date
from decimal import Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402

FX = json.loads((ROOT / "tests" / "fixtures" / "fide_history" / "published_periods.json").read_text(encoding="utf-8"))


def test_versions_by_tournament_start():
    assert lh.version(date(2021, 12, 31)) == "2017"
    assert lh.version(date(2022, 1, 1)) == "2022"
    assert lh.version(date(2024, 2, 29)) == "2022"
    assert lh.version(date(2024, 3, 1)) == "2024"
    assert lh.version(date(2025, 9, 30)) == "2024"
    assert lh.version(date(2025, 10, 1)) == "2025-10"


def test_the_400_point_rule_in_each_version():
    opps = [2300, 2250, 2600]                                   # gaps 450, 500, 150 for a 2750
    assert lh.differences(2750, opps, date(2021, 6, 1)) == [400, 400, 150]          # 2017: every game capped
    assert lh.differences(2750, opps, date(2023, 6, 1)) == [450, 400, 150]          # 2022: one upgrade, the greatest gap
    assert lh.differences(2750, opps, date(2024, 9, 1)) == [400, 400, 150]          # 2024 as read (R-14a)
    assert lh.differences(2750, opps, date(2025, 10, 1)) == [450, 500, 150]         # 2650 and above: no cap
    assert lh.differences(2600, opps, date(2025, 10, 1)) == [300, 350, 0]
    assert lh.differences(2300, [2750, 2800], date(2023, 6, 1)) == [-400, -400]      # the underdog: every game capped
    assert lh.differences(2750, [2300, 2300], date(2023, 6, 1)) == [400, 450]        # a tie: the first keeps the upgrade


def test_rounding_in_each_version():
    # §8.57 of 2017, "0.5 is rounded up (whether the change is positive or negative)", is read as up in size, away from
    # zero, as FIDE's own lists of 2020 and 2021 apply it (fixture F-H02; E17 §2); the literal reading is kept apart.
    assert lh.round_change(Decimal("-2.5"), "2021-12") == -3
    assert lh.round_change_literal_2017(Decimal("-2.5")) == -2
    assert lh.round_change(Decimal("2.5"), "2021-12") == lh.round_change_literal_2017(Decimal("2.5")) == 3
    assert lh.round_change(Decimal("-2.5"), "2022-01") == -3                       # §8.3.4 since 2022: away from zero
    assert lh.round_change(Decimal("-2.4"), "2021-03") == -2 and lh.round_change(Decimal("-2.6"), "2021-03") == -3
    assert lh.round_change(Decimal("2.5"), "2026-10") == layer0.round_change(Decimal("2.5")) == 3
    f_h02 = next(c for c in FX["cases"] if c["id"] == "F-H02")
    assert Decimal(f_h02["sum"]) % 1 == Decimal("-0.5") and f_h02["list"] < "2022-01"
    assert lh.round_change(Decimal(f_h02["sum"]), f_h02["list"]) == f_h02["published_change"]
    assert lh.round_change_literal_2017(Decimal(f_h02["sum"])) != f_h02["published_change"]


def test_fides_published_calculations_are_reproduced():
    assert not FX["missing"] and [c["id"] for c in FX["cases"]] == ["F-H01", "F-H02", "F-H03", "F-H04", "F-H05"]
    for case in FX["cases"]:
        total = Decimal(0)
        for tr in case["tournaments"]:
            start = date.fromisoformat(tr["start"])
            games = [(g["opponent_rating"], Decimal(g["score"])) for g in tr["games"]]
            ds = lh.deltas(tr["ro"], games, start)
            assert [str(d) for d in ds] == [g["chg"] for g in tr["games"]], (case["id"], tr["start"])
            assert Decimal(tr["k"]) * sum(ds, Decimal(0)) == Decimal(tr["k_chg"]), (case["id"], tr["start"])
            total += Decimal(tr["k"]) * sum(ds, Decimal(0))
        assert lh.round_change(total, case["list"]) == case["published_change"], case["id"]


def _reproduced(tr, as_of: date | None) -> bool:
    """FIDE's chg of every game of the tournament under the rules in force at `as_of`, or with no cap if None."""
    games = [(g["opponent_rating"], Decimal(g["score"])) for g in tr["games"]]
    ds = lh.deltas(tr["ro"], games, as_of) if as_of else [s - layer0.expected_score(tr["ro"] - r) for r, s in games]
    return [str(d) for d in ds] == [g["chg"] for g in tr["games"]]


def test_each_fixture_shows_its_rule_and_the_neighbouring_reading_fails_it():
    case = {c["id"]: c for c in FX["cases"]}
    beyond = lambda tr: [g for g in tr["games"] if tr["ro"] - g["opponent_rating"] > 400]  # noqa: E731
    start = lambda tr: date.fromisoformat(tr["start"])  # noqa: E731
    # F-H01: the 2017 plain cap at work; without the cap the tournament is not reproduced.
    trs = [tr for tr in case["F-H01"]["tournaments"]
           if lh.version(start(tr)) == "2017" and any(g["capped_mark"] for g in tr["games"])]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, None) for tr in trs)
    # F-H03: under the 2022 text, of two or more differences beyond 400 FIDE capped one, the greatest; the plain cap
    # of 2017 does not reproduce the tournament.
    trs = [tr for tr in case["F-H03"]["tournaments"]
           if lh.version(start(tr)) == "2022" and len(beyond(tr)) >= 2 and sum(g["capped_mark"] for g in beyond(tr)) == 1]
    assert trs
    for tr in trs:
        assert max(beyond(tr), key=lambda g: tr["ro"] - g["opponent_rating"])["capped_mark"]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, date(2021, 6, 1)) for tr in trs)
    # F-H04: from 1 March 2024 FIDE capped two or more of a favourite's games; the 2022 clause does not reproduce it.
    trs = [tr for tr in case["F-H04"]["tournaments"]
           if lh.version(start(tr)) == "2024" and sum(g["capped_mark"] for g in beyond(tr)) >= 2]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, date(2023, 6, 1)) for tr in trs)
    # F-H05: from 1 October 2025 a player rated 2650 or more is not capped; the rule of 2024 does not reproduce it.
    trs = [tr for tr in case["F-H05"]["tournaments"]
           if lh.version(start(tr)) == "2025-10" and tr["ro"] >= 2650 and any(not g["capped_mark"] for g in beyond(tr))]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, date(2024, 9, 1)) for tr in trs)


# ------------------------------------------------------------------ the replay's own functions (analysis/e17_top100_extract.py)
import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "analysis"))
import e17_top100_extract as ex  # noqa: E402


def test_name_keys_meet_across_word_order_and_accents():
    # Synthetic names: no real player is named in a committed file (SPEC-TOP100 §2, §8).
    assert ex.norm("Doe, Jane") == ex.norm("Jane Doe") == ex.norm("DOE  jane")
    assert ex.norm("Núñez Pérez, Ana") == ex.norm("Ana Nunez Perez")
    assert ex.norm("Roe, Sam") != ex.norm("Roe, Samuel")


def test_the_list_a_tournament_uses():
    assert ex.list_used("2019-12-27", "2020-02") == "2019-12"      # started under the December list, rated in February
    assert ex.list_used("2020-01-19", "2020-02") == "2020-01"
    assert ex.list_used("2020-02-03", "2020-02") == "2020-01"      # never later than the list before the one rating it
    assert ex.list_used(None, "2020-02") == "2020-01"


def test_a_colour_needs_one_broadcast_game():
    day = date(2023, 5, 2)
    games = {day: [("111", "222", "a b", "c d", "1-0")]}
    m = ex.match_colour("111", "a b", "222", "c d", Decimal(1), "2023-05-01", "2023-05-09", games)
    assert m == "white"
    assert ex.match_colour("222", "c d", "111", "a b", Decimal(0), "2023-05-01", "2023-05-09", games) == "black"
    assert ex.match_colour("111", "a b", "222", "c d", Decimal("0.5"), "2023-05-01", "2023-05-09", games) is None
    twice = {day: games[day], date(2023, 5, 5): [("222", "111", "c d", "a b", "0-1")]}       # two games, two colours
    assert ex.match_colour("111", "a b", "222", "c d", Decimal(1), "2023-05-01", "2023-05-09", twice) is None
    by_name = {day: [("", "", "a b", "c d", "1-0")]}                                        # no IDs in the broadcast
    assert ex.match_colour("111", "a b", None, "c d", Decimal(1), "2023-05-01", "2023-05-09", by_name) == "white"


def test_rung_2s_expectation_sums_to_one_and_has_no_cap():
    for own, opp in ((2750, 2700), (2750, 2300), (2650, 2100), (2400, 2390)):
        assert ex.e_rung2(own, opp, 1) + ex.e_rung2(opp, own, -1) == 1
        assert ex.e_rung2(own, opp, 0) + ex.e_rung2(opp, own, 0) == 1
    assert ex.e_rung2(2800, 2000, 0) > layer0.expected_score(400)  # no 400-point rule: an 800-point favourite expects more


def test_the_difference_is_nil_before_the_replay_starts():
    r2, l0 = {"1": {"2020-01": 2700, "2020-02": 2705}}, {"1": {"2020-01": 2700, "2020-02": 2701}}
    assert ex.diff(r2, l0, "1", "2019-12") == 0 and ex.diff(r2, l0, "1", "2020-02") == 4
