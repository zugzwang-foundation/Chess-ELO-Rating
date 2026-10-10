# analysis/ — calculations for the proposal documents

These scripts are **not the rating engine**: the engine is the package `src/layer0/`, written after SPEC-L0 was ratified (D-0006); scripts that need it import it. The scripts are deterministic, Python 3 standard library only, and exist so that every number printed in `docs/proposal/ELO-PROPOSAL_v0_4.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v0_4.md`, `docs/proposal/ELO-BRIEF_v0_4.md`, the specifications and the evidence pages can be regenerated and checked.

| File | Purpose |
|---|---|
| `v04_calculations.py` | Expected-score function with the draw decay of D1 and its numerical checks; band-edge steps (D6); colour; K from certainty on the published scale (D3 as revised by R6); continuous junior compensation (D5 with R5 and R8); worked examples (i)–(iii) of annex T10; the monthly adjustment with its soft deadband (D7) and accrual by activity (R3); the ledger identity (annex T6) on a synthetic month with a floor exit, a newcomer, a re-entry and a refused re-entry; the R1 spread-ratio threshold from the Layer 1 history fit; a Layer 0 test vector |
| `OUTPUT_v0_4.md` | The script's output, committed so that the documents can be diffed against it |
| `l0_fixtures_report.py` | Recomputes every fixture in `tests/fixtures/fide_calculator/` (FIDE's online calculator and published calculations) from tables 8.1.1, 8.1.2 and 1.4.9 as transcribed, under each reading SPEC-L0 names, and checks every derived value stored in the fixtures |
| `OUTPUT_L0_fixtures.md` | Its output, cited by SPEC-L0 |
| `l0_rounding_report.py` | SPEC-L0 §8 Q-1 (D-0008, R10): for every multi-event period of FIDE's published calculations (`tests/fixtures/fide_calculator/`), the change rounded once and per tournament against the published list, with base corrections identified |
| `OUTPUT_L0_rounding.md` | Its output |
| `l0_k_rules_extract.py` | Needs `data/`: scores orders of the K rules (SPEC-L0 R-18 to R-22) against the K FIDE published on every standard list, February 2015 to October 2026; prints counts only |
| `aggregates/L0_k_rules.json` | Its output: counts only, no player data |
| `l0_k_rules_report.py` | Turns the K aggregates into the tables SPEC-L0 cites |
| `OUTPUT_L0_k_rules.md` | Its output |
| `l0_ratification_check.py` | Measures the pre-agreed ratification rule of SPEC-L0: every rule has a quoted citation or an existing fixture and is mentioned by a test; every acceptance criterion has a test module (D-0006) |
| `OUTPUT_L0_ratification.md` | Its output |
| `e0_l0_validation.py` | Runs the Layer-0 engine on the 2025 US Championship fixture and compares game by game and player by player with FIDE; its output is the evidence page `docs/evidence/E0_l0-validation.md` itself |
| `e1_fide_lists_extract.py` | Needs `data/`: anchor-cohort drift, the 1400 floor, exits, newcomers by year, age and rating, and the K distribution, from every standard, rapid and blitz list, February 2015 to October 2026; counts and medians only |
| `aggregates/E1_standard.json`, `aggregates/E1_rapid.json`, `aggregates/E1_blitz.json` | Its outputs |
| `e1_fide_lists_report.py` | Turns the E1 aggregates into the evidence page `docs/evidence/E1_fide-lists.md` |
| `e2_broadcast_extract.py` | Needs `data/`: the Lichess broadcast archive (CC BY-SA 4.0) against FIDE's lists under `docs/specs/SPEC-TABLE-FIT_v1_0.md`: coverage, descriptive measures, the rolling fits and their out-of-sample sums; counts, sums and fitted values only |
| `aggregates/E2_broadcast.json` | Its output |
| `e2_broadcast_report.py` | Applies the decision rules of annex T8 and writes `docs/evidence/E2_broadcast-calibration.md` and, with `--yaml`, `params/table_fit_2026-10.yaml` |
| `e3_us_championships.py` | Runs `tools/compare_event.py` on the 2025 and 2026 U.S. Championship event files and writes the evidence page `docs/evidence/E3_us-championship-2026.md` |
| `community/register.json` | The community register (session ELO-4, Phase 2): every item read, January 2023 to September 2026, with its themes, paraphrases, stances and author counts; every fetch attempted, including refusals; and the disposition of each theme. Compiled from the reading, not from `data/` |
| `e4_community_report.py` | Counts the register and writes the evidence page `docs/evidence/E4_community-register.md` |
| `fide_panel.py` | A module (registered under "modules"): FIDE's monthly lists as per-month arrays indexed by player, and the April 2026 batch of D-0008 R11; reads `data/`, writes nothing |
| `e5_deflation_extract.py` | Needs `data/`: the deflation question (session ELO-4, Phase 1): per-player and cross-sectional change of published ratings by group, band and age, the composition of the active list, Ghita's measures as his book defines them, the top and the spread, and the drain implied by the favourite's over-prediction on broadcast games; counts, medians, percentiles and sums only; enforces the ELO-4 data cutoff (no broadcast game after 2026-09-30) |
| `aggregates/E5_deflation.json` | Its output |
| `e5_deflation_report.py` | Turns the E5 aggregates (and E1's, for the K scheme of the rapid and blitz lists) into the evidence page `docs/evidence/E5_deflation.md` |
| `l1_common.py` | A module (registered under "modules"): the shared setup of the Layer 1 analyses (SPEC-L1): the table's parameters read from the frozen parameter file, the game records and list lookups of `src/layer1/data.py`, the anchor panels and the priors; reads `data/`, writes nothing |
| `l1_history_extract.py` | Needs `data/`: Layer 1 on history (session ELO-4, Phase 3; `docs/specs/SPEC-L1_v1_0.md`): the hyperparameters chosen on held-out games, the fit on every broadcast game with FIDE IDs from January 2023 to September 2026, σ's calibration, the anchor and spread series, the outputs of SPEC-L1 §5 at the October 2026 list (K by R6, information share and compensation by R5, seeds) and the coverage by band and age; aggregates only; the data cutoff is enforced in `src/layer1/` |
| `aggregates/L1_history.json` | Its output |
| `l1_history_report.py` | Turns the Layer 1 aggregates into `OUTPUT_L1_history.md` |
| `OUTPUT_L1_history.md` | Its output, cited by SPEC-L1 and the evidence pages |
| `e6_rungs_extract.py` | Needs `data/`: rungs 3 to 6 against Layer 0 on rolling held-out months, 2025-01 to 2026-09 (session ELO-4, Phase 4; decision D12): Layer 1 refitted each month on the 36 months before it, then newcomer seeds, K from certainty (R6), junior compensation (R5, R8) and the monthly adjustment (R3) scored under the decision rules of annex T8, with the paired moving-block bootstrap; and R12's pooled farming-region test from the E2 aggregates; aggregates only |
| `aggregates/E6_rungs.json` | Its output |
| `e6_rungs_report.py` | Applies the decision rules and writes the evidence page `docs/evidence/E6_rungs-on-history.md` |
| `e7_cross_border_extract.py` | Needs `data/`: the direction of Ghita's federation residuals on broadcast standard games (session ELO-4, Phase 5.3): his weighted, recursive cross-border index as his book and blog describe it, at the logistic scales 400 and 459, the sign test against the federations he names, the distribution of the offsets without names (annex T8.4) and the sample's rating profile against the active pool; aggregates only |
| `aggregates/E7_cross_border.json` | Its output |
| `e7_cross_border_report.py` | Writes the evidence page `docs/evidence/E7_cross-border.md` |
| `e8_k_activity_extract.py` | Needs `data/`: rung 4 redesigned (session ELO-5, Phase 1; `docs/specs/SPEC-K-ACTIVITY_v1_0.md`): the certainty σ_i built from FIDE's monthly lists alone (`src/layer2/kactivity.py`), K by ruling R16, the growth scale chosen on 2023–2024 months, and rung 4 tested exactly as E6 tested it (E6's harness functions imported unchanged); the K of established elite players and club adults at the October 2026 list; aggregates only |
| `aggregates/E8_k_activity.json` | Its output |
| `e8_k_activity_report.py` | Applies rung 4's decision rules (E6's helpers) and writes the evidence page `docs/evidence/E8_k-from-activity.md` |
| `e10_guard_extract.py` | Needs `data/`: the farming guard of ruling R17 (session ELO-5, Phase 2; `src/layer2/guard.py`): E2's sample rebuilt with E2's own functions and its 21 test months re-evaluated with E2's monthly parameters, reproducing E2's sums exactly, then with the guard: calibration bins, log-loss, and the farming region and the guard's region with E6's bootstraps; aggregates only |
| `aggregates/E10_guard.json` | Its output |
| `e10_guard_report.py` | Applies E2's decision rules (imported unchanged) with and without the guard, checks both 2026 championship fields against the guard's region, and writes the evidence page `docs/evidence/E10_farming-guard.md` |
| `outputs.json` | The registry of scripts and outputs that check (a) reruns (`tools/README.md`) |

Run: `python3 analysis/v04_calculations.py > analysis/OUTPUT_v0_4.md` and `git diff` must be empty. Scripts registered with `needs_data` read files under `data/` (never committed; `tools/README.md` says how to rebuild them); CI checks that their outputs exist and `python3 tools/checks/check_outputs.py --all` reruns them locally. Every script here is registered in `analysis/outputs.json` with the file its output must equal; check (a) of the automated check reruns them on every pull request. The v0.3 script and its output were bumped to v0.4 with `git mv`; earlier versions are in git history.

Every parameter value in the scripts is PROVISIONAL, except the expected-score table's, which `v04_calculations.py` reads from `params/table_fit_2026-10.yaml` (PROVISIONAL-FITTED, E2; `docs/decisions/D-0007_evidence-folded-into-v0.3.md`). The expected-score function is evaluated in binary floating point and rounded half up to three decimals; the Layer 1 quantities (posterior means and SDs, anchor means) are inputs chosen for illustration, not model outputs.
