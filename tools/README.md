# tools/

Status: DRAFT — utilities, not the rating engine.

## checks/ — the automated check

The workflow `.github/workflows/check.yml` runs on every pull request to `main`; a pull request is merged only when it is green (`docs/decisions/D-0004_merge-policy.md`). The same checks run locally from the repository root:

| Check | Command | What it enforces |
|---|---|---|
| (a) | `python3 tools/checks/check_outputs.py` | every script registered in `analysis/outputs.json` reproduces its committed output byte for byte; every `analysis/*.py` is registered. Add `--all` to also rerun the scripts that read raw data under `data/` |
| (b) | `python3 -m pytest -q` | the test suite, once tests exist |
| (c) | `python3 tools/checks/check_refs.py` | relative links and repository paths in code spans exist; `[R n]`, `[V k]` and `[T n]` references resolve against the research report, the verification sweep and the current technical annex |
| (d) | `python3 tools/checks/check_wordcount.py` | the body of the current proposal is at most 4,500 words by ELO-2's strict count, and the current brief at most 900 words (D-0005) |

Python standard library only (pytest for (b)). Python 3.12 in CI.
