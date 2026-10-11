# D-0016 — Rulings on ELO-8's questions: the forecast test's reading confirmed (Freeze 3d), the self-calibrating tables' rules, name matching and the aggregates

Date: 2026-10-11 (UTC; recorded at about 10:15) · Session: ELO-9, Phase 0 · Status: DECIDED — the architect's rulings R66 to R73, given by Web Claude in the ELO-9 brief and recorded by the executor before any result of either 2026 championship was read, with Freeze 3d, which extends Freeze 3c (`docs/decisions/D-0015_forecast-test-reading.md`) and is tagged `freeze-3d`. R68 to R72 are applied in the pull request that follows this record (Phase 0b), as D-0014's part B followed its part A; what that pull request does is fixed below, before it runs.

## Context

The ELO-8 close-out (the operator's files, not in the repository) left eight open questions, Q1 to Q8. The ELO-9 brief answers them with the rulings R66 to R73. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed below and marked as such; a later record can overrule a reading without reopening the ruling.

The brief also orders, for the whole session:

- Freeze 1, 2, 3, 3a, 3b and 3c files are untouched, except where this record authorises it. **It authorises no change: no frozen file changes.** Freeze 3d adds new files only.
- No result of the 2026 U.S. Championships is read, entered or looked up.
- No game data from a source whose licence or terms do not allow this use; The Week in Chess, ChessBase and similar are excluded unless the operator supplies written permission, and contacting anyone remains forbidden.
- FIDE's site is fetched politely: robots.txt respected, at least two seconds between requests, every page cached once and never fetched again.

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## The rulings

The text of each ruling is the brief's, transcribed.

| # | Answers | Ruling (the brief's text) |
|---|---|---|
| R66 | Q1 | D-0015 confirmed: the Brier difference is the primary endpoint, read with the interval over games; every log-loss line is read with the crossed interval (games × players). |
| R67 | Q2 | Confirmed: (b) − (a) is not fixed by the pairings, because m multiplies the score; E13's bounds stand. |
| R68 | Q3 | Choosing a table's form needs 24 months of games after the last rule change that moved ratings; refitting the parameters of the chosen form needs at least 10 months. State that the 10-month figure was set after the counts were known. |
| R69 | Q4 | After a rule change that moved ratings, the QC may lift the yearly caps for the first refit only, by a recorded decision; otherwise they hold. E18 adds a sensitivity line with 2026's caps lifted; E19's headline is unchanged. |
| R70 | Q5 | Name matching of 2020–2023 broadcast games is allowed only as a labelled sensitivity: a unique match on name, federation and an Elo tag within 10 points of the FIDE list in force; unmatched games are dropped. If it yields tables for 2023 or 2024, report the three-way test and E19 with them beside the headline, which keeps R65's sample rule. |
| R71 | Q6 | R59: print both readings; the headline uses the by-band one; both are called estimates, not bounds. |
| R72 | Q7, founder default | The committed aggregates keep only each player's difference between the two systems; FIDE's published ratings stay in the local cache (gitignored). The appendix keeps the October 2026 ratings of the 100 players. |
| R73 | Q8 | Publication outside the repository remains the operator's decision. |

## Where each ruling is applied

| # | Where |
|---|---|
| R66 | Phase 0, this record: Freeze 3d (below): `tools/compare_event_v3d.py`, `analysis/e13_us_championships_freeze3d.py`, `tools/checks/check_freeze3d.py`; E13; the proposal's §10 (how the intervals are read, and the blanks R66 adds); annex T8.10 |
| R67 | No change: E13 keeps printing, for (b) − (a), only its values with no point scored and with every game won (D-0014, reading 7) |
| R68 | Phase 0b: SPEC-SELFCAL v1.2 (§5, §13) states the rule and that the 10-month figure was set after the counts were known; E18 and E19 print, beside the headline, the 2026 table in the form R68 keeps (reading 6); the proposal's Appendix H and annex T3.7 say so |
| R69 | Phase 0b: SPEC-SELFCAL v1.2 §6; E18 adds the three-way test with 2026's caps lifted, labelled a sensitivity; E19's headline is unchanged |
| R70 | Phase 0b: a committed script counts, in the broadcast archive's files of 2020 to 2023, the games without both FIDE IDs and the tags R70's match needs, and applies the match; E18 prints the counts and what the match yields (reading 11) |
| R71 | Phase 0b: E19 §3 and its summary, Appendix H, annex T8.10: R59's two corrections printed side by side, the headline sentence using the one by level band, both called estimates |
| R72 | Phase 0b: E19's extraction writes, for every list, each player's difference between the two systems only, and the two published series to the local cache under `data/` (gitignored); E19 §2 and Appendix H keep the October 2026 ratings of the 100 players |
| R73 | Nothing is published outside the repository; E19 and Appendix H stay where they are |

## Freeze 3d: what is added before any result is read

Recorded by the executor in Phase 0 of session ELO-9, on 2026-10-11 at about 10:15 UTC. It extends Freeze 3c (D-0015), which stands unchanged: no file of Freeze 1, 2, 3, 3a, 3b or 3c is modified.

**Why.** D-0015's reading 3 makes the interval over games "the one to read for every measure and scope". The ELO-8 review's simulation (`analysis/OUTPUT_ELO8_review.md`) found that for the log-loss, which is skewed, the interval over games covered the true mean in 0.83 of 200 simulated events on the 2025 pairings and the crossed interval over players in 0.94; for the Brier difference, 0.96 and 0.99. R66 therefore keeps the primary endpoint and its interval over games, and reads every log-loss line with the crossed interval. Freeze 3c prints the crossed interval only for R54's measures; the log-loss with one draw model and the rounds 3–11 line carry an interval over games alone, or R54's interval over players.

**What is added.**

1. **The crossed interval of every log-loss line.** `tools/compare_event_v3d.py` (new) computes, with Freeze 3c's crossed bootstrap unchanged (`tools/compare_event_v3c.py`, `crossed`: within each event the players drawn with replacement, each game weighted by the product of its two players' multiplicities; 2,000 resamples, seed 20261009), the crossed interval of: (a)'s and (b′)'s mean log-loss and their difference (equal to Freeze 3c's, since the bootstrap's draws do not depend on the measure); the log-loss difference with one draw model and (a)'s mean under it; and the rounds 3–11 log-loss difference. Per event and pooled, over the counted games, once both events are complete.
2. **E13.** The page `docs/evidence/E13_us-championship-2026-freeze-3.md` is now printed by `analysis/e13_us_championships_freeze3d.py` (new), which runs Freeze 3c's page script unchanged and adds: R66's reading; every log-loss line with its crossed interval on 2025's games (in sample; the log-loss difference with one draw model is −0.0197, crossed −0.1212 to +0.0468, and rounds 3–11's −0.0664, crossed −0.2658 to +0.0542 [E13]); the same table for the 2026 events once both are complete; the blanks below; and Freeze 3d's manifest.
3. **The blanks of the proposal's §10**, printed by E13 once both events are complete, for * = OPEN, WOMEN and POOLED: `{{US26_*_LL_A_CROSSED}}` and `{{US26_*_LL_BP_CROSSED}}` (the crossed intervals of (a)'s and (b′)'s mean log-loss), `{{US26_*_LL_DIFF_SHARED_CROSSED}}` (the log-loss difference with one draw model) and `{{US26_*_R3_LL_DIFF_CROSSED}}` (rounds 3–11). `{{US26_*_LL_DIFF_CROSSED}}` is D-0015's.
4. **The check.** A new check (a‴), `tools/checks/check_freeze3d.py`, run by a new step of the automated check (`.github/workflows/check.yml`), compares Freeze 3d's live manifest with the one this record holds; a missing record or manifest fails it. Checks (a), (a′) and (a″) still compare Freeze 3a's, 3b's and 3c's manifests with D-0012's, D-0014's and D-0015's.
5. **Tests.** `tests/test_compare_event_v3d.py`, on the synthetic event and the 2025 event, never on a 2026 result; the 2026 event files hold no result.

**How the test is read, after this record.**

- **The primary endpoint** stands as D-0015 fixes it: the pooled Brier difference (b′) − (a), with its interval over games, read with one of D-0015's three sentences. Every other Brier line is read with its interval over games.
- **Every log-loss line** is read with its crossed interval over players: (a)'s and (b′)'s means, their difference, the difference with one draw model and the rounds 3–11 difference, per event and pooled. The interval over games is printed beside it. For the log-loss lines this supersedes D-0015's "the interval over games is the one to read for every measure"; nothing else of D-0015 changes.
- **R54's interval over players** stays as Freeze 3b computes it, labelled "narrower by construction, not a test".
- **`{{US26_READING}}`** quotes, with every log-loss figure it states, the crossed interval.

### What will be computed after the event, and nothing else

D-0015's list stands, with the crossed intervals of item 1 and the blanks of item 3 added. Nothing else is computed on the event.

### The time of the freeze, and the rounds completed

The official schedule, as D-0011 part B transcribed it from the Saint Louis Chess Club's official page (read on 10 October at about 14:35 UTC for the schedule only; rounds at "12:00" without a time zone, read as Saint Louis local time, UTC − 5): round 1 on 9 October; round 2 on 10 October at 17:00 UTC; round 3 on 11 October at 17:00 UTC; rounds 4 to 11 on 12, 14–17 and 19–21 October. The page was not opened in this session. This record is written at about 10:15 UTC on 11 October; the commit that merges it is tagged `freeze-3d`, and that commit's time is the freeze's time. **At that moment, by the schedule, two rounds of each event had been played (round 1 on 9 October, round 2 begun at 17:00 UTC on 10 October), and round 3 was scheduled to start at 17:00 UTC on 11 October, about seven hours later.** No result of any round has been read in this session.

### The scope

Freeze 3d covers Freeze 3c's 59 entries (D-0015), unchanged, and the three files it adds: `tools/compare_event_v3d.py`, `analysis/e13_us_championships_freeze3d.py` and `tools/checks/check_freeze3d.py`. The tests stay outside it, as before; so does the workflow file that runs the checks.

### The manifest

E13 prints the SHA-256 of each of the 62 entries (60 files and the two event files without their results) and their manifest, the SHA-256 of the lines "hash  file" in the order E13 prints them. At this record:

Freeze-3d manifest: `eee2a50b1a5db3ceab6972ab6118c12bd54bfdc9b775cf42eac4a18db0498603` (62 entries)

A change to any frozen file fails check (a‴) until a new decision record supersedes this one.

## Executor's readings where a ruling leaves a detail open

1. **R66: "every log-loss line".** Each log-loss mean or difference that E13 prints for the 2026 events: (a)'s and (b′)'s means and their difference (R54), the difference with one draw model (D-0015, with (a)'s mean under it), and the rounds 3–11 difference (D-0015); per event and pooled.
2. **R66: "the crossed interval (games × players)".** D-0015's crossed interval over players, in which each game is weighted by the product of its two players' draws, so that the bootstrap crosses the games with the players who play them; it is the interval the ELO-8 review simulated (coverage 0.94 for the log-loss). No new kind of interval is introduced.
3. **R66: "read with".** The interval quoted with each log-loss figure in `{{US26_READING}}`; the interval over games stays printed beside it. Every Brier line, not only the primary endpoint, is read with its interval over games, as D-0015's reading 3 has it: R66 changes the log-loss lines only.
4. **R66: new files.** Two log-loss lines had no crossed interval, so Freeze 3d adds the computation in new files before any result is read, as Freeze 3c did; no file of an earlier freeze changes.
5. **R67.** No file changes.
6. **R68: when it applies.** The rule governs every table fitted from this record on, the next being 2027's. The 2026 table, whose form was chosen under SPEC-SELFCAL v1.1 with the 10-month figure before this ruling, stays in E18's headline and E19's (R69: "E19's headline is unchanged"), so that no table is changed after its result was seen (R65: the method never changes because of results). E18 and E19 print, beside the headline, the 2026 table in the form R68 keeps (form E with the draw tail, v1.1's form for standard, refitted on the 2026 window's 22 months within the caps), labelled "R68 applied to 2026". If the architect means R68 to apply to 2026, that line becomes the headline and no new computation is needed. For the architect.
7. **R68: counting the months.** "24 months of games after the last rule change" counts the window's months from the first list after the change (March 2024, SPEC-SELFCAL W2). A choice uses the window's last 12 months as test months (six to select, six to confirm, as SPEC-TABLE-FIT v1.2), so at least 12 months of training precede the first selection month; a window of 10 to 23 months refits the parameters of the form in force without a choice; a window under 10 months gives no table (W4). The 2025 window holds exactly 10 months and the 2026 window 22; the first window that may choose a form is 2027's (2024-03 to 2026-12, 34 months).
8. **R68: the statement.** "The 10-month figure was set after the counts were known" is printed in SPEC-SELFCAL v1.2 (§5, §13), E18 (§1, §2, §5) and Appendix H: SPEC-SELFCAL v1.0 set it once E18 §1's counts had fixed the windows at 10 and 22 months, and before any table was fitted. The first table, 2025's, exists only because of it.
9. **R69: "the first refit".** The first table fitted with a predecessor after the change: 2026's (2025's is the first fit and has no caps, SPEC-SELFCAL §6). No decision lifts the caps, so they hold in E18's tables and in E19.
10. **R69: the sensitivity line.** E18's three-way test with the 2026 table refitted without caps in its chosen form (form P with the colour term by level, no tail; E18 §2's "2026 without caps"): (3) − (2) and (3) − (1), log-loss and Brier, with their month-block intervals, labelled "sensitivity: 2026's caps lifted (R69), not the headline". E19 is not rerun with it.
11. **R70: the match.** Name: the PGN's White or Black tag; federation: a tag naming the player's federation; Elo tag: WhiteElo or BlackElo; the FIDE list in force: the standard list E2 reads for the game (SPEC-SELFCAL §2). A player matches when exactly one player on that list has the same name, normalised to letters, the same federation and a rating within 10 points of the Elo tag; a game counts when both players match; every other game is dropped. Before writing this record the executor counted the tags in the archive's files: **no game of 2020 to 2023 carries a federation tag**, or any tag naming a country; the first such tags (WhiteCountry, BlackCountry) appear in the file of April 2026. If the committed count confirms it, no game can match, every game is dropped and no table for 2023 or 2024 results; E18 says so, and the three-way test and E19 gain no line. No looser match (name and Elo tag without federation) is tried: R70 allows none. For the architect.
12. **R71.** E19's headline sentence gives +11.9 (by level band) as R59's estimate, with +11.2 (by band and 50-point gap) beside it; "bound" is replaced by "estimate" wherever a document names R59's correction; the aggregate's field names stay.
13. **R72: which aggregates.** E19's (`analysis/aggregates/E19_top100_selfcal.json`) holds FIDE's published rating of each of the 100 players on 82 lists (8,200 ratings) beside the self-calibrating one; it will hold, per list, only each player's difference, with the October 2026 ratings (FIDE's and the self-calibrating ones) for E19 §2 and Appendix H. E17's aggregate holds the October 2026 ratings and differences only, and no change is needed. The published series goes to `data/` (gitignored), where the deferred video session can read it.
14. **R72: git history.** The aggregate as committed in session ELO-8 stays in the public repository's history; removing it would rewrite `main`, which the merge rule forbids. For the operator.
15. **R73.** Nothing is posted or sent; E19 and Appendix H stay in the repository with their names and banners.
16. **The rounds completed** are taken from the official schedule as D-0011 part B transcribed it, without opening the page.

## For the architect (decided conservatively, recorded here)

- Reading 6: R68 applies from 2027; the 2026 table stays in the headlines, with the table R68 keeps beside them.
- Reading 7: the 24 months are counted as the window's months, test months included.
- Reading 11: the archive's 2020–2023 games carry no federation tag, so R70's match, as ruled, matches none.
- Reading 14: the published series remains in the repository's history.

## Consequences

- After the last round the operator enters the results as D-0013 reads §5.1, regenerates E13 with `.venv/bin/python analysis/e13_us_championships_freeze3d.py` and E3 with `.venv/bin/python analysis/e3_freeze2_record.py` once, and fills the blanks of the proposal's §10 from E13, the new ones included; `{{US26_*_L0_MATCH}}` follows FIDE's published calculations after the 1 November list.
- D-0015 stands except where reading 3 above supersedes its reading 3 for the log-loss lines; D-0014, D-0013 and D-0012 stand.
- No change to `src/layer0/` before the comparison and the 1 November check (R21, R42, R53).
