# D-0014 — A forecast test pre-registered (Freeze 3b), what the pairings fix, the PILOT on (b′); and the rulings for the other questions

Date: 2026-10-11 (UTC; part A recorded at about 06:20) · Session: ELO-8, Phase 0 (part A) and Phase 1 (part B) · Status: DECIDED — the architect's rulings R54 to R65, given by Web Claude in the ELO-8 brief and recorded by the executor. Part A (R54 to R57) is recorded before any result of either 2026 championship was read, with Freeze 3b, which extends Freeze 3a (`docs/decisions/D-0012_pre-results-amendments.md`) and is tagged `freeze-3b`; part B (R58 to R65) follows in Phase 1, as D-0011's part B followed its part A.

## Context

The ELO-7 close-out (the operator's files, not in the repository) left ten open questions, Q1 to Q10. The ELO-8 brief answers them with the rulings R54 to R65. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed below and marked as such; a later record can overrule a reading without reopening the ruling.

The brief also orders, for the whole session: Freeze 1, 2, 3 and 3a files are untouched, except where this record authorises it; no result of the 2026 U.S. Championships is read, entered or looked up (their pairings and official schedule may be read, their results page may not); the championship's tables stay as frozen, fitted on games to 30 September 2026; no game from October 2026 onward is used anywhere.

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## Part A — the forecast test, what the pairings fix and the PILOT on (b′): Freeze 3b

### The rulings

The text of each ruling is the brief's, transcribed.

| # | Answers | Ruling (the brief's text) |
|---|---|---|
| R54 | Q1 (§10 measures the pairings) | A results-dependent test is pre-registered. For every counted game of both 2026 championships (D-0013), compute the per-game three-outcome log-loss and the expected-score Brier score of FIDE's expectation (column (a): table 8.1.2 as FIDE applies it, October 2026 ratings) and of rung 2's (column (b′): Freeze 3's v2 table with its guard and colour term). Report the two means and their difference, with bootstrap 95 % intervals over games and over players, per event and pooled. State in advance that the sample is small, that the result may go either way, and that it will be reported whatever it shows. Add the blanks to §10, the computation in new code, and its hash to the manifest; tag `freeze-3b` and push the tag. |
| R55 | Q1 (the values the pairings fix) | Print now, in E13, every figure the pairings and the October ratings fix: per player (b′) − (a), (b) − (a), (b0) − (a) and the PILOT's difference, assuming every game is played (a game not counted under D-0013 removes its term). Label them "fixed by the pairings and the October ratings — the same whatever the results". Compute nothing that depends on a result. |
| R56 | Q2 (the PILOT's m) | The PILOT is rebuilt on (b′) at today's K. The PILOT on (b) with K × m is withdrawn, reported once and labelled superseded. |
| R57 | Q3 (D-0013) | D-0013's reading is confirmed as written. |

### Freeze 3b: what is added, before any result was read

Recorded by the executor in Phase 0 of session ELO-8, on 2026-10-11 at about 06:20 UTC. It extends Freeze 3a (D-0012), which stands unchanged: no file of Freeze 1, 2, 3 or 3a is modified.

**Why.** The ELO-7 review found that the score cancels from (b′) − (a), from (b0) − (a) and from the PILOT's difference, so that §10's main blanks are set by the pairings and the October ratings, results moving them only through games not counted (`docs/review/REDTEAM_v1_0.md`, ELO7-STAT-1). R54 adds a measure the results decide; R55 prints now what the pairings already fix; R56 rebases the PILOT on the main column.

**What is added.**

1. **The forecast test (R54).** For every counted game of each event (a result of 1-0, ½-½ or 0-1; a game marked `unplayed` under D-0013, or without a result, is not counted), two forecasts of the result, each scored from White's side:
   - **(a), FIDE's expectation:** E_a, table 8.1.2's expected score for White as Layer 0 applies it (the 400-point rule as it applies to each player) on the October 2026 ratings of the event files. Table 8.1.2 has no draw model, so the three outcomes split E_a with the draw rate of the game's 100-point level band in the v2 table's training months, standard broadcast games of 2023-10 to 2026-09 (E2's construction for Layer 0, `docs/specs/SPEC-TABLE-FIT_v1_0.md` §3): P_D = min(rate, 2E − 0.002, 2(1 − E) − 0.002) with E clipped to [0.002, 0.998], P_W = E − P_D/2, P_L = 1 − E − P_D/2 (E6's split). The rates are frozen in `params/draw_rate_2026-10b.json`, written by `analysis/us26_draw_rate_extract.py`, which rebuilds E11's sample from the archive files E11 read and checks that it is E11's game for game: the window's 339,485 games, its 33,386 cells and the log-likelihood at E11's published fit (−316,260.136125) all equal E11's. At the level bands of the two fields' games the rates are 0.318 (2200–2299), 0.370 (2300–2399), 0.440 (2400–2499), 0.575 (2600–2699) and 0.596 (2700–2799) [E13].
   - **(b′), rung 2's expectation:** E_b′, the expectation column (b′) uses for White (Freeze 3's v2 table's published entry at the game's level band with its colour term η = 36 and the narrowed guard where it applies), split with the v2 model's own draw probability at the game's effective gap and band by the same rule, so that, as where E10 and E6 guard a game, the draw probability is the model's and the win and loss probabilities carry the column's expectation.
   - **The measures:** the three-outcome log-loss, −ln of the probability the forecast gave the result (nats), and the expected-score Brier score, (S − E)², each column's expectation E unclipped; their means over the counted games, and the difference (b′) − (a), a negative difference favouring (b′).
   - **The intervals:** percentile bootstrap 95 % intervals, 2,000 resamples, seed 20261009 (annex T8.5's), for each mean and for the difference, paired across the columns: over games, the games resampled within each event; over players, the players resampled within each event, each bringing all its counted games, so that a game enters once for each of its players drawn. Per event, and pooled over the two events with each event resampled within itself.
   - **Stated in advance:** "The sample is small (at most 66 games an event, 132 in all): the difference may favour either column, or neither, and it is reported whatever it shows." The statement is printed with the test in E13, in §10 and here.
   - **The code:** `tools/compare_event_v3b.py` (new), tested in `tests/test_compare_event_v3b.py` on the synthetic event and the 2025 event, never on a 2026 result.
2. **What the pairings fix, printed now (R55).** Per player, assuming every game is played, a game marked `unplayed` removing its term: (b′) − (a) = K × Σ(E_a − E_b′) and (b0) − (a), where the score cancels; the PILOT's difference, on (b′) at today's K and, once, on (b) with K × m, labelled superseded; and, for (b) − (a), only what the pairings fix (reading 7). The figures come from Freeze 3a's own code, unchanged, run on two copies of each event in which every game not marked `unplayed` carries a placeholder result (all draws; all wins for White): the two runs must agree exactly, and agree with the direct sums, or the page is not printed. No result is read; the copies overwrite whatever the files hold. E13 prints them under the label "fixed by the pairings and the October ratings — the same whatever the results", with the event-level means and largest differences. With every game played: in the open event the mean of |(b′) − (a)| is 2.09 points and the largest +4.70; in the women's 2.44 and −7.58; for (b0) 3.28 and +7.40, 3.47 and −10.10 [E13].
3. **The PILOT on (b′) (R56).** Rung 5 on top of (b′) at today's K: Freeze 3's PILOT computation (`tools/compare_event_v3.py`) with the slope ratio switched off, with the frozen rung-5 inputs (`params/rung5_us2026.json`, D-0010). `{{US26_*_R5_GAMES}}` and `{{US26_*_R5_DIFF}}` now measure it: 20 and 9 games of a compensated junior against an opponent not eligible, those opponents' total change minus (b′) +14.73 and +0.61 points if every game is played. The PILOT on (b), with K × m, is withdrawn; E13 reports it once, in the section on what the pairings fix, labelled superseded (+24.22 and +0.89), and prints no PILOT table on (b) after the event.
4. **E13.** The page `docs/evidence/E13_us-championship-2026-freeze-3.md` is now printed by a new script, `analysis/e13_us_championships_freeze3b.py`, which prints what the pairings fix now, and after the event the columns, the PILOT on (b′), the forecast test and the blanks; Freeze 3a's page script stays unchanged and is used as a module (its file list and manifest), as Freeze 3a used Freeze 3's.
5. **The check.** Check (a) (`tools/checks/check_outputs.py`, unchanged) still compares Freeze 3a's live manifest with D-0012's. A new check (a′), `tools/checks/check_freeze3b.py`, run by a new step of the automated check (`.github/workflows/check.yml`), compares Freeze 3b's live manifest with the one this record holds; a missing record or manifest fails it.
6. **R57.** D-0013's reading of §5.1 stands as written: no file changes.

### What will be computed after the event, and nothing else

This list extends D-0012's (items 1 to 5), which stands except where it says otherwise.

1. **Results**, as D-0012 item 1, entered once after the last round from the official page, with `unplayed` for every game §5.1 does not count or rate as D-0013 reads it (R57).
2. **The main table**, as D-0012 item 2: (a), (b′), (b) and (b0), each with its difference from (a).
3. **The PILOT table**, printed separately: rung 5 on top of (b′) at today's K (R56). The PILOT on (b) is not printed after the event.
4. **The blanks of the proposal's §10**, printed by E13 once both events are complete, over counted games only: D-0012's blanks, with `{{US26_*_R5_GAMES}}` and `{{US26_*_R5_DIFF}}` now for the PILOT on (b′); and for the forecast test, for * = OPEN, WOMEN and POOLED (both events together):
   - `{{US26_*_LL_A}}` and `{{US26_*_LL_BP}}`: the mean three-outcome log-loss of (a) and of (b′), nats a game, four decimals, each with its two intervals, written "mean (games lo to hi; players lo to hi)";
   - `{{US26_*_LL_DIFF}}`: the mean of (b′)'s log-loss minus (a)'s, signed, with its two intervals;
   - `{{US26_*_BRIER_A}}`, `{{US26_*_BRIER_BP}}` and `{{US26_*_BRIER_DIFF}}`: the same for the Brier score.
5. **`{{US26_READING}}`**, as D-0012 item 4, adds one thing: the forecast test's result in words, whatever it shows, with the statement made in advance that the sample is small and the result may go either way.
6. **Not computed on the event**: as D-0011 part B, item 5; the figures the pairings fix are printed already and are not recomputed with the results, except that a game marked `unplayed` removes its term.

### The time of the freeze, and the rounds completed

The official schedule, as D-0011 part B transcribed it from the Saint Louis Chess Club's official page (read on 10 October at about 14:35 UTC for the schedule only; rounds at "12:00" without a time zone, read as Saint Louis local time, UTC − 5): round 1 on 9 October; round 2 on 10 October at 17:00 UTC; round 3 on 11 October at 17:00 UTC; rounds 4 to 11 on 12, 14–17 and 19–21 October. The page was not opened again in this session, so that no result could be seen. This part is written at about 06:20 UTC on 11 October; the commit that merges it is tagged `freeze-3b`, and that commit's time is the freeze's time. **At that moment, by the schedule, two rounds of each event had been played (round 1 on 9 October; round 2, begun at 17:00 UTC on 10 October, some thirteen hours earlier), and round 3 was scheduled to start at 17:00 UTC on 11 October.** No result of any round was read.

### The scope

Freeze 3b covers Freeze 3a's files (D-0012, "The scope"), unchanged, and the five files it adds: `tools/compare_event_v3b.py`, `analysis/e13_us_championships_freeze3b.py`, `analysis/us26_draw_rate_extract.py`, `params/draw_rate_2026-10b.json` and `tools/checks/check_freeze3b.py`. The tests and the synthetic event file stay outside it, as Freeze 3a's do; so does the workflow file that runs the checks.

### The manifest

E13 prints the SHA-256 of each of the 56 entries (54 files and the two event files without their results) and their manifest, the SHA-256 of the lines "hash  file" in the order E13 prints them. At this record:

Freeze-3b manifest: `48457b941e833e7d3d54203228c120fe1ef98c579435d9e987c51003f73bfe7d` (56 entries)

Check (a′) reruns the computation on every pull request and compares the live manifest with the one recorded above; a change to any frozen file therefore fails the check, even after E13 is regenerated, until a new decision record supersedes this one. Freeze 3a's manifest (`44954559b5b8609f70128bec71af642d7164bcec939441891fe70942a1667212`, D-0012) is not superseded: its 51 entries are unchanged and check (a) keeps comparing it.

### Executor's readings where a ruling leaves a detail open

1. **R54: (a)'s three outcomes.** Table 8.1.2 prints an expected score only. The draw share is E2's for Layer 0 (the training months' draw rate of the game's 100-point level band, with E6's floor), taken from the training months of the table (b′) uses, so that both columns rest on the same games; it adds no parameter to either column.
2. **R54: (b′)'s three outcomes.** The v2 model's draw probability with the column's expectation, so that each forecast's expected score is exactly the expectation its column uses, the guard included (it binds in no pairing of either field).
3. **R54: the Brier score** is computed on each column's own expectation, as E2 computes it, without the clipping the log-loss needs.
4. **R54: White's side.** Each game is scored once, from White's side; no pairing of either field has a gap beyond 400 points, so White's and Black's forecasts are mirror images.
5. **R54: "over players".** Players are resampled within each event, each bringing all its counted games, and the statistic is the mean over the drawn players' games; pooled intervals resample each event within itself, for games and for players.
6. **R54: the blanks.** One blank per mean and per difference, each printed with both intervals; "POOLED" for both events together.
7. **R55: (b) − (a).** The score enters (b) − (a) through m: (b) − (a) = C + K × Σ (m − 1) × score over the player's games. "Compute nothing that depends on a result" is read as governing the list, so E13 prints for (b) − (a) only what the pairings fix, C (no point scored) and C + W (every game won, W = K × Σ (m − 1)), and says that the value between them waits for the results.
8. **R55: "assuming every game is played".** Computed by Freeze 3a's code on placeholder results, two sets that must agree, and checked against the direct sums; a game already marked `unplayed` keeps its marker and removes its term. The event-level means and largest differences of (b′) and (b0), and the PILOT's totals, are printed with the per-player figures, under the same label, since the pairings fix them too.
9. **R56: "reported once".** The PILOT on (b) appears once, in E13's section on what the pairings fix, labelled superseded; §10 names it once in a table row.
10. **The 2025 illustration.** E13 also runs the forecast test on the 2025 event, as it prints 2025's other blanks, labelled in sample: the v2 table and the draw rates were fitted on broadcast games of 2023-10 to 2026-09, which include 2025's event wherever it was broadcast.
11. **The check.** Freeze 3b adds a check rather than changing check (a), a Freeze 3a file, so that no file of Freeze 3a changes.
12. **The rounds completed** are taken from the official schedule as D-0011 part B transcribed it, without opening the page again.

### For the architect (decided conservatively, recorded here)

- Reading 7: (b) − (a) is not fixed by the pairings; E13 prints its bounds, not a value.
- Reading 1: the draw share behind (a)'s log-loss comes from the training months' rates by level band; the Brier score, which needs none, is reported beside it.
- Reading 10: the 2025 illustration of the forecast test is in sample.

### Consequences

- After the last round the operator enters the results as D-0013 reads §5.1, regenerates E13 with `.venv/bin/python analysis/e13_us_championships_freeze3b.py` and E3 with `.venv/bin/python analysis/e3_freeze2_record.py` once, and fills the blanks of the proposal's §10 from E13; `{{US26_*_L0_MATCH}}` follows FIDE's published calculations after the 1 November list.
- D-0012 stands; D-0011 part B stands where D-0012 left it. No change to `src/layer0/` before the comparison and the 1 November check (R21, R42, R53).
