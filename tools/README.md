# tools/

Status: DRAFT — utilities, not the rating engine.

## checks/ — the automated check

The workflow `.github/workflows/check.yml` runs on every pull request to `main`; a pull request is merged only when it is green (`docs/decisions/D-0004_merge-policy.md`). The same checks run locally from the repository root:

| Check | Command | What it enforces |
|---|---|---|
| (a) | `python3 tools/checks/check_outputs.py` | every script registered in `analysis/outputs.json` reproduces its committed output byte for byte; every `analysis/*.py` is registered. Add `--all` to also rerun the scripts that read raw data under `data/` (`"needs_data": true`) and the slow ones (`"slow": true`, the simulator) |
| (b) | `python3 -m pytest -q` | the test suite under `tests/`, configured in `pyproject.toml`: the SPEC-L0 acceptance tests A-1 to A-10 against the engine in `src/layer0/` |
| (c) | `python3 tools/checks/check_refs.py` | relative links and repository paths in code spans exist (records, and documents marked RATIFIED, may name a path that existed earlier in git history); `[R n]`, `[V k]`, `[VT k]`, `[VP k]`, `[E n]` and `[T n]` references resolve against the research report, the three verification sweeps, the evidence reports and the current technical annex |
| (d) | `python3 tools/checks/check_wordcount.py` | the body of the current proposal is at most 4,500 words by ELO-2's strict count, and the current brief at most 900 words (D-0005) |

Python standard library only (pytest for (b)). Python 3.12 in CI.

## compare_event.py — one event under FIDE's rules and under rung 2

`tools/compare_event.py` (`docs/specs/SPEC-COMPARE_v1_0.md`) reads an event file from `tools/events/` and prints, per player, the rating change under (a) FIDE today, computed by the Layer-0 engine, and (b) rung 2, the fitted table of `params/table_fit_2026-10.yaml` with the same K. `--csv FILE` also writes a CSV; `--rung4` and `--rung5` accept only `off` until Layer 1 exists. `tools/set_results.py` records a round's results in an event file.

| Event file | Event |
|---|---|
| `tools/events/us_championship_2025.json` | 2025 U.S. Championship (the check: column (a) equals FIDE's calculation) |
| `tools/events/us_championship_2026.json` | 2026 U.S. Championship, 9–21 October 2026 |
| `tools/events/us_womens_championship_2026.json` | 2026 U.S. Women's Championship, 9–21 October 2026 |

**Run once, after the event ends** (the operator's decision of 2026-10-09; it replaces the per-round rerun of the ELO-3 brief). The model is frozen beforehand: `docs/evidence/E3_us-championship-2026.md` prints the SHA-256 of the parameter file, `tools/compare_event.py` and `src/layer0/`, and check (a) fails if any of them changes. After the last round, read each round's results from the official page (https://saintlouischessclub.org/event/2026-us-chess-championships/) and enter them board by board (`1-0`, `1/2-1/2`, `0-1`), one command per round, using `tools/events/us_womens_championship_2026.json` for boards 7–12. Then regenerate the page once; an event's table appears only when all its games have results:

```
python3 tools/set_results.py tools/events/us_championship_2026.json ROUND R1 R2 R3 R4 R5 R6
python3 analysis/e3_us_championships.py > docs/evidence/E3_us-championship-2026.md
```

## data/ — downloads and conversions

Raw and converted data live under `data/` at the repository root, which is never committed (`.gitignore`): FIDE's lists carry no data licence and are analysed, never redistributed [V 3]. Only aggregates computed from them are committed, under `analysis/aggregates/`.

| Script | What it does |
|---|---|
| `tools/data/fetch_fide_lists.py` | Downloads FIDE's monthly lists (TXT in zip) for one time control and a range of months into `data/raw/fide/<tc>/`, one request at a time, recording URL, UTC time, size and SHA-256 in `data/raw/fide/MANIFEST.tsv` |
| `tools/data/convert_fide_lists.py` | Converts each list into `data/interim/fide/<tc>/YYYY-MM.tsv` (id, rating, games, K, year of birth, sex, federation, flag, title), locating the fixed-width columns from each file's header |
| `tools/data/fetch_lichess_broadcasts.py` | Downloads the Lichess broadcast archive (monthly PGN, zstd; CC BY-SA 4.0 [V 4]) into `data/raw/lichess_broadcast/`, checking each file against the published SHA-256 sums and recording it in a manifest |
| `tools/data/fetch_fide_calculations.py` | Selects players and periods deterministically from the converted lists (`select`, and `select-cross` for periods holding an event that started under an earlier list, from the broadcast tours), fetches FIDE's published per-player calculations one at a time at least 10 s apart (`fetch`; raw responses under `data/raw/fide_calculations/`), and assembles `tests/fixtures/fide_calculator/published_multi_event_periods.json` (`assemble`); opponents' names are never recorded |
| `tools/data/convert_broadcasts.py` | Converts each month into `data/interim/broadcast/YYYY-MM.tsv`: one line of game headers per game, no moves (needs the `zstd` command) |

To rebuild what the `needs_data` scripts of `analysis/outputs.json` read: run `python3 tools/data/fetch_fide_lists.py <tc> 2015-02 2026-10` and `python3 tools/data/convert_fide_lists.py <tc>` for `standard`, `rapid` and `blitz`; `python3 tools/data/fetch_lichess_broadcasts.py 2023-01 2026-09` and `python3 tools/data/convert_broadcasts.py`; then `python3 tools/checks/check_outputs.py --all`.
