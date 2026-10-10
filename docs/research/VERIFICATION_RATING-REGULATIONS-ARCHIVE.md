# Verification sweep — the FIDE Rating Regulations in force from February 2020 to October 2026

Status: VERIFICATION RECORD (primary-source transcription). Session ELO-7, Phase 2. Author: The Zugzwang Authors. Licence: CC BY 4.0 (see `docs/LICENSE-docs.md`); quoted third-party text remains its owners' and is reproduced for verification only.

**Why.** The replay of the October 2026 top 100 from January 2020 (`docs/specs/SPEC-TOP100_v1_0.md`, Addendum 2 of the ELO-7 brief) must apply the rating rules in force at each date. Layer 0 implements the regulations effective 1 March 2024 as amended 1 October 2025, transcribed in `docs/research/VERIFICATION_2026-10-09.md` [V 1]. This record transcribes, from FIDE's handbook archive, the earlier versions that governed rating periods from February 2020, and only the passages that differ for these players: the 400-point rule, K, rating periods and rounding. Nothing below is filled from memory.

**Method.** Each page was fetched once with `tools/data/fetch_fide_handbook.py` (User-Agent "Mozilla/5.0", one request at a time, three seconds or more apart; handbook.fide.com publishes no robots.txt, HTTP 404 on 2026-10-10 at 20:34:26 UTC) and cached under `data/raw/fide_site/handbook/`, never fetched again. HTML was converted to text with a Python standard-library parser and the passages below were copied from that text by script, not retyped, and checked against it line by line (whitespace aside); the score-probability tables were read from the pages' `<table>` markup and compared by script.

| # | Item | Status | Fetched (UTC) |
|---|---|---|---|
| 1 | FIDE Rating Regulations effective from 1 July 2017 till 31 December 2021 (with amendments effective from 1 February 2021) | VERIFIED | 2026-10-10T20:53:48Z |
| 2 | FIDE Rating Regulations effective from 1 January 2022 till 29 February 2024 | VERIFIED | 2026-10-10T20:53:43Z |
| 3 | FIDE Rating Regulations effective from 1 March 2024 (as amended 1 October 2025), re-fetched for the comparison | VERIFIED | 2026-10-10T20:53:22Z |
| 4 | The regulations' text in force from 1 March 2024 to 30 September 2025 for the 400-point rule | NOT VERIFIED (the handbook shows only the amended text) | — |

---

## 1. FIDE Rating Regulations effective from 1 July 2017 till 31 December 2021 (with amendments effective from 1 February 2021) — VERIFIED

- URL: https://handbook.fide.com/chapter/B022017
- Fetched: 2026-10-10T20:53:48Z, HTTP 200, 125,794 bytes, SHA-256 5c78b7a50e1ff6feaac41f69f179cb054e18ff7df84cad8a80d645f42d392cd1.
- Page header (verbatim): "Effective from 1 July 2017 (with amendments effective from 1 February 2021)." / "Approved by the 1982 General Assembly, amended by the General Assemblies of 1984 through 2016."

> 7.1 On the first day of each month, the QC shall prepare a list which incorporates the rated play during the rating period into the previous list. This shall be done using the rating system formula.
>
> 7.11 The rating period (for new players, see 7.14) is the period where a certain rating list is valid.

> 8.54 A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points.
>
> 8.55 (a) Use table 8.1(b) to determine the player’s score probability PD
> (b) ΔR = score – PD. For each game, the score is 1, 0.5 or 0.
> (c) ΣΔR x K = the Rating Change for a given tournament, or Rating period.
>
> 8.56 K is the development coefficient.
> K = 40 for a player new to the rating list until he has completed events with at least 30 games.
> K = 20 as long as a player's rating remains under 2400.
> K = 10 once a player's published rating has reached 2400 and remains at that level subsequently, even if the rating drops below 2400.
> K = 40 for all players until their 18th birthday, as long as their rating remains under 2300.
> If the number of games (n) for a player on any list for a rating period multiplied by K (as defined above) exceeds 700, then K shall be the largest whole number such that K x n does not exceed 700.
>
> 8.57 The Rating Change is rounded to the nearest whole number. 0.5 is rounded up (whether the change is positive or negative).

## 2. FIDE Rating Regulations effective from 1 January 2022 till 29 February 2024 — VERIFIED

- URL: https://handbook.fide.com/chapter/B022022
- Fetched: 2026-10-10T20:53:43Z, HTTP 200, 133,080 bytes (the size `docs/research/VERIFICATION_TITLES.md` recorded on 2026-10-09), SHA-256 96857791b2490ffeb3cf7e7cd761dafb40938c93512db0ee3456bc5fbbc47b83.
- Page header (verbatim): "FIDE RATING REGULATIONS (Approved by FIDE Council on 27/10/2021)" / "Applied from 1 January, 2022".

> 7.1 On the first day of each month, FIDE shall prepare a list which incorporates all rated play during the rating period into the previous list. This shall be done using the rating system formula.
>
> 7.1.1 The rating period (for new players, see 7.1.4) is the period where a certain rating list is valid.

> 8.3.1 For each game played against a rated player, determine the difference in rating between the player and their opponent, D.
> A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points. In any tournament, a player may benefit from only one upgrade under this rule, for the game in which the rating difference is greatest.
>
> 8.3.2 a) Use table 8.1.2 to determine the player's score probability PD for each game.
> b) Delta R = score - PD. For each game, the score is 1, 0.5 or 0.
> c) Sigma Delta R = the sum of Delta Rs for a tournament or Rating Period.
> d) Sigma Delta R x K = the Rating Change for a tournament or Rating Period.
>
> 8.3.3 K is the development coefficient.
> K = 40 for a player new to the rating list until they have completed events with at least 30 games.
> K = 20 as long as a player's rating remains under 2400.
> K = 10 once a player's published rating has reached 2400 and remains at that level subsequently, even if the rating drops below 2400.
> K = 40 for all players until the end of the year of their 18th birthday, as long as their rating remains under 2300.
> If the number of games (n) for a player on any list for a rating period multiplied by K (as defined above) exceeds 700, then K shall be the largest whole number such that K x n does not exceed 700.
>
> 8.3.4 The Rating Change for a Rating Period is rounded to the nearest whole number. 0.5 is rounded away from zero.

## 3. FIDE Rating Regulations effective from 1 March 2024, as amended 1 October 2025 — VERIFIED (re-fetched)

- URL: https://handbook.fide.com/chapter/B022024
- Fetched: 2026-10-10T20:53:22Z, HTTP 200, 162,773 bytes (the size of [V 1], fetched 2026-10-09), SHA-256 43f8c7b0c85121b33ed0c5bc24bd8da0a62aee899bfc43d015c05c61a695b411.
- Page header (verbatim): "FIDE RATING REGULATIONS (Approved by FIDE Council on 15/12/2023)" / "Applied from 1 March, 2024".
- §7.1, §7.1.1, §8.3.2, §8.3.3 and §8.3.4 read as in item 2 above, word for word; §8.3.1 reads as [V 1] transcribes it: "Effective from 1 October 2025: A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points for players rated below 2650. For players rated 2650 and above, the difference between ratings shall be used in all cases".

## 4. The 400-point rule from 1 March 2024 to 30 September 2025 — NOT VERIFIED

The handbook's page for the regulations applied from 1 March 2024 prints §8.3.1 only as amended from 1 October 2025, and its archive lists no separate version for 1 March 2024 to 30 September 2025. The research report dates the 2650 exemption to 1 October 2025, the cap having applied to every player since 1 March 2024 [R §2]; SPEC-L0 reads it so (R-14a), NOT VERIFIED. Whether the 2022 version's one-upgrade clause still applied in those months is not shown. The replay uses the plain cap for every player there and tests the reading against FIDE's published calculations of those months (`docs/specs/SPEC-TOP100_v1_0.md` §5).

## 5. The score-probability table across the three versions

Read from the `<table>` markup of each page: table 8.1(b) of item 1 and table 8.1.2 of items 2 and 3 hold the same 50 rows, D from 0–3 (.50/.50) to 620–735 (.99/.01), with identical H and L values, so Layer 0's table (`src/layer0/tables.py`, transcribed from [V 1]) serves every version.

## 6. What differs, in one table

| Rule | to 31 December 2021 (item 1) | 1 January 2022 to 29 February 2024 (item 2) | 1 March 2024 to 30 September 2025 | from 1 October 2025 (item 3, [V 1]) |
|---|---|---|---|---|
| 400-point rule | plain cap for every player | cap; "only one upgrade" per tournament, for the game with the greatest difference | NOT VERIFIED; read as the plain cap (R-14a) | cap below 2650; actual difference from 2650 |
| K | 40 / 20 / 10; juniors to the 18th birthday; 700 rule | 40 / 20 / 10; juniors to the end of the year of the 18th birthday; 700 rule | as item 2 | as item 2 |
| Rounding | "0.5 is rounded up (whether the change is positive or negative)"; "The Rating Change" | "The Rating Change for a Rating Period"; "0.5 is rounded away from zero" | as item 2 | as item 2 |
| Rating period | monthly | monthly | monthly | monthly |
| Table 8.1(b) / 8.1.2 | identical in all versions (§5) | | | |
