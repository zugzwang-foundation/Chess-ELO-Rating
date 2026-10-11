# D-0017 — Rulings on the greats' replay and data: the rounding before July 2014, politeness, OlimpBase, git history and test fixtures

Date: 2026-10-11 (UTC; recorded at about 14:00) · Session: ELO-9, Phase 3 · Status: DECIDED — the architect's rulings R74 to R79, given by Web Claude in the ELO-9 brief's Addendum 1 while FIDE's per-player calculations for the greats' replay were still being fetched, and recorded by the executor before the full replay ran. No result of either 2026 championship was read. No frozen file changes.

## Context

During Phase 3 the replay of the greats (`docs/specs/SPEC-GREATS_v1_0.md` §6) ran on the pages fetched so far, and the executor reported, among other things, that the reading of the rounding fixed in the rules record before FIDE's pages were seen (`docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md` §5: the period's change rounded with 0.5 away from zero on the lists before July 2014, where the 2007 and 2010 texts have no rounding clause) reproduced 27 of the 49 half-point periods then seen, against 44 for 0.5 towards +infinity. The addendum answers that report and five other points. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed below and marked as such.

## The rulings

The text of each ruling is the addendum's, transcribed.

| # | Ruling (the addendum's text) |
|---|---|
| R74 | Rounding before July 2014. The rules record's reading (half points away from zero) was fixed before FIDE's pages were seen, and the pages contradict it: towards +∞ reproduces 44 of 49 half-point periods, away from zero 27. Layer 0's job is to reproduce FIDE's arithmetic. Adopt "towards +∞" (the 2014 text read literally) for every version before July 2014, as finding F-H09 in SPEC-L0. Disclose the counts under both readings, and that the switch was made after seeing partial pages, before the full replay. Periods neither reading reproduces stay thin and carry FIDE's change. Report the number of thin periods under both readings. Rung 2's comparison is unaffected either way. |
| R75 | Politeness slips: recorded as you did; the fixes stand. Keep at least 4 s between requests to ratings.fide.com and at least 8 s to the Internet Archive, measured across runs. State both slips in DATA-PROBE, E20's data section and the close-out. |
| R76 | R70 found no federation tags in 2020–2023, so no match and no table: accepted. Do not relax the rule. |
| R77 | OlimpBase (non-commercial terms). As with R72, the repository keeps only derived figures (ranks, dominance gaps, differences between systems), with attribution; OlimpBase's series stay in the gitignored cache. Quote OlimpBase's terms verbatim in DATA-PROBE. Credit OlimpBase on every appendix table that uses it. |
| R78 | Do not rewrite git history. It still holds ELO-8's FIDE series from before PR #52, and rewriting would break the freeze tags. Record this in the close-out. |
| R79 | Test fixtures from FIDE's calculation pages: commit only a small sample, chosen by a fixed rule (at most 30 player-periods). Include the first period of each rules version and the periods either side of 1 July 2009 and of 1 July 2014. The full reproduction runs locally from the gitignored cache; commit only its counts. |

## Where each ruling is applied

| # | Where |
|---|---|
| R74 | `src/layer0_greats/` (the period's change on a list before July 2014 rounded with 0.5 towards +infinity; the reading away from zero kept beside it for the test); `docs/specs/SPEC-L0_fide-reference-engine_v1_3.md` §11, finding F-H09; the rules record's §5; E20 §4.2 and §4.3 (the counts under both readings, the thin periods under both, the order of events); `tests/test_layer0_greats.py` with fixture F-G06 |
| R75 | `tools/data/fetch_probe.py` (at least four seconds to ratings.fide.com and eight to web.archive.org, measured from the last request any of the session's manifests records to the host); `tools/data/fetch_greats_calculations.py` (the same, across every manifest); `docs/research/DATA-PROBE_greats.md` §1 and E20 §1 (both slips and the smallest gaps since the fixes); the close-out |
| R76 | No change: E18's R70 line stands (`docs/specs/SPEC-SELFCAL_v1_2.md`, R70) |
| R77 | Only derived figures from OlimpBase's transcription are committed (ranks, counts, dominance gaps, and per player the peak of SPEC-GREATS §4 with its lists; reading 3 below), with attribution; OlimpBase's lists stay under `data/` (gitignored); DATA-PROBE §3 quotes OlimpBase's copyright policy and footer whole; every table of E20 and of the proposal's appendix that uses OlimpBase's lists carries a line crediting it |
| R78 | No change to git history; recorded in the close-out |
| R79 | `tools/data/assemble_greats_fixtures.py` and `tests/fixtures/fide_greats/published_periods.json`: fourteen cases chosen by a fixed rule, at most 30 player-periods; the replay's aggregate commits counts, and per player only the lists of the thin periods SPEC-GREATS §6 asks E20 to list, with their causes |

## Executor's readings where a ruling leaves a detail open

1. **R74, the boundary.** "Every version before July 2014" is applied to the lists published before July 2014: rounding is applied to a period's change when a list is published, and `src/layer0_history/` dates its rounding by the list in the same way. From the list of July 2014 the 2014 clause keeps the reading the rules record gave it, 0.5 away from zero, as E17 found FIDE's lists of 2020 and 2021 apply the same words of 2017.
2. **R74, beyond its scope.** The replay also reports, for the architect's information only, a third run with 0.5 towards +infinity on every list of the window (to December 2019), with its thin periods, and how FIDE's lists from July 2014 rounded each negative half point, by year, because FIDE's pages from July 2014 do not follow the reading kept there throughout (E20 §4.2 gives the counts). No reading beyond R74's scope is adopted; the question is listed in the close-out.
3. **R77, the peak.** SPEC-GREATS §4, fixed before any analysis, commits for each player the peak published rating and the lists on which it stood. The executor reads a peak as a derived figure (one value, the maximum of a series that stays in the cache), committed with attribution where it comes from OlimpBase's transcription; no series, list or per-list rating from OlimpBase is committed.
4. **R79, the sample.** The fourteen cases are those listed in the assembler's docstring: one per rule the module transcribes (the 350-point rule, the 400-point rule with and without FIDE's mark, K 15, the 2014 cap), F-G06 for R74, the first period with a tournament of each version (2007, 2009, 2014, 2017), and the periods holding the latest start before and the earliest start on or after 1 July 2009 and 1 July 2014, each among the periods Layer 0 reproduces.

## Consequences

- Layer 0's reading of the rounding on the lists before July 2014 changes after partial pages were seen and before the full replay; E20 says so, and gives the counts and the thin periods under both readings.
- No frozen file changes; SPEC-L0 moves to v1.3 for F-H09 and changes no rule of §3.
