"""Maximum likelihood for the v2 table (SPEC-TABLE-FIT v1.1 §2): a module of the E11 extraction, not a script.

The likelihood is summed over cells of identical (gap, level band, outcome); the parameters are
(kappa, lambda, eta, alpha, beta, gamma, mu) of src/layer2/table_v2.py, mu fixed at 0 unless the draw tail is
fitted. A damped Newton method with the analytic score and a finite-difference Hessian (as v1.0's fit in
analysis/e2_broadcast_extract.py); a step that breaks a bound is halved until it holds (kappa >= 0.05, and
0 <= gamma(L) <= 1/2 at every band midpoint); it stops when no parameter moves by more than 1e-7, or after 50
iterations; standard errors from the inverse observed information of the free parameters. Standard library only.
"""
from __future__ import annotations

import math

from layer2 import table_v2 as t2

ELLS = tuple(t2.ell(m) for m in t2.BAND_MIDS)
L_MIN, L_MAX = min(ELLS), max(ELLS)
GAMMA_MAX = 0.5


def group(cells: list[tuple]) -> list[tuple[float, list[tuple]]]:
    """Cells (x, l, s, w) grouped by level: [(l, [(x, s, w), ...]), ...] in a fixed order."""
    by: dict[float, list[tuple]] = {}
    for x, l, s, w in cells:
        by.setdefault(l, []).append((x, s, w))
    return [(l, by[l]) for l in sorted(by)]


def loglik_grad(p: list[float], grouped: list) -> tuple[float, list[float]]:
    """Log-likelihood and its score over the grouped cells."""
    kappa, lam, eta, alpha, beta, gamma, mu = p
    exp, log = math.exp, math.log
    ll = 0.0
    g0 = g1 = g2 = g3 = g4 = g5 = g6 = 0.0
    q = t2.Q
    for l, rows in grouped:
        el = exp(lam * l)
        kq = kappa * el * q
        em = exp(mu * l)
        gl = gamma * em
        base = alpha + beta * l
        for x, s, w in rows:
            z = kq * (x + eta)
            az = z if z >= 0 else -z
            nu = exp(base - gl * az)
            a = exp(z / 2.0)
            b = 1.0 / a
            den = a + b + nu
            pw, pd, pl = a / den, nu / den, b / den
            if s == 1.0:
                ll += w * log(pw)
                dr = 0.0
            elif s == 0.5:
                ll += w * log(pd)
                dr = 1.0
            else:
                ll += w * log(pl)
                dr = 0.0
            sg = 1.0 if z > 0 else -1.0 if z < 0 else 0.0
            u = w * ((s - (pw + 0.5 * pd)) - gl * sg * (dr - pd))
            uz = u * z
            g0 += uz / kappa
            g1 += uz * l
            g2 += u * kq
            r = w * (dr - pd)
            g3 += r
            g4 += l * r
            g5 -= az * em * r
            g6 -= gl * l * az * r
    return ll, [g0, g1, g2, g3, g4, g5, g6]


def feasible(p: list[float]) -> bool:
    if p[0] < 0.05 or p[5] < 0.0:
        return False
    return max(p[5] * math.exp(p[6] * L_MIN), p[5] * math.exp(p[6] * L_MAX)) <= GAMMA_MAX + 1e-12


def _solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-14:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for cc in range(c, n + 1):
                    m[r][cc] -= f * m[c][cc]
    return [m[i][n] / m[i][i] for i in range(n)]


def _hessian(p: list[float], grouped: list, free: list[int]) -> list[list[float]]:
    h_ = [[0.0] * 7 for _ in range(7)]
    for j in free:
        h = 1e-4 * max(1.0, abs(p[j]))
        pp, pm = list(p), list(p)
        pp[j] += h
        pm[j] -= h
        _, gp = loglik_grad(pp, grouped)
        _, gm = loglik_grad(pm, grouped)
        for i in range(7):
            h_[i][j] = (gp[i] - gm[i]) / (2 * h)
    return h_


def _at_bound(p: list[float], g: list[float]) -> bool:
    """gamma(L) at a bound with the score pushing outward (the free set then drops gamma, as v1.0 does)."""
    top = max(p[5] * math.exp(p[6] * L_MIN), p[5] * math.exp(p[6] * L_MAX))
    return (p[5] <= 0.0 and g[5] < 0) or (top >= GAMMA_MAX - 1e-12 and g[5] > 0)


def fit(cells: list[tuple], start: tuple, tail: bool = False) -> dict:
    """ML over cells (x, l, s, w) from start = (kappa, eta, alpha, beta, gamma) of v1.0's fit of the same window,
    with lambda = 0 and mu = 0; mu stays 0 unless tail."""
    grouped = group(cells)
    kappa, eta, alpha, beta, gamma = start
    p = [kappa, 0.0, eta, alpha, beta, min(max(gamma, 0.0), GAMMA_MAX), 0.0]
    base_free = [0, 1, 2, 3, 4, 5] + ([6] if tail else [])
    ll, g = loglik_grad(p, grouped)
    it = 0
    for it in range(1, 51):
        free = [j for j in base_free if not (j == 5 and _at_bound(p, g))]
        h_ = _hessian(p, grouped, free)
        step_free = _solve([[-h_[i][j] for j in free] for i in free], [g[i] for i in free])
        if step_free is None:
            break
        step = [0.0] * 7
        for i, j in enumerate(free):
            step[j] = step_free[i]
        t = 1.0
        accepted = None
        while t >= 1e-6:
            cand = [p[i] + t * step[i] for i in range(7)]
            if feasible(cand):
                ll_c, g_c = loglik_grad(cand, grouped)
                if ll_c >= ll - 1e-9:
                    accepted = (cand, ll_c, g_c)
                    break
            t /= 2
        if accepted is None:
            break
        cand, ll_c, g_c = accepted
        moved = max(abs(cand[i] - p[i]) for i in range(7))
        p, ll, g = cand, ll_c, g_c
        if moved < 1e-7:
            break
    free = [j for j in base_free if not (j == 5 and _at_bound(p, g))]
    h_ = _hessian(p, grouped, free)
    se: dict = {}
    for k, j in enumerate(free):
        e = [1.0 if i == k else 0.0 for i in range(len(free))]
        col = _solve([[-h_[i][jj] for jj in free] for i in free], e)
        se[t2.NAMES[j]] = math.sqrt(col[k]) if col is not None and col[k] > 0 else None
    out = {name: p[i] for i, name in enumerate(t2.NAMES)}
    out.update({"loglik": ll, "n": int(sum(c[3] for c in cells)), "cells": len(cells), "iterations": it,
                "tail": tail, "gamma_at_bound": 5 not in free, "se": se,
                "max_abs_score": max(abs(g[j]) for j in free)})
    return out


def par_of(f: dict) -> tuple:
    return tuple(f[k] for k in t2.NAMES)
