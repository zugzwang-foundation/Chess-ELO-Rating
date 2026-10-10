#!/usr/bin/env python3
"""E14 runs: the simulator rerun with the v2 table as the pool's true model (session ELO-6, Phase 5; slow).

E9's runs (analysis/e9_simulator_run.py, imported unchanged: its scenarios, seeds, thresholds and summaries) with the
replacements of src/simulator/v2.py installed in every worker process: the v2 table (E11) as the true outcome model
and as Layer 1's proxy's model; rung 2's ledgers on the published v2 table, with the narrowed guard (R24, E12) and K
times the printed slope ratio (R32); rung 4's K fixed per event (R25); accrual ending three months after the last
rated game (R33). Added to E9's summaries: rung 6 scored on the growth of |d_t| (R30), the per-player line-2 creation
that sizes R29's cap, and R1's review under R31 and R40 (the spread condition paired with κ at its annual cap). No
data/ is read. Takes minutes: registered as slow in analysis/outputs.json, rerun by check (a) with --all.

Usage: python3 analysis/e14_simulator_v2_run.py > analysis/aggregates/E14_simulator_v2.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e9_simulator_run as e9  # noqa: E402  (E9's scenarios, seeds, thresholds and summaries, unchanged)
from simulator import config as C  # noqa: E402
from simulator import v2  # noqa: E402

V2_TABLE = "params/table_fit_2026-10b.yaml"
V2_GUARD = "params/guard_2026-10b.yaml"


def one(task: tuple) -> dict:
    name, seed, kw = task
    return v2.run_v2(C.scenario(name, seed, **kw))


def summarise(run: dict) -> dict:
    """E9's summary of one run, with rung 6 scored under R30 and R29's line-2 statistics."""
    out = e9.summarise(run)
    for n, s in run["series"].items():
        d = s["d_t"]
        g = [abs(d[i]) - abs(d[i - 12]) for i in range(12, len(d)) if d[i] is not None and d[i - 12] is not None]
        out["series"][n]["r30_share_not_widening_beyond_2"] = round(sum(1 for x in g if x <= 2.0) / len(g), 3) if g else None
        out["series"][n]["r30_largest_widening"] = round(max(g), 2) if g else None
    out["line2"] = run["line2"]
    return out


def paired_trigger(ratchet: list[dict]) -> dict:
    """R31 and R40 (D-0011, reading 13): the review triggers when the trailing twelve-month mean of the noise-corrected
    spread ratio has moved more than θ_R1 from its reference AND κ has sat at its annual cap. In the simulator κ is
    held fixed outside the ratchet scenario, so it never sits at its cap there and the paired trigger cannot fire from
    noise; in the ratchet runs κ sits at its cap from the twelfth month of operation, and the trigger is the raw
    statistic's first crossing from then on."""
    out = {}
    for th in e9.THETAS:
        months = []
        for r in ratchet:
            m = e9.trailing12(r["series"]["R2"]["spread_r1"])
            dev = [x - m[0] for x in m]
            first = next((t for t, v in enumerate(dev) if t >= 1 and abs(v) > th), None)
            months.append(first)
        hit = sorted(v for v in months if v is not None)
        out[str(th)] = {"detect_share": round(len(hit) / len(ratchet), 3),
                        "median_months": hit[len(hit) // 2] if hit else None}
    return out


def main() -> int:
    tasks = [(s, seed, {}) for s in e9.SCENARIOS for seed in e9.SEEDS]
    r1 = [("baseline", seed, {"ledgers": ("L0", "R2")}) for seed in e9.R1_SEEDS] + \
         [("ratchet", seed, {}) for seed in e9.R1_SEEDS]
    with Pool(8) as pool:
        runs = pool.map(one, tasks + r1, chunksize=1)
    main_runs, r1_runs = runs[:len(tasks)], runs[len(tasks):]
    out = {"spec": "docs/specs/SPEC-SIM_v1_0.md", "v2": {"table": V2_TABLE, "guard": V2_GUARD,
                                                          "module": "src/simulator/v2.py", "parameters": list(v2.PAR),
                                                          "k_scale": {str(k): v for k, v in sorted(v2.M100.items())},
                                                          "guard_applies": v2.GUARD_APPLIES},
           "seeds": e9.SEEDS, "r1_seeds": e9.R1_SEEDS,
           "defaults": {k: v for k, v in asdict(C.Config()).items() if k not in ("extra",)},
           "scenarios": {}}
    for (name, seed, _kw), run in zip(tasks, main_runs):
        out["scenarios"].setdefault(name, {})[str(seed)] = summarise(run)
    out["r1_calibration"] = e9.r1_calibration(r1_runs[:len(e9.R1_SEEDS)], r1_runs[len(e9.R1_SEEDS):])
    out["r1_paired_trigger"] = paired_trigger(r1_runs[len(e9.R1_SEEDS):])
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=list)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
