"""The simulator: a synthetic rated pool with known true strengths (docs/specs/SPEC-SIM_v1_0.md; annex T9).

Not engine code: it runs Layer 0 (integer port of SPEC-L0, `fide`) and each rung (`ledger`) on the same simulated
games (`pool`, `events`), with a forward-filter proxy of Layer 1 (`proxy`); `run.run(config)` returns aggregates.
Standard library only.
"""
