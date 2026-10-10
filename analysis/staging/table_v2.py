"""Rung 2, version 2: the expected-score table with a slope that depends on the level (SPEC-TABLE-FIT v1.1 §2).

White's view, with q = ln 10/400, L the midpoint of the 100-point level band and l = (L - 2000)/400:
  kappa(L) = kappa exp(lambda l),  z = kappa(L) q (gap + eta),
  nu = exp(alpha + beta l - gamma(L) |z|),  gamma(L) = gamma exp(mu l)  (mu = 0 without the draw tail),
  P_W : P_D : P_L = e^{z/2} : nu : e^{-z/2}.
`par` is (kappa, lambda, eta, alpha, beta, gamma, mu); with lambda = mu = 0 it is v1.0's model (src/layer2/table.py).
Three forms, as in src/layer2/table.py: `probs` and `expected_white` evaluate the model (fractional eta, unrounded);
`published` is the published table's entry (eta rounded to a whole number and added to the gap, E to three decimals
half up, E(-x) = 1 - E(x)); `slope_at_zero` and `ratio_812` give R32's slope ratio (D-0011, reading 7).
Staged under analysis/staging/ until Freeze 3 (D-0011, reading 1); library code, not a script. Standard library only.
"""
from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

import layer0

Q = math.log(10.0) / 400.0
BAND_MIDS = tuple([1450] + [1550 + 100 * k for k in range(13)] + [2850])     # the fifteen bands of annex T3.4
NAMES = ("kappa", "lambda", "eta", "alpha", "beta", "gamma", "mu")


def band_mid(level: int) -> int:
    """Midpoint of the 100-point level band (annex T3.4): 1450 below 1500, 2850 from 2800."""
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


def ell(mid: float) -> float:
    return (mid - 2000.0) / 400.0


def kappa_at(par: tuple, mid: float) -> float:
    return par[0] * math.exp(par[1] * ell(mid))


def gamma_at(par: tuple, mid: float) -> float:
    return par[5] * math.exp(par[6] * ell(mid))


def probs(par: tuple, gap_white: float, mid: float) -> tuple[float, float, float]:
    """(P_W, P_D, P_L) at White's published gap (without colour; eta is added here) and level band midpoint."""
    kappa, lam, eta, alpha, beta, gamma, mu = par
    l = ell(mid)
    z = kappa * math.exp(lam * l) * Q * (gap_white + eta)
    nu = math.exp(alpha + beta * l - gamma * math.exp(mu * l) * abs(z))
    a = math.exp(z / 2.0)
    b = 1.0 / a
    den = a + b + nu
    return a / den, nu / den, b / den


def expected_white(par: tuple, gap_white: float, mid: float) -> float:
    pw, pd, _pl = probs(par, gap_white, mid)
    return pw + pd / 2.0


def eta_whole(eta: float) -> int:
    """eta rounded half up to a whole number of points (annex T3.4)."""
    return int(Decimal(repr(eta)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def expected_effective(x: float, mid: float, par: tuple) -> float:
    """The unrounded entry at effective gap x (colour included): the function the published table rounds."""
    kappa, lam, _eta, alpha, beta, gamma, mu = par
    l = ell(mid)
    z = kappa * math.exp(lam * l) * Q * abs(x)
    nu = math.exp(alpha + beta * l - gamma * math.exp(mu * l) * z)
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    e = (a + nu / 2.0) / (a + b + nu)
    return e if x >= 0 else 1.0 - e


def published(x: int, mid: int, par: tuple) -> Decimal:
    """The published entry at effective gap x (colour included, eta whole), three decimals half up; E(-x) = 1 - E(x)."""
    e = Decimal(repr(expected_effective(abs(x), mid, par))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return e if x >= 0 else Decimal(1) - e


def slope_at_zero(par: tuple, mid: float) -> float:
    """The table's slope at an even gap, kappa(L) q / (2 (2 + nu_0(L))) (annex T3.5); the draw tail enters through |z|
    only, so it does not change the slope at zero."""
    nu0 = math.exp(par[3] + par[4] * ell(mid))
    return kappa_at(par, mid) * Q / (2.0 * (2.0 + nu0))


@lru_cache(maxsize=1)
def slope_812() -> float:
    """Table 8.1.2's slope near zero: the least-squares slope of its H entries over D = 0 to 100 [V 1], as the v1.0
    calculations define it (analysis/OUTPUT_v1_0.md, section 13.4)."""
    ds = list(range(0, 101))
    hs = [float(layer0.expected_score(d)) for d in ds]
    md, mh = sum(ds) / len(ds), sum(hs) / len(hs)
    return sum((d - md) * (h - mh) for d, h in zip(ds, hs)) / sum((d - md) ** 2 for d in ds)


def ratio_812(par: tuple, mid: float) -> float:
    """R32's ratio m(L) = E'_8.1.2(0) / E'_v2(0), unrounded."""
    return slope_812() / slope_at_zero(par, mid)


def ratio_printed(par: tuple, mid: float) -> Decimal:
    """m(L) as printed with the table, two decimals half up; the printed value is normative (D-0011, reading 7)."""
    return Decimal(repr(ratio_812(par, mid))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def needs_scaling(par: tuple) -> bool:
    """R32: no scaling when every band's printed ratio lies within 0.9-1.1."""
    return any(not (Decimal("0.9") <= ratio_printed(par, m) <= Decimal("1.1")) for m in BAND_MIDS)


def load(text: str, chapter: str) -> dict:
    """One time control of a v2 parameter file (the format analysis/staging/e11_table_by_level_report.py --yaml
    writes): the printed parameters, R32's printed ratios by band midpoint and whether K is scaled, the fit window
    and the status line."""
    status = re.search(r"^status: (.+)$", text, re.M).group(1).strip()
    block = re.search(rf"^{chapter}:\n((?:  .*\n?)+)", text, re.M)
    if not block:
        raise ValueError(f"no parameters for {chapter}")
    b = block.group(1)
    par = tuple(float(re.search(rf"^  {k}: {{value: (-?[\d.]+)", b, re.M).group(1)) for k in NAMES)
    scale = {int(k): Decimal(v) for k, v in re.findall(r"(\d{4}): ([\d.]+)", re.search(r"^  k_scale: \{(.*)\}$", b, re.M).group(1))}
    w = re.search(r'fit_window: \{from: "([\d-]+)", to: "([\d-]+)"\}', b)
    return {"par": par, "k_scale": scale, "k_scale_applies": re.search(r"^  k_scale_applies: (\w+)$", b, re.M).group(1) == "true",
            "draw_tail": re.search(r"^  draw_tail: (\w+)$", b, re.M).group(1) == "true", "status": status,
            "window": f"{w.group(1)} to {w.group(2)}"}
