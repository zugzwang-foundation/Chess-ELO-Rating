# D-0015 — How the forecast test is read: the primary endpoint, the intervals, two secondary lines, and the 24 games (Freeze 3c)

Date: 2026-10-11 (UTC; recorded at about 07:55) · Session: ELO-8, Phase 6 · Status: DECIDED — the executor's readings under ruling R54 (`docs/decisions/D-0014_forecast-test-and-rulings.md`, part A), which they extend and do not reopen, recorded before any result of either 2026 championship was read, after the session's red-team review (`docs/review/REDTEAM_v1_0.md`, ELO-8 addendum: ELO8-STAT-1, ELO8-STAT-2, ELO8-QC-1), with Freeze 3c, which extends Freeze 3b and is tagged `freeze-3c`. D-0014 provides that "a later record can overrule a reading without reopening the ruling"; the architect may overrule these the same way.

## Context

R54 pre-registers a forecast test: for every counted game of both championships, the three-outcome log-loss and the expected-score Brier score of column (a) and column (b′), "the two means and their difference, with bootstrap 95 % intervals over games and over players, per event and pooled", reported whatever it shows. The review found three gaps that would leave choices to be made after the results:

- **The interval over players is narrower by construction** (ELO8-STAT-1). In a round robin every game belongs to two players; resampling players and counting each game for both treats twelve overlapping clusters as independent. On 2025's games the interval over players of the log-loss difference (−0.0942 to −0.0038) is half as wide as the interval over games (−0.1475 to +0.0250), and only it excludes zero [E13].
- **Column (a)'s draw share tilts the log-loss towards (b′)** (ELO8-STAT-2). (a) splits FIDE's expectation with the level band's draw rate, which ignores the gap; (b′) uses the v2 model's draw probability, which falls as the gap grows. From the pairings alone, if (b′)'s forecasts were exactly right, its expected log-loss advantage would be 0.0358 nats a game in the open event and 0.0327 in the women's, of which the draw split contributes 0.0185 and 0.0208; the mean draw probability in the women's event is 0.374 under (a) and 0.450 under (b′) [E13]. D-0014's reading 1 called the draw share "decided conservatively"; it is not, and that wording is withdrawn.
- **Nothing names a primary endpoint or how the result will be read** (ELO8-QC-1): two measures, three scopes and two intervals make twelve intervals, and the reading would be written by hand after the results. And by the schedule, rounds 1 and 2, 24 of the 132 games, were played before Freeze 3b.

## The readings

1. **The primary endpoint** is the pooled expected-score Brier difference, (b′) − (a), over the counted games of both events, with its percentile bootstrap 95 % interval over games (games resampled within each event; 2,000 resamples, seed 20261009), as Freeze 3b computes it. The Brier score compares the two columns' expectations alone, with no draw model; it is the measure R54's comparison of the two expectations needs.
2. **It is read with one of three sentences, fixed now**, the numbers filled from E13 (d the difference, lo and hi its interval):
   - interval below zero: "On the 2026 championships the main column's expectations forecast the results better than FIDE's: the Brier score is lower by d a game (lo to hi over games).";
   - interval above zero: "On the 2026 championships FIDE's expectations forecast the results better than the main column's: the Brier score is higher by d a game (lo to hi over games).";
   - interval across zero: "The 2026 championships cannot tell the two columns' expectations apart: the Brier difference is d a game (lo to hi over games), an interval that includes zero."
   The sentence opens the forecast test's part of `{{US26_READING}}`, followed by D-0014's statement that the sample is small and the result could go either way.
3. **The intervals.** The interval over games is the one to read for every measure and scope. R54's interval over players is still reported as Freeze 3b computes it, labelled "narrower by construction: each game counts for both its players; not a test". Beside it, a **crossed interval over players** is reported: in each event the players are drawn with replacement and each game is weighted by the product of its two players' multiplicities, 2,000 resamples, seed 20261009; it is the players-level interval to read. On 2025's games it is wider than the interval over games (log-loss difference −0.2111 to +0.0514) [E13].
4. **Two secondary lines, which are not endpoints:**
   - **one draw model**: the log-loss with column (a)'s expectation split by (b′)'s own draw probability, so that the log-loss compares the two expectations under one draw model, reported beside the log-loss as frozen;
   - **rounds 3 to 11 only**: every measure on the games of rounds 3 to 11, which by the schedule were all played after Freeze 3b and this record.
5. **What the pairings fix about the test** is printed now in E13: with every game played and (b′)'s forecasts exactly right, the expected log-loss advantage of (b′), as frozen and with one draw model, the expected Brier advantage, (E_a − E_b′)² a game (0.00215 in the open event, 0.00237 in the women's), and each column's mean draw probability [E13]. These benchmarks are fixed by the pairings and the October ratings.
6. **Disclosure.** By the official schedule, as D-0011 part B transcribed it, rounds 1 and 2 (24 of the 132 games) were played before Freeze 3b (06:21:57 UTC on 11 October). R54 came in the architect's brief of 11 October, which carries a date but no time. The executor has read no result of any round; this record cannot say whether anyone else involved in the brief had seen one. That is why the rounds 3–11 line exists. §10 says so.
7. **What does not change.** R54's two measures, their means and differences, the intervals over games and over players as Freeze 3b computes them, the scopes, the draw rates and the statement made in advance all stand; no file of Freeze 1, 2, 3, 3a or 3b changes.

## Freeze 3c

- **The files it adds** to Freeze 3b's (D-0014, part A), new code in new files: `tools/compare_event_v3c.py` (the primary endpoint and its sentences, the crossed interval, the two secondary lines, the benchmarks), `analysis/e13_us_championships_freeze3c.py` (which now prints E13: it runs Freeze 3b's page script unchanged and adds this record's sections at fixed places), and `tools/checks/check_freeze3c.py` (check (a″), a new step of the automated check). The tests (`tests/test_compare_event_v3c.py`) stay outside it, as before.
- **The checks.** Check (a) still compares Freeze 3a's manifest with D-0012's and check (a′) Freeze 3b's with D-0014's; check (a″) compares Freeze 3c's with the one below.
- **The blanks of §10** gain: `{{US26_PRIMARY}}`, the sentence of reading 2 with its numbers; and, for * = OPEN, WOMEN and POOLED, `{{US26_*_LL_DIFF_CROSSED}}` and `{{US26_*_BRIER_DIFF_CROSSED}}` (the crossed intervals), `{{US26_*_LL_DIFF_SHARED}}` (the log-loss difference with one draw model, with its interval over games), and `{{US26_*_R3_LL_DIFF}}` and `{{US26_*_R3_BRIER_DIFF}}` (rounds 3 to 11), each printed by E13 once both events are complete.

### The time of the freeze, and the rounds completed

Recorded at about 07:55 UTC on 11 October 2026; the commit that merges it is tagged `freeze-3c`, and that commit's time is the freeze's time. By the official schedule, as D-0011 part B transcribed it (the page has not been opened in this session), rounds 1 and 2 had been played and round 3 starts at 17:00 UTC on 11 October. No result of any round has been read.

### The manifest

E13 prints the SHA-256 of each of the 59 entries (Freeze 3b's 56 and the three files above) and their manifest. At this record:

Freeze-3c manifest: `4bdb2c98e71e8c28dd18da0998229942a2bb24161f80572173f0ce98f970f35b` (59 entries)

A change to any frozen file fails check (a″) until a new decision record supersedes this one.
