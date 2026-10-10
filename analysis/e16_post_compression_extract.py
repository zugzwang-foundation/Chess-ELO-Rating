#!/usr/bin/env python3
"""E16 extraction: rung 2 v2 refitted on games after the March 2024 compression (session ELO-6, Phase 5, after
Freeze 3; review finding ELO6-STAT-2; needs data/).

On the March 2024 lists FIDE raised every rating below 2000 once, by round(0.4 x (2000 - R)), in all three time
controls [E5], so a fit window that reaches back before March 2024 pools games rated on two published scales. E11
fitted the v2 table on 36-month windows that do: the published fit (2023-10 to 2026-09) holds five months before the
compression, the rolling fits of the 21 test months up to 26. This script repeats E11's fits and evaluation with the
functions of analysis/e11_table_by_level_extract.py, imported unchanged, and with every fit window cut at 2024-03:
the rolling fit of each of E2's 21 test months on max(t - 36, 2024-03) to t - 1, and a fit on 2024-03 to 2026-09
in place of the published one, each with the model E11 published for that time control (the draw tail in standard,
the slope by level alone in rapid and blitz). The frozen table (params/table_fit_2026-10b.yaml, Freeze 3) is not
changed: the refit is shown beside it (docs/evidence/E16_rung2-under-review.md). The data cutoff is E10's builder's.
Only aggregates leave the script.

Usage: python3 analysis/e16_post_compression_extract.py > analysis/aggregates/E16_post_compression.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's helpers, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import e11_table_by_level_extract as e11x  # noqa: E402  (E11's fit task and evaluation, unchanged)
import table_v2_fit as tf  # noqa: E402

COMPRESSION = "2024-03"          # the first list on the compressed scale [E5]
LAST = "2026-09"


def main() -> int:
    e2 = json.loads((ROOT / "analysis" / "aggregates" / "E2_broadcast.json").read_text(encoding="utf-8"))
    e11 = json.loads((ROOT / "analysis" / "aggregates" / "E11_table_by_level.json").read_text(encoding="utf-8"))
    smp, meta = e10.sample()
    out: dict = {"cutoff": meta, "compression_list": COMPRESSION, "rolling": {}, "fit": {}}
    with Pool(8) as pool:
        for tc in e2x.TCS:
            tail = "tail" in e11["rolling"][tc]
            rr = e2["rolling"][tc]
            S = smp[tc]
            months = sorted({row[0] for row in S})
            cells_by_month: dict[str, Counter] = {m: Counter() for m in months}
            draws_by_month: dict[str, Counter] = {m: Counter() for m in months}
            games_by_month: dict[str, list[tuple]] = {m: [] for m in months}
            for m, tour, w, b, rw, rb, s, e0 in S:
                mid = e2x.band100_mid((rw + rb) // 2)
                cells_by_month[m][(rw - rb, mid, s)] += 1
                draws_by_month[m][(mid, s == 0.5)] += 1
                games_by_month[m].append((w, b, rw, rb, s, e0))

            def window_cells(lo: str, hi: str) -> list[tuple]:
                agg = Counter()
                for mm in months:
                    if lo <= mm <= hi:
                        agg.update(cells_by_month[mm])
                return [(x, (mid - 2000.0) / 400.0, s, float(wt)) for (x, mid, s), wt in sorted(agg.items())]

            test = rr["test_months"]
            starts = {m: tuple(rr["per_month"][m]["params"][k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
                      for m in test}
            windows = {m: (max(e2x.month_add(m, -e2x.WINDOW), COMPRESSION), e2x.month_add(m, -1)) for m in test}
            fits = dict(zip(test, pool.map(e11x.fit_task, [(window_cells(*windows[m]), starts[m], tail) for m in test],
                                           chunksize=1)))
            res = e11x.evaluate(rr, months, fits, games_by_month, draws_by_month)
            res["level_pattern"] = e11x.level_pattern(res["bands"]["v2"])
            f1 = e2["final_fit"][tc]
            start = tuple(f1[k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
            out["rolling"][tc] = {"model": "tail" if tail else "lambda", "test_months": test,
                                  "windows": {m: list(windows[m]) for m in test}, "evaluation": res}
            out["fit"][tc] = {"from": COMPRESSION, "to": LAST, "model": "tail" if tail else "lambda",
                              "params": tf.fit(window_cells(COMPRESSION, LAST), start, tail)}
            print(f"{tc}: {len(test)} rolling fits from {COMPRESSION}; reproduces E2 within "
                  f"{res['reproduces_e2']['max_abs_difference_of_monthly_sums']:.2e}", file=sys.stderr, flush=True)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
