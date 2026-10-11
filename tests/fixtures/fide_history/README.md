# tests/fixtures/fide_history/

Status: DRAFT — test fixtures, not for publication.

`published_periods.json`: FIDE's published per-player calculations of a few periods of the October 2026 top 100, one for each rule that changed between February 2020 and October 2026 (`docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`; `docs/specs/SPEC-TOP100_v1_0.md` §5.1), written by `tools/data/assemble_history_fixtures.py` from the pages cached by `tools/data/fetch_top100_calculations.py`. Opponents are identified by the rating FIDE used, never by name, and no player's FIDE ID or event is recorded (SPEC-TOP100 §8; review finding ELO7-QC-5); the values are single figures quoted from FIDE's calculations and lists for verification, as in `tests/fixtures/fide_calculator/`. `tests/test_layer0_history.py` checks `src/layer0_history/` against them.
