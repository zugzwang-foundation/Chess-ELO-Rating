"""The self-calibrating table's model and its fit (SPEC-SELFCAL v1.0 §5; SPEC-TABLE-FIT v1.2 §2): a module of the E18 and
E19 extractions, not a script.

White's view, with q = ln 10/400, L the midpoint of the 100-point level band and l = (L - 2000)/400:
  z = kappa(L) q (x + eta(L)),  nu = exp(alpha + beta l - gamma(L) |z|),  P_W : P_D : P_L = e^{z/2} : nu : e^{-z/2};
  kappa(L) of form E, kappa exp(lambda l), or of form P, piecewise-linear between the knots 1500, 1700, ..., 2700 and
  constant beyond them; eta(L) = eta + zeta l; gamma(L) = gamma exp(mu l).
A table is a dict {"form": {"slope": "E" | "P", "colour_by_level": bool, "tail": bool}, "par": {name: value}}; a
parameter outside the form (zeta without the colour term by level, mu without the tail) is 0. The fit maximises the
likelihood over cells (x, band midpoint, score, weight) with box bounds (kappa(L) >= 0.05 through each slope parameter,
gamma >= 0 with no upper bound, R7; the yearly caps of SPEC-SELFCAL §6), a damped projected Newton method with the
analytic score and a central finite-difference Hessian; standard errors and the covariance from the inverse observed
information of the free parameters (those not on a bound). The published entry (annex T3.4) rounds eta(L) half up to
whole points in each band and E to three decimals half up, E(-x) = 1 - E(x). Freeze 3's analysis/table_v2_fit.py keeps
v1.1's bound gamma <= 1/2 and is not used here. Standard library only.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal

Q = math.log(10.0) / 400.0
BAND_MIDS = tuple([1450] + [1550 + 100 * k for k in range(13)] + [2850])
KNOTS = (1500, 1700, 1900, 2100, 2300, 2500, 2700)
KAPPA_MIN = 0.05
SEED, DRAWS = 20261009, 2000


def ell(mid: float) -> float:
    return (mid - 2000.0) / 400.0


def names(form: dict) -> tuple[str, ...]:
    slope = ("kappa", "lambda") if form["slope"] == "E" else tuple(f"kappa_{k}" for k in KNOTS)
    return slope + ("eta", "zeta", "alpha", "beta", "gamma", "mu")


def knot_weights(mid: float) -> list[float]:
    """Linear interpolation weights of the seven knots at a band midpoint, constant beyond the end knots."""
    w = [0.0] * len(KNOTS)
    if mid <= KNOTS[0]:
        w[0] = 1.0
    elif mid >= KNOTS[-1]:
        w[-1] = 1.0
    else:
        j = max(i for i, k in enumerate(KNOTS) if k <= mid)
        t = (mid - KNOTS[j]) / (KNOTS[j + 1] - KNOTS[j])
        w[j], w[j + 1] = 1.0 - t, t
    return w


def kappa_at(table: dict, mid: float) -> float:
    p = table["par"]
    if table["form"]["slope"] == "E":
        return p["kappa"] * math.exp(p["lambda"] * ell(mid))
    return sum(wj * p[f"kappa_{k}"] for wj, k in zip(knot_weights(mid), KNOTS))


def eta_at(table: dict, mid: float) -> float:
    return table["par"]["eta"] + table["par"]["zeta"] * ell(mid)


def gamma_at(table: dict, mid: float) -> float:
    return table["par"]["gamma"] * math.exp(table["par"]["mu"] * ell(mid))


def nu0(table: dict, mid: float) -> float:
    return math.exp(table["par"]["alpha"] + table["par"]["beta"] * ell(mid))


def probs(table: dict, x: float, mid: float) -> tuple[float, float, float]:
    """(P_W, P_D, P_L) at White's published gap x (colour not included: eta(L) is added here) and band midpoint."""
    z = kappa_at(table, mid) * Q * (x + eta_at(table, mid))
    nu = nu0(table, mid) * math.exp(-gamma_at(table, mid) * abs(z))
    a = math.exp(z / 2.0)
    b = 1.0 / a
    den = a + b + nu
    return a / den, nu / den, b / den


def expected_effective(table: dict, x: float, mid: float) -> float:
    """The unrounded entry at effective gap x (colour included): the function the published table rounds."""
    z = kappa_at(table, mid) * Q * abs(x)
    nu = nu0(table, mid) * math.exp(-gamma_at(table, mid) * z)
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    e = (a + nu / 2.0) / (a + b + nu)
    return e if x >= 0 else 1.0 - e


def eta_whole(table: dict, mid: int) -> int:
    """eta(L) rounded half up to whole points in the band (annex T3.4)."""
    return int(Decimal(repr(eta_at(table, mid))).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def published(table: dict, x_eff: int, mid: int) -> Decimal:
    """The published entry at effective gap x_eff (colour included, whole points), three decimals half up."""
    e = Decimal(repr(expected_effective(table, abs(x_eff), mid))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return e if x_eff >= 0 else Decimal(1) - e


def slope_at_zero(table: dict, mid: float) -> float:
    """The table's slope at an even gap, kappa(L) q / (2 (2 + nu_0(L))) (annex T3.5)."""
    return kappa_at(table, mid) * Q / (2.0 * (2.0 + nu0(table, mid)))


# ------------------------------------------------------------------ the likelihood
def group(cells: list[tuple]) -> list[tuple[float, list[tuple]]]:
    """Cells (x, mid, s, w) grouped by band midpoint: [(mid, [(x, s, w), ...]), ...] in a fixed order."""
    by: dict[float, list[tuple]] = {}
    for x, mid, s, w in cells:
        by.setdefault(mid, []).append((x, s, w))
    return [(mid, by[mid]) for mid in sorted(by)]


def table_of(form: dict, theta: list[float]) -> dict:
    return {"form": form, "par": dict(zip(names(form), theta))}


def loglik_grad(form: dict, theta: list[float], grouped: list) -> tuple[float, list[float]]:
    """Log-likelihood and its score over the grouped cells."""
    nm = names(form)
    ix = {k: i for i, k in enumerate(nm)}
    tab = table_of(form, theta)
    p = tab["par"]
    g = [0.0] * len(nm)
    ll = 0.0
    exp, log = math.exp, math.log
    for mid, rows in grouped:
        l = ell(mid)
        kl = kappa_at(tab, mid)
        kq = kl * Q
        el = eta_at(tab, mid)
        em = exp(p["mu"] * l)
        gl = p["gamma"] * em
        base = p["alpha"] + p["beta"] * l
        su = suz = sr = sraz = 0.0
        for x, s, w in rows:
            z = kq * (x + el)
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
            r = w * (dr - pd)
            su += u
            suz += u * z
            sr += r
            sraz += r * az
        d_kl = suz / kl                         # d LL / d kappa(L)
        if form["slope"] == "E":
            g[ix["kappa"]] += d_kl * kl / p["kappa"]
            g[ix["lambda"]] += d_kl * kl * l
        else:
            for wj, k in zip(knot_weights(mid), KNOTS):
                if wj:
                    g[ix[f"kappa_{k}"]] += d_kl * wj
        g[ix["eta"]] += kq * su
        g[ix["zeta"]] += kq * su * l
        g[ix["alpha"]] += sr
        g[ix["beta"]] += l * sr
        g[ix["gamma"]] -= em * sraz
        g[ix["mu"]] -= gl * l * sraz
    return ll, g


# ------------------------------------------------------------------ the fit
def _solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-300:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def _hessian(form: dict, theta: list[float], grouped: list, free: list[int]) -> list[list[float]]:
    h = [[0.0] * len(free) for _ in free]
    for a, j in enumerate(free):
        step = 1e-5 * max(1.0, abs(theta[j]))
        up, dn = theta[:], theta[:]
        up[j] += step
        dn[j] -= step
        gu, gd = loglik_grad(form, up, grouped)[1], loglik_grad(form, dn, grouped)[1]
        for b_, k in enumerate(free):
            h[b_][a] = (gu[k] - gd[k]) / (2.0 * step)
    return [[0.5 * (h[i][j] + h[j][i]) for j in range(len(free))] for i in range(len(free))]


def bounds_for(form: dict, caps: dict | None = None) -> dict[str, tuple[float, float]]:
    """Box bounds: kappa >= 0.05 for every slope parameter (form E's lambda free), gamma >= 0, zeta and mu fixed at 0
    outside the form; with caps, each capped parameter within its cap of the previous table's value."""
    out = {}
    for k in names(form):
        lo, hi = -math.inf, math.inf
        if k == "kappa" or k.startswith("kappa_"):
            lo = KAPPA_MIN
        if k == "gamma":
            lo = 0.0
        if (k == "zeta" and not form["colour_by_level"]) or (k == "mu" and not form["tail"]):
            lo = hi = 0.0
        if caps and k in caps and lo < hi:
            c_lo, c_hi = caps[k]
            lo, hi = max(lo, c_lo), min(hi, c_hi)
        out[k] = (lo, hi)
    return out


def fit(form: dict, cells: list[tuple], start: dict[str, float], caps: dict | None = None) -> dict:
    """Maximum likelihood over cells (x, mid, s, w) from start {name: value} (missing names at 0, clipped into the
    bounds); caps {name: (lo, hi)} from SPEC-SELFCAL §6."""
    grouped = group(cells)
    nm = names(form)
    bd = bounds_for(form, caps)
    lo = [bd[k][0] for k in nm]
    hi = [bd[k][1] for k in nm]
    theta = [min(max(start.get(k, 0.0), lo[i]), hi[i]) for i, k in enumerate(nm)]
    ll, g = loglik_grad(form, theta, grouped)

    def free_set(th: list[float], gr: list[float]) -> list[int]:
        out = []
        for j in range(len(nm)):
            if lo[j] == hi[j]:
                continue
            if th[j] <= lo[j] and gr[j] <= 0:
                continue
            if th[j] >= hi[j] and gr[j] >= 0:
                continue
            out.append(j)
        return out

    it = 0
    for it in range(1, 51):
        free = free_set(theta, g)
        if not free:
            break
        h = _hessian(form, theta, grouped, free)
        step_f = _solve([[-h[i][j] for j in range(len(free))] for i in range(len(free))], [g[j] for j in free])
        if step_f is None:
            break
        t = 1.0
        accepted = None
        while t >= 1e-6:
            cand = theta[:]
            for i, j in enumerate(free):
                cand[j] = min(max(theta[j] + t * step_f[i], lo[j]), hi[j])
            ll_c, g_c = loglik_grad(form, cand, grouped)
            if ll_c >= ll - 1e-9:
                accepted = (cand, ll_c, g_c)
                break
            t /= 2.0
        if accepted is None:
            break
        cand, ll_c, g_c = accepted
        moved = max(abs(cand[j] - theta[j]) for j in range(len(nm)))
        theta, ll, g = cand, ll_c, g_c
        if moved < 1e-7:
            break
    free = [j for j in range(len(nm)) if lo[j] < hi[j] and lo[j] < theta[j] < hi[j]]
    h = _hessian(form, theta, grouped, free) if free else []
    cov = None
    if free:
        neg = [[-h[i][j] for j in range(len(free))] for i in range(len(free))]
        cols = [_solve(neg, [1.0 if r == c else 0.0 for r in range(len(free))]) for c in range(len(free))]
        if all(col is not None for col in cols):
            cov = [[cols[c][r] for c in range(len(free))] for r in range(len(free))]
    se = {nm[j]: (math.sqrt(cov[i][i]) if cov and cov[i][i] > 0 else None) for i, j in enumerate(free)}
    on_bound = {nm[j]: ("lower" if theta[j] <= lo[j] else "upper") for j in range(len(nm))
                if lo[j] < hi[j] and (theta[j] <= lo[j] or theta[j] >= hi[j])}
    return {"form": form, "par": dict(zip(nm, theta)), "loglik": ll, "n": int(sum(c[3] for c in cells)),
            "cells": len(cells), "iterations": it, "se": se, "free": [nm[j] for j in free],
            "cov": cov, "on_bound": on_bound, "bounds": {k: list(v) for k, v in bd.items()},
            "max_abs_score": max((abs(g[j]) for j in free), default=0.0)}


def draws(f: dict, n: int = DRAWS, seed: int = SEED) -> list[dict]:
    """n parameter draws from the fit's normal approximation over its free parameters (the others fixed): for the
    intervals of derived quantities (SPEC-SELFCAL §8)."""
    free, cov = f["free"], f["cov"]
    base = dict(f["par"])
    if not free or cov is None:
        return [dict(base) for _ in range(n)]
    k = len(free)
    lch = [[0.0] * k for _ in range(k)]                  # Cholesky factor of the covariance
    for i in range(k):
        for j in range(i + 1):
            s = cov[i][j] - sum(lch[i][m] * lch[j][m] for m in range(j))
            if i == j:
                lch[i][j] = math.sqrt(max(s, 0.0))
            else:
                lch[i][j] = s / lch[j][j] if lch[j][j] > 0 else 0.0
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        e = [rnd.gauss(0.0, 1.0) for _ in range(k)]
        d = dict(base)
        for i, name in enumerate(free):
            d[name] = base[name] + sum(lch[i][m] * e[m] for m in range(i + 1))
        out.append(d)
    return out


def interval(values: list[float]) -> tuple[float, float]:
    v = sorted(values)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]
