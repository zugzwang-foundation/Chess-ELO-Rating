## Appendix H Self-calibrating: one table a year, and today's top 100 under it

*Under this rule, with the same results — not anyone's true strength.*

Rung 2 as recommended is self-calibrating (R65): each year's table is refitted by SPEC-TABLE-FIT v1.2's rules on the games played before that year only, within annex T7.1's yearly caps, by a method fixed before any table was fitted (`docs/specs/SPEC-SELFCAL_v1_2.md`). Run back in time on the broadcast archive, the data allow two tables: 2016–2019 could not be sourced legitimately, and the archive's games before 2023 carry no FIDE IDs, so the first window is 2024-03 to 2024-12, after the March 2024 compression [E18 §1]. The 2025 table keeps v1.1's form; for 2026 the rule of choice picked a piecewise-linear slope by level and a colour term rising with the level, and the yearly caps held six of its parameters at their bounds [E18 §2].

Forecasting each year's games, the year's table beat table 8.1.2 as FIDE applied it in every year (log-loss −0.0516 in 2025, −0.0477 in 2026, nats a game, intervals below zero), and in 2026 it beat the first table kept frozen (−0.00038; −0.00050 to −0.00030): self-calibration earns its name in 2026, the one year that can tell. The size is small: 0.0004 nats a game, against 0.048 over table 8.1.2, and 0.0001 in the form ruling R68 keeps (a choice of form needs 24 months of games after the last rule change; R68 applies from 2027, and the 10-month figure that allowed the 2026 choice was set after the counts were known); and with one year, against a frozen table fitted on 10 months to the year's 22, the result is consistent with self-calibration and cannot establish it [E18 §3]. Table 8.1.2 expects a 100-point favourite at 2700 to score 0.640; the tables, 0.589 and 0.590; White's edge at 2700–2799 is 35 and 43 rating points (48 without the caps), against none in table 8.1.2 [E18 §4].

Today's top 100 replayed with these tables, FIDE's rules before 2025, and K by FIDE's rules on each system's own rating (R61, which changes no K here): in October 2026 the self-calibrating system rates them +14.5 points higher on average than FIDE's rules (−1 to +29); +10.1 to +18.7 with the opponents outside the 100 rated 10 points lower or higher from 2025 (R58); +11.9 with each table's own residual at levels of 2300 or more removed by level band, and +11.2 by band and gap (R59's two estimates, neither a bound, R71); +14.6 with the 2026 table in the form R68 keeps; 38 and 5 of the 100 at 2700 and 2800, against 33 and 1 [E19]. E17's frozen table gave +23.3 over 2020–2026 (Appendix G); E19 supersedes it (R59).

The five largest differences and the five smallest, with every player tied at the cut, names beside FIDE IDs (R60):

*Under this rule, with the same results — not anyone's true strength.*

| | name | FIDE ID | FIDE's rules, October 2026 | self-calibrating | difference |
|---|---|---|---|---|---|
| largest | Erigaisi Arjun | 35009192 | 2746 | 2775 | +29 |
| largest | Mamedyarov, Shakhriyar | 13401319 | 2710 | 2738 | +28 |
| largest | Caruana, Fabiano | 2020009 | 2784 | 2811 | +27 |
| largest | Tabatabaei, M. Amin | 12521213 | 2728 | 2755 | +27 |
| largest | Abdusattorov, Nodirbek | 14204118 | 2780 | 2807 | +27 |
| largest | Sarana, Alexey | 24133795 | 2671 | 2698 | +27 |
| smallest | Dominguez Perez, Leinier | 3503240 | 2732 | 2731 | −1 |
| smallest | Topalov, Veselin | 2900084 | 2695 | 2695 | +0 |
| smallest | Anand, Viswanathan | 5000017 | 2739 | 2739 | +0 |
| smallest | Howell, David W L | 410608 | 2665 | 2666 | +1 |
| smallest | Christiansen, Johan-Sebastian | 1512668 | 2633 | 2634 | +1 |

Read with these caveats [E18 §5] [E19 §8]:

- Two tables only, so the test of self-calibration rests on 2026; the replay differs from FIDE's rules over 22 lists, not E17's 81.
- Opponents outside the 100 keep their published ratings (R58's range above); a replay of the whole pool needs FIDE's tournament reports (section 9, stage 2).
- The tables' own error at the top is estimated, not removed (R59's two estimates above, R71).
- A flatter table spreads ratings further apart at the top (annex T3.5): counts above 2700 and 2800 compare two scales as well as two rules.
- The tables are fitted on broadcast games, stronger and more international than the rated pool.
- Layer 0 reads the 400-point rule of March 2024 to September 2025 as the plain cap, NOT VERIFIED against the handbook; FIDE's calculations agree in every tournament that can tell [E17 §2].
- The figures describe the rule, not the players: who is stronger is not their question.

*Under this rule, with the same results — not anyone's true strength.*
