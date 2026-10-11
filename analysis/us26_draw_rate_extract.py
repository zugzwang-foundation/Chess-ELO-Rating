#!/usr/bin/env python3
"""The draw rate by level band behind column (a)'s three-outcome forecast in the championships' forecast test (R54), frozen
before any result is read (session ELO-8, Phase 0, Freeze 3b, docs/decisions/D-0014_forecast-test-and-rulings.md; needs
data/).

Table 8.1.2 gives an expected score and no draw probability, so a three-outcome log-loss for FIDE's expectation needs a
draw share. As E2 does for Layer 0 (docs/specs/SPEC-TABLE-FIT_v1_0.md §3; analysis/e2_broadcast_extract.py), the share is
the draw rate of the game's 100-point level band in the training months, here those of the v2 table the comparison uses
(params/table_fit_2026-10b.yaml, standard, fitted on broadcast games of 2023-10 to 2026-09). The sample is E11's, built
with E10's builder (analysis/e10_guard_extract.py: E2's functions, the data cutoff of 2026-09-30 enforced) from the
archive files E11 read (2023-01 to 2026-09; the files of 2020 to 2022, added in session ELO-7 for E17, are left out so
that the sample is E11's game for game). The script checks that it is: the window's games, cells and the log-likelihood
at E11's published fit must equal E11's (analysis/aggregates/E11_table_by_level.json). It prints the games and draws of
each band in the window and their rate, counts only. Python standard library only.

Usage: python3 analysis/us26_draw_rate_extract.py > params/draw_rate_2026-10b.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's helpers, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import table_v2_fit as tf  # noqa: E402  (E11's likelihood, unchanged)
from layer2 import table_v2 as t2  # noqa: E402

TABLE = "params/table_fit_2026-10b.yaml"
TC = "standard"
FIRST_FILE = "2023-01"            # the archive as E11 read it
_LOAD = e2x.load_games


def load_games_as_e11() -> tuple[list, dict]:
    """E2's loader, unchanged, keeping the games of the files E11 read (2023-01 to 2026-09)."""
    games, raw = _LOAD()
    return [g for g in games if g.file_month >= FIRST_FILE], raw


def main() -> int:
    text = (ROOT / TABLE).read_text(encoding="utf-8")
    w = re.search(rf"^{TC}:\n(?:  .*\n)*?  fit_window: \{{from: \"([\d-]+)\", to: \"([\d-]+)\"\}}", text, re.M)
    lo, hi = w.group(1), w.group(2)
    e2x.load_games = load_games_as_e11            # E10's builder calls E2's loader; only the file filter is added
    smp, meta = e10.sample()
    e2x.load_games = _LOAD
    games, draws, cells = Counter(), Counter(), Counter()
    for m, _tour, _w, _b, rw, rb, s, _e0 in smp[TC]:
        if lo <= m <= hi:
            mid = e2x.band100_mid((rw + rb) // 2)
            games[mid] += 1
            draws[mid] += s == 0.5
            cells[(rw - rb, mid, s)] += 1
    e11 = json.loads((ROOT / "analysis" / "aggregates" / "E11_table_by_level.json").read_text(encoding="utf-8"))
    f = e11["final_fit"][TC]
    pub = f["tail"] if "tail" in f else f["lambda"]
    grouped = tf.group([(x, t2.ell(mid), s, float(n)) for (x, mid, s), n in sorted(cells.items())])
    ll, _g = tf.loglik_grad(list(tf.par_of(pub)), grouped)
    check = {"games": sum(games.values()), "cells": len(cells), "loglik_at_E11_fit": round(ll, 6),
             "E11_games": pub["n"], "E11_cells": pub["cells"], "E11_loglik": round(pub["loglik"], 6)}
    if (check["games"], check["cells"]) != (pub["n"], pub["cells"]) or abs(ll - pub["loglik"]) > 1e-6 * abs(ll):
        raise SystemExit(f"the window's sample is not E11's: {check}")
    out = {
        "status": "MEASURED on broadcast games, PROVISIONAL: frozen in Freeze 3b (D-0014) before any result of the 2026 "
                  "U.S. Championships was read",
        "use": "column (a)'s three-outcome forecast in the championships' forecast test (R54): FIDE's expected score split "
               "with the draw rate of the game's 100-point level band (E2's construction, SPEC-TABLE-FIT v1.0 §3)",
        "source": "Lichess broadcast archive (https://database.lichess.org/broadcast/, CC BY-SA 4.0), E11's sample: "
                  "files 2023-01 to 2026-09, games dated to 2026-09-30, both players on FIDE's standard list in force",
        "generated_by": "analysis/us26_draw_rate_extract.py",
        "table": TABLE, "time_control": TC, "window": [lo, hi], "cutoff": meta,
        "reproduces_E11": check,
        "bands": {str(mid): {"games": games[mid], "draws": draws[mid], "rate": round(draws[mid] / games[mid], 6)}
                  for mid in sorted(games)},
    }
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
