#!/usr/bin/env python3
"""E9 runs: the simulator of docs/specs/SPEC-SIM_v1_0.md, every scenario and seed (ELO-5, Phase 3; slow).

Runs `src/simulator` on the scenarios of SPEC-SIM §3.5 and §9 in parallel processes (each run deterministic
for its seed; results gathered in input order), and prints aggregates only: per scenario and ledger the
measurements of §6 and §7 for every seed, and the calibration of R1's review threshold of §8 on twenty
paired baseline and ratchet runs. No data/ is read: the pool is synthetic, calibrated on the committed
evidence. Takes minutes: registered as slow in analysis/outputs.json, rerun by check (a) with --all.

Usage: python3 analysis/e9_simulator_run.py > analysis/aggregates/E9_simulator.json
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, replace
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from simulator import config as C  # noqa: E402
from simulator import run as R  # noqa: E402

SEEDS = [20261010 + k for k in range(5)]
R1_SEEDS = [20262000 + k for k in range(20)]
SCENARIOS = ("baseline", "noise2", "deflation", "federations", "adversaries")
THETAS = (0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04)


def one(task: tuple) -> dict:
    name, seed, kw = task
    return R.run(C.scenario(name, seed, **kw))


def mean(v: list) -> float | None:
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 3) if v else None


def summarise(run: dict) -> dict:
    """The per-run measurements kept for the report (SPEC-SIM §6, §7)."""
    out = {"pool": run["pool"], "fed_offsets_at_adoption": run["fed_offsets_at_adoption"],
           "fed_offsets_end": run["fed_offsets_end"], "newcomer_n50": run["newcomer_n50"],
           "junior_drain": {n: {b: [v[0], round(v[1] / v[0], 2)] for b, v in sorted(d.items())}
                            for n, d in run["junior_drain"].items()},
           "ledger_lines": {n: {k: round(v, 1) for k, v in d.items()} for n, d in run["ledger_lines"].items()},
           "calibration": run["calibration"], "adversaries": run.get("adversaries")}
    err = {}
    for n, e in run["err"].items():
        err[n] = {k: {"n": a[0], "bias_raw": round(a[1] / a[0], 1), "bias": round(a[2] / a[0], 1),
                      "rmse": round(math.sqrt(a[3] / a[0]), 1)} for k, a in sorted(e.items())}
    out["error"] = err
    ser = {}
    for n, s in run["series"].items():
        yearly = {k: [s[k][i] for i in range(11, len(s[k]), 12)] for k in ("level", "d_t", "spread_true", "spread_r1",
                                                                          "n_2600_pub", "n_2600_true")}
        d = s["d_t"]
        r15 = [abs(d[i] - d[i - 12]) for i in range(12, len(d)) if d[i] is not None and d[i - 12] is not None]
        ser[n] = {"yearly": yearly, "top_change": s.get("top_change"), "top_true_change": s.get("top_true_change"),
                  "a_t_mean": mean(s["a_t"]), "a_t_abs_max": max(abs(a) for a in s["a_t"]),
                  "r15_max_12m_change_from_month_13": round(max(r15), 2) if r15 else None,
                  "r15_share_within_2": round(sum(1 for x in r15 if x <= 2.0) / len(r15), 3) if r15 else None,
                  "d_t_first_year_mean": mean(d[:12]), "d_t_last_year_mean": mean(d[-12:])}
    out["series"] = ser
    return out


def trailing12(v: list) -> list:
    return [sum(v[i - 11:i + 1]) / 12 for i in range(11, len(v))]


def r1_calibration(base: list[dict], ratchet: list[dict]) -> dict:
    """SPEC-SIM §8 with D-0009 readings 5 and 6: the trailing twelve-month mean of R2's noise-corrected spread
    ratio, its reference after the first twelve months of operation; raw triggers in the baseline, the
    false-alarm rate of the noise alone (the series net of its own linear trend), and the months a ratchet at
    κ's annual cap takes to trigger on its own (the paired difference, ratchet minus baseline, same seed)."""
    rows = []
    for b, r in zip(base, ratchet):
        mb = trailing12(b["series"]["R2"]["spread_r1"])
        mr = trailing12(r["series"]["R2"]["spread_r1"])
        dev = [x - mb[0] for x in mb]
        n = len(dev)
        tbar = (n - 1) / 2
        slope = sum((t - tbar) * dev[t] for t in range(n)) / sum((t - tbar) ** 2 for t in range(n))
        noise = [dev[t] - slope * (t - tbar) - (dev[0] - slope * (0 - tbar)) for t in range(n)]
        diff = [x - y for x, y in zip(mr, mb)]
        rows.append({"slope_per_year": round(12 * slope, 4), "raw": dev, "noise": noise, "ratchet": diff})
    out = {"runs": len(rows), "slope_per_year": [x["slope_per_year"] for x in rows],
           "noise_sd": round(math.sqrt(sum(v * v for x in rows for v in x["noise"]) / sum(len(x["noise"]) for x in rows)), 4)}
    per = {}
    for th in THETAS:
        first = lambda s: next((t for t, v in enumerate(s) if abs(v) > th), None)  # noqa: E731
        raw = [first(x["raw"]) for x in rows]
        noise = [first(x["noise"]) for x in rows]
        rat = [first(x["ratchet"]) for x in rows]
        per[str(th)] = {"raw_trigger_share": round(sum(v is not None for v in raw) / len(rows), 3),
                        "raw_median_months": sorted(v for v in raw if v is not None)[len([v for v in raw if v is not None]) // 2]
                        if any(v is not None for v in raw) else None,
                        "noise_false_alarm_share": round(sum(v is not None for v in noise) / len(rows), 3),
                        "ratchet_detect_share": round(sum(v is not None for v in rat) / len(rows), 3),
                        "ratchet_median_months": sorted(v for v in rat if v is not None)[len([v for v in rat if v is not None]) // 2]
                        if any(v is not None for v in rat) else None}
    out["thresholds"] = per
    ok = [th for th in THETAS if per[str(th)]["noise_false_alarm_share"] <= 0.05]
    out["calibrated"] = min(ok) if ok else None
    return out


def main() -> int:
    tasks = [(s, seed, {}) for s in SCENARIOS for seed in SEEDS]
    r1 = [("baseline", seed, {"ledgers": ("L0", "R2")}) for seed in R1_SEEDS] + \
         [("ratchet", seed, {}) for seed in R1_SEEDS]
    with Pool(8) as pool:
        runs = pool.map(one, tasks + r1, chunksize=1)
    main_runs, r1_runs = runs[:len(tasks)], runs[len(tasks):]
    out = {"spec": "docs/specs/SPEC-SIM_v1_0.md", "seeds": SEEDS, "r1_seeds": R1_SEEDS,
           "defaults": {k: v for k, v in asdict(C.Config()).items() if k not in ("extra",)},
           "scenarios": {}}
    for (name, seed, _kw), run in zip(tasks, main_runs):
        out["scenarios"].setdefault(name, {})[str(seed)] = summarise(run)
    out["r1_calibration"] = r1_calibration(r1_runs[:len(R1_SEEDS)], r1_runs[len(R1_SEEDS):])
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=list)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
