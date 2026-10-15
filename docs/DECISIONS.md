# Decisions

Status: DECIDED — the project's decision log from 12 October 2026: one dated line per decision, newest date first; the ten of 12 October 2026 stand in the order they were given, and a later decision takes the next number and goes on top. The decision records D-0001 to D-0018 in `docs/decisions/` stay as history; a mistake in one is fixed in place, with a dated line saying what changed.

46\. 2026-10-15 — Word caps kept, the body at most 4,500 words with section 10's blanks counted as filled and the brief at most 900: the new evidence replaces words, detail goes to the annex and appendices, and no verdict, condition, disclosure or required line is cut; every change since the review of 12 October is listed in STATUS and checked by a fresh-eyes review of the changed passages (founder) (session ELO-15c): `STATUS.md`, "Changed since the review of 12 October".

45\. 2026-10-15 — SPEC-L0's open question Q-12 (the 7 pages printed with Ro 0 and no K, whose games the lists rated) and the R-09/R-10 observation of E21 §10.2 are recorded for session ELO-17; no specification change now (founder) (session ELO-15c): `STATUS.md`, Next.

44\. 2026-10-15 — The probe's 20 tournament reports are deleted, each first checked against its logged SHA-256 and read no further, and listed in the local manifest; commit eed5127, the club-level sample's plan, which the squash-merge left outside main's history, is tagged elo-d2-plan (founder) (session ELO-15c): `tools/data/fetch_sourcing.py` (mode delete-reports), `docs/research/SOURCES_v1_0.md` §5.

43\. 2026-10-15 — The data rule: where this project's material shows a named player's FIDE rating, it is FIDE's published rating, credited to FIDE; no FIDE list file is published; FIDE IDs are committed only in the test fixtures quoting FIDE's published calculations, the event files and for the named players of today's top 100 and the greats; section 9's request for FIDE's written permission stays (founder) (session ELO-15c): proposal Appendix I, annex T8.6, `README.md`, `docs/research/SOURCES_v1_0.md`.

42\. 2026-10-15 — One sentence on the Qualification Commission's decisions of 23 September 2026 (summary posted 12 October 2026) beside rungs 4 and 5: K = 40 for non-junior players rejected; standard events reported every 60 days rather than 30, subject to the Ratings Office; the annex lists the four relevant decisions and Appendix C the source (founder) (session ELO-15c): proposal §8, annex T8.10, Appendix C.

41\. 2026-10-15 — ELO-D1's proposed edits adopted, every figure of Sonas's with its period, before FIDE's regulations of 1 March 2024; the greats' differences list by list stay out of the proposal (founder) (session ELO-15c): proposal §2(a), §2(b), §8; annex T3.8, T4.6, T4.7, T8.6.

40\. 2026-10-15 — Appendix F gains the finding on FIDE's game pages against its lists, descriptive and dated (pages read 14 October 2026), with no claim about why (founder) (session ELO-15c): proposal Appendix F.4.

39\. 2026-10-15 — Newcomers are never said to be rated behind their strength: the documents give their first year slightly below their ratings and the young's later climb, which is improvement; rung 3 keeps TEST ON FIDE DATA, its problem restated; "fast improvers" rests on juniors (founder) (session ELO-15c): proposal §2(b), §6, §8; annex T4.7, T8.1, T8.10.

38\. 2026-10-15 — Rung 1's criterion, decided after E21 §10: every game and tournament sum FIDE prints is reproduced from FIDE's printed inputs; a list change that differs from FIDE's own page is reported to FIDE (Appendix F), not counted against the replica; the check on FIDE's 1 November list applies it (founder) (session ELO-15c): proposal §1, §8, §11; annex T8.1, T8.10.

37\. 2026-10-15 — Rung 2: RECOMMENDED NOW in standard from 2000, where the table fitted on broadcast games fits FIDE's own 2025 games; below 2000 the table, colour term included, is refitted on FIDE's own games before it applies there, because there it overshoots about as much as table 8.1.2 errs (E21 §11); the shadow year stays; this settles the review's question 7 (ELO6-STAT-1) (founder) (session ELO-15c): proposal §1, §2(a), §8, §15; annex T3.8, T8.2, T8.10; the brief.

36\. 2026-10-14 — Analyses chosen after seeing the pilot are labelled so; the club-level sample's analyses are fixed in its plan before the main fetch (founder) (session ELO-D2): `docs/specs/SPEC-SOURCING_v1_1.md` §7.

35\. 2026-10-14 — Once the session's analysis is verified, the raw pages of ELO-D1's pilot and of this run, and every per-game file derived from them, are deleted; a local manifest of links, periods and checksums is kept so that anyone can fetch them again; E17's and E20's caches are not touched; only totals are committed (founder) (session ELO-D2): `docs/specs/SPEC-SOURCING_v1_1.md` §9.

34\. 2026-10-14 — No request to FIDE or to anyone in this session (founder) (session ELO-D2).

33\. 2026-10-14 — Run only Tier 0, the list-change puzzle and the parser fix on the pages already held, and Tier 1, a level-stratified sample of about 5,500 of FIDE's per-player game pages of 2025; not run: the targeted countries sample and any larger fetch (founder) (session ELO-D2). This settles item 29: SPEC-SOURCING v1.0's smaller run is not run, and the plan is bumped to `docs/specs/SPEC-SOURCING_v1_1.md`, the club-level sample's.

32\. 2026-10-14 — Every new analysis of the session is labelled as decided after seeing the data (founder) (session ELO-D1): `docs/evidence/E21_sourcing.md`, SPEC-SOURCING v1.0 (bumped to `docs/specs/SPEC-SOURCING_v1_1.md` in session ELO-D2, item 33).

31\. 2026-10-14 — Sampled players' data never leave `data/` (founder): only totals by federation, level, age group and colour are committed, and no sampled player's name, FIDE ID or row; many sampled players are minors (session ELO-D1): `docs/evidence/E21_sourcing.md`, `docs/research/SOURCES_v1_0.md`.

30\. 2026-10-14 — Left (founder): URS, which mixes standard, rapid and blitz and whose main use, the sizes of countries' offsets, the proposal keeps for FIDE's commission; Ghita's 2025 game extract, private to him; Chess-Results, whose data may not be copied without consent; The Week in Chess, ChessBase and the Lumbras Gigabase, elite-heavy (Ghita, p. 73); the Kaggle data of 2010–2011; FIDE's rapid and blitz lists (session ELO-D1): `docs/research/SOURCES_v1_0.md`.

29\. 2026-10-14 — Not in this session: the large fetch of FIDE's per-player game pages; the founder decides it after the session's go/no-go brief (founder) (session ELO-D1): `docs/evidence/E21_sourcing.md` §7, SPEC-SOURCING v1.0 (DRAFT, pending; bumped to `docs/specs/SPEC-SOURCING_v1_1.md` in session ELO-D2, item 33).

28\. 2026-10-14 — Taken: a probe of 20 of FIDE's tournament reports, of events that ended before 1 October 2026, none of a 2026 U.S. Championship (founder) (session ELO-D1): `docs/evidence/E21_sourcing.md` §6.

27\. 2026-10-14 — Taken: a pilot of 2,000 of FIDE's per-player game pages of 2025 standard periods, drawn from the October 2025 list's active players of every federation with at least 1,000 rated players plus England, Scotland and Wales, at every level, juniors and newcomers oversampled (founder) (session ELO-D1): `tools/data/fetch_sourcing.py`, `docs/evidence/E21_sourcing.md` §5.

26\. 2026-10-14 — Taken: FIDE's published Qualification Commission reports, cited (founder): Sonas's reports of July and October 2023 and January 2024, by page, with short quotations (session ELO-D1): `docs/evidence/E21_sourcing.md` §4.

25\. 2026-10-14 — Taken: new analyses of FIDE's standard lists already held, totals only (founder): who plays the rated games, by K; juniors' climb against adults'; newcomers' first ratings against their ratings 12 and 24 months later, called a climb and not proof of under-rating (session ELO-D1): `docs/evidence/E21_sourcing.md` §3.

24\. 2026-10-14 — Taken: the greats' month-by-month replay, from FIDE's pages already cached (founder): E20's replay rerun list by list, its year-end values equal to E20's (session ELO-D1): `analysis/aggregates/E20_greats_replay_by_list.json`, `docs/evidence/E21_sourcing.md` §2.

23\. 2026-10-12 — §2(a)'s answer to the deflation figures restored, the brief's link restored, and annex T8's "at most 36 months" (founder): §2(a) again answers the deflation figures in Ghita's book (session ELO-15 cut the sentence in error, on the architect's relay): since the March 2024 reform the active list's median still falls, 11 to 16 points a year, but only because entrants arrive below the players who stop, and steadily active adults gain 2 to 3 points a year in standard; the brief says again that top players are usually favourites, so that it ties the table's error to the top's loss; E6's fits used at most 36 months, from the archive's first month 2023-01 (session ELO-15b): proposal §2(a), the brief's "What is wrong", annex T8's record of what has been run, `analysis/README.md`.

22\. 2026-10-12 — E6's junior figures are from 2025-01 to 2026-09, after the March 2024 reform, and the proposal says so (founder): the 21 held-out months that annex T8.3's protocol fixed before E6 ran; no figure changes (session ELO-15): proposal summary, §2(b) and §8's rung 5 row; annex T4.6, T8.1 and T8's record of what has been run.

21\. 2026-10-12 — Who runs what (founder): the Zugzwang Foundation computes the shadow list from stage 2 and the pilot federation's domestic list in stage 3, monthly, at no cost to FIDE or the federation, and either can run the open code themselves; this replaces item 18 (session ELO-15): proposal §13, "Who runs what", and one clause in the brief.

20\. 2026-10-12 — The headline covers players rated 2200 or more, in two parts (founder): since the March 2024 reform the second drain is at most 0.08 a game; what remains at the top is about what table 8.1.2's over-prediction implies at the players' own levels; rung 2's line follows (session ELO-15): proposal summary and §2(a), the brief's "What is wrong", `docs/evidence/E5_deflation.md`.

19\. 2026-10-12 — The contact named in the proposal (founder): "Hrishikesh, The Zugzwang Foundation", in the front matter of the proposal and of the brief; no email address (session ELO-14): `docs/proposal/ELO-PROPOSAL_v1_0.md`, `docs/proposal/ELO-BRIEF_v1_0.md`.

18\. 2026-10-12 — The Zugzwang Foundation runs the pilot's shadow list at no cost (founder): during the pilot it maintains the open code and runs the shadow list each month, at no cost to FIDE or to the pilot federation; the code is open, so FIDE or the federation can run it themselves at any time; arbiters' tools do not change until FIDE adopts a step; the pilot federation shares its rated games under a data agreement and pays nothing (session ELO-14): proposal §13, "Who runs the pilot", and one clause in the brief.

17\. 2026-10-12 — E5 measures the over-prediction at the players' own levels throughout: every band's figure uses the game's 100-point level band and 50-point gap bin, as item 14 did for players rated 2400 or more, and the figure averaged over all levels stays beside it for comparison; the split by level band was chosen after seeing the data, not registered in advance; E5's verdict and its paragraph on the second drain are re-read on these figures (session ELO-14): `docs/evidence/E5_deflation.md`; proposal §2(a).

16\. 2026-10-12 — Appendix G, the superseded replay of today's top 100, is replaced by one line pointing to the current replay, Appendix H (E19); its text stays on record as its script writes it, `analysis/OUTPUT_E17_appendix.md` (session ELO-13).

15\. 2026-10-12 — The Brier score of the expected score is reported beside every log-loss criterion of the tests on FIDE's data, as a secondary measure; log-loss stays the main criterion; no figure changes (session ELO-13): proposal §11, annex T8.1 and T8.2.

14\. 2026-10-12 — E5 measures the over-prediction's cost to players rated 2400 or more at their own levels, by 100-point level band (as E10 §5 bands it) and 50-point gap bin, beside the figure averaged over all levels; the band split was chosen after seeing the data, not registered in advance (session ELO-13): `docs/evidence/E5_deflation.md` §5.

13\. 2026-10-12 — Section 10's reading restored to D-0015's order: the fixed sentence, then directly the small-sample statement, then the log-loss lines; the words unchanged (session ELO-13): `tests/test_section10_reading.py`.

12\. 2026-10-12 — Project knowledge (founder): at every close-out the close-out goes to the operator's project knowledge; the full folder with its PK-MANIFEST.md is built only when the relay asks for it, after substantial sessions; this replaces item 8: `CLAUDE.md`, "How we work".

11\. 2026-10-12 — No new freezes. Pre-registration only where the proposal promises it: the championship comparison and the tests on FIDE's data (session ELO-12): `CLAUDE.md`, "How we work".

The ten decisions of 12 October 2026, in the order they were given:

1. 2026-10-12 — Light mode adopted (founder): `CLAUDE.md`, "How we work".
2. 2026-10-12 — The championship lock stays until the comparison has run once; then the freeze checks retire; the tags stay (founder).
3. 2026-10-12 — Code tests and the automatic checks stay (founder).
4. 2026-10-12 — Freeze 2: four report files (`analysis/l0_ratification_check.py`, `analysis/OUTPUT_L0_ratification.md`, `analysis/l0_fixtures_report.py`, `analysis/OUTPUT_L0_fixtures.md`) were re-pointed to new SPEC-L0 versions in ELO-8 and ELO-9 without a record; E3 lists the commits. They stay as they are; none is part of the championship comparison; no new check.
5. 2026-10-12 — SPEC-L0 v1.4 stays beside v1.5, because those report files read it.
6. 2026-10-12 — FIDE's material (founder): besides aggregates and differences, the repository holds test fixtures quoting FIDE's published calculations, three event files, short quotations of FIDE's texts and single published ratings where a table needs them. All of it is listed in the request for FIDE's permission.
7. 2026-10-12 — F-N01: identifiers the test does not use are replaced by placeholders (session ELO-11); git history unchanged.
8. 2026-10-12 — Project knowledge: a full folder at every close-out.
9. 2026-10-12 — D-0018 corrected in place: R80 (ii), R81 (ii), R82, R84, R86 (2).
10. 2026-10-12 — Prior work credited and the sources list cleaned (session ELO-11).
