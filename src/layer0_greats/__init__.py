"""Layer 0 with the FIDE Rating Regulations in force from the list of April 2008 to December 2019, for the greats'
replay (SPEC-GREATS v1.0 §6).

Layer 0 (`src/layer0/`, Freeze 1, unchanged) implements the regulations effective 1 March 2024 as amended 1 October
2025, and `src/layer0_history/` (E17) the versions from 1 July 2017. This package adds, beside them, the versions in force
before July 2017, as transcribed from FIDE's handbook and the Internet Archive's copies of it in
docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md:

- **"2007"**, for tournaments that start before 1 July 2009: each game against a rated player, "A difference in rating
  of more than 350 points shall be counted for rating purposes as though it were a difference of 350 points", ΔR = score
  − PD, ΣΔR × K (§10.51 of the text FIDE's handbook carried in October 2007); K 25, 15 and 10 (§10.52);
- **"2009"**, for tournaments that start from 1 July 2009 to 30 June 2014: the same with 400 points (§8.54 and §8.55 of
  the text of June 2010); K 25, 15 and 10 (§8.56);
- **"2014"**, from 1 July 2014 to 30 June 2017: 400 points (§8.54); K 40, 20 and 10, and 40 for juniors under 2300
  (§8.56); "The Rating Change is rounded to the nearest whole number. 0.5 is rounded up ( whether the change is positive
  or negative )" (§8.57);
- from 1 July 2017, `layer0_history`'s versions.

Two readings the texts leave open are tested by the replay on FIDE's own calculations (E20 §4.2): the date the
350-point rule became the 400-point rule (between the copies of October 2007 and June 2010; read as 1 July 2009, which
FIDE's pages bear out), and the rounding of the period's change on the lists published before July 2014. The 2007 and
2010 texts round the rated player's new rating, the old rating plus the change ("Rn is rounded off to the nearest 1 or
0", §10.53 of 2007; "R n is rounded off to the nearest 1 or 0, 0.5 is rounded to 1", §8.57 of 2010), which with 0.5
rounded up rounds the change with 0.5 towards +infinity. The rules record first described those clauses as rounding a
new player's rating and read the lists before July 2014 as the 2014 clause applied as E17 found FIDE's lists apply the
same words of 2017, 0.5 away from zero; FIDE's pages contradict that reading, ruling R74
(docs/decisions/D-0017_rulings-on-the-greats.md; SPEC-L0 §11, finding F-H09) adopts 0.5 towards +infinity for every
list published before July 2014 (the switch made after partial pages had been seen, before the full replay), and the
session's review corrected the description of the texts (docs/review/REDTEAM_v1_0.md, ELO9-QC-1). Ruling R80
(docs/decisions/D-0018_rulings-on-elo-9-questions.md; SPEC-L0 §11, finding F-H10) extends 0.5 towards +infinity to every
list to October 2018: FIDE's lists of July 2014 to July 2018 round every negative half point that way, as the 2014 and
2017 words read literally say, "0.5 is rounded up (whether the change is positive or negative)"; from the list of
November 2018 the change is rounded 0.5 away from zero, FIDE's arithmetic having changed while the words did not (as
E17 found on the lists from February 2020, F-H07). The switch lies between the lists of August and November 2018, and
its exact list is NOT VERIFIED; R80 was set after FIDE's pages had been read in the full replay. D-0017's reading, 0.5
away from zero from the list of July 2014, is kept beside it (round_change_d0017), as R74 kept the first reading, so
that E20 prints the counts under both. The score-probability table of every version equals table 8.1.2 (the record,
§5), so PD comes from Layer 0's table. A version applies to the tournaments that start on or after its date, and a
rounding to the lists published on or after its date. Python standard library only.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_FLOOR, Decimal

import layer0
import layer0_history

V2009 = date(2009, 7, 1)          # the 400-point rule (reading: the first date after the October 2007 copy's 350 points)
V2014 = date(2014, 7, 1)          # "effective from 1 July 2014 till 30 June 2017"
V2017 = date(2017, 7, 1)          # layer0_history's first version
ROUNDING_2014_LIST = "2014-07"    # the first list published under the 2014 regulations (R74: before it, 0.5 up)
ROUNDING_2018_LIST = "2018-11"    # R80: the first list rounding 0.5 away from zero (before it, 0.5 up)


def version(start: date) -> str:
    """The regulations in force for a tournament that starts on `start`."""
    if start < V2009:
        return "2007"
    if start < V2014:
        return "2009"
    if start < V2017:
        return "2014"
    return layer0_history.version(start)


def cap(start: date) -> int:
    """The rating-difference rule's limit in force for a tournament that starts on `start`, before July 2017."""
    return 350 if start < V2009 else 400


def differences(own: int, opponents: list[int], start: date) -> list[int]:
    """D for each of one player's games in one tournament, under the rating-difference rule in force at its start."""
    if start >= V2017:
        return layer0_history.differences(own, opponents, start)
    c = cap(start)
    return [d if abs(d) <= c else (c if d > 0 else -c) for d in (own - o for o in opponents)]


def deltas(own: int, games: list[tuple[int, Decimal]], start: date) -> list[Decimal]:
    """Delta R = score - PD for each (opponent's rating, score) of one tournament."""
    ds = differences(own, [o for o, _s in games], start)
    return [Decimal(s) - layer0.expected_score(d) for d, (_o, s) in zip(ds, games)]


def round_change(x: Decimal, list_month: str) -> int:
    """The period's change on the list `list_month` rounded to a whole number (R80): on every list to October 2018, 0.5
    towards +infinity (round_change_up; R74 before July 2014, R80 from it); from the list of November 2018, 0.5 away
    from zero (round_change_away)."""
    return round_change_up(x) if list_month < ROUNDING_2018_LIST else round_change_away(x)


def round_change_d0017(x: Decimal, list_month: str) -> int:
    """D-0017's reading, which R80 supersedes from the list of July 2014 and which is kept for the counts E20 prints
    beside R80's: 0.5 towards +infinity on the lists before July 2014 (R74), away from zero from the list of July
    2014."""
    return round_change_up(x) if list_month < ROUNDING_2014_LIST else round_change_away(x)


def round_change_away(x: Decimal) -> int:
    """0.5 away from zero: FIDE's lists from November 2018 (R80), as E17 found them from February 2020 for the same
    words of 2017 (F-H07), and as the 2022 text says outright; also the rules record's first reading for every list,
    which FIDE's pages contradict before November 2018 (R74, R80), kept for that test."""
    return layer0.round_change(Decimal(x))


def round_change_up(x: Decimal) -> int:
    """0.5 towards +infinity whatever the sign: the new rating rounded with 0.5 up (§8.57 of 2010, "0.5 is rounded to
    1"), and the words of §8.57 of 2014 and of 2017, "0.5 is rounded up ( whether the change is positive or negative
    )", read literally; FIDE's lists to October 2018 follow it (R74 before July 2014, finding F-H09; R80 from July
    2014, finding F-H10; E20 §4.2)."""
    return int((Decimal(x) + Decimal("0.5")).to_integral_value(rounding=ROUND_FLOOR))


def k_rule(ver: str, rating: int, ever2400: bool, games_total: int, junior_under_2300: bool = False) -> int:
    """K by the version's §10.52 / §8.56 for a player with `games_total` games so far: 10 once the published rating has
    reached 2400 (the 2007 text: "and he has also completed events with a total of at least 30 games"; from 2009 it
    "remains at that level subsequently, even if the rating drops below 2400"), otherwise the version's value for a
    player new to the list until 30 games (25; 40 from 2014) or its middle value (15; 20 from 2014); 2014 adds 40 for
    juniors under 2300. `rating` is kept for the caller's record: every version's rule reads the published rating
    through `ever2400`. From 2017, layer0.published_k applies instead."""
    if ver == "2007":
        if ever2400 and games_total >= 30:
            return 10
        return 25 if games_total < 30 else 15
    if ver in ("2009", "2014"):
        if ever2400:
            return 10
        if ver == "2014" and junior_under_2300:
            return 40
        if games_total < 30:
            return 25 if ver == "2009" else 40
        return 15 if ver == "2009" else 20
    raise ValueError(f"version {ver}: use layer0.published_k")
