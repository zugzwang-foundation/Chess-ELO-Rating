# Verification sweep — 2026-10-09

Status: VERIFICATION RECORD (primary-source transcription). Session ELO-1, Phase 1. Author: The Zugzwang Authors. Licence: CC BY 4.0 (see `docs/LICENSE-docs.md`); quoted third-party text remains its owners' and is reproduced for verification only.

**Method.** Each URL was fetched with `curl` (User-Agent "Mozilla/5.0") from the operator's machine at the UTC time shown. HTML was converted to text with a Python standard-library parser; tables were read directly from the `<table>` markup and rendered to Markdown by script, not retyped. Every item is marked VERIFIED (URL, UTC timestamp, extracted text) or NOT VERIFIED. Nothing below was filled from memory.

| # | Item | Status | Fetched (UTC) |
|---|---|---|---|
| 1 | FIDE Rating Regulations effective 1 March 2024 (§7, §8 in full) | VERIFIED | 2026-10-09T14:28:34Z |
| 2 | FIDE Rapid and Blitz Rating Regulations effective 1 March 2024 (differences only) | VERIFIED | 2026-10-09T14:28:38Z |
| 3 | ratings.fide.com/download_lists.phtml (files, formats, fields, terms) | VERIFIED | 2026-10-09T14:28:44Z |
| 4 | database.lichess.org (licence verbatim; monthly sizes 2024–2026) | VERIFIED | 2026-10-09T14:28:53Z |
| 5 | Licences of Remi-Coulom/WHR, goshrine/whole_history_rating, wind23/whole_history_rating, lichess-org/lila | VERIFIED | 2026-10-09T14:28:56Z |
| + | ratings.fide.com/calc.phtml?page=change reachable (for the Layer-0 test-vector plan) | VERIFIED (HTTP 200 only; content not transcribed) | 2026-10-09T14:30:34Z |

---

## 1. FIDE Rating Regulations effective from 1 March 2024 — VERIFIED

- URL: https://handbook.fide.com/chapter/B022024
- Fetched: 2026-10-09T14:28:34Z, HTTP 200, 162,773 bytes, server-rendered HTML (rules text inline).
- Page title: "FIDE Handbook FIDE Rating Regulations effective from 1 March 2024".
- Page header (verbatim): "FIDE RATING REGULATIONS (Approved by FIDE Council on 15/12/2023)" / "Applied from 1 March, 2024".
- Handbook sidebar lists the archived versions: "effective from 1 January 2022 till 29 February 2024", "effective from 1 July 2017 till 31 December 2021 (with amendments effective from 1 February 2021)", "effective from 1 July 2014 till 30 June 2017".

### §1 Rate of Play (transcribed because Layer 0 needs it to classify a game as standard)

> 1. Rate of Play
> 1.1 For a game to be rated each player must at the start of the game have the following minimum periods in which to complete all the moves, assuming the game lasts 60 moves.
> Where at least one of the players in the game has a rating of 2400 or higher, each player must have a minimum of 120 minutes.
> Where at least one of the players in the game has a rating 1800 or higher, each player must have a minimum of 90 minutes.
> Where both of the players in the game are rated below 1800, each player must have a minimum of 60 minutes.
> 1.2 Where a certain number of moves is specified in the first time control, it shall be at least 30 moves.

### §5 and §6 (short, needed by Layer 0)

> 5. Unplayed Games
> 5.1 Whether these occur because of forfeiture or any other reason, they are not counted. Except in case of force majeure, any game where both players have made at least one move will be rated, unless the regulations relating to Fair Play require otherwise.
> 6. Matches
> 6.1 Matches in which one player is unrated shall not be rated.
> 6.2 Where a match is over a specific number of games, those played after one player has won shall not be rated. This requirement may be waived by prior request.

### §7 Official FIDE Rating List (in full)

> 7. Official FIDE Rating List
> 7.1 On the first day of each month, FIDE shall prepare a list which incorporates all rated play during the rating period into the previous list. This shall be done using the rating system formula.
> 7.1.1 The rating period (for new players, see 7.1.4) is the period where a certain rating list is valid.
> 7.1.2 The following data will be published concerning each player whose rating is at least 1400 as of the current list: FIDE title, Federation, Current Rating, ID Number, Number of games rated in the rating period, Year of Birth, Gender and the current value of K for the player.
> 7.1.3 The closing date for tournaments for a list is 3 days before the date of the list; tournaments ending before or on that day may be rated on the list. Official FIDE events may be rated on the list even if they end on the last day before the list date.
> 7.1.4 A rating for a player new to the list shall be published when it is based on at least 5 games against rated opponents. This need not be met in one tournament. Results from other tournaments played within consecutive rating periods of not more than 26 months are pooled to obtain the initial rating. The rating must be at least 1400.
> 7.2 Players who are not to be included on the list or to be shown as inactive:
> 7.2.1 Players whose ratings drop below 1400 are shown as unrated on the next list. Thereafter they are treated in the same manner as any other unrated player.
> 7.2.2 Players listed as active:
> A player is considered to commence inactivity if they play no rated games in a one-year period.
> A player regains their activity if they play at least one rated game in a period. They are then listed as active on the next list.

### §8 The working of the FIDE Rating System (in full)

> 8. The working of the FIDE Rating System
> The FIDE Rating system is a numerical system in which fractional scores are converted to rating differences and vice versa. Its function is to produce measurement information of the best statistical quality.
> 8.1 The rating scale is an arbitrary one with a class interval set at 200 points. The tables that follow show the conversion of fractional score 'p' into rating difference 'dp'. For a zero or 1.0 score dp is necessarily indeterminate but is shown notionally as 800. The second table shows conversion of difference in rating 'D' into scoring probability 'PD' for the higher 'H' and the lower 'L' rated player respectively. Thus, the two tables are effectively mirror-images.
> 8.1.1 The table of conversion from fractional score, p, into rating differences, dp

**Table 8.1.1 (verbatim layout, 6 column-pairs as on the page):**

| p | dp | p | dp | p | dp | p | dp | p | dp | p | dp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 800 | .83 | 273 | .66 | 117 | .49 | -7 | .32 | -133 | .15 | -296 |
| .99 | 677 | .82 | 262 | .65 | 110 | .48 | -14 | .31 | -141 | .14 | -309 |
| .98 | 589 | .81 | 251 | .64 | 102 | .47 | -21 | .30 | -149 | .13 | -322 |
| .97 | 538 | .80 | 240 | .63 | 95 | .46 | -29 | .29 | -158 | .12 | -336 |
| .96 | 501 | .79 | 230 | .62 | 87 | .45 | -36 | .28 | -166 | .11 | -351 |
| .95 | 470 | .78 | 220 | .61 | 80 | .44 | -43 | .27 | -175 | .10 | -366 |
| .94 | 444 | .77 | 211 | .60 | 72 | .43 | -50 | .26 | -184 | .09 | -383 |
| .93 | 422 | .76 | 202 | .59 | 65 | .42 | -57 | .25 | -193 | .08 | -401 |
| .92 | 401 | .75 | 193 | .58 | 57 | .41 | -65 | .24 | -202 | .07 | -422 |
| .91 | 383 | .74 | 184 | .57 | 50 | .40 | -72 | .23 | -211 | .06 | -444 |
| .90 | 366 | .73 | 175 | .56 | 43 | .39 | -80 | .22 | -220 | .05 | -470 |
| .89 | 351 | .72 | 166 | .55 | 36 | .38 | -87 | .21 | -230 | .04 | -501 |
| .88 | 336 | .71 | 158 | .54 | 29 | .37 | -95 | .20 | -240 | .03 | -538 |
| .87 | 322 | .70 | 149 | .53 | 21 | .36 | -102 | .19 | -251 | .02 | -589 |
| .86 | 309 | .69 | 141 | .52 | 14 | .35 | -110 | .18 | -262 | .01 | -677 |
| .85 | 296 | .68 | 133 | .51 | 7 | .34 | -117 | .17 | -273 | .00 | -800 |
| .84 | 284 | .67 | 125 | .50 | 0 | .33 | -125 | .16 | -284 |  |  |


> 8.1.2 Table of conversion of difference in rating, D, into scoring probability PD, for the higher, H, and the lower, L, rated player respectively.

**Table 8.1.2 (verbatim layout, 4 column-groups as on the page):**

| D (Rtg Dif) | PD H | PD L | D (Rtg Dif) | PD H | PD L | D (Rtg Dif) | PD H | PD L | D (Rtg Dif) | PD H | PD L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-3 | .50 | .50 | 92-98 | .63 | .37 | 198-206 | .76 | .24 | 345-357 | .89 | .11 |
| 4-10 | .51 | .49 | 99-106 | .64 | .36 | 207-215 | .77 | .23 | 358-374 | .90 | .10 |
| 11-17 | .52 | .48 | 107-113 | .65 | .35 | 216-225 | .78 | .22 | 375-391 | .91 | .09 |
| 18-25 | .53 | .47 | 114-121 | .66 | .34 | 226-235 | .79 | .21 | 392-411 | .92 | .08 |
| 26-32 | .54 | .46 | 122-129 | .67 | .33 | 236-245 | .80 | .20 | 412-432 | .93 | .07 |
| 33-39 | .55 | .45 | 130-137 | .68 | .32 | 246-256 | .81 | .19 | 433-456 | .94 | .06 |
| 40-46 | .56 | .44 | 138-145 | .69 | .31 | 257-267 | .82 | .18 | 457-484 | .95 | .05 |
| 47-53 | .57 | .43 | 146-153 | .70 | .30 | 268-278 | .83 | .17 | 485-517 | .96 | .04 |
| 54-61 | .58 | .42 | 154-162 | .71 | .29 | 279-290 | .84 | .16 | 518-559 | .97 | .03 |
| 62-68 | .59 | .41 | 163-170 | .72 | .28 | 291-302 | .85 | .15 | 560-619 | .98 | .02 |
| 69-76 | .60 | .40 | 171-179 | .73 | .27 | 303-315 | .86 | .14 | 620-735 | .99 | .01 |
| 77-83 | .61 | .39 | 180-188 | .74 | .26 | 316-328 | .87 | .13 | > 735 | 1.0 | .00 |
| 84-91 | .62 | .38 | 189-197 | .75 | .25 | 329-344 | .88 | .12 |  |  |  |

**Derived from the transcription above (same data, re-arranged one entry per line for implementation and test vectors):**

Table 8.1.1 flattened, p → dp:

| p | dp |
|---|---|
| 1.0 | 800 |
| .99 | 677 |
| .98 | 589 |
| .97 | 538 |
| .96 | 501 |
| .95 | 470 |
| .94 | 444 |
| .93 | 422 |
| .92 | 401 |
| .91 | 383 |
| .90 | 366 |
| .89 | 351 |
| .88 | 336 |
| .87 | 322 |
| .86 | 309 |
| .85 | 296 |
| .84 | 284 |
| .83 | 273 |
| .82 | 262 |
| .81 | 251 |
| .80 | 240 |
| .79 | 230 |
| .78 | 220 |
| .77 | 211 |
| .76 | 202 |
| .75 | 193 |
| .74 | 184 |
| .73 | 175 |
| .72 | 166 |
| .71 | 158 |
| .70 | 149 |
| .69 | 141 |
| .68 | 133 |
| .67 | 125 |
| .66 | 117 |
| .65 | 110 |
| .64 | 102 |
| .63 | 95 |
| .62 | 87 |
| .61 | 80 |
| .60 | 72 |
| .59 | 65 |
| .58 | 57 |
| .57 | 50 |
| .56 | 43 |
| .55 | 36 |
| .54 | 29 |
| .53 | 21 |
| .52 | 14 |
| .51 | 7 |
| .50 | 0 |
| .49 | -7 |
| .48 | -14 |
| .47 | -21 |
| .46 | -29 |
| .45 | -36 |
| .44 | -43 |
| .43 | -50 |
| .42 | -57 |
| .41 | -65 |
| .40 | -72 |
| .39 | -80 |
| .38 | -87 |
| .37 | -95 |
| .36 | -102 |
| .35 | -110 |
| .34 | -117 |
| .33 | -125 |
| .32 | -133 |
| .31 | -141 |
| .30 | -149 |
| .29 | -158 |
| .28 | -166 |
| .27 | -175 |
| .26 | -184 |
| .25 | -193 |
| .24 | -202 |
| .23 | -211 |
| .22 | -220 |
| .21 | -230 |
| .20 | -240 |
| .19 | -251 |
| .18 | -262 |
| .17 | -273 |
| .16 | -284 |
| .15 | -296 |
| .14 | -309 |
| .13 | -322 |
| .12 | -336 |
| .11 | -351 |
| .10 | -366 |
| .09 | -383 |
| .08 | -401 |
| .07 | -422 |
| .06 | -444 |
| .05 | -470 |
| .04 | -501 |
| .03 | -538 |
| .02 | -589 |
| .01 | -677 |
| .00 | -800 |

(entries: 101)

Table 8.1.2 flattened, D → PD(H), PD(L):

| D | H | L |
|---|---|---|
| 0-3 | .50 | .50 |
| 4-10 | .51 | .49 |
| 11-17 | .52 | .48 |
| 18-25 | .53 | .47 |
| 26-32 | .54 | .46 |
| 33-39 | .55 | .45 |
| 40-46 | .56 | .44 |
| 47-53 | .57 | .43 |
| 54-61 | .58 | .42 |
| 62-68 | .59 | .41 |
| 69-76 | .60 | .40 |
| 77-83 | .61 | .39 |
| 84-91 | .62 | .38 |
| 92-98 | .63 | .37 |
| 99-106 | .64 | .36 |
| 107-113 | .65 | .35 |
| 114-121 | .66 | .34 |
| 122-129 | .67 | .33 |
| 130-137 | .68 | .32 |
| 138-145 | .69 | .31 |
| 146-153 | .70 | .30 |
| 154-162 | .71 | .29 |
| 163-170 | .72 | .28 |
| 171-179 | .73 | .27 |
| 180-188 | .74 | .26 |
| 189-197 | .75 | .25 |
| 198-206 | .76 | .24 |
| 207-215 | .77 | .23 |
| 216-225 | .78 | .22 |
| 226-235 | .79 | .21 |
| 236-245 | .80 | .20 |
| 246-256 | .81 | .19 |
| 257-267 | .82 | .18 |
| 268-278 | .83 | .17 |
| 279-290 | .84 | .16 |
| 291-302 | .85 | .15 |
| 303-315 | .86 | .14 |
| 316-328 | .87 | .13 |
| 329-344 | .88 | .12 |
| 345-357 | .89 | .11 |
| 358-374 | .90 | .10 |
| 375-391 | .91 | .09 |
| 392-411 | .92 | .08 |
| 412-432 | .93 | .07 |
| 433-456 | .94 | .06 |
| 457-484 | .95 | .05 |
| 485-517 | .96 | .04 |
| 518-559 | .97 | .03 |
| 560-619 | .98 | .02 |
| 620-735 | .99 | .01 |
| > 735 | 1.0 | .00 |

(entries: 51)

> 8.2 Determining the initial rating 'Ru' of a player.
> 8.2.1 If an unrated player scores zero in their first event this score is disregarded. Otherwise, their rating is calculated using all their results as in 7.1.4.
> 8.2.2 Ra is the average rating of the player's rated opponents plus two hypothetical opponents rated 1800. The result against these two hypothetical opponents is considered as a draw.
> 8.2.3 Ru = Ra + dp
> Ru is rounded to the nearest whole number.
> The maximum initial rating is 2200.
> 8.2.4 If an unrated player receives a published rating before a particular tournament in which they have played is rated, then they are rated as a rated player with their current rating, but in the rating of their opponents they are counted as an unrated player.
> 8.3 Determining the rating change for a rated player
> 8.3.1 For each game played against a rated player, determine the difference in rating between the player and their opponent, D.
> Effective from 1 October 2025: A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points for players rated below 2650. For players rated 2650 and above, the difference between ratings shall be used in all cases
> 8.3.2 a) Use table 8.1.2 to determine the player's score probability PD for each game.
> b) Delta R = score - PD. For each game, the score is 1, 0.5 or 0.
> c) Sigma Delta R = the sum of Delta Rs for a tournament or Rating Period.
> d) Sigma Delta R x K = the Rating Change for a tournament or Rating Period.
> 8.3.3 K is the development coefficient.
> K = 40 for a player new to the rating list until they have completed events with at least 30 games.
> K = 20 as long as a player's rating remains under 2400.
> K = 10 once a player's published rating has reached 2400 and remains at that level subsequently, even if the rating drops below 2400.
> K = 40 for all players until the end of the year of their 18th birthday, as long as their rating remains under 2300.
> If the number of games (n) for a player on any list for a rating period multiplied by K (as defined above) exceeds 700, then K shall be the largest whole number such that K x n does not exceed 700.
> 8.3.4 The Rating Change for a Rating Period is rounded to the nearest whole number. 0.5 is rounded away from zero.

Notes on the text as published: the sentence in 8.3.1 ends without a full stop on the page; the page writes "Delta", "Sigma" and "x" in words/letters, not as symbols. The 1 October 2025 amendment is embedded in §8.3.1 with the words "Effective from 1 October 2025:" and is the only "Effective from" note inside the chapter body.

### §9.1 Reporting Procedures (TRF, needed by Layer 0 inputs)

> 9.1 The Chief Arbiter of a FIDE registered tournament must provide the tournament report (TRF file) to the Rating Officer of the federation where the tournament took place.
> Once satisfied that the tournament was conducted in accordance with all relevant FIDE Regulations, the Rating Officer shall be responsible for uploading the TRF file to the FIDE Rating Server. This should be done in time for the tournament to be rated in the monthly list in which the tournament is registered or, if there are five days or less from the last day of the tournament to the end of the month, for the following list.
> If the tournament report is not submitted in time to be included in the third rating list after it ends, the tournament will not be rated.

---

## 2. FIDE Rapid and Blitz Rating Regulations effective from 1 March 2024 — VERIFIED (differences from standard only)

- URL: https://handbook.fide.com/chapter/B02RBRegulations2024
- Fetched: 2026-10-09T14:28:38Z, HTTP 200, 159,031 bytes.
- Page header (verbatim): "FIDE RAPID AND BLITZ RATING REGULATIONS (Approved by FIDE Council on 15/12/2023)" / "Applied from 1 March, 2024".
- Method: both chapters converted to text, section numbers stripped, `diff` run. Tables 7.1.1 and 7.1.2 of the rapid/blitz chapter were parsed and compared with 8.1.1 and 8.1.2 above: **byte-for-byte identical**.
- Section numbering is shifted by one from §6 onward (standard §7 = rapid/blitz §6; standard §8 = rapid/blitz §7; standard §9 = rapid/blitz §8; standard §10 = rapid/blitz §9).

Differences in content (everything else is word-for-word the same as the standard chapter):

| Topic | Standard chapter | Rapid and Blitz chapter (verbatim) |
|---|---|---|
| Registration (§0.2) | Two notice periods (30 days if a player is over 2700 / female over 2500; otherwise 3 days); exceptions by President / QC Chairman | "The tournament and its playing schedule must be registered three days before the tournament starts. The QC Chairperson may refuse to register a tournament. He/she may also allow a tournament to be rated even though it has been registered less than three days before the tournament starts." |
| Rate of play (§1.1) | Minimum 120/90/60 minutes by rating band; first time control at least 30 moves | "1.1.1 for a rapid game all the moves must be made in a fixed time of more than 10 minutes but less than 60 minutes for each player; or the time allotted + 60 times any increment must be more than 10 minutes but less than 60 minutes for each player;" / "1.1.2 for a blitz game all the moves must be made in a fixed time of more than 3 minutes but not more than 10 minutes for each player; or the time allotted + 60 times any increment must be more than 3 minutes but not more than 10 minutes for each player." / "1.2 Games where the players have different playing times are not rated." |
| Hours of play / reporting frequency (standard §3, §4) | Max 12 hours play per day; interim monthly reports for events over 30 days | Replaced by "3. Number of Rounds per Day / 3.1 The maximum number of rounds per day are: / 3.1.1 For Rapid games, 15 rounds per day / 3.1.2 For Blitz games, 30 rounds per day" |
| List heading (§7 vs §6) | "Official FIDE Rating List" | "Official FIDE Rapid and Blitz Rating Lists" |
| §7.2 vs §6.2 heading | "Players who are not to be included on the list or to be shown as inactive:" | "Players who are not to be included on the list:" (the inactivity rules 6.2.2 themselves are identical) |
| Initial rating, extra rule (§7.2.1 in rapid/blitz) | no equivalent | "7.2.1 If an unrated player has a standard rating at the beginning of a rapid or blitz tournament, their standard rating is used for rating calculation. Such a player is considered to be rated, and 7.2.2 to 7.2.5 below do not apply." (the remaining initial-rating rules are renumbered 7.2.2–7.2.5 and are otherwise identical, including the two hypothetical 1800 draws and the 2200 maximum) |
| 400-point rule (§8.3.1 vs §7.3.1) | 1 Oct 2025 wording with the 2650+ exemption (see §8.3.1 above) | "A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points." — **no 2650 exemption in the rapid/blitz chapter as published** — followed by: "Effective from 1 December 2024: Games played between players with a rating difference of 600 points or more shall not be rated if at least one of the players is rated above 2600 on the relevant list." |
| K rules (§8.3.3 vs §7.3.3) and rounding (§8.3.4 vs §7.3.4) | — | identical text (40 until 30 games; 20 under 2400; 10 once 2400 reached; 40 for juniors under 2300 until the end of the year of their 18th birthday; K×n ≤ 700; 0.5 rounded away from zero) |

Implication for Layer 0: the rapid and blitz engines share the standard tables, K rules and rounding, but need (a) their own time-control classifier, (b) the standard-rating seed rule for unrated players, (c) the plain 400-point cap without the 2650 exemption, and (d) the 600-point/2600 "not rated" exclusion from 1 December 2024.

---

## 3. ratings.fide.com/download_lists.phtml — VERIFIED

- URL: https://ratings.fide.com/download_lists.phtml
- Fetched: 2026-10-09T14:28:44Z, HTTP 200, 55,670 bytes.
- Page heading: "Download October 2026 FRL".

Files offered (name, format, date and size exactly as listed):

| Group | Link text | File | Date | Size |
|---|---|---|---|---|
| Combined list STD, BLZ, RPD | TXT format | https://ratings.fide.com/download/players_list.zip | 08 Oct 2026 | 42.61 MB |
| Combined list STD, BLZ, RPD | XML format | https://ratings.fide.com/download/players_list_xml.zip | 08 Oct 2026 | 48.22 MB |
| LEGACY format (not rated included) STD, RPD, BLZ combined | TXT format | https://ratings.fide.com/download/players_list_legacy.zip | 08 Oct 2026 | 42.43 MB |
| LEGACY format (not rated included) | XML format | https://ratings.fide.com/download/players_list_xml_legacy.zip | 08 Oct 2026 | 47.63 MB |
| STANDARD | TXT format | https://ratings.fide.com/download/standard_rating_list.zip | 08 Oct 2026 | 12.67 MB |
| STANDARD | XML format | https://ratings.fide.com/download/standard_rating_list_xml.zip | 08 Oct 2026 | 13.66 MB |
| RAPID | TXT format | https://ratings.fide.com/download/rapid_rating_list.zip | 08 Oct 2026 | 10.72 MB |
| RAPID | XML format | https://ratings.fide.com/download/rapid_rating_list_xml.zip | 08 Oct 2026 | 11.54 MB |
| BLITZ | TXT format | https://ratings.fide.com/download/blitz_rating_list.zip | 08 Oct 2026 | 7.25 MB |
| BLITZ | XML format | https://ratings.fide.com/download/blitz_rating_list_xml.zip | 08 Oct 2026 | 7.80 MB |

Archive: a "Select Archive Period" selector lists every month from February 2015 to October 2026.

Fields (the page's "Legend", verbatim):

> STD/SRTNG - Standard rating
> RPD/RRTNG - Rapid rating
> BLZ/BRTNG - Blitz rating
> SGM - number of STANDARD rated games in given period
> RGM - number of RAPID rated games in given period
> BGM - number of BLITZ rating games in given period
> SK - STANDARD rating K factor
> RK - RAPID rating K factor
> BK - BLITZ rating K factor
> B-day/BORN - year of birth of a player
> ID NUMBER - identification number of a player within FIDE database
> NAME - name of a player
> TIT/TITL - title of a player (g - Grand Master, wg - Woman Grand Master, m - Interntional Master, wm - Woman International Master, f - FIDE Master, wf - Woman FIDE Master, c - Candidate Master, wc - Woman Candidate Master)
> FED - Federation of a player
> OTIT - Other titles of a player which may include (IA - International Arbiter, FA - FIDE Arbiter, NA - National Arbiter, IO - International Organizer, FT - FIDE Trainer, FST - FIDE Senior Trainer, DI - Developmental Instructor, NI - National Instructor)
> FLAG - flag of inactivity (I - inactive, WI - woman inactive, w - woman)
> SEX - sex of a player (M - male, F - female)

Licence or terms for the data: **no data-specific licence or terms text found on the page.** The only rights statement is the site-wide footer, verbatim:

> © 2026 FIDE International Chess Federation. All Rights Reserved. No part of this site may be reproduced, stored in a retrieval system or transmitted in any way or by any means (including photocopying, recording or storing it in any medium by electronic means), without the written permission of FIDE International Chess Federation.

(There is also a "PRIVACY POLICY" link to https://www.fide.com/privacy; not fetched.) Consequence: the lists are downloadable without login, but redistribution needs FIDE's written permission; the repository must not commit them (see `.gitignore`).

Discrepancy with the research report: the report (§5) describes the October 2026 list as "dated 07 Oct 2026" and "about 42.6 MB"; the page now shows 08 Oct 2026 and 42.61 MB. The sizes 12.7 / 10.7 / 7.3 MB in the report match the page (12.67 / 10.72 / 7.25 MB).

---

## 4. database.lichess.org — VERIFIED

- URL: https://database.lichess.org/
- Fetched: 2026-10-09T14:28:53Z, HTTP 200, 473,710 bytes.

Licence text, verbatim from the page:

> Database exports are released under the Creative Commons CC0 license. Use them for research, commercial purpose, publication, anything you like. You can download, modify and redistribute them, without asking for permission.

and, for broadcasts:

> Broadcast games are released under the Creative Commons Attribution-ShareAlike 4.0 license .

Standard games headline, verbatim: "8,220,312,882 standard rated games, played on lichess." (matches the research report). Note on files, verbatim: "Each file contains the games for one month only; they are not cumulative."

Monthly standard-rated files, 2024–2026, exactly as listed (size and game count are the page's own figures):

| File | Month (as listed) | Size (as listed) | Games (as listed) |
|---|---|---|---|
| lichess_db_standard_rated_2024-01.pgn.zst | 2024 - January | 32.4 GB | 98,994,760 |
| lichess_db_standard_rated_2024-02.pgn.zst | 2024 - February | 29.8 GB | 91,567,975 |
| lichess_db_standard_rated_2024-03.pgn.zst | 2024 - March | 31.1 GB | 95,804,114 |
| lichess_db_standard_rated_2024-04.pgn.zst | 2024 - April | 29.6 GB | 91,377,787 |
| lichess_db_standard_rated_2024-05.pgn.zst | 2024 - May | 30.7 GB | 94,400,051 |
| lichess_db_standard_rated_2024-06.pgn.zst | 2024 - June | 29.1 GB | 89,342,529 |
| lichess_db_standard_rated_2024-07.pgn.zst | 2024 - July | 29.3 GB | 90,106,180 |
| lichess_db_standard_rated_2024-08.pgn.zst | 2024 - August | 30 GB | 92,198,878 |
| lichess_db_standard_rated_2024-09.pgn.zst | 2024 - September | 28.6 GB | 87,713,219 |
| lichess_db_standard_rated_2024-10.pgn.zst | 2024 - October | 30.7 GB | 94,254,891 |
| lichess_db_standard_rated_2024-11.pgn.zst | 2024 - November | 29.6 GB | 90,847,982 |
| lichess_db_standard_rated_2024-12.pgn.zst | 2024 - December | 31.6 GB | 96,587,411 |
| lichess_db_standard_rated_2025-01.pgn.zst | 2025 - January | 32.9 GB | 100,412,379 |
| lichess_db_standard_rated_2025-02.pgn.zst | 2025 - February | 29.2 GB | 89,430,612 |
| lichess_db_standard_rated_2025-03.pgn.zst | 2025 - March | 31.8 GB | 97,512,351 |
| lichess_db_standard_rated_2025-04.pgn.zst | 2025 - April | 29.8 GB | 91,757,350 |
| lichess_db_standard_rated_2025-05.pgn.zst | 2025 - May | 30.7 GB | 94,068,115 |
| lichess_db_standard_rated_2025-06.pgn.zst | 2025 - June | 29.7 GB | 91,189,178 |
| lichess_db_standard_rated_2025-07.pgn.zst | 2025 - July | 30.4 GB | 93,092,772 |
| lichess_db_standard_rated_2025-08.pgn.zst | 2025 - August | 30.2 GB | 92,695,519 |
| lichess_db_standard_rated_2025-09.pgn.zst | 2025 - September | 28.3 GB | 87,049,890 |
| lichess_db_standard_rated_2025-10.pgn.zst | 2025 - October | 29.9 GB | 91,549,148 |
| lichess_db_standard_rated_2025-11.pgn.zst | 2025 - November | 29.4 GB | 90,633,152 |
| lichess_db_standard_rated_2025-12.pgn.zst | 2025 - December | 30.8 GB | 94,847,276 |
| lichess_db_standard_rated_2026-01.pgn.zst | 2026 - January | 30.7 GB | 94,604,722 |
| lichess_db_standard_rated_2026-02.pgn.zst | 2026 - February | 27.8 GB | 84,600,043 |
| lichess_db_standard_rated_2026-03.pgn.zst | 2026 - March | 29.4 GB | 90,074,196 |
| lichess_db_standard_rated_2026-04.pgn.zst | 2026 - April | 29.3 GB | 89,962,564 |
| lichess_db_standard_rated_2026-05.pgn.zst | 2026 - May | 29.7 GB | 90,887,615 |
| lichess_db_standard_rated_2026-06.pgn.zst | 2026 - June | 28.2 GB | 86,483,328 |
| lichess_db_standard_rated_2026-07.pgn.zst | 2026 - July | 29.1 GB | 89,288,421 |
| lichess_db_standard_rated_2026-08.pgn.zst | 2026 - August | 30.1 GB | 91,912,325 |
| lichess_db_standard_rated_2026-09.pgn.zst | 2026 - September | 29.2 GB | 89,616,462 |

(rows: 33; the page lists September 2026 as the latest month at fetch time)

---

## 5. Licences of the four repositories — VERIFIED

- Method: GitHub REST API via `gh api repos/{owner}/{repo}/license` at 2026-10-09T14:28:56Z, which returns the licence file's path, GitHub's SPDX detection for that file, and the file content (decoded and inspected).

| Repository | Licence file | SPDX id | First copyright line in the file | Default branch | Last push (API) |
|---|---|---|---|---|---|
| github.com/Remi-Coulom/WHR | LICENSE | **MIT** | "Copyright (c) 2005 Rémi Coulom" (file begins "The MIT License (MIT)") | master | 2023-05-27T19:50:24Z |
| github.com/goshrine/whole_history_rating | LICENSE | **MIT** | "Copyright (c) 2012 Pete Schwamb" | master | 2020-08-25T12:36:40Z |
| github.com/wind23/whole_history_rating | LICENSE | **MIT** | "Copyright (c) 2012 Pete Schwamb" / "Copyright (c) 2019 Tianyi Hao" | master | 2026-09-28T20:33:23Z |
| github.com/lichess-org/lila | LICENSE | **AGPL-3.0** | file begins "GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007" | master | 2026-10-09T10:43:44Z |

Consequence: all three WHR implementations are MIT and can be studied or vendored into an Apache-2.0 code base with attribution; lila is AGPL-3.0 and must not be copied into this repository (read for reference only). This confirms the research report's "lila licence believed AGPL (verify)" and resolves its "Licence not verified" for the WHR repositories.

---

## Additional check

- https://ratings.fide.com/calc.phtml?page=change returned HTTP 200 at 2026-10-09T14:30:34Z (reachable; page content not transcribed in this sweep — it is the test-vector oracle named in the Layer-0 spec).

## Not verified in this sweep (for the record)

- The FIDE Council decision documents behind the 1 October 2025 amendment (fide.com news) and the 1 December 2024 rapid/blitz exclusion: only the handbook text embedding them was verified.
- The content of the FIDE calculator page, the TXT/XML list file layouts (files not downloaded), and the Lichess page's totals for variants, puzzles and evaluations (not needed).
- Everything else in the research report's source list (Appendix C of the proposal marks each source VERIFIED or NOT VERIFIED accordingly).
