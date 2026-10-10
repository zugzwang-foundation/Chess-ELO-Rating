#!/usr/bin/env python3
"""Rung 5's inputs for the 2026 U.S. Championships, frozen before any result is read (ELO-5, Phase 6; needs data/).

Fits Layer 1 (docs/specs/SPEC-L1_v1_0.md) once, as E6 fits it at a test month, for the list in force at the
championships, October 2026: the 36 months before it, 2023-10 to 2026-09, with the hyperparameters chosen on
history (`analysis/aggregates/L1_history.json`). The data cutoff (no broadcast file after 2026-09, no game dated
after 2026-09-30) is enforced by `layer1.data` and again by `layer1.fit`, so no game of either championship can
enter. For every player of the two fields (`tools/events/`), in standard, it applies annex T4.6's gates and R5's
information share and computes the compensation c_j with E6's functions (`layer1.outputs`), and prints, per
player, the gates, the eligibility flag and c_j only: the model's estimates of named players go to the QC only
(D17), while the flag and RX = R + c_j are list columns (R20). The output is the frozen parameter file that
`tools/compare_pilot.py` reads for the PILOT column (Freeze 2). Standard library only.

Usage: python3 analysis/us26_rung5_extract.py > params/rung5_us2026.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import l1_common as c  # noqa: E402
from layer1 import data, fit, outputs  # noqa: E402

EVENTS = ("tools/events/us_championship_2026.json", "tools/events/us_womens_championship_2026.json")
LIST_IN_FORCE = (2026, 10)
WINDOW = 36
TC = 0                                   # standard


def main() -> int:
    s = c.load()
    chosen = json.loads((ROOT / "analysis" / "aggregates" / "L1_history.json").read_text(encoding="utf-8"))["fit"]["chosen"]
    hyper = fit.Hyper(c_theta=chosen["c_theta"], omega=chosen["omega"], max_sweeps=150)
    t = fit.month_index(*LIST_IN_FORCE)
    lo, hi, lab = fit.month_label(t - WINDOW), fit.month_label(t - 1), fit.month_label(t)
    f = c.fit_window(s, lo, hi, hyper)
    name = c.TCS[TC]
    pres = [(p, f.index[p], s.lists.rating(name, lab, str(p))) for p in s.panels[TC] if p in f.index]
    pres = [(p, i, r) for p, i, r in pres if r]
    m_t = sum(r for _, _, r in pres) / len(pres)
    m_hat = sum(fit.strength(f, i, TC, t) for _, i, _ in pres) / len(pres)
    played: dict[tuple[int, int], list] = defaultdict(list)
    for g in s.games:
        if t - WINDOW <= g.month <= t - 1:
            played[(g.white, g.tc)].append((g.month, g.black, g.tour))
            played[(g.black, g.tc)].append((g.month, g.white, g.tour))
    events = [(path, json.loads((ROOT / path).read_text(encoding="utf-8"))) for path in EVENTS]
    field = data.Lists(ROOT)                  # the list in force for every player of the fields, in the fit or not
    field.load(name, lab, {str(pl["fide_id"]) for _, ev in events for pl in ev["players"]})
    rows = []
    for path, event in events:
        for pl in sorted(event["players"], key=lambda p: p["fide_id"]):
            p = pl["fide_id"]
            r = field.rating(name, lab, str(p))
            if r != pl["rating"]:
                raise SystemExit(f"{p}: the event file's rating {pl['rating']} is not the {lab} list's {r}")
            by = s.birth.get(p) or field.birth.get(str(p))
            age = (t // 12) - by if by else None
            row = {"event": path, "fide_id": p, "age_at_most_19": age is not None and age <= 19}
            i = f.index.get(p)
            if not row["age_at_most_19"] or i is None:
                row.update({"in_fit": i is not None, "eligible": False, "c_j": 0})
                rows.append(row)
                continue
            s_hat = fit.strength(f, i, TC, t)
            sg = fit.sigma_tc(fit.covariance_at(f, i, t), TC)
            theta_t = outputs.theta_tilde(s_hat, m_t, m_hat, s.kappa[TC])
            hist = played[(p, TC)]
            others = tuple(o for o in range(3) if o != TC)
            if not any(played.get((p, o)) for o in others):
                share = 1.0
            else:
                c_tc = fit.covariance_at(f, i, t, fit.last_cov_variant(f, i, drop_tc=others))
                c_0 = fit.covariance_at(f, i, t, fit.last_cov_variant(f, i, with_games=False))
                share = outputs.info_share(1 / sg ** 2, 1 / fit.sigma_tc(c_tc, TC) ** 2, 1 / fit.sigma_tc(c_0, TC) ** 2)
            opponents, tours = {x[1] for x in hist}, {x[2] for x in hist}
            eligible = outputs.junior_eligible(age, len(hist), len(opponents), len(tours), share)
            row.update({"in_fit": True, "games_in_window": len(hist), "opponents": len(opponents), "events": len(tours),
                        "info_share_at_least_half": share >= 0.5, "eligible": eligible,
                        "c_j": outputs.compensation(theta_t, sg / s.kappa[TC], r, eligible)})
            rows.append(row)
    out = {"status": "FROZEN (Freeze 2) — rung 5, PILOT; every parameter PROVISIONAL (annex T1, T4.6)",
           "generated_by": "analysis/us26_rung5_extract.py",
           "spec": "docs/specs/SPEC-L1_v1_0.md; annex T4.6 (R5, R8, R18, R20); E6's functions (layer1.outputs)",
           "list_in_force": lab, "fit_window": [lo, hi], "data_cutoff": fit.CUTOFF.isoformat(),
           "hyperparameters": {"c_theta": hyper.c_theta, "omega": hyper.omega},
           "fit": {"games": f.games_used, "players": len(f.players), "sweeps": f.sweeps, "max_move": round(f.max_move, 4)},
           "anchor_standard": {"members_in_fit": len(pres), "m_t": round(m_t, 2), "m_hat_t": round(m_hat, 2),
                               "d_t": round(m_hat - m_t, 2)},
           "compensation": {"tau": outputs.TAU, "c_cap": outputs.C_CAP, "z": outputs.Z90},
           "players": rows}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
