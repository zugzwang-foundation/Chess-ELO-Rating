# Verification sweep — FIDE Title Regulations and the archived rating regulations, 2026-10-09

Status: VERIFICATION RECORD (primary-source transcription). Session ELO-3, Phase 2. Author: The Zugzwang Authors. Licence: CC BY 4.0 (see `docs/LICENSE-docs.md`); quoted FIDE text remains FIDE's and is reproduced for verification only.

**Method.** Each page was fetched with `curl` (User-Agent "Mozilla/5.0") from the operator's machine at the UTC time shown, saved, and converted to text with a Python standard-library script that takes the chapter's paragraphs, lettered lists and tables in document order; tables are rendered from their `<table>` markup, nothing is retyped. Section headings and numbering are as on the page. Every item is marked VERIFIED (URL, UTC timestamp, extracted text) or NOT VERIFIED. Nothing below was filled from memory. Citation key: `[VT k]` is item k of this file.

| # | Item | Status | Fetched (UTC) |
|---|---|---|---|
| 1 | FIDE Title Regulations effective from 1 January 2024: the parts that use ratings or the rating tables (§0.5, §0.6.2, §1.1.4, §1.3, §1.4.6–§1.4.9, §1.5.3, §1.7) | VERIFIED | 2026-10-09T17:56:10Z |
| 2 | FIDE Rating Regulations effective from 1 January 2022 till 29 February 2024 (archived): §8.2 and §8.3.1, for comparison with FIDE's online calculator | VERIFIED | 2026-10-09T17:36:02Z |
| 3 | Table 1.4.9 of the Title Regulations compared with table 8.1.1 of the Rating Regulations [V 1] | VERIFIED: identical, 101 entries out of 101 | derived from items 1 and [V 1] |

---

## 1. FIDE Title Regulations effective from 1 January 2024 — VERIFIED

- URL: https://handbook.fide.com/chapter/B012024
- Fetched: 2026-10-09T17:56:10Z, HTTP 200, 492,375 bytes.
- Page header (verbatim): "FIDE TITLE REGULATIONS" / "Applied from 1 January, 2024". The handbook lists the chapter as "FIDE Title Regulations effective from 1 January 2024", with archived versions for 2023, 2022, 2017–2021 and 2014–2017.

> 0.5 Definitions
>
> In the following text some special terms are used.
>
> Rating refers to a player’s Standard FIDE rating
>
> Rating performance is based on the player’s result and average rating of opponents (see 1.4.6 to 1.4.8).
>
> Title performance is a result that gives a performance rating as defined in 1.4.6 to 1.4.9 against the minimum average of the opponents, for that title.
>
> GM performance is ≥ 2600 performance against opponents with average rating ≥ 2380.
>
> IM performance is ≥ 2450 performance against opponents with average rating ≥ 2230.
>
> WGM performance is ≥ 2400 performance against opponents with average rating ≥ 2180.
>
> WIM performance is ≥ 2250 performance against opponents with average rating ≥ 2030.
>
> Title norm is a title performance fulfilling additional requirements concerning the mix of titled players and nationalities as specified in articles 1.4.2 to 1.4.5.
>
> Direct title (automatic title) is a title gained by achieving a certain place or result in a tournament. On application by the player’s federation and confirmation by the Qualification Commission, such titles are awarded automatically by FIDE.
>

> 0.6.2 For a direct title to be awarded immediately an applicant has to have achieved at some time a minimum rating published or interim (see 1.5.3a), as follows:
>

| GM | 2300 | WGM | 2100 |
|---|---|---|---|
| IM | 2200 | WIM | 2000 |
| FM | 2100 | WFM | 1900 |
| CM | 2000 | WCM | 1800 |

> This requirement does not apply to direct CM/WCM titles earned at the Open and Women’s Chess Olympiads
>
> For ratings achieved after 1st January 2024, the player must at that time have played at least 30 rated games
>
> If an applicant is rated lower the title is awarded conditionally and will be awarded finally on request by the respective federation as soon as the minimum rating is achieved. Any player with a conditional title may take a lower title when they reach the required rating for that lower title. ‘Lower titles’ are lesser titles within the same category (Open or Women’s titles)
>

> 1.1.4 In tournaments which last longer than 30 days, the opponents’ ratings and titles used shall be those applying when the games were played.
>

> 1.3 Titles may be gained by achieving a published or interim rating at some time (see 1.5.3a). For ratings achieved after 1st July 2017, the player must at that time have played at least 30 rated games:
>
> 1.3.1 FIDE Master ≥2300
>
> 1.3.2 Candidate Master ≥2200
>
> 1.3.3 Women FIDE Master ≥2100
>
> 1.3.4 Women Candidate Master ≥2000
>

> 1.4.6 Rating of opponents
>
> a) The Rating List in effect at the start of the tournament shall be used (see exception 1.1.4). The rating of players who belong to federations which are temporarily excluded when the tournament starts can be determined on application to the FIDE Office.
>
> b) For the purposes of norms, the minimum rating (adjusted rating floor) for the opponents shall be as follows:
>

| Grandmaster norm | 2200 |
|---|---|
| International Master norm | 2050 |
| Woman Grandmaster norm | 2000 |
| Woman International Master norm | 1850 |

> c) No more than one opponent shall have their rating raised to this adjusted rating floor. Where more than one opponent is below the floor, the rating of the lowest rated opponent shall be raised.
>
> d) Unrated opponents not covered by 1.4.6b shall be considered to be rated 1400.
>
> 1.4.7 Rating average of opponents
>
> a) This is the total of the opponents’ ratings divided by the number of opponents taking 1.4.6 into account.
>
> b) Rounding of the rating average is made to the nearest whole number. The fraction 0.5 is rounded upward.
>
> 1.4.8 Performance Rating (Rp)
>
> In order to achieve a norm, a player must perform at a level at least of that shown below:
>

|  | Minimum level prior to rounding | Minimum level after rounding |
|---|---|---|
| GM | 2599.5 | 2600 |
| IM | 2449.5 | 2450 |
| WGM | 2399.5 | 2400 |
| WIM | 2249.5 | 2250 |

> Calculation of a Performance Rating (Rp):
>
> Ra = rating average of opponents (see 1.4.7)
>
> dp = rating difference from 1.4.9 below
>
> Rp = Ra + dp
>
> a) The minimum average ratings Ra of the opponents are as follows: GM 2380; IM 2230; WGM 2180; WIM 2030
>
> b) The minimum score is 35% for all norms.
>

> 1.4.9 Table
>

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

> All percentages are rounded to the nearest whole number. 0.5% is rounded up.
>

> 1.5.3 To have achieved at some time a rating as follows:
>
> GM ≥ 2500
>
> IM ≥ 2400
>
> WGM ≥ 2300
>
> WIM ≥ 2200
>
> a) Such a rating need not be published. It can be obtained in the middle of a rating period, or even in the middle of a tournament. The player may then disregard subsequent results for the purpose of their title application. However, the burden of proof then rests with the federation of the title applicant. Title applications based on unpublished ratings shall only be accepted by FIDE after agreement with the Rating Administrator and the QC. Ratings in the middle of a period can be confirmed only after all tournaments for that period have been received and rated by FIDE.
>

> 1.7 Summary of Requirements for the Number of Opponents
>
> Determining whether a result is adequate for a norm is dependent on the average rating of the opponents. Tables in the Annex show the range for tournaments up to 19 rounds. Norms achieved in a tournament with more than 13 rounds count only as 13 games.
>


---

## 2. FIDE Rating Regulations effective from 1 January 2022 till 29 February 2024 (archived) — VERIFIED

- URL: https://handbook.fide.com/chapter/B022022
- Fetched: 2026-10-09T17:36:02Z, HTTP 200, 133,080 bytes.
- Transcribed because FIDE's online calculator (https://ratings.fide.com/calc.phtml) still computes initial ratings by this rule and applies this chapter's 400-point rule (fixtures in `tests/fixtures/fide_calculator/`).

> 8.2 Determining the initial rating 'Ru' of a player.
>
> 8.2.1 If an unrated player scores zero in their first event this score is disregarded. Otherwise, their rating is calculated using all their results as in 7.1.4.
>
> 8.2.2 Ra is the average rating of the player's rated opponents.
>
> 8.2.3 If the player scores 50%, then Ru = Ra.
>
> If they score more than 50%, then Ru = Ra + 20 for each half point scored over 50%.
>
> If they score less than 50%, then Ru = Ra + dp
>
> Ru is rounded to the nearest whole number.
>
> 8.2.4 If an unrated player receives a published rating before a particular tournament in which they have played is rated, then they are rated as a rated player with their current rating, but in the rating of their opponents they are counted as an unrated player.
>
> 8.3 Determining the rating change for a rated player
>
> 8.3.1 For each game played against a rated player, determine the difference in rating between the player and their opponent, D.
>
> A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points. In any tournament, a player may benefit from only one upgrade under this rule, for the game in which the rating difference is greatest.
>


---

## 3. Table 1.4.9 against table 8.1.1 — VERIFIED

Every one of the 101 (p, dp) pairs of table 1.4.9 [VT 1] equals the corresponding pair of table 8.1.1 as transcribed in [V 1] (checked by script, pair by pair, on 2026-10-09).

## Notes for the proposal and SPEC-L0 (facts only)

- The norm arithmetic of the Title Regulations computes Rp = Ra + dp with dp from its own table 1.4.9 [VT 1], which is identical to table 8.1.1 [VT 3]. It does not use table 8.1.2 (D into PD). Replacing table 8.1.2 (rung 2 of the proposal) therefore leaves the norm formula and its table unchanged; the ratings that enter Ra, the opponents' rating floors (§1.4.6 b), the titles by rating (§1.3), the minimum ratings for direct titles (§0.6.2) and the rating requirement of §1.5.3 are still affected by any rung that changes published ratings.
- §1.4.6 a) and §1.1.4 use the rating list in effect at the start of the tournament, and, for tournaments longer than 30 days, the ratings applying when the games were played. The Rating Regulations [V 1] state no such rule for rating calculations; FIDE's published calculations follow the same convention (SPEC-L0, R-11a).
- §1.4.7 b) and the sentence after table 1.4.9 are the only FIDE texts found that state how an average and a percentage are rounded before a table lookup: "Rounding of the rating average is made to the nearest whole number. The fraction 0.5 is rounded upward." and "All percentages are rounded to the nearest whole number. 0.5% is rounded up." SPEC-L0 adopts the same reading for the initial-rating lookup of §8.2.3 [V 1] (R-30), marked NOT VERIFIED for that paragraph.
- In the archived chapter [VT 2] the 400-point rule allowed "only one upgrade" per tournament; the current §8.3.1 [V 1] has no such sentence.

## Not verified in this sweep

- The Annex of the Title Regulations (tables for 7 to 19 rounds giving, per score, the minimum average rating of the opponents for each norm, with rating floors and title counts) was seen on the page but not transcribed. It opens with "In the case of any discrepancy, the regulations above shall take precedence."; SPEC-L0 does not use it.
- Whether FIDE's statutes would let the Qualification Commission publish a new normative table each year without a Council decision (proposal §11): not part of these chapters.
