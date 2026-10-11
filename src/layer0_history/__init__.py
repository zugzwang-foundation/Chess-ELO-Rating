"""Layer 0 with the FIDE Rating Regulations in force at each date, February 2020 to October 2026 (SPEC-TOP100 §5).

Layer 0 (`src/layer0/`, Freeze 1, unchanged) implements the regulations effective 1 March 2024 as amended 1 October
2025. This package adds, beside it, the earlier rules that differ for the October 2026 top 100 over the replay's window,
as transcribed from FIDE's handbook archive in docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md:

- the 400-point rule: to 31 December 2021 a plain cap for every player (§8.54 of the 2017 regulations); from
  1 January 2022 to 29 February 2024 the cap with "only one upgrade" per tournament, for the game in which the
  difference is greatest (§8.3.1 of the 2022 regulations); from 1 March 2024 to 30 September 2025 the plain cap for
  every player (SPEC-L0 R-14a, NOT VERIFIED: the handbook shows only the amended text); from 1 October 2025 the cap
  below 2650 and the actual difference from 2650 (Layer 0, R-14);
- rounding: "0.5 is rounded up (whether the change is positive or negative)" (§8.57 of 2017) and, from 1 January
  2022, "0.5 is rounded away from zero" (§8.3.4, Layer 0's R-25). The 2017 words are read as rounding up in size, away
  from zero, as FIDE's own lists of 2020 and 2021 show: in every period of the top 100 whose sum ended in -x.5 the
  published change was rounded away from zero, never towards +infinity (E17, validation). The literal reading, towards
  +infinity, is kept as round_change_literal_2017 for the record of that test.

Table 8.1.2 (8.1(b) in 2017) is the same in every version, so PD comes from Layer 0's table. A version applies to the
tournaments that start on or after its effective date, and its rounding to the lists published on or after it (the
reading SPEC-L0 R-14a takes for the 1 October 2025 amendment; tested against FIDE's published calculations).
Python standard library only.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_FLOOR, Decimal

import layer0

V2022 = date(2022, 1, 1)          # "effective from 1 January 2022 till 29 February 2024"
V2024 = date(2024, 3, 1)          # "Applied from 1 March, 2024"
V2025 = layer0.rules.AMENDMENT_2650   # "Effective from 1 October 2025"
ROUNDING_2022_LIST = "2022-01"    # the first list published under the 2022 regulations


def version(start: date) -> str:
    """The regulations in force for a tournament that starts on `start`."""
    if start < V2022:
        return "2017"
    if start < V2024:
        return "2022"
    if start < V2025:
        return "2024"
    return "2025-10"


def differences(own: int, opponents: list[int], start: date) -> list[int]:
    """D for each of one player's games in one tournament, under the 400-point rule in force at the tournament's start.

    A difference beyond 400 counts as 400. In the 2022 version a player "may benefit from only one upgrade under this
    rule, for the game in which the rating difference is greatest": the cap lowers a favourite's PD, so for the
    favourite only the game with the greatest difference is capped (the first such game if several tie); a capped game
    raises the underdog's PD, so the underdog's are all capped. From 1 October 2025 a player rated 2650 or more uses
    the actual difference."""
    v = version(start)
    raw = [own - o for o in opponents]
    if v == "2025-10" and own >= 2650:
        return raw
    out = [d if abs(d) <= 400 else (400 if d > 0 else -400) for d in raw]
    if v == "2022":
        ups = [i for i, d in enumerate(raw) if d > 400]
        if len(ups) > 1:
            keep = max(ups, key=lambda i: (raw[i], -i))          # the greatest difference keeps its upgrade
            for i in ups:
                if i != keep:
                    out[i] = raw[i]
    return out


def deltas(own: int, games: list[tuple[int, Decimal]], start: date) -> list[Decimal]:
    """Delta R = score - PD for each (opponent's rating, score) of one tournament (§8.3.2, §8.55)."""
    ds = differences(own, [o for o, _s in games], start)
    return [Decimal(s) - layer0.expected_score(d) for d, (_o, s) in zip(ds, games)]


def round_change(x: Decimal, list_month: str) -> int:
    """The period's change rounded to a whole number, 0.5 away from zero, for every list of the window: §8.3.4 since
    January 2022, and §8.57 of 2017 read as FIDE's lists of 2020 and 2021 apply it (module docstring)."""
    return layer0.round_change(Decimal(x))


def round_change_literal_2017(x: Decimal) -> int:
    """§8.57 of 2017 read literally, 0.5 towards +infinity whatever the sign: the reading FIDE's lists refute."""
    return int((Decimal(x) + Decimal("0.5")).to_integral_value(rounding=ROUND_FLOOR))
