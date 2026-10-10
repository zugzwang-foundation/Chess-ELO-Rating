"""Shared setup for the Layer 1 analyses on history (SPEC-L1; needs data/, never committed).

A module, not a script: `analysis/l1_history_extract.py` (Phase 3) and the rung
tests of Phase 4 import it. It reads the published table's parameters from the
frozen parameter file (read only), builds the game records and the FIDE-list
lookups through `layer1.data`, the anchor panels of SPEC-L1 §3.5, and the priors
of §3.4. Nothing here writes any file. Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from layer1 import data, fit, model  # noqa: E402

TCS = data.TCS
T_REF = "2025-01"
S_LIST, S_0 = 120.0, 250.0
# SPEC-L1 §3.4: E1's age group that holds most of each Layer 1 age band (2025 newcomers' median first rating)
E1_GROUP_OF_BAND = ("<10", "10-14", "15-19", "20-29", "30-49", "50+", "50+")


def table_params() -> dict[int, dict[str, float]]:
    """κ, η, α, β, γ of each time control from params/table_fit_2026-10.yaml (Freeze 1; read only)."""
    out, tc = {}, None
    for line in (ROOT / "params" / "table_fit_2026-10.yaml").read_text(encoding="utf-8").splitlines():
        if line in ("standard:", "rapid:", "blitz:"):
            tc = TCS.index(line[:-1])
            out[tc] = {}
            continue
        m = re.match(r"\s+(kappa|eta|alpha|beta|gamma): \{value: ([-0-9.]+)", line)
        if m and tc is not None:
            out[tc][m.group(1)] = float(m.group(2))
    return out


def outcome_latent(tp: dict) -> dict[str, tuple]:
    """SPEC-L1 §3.2: the table's outcome parameters in latent units."""
    return {"eta": tuple(tp[t]["kappa"] * tp[t]["eta"] for t in range(3)),
            "alpha": tuple(tp[t]["alpha"] for t in range(3)), "beta": tuple(tp[t]["beta"] for t in range(3)),
            "gamma": tuple(tp[t]["gamma"] for t in range(3))}


def newcomer_mu0_published() -> list[float]:
    e1 = json.loads((ROOT / "analysis" / "aggregates" / "E1_standard.json").read_text(encoding="utf-8"))
    by_age = e1["newcomers_by_year"]["2025"]["by_age"]
    return [float(by_age[g]["median"]) for g in E1_GROUP_OF_BAND]


@dataclass
class Setup:
    games: list
    lists: data.Lists
    meta: dict
    tp: dict
    kappa: tuple
    panels: dict          # tc -> {player: published rating at T_REF}
    m_ref: dict           # tc -> panel published mean
    birth: dict           # player -> year of birth
    mu0_pub: list


def load() -> Setup:
    games, lists, meta = data.build_games(ROOT)
    tp = table_params()
    kappa = tuple(tp[t]["kappa"] for t in range(3))
    in_fit: dict[int, set] = {0: set(), 1: set(), 2: set()}
    for g in games:
        in_fit[g.tc].update((g.white, g.black))
    panels = {}
    for tc, name in enumerate(TCS):
        raw = data.anchor_panel(ROOT, name, T_REF)
        panels[tc] = {int(p): r for p, r in sorted(raw.items(), key=lambda kv: int(kv[0])) if int(p) in in_fit[tc]}
    m_ref = {tc: sum(v.values()) / len(v) for tc, v in panels.items()}
    for tc, name in enumerate(TCS):                     # every list of the window, for priors and outputs
        for y in range(2023, 2027):
            for mo in range(1, 13):
                lm = f"{y:04d}-{mo:02d}"
                if lm <= "2026-10":
                    lists.load(name, lm, {str(p) for p in in_fit[0] | in_fit[1] | in_fit[2]})
    birth = {int(p): b for p, b in lists.birth.items()}
    return Setup(games, lists, meta, tp, kappa, panels, m_ref, birth, newcomer_mu0_published())


def prior_factory(s: Setup):
    """SPEC-L1 §3.4: the published rating on the list of the first month stands in for the previous fit; otherwise the
    age-only newcomer prior. No federation."""
    mu_init = {0: 0.0, 1: s.m_ref[1] - s.m_ref[0], 2: s.m_ref[2] - s.m_ref[0]}

    def prior_of(player: int, month: int) -> fit.Prior:
        lm = fit.month_label(month)
        for tc, name in enumerate(TCS):
            r = s.lists.rating(name, lm, str(player))
            if r:
                return fit.Prior(s.m_ref[tc] + s.kappa[tc] * (r - s.m_ref[tc]) - mu_init[tc], S_LIST ** 2)
        by = s.birth.get(player)
        band = model.age_band((month // 12) - by if by else None)
        return fit.Prior(s.m_ref[0] + s.kappa[0] * (s.mu0_pub[band] - s.m_ref[0]), S_0 ** 2)
    return prior_of


def fit_window(s: Setup, first: str, last: str, hyper: fit.Hyper, warm: fit.Fit | None = None, log=None) -> fit.Fit:
    """One MAP fit on the games of months first..last (SPEC-L1 §4)."""
    games = [g for g in s.games if first <= fit.month_label(g.month) <= last]
    f = fit.build(games, s.birth, prior_factory(s), hyper, outcome=outcome_latent(s.tp))
    if warm is not None:
        from layer1 import forecast
        forecast.warm_start(f, warm)
    panels = {tc: [(f.index[p], r) for p, r in v.items() if p in f.index] for tc, v in s.panels.items()}
    y, m = int(T_REF[:4]), int(T_REF[5:7])
    return fit.run(f, panels, fit.month_index(y, m), log=log)
