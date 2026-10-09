# FIDE fixtures for SPEC-L0

Status: REVIEW — recorded 2026-10-09 (session ELO-3, Phase 2) for `docs/specs/SPEC-L0_fide-reference-engine_v1_0.md`; `published_multi_event_periods.json` added in session ELO-4 under D-0008, R10. Every derived value of the ELO-3 files is recomputed by `analysis/l0_fixtures_report.py` (output `analysis/OUTPUT_L0_fixtures.md`); the rounding evidence of all published calculations by `analysis/l0_rounding_report.py` (output `analysis/OUTPUT_L0_rounding.md`).

## Files

| File | Cases | Source | What they settle |
|---|---|---|---|
| `calculator_rating_change.json` | F-C01 to F-C24 | FIDE's online calculator, rating change (`https://ratings.fide.com/a_calc_rtd.php`, behind `calc.phtml`) | Table 8.1.2 row edges on both sides of D; the K multiplication; the calculator's own 400-point rule |
| `calculator_initial_rating.json` | F-I01 to F-I08 | FIDE's online calculator, initial rating (`https://ratings.fide.com/a_calc_initial.php`) | Which initial-rating rule the calculator applies |
| `published_calculations.json` | F-P01 to F-P05 | FIDE's published per-player calculations (`https://ratings.fide.com/a_indv_calculation.php`, behind `calculations.phtml`) plus single values from the monthly lists | R-11a (which list's ratings a tournament uses), R-14 (who is exempt from the 400-point cap), several capped games in one event, R-23 (K × n ≤ 700), R-25 (rounding, −2.50 → −3), base corrections, and the open question of rounding per period or per tournament |
| `published_multi_event_periods.json` | F-M01 to F-M58 | FIDE's published per-player calculations, fetched and parsed by `tools/data/fetch_fide_calculations.py`, plus single values from the monthly lists | SPEC-L0 §8 Q-1 (D-0008, R10): rating periods with two or more tournaments, each checked game by game against the engine, with the change rounded once and per tournament against the published list |
| `published_initial_rating.json` | F-N01 | FIDE's published calculation and tournament report for a player new to the list, plus the first published rating | R-27 to R-30 (the current initial-rating rule) and what FIDE's printed "Rp" means |

Each case carries the URL, the UTC time of the request and the response (verbatim text for the calculator; parsed fields for the published calculations).

## Method

- Requests were sent from the operator's machine with `curl`, one at a time, at least 6 seconds apart (34 to the calculator endpoints, including two probes; 12 per-player calculations; 3 tournament reports).
- The calculator cases were chosen before any request was made: every row edge of table 8.1.2 that a single game can probe, both signs of D, the 400-point rule on both sides of 2650, and the initial-rating rule at, above and below 50 %, at the 2200 maximum and near 1400.
- The published calculations were chosen to answer specific questions: a player rated above 2650 against one rated below (R-14, F-P01 and F-P02 are the two sides of the same game), players with several events in one period (F-P02, F-P03, F-P05), an event that started on the last day of a month (F-P03), a player with 39 games in one period (F-P05) and an apparent base correction (F-P04).

### Multi-event periods (session ELO-4, D-0008 R10)

- Two deterministic selections from the converted lists, made before any request: `select 2026-04 2026-06 2026-08 2026-10` (adults with K 10 or 20 on the previous list and at least 12 rated games in the period; the first 10 per period in the SHA-256 order of "PERIOD:ID") and `select-cross 2025-06 2026-09` (adults of broadcast tours that span a month boundary, so that their period holds an event started under an earlier list; at most 40).
- 76 requests (40 and 36, four candidates being common to both selections), one at a time, at least 10 seconds apart, on 2026-10-09 between 23:05 and 23:31 UTC; the endpoint answers only requests carrying the headers the page itself sends (`X-Requested-With: XMLHttpRequest` and the page as referer). Raw responses stay under `data/raw/fide_calculations/` and are not committed.
- 58 of the 76 periods hold two or more tournaments and are kept; the other 18 hold one.

## Findings

1. **FIDE's online calculator is out of date.** The rating-change calculator applies the 400-point cap to everyone, including players rated 2650 or above, so it does not implement §8.3.1 as amended on 1 October 2025 (F-C16, F-C17, F-C20, F-C21). The initial-rating calculator applies the archived rule of 1 January 2022 till 29 February 2024 (F-I01 to F-I08). Both calculators agree with tables 8.1.2 and 8.1.1 wherever those rules coincide. The calculator therefore settles the table rows and the multiplication, not the 2650 exemption or the initial-rating rule; under the brief's fallback, FIDE's published per-player calculations do.
2. **R-14, own rating.** In the same game, the player rated 2813 uses the full difference of 413 (PD .93, F-P01), while the opponent rated 2400 sees "2800 *", the capped value (F-P02). The exemption depends on the rating of the player whose change is computed.
3. **Several capped games in one event** are each capped (F-P02: three in one event). The archived chapter allowed "only one upgrade" per tournament; the current text does not.
4. **R-11a: ratings are taken from the list in force when the tournament starts.** An event from 31 October to 2 November 2025, rated in the December 2025 period, used the October list (F-P02, F-P03). This is written in the Title Regulations (§1.4.6 a) but not in the Rating Regulations.
5. **R-23.** With 39 games in a period, K = 17 = ⌊700 / 39⌋ (F-P05).
6. **R-25.** A change of −2.50 is published as −3 (F-P01).
7. **Rounding per period or per tournament: unresolved.** F-P02 is reproduced only by rounding each tournament's change separately; F-P05 only by rounding the period's change once, as §8.3.4 is written. Of six further players in the same events, not recorded because they are minors, one is reproduced only per tournament, one only per period and four both ways (two of them after a base correction). SPEC-L0 follows the text and marks the point NOT VERIFIED.
8. **Base corrections.** FIDE's starting rating (Ro) can differ from the previously published list: 2053 against 2052 in F-P04. Layer 0 cannot reproduce such a correction from the lists alone.
9. **Initial rating.** The first published rating of F-N01 (1922) follows the current rule, (sum of opponents + 2 × 1800) / (n + 2) + dp. The "Rp" FIDE prints beside it (1921) follows the archived rule, average + 20 per half point over 50 %.

10. **Rounding once per period (Q-1), the R10 evidence.** In 13 of the 14 periods of all published calculations in which rounding once and rounding per tournament give different changes, the list follows rounding once, as §8.3.4 is written (12 of them new, F-M; the 13th F-P05). F-P02 remains the one exception. Eight of the 13 hold an event that started under an earlier list, so such events are not rounded separately either (`analysis/OUTPUT_L0_rounding.md`).
11. **The engine on 923 more games.** Every game of the 58 new periods is reproduced by Layer 0, with each tournament's sum, K (from the previous list, reduced under R-23) and K × sum (`tests/test_l0_rounding_periods.py`).
12. **Base corrections are common.** In 6 of the 58 new periods a tournament's starting rating Ro differs from the list in force at its start; in each of them the period's change, rounded once and applied to FIDE's own Ro, reproduces the next list exactly. Two periods (F-M09, F-M18) are one point off under both roundings with no visible base correction.

## Privacy and licence

- Only adults (born 2007 or earlier) are recorded. Opponents are identified by the rating FIDE used, never by name. Tournament names and places are as FIDE publishes them.
- Values quoted from the monthly lists are single values per player, recorded to check the calculations. The lists themselves are not committed or redistributed (`.gitignore`; FIDE's terms, `docs/research/VERIFICATION_2026-10-09.md`, item 3).
- These files record facts returned by FIDE's public pages, for verification. They are part of `tests/`, so the code licence (Apache-2.0) covers the files; the FIDE content quoted in them remains FIDE's.
