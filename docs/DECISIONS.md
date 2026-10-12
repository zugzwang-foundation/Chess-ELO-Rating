# Decisions

Status: DECIDED — the project's decision log from 12 October 2026: one dated line per decision, newest date first; the ten of 12 October 2026 stand in the order they were given, and a later decision takes the next number and goes on top. The decision records D-0001 to D-0018 in `docs/decisions/` stay as history; a mistake in one is fixed in place, with a dated line saying what changed.

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
