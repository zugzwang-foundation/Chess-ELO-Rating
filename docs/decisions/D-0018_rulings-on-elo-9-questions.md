# D-0018 — Rulings on ELO-9's questions: the greats' rounding, the backward table, data terms and housekeeping

Date: 2026-10-11 (UTC; recorded at about 20:00; the brief is dated 12 October) · Session: ELO-10, Phase 0 · Status: DECIDED — the architect's rulings R80 to R89, given by Web Claude in the ELO-10 brief and recorded by the executor before any change they govern. R83, R84, R85 and R89 are founder decisions. No result of either 2026 championship was read. No frozen file changes.

## Context

The ELO-9 close-out (the operator's files, not in the repository) left seven open questions, Q1 to Q7: the greats' rounding from July 2014 and the list of January 2009, the backward table's headline, ties in the selection, the data terms, R68's time of effect, git history and one list on which two FIDE sources disagree. The ELO-HANDOVER close-out (also the operator's) added the narrowed guard's two labels (H3 in the brief), statements that lack a NOT VERIFIED label (H4) and the executor's readings recorded "for the architect" and not yet ruled on (§10, item 8 in the brief); and D-0005 lists one founder item as still open, the repository's name and visibility ("revisit before v1.0?"). The ELO-10 brief answers them with the rulings R80 to R89. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed below and marked as such; a later record can overrule a reading without reopening the ruling.

The brief also orders, for the whole session:

- Freezes 1, 2, 3, 3a, 3b, 3c and 3d, their tags and their files never change. Freeze 2's files are those E3 lists, which no live check covers: the rule alone protects them. A correction a frozen file would need is recorded here instead (below).
- No result of the 2026 U.S. Championships is read, entered or looked up.
- Nothing is fetched: no request to FIDE's site, the Internet Archive, OlimpBase or any other source; the work runs from the local cache only.
- Git history is not rewritten; `src/layer0/` (Freeze 1; the 1 November check, R21, R42, R53) and `src/layer0_history/` do not change.
- Records are not edited: decision records, `docs/review/REDTEAM_v0_*.md`, and any page whose generator is frozen.

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## The rulings

The text of each ruling is the brief's, transcribed: the brief's line breaks within a sentence are not kept, and its lists are set as lists.

### R80 (ELO-9 Q1)

> Rounding of a period's change on FIDE's lists, 2008-2019.
>
> (i) D-0018 supersedes D-0017's description of the 2007 and 2010 texts as having "no rounding clause": the 2003, 2007 and 2010 texts round Rn "to the nearest 1 or 0" (§10.66 of 2003, §10.53 of 2007), the 2010 text adding "0.5 is rounded to 1" (§8.57), as the rules record §5 and SPEC-L0 v1.4 (F-H09) already say. The reading of Rn as the rated player's new rating, and of the 2007 text's half point, stays NOT VERIFIED.
>
> (ii) src/layer0_greats/ rounds a period's half point towards +∞ on every list to October 2018, and away from zero from the list of November 2018. Basis: FIDE's output (every negative half point towards +∞ on the lists of July 2014 to July 2018, 27 of 27; away from zero from November 2018, 12 of 12; E20 §4.2). To July 2018 that output also matches the 2014 and 2017 words read literally, "0.5 is rounded up (whether the change is positive or negative)"; from November 2018 FIDE's arithmetic changed while the words did not, consistent with F-H07. The switch lies between the lists of August and November 2018; the exact list is NOT VERIFIED. R80 supersedes D-0017 reading 1 from the list of July 2014.
>
> (iii) The list of January 2009 gets no list-level exception: its periods stay thin and are recorded as a finding.
>
> (iv) Disclosure: (ii) was set after FIDE's pages had been read in the full replay. E20 prints the thin periods and §5's comparison under D-0017's reading and under R80's; §5 uses R80's. SPEC-L0 v1.5 records (ii) and (iii) as findings, with two new fixtures chosen by R79's rule: the last period before the switch and the first after it whose sum ends in a negative half point, among the periods Layer 0 reproduces.

Corrected 2026-10-12 (ELO-11): R80 (ii): whether FIDE's words changed in 2018 is NOT VERIFIED; the repository holds the 2014 text and the 2017 text as amended from 1 February 2021.

### R81 (ELO-9 Q2)

> The greats' backward replay.
>
> (i) The headlines of E20 and Appendix I are the lead over one's own era (E20 §3) and the replay's validation and findings from FIDE's pages (§4). The backward replay (§5) has no headline.
>
> (ii) E20 §5 describes it as the distance between the 2025 table and table 8.1.2 at these players' gaps, on results 8.1.2 already fits. Its calibration check is printed with this caveat, the threshold computed by E20's report script as the midpoint of the two mean residuals over every level: "The players were chosen because they reached the top three, so their results run ahead of any forecast. That lifts both tables' residuals alike; a lift above <threshold> a game would reverse which table sits nearer the results. Only an unselected sample of the era, which FIDE's tournament reports would provide, can say which table fits it."
>
> (iii) +27.0, its range and the per-player figures under the 2025 table appear only in E20 §5, under its label. E20's "In brief" and Appendix I describe the backward replay without them. Appendix I gives two sentences on what was done and what it measures, and points to E20 §5 (founder decision, 12 October).
>
> (iv) E20 §5 adds: "Here a table fitted on games of March to December 2024 sits further from these 2008-2019 results than FIDE's own. That is consistent with calibration changing between eras, with the table's thin support at the top, or with a sample chosen for success; it proves none of them."
>
> (v) No R59-style estimate is added: its correction at 2800 and above rests on a handful of games (E19 §3) and would move 936 game rows here (E20 §5). E20 §5 says so in one sentence.

Corrected 2026-10-12 (ELO-11): R81 (ii): the caveat's premise held for only part of the sample; E20 §5 now gives the check split by when the players were chosen.

### R82 (ELO-9 Q3)

> The 36 players fixed in SPEC-GREATS stand; no change after results (SPEC-GREATS §9). E20 and Appendix I state the asymmetry and its source. Before 2000 a shared place counts, since ratings before 1999 are multiples of five; six players are in only that way: Polugaevsky, Mecking, Beliavsky, Vaganian, Sokolov, Salov. From July 2000 FIDE's printed order decides; Svidler, 4th on the 3rd's rating in October 2006, is not among the 36.

Corrected 2026-10-12 (ELO-11): R82: from July 2000 FIDE's printed order decides where a printed copy survives (121 of 144 lists); a shared place counts on the other 23.

### R83 (ELO-9 Q4; founder decision)

> Every table or figure derived from OlimpBase's transcription carries: "Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences." README's licence section adds the carve-out and names every file holding such figures, documents and committed aggregates alike.

### R84 (ELO-9 Q4; founder decision)

> FIDE's written permission for the use of its pages and files will be requested by the operator, disclosing the use. Until FIDE answers nothing changes: FIDE's material is analysed from the local cache and only aggregates and differences are committed. DATA-PROBE §3's FIDE row says so, without any date.

Corrected 2026-10-12 (ELO-11): R84: the repository also holds the material `docs/DECISIONS.md` item 6 lists.

### R85 (ELO-9 Q4; founder decision)

> Future fetches identify themselves with the User-Agent "Zugzwang-Elo-research (+https://github.com/zugzwang-foundation/Chess-ELO-Rating)", with no email. Set it in the shared module the fetch tools use (tools/data/politeness.py, or wherever the shared session is built), with a test. Frozen fetch tools are not edited; the close-out lists which tools use the shared module and which are frozen. Nothing is fetched in this session.

### R86 (ELO-9 Q5-Q7)

> - R68 applies from 2027: confirmed (D-0016 reading 6). Applying it to 2026 would change a table after its results were seen (R65).
> - R78 stands.
> - Appendix F gains F.3, "From the greats' replay, 2008-2019", from E20 only:
>   (1) in the greats' games FIDE applied the 350-point rule to tournaments starting up to 28 June 2009 and the 400-point rule from 9 July 2009, a date no text gives;
>   (2) the same rounding words were applied two ways: a period's negative half point went towards +∞ on the lists to July 2018 and away from zero from November 2018, before the 2022 text said "away from zero"; the list of January 2009 is the exception;
>   (3) Carlsen, April 2003: FIDE's file and FIDE's own history differ by 41 points. The size only, with no view on which is right.
>   Nothing is sent to FIDE (R14, R64).

Corrected 2026-10-12 (ELO-11): R86 (2): which text was in force in 2018 is NOT VERIFIED.

### R87 (the handover's H3)

> The narrowed guard's label. "Fixed by ruling" means set by a ruling rather than fitted: R24 fixed the guard's rule, region and blends (level 2300, gap 400, blends of 50, the 735 stop) before the refit, and R46 fixed the one test that imposes or lifts it. "PROVISIONAL" means not yet estimated from FIDE's data: those numbers stay PROVISIONAL until FIDE's data set the guard's shape (R47; CLAUDE.md rule 7). Both hold. Annex T1's row reads "2300, 400, 50, 735 (fixed by ruling, R24; PROVISIONAL until set on FIDE's data, R47)". The parameter file already says both and is frozen. E12, printed by a frozen script, and SPEC-TOP100, the pre-registration of a superseded replay, stay as written and are read through this record.

### R88 (the handover's §10, item 8)

> The executor's readings recorded "for the architect" and not yet ruled on are confirmed as recorded. D-0018 lists each by record and number, with a one-line summary:
>
> - D-0012 reading 3: §10's blanks take their means and counts over the players with at least one counted game; K × n ≤ 700 counts played games.
> - D-0012 reading 9: SPEC-TABLE-FIT v1.2 splits the test months into selection months and later confirmation months; a candidate improves when its month-block log-loss interval lies below zero; it fixes three candidate forms.
> - D-0014 part A reading 1: column (a)'s three outcomes split FIDE's expectation by the level band's training-month draw rate (E2, with E6's floor); D-0015 withdrew the words "decided conservatively".
> - D-0014 part A reading 10: E13's 2025 illustration of the forecast test is in sample, and labelled so.
> - D-0014 part B reading 4: in the replays, the K rules' inputs other than the rating (games, year of birth, list in force) are FIDE's under both systems.
> - D-0016 reading 6: R68 applies from 2027; the 2026 table stays in E18's and E19's headlines (also R86).
> - D-0016 reading 7: R68's 24 months are the window's months counted from March 2024, test months included.
> - D-0017 reading 1, for the lists before July 2014: R74's boundary is the date the list is published (from July 2014, superseded by R80).
> - D-0017 reading 2: the third run (towards +∞ to December 2019) and the negative half points by year are reported for information only.
> - D-0017 reading 3: a player's peak is a derived figure, committed with attribution; no OlimpBase series, list or per-list rating is committed (now under R83's label).
> - D-0017 reading 4: R79's sample is the fourteen cases in the assembler's docstring; R80 adds two, within R79's cap.
>
> Not confirmed: D-0014 part B reading 6 (R-22b's two cases), which waits for the 1 November check (R42, R53, R63).

### R89 (founder decision; D-0005's open item "revisit before v1.0?")

> The repository keeps its name, Chess-ELO-Rating, and stays public. D-0001 stands, and D-0005's item is closed.

### The corrections the brief orders recorded here

> D-0018 also records these corrections, because the files cannot change:
>
> - E4 (printed by analysis/e4_community_report.py, frozen in Freeze 2) still prints NOT VERIFIED on the norm question, which the titles sweep and the proposal's §14 settled; read E4 with this correction.
> - REDTEAM_v0_1's totals line disagrees with its rows, and the ELO-4 session log's count of findings disagrees with REDTEAM_v0_4. Count the rows and record what each file shows; the repository's records are the reference.
> - E12's and SPEC-TOP100's "fixed by ruling": read as R87 says.

## Where each ruling is applied

| # | Where |
|---|---|
| R80 | Phase 2. `src/layer0_greats/`: a period's change rounded with 0.5 towards +∞ on every list to October 2018 and away from zero from the list of November 2018, with D-0017's reading kept beside it as R74 kept the first one (readings 1 and 2); `analysis/e20_greats_replay_extract.py` (the replay under each reading, reading 2); `tools/data/assemble_greats_fixtures.py`, whose docstring names the rule, and `tests/fixtures/fide_greats/` (F-G15 and F-G16, reading 4); `tests/test_layer0_greats.py`; E20 (its brief, §4.2, §4.3, §5 and §7) and Appendix I, through `analysis/e20_greats_report.py`; SPEC-L0 v1.5, a new file in `docs/specs/` (readings 5 and 6); the rules record's §5, through `analysis/greats_rules_record.py`; every document that quotes a changed E20 figure |
| R81 | Phase 3. E20's brief and §5, and Appendix I, through `analysis/e20_greats_report.py` (readings 7 to 9) |
| R82 | Phase 3. E20 (its brief, §2 and §7) and Appendix I state the asymmetry and its source (reading 10); SPEC-GREATS v1.0's rule and names unchanged |
| R83 (founder decision) | Phase 3. The label on every table or figure derived from OlimpBase's transcription, in every committed file that Phase 1 finds holding one, documents and aggregates (reading 11); README's licence section, with the carve-out and the files named |
| R84 (founder decision) | Phase 3. DATA-PROBE §3's FIDE row and §2.6, through `analysis/probe_greats_report.py`; E20's data paragraph and Appendix I's account of the data, which said that FIDE's permission had not been sought (reading 12) |
| R85 (founder decision) | Phase 3. `tools/data/politeness.py` and the fetch tools outside every freeze; a test that opens no connection; the close-out lists which tools use the shared module and which are frozen (reading 13) |
| R86 | R68 and R78: no change (D-0016 reading 6 stands, as E18 and E19 already print it; git history is not rewritten). Phase 3: the proposal's Appendix F gains F.3, from E20 only (reading 14) |
| R87 | Phase 3. Annex T1's guard row, as R87 words it. E12, SPEC-TOP100 and `params/guard_2026-10b.yaml` unchanged |
| R88 | This record (the list above); no file changes |
| R89 (founder decision) | No change: the repository's name and visibility stay as D-0001 records them; D-0005 is not edited, and its open item is closed by this record |

## Executor's readings where a ruling leaves a detail open

1. **R80 (ii), the boundary.** "Every list to October 2018" and "from the list of November 2018" are applied by the date the list is published, as `src/layer0_greats/` dates every rounding (D-0017 reading 1, confirmed for the lists before July 2014 by R88): the lists dated up to 2018-10 round 0.5 towards +∞, those dated from 2018-11 away from zero. FIDE published lists in August, September and October 2018; Phase 1 counts the replayed periods on them whose sum ends in a negative half point, the only periods on which the two roundings differ, so that the record shows whether any of FIDE's output there could date the switch more closely.
2. **R80 (ii) and (iv), the readings printed.** The replay runs under four readings of the rounding, each for Layer 0 and rung 2 alike: R80's, which §5 uses; D-0017's (R74 with D-0017 reading 1: 0.5 towards +∞ on the lists before July 2014, away from zero from July 2014), which R80 (iv) asks to be printed beside it; the rules record's first reading (away from zero on every list), which R74 asks to be reported and which no ruling withdraws; and 0.5 towards +∞ on every list to December 2019, with the negative half points by year, for information only (D-0017 reading 2, confirmed by R88). E20 prints the thin periods and the mean difference of §5 under each.
3. **R80 (iii), "its periods stay thin".** On the list of January 2009, the three periods whose negative half point FIDE rounded away from zero, and the one whose published change is not a rounding of its sum, stay thin under R80's reading and carry FIDE's change for both systems; E20 §4.2 and SPEC-L0 v1.5 (F-H09) record them as a finding.
4. **R80 (iv), the two fixtures.** Chosen by R79's rule as the assembler applies it (among the periods Layer 0 with the rules in force reproduces: every game, every tournament's K × sum and the published change), in the order of list and FIDE ID: **F-G15**, on the latest list published before November 2018 that holds such a period, the first period whose sum ends in a negative half point, rounded towards +∞ and not reproduced by rounding away from zero; **F-G16**, the first period on a list published from November 2018 whose sum ends in a negative half point, rounded away from zero and not reproduced by rounding towards +∞. The sample then holds sixteen cases, within R79's 30 player-periods.
5. **R80 (iv), SPEC-L0 v1.5 is a new file; v1.4 stays.** The brief asks for v1.5 by `git mv` from v1.4, "as R63 did; no frozen file cites v1.4". Four files of Freeze 2, as E3 lists them, cite v1.4 by its path: `analysis/l0_ratification_check.py`, which reads it (its `SPEC`) and which check (a) runs on every pull request, with its output `analysis/OUTPUT_L0_ratification.md`; and `analysis/l0_fixtures_report.py`, which prints the path, with its output `analysis/OUTPUT_L0_fixtures.md`. Moving v1.4 would make the first fail, and the brief forbids editing any of them. So v1.5 is written as a new file and v1.4 stays in place, unchanged, as SPEC-TABLE-FIT v1.0 and v1.1 stayed because frozen files cite them (D-0011 reading 2; D-0012 reading 9); every document that names the current specification names v1.5. How those four files came to cite v1.4, after the tag `freeze-2`, is measured in Phase 1 and reported in the close-out. For the architect.
6. **R80 (iv), which finding.** SPEC-L0 v1.5 adds **F-H10** for R80 (ii), the rounding of the 2014 and 2017 words on FIDE's lists of July 2014 to October 2018 and the change from November 2018, with F-G15 and F-G16, the switch's list NOT VERIFIED; it **extends F-H09** for R80 (iii), the list of January 2009, which F-H09 already names; and F-H07's row says that its reading of the 2017 words holds on the lists from November 2018. No rule of §3 changes, and the engine in `src/layer0/` is unchanged. In the same version R-12 becomes READ, NOT VERIFIED, with its entry in §8 (the handover's H4).
7. **R81 (i) and (iii), the headlines.** E20's "In brief" keeps its items on the sources, the lead over one's own era (§3) and the replay's validation and findings (§4), and gives the backward replay one item without +27.0, its range or any player's figure; Appendix I keeps its lead table, the replay's validation and findings, the tie rule and "What permission would add", and gives the backward replay two sentences, what was done and what it measures, pointing to E20 §5, with no per-player table under the 2025 table. The calibration check and its caveat stay in §5.
8. **R81 (ii), the threshold.** The midpoint of the two mean residuals over every level, (table 8.1.2's + the 2025 table's) / 2, from the calibration check's overall means as the replay's aggregate holds them (four decimals), printed to three decimals in place of `<threshold>`; the caveat's words are printed as R81 gives them, under the check's table.
9. **R81 (v), the sentence.** One sentence in §5, its count of game rows at 2800 or more printed from the replay's aggregate: no estimate of the 2025 table's own error at the top is added, as R59 added one for E19, because its correction at 2800 and above rests on a handful of games (E19 §3) and would move those game rows.
10. **R82, "the asymmetry and its source".** The asymmetry: a share of 3rd place selects a player on the lists to April 2000, whose ranks SPEC-GREATS §2 computes from the ratings, and not from July 2000, where FIDE's printed order decides. Its source: SPEC-GREATS §2's rule, which ranks the lists to April 2000 by their ratings, multiples of five before 1999 (DATA-PROBE §3, OlimpBase's remarks), and takes the rank FIDE printed from July 2000. E20 (its brief, §2 and §7) and Appendix I's "Who" say so with R82's names; SPEC-GREATS is unchanged.
11. **R83, where the label goes.** The label is the sentence R83 gives, unchanged. (a) Directly under every table derived from OlimpBase's transcription, beside R77's credit line, which stays. (b) Where a document states such figures outside a table, once after the paragraph or list that states them. (c) A committed aggregate that holds such figures carries the label in a top-level field, `terms`, written by the script that writes the aggregate. (d) A reviewer's report reproduced verbatim in `docs/review/` is not edited: the session's review addendum carries the label for the figures in it, and README names the file. "Derived from OlimpBase's transcription" is read as resting, for any list before 2001, on OlimpBase's lists: the selection, the ranks and counts, the peaks, the dominance gaps, the checks of OlimpBase's lists against FIDE's files of 2001, and the counts of OlimpBase's lists themselves. The replay of 2008–2019 rests on FIDE's pages and FIDE's own files; Phase 1 checks whether any of its figures depends on OlimpBase's lists.
12. **R84, what the row says.** DATA-PROBE §3's FIDE row says that FIDE's written permission is to be requested and that, until FIDE answers, nothing changes: FIDE's pages and files are analysed from the local cache (gitignored) and only aggregates and differences are committed. It gives no date; beyond R84's own words, transcribed above, the repository records nothing about the request. §2.6, E20's data paragraph and Appendix I, which said that FIDE's permission "has not been sought", say the same.
13. **R85, the shared module.** `tools/data/politeness.py` builds no session; it is the one module the fetch tools share. It holds the User-Agent, with a helper that gives a request's headers. The five fetch tools outside every freeze take their User-Agent from it: `fetch_probe.py` and `fetch_greats_calculations.py`, which already take their gaps from the module, and `fetch_fide_old_lists.py`, `fetch_fide_handbook.py` and `fetch_top100_calculations.py`, which import it for the User-Agent only. The three frozen tools (Freeze 2: `fetch_fide_calculations.py`, `fetch_fide_lists.py`, `fetch_lichess_broadcasts.py`) are not edited and keep their own, should they ever run again. The test reads the module and the tools' sources and opens no connection; nothing is fetched.
14. **R86, F.3.** Worded as E20 states it, citing E20 only. "Before the 2022 text said 'away from zero'": E20 §4.2 quotes §8.3.4 of the regulations in force from 1 January 2022, as `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md` transcribes it ("0.5 is rounded away from zero"), so that F.3 cites E20 alone. Appendix F lies outside the body's word count. Nothing is sent to FIDE.

## The corrections recorded, because the files cannot change

1. **E4** (`docs/evidence/E4_community-register.md`, printed by `analysis/e4_community_report.py`, a file of Freeze 2). Twice, under "Titles and norms", E4 says that "whether any norm arithmetic that uses table 8.1.2 would need to change is NOT VERIFIED". The titles sweep settled it: norm arithmetic uses table 1.4.9, which equals table 8.1.1 entry by entry, never table 8.1.2 [VT 1, 3] (`docs/research/VERIFICATION_TITLES.md`; the proposal's §14; `docs/review/REDTEAM_v0_4.md`, V4-QC-4). Read E4 with this correction.
2. **`docs/review/REDTEAM_v0_1.md`.** Its totals line reads "30 findings; 5 blockers, 17 majors, 8 minors. Blockers and majors: 20 fixed, 2 justified, 0 open. Minors: 4 fixed, 4 justified." Its rows, counted by script, give 30 findings: 6 blockers (R-STAT-1, R-STAT-2, R-QC-1, R-QC-2, R-QC-3, R-EXPLOIT-1), 17 majors and 7 minors (R-STAT 2, 6 and 2; R-QC 3, 6 and 1; R-EXPLOIT 1, 5 and 4). Their status cells: of the 23 blockers and majors, 18 fixed, 1 justified (R-QC-1) and 4 with two statuses (R-STAT-2 fixed and justified, R-QC-9 fixed with its sign open, R-EXPLOIT-1 fixed and justified, R-EXPLOIT-4 fixed and open); of the 7 minors, 4 fixed, 2 justified (R-EXPLOIT-7, R-EXPLOIT-8) and 1 with two (R-QC-10, fixed and justified). The rows are the reference.
3. **The ELO-4 count.** The ELO-4 session log (the operator's files) records "REDTEAM_v0_4 (17 findings: 7 blockers, 6 majors, 4 minors; all fixed or fixed in part)". `docs/review/REDTEAM_v0_4.md` lists 15 findings, in its disposition table and in the reviewer's verbatim report alike: 6 blockers (V4-STAT-1, V4-STAT-2, V4-QC-1, V4-QC-2, V4-EXPLOIT-1, V4-EXPLOIT-2), 5 majors (V4-STAT-3, V4-STAT-4, V4-QC-3, V4-QC-4, V4-EXPLOIT-3) and 4 minors (V4-STAT-5, V4-QC-5, V4-QC-6, V4-QC-7). The record is the reference: 15.
4. **"Fixed by ruling"** in E12's status line (`docs/evidence/E12_guard-v2.md`, printed by the frozen `analysis/e12_guard_v2_report.py`: "the guard's region and blend are fixed by ruling (R24)") and in SPEC-TOP100's status line ("fixed by ruling (the guard)"): read as R87 says. The guard's rule, region and blends were set by ruling R24 before the refit, and its one test by R46; its numbers stay PROVISIONAL until FIDE's data set its shape (R47).

## For the architect (recorded here)

- Reading 5: SPEC-L0 v1.5 as a new file beside v1.4, which stays because four files of Freeze 2 cite it by path, against the brief's premise that no frozen file does.
- Reading 2: the rules record's first reading stays among the runs E20 prints, since R74's disclosure asks for it.
- Reading 11: R83's label as a top-level field of each aggregate, and carried for a verbatim reviewer's report by the session's addendum rather than inside it.
- Reading 12: the FIDE row says that permission is to be requested, without saying by whom.
- Reading 13: the fetch tools outside the freezes that did not use the shared module now take their User-Agent from it.

## Consequences

- From the list of July 2014 to that of October 2018, Layer 0's reading of the greats' rounding changes after FIDE's pages had been read in the full replay (R80 (iv)); E20 says so, and prints the thin periods and §5's mean difference under D-0017's reading and under R80's.
- No frozen file changes. SPEC-L0 v1.5 changes no rule of §3; `src/layer0/` and `src/layer0_history/` are unchanged.
- D-0017 stands, except its description of the 2007 and 2010 texts (superseded by R80 (i)) and its reading 1 from the list of July 2014 (superseded by R80 (ii)). D-0016, D-0015, D-0014, D-0013 and D-0012 stand. The readings R88 lists are confirmed; D-0014 part B reading 6 waits for the 1 November check.
- The steps after the last round of the 2026 championships and after the 1 November list are D-0016's, unchanged.
