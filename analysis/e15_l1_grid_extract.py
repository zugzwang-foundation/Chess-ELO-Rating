#!/usr/bin/env python3
"""E15 extraction: Layer 1's hyperparameter grids widened beyond their edges (ruling R41; session ELO-6, Phase 5; needs data/).

SPEC-L1 §4.6 chose c_θ and ω on held-out games (fit 2023-01 to 2024-09, score 2024-10 to 2024-12, three-outcome
log-loss), first c_θ in {0.5, 1.0, 2.0} at ω = 8.0, then ω in {4.0, 16.0} at the best c_θ; both choices, c_θ = 2.0
and ω = 4.0, sat at the edges of their grids (analysis/aggregates/L1_history.json). R41 widens the grids beyond those
edges and refits (D-0011, reading 15): each grid is extended by two of its own steps (factors of two), c_θ to 4.0 and
8.0 and ω to 2.0 and 1.0, and searched as before: c_θ in {2.0, 4.0, 8.0} at ω = 4.0, then ω in {1.0, 2.0, 4.0} at the
best c_θ. The point (2.0, 4.0) is refitted and must reproduce L1_history.json's value. The fits, data and protocol
are analysis/l1_history_extract.py's (its grid_job imported unchanged), with the data cutoff enforced in src/layer1/.
Only the grid's held-out scores leave the script.

Usage: python3 analysis/e15_l1_grid_extract.py > analysis/aggregates/E15_l1_grid.json
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import l1_common as c  # noqa: E402
import l1_history_extract as l1h  # noqa: E402  (the grid's fit and score, unchanged)

C_THETA = (2.0, 4.0, 8.0)
OMEGA = (1.0, 2.0, 4.0)


def main() -> int:
    l1h.S = c.load()
    ctx = mp.get_context("fork")
    with ctx.Pool(3) as pool:
        first = pool.map(l1h.grid_job, [(ct, 4.0) for ct in C_THETA])
    best_c = min(first, key=lambda r: (r["log_loss"], r["c_theta"]))["c_theta"]
    with ctx.Pool(2) as pool:
        second = pool.map(l1h.grid_job, [(best_c, om) for om in OMEGA if om != 4.0])
    grid = first + second
    best = min(grid, key=lambda r: (r["log_loss"], r["c_theta"], r["omega"]))
    old = json.loads((ROOT / "analysis" / "aggregates" / "L1_history.json").read_text(encoding="utf-8"))["fit"]
    ref = next(r for r in first if r["c_theta"] == 2.0)
    out = {"protocol": {"fit": list(l1h.GRID_FIT), "score": list(l1h.GRID_TEST), "c_theta": list(C_THETA),
                        "omega": list(OMEGA)},
           "previous": {"grid": old["grid"], "chosen": old["chosen"]},
           "reproduces_previous_point": ref["log_loss"] == old["chosen"]["log_loss"],
           "grid": grid, "chosen": best,
           "at_edge": {"c_theta": best["c_theta"] == max(C_THETA), "omega": best["omega"] == min(OMEGA)}}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
