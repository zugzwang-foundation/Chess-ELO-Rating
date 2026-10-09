# analysis/ — calculations for the proposal documents

These scripts are **not the rating engine**. By project rule (CLAUDE.md, hard rule 1) no engine code exists before SPEC-L0 is ratified, and nothing here is engine code. The scripts are deterministic, Python 3 standard library only, and exist so that every number printed in `docs/proposal/ELO-PROPOSAL_v0_3.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md` and `docs/proposal/ELO-BRIEF_v0_3.md` can be regenerated and checked.

| File | Purpose |
|---|---|
| `v03_calculations.py` | Expected-score function with the draw decay of D1 and its numerical checks; band-edge steps (D6); colour; K from certainty (D3); continuous junior compensation (D5); worked examples (i)–(iii) of annex T10; the monthly adjustment with its soft deadband (D7); the ledger identity (annex T6) on a synthetic month with a floor exit, a newcomer, a re-entry and a refused re-entry; a Layer 0 test vector |
| `OUTPUT_v0_3.md` | The script's output, committed so that the documents can be diffed against it |
| `outputs.json` | The registry of scripts and outputs that check (a) reruns (`tools/README.md`) |

Run: `python3 analysis/v03_calculations.py > analysis/OUTPUT_v0_3.md` and `git diff` must be empty. Every script here is registered in `analysis/outputs.json` with the file its output must equal; check (a) of the automated check reruns them on every pull request. The v0.2 script and its output were bumped to v0.3 with `git mv`; earlier versions are in git history.

Every parameter value in the scripts is PROVISIONAL. The expected-score function is evaluated in binary floating point and rounded half up to three decimals; the Layer 1 quantities (posterior means and SDs, anchor means) are inputs chosen for illustration, not model outputs.
