"""Layer 0 with the rules in force from April 2008 to June 2017 (src/layer0_greats/; SPEC-GREATS v1.0 §6).

The rules are those transcribed in docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md: the 350-point rule of the
October 2007 text, the 400-point rule of the June 2010 text (read as applying to tournaments from 1 July 2009, which
FIDE's pages bear out), K 25/15/10 and, from 1 July 2014, 40/20/10; the rounding of the lists before July 2014, 0.5
towards +infinity (ruling R74, SPEC-L0 §11, F-H09: the 2007 and 2010 texts round the new rating, §10.53 and §8.57),
and from July 2014 the 2014 clause read as away from zero.
The fixtures are a small sample of FIDE's published calculations of the greats' periods chosen by a fixed rule (R79:
at most 30 player-periods; tests/fixtures/fide_greats/published_periods.json, written by
tools/data/assemble_greats_fixtures.py): every game's Delta R, every tournament's K x sum and the list change,
opponents identified by the rating FIDE used, never by name."""
import json
from datetime import date
from decimal import Decimal

from l0_helpers import ROOT, require_layer0

require_layer0()
import layer0  # noqa: E402
import layer0_greats as lg  # noqa: E402

FX = json.loads((ROOT / "tests" / "fixtures" / "fide_greats" / "published_periods.json").read_text(encoding="utf-8"))


def test_versions_by_tournament_start():
    assert lg.version(date(2008, 1, 12)) == "2007"
    assert lg.version(date(2009, 6, 30)) == "2007"
    assert lg.version(date(2009, 7, 1)) == "2009"
    assert lg.version(date(2014, 6, 30)) == "2009"
    assert lg.version(date(2014, 7, 1)) == "2014"
    assert lg.version(date(2017, 6, 30)) == "2014"
    assert lg.version(date(2017, 7, 1)) == "2017"                    # layer0_history's first version


def test_the_350_and_400_point_rules():
    assert lg.differences(2700, [2300, 2650, 3100], date(2008, 5, 12)) == [350, 50, -350]
    assert lg.differences(2700, [2300, 2650, 3150], date(2009, 7, 9)) == [400, 50, -400]
    assert lg.differences(2710, [2339], date(2009, 6, 30)) == [350]          # a gap of 371: capped before July 2009
    assert lg.differences(2710, [2339], date(2009, 7, 1)) == [371]           # and used in full from it
    assert lg.differences(2700, [2250], date(2016, 1, 1)) == [400]
    assert lg.differences(2700, [2250], date(2018, 1, 1)) == [400]           # 2017: layer0_history's plain cap
    assert lg.deltas(2700, [(2300, Decimal(1))], date(2008, 5, 12)) == [Decimal("0.11")]
    assert lg.deltas(2700, [(2300, Decimal(1))], date(2009, 7, 9)) == [Decimal("0.08")]


def test_k_rules_of_each_version():
    assert lg.k_rule("2007", 2344, False, 30) == 15                          # below 2400, never 2400, 30 games
    assert lg.k_rule("2007", 2344, False, 12) == 25                          # new to the list
    assert lg.k_rule("2009", 2380, True, 30) == 10                           # 2400 reached once: "remains at that level"
    assert lg.k_rule("2014", 2380, False, 30) == 20
    assert lg.k_rule("2014", 2250, False, 30, junior_under_2300=True) == 40
    assert lg.k_rule("2014", 2700, True, 300) == 10


def test_rounding_by_the_list():
    # R74: on the lists before July 2014 0.5 towards +infinity: the 2007 and 2010 texts round the new rating (§10.53;
    # §8.57, "0.5 is rounded to 1"), as FIDE's lists show (F-H09);
    # from the list of July 2014 the 2014 clause read as away from zero, as E17 found the same words of 2017 applied.
    assert lg.round_change(Decimal("-8.5"), "2014-06") == -8 and lg.round_change(Decimal("8.5"), "2014-06") == 9
    assert lg.round_change(Decimal("-8.5"), "2014-07") == -9 and lg.round_change(Decimal("8.5"), "2014-07") == 9
    assert lg.round_change(Decimal("-8.4"), "2010-01") == -8 and lg.round_change(Decimal("-8.6"), "2010-01") == -9
    assert lg.round_change_up(Decimal("-2.5")) == -2 and lg.round_change_away(Decimal("-2.5")) == -3
    assert lg.round_change_away(Decimal("2.5")) == layer0.round_change(Decimal("2.5")) == 3


def test_the_sample_is_small_and_complete():
    # R79: at most 30 player-periods, chosen by the fixed rule of tools/data/assemble_greats_fixtures.py
    assert not FX["missing"] and [c["id"] for c in FX["cases"]] == [f"F-G{i:02d}" for i in range(1, 15)]
    periods = {(c["list"], c["sum"], json.dumps(c["tournaments"], sort_keys=True)) for c in FX["cases"]}
    assert len(periods) == FX["player_periods"] <= 30


def test_fides_published_calculations_are_reproduced():
    for case in FX["cases"]:
        total = Decimal(0)
        for tr in case["tournaments"]:
            start = date.fromisoformat(tr["start"])
            games = [(g["opponent_rating"], Decimal(g["score"])) for g in tr["games"]]
            ds = lg.deltas(tr["ro"], games, start)
            assert [str(d) for d in ds] == [g["chg"] for g in tr["games"]], (case["id"], tr["start"])
            assert Decimal(tr["k"]) * sum(ds, Decimal(0)) == Decimal(tr["k_chg"]), (case["id"], tr["start"])
            total += Decimal(tr["k"]) * sum(ds, Decimal(0))
        assert str(total) == case["sum"] and lg.round_change(total, case["list"]) == case["published_change"], case["id"]


def _reproduced(tr, as_of: date | None) -> bool:
    """FIDE's chg of every game of the tournament under the rules in force at `as_of`, or with no cap if None."""
    games = [(g["opponent_rating"], Decimal(g["score"])) for g in tr["games"]]
    ds = lg.deltas(tr["ro"], games, as_of) if as_of else [s - layer0.expected_score(tr["ro"] - r) for r, s in games]
    return [str(d) for d in ds] == [g["chg"] for g in tr["games"]]


def test_each_fixture_shows_its_rule_and_the_neighbouring_reading_fails_it():
    case = {c["id"]: c for c in FX["cases"]}
    start = lambda tr: date.fromisoformat(tr["start"])  # noqa: E731
    gaps = lambda tr: [(tr["ro"] - g["opponent_rating"], tr["ro"] - g["printed_rating"], g["capped_mark"])  # noqa: E731
                       for g in tr["games"]]
    # F-G01: before July 2009 FIDE printed a gap beyond 350 as 350, unmarked; the 400-point rule does not reproduce it.
    trs = [tr for tr in case["F-G01"]["tournaments"] if lg.version(start(tr)) == "2007"
           and any(abs(gs) == 350 < abs(ga) and not c for ga, gs, c in gaps(tr))]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, date(2009, 7, 1)) for tr in trs)
    # F-G02: from July 2009 FIDE marked a gap beyond 400 as capped at 400; without the cap it is not reproduced.
    trs = [tr for tr in case["F-G02"]["tournaments"] if lg.version(start(tr)) == "2009"
           and any(c and abs(gs) == 400 < abs(ga) for ga, gs, c in gaps(tr))]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, None) for tr in trs)
    # F-G03: from July 2009 a gap of 351 to 400 points counted in full; the 350-point rule does not reproduce it.
    trs = [tr for tr in case["F-G03"]["tournaments"] if lg.version(start(tr)) == "2009"
           and any(350 < abs(ga) <= 400 and ga == gs for ga, gs, _c in gaps(tr))]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, date(2009, 6, 30)) for tr in trs)
    # F-G04: K 15 for a player below 2400 who had never reached it (§10.52 of the October 2007 text).
    c4 = case["F-G04"]
    assert not c4["ever_2400_before"]
    assert any(tr["k"] == 15 and lg.k_rule("2007", tr["ro"], False, 30) == 15 for tr in c4["tournaments"])
    # F-G05: the 2014 regulations' 400-point rule; without the cap it is not reproduced.
    trs = [tr for tr in case["F-G05"]["tournaments"] if lg.version(start(tr)) == "2014"
           and any(c and abs(gs) == 400 < abs(ga) for ga, gs, c in gaps(tr))]
    assert any(_reproduced(tr, start(tr)) and not _reproduced(tr, None) for tr in trs)


def test_f_g06_a_negative_half_point_before_july_2014_went_up():
    # F-H09 (R74): on a list before July 2014 FIDE rounded a negative half point towards +infinity, not away from zero.
    c = next(c for c in FX["cases"] if c["id"] == "F-G06")
    total = Decimal(c["sum"])
    assert c["list"] < "2014-07" and total < 0 and abs(total) % 1 == Decimal("0.5")
    assert lg.round_change_up(total) == c["published_change"] != lg.round_change_away(total)


def test_first_period_of_each_version_and_either_side_of_the_switches():
    case = {c["id"]: c for c in FX["cases"]}
    versions = lambda c: {lg.version(date.fromisoformat(tr["start"])) for tr in c["tournaments"]}  # noqa: E731
    starts = lambda c: [tr["start"] for tr in c["tournaments"]]  # noqa: E731
    for fid, ver in (("F-G07", "2007"), ("F-G08", "2009"), ("F-G09", "2014"), ("F-G10", "2017")):
        assert ver in versions(case[fid]), fid
    for before, after, d0 in (("F-G11", "F-G12", "2009-07-01"), ("F-G13", "F-G14", "2014-07-01")):
        assert any(x < d0 for x in starts(case[before])) and any(x >= d0 for x in starts(case[after]))
        assert max(x for x in starts(case[before]) if x < d0) < d0 <= min(x for x in starts(case[after]) if x >= d0)
