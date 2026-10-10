# SPEC-TOP100 — today's top 100 replayed under Layer 0 and under rung 2, v1.0

**Status: REVIEW — written before the replay is run (ELO-7 brief, Phase 2, with the operator's Addendum 2 of 2026-10-10).** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10. The data were collected before this specification was written, under the definitions of the brief and the addendum (the players, the window and the sources below); no replay, rating, comparison or statistic was computed from them before it was committed. Every parameter of rung 2 is PROVISIONAL-FITTED (the table) or fixed by ruling (the guard), and every figure the replay produces describes the rules, not the players.

## 1 The question

With the same games and the same results, what would the players at the top of FIDE's October 2026 standard list be rated today if, from January 2020, every game had been rated by rung 2 of the adoption ladder, the table calibrated by level with the narrowed guard at today's K (R44), instead of by FIDE's rules? Every table that answers it carries the fixed wording "under this rule, with the same results — not anyone's true strength".

## 2 The players

The top 100 active players of FIDE's October 2026 standard list [V 3]: the players without an inactivity flag (`i` or `wi`) on that list, ranked by rating, ties at rank 100 broken by FIDE ID. On the October 2026 list rank 100 is rated 2626 and rank 101 2624, so no tie arises. The report also states how many of the 100 meet E5's reading of "active" (at least one rated game on the twelve lists up to October 2026) [E5]. Players are identified by FIDE ID; names are used only inside `data/` to identify opponents (§4) and never enter a committed file.

## 3 The window

- **Start.** Each player's rating on FIDE's January 2020 standard list. All 100 are on it. A player whose January 2020 rating did not exist would start from the first list that rates them, and the report would say so.
- **Games.** Every standard game FIDE rated for the player from the February 2020 list to the October 2026 list (81 lists), read from FIDE's published per-player calculations (§4). The calculations reach back to February 2020 (the first page fetched, the February 2020 list's calculation of the player ranked first, shows the event of January 2020). A list on which the player's games field is zero has no calculation to read; a published rating change on such a list is reported as a mismatch (§5.3).
- **Nothing from the November 2026 rating period is read**: no list after October 2026 and no calculation of the November 2026 period, so no game of the 2026 U.S. Championships, which that period rates.

## 4 Sources and collection

1. **FIDE's monthly standard lists**, January 2020 to October 2026, already downloaded (`tools/data/fetch_fide_lists.py`, `data/raw/fide/`): rating, games, K, flag, federation, and, in the raw files, names. Analysed, never redistributed [V 3].
2. **FIDE's per-player calculations** (`https://ratings.fide.com/calculations.phtml`, data from `/a_indv_calculation.php`), one page per player and list on which the player has rated games: 3,685 pages, fetched by `tools/data/fetch_top100_calculations.py` under the brief's rules (ratings.fide.com publishes no robots.txt, HTTP 404 on 2026-10-10; one request at a time, three seconds apart; every page cached once under `data/raw/fide_calculations/` and never fetched again; a refusal stops the run and is recorded). Per tournament: the event, its place and dates, Rc, Ro, w, n, chg, K and K × chg; per game: the colour mark, the opponent's name, title and federation, the opponent's rating as FIDE used it (an asterisk marks the 400-point rule), the score, chg, K and K × chg; per page, the total change. Analysed, never redistributed; committed files carry aggregates and the per-player figures of §7 only.
3. **FIDE's handbook**, for the rules in force at each date (§5.1): the Rating Regulations effective from 1 July 2017 till 31 December 2021 (with amendments effective from 1 February 2021), from 1 January 2022 till 29 February 2024, and from 1 March 2024 (as amended 1 October 2025), fetched once each by `tools/data/fetch_fide_handbook.py` and transcribed in `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`.
4. **The Lichess broadcast archive**, January 2020 to September 2026 (`tools/data/fetch_lichess_broadcasts.py`, each month checked against the published SHA-256), for colours (§6.3). CC BY-SA 4.0, attributed; aggregates only [V 4].

**Opponents** are identified by FIDE ID from the name and federation the calculation prints (names normalised: accents, case and punctuation removed), against the names of every list of the window; the rating FIDE used, on the list the tournament used, breaks a tie, and an opponent among the 100 may also be matched on the name alone (a change of federation). The share identified is reported; an opponent who cannot be identified keeps the rating FIDE used and has no colour match.

## 5 Layer 0 with the rules in force at each date

### 5.1 The rules that changed between February 2020 and October 2026

Transcribed from the handbook (§4.3); none is filled from memory. New code beside the engine, src/layer0_history/ (written after this specification), applies them; `src/layer0/` (Freeze 1) is unchanged and supplies table 8.1.2 and everything that did not change.

- **The score-probability table** (8.1(b) in 2017, 8.1.2 since 2022): identical in the three versions, row for row, as a script verifies from the pages' table markup.
- **The 400-point rule**: (i) to 31 December 2021, "A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points"; (ii) from 1 January 2022 to 29 February 2024, the same with "In any tournament, a player may benefit from only one upgrade under this rule, for the game in which the rating difference is greatest", read as: a favourite keeps the cap only in its game of greatest difference (the first if several tie), while an underdog's games are all capped, since the cap raises its PD; FIDE's asterisks test the reading; (iii) from 1 October 2025, the cap for players rated below 2650 and the actual difference for players rated 2650 and above. For 1 March 2024 to 30 September 2025 the handbook shows only the amended text; Layer 0 reads the plain cap for every player (SPEC-L0 R-14a), NOT VERIFIED, and FIDE's published calculations of those months test the reading (§5.3).
- **K**: the same three values and the 700 rule in every version, except the junior line (to the 18th birthday until 2021, to the end of the year of the 18th birthday since 2022). The replay takes K from FIDE's published calculation of each tournament and checks it against the list's K under the 700 rule (SPEC-L0 R-22b).
- **Rounding**: to 31 December 2021, "The Rating Change is rounded to the nearest whole number. 0.5 is rounded up (whether the change is positive or negative)"; since 1 January 2022, "The Rating Change for a Rating Period is rounded to the nearest whole number. 0.5 is rounded away from zero".
- **Rating periods**: monthly in every version ("On the first day of each month ... the rating period ... is the period where a certain rating list is valid").

**Which version applies.** A version's rules apply to the tournaments that start on or after its effective date (the reading Layer 0 uses for the 1 October 2025 amendment, SPEC-L0 R-14a), and its rounding to the lists published on or after that date; both readings are tested against FIDE's calculations and lists, and any game or list they fail is reported.

### 5.2 The replay under Layer 0

For each player and each list from February 2020 to October 2026: each game's ΔR = score − PD from table 8.1.2 at the difference the rule in force gives, with the player's own rating Ro as FIDE used it and the opponent's actual rating (the rating FIDE used, or, where FIDE printed a capped one, the opponent's rating on the list the tournament used); each tournament's K × ΣΔR with FIDE's K; the period's change rounded once, by the rounding of the list that rates it (rounding per tournament computed beside it and reported where only it matches the list); and two ratings: the previous published rating plus the period's change, checked against the list, and the replay carried from January 2020.

### 5.3 Validation first

Before any rung-2 figure is computed, the report prints:

1. games whose ΔR differs from FIDE's chg, and why (the 400-point rule's version, the one-upgrade clause, an unidentified edge);
2. tournaments whose K × ΣΔR differs from FIDE's;
3. every list on which the replayed rating, carried from January 2020, differs from the published rating, for every player, with its cause where one is found (a base correction of Ro, a tournament rated late or re-rated, a rounding version, a change on a list with no games), and unexplained otherwise.

A mismatch is a finding about Layer 0's reading of the historical rules or about FIDE's data, never a reason to edit the published ratings, which stay the reference.

## 6 Rung 2 replayed

### 6.1 The rule

Rung 2 as recommended (R44, R45): the v2 table of Freeze 3 (`params/table_fit_2026-10b.yaml`, standard; [E11]), its published entry at the game's level band and the effective gap, with the narrowed guard (`params/guard_2026-10b.yaml`, `src/layer2/guard_v2.py`; [E12]) and no 400-point rule; K and rounding are Layer 0's at every date, so that only the expectation differs (Addendum 2). The table was fitted on broadcast games of October 2023 to September 2026: the replay's games from October 2023 are in sample and those of 2020 to September 2023 out of sample, stated with every result.

### 6.2 Ratings

The 100 are replayed together, month by month, from their January 2020 ratings. A player's rung-2 difference on a list is the rung-2 replay minus the Layer 0 replay on that list, both carried from January 2020 with the same K and rounding. In each game the player's own rating is Ro, as FIDE used it, plus the player's rung-2 difference on the list the tournament used (the list in force at its start, at most the list before the one that rates it); the opponent's is the opponent's actual rating plus the opponent's rung-2 difference if the opponent is one of the 100, and the actual rating otherwise; the level, the gap and the guard's region come from these two. **Approximation, stated:** opponents outside the 100 keep their published ratings, although under rung 2 theirs would differ too.

### 6.3 Colours

A game's colour comes from the Lichess broadcast archive, games that E2's classifier calls standard or cannot classify: a FIDE game matches a broadcast game when the broadcast's two players are the player and the opponent (by FIDE ID, or by normalised name where the broadcast carries no ID), its date lies within the tournament's dates (one day's tolerance at each end), and its result is FIDE's score from the player's side; the match must be unique, every candidate on one day and of one colour (duplicate broadcasts of one game), or the game is unmatched. The colour term is η = 36 points, added for White and subtracted for Black; an unmatched game carries none and is flagged. Coverage is reported by year. FIDE's calculation also prints a colour mark for each game: its agreement with the broadcast colours on matched games is reported, and a replay using FIDE's marks for every game is shown beside, labelled a sensitivity, not the method.

### 6.4 The table's effect and colour's effect

Three replays on the same games: Layer 0; rung 2 with no colour term in any game; rung 2 with the colour term where the colour is matched. A player's difference (rung 2 − Layer 0) splits into the table's effect (colourless rung 2 − Layer 0) and colour's effect (rung 2 − colourless rung 2), at every list. The difference is measured against Layer 0's replay, not the published list, so that a correction FIDE made outside the games (a mismatch of §5.3) is not counted as the rule's; the rung-2 rating reported is the published rating plus the difference.

## 7 Outputs: docs/evidence/E17_top100-replay.md

Generated by analysis/e17_top100_report.py from analysis/aggregates/E17_top100.json, which analysis/e17_top100_extract.py writes from `data/` (registered with check (a) as needing data):

- the validation of §5.3, first;
- per player: the October 2026 rating, the replayed rating under rung 2, the difference, the games, the share of games as the favourite, the mean gap, the colour balance (Whites minus Blacks among matched games), and the difference split into the table's and colour's effects;
- the largest risers and fallers; rank changes within the 100;
- on every list from February 2020 to October 2026, how many of the 100 are rated 2700 or more and 2800 or more under each system;
- the cumulative difference over time, by player at each December list and October 2026, and on average at every list; each calendar year's change, from the December list before (January 2020 for 2020) to the December list (October 2026 for 2026), split into the table's and colour's effects;
- colour coverage by year, FIDE's colour marks beside, and the sensitivity of §6.3.

Every table carries the fixed wording. The report states that the 100 are chosen at the end of the window, so earlier lists count only these players, not the top of those lists; that the replay is in sample from October 2023; and that opponents outside the 100 keep their published ratings.

## 8 What is published and what is not

Committed: aggregates, and per player only the figures of §7 for the 100 (identified by FIDE ID). Not committed: FIDE's pages, lists or per-player monthly series, broadcast games, names. A monthly series of both systems' ratings for each player, for the operator's video (the operator's Addendum 1, not received in this session), is written to the operator's `~/Downloads` only.
