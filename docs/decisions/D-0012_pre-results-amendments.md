# D-0012 — Pre-results amendments: a game not played, rung 2 at today's K, column (b′) and Freeze 3a

Date: 2026-10-10 (UTC; recorded at about 20:30) · Session: ELO-7, Phase 0 · Status: DECIDED — the architect's rulings R43 to R53, given by Web Claude in the ELO-7 brief, recorded by the executor before any result of either 2026 championship was read, with Freeze 3a, which amends Freeze 3 (D-0011, part B) and is tagged `freeze-3a`

## Context

The ELO-6 close-out (the operator's files, not in the repository) left fourteen open questions, Q1 to Q14: two time-critical ones on the championship comparison (an unplayed game would block §10; column (b) would mostly measure R32's factor m), seven on the rulings R24 and R32 and on the next fit, three on PROVISIONAL values and two of housekeeping. The ELO-7 brief answers them with the rulings R43 to R53. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed below and marked as such; a later record can overrule a reading without reopening the ruling.

The brief also orders, for the whole session: Freeze 1, 2 and 3 files are not modified, except where this record authorises it, namely the results-entry tool, E13 and the check, for unplayed games and the new column only; every fit uses games up to 30 September 2026; no result of the 2026 U.S. Championships is read, entered or looked up (their pairings and official schedule may be read).

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## The rulings

The text of each ruling is the brief's, transcribed.

| # | Answers | Ruling (the brief's text) |
|---|---|---|
| R43 | Q1 (an unplayed game blocks §10) | Unplayed games: tools/set_results.py gets a marker for a game not played (forfeit, withdrawal, bye), distinct from "no result yet". An event is complete when every game of rounds 1–11 has a result or the unplayed marker. Unplayed games are excluded from every column, as FIDE does not rate them, and §10 counts played games only. Update E13 and check (a) to match; test with a synthetic event file kept apart from the 2026 files. |
| R44 | Q5 (R32) | R32 is withdrawn (architect's correction: m raised K by 24–149 %, raised the chance of touching 2500 within 27 games from 5 % to 17 %, and worsened forecasts in standard and blitz). Rung 2 is the v2 table with the narrowed guard at today's K. |
| R45 | Q2 (column (b) measures m) | A new column (b′), "v2 table and narrowed guard at today's K", computed only from Freeze 3's frozen table and guard and Layer 0's K — no new parameter. It is §10's main column; (b) and (b0) stay reported as pre-registered and labelled. Add (b′) to E13 (new code in new files where possible), extend the manifest, record its hash in D-0012, tag `freeze-3a` and push the tag. |
| R46 | Q3 | The guard keeps R24's strict test, one test both to impose and to lift it, run on FIDE's games where the sample can decide. State that the broadcast sample cannot lift it. |
| R47 | Q4 | The narrowed guard stays as frozen. Its limits are stated (no favourite below 2500 guarded at full weight; blend steps 0.011–0.016; rapid's 735 step), and its exact shape is set on FIDE's data. It changes no championship expectation (largest gaps 165 and 250). |
| R48 | Q5 | Moot under R44: interim ratings under rung 2 use today's K; T8.2's tolerance is unchanged. |
| R49 | Q6 | Rung 2's verdict wording: "RECOMMENDED NOW: ready for the shadow list today; it changes no official rating until the shadow year confirms calibration by level band on FIDE's data." Rapid and blitz keep R35's condition. |
| R50 | Q7–Q9 | SPEC-TABLE-FIT v1.2 sets the rules for the next yearly fit: only games since the last rule change that moved ratings (March 2024); a more flexible slope by level chosen on held-out log-loss (for example a piecewise-linear κ by 200-point band); a colour term by level if it improves held-out log-loss. Evidence: E16. No new table is fitted before submission; Freeze 3's v2 table is this year's. |
| R51 | Q10, Q11, Q14 | The paired trigger's false-alarm rate, R29's cap and ω's weak identification are stated as PROVISIONAL, to be set on FIDE's data. |
| R52 | Q12 | E3's Freeze-2 page becomes a static record of the 89 hashes as at freeze-2; stop regenerating its file list. |
| R53 | Q13 | As R42: after the 1 November check. |

## Freeze 3a: what changed, before any result was read

Recorded by the executor in Phase 0 of session ELO-7, on 2026-10-10 at about 20:30 UTC. It amends Freeze 3 (D-0011, part B), which stands except where this section says otherwise.

### Why

Two findings of the ELO-6 review needed a decision before any result is read, because after it either change would be a choice made after the fact (`docs/review/REDTEAM_v1_0.md`, addendum, ELO6-EXPLOIT-2 and ELO6-EXPLOIT-3). Under Freeze 3 a game not played was entered as `-`, which `tools/set_results.py` stores as "no result yet", so a single forfeit or withdrawal would have kept both events pending and every blank of §10 empty. And column (b), rung 2 with K × m, differed from column (a) on the 2025 event by 5.49 points on average, 4.80 of them from R32's factor m, while the v2 table at today's K differed by 1.94 [E16 §7]; R44 now withdraws R32, so the rung that §10 should measure is the v2 table with the narrowed guard at today's K.

### What changed

1. **A game not played (R43).** `tools/set_results.py` (a Freeze 2 and Freeze 3 file, changed as this record authorises) accepts the marker `unplayed` for a game not played, a forfeit, a withdrawal or a bye, stored in the game's result field and logged with its time of entry like a result; `-` keeps its meaning, no result yet. FIDE does not rate such a game: "Whether these occur because of forfeiture or any other reason, they are not counted" (§5.1 [V 1]). Every column excludes it, as Freeze 1's, Freeze 2's and Freeze 3's tools already exclude any game whose result is not 1-0, 1/2-1/2 or 0-1; it adds nothing to n in K × n ≤ 700 and nothing to the games counted. An event is complete when every game of rounds 1 to 11 has a result or the marker; its tables are printed only then, and the blanks only when both events are complete. The rule is tested on a synthetic event file kept apart from the 2026 files (`tests/fixtures/events/synthetic_double_round_robin.json`, `tests/test_compare_event_v3a.py`).
2. **Column (b′) (R44, R45).** "v2 table and narrowed guard at today's K": per player, the sum over the event's counted games of K × (score − expectation), with the expectation of column (b) (the v2 table's published entry at the game's level band with colour and draws, `params/table_fit_2026-10b.yaml`, and the narrowed guard, `params/guard_2026-10b.yaml`) and K that of column (a), today's K from the list in force reduced under K × n ≤ 700 (Layer 0), not multiplied by m; unrounded and rounded once. It is computed by Freeze 3's tool `tools/compare_event_v3.py`, unchanged, with the slope ratio switched off, through a new file, `tools/compare_event_v3a.py`: no new parameter. On the 2025 event it equals E16's "v2 table and the guard at today's K" for every player (mean |(b′) − (a)| 1.94, largest −4.30, 10 of 12 rounded changes differing) [E13] [E16 §7]. **(b′) is §10's main column.** Column (b), rung 2 with K × m, and column (b0), Freeze 2's, stay reported as pre-registered and labelled.
3. **E13.** The page `docs/evidence/E13_us-championship-2026-freeze-3.md` is now printed by a new script, `analysis/e13_us_championships_freeze3a.py`, which prints (a), (b′), (b) and (b0) side by side, the PILOT table, the blanks as redefined below, the completion rule and Freeze 3a's manifest. Freeze 3's page script, `analysis/e13_us_championships_freeze3.py`, is unchanged and used by the new one as a module (its file list and hashing); it is registered with check (a) as a module.
4. **The check.** Check (a) (`tools/checks/check_outputs.py`, the one file of the check, changed as this record authorises) compares the live Freeze-3a manifest, computed by the new E13 script, with the one this record holds, instead of D-0011's; a missing record now fails the check.
5. **The PILOT is unchanged**: rung 5 on top of (b), as Freeze 3 pre-registered it (reading 6).
6. **E3 (R52).** The Freeze-2 section of `docs/evidence/E3_us-championship-2026.md` is now a static record of the 89 hashes as they stood at the tag `freeze-2`, printed by a new script, `analysis/e3_freeze2_record.py`, which runs Freeze 2's page script `analysis/e3_us_championships.py` unchanged and refuses to print unless the record's manifest equals D-0010's (`64a60a37dccf7cb75a81bef356180c21d88d9b9c87ee5111b087d48e2bb0e632`). The rest of E3's page is generated as before.

No other frozen file changed. The executor verified, against the page at the tag `freeze-3`, that 45 of Freeze 3's 47 files keep their Freeze-3 hashes; the two that differ are the ones this record changes (`tools/set_results.py`, `tools/checks/check_outputs.py`). Of Freeze 2's 87 files, the same two differ from their hashes at the tag `freeze-2` and the other 85 are unchanged; Freeze 1's seven files are unchanged.

### What will be computed after the event, and nothing else

This list replaces items 1, 2 and 4 of D-0011 part B's list; items 3 and 5 stand.

1. **Results.** The results of rounds 1 to 11 of each event (132 games), entered once after the last round from the official page with `tools/set_results.py`, board by board: 1-0, 1/2-1/2 or 0-1, or `unplayed` for a game not played (a forfeit, a withdrawal, a bye), which is not counted (§5.1 [V 1]; SPEC-L0 R-05). Playoff games are not part of the comparison.
2. **The main table** (`tools/compare_event_v3a.py`, printed by E13), per player of each event: (a) the event's change under FIDE's rules, computed by Layer 0 (Freeze 1), with K reduced under K × n ≤ 700; **(b′)** rung 2 at today's K, as item 2 above defines it, the main column; (b) rung 2 v2 with K × m exactly as Freeze 3 pre-registered it, labelled "Freeze 3, K × m (R32, withdrawn)"; (b0) rung 2 exactly as Freeze 2 pre-registered it, labelled "first pre-registration, superseded"; each unrounded and rounded once, with (b′) − (a), (b) − (a) and (b0) − (a).
3. **The PILOT table**, printed separately and never in the main table: as D-0011 part B, item 3 (rung 5 on top of (b)).
4. **The blanks of the proposal's §10**, each printed by E13 from the two tables once both events are complete, over played games only, for each event:
   - `{{US26_*_GAMES}}`: the games counted, those with a result (games marked not played excluded);
   - `{{US26_*_MEAN_ABS_DIFF}}`: the mean of |(b′) − (a)|, unrounded, to two decimals, over the event's players who played at least one counted game;
   - `{{US26_*_MAX_DIFF}}`: the (b′) − (a) of largest absolute value, signed, unrounded, to two decimals;
   - `{{US26_*_N_DIFFER}}`: the number of those players whose rounded (b′) differs from their rounded (a), written "k of n";
   - `{{US26_*_B_MEAN_ABS_DIFF}}`, `{{US26_*_B_MAX_DIFF}}`, `{{US26_*_B_N_DIFFER}}`: the same three for (b), Freeze 3's column with K × m;
   - `{{US26_*_B0_MEAN_ABS_DIFF}}`, `{{US26_*_B0_MAX_DIFF}}`, `{{US26_*_B0_N_DIFFER}}`: the same three for (b0), the first pre-registration;
   - `{{US26_*_R5_GAMES}}` and `{{US26_*_R5_DIFF}}`: as D-0011 part B (the PILOT on (b));
   - `{{US26_*_L0_MATCH}}`: as D-0011 part B;
   - `{{US26_READING}}`: one paragraph, written after the event, that restates the blanks in words, names the three pre-registrations plainly (Freeze 2's (b0), superseded; Freeze 3's (b), with K × m, R32 since withdrawn; Freeze 3a's (b′), the main column), adds no number E13 does not print, and says that 132 games illustrate the rungs and cannot test them; it may point to §10's 2025 table, which E13 prints from the same definitions.
5. **Not computed on the event**: as D-0011 part B, item 5.

### The data cutoff, and the event's games

As D-0011 part B: every fit behind a number in the comparison uses games up to 30 September 2026, a cutoff enforced in code; Freeze 3a adds no fit and no parameter. No game of either 2026 championship has been read in this session; both event files hold the pairings and the October 2026 ratings and K, and every result is empty (0 of 66 each, E13).

### The time of the freeze, and the rounds completed

The official schedule, as D-0011 part B transcribed it from the Saint Louis Chess Club's official page (read on 9 and 10 October; rounds at "12:00" without a time zone, read as Saint Louis local time, UTC − 5): round 1 on 9 October; round 2 on 10 October at 17:00 UTC; round 3 on 11 October at 17:00 UTC; rounds 4 to 11 on 12, 14–17 and 19–21 October. The page was not opened again in this session, so that no result could be seen. This record is written at about 20:30 UTC on 10 October; the commit that merges it is tagged `freeze-3a`, and that commit's time is the freeze's time. **At that moment, by the schedule, one round of each event had been completed (round 1, 9 October), and round 2 had begun at 17:00 UTC, three and a half hours earlier; the schedule gives start times only, so round 2 may have finished or may still be in progress.** No result of any round was read.

### The scope

Freeze 3a covers Freeze 3's files (D-0011 part B, "The scope"), two of them changed as above, and the two files it adds: `tools/compare_event_v3a.py` and `analysis/e13_us_championships_freeze3a.py`. The synthetic event file and the tests stay outside it, as Freeze 3's tests do; so do `analysis/e3_freeze2_record.py` and E3's page, which produce no number of the comparison. Numbers of the proposal drawn from history and from the simulator may be updated until submission, provided no event game is read; prose may change until submission.

### The manifest

E13 prints the SHA-256 of each of the 51 entries (49 files and the two event files without their results) and their manifest, the SHA-256 of the lines "hash  file" in the order E13 prints them. At this record:

Freeze-3a manifest: `44954559b5b8609f70128bec71af642d7164bcec939441891fe70942a1667212` (51 entries)

Check (a) reruns E13 on every pull request and compares the live manifest with the one recorded above; a change to any frozen file therefore fails the check even after E13 is regenerated, until a new decision record supersedes this one. Freeze 3's manifest (`e84f0564153579dcd394381e96fd55d046a2fe9f903b2806e758008230463ff5`, D-0011) is superseded. The commit that merges this record is tagged `freeze-3a`.

## Where each ruling is applied

| # | In this session | Documents (Phase 1: proposal, annex, brief) |
|---|---|---|
| R43 | Phase 0: `tools/set_results.py`, `tools/compare_event_v3a.py`, the E13 script, check (a), the synthetic test | proposal §10; annex T8.10 |
| R44 | Phase 1: m removed from rung 2 in the documents and in the scripts that print rung-2 figures outside Freeze 3; every rung-2 figure restated at today's K from committed scripts; the simulator's rung-2 ledger rerun at today's K | proposal §1, §5, §8, §10, §13, §14; annex T1, T3, T4.4, T5, T7, T8, T10, T11; brief |
| R45 | Phase 0: column (b′), E13, Freeze 3a's manifest, the tag `freeze-3a` | proposal §10 (the main column; the 2025 table with (a), (b′), (b), (b0); the blanks) |
| R46 | — | annex T3.6, T8.2, T11; proposal §5, §15 |
| R47 | — | annex T3.6, T5 (P3, P4); proposal §5, §8 |
| R48 | — | annex T3.5, T8.2, T11 (§1.5.3 a); proposal §14 |
| R49 | — | proposal §1, §8; annex T8.10; brief |
| R50 | Phase 0: `docs/specs/SPEC-TABLE-FIT_v1_2.md` | annex T3.3, T7; proposal §8, §15 |
| R51 | — | annex T2.3a, T3.5, T6, T8.4, T8.9, T9.4, T9.5; proposal §5, §13 |
| R52 | Phase 0: `analysis/e3_freeze2_record.py`, E3's page | — |
| R53 | none before the 1 November check | — |

## Executor's readings where a ruling or the brief leaves a detail open

1. **R43: the marker.** It is the word `unplayed`, stored in the game's result field. There it is removed with every result when the event file is hashed for the freeze (`event_sha_without_results` in `analysis/e3_us_championships.py`), so entering it changes no manifest, and every tool of Freezes 1 to 3 already skips it, since each counts only 1-0, 1/2-1/2 and 0-1. Any game the official page shows as not played is entered with it, whatever score a forfeit awards on the page.
2. **R43: complete.** An event is complete when every game of rounds 1 to 11 in its event file has 1-0, 1/2-1/2, 0-1 or `unplayed`; the event files hold rounds 1 to 11 only. E3's frozen page script counts any entry as a result, so it treats the marker the same way; its tables, which Freeze 3 superseded, skip the game as every column does.
3. **R43: "§10 counts played games only."** `{{US26_*_GAMES}}` counts the games with a result. The means and counts of the blanks are taken over the players with at least one counted game: a player who played none has no change in any column, and with every player playing, as in 2025, these are D-0011's twelve players. K × n ≤ 700 counts played games, as Layer 0 does (§5.1 [V 1]).
4. **R45: "computed only from Freeze 3's frozen table and guard and Layer 0's K".** (b′) is Freeze 3's own computation of column (b) with the slope ratio switched off (`scaled=False` in `tools/compare_event_v3.py`'s `Rung2`), which is how E16 §7 computed "the v2 table and the guard at today's K"; the table's entries, the guard's code and Layer 0's K are Freeze 3's, unchanged. "New code in new files where possible": the column and the completion rule are in `tools/compare_event_v3a.py`, the page in `analysis/e13_us_championships_freeze3a.py`; the only Freeze 3 files changed are the results-entry tool and the check, which the brief names.
5. **R45: the blanks.** "The blanks are redefined for (b′)" (brief, Phase 1) is read as: the three main blanks now measure (b′); (b)'s three are renamed with the prefix B_ and kept; (b0)'s keep their names; `{{US26_READING}}` names three pre-registrations.
6. **The PILOT stays on (b).** R45 adds one column and the brief authorises changes "for unplayed games and the new column only", so rung 5 stays on top of (b), with K × m inside it, as Freeze 3 pre-registered it. A PILOT on (b′) would be a further column: for the architect.
7. **R45: the manifest.** Freeze 3a's manifest is Freeze 3's 47 files, two of them changed, the two new files and the two event files without their results: 51 entries. The synthetic event file and the tests are outside it, as Freeze 3's tests are.
8. **R52: the static record.** E3's page is printed by a new script that runs Freeze 2's page script unchanged and replaces only its Freeze-2 section by the 89 lines of the page at the tag `freeze-2`, held in the script and checked against D-0010's manifest. The frozen script's docstring still names the page as its output; the new script's docstring and `analysis/outputs.json` say which script prints it now.
9. **R50: SPEC-TABLE-FIT v1.2 is a new file.** Version 1.1 stays in place because Freeze 3's parameter file and scripts cite it, as D-0011 (reading 2) kept v1.0. To make "chosen on held-out log-loss" hold, v1.2 splits the test months into selection months, which choose the form, and later confirmation months, which test the chosen table and are not used to choose (REDTEAM_v1_0, ELO6-STAT-2); a candidate "improves" when the month-block interval of its log-loss difference lies below zero (annex T8.2's "better"); the candidates fixed now are v1.1's exponential slope, a piecewise-linear κ with knots every 200 points from 1500 to 2700, and a colour term linear in the level.
10. **R44: m in frozen files.** The frozen files that still carry m stay as frozen: `params/table_fit_2026-10b.yaml` (its `k_scale` and "K scaled by m"), E11's and E12's pages and scripts, and column (b) of `tools/compare_event_v3.py`. Outside them, rung 2 has no m: the documents and the scripts that are not frozen drop it in Phase 1, and column (b) keeps it, labelled.
11. **R46: the statement.** The guard is imposed and lifted by one test, rule (i) read strictly: the guard lapses in a time control only when the 95 % player-clustered interval of the favourite's residual in the farming region lies inside ±0.01, on FIDE's games, where the region holds enough games for that interval to fit (from about 1,600 games in standard, 2,400 in blitz and 5,300 in rapid at a centred residual [E16 §6]). The broadcast sample, 827 to 1,020 region games, cannot lift it. The weaker reading is no longer offered.
12. **R47: the limits.** Stated from E12 and E16: the region guards no favourite rated below 2500 and reaches full weight only from 2575 (193 of 827 standard region games at full weight) [E16 §6]; inside the blend the guarded table steps by 0.011 to 0.016 for a one-point move, above R24's 0.01; at the 735-point stop it steps by 0.080 in rapid (0.031 in blitz, 0.004 in standard) [E12 §2]; no pairing of either 2026 field lies in the region (largest gaps 165 and 250) [E12 §7].
13. **R49: the verdict.** Rung 2's verdict in standard reads as R49 words it; rapid and blitz keep R35's condition (re-tested on FIDE's games before adoption there, whatever broadcast games show).
14. **R51: PROVISIONAL.** The paired trigger's false-alarm rate (R31, R40; unmeasurable in the simulator, where κ is fixed), R29's cap (127, 128 and 133 from the simulator only) and ω (E15: 2.0 and 4.0 differ by 0.000001 nats a game) are stated as PROVISIONAL, to be set on FIDE's data.
15. **The rounds completed.** Taken from the official schedule as D-0011 part B transcribed it, without opening the page again, so that no result could be seen.

## For the architect (decided conservatively, recorded here)

- Reading 6: the PILOT stays on (b), with K × m inside it, as pre-registered; rebasing it on (b′) would add a column after this record.
- Reading 3: the blanks' means and counts exclude a player who played no counted game.
- Reading 9: SPEC-TABLE-FIT v1.2's selection and confirmation months, and its candidate forms.

## Consequences

- After the last round the operator enters the results, with `unplayed` for any game not played, regenerates E13 with `python3 analysis/e13_us_championships_freeze3a.py` and E3 with `python3 analysis/e3_freeze2_record.py` once, and fills the blanks of the proposal's §10 from E13; after the list that rates the events, `{{US26_*_L0_MATCH}}` is filled from FIDE's published calculations.
- D-0011 part B stands except where this record amends it: items 1, 2 and 4 of its list, and the manifest the check compares. D-0010 stays the record of the first pre-registration.
- R32 is withdrawn: D-0011's reading 7 no longer applies to rung 2, and R32's ratio stays only in Freeze 3's files and in column (b).
- No change to `src/layer0/` before the comparison and the 1 November check (R21, R42, R53). Any change to a file of Freeze 3a before the comparison runs is a new decision, in a new record that says what changed and why and updates the check.
