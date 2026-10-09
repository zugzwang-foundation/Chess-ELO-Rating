# D-0006 — SPEC-L0 v1.0 ratified

Date: 2026-10-09 · Session: ELO-3 · Status: DECIDED (by the pre-agreed rule of the ELO-3 brief, Phase 2.3; applied by the executor)

## Context

CLAUDE.md, hard rule 1: rating code is written only once the Layer-0 specification carries status RATIFIED. The ELO-3 brief fixes the ratification rule in advance: "the spec is ratified when every rule has a fixture or a verbatim citation and every acceptance criterion is an executable test." SPEC-L0 v1.0 was merged with status READY in pull request #4. This record applies the rule.

## The rule, measured

`analysis/l0_ratification_check.py` reads the specification, the test modules and the fixtures, and its output `analysis/OUTPUT_L0_ratification.md` is committed and rerun by check (a) on every pull request:
- every rule of §3 carries a quoted FIDE text (CIT) or a fixture whose identifier exists under `tests/fixtures/` (FIX), and every rule is mentioned by at least one test module;
- every acceptance criterion A-1 to A-10 of §7 names a test module that exists and defines test functions;
- the script's verdict line states that the rule is met.

The tests were written and committed before any engine code; until the package `layer0` exists under src, every test that needs it is skipped and the two tests of the transcribed tables run. Check (b) runs all of them on every pull request.

## Decision

1. SPEC-L0 v1.0 (`docs/specs/SPEC-L0_fide-reference-engine_v1_0.md`) is RATIFIED; its status line says so. The engine may now be written, in the package and with the interfaces of SPEC-L0 §4 and §10.
2. Clarifications added between READY and RATIFIED, none of which changes a rule:
   - the readings the tests encode are stated where the text is silent: R-01 (unrated players count as below 1800), R-06 (when a match is decided), R-10 (the third list after the end), R-12 ("current rating"), R-27 (the 26-period pool), R-28 (the first event), R-31 (K and the new rating of a player seeded from the standard list), R-32 (the games counter is kept), R-33 (inactivity after 12 periods without games) and R-34 (which fields the engine computes);
   - R-14a cites the amendment's words "Effective from 1 October 2025:" and the research report's timeline [R §2];
   - R-22 and R-24 quote the text they order or apply;
   - §2.4 is renamed "Corrections";
   - §4 lists the concrete signatures;
   - §7 describes A-8 to A-10 as tested.
3. A change to any rule after ratification needs a new version of the specification (bumped with `git mv`, D-0004) and a decision record.
4. The readings marked NOT VERIFIED stay open questions (SPEC-L0 §8, Q-1 to Q-11). They are recorded, not ratified as FIDE's rules: when a fixture or FIDE settles one, the specification and the test change together.

## Consequences

- Phase 3 of ELO-3 continues: the engine is written against tests that existed before it, and the 2025 US Championship validation (A-10) reports per player under docs/evidence.
- Q-1 has evidence in both directions:
  - rounding once per period, as written, reproduces F-P05 and the 2025 US Championship;
  - rounding per tournament reproduces F-P02.
  - Layer 0 follows the text and reports the alternative.
