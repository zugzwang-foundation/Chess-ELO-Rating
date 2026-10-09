# analysis/ — illustrative calculations for the proposal documents

These scripts are **not the rating engine**. By project rule (CLAUDE.md, hard rule 1) no engine code exists before SPEC-L0 is ratified; nothing here is under `src/`. The scripts are deterministic, Python 3 standard library only, and exist so that every number printed in `docs/proposal/ELO-PROPOSAL_v0_2.md` and `docs/proposal/ELO-TECHNICAL-ANNEX_v0_2.md` can be regenerated and checked.

| File | Purpose |
|---|---|
| `v02_calculations.py` | Expected-score function (AR-1) and its numerical checks; K mapping (AR-2); worked examples (i)–(iii) of annex T10; ledger identity (T6) on a synthetic month; feedback-loop trajectory of the global adjustment (AR-3) |
| `OUTPUT_v0_2.md` | The script's output, committed so that the documents can be diffed against it |

Run: `python3 analysis/v02_calculations.py > analysis/OUTPUT_v0_2.md` and `git diff` must be empty.

Every parameter value in the script is PROVISIONAL. The expected-score function is evaluated in binary floating point and then rounded to three decimals; the engine, when written, will publish the table from a fixed-precision evaluation and this script's values will be checked against it. Layer 1 quantities (posterior means and SDs, anchor means) are inputs chosen for illustration, not model outputs.
