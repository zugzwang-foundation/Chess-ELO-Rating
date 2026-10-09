# tools/

Status: DRAFT — utilities, not the rating engine.

## checks/ — the automated check

The workflow `.github/workflows/check.yml` runs on every pull request to `main`; a pull request is merged only when it is green (`docs/decisions/D-0004_merge-policy.md`). The same checks run locally from the repository root:

| Check | Command | What it enforces |
|---|---|---|
| (a) | `python3 tools/checks/check_outputs.py` | every script registered in `analysis/outputs.json` reproduces its committed output byte for byte; every `analysis/*.py` is registered. Add `--all` to also rerun the scripts that read raw data under `data/` |
| (b) | `python3 -m pytest -q` | the test suite under `tests/`, configured in `pyproject.toml`: the SPEC-L0 acceptance tests A-1 to A-10 against the engine in `src/layer0/` |
| (c) | `python3 tools/checks/check_refs.py` | relative links and repository paths in code spans exist; `[R n]`, `[V k]`, `[VT k]` and `[T n]` references resolve against the research report, the two verification sweeps and the current technical annex |
| (d) | `python3 tools/checks/check_wordcount.py` | the body of the current proposal is at most 4,500 words by ELO-2's strict count, and the current brief at most 900 words (D-0005) |

Python standard library only (pytest for (b)). Python 3.12 in CI.

## data/ — downloads and conversions

Raw and converted data live under `data/` at the repository root, which is never committed (`.gitignore`): FIDE's lists carry no data licence and are analysed, never redistributed [V 3]. Only aggregates computed from them are committed, under `analysis/aggregates/`.

| Script | What it does |
|---|---|
| `tools/data/fetch_fide_lists.py` | Downloads FIDE's monthly lists (TXT in zip) for one time control and a range of months into `data/raw/fide/<tc>/`, one request at a time, recording URL, UTC time, size and SHA-256 in `data/raw/fide/MANIFEST.tsv` |
| `tools/data/convert_fide_lists.py` | Converts each list into `data/interim/fide/<tc>/YYYY-MM.tsv` (id, rating, games, K, year of birth, sex, federation, flag, title), locating the fixed-width columns from each file's header |

To rebuild what the `needs_data` scripts of `analysis/outputs.json` read: `python3 tools/data/fetch_fide_lists.py standard 2015-02 2026-10`, then `python3 tools/data/convert_fide_lists.py standard`, then `python3 tools/checks/check_outputs.py --all`.
