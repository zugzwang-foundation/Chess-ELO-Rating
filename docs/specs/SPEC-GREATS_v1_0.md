# SPEC-GREATS — the greats on legitimate data: who is studied, what is computed for each, and how it is worded, v1.0

**Status: REVIEW — written before any analysis of the players it names (ELO-9 brief, Phase 2).** The names in §2 come from `analysis/greats_select.py`, which applies §2's rule to the lists and computes nothing else; no rating series, gap or replay of any player named here had been computed when this specification was merged. Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`), except the figures of §2's table that rest on OlimpBase's transcription, which carry ruling R83's label (added in session ELO-10, `docs/decisions/D-0018_rulings-on-elo-9-questions.md`; the rule, the names and the definitions are unchanged, §9) · Date: 2026-10-11 · The table applied backwards in §6 is PROVISIONAL-FITTED (E18); every other parameter met here is PROVISIONAL.

## 1 Purpose, and the words on every table

E20 reports what FIDE's own data, as far as they are legitimately available (`docs/research/DATA-PROBE_greats.md`), show about the players ranked 1st to 3rd on FIDE's lists since 1971: their published series, their dominance of their own lists, and, where FIDE's calculations give every game, their ratings replayed under FIDE's rules and under the 2025 self-calibrating table applied backwards. It is not an all-time ranking and makes no comparison across eras (§7).

Every table of E20 and of the proposal's appendix carries, above it, the fixed wording:

> *Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's own era.*

## 2 Who is studied (the founder default)

**The rule.** Everyone ranked 1st to 3rd on any FIDE standard list from July 1971 to December 2019 that the data probe found legitimately available:

- **July 1971 to April 2000.** FIDE's official lists as OlimpBase transcribes them (free of charge, citing the source, non-commercial; DATA-PROBE §3), without the supplementary lists of July 1978, 1979 and 1980, which carry only a few players, and without the unofficial lists before July 1971. A player's rank is 1 + the number of ranked players with a higher rating, players tied sharing a rank. Ranked are the players with a rating who are not flagged inactive (the lists carry flags from July 1992) and, from the January 1999 list, are active by FIDE's rule for the top list: "Players are considered to commence inactivity if they play fewer than 4 rated games in a one year period" and "a player who is deemed to be inactive over a 12 months period of inactivity on the rating list will no longer appear on the monthly top list (GA '98)" (FIDE Handbook B.02 §9.2.3a and §9.2.3d, http://www.fide.com/official/handbook.asp?level=B0209, the Internet Archive's copy of 2003-05-12), the games counted on the lists dated in the twelve months up to the list.
- **July 2000 to December 2019.** FIDE's own printed top-100 list of the date, as the Internet Archive keeps FIDE's top-list archive (DATA-PROBE §2.2), the rank as FIDE printed it. FIDE breaks ties: on its list of October 2006 Kramnik is 3rd and Svidler 4th on 2750 each (https://web.archive.org/web/2008id_/http://ratings.fide.com:80/toparc.phtml?cod=101, read on 2026-10-11). Where no copy of a date's top list survives, the rank is computed as above from FIDE's full list of that date, with the activity rule in force: fewer than four rated games in a year to the lists of June 2009; from July 2009, "A player is considered to commence inactivity if he plays no rated games in a one year period" with "a player who is inactive over a 12 month period of inactivity on the rating list will no longer appear on the top list" (B.02 §7.23a and §7.24, http://www.fide.com/fide/handbook.html?id=72&view=article, the Internet Archive's copy of 2010-06-09; the July 2009 date of the change is a reading, NOT VERIFIED).
- **The player.** On OlimpBase's lists, OlimpBase's standard form of the name, joined to the FIDE ID that the same name carries on OlimpBase's lists of 2001: FIDE's IDs begin in 1990, changed format in July 1990, changed again when federations split, and were reassigned (Shirov's Latvian ID of 1994 belongs to another player on FIDE's later lists), so a name is the stable key before 2001. From 2001 the key is the FIDE ID; a printed top list is joined to the ID that FIDE's full list of the same date gives the same name and federation.

**How the rule came to be.** The first version ranked every list from its flags and keyed players by FIDE ID. Its first runs, which computed ranks only, showed three things before the rule was fixed: players split by the ID changes; Shirov's 1994 rank credited to the later holder of his old ID; and FIDE's files leaving Kasparov unflagged from April 2005 to October 2007, after his last rated games, while FIDE's own top list of April 2006 omits him (Topalov 1st, Anand 2nd, Aronian 3rd; https://web.archive.org/web/2008id_/http://ratings.fide.com:80/toparc.phtml?cod=93, read on 2026-10-11). The rule above replaces the flags with FIDE's top-list rule and FIDE's printed ranks wherever FIDE printed them, and keys players as described. No series, gap or replay had been computed. E20 compares, on every date with both, the top three the computed rule gives with FIDE's printed ones.

**The players.** Printed by `python3 analysis/greats_select.py --table` from `analysis/aggregates/GREATS_players.json` (`tests/test_greats_spec.py` checks that this table is that output, verbatim). Names and IDs are FIDE's as its lists print them (OlimpBase's standard form for players who left before 2001), with the federation of their latest list:

<!-- GREATS-TABLE START -->
| # | name | FIDE ID | federation | first list ranked 1–3 | last | lists ranked 1–3 | lists ranked 1st | best rank |
|---|---|---|---|---|---|---|---|---|
| 1 | Fischer, Robert J | 2000016 | USA | 1971-07 | 1975-01 | 5 | 5 | 1 |
| 2 | Korchnoi, Viktor | 1300016 | SUI | 1971-07 | 1984-01 | 13 | 0 | 2 |
| 3 | Spassky, Boris V. | 600024 | RUS | 1971-07 | 1979-01 | 4 | 0 | 2 |
| 4 | Petrosian, Tigran | — | URS | 1972-07 | 1977-01 | 3 | 0 | 2 |
| 5 | Polugaevsky, Lev | — | RUS | 1972-07 | 1976-01 | 2 | 0 | 3 |
| 6 | Karpov, Anatoly | 4100026 | RUS | 1973-07 | 1997-01 | 41 | 14 | 1 |
| 7 | Tal, Mikhail N. | — | LAT | 1973-07 | 1980-01 | 2 | 0 | 2 |
| 8 | Mecking, Henrique | 2100010 | BRA | 1978-01 | 1978-01 | 1 | 0 | 3 |
| 9 | Portisch, Lajos | 700037 | HUN | 1978-01 | 1981-01 | 3 | 0 | 2 |
| 10 | Huebner, Robert | 4600010 | GER | 1981-07 | 1981-07 | 1 | 0 | 3 |
| 11 | Timman, Jan H | 1000012 | NED | 1982-01 | 1990-01 | 7 | 0 | 2 |
| 12 | Kasparov, Garry | 4100018 | RUS | 1982-07 | 2006-01 | 57 | 53 | 1 |
| 13 | Ljubojevic, Ljubomir | 900010 | SRB | 1983-01 | 1984-01 | 3 | 0 | 3 |
| 14 | Beliavsky, Alexander G | 14602377 | SLO | 1985-07 | 1985-07 | 1 | 0 | 3 |
| 15 | Jussupow, Artur | 4618777 | GER | 1986-01 | 1987-07 | 4 | 0 | 3 |
| 16 | Vaganian, Rafael A | 13300016 | ARM | 1986-01 | 1986-01 | 1 | 0 | 3 |
| 17 | Sokolov, Andrei | 627089 | FRA | 1987-01 | 1987-07 | 2 | 0 | 3 |
| 18 | Short, Nigel D | 400025 | ENG | 1988-07 | 1989-07 | 3 | 0 | 3 |
| 19 | Ivanchuk, Vassily | 14100010 | UKR | 1989-07 | 2009-01 | 10 | 0 | 2 |
| 20 | Gelfand, Boris | 2805677 | ISR | 1990-07 | 1991-01 | 2 | 0 | 3 |
| 21 | Anand, Viswanathan | 5000017 | IND | 1993-01 | 2015-12 | 67 | 8 | 1 |
| 22 | Shirov, Alexei | 2209390 | ESP | 1994-01 | 1994-07 | 2 | 0 | 2 |
| 23 | Kramnik, Vladimir | 4101588 | RUS | 1994-07 | 2018-03 | 77 | 2 | 1 |
| 24 | Salov, Valery | 4100069 | RUS | 1995-01 | 1995-01 | 1 | 0 | 3 |
| 25 | Topalov, Veselin | 2900084 | BUL | 2005-01 | 2015-12 | 31 | 10 | 1 |
| 26 | Aronian, Levon | 13300474 | ARM | 2006-04 | 2017-12 | 43 | 0 | 2 |
| 27 | Morozevich, Alexander | 4116992 | RUS | 2008-04 | 2008-10 | 3 | 0 | 2 |
| 28 | Carlsen, Magnus | 1503014 | NOR | 2009-04 | 2019-12 | 108 | 102 | 1 |
| 29 | Caruana, Fabiano | 2020009 | USA | 2013-07 | 2019-12 | 51 | 0 | 2 |
| 30 | Nakamura, Hikaru | 2016192 | USA | 2014-01 | 2015-10 | 4 | 0 | 2 |
| 31 | Grischuk, Alexander | 4126025 | RUS | 2014-05 | 2015-02 | 6 | 0 | 3 |
| 32 | Giri, Anish | 24116068 | NED | 2016-01 | 2016-02 | 2 | 0 | 3 |
| 33 | Vachier-Lagrave, Maxime | 623539 | FRA | 2016-08 | 2017-10 | 5 | 0 | 2 |
| 34 | So, Wesley | 5202213 | USA | 2017-02 | 2017-08 | 7 | 0 | 2 |
| 35 | Mamedyarov, Shakhriyar | 13401319 | AZE | 2017-12 | 2019-01 | 14 | 0 | 2 |
| 36 | Ding, Liren | 8603677 | CHN | 2019-02 | 2019-12 | 11 | 0 | 3 |
<!-- GREATS-TABLE END -->

For the table's lists to April 2000, under ruling R83 (`docs/decisions/D-0018_rulings-on-elo-9-questions.md`): Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

## 3 The data

- **FIDE's lists**: OlimpBase's transcription of FIDE's official lists, July 1971 to October 2001 (checked against FIDE's own four lists of 2001 in E20 before use); FIDE's own files from January 2001 to January 2015 (fetched once, `tools/data/fetch_fide_old_lists.py`; on their first eighteen requests the tool logged each request's time before its wait, so that about every other request went out one second after the one before, against the brief's two: recorded in E20 and fixed) and from February 2015 to October 2026 (on disk since session ELO-1); FIDE's printed top-100 lists of July 2000 to December 2019 as the Internet Archive keeps them (`tools/data/fetch_probe.py`, one request at least eight seconds after the last to that host).
- **FIDE's per-player calculations** (§6), fetched once each, politely (`tools/data/fetch_probe.py`).
- **The rules in force** (§6): FIDE's handbook online from 1 July 2014; before it, the Internet Archive's copies of FIDE's handbook, transcribed with their URLs and snapshot times in a new verification record before the replay runs.
- Nothing from TWIC, ChessBase, Chessmetrics or any source the probe marked "needs permission" or "unusable". FIDE's lists and OlimpBase's are analysed and never committed: E20 commits aggregates, differences and the few published ratings named in §4 only.

## 4 (i) FIDE's published series, for every player

For each player, FIDE's published rating at every list date on which the player appears, July 1971 to October 2026 (OlimpBase's transcription to 2000, FIDE's files from 2001), and the rank of §2's rule on the lists from July 1971 to December 2019. Committed per player: the first and last list on which the player appears and their number; the peak published rating and the list dates it was reached; the lists ranked 1st, 1st to 3rd and 1st to 10th. Each player's full series stays in the local cache under `data/` (gitignored), as R72 orders for FIDE's published ratings.

## 5 (ii) Dominance, wherever top lists exist

On every list date from July 1971 to December 2019 the ratings of the list's #1, #2 and #10 are taken from the same source as §2's ranks (FIDE's printed top list where it survives; otherwise the full list's ranked players, the #2 and #10 being the second- and tenth-highest ratings among them).

- **The gaps.** On each list on which a player is ranked: gap to #2 = the player's rating − the list's #2 (for the list's #1, the lead over #2; for any other player zero or less); gap to #10 = the player's rating − the list's #10.
- **The best three consecutive years.** For each list date t on which the player is ranked, the window holds every list dated from t to before t + 36 months; it counts only if the player is ranked on each of its lists. The player's best window is the one with the highest mean gap to #2 over its lists (the earliest, on a tie); reported with its first and last list, its number of lists, the mean gaps to #2 and to #10, and the lists in it at #1. The best window by the mean gap to #10 is reported beside it.
- **The era caveat applies most here**: a gap measures a lead over one's own contemporaries, on lists whose frequency (one a year in the 1970s, twelve a year from 2013) and spread change with the era.

## 6 (iii) The replay under both systems, where FIDE's calculations give every game

- **Who and when.** Every player of §2 with at least one standard rating period, on the lists of April 2008 to December 2019, whose FIDE calculation gives every game (DATA-PROBE §2.4: per-game rows from the list of April 2008; tournament totals only from July 2001 to January 2008, which cannot carry a per-game table and are not replayed). The periods are read from FIDE's calculations index for each player.
- **As E17 and E19** (`docs/specs/SPEC-TOP100_v1_0.md`, `docs/specs/SPEC-SELFCAL_v1_2.md` §9, §10): the players replayed together month by month, each from the published rating of the list before the first replayed period; every standard game FIDE rated for them from FIDE's per-player calculations; opponents outside the set at the ratings FIDE's pages print (R58's approximation); opponents inside the set at their replayed ratings.
- **Layer 0** applies the rules in force at each tournament's start (K, the 350- and 400-point rules and rounding, in the versions of the period, transcribed before the replay runs) and must reproduce FIDE's published changes: each game's change, each period's change and each published rating, period by period. A period whose page is missing, or which Layer 0 cannot reproduce, is flagged "thin"; the replay carries FIDE's published change through it, as E17 does, and E20 lists every thin period.
- **Rung 2** applies the 2025 self-calibrating table (E18's first table, form E with the draw tail) to every replayed game, labelled **"applied backwards, not fitted on that era"**: η(L) whole in each band, the published entry to three decimals, the narrowed guard as frozen, no 400-point rule; colours from FIDE's colour marks (E17: 98.4 % agreement with the broadcast archive in 2020–2026; unchecked before 2020); K by FIDE's K rules in force on each system's own rating (R61).
- **Reported per player**: the difference rung 2 − Layer 0 on the last replayed list, split into the table's effect and colour's; the highest rating within the window under each system; the games replayed; the thin periods. Beside the method: the replay without colour, and with every opponent outside the set rated 10 points lower and higher (R58).

## 7 (iv) The cross-era head-to-head: not attempted

The probe found no legitimately usable game data linking the eras (DATA-PROBE §5): TWIC, ChessBase, Chessmetrics and the other game collections need permission; OlimpBase's Olympiad games credit ChessBase's database and TWIC's editor among their sources; the Lichess broadcast archive starts in 2020; FIDE's calculations give each player's own games, from 2008 only, and link no earlier era. E20 and the appendix say so; with permission (TWIC, ChessBase or Chessmetrics), the full study would become possible.

## 8 Outputs

- `analysis/greats_select.py` (needs `data/`) writes `analysis/aggregates/GREATS_players.json` (this specification's §2).
- Phase 3: an extraction (needs `data/`) writes E20's aggregate, aggregates and differences only, and a report writes docs/evidence/E20_greats.md (to be written in Phase 3); the transcription of the rules in force before July 2014, with fixtures and tests, in new code; nothing in a frozen file changes.

## 9 Fixed before the analysis

The rule and the names of §2, the definitions of §4 to §6 and the wording of §1 are fixed by this version. A later version may correct an error it finds, and says so; it does not change a definition because of a result.
