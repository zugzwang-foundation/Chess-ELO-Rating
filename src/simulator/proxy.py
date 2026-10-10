"""Layer 1 in the simulator: a forward filter with Layer 1's ingredients (docs/specs/SPEC-SIM_v1_0.md §5).

Per player a Gaussian estimate (mean, variance) in latent units. Each month: the mean moves by the pool's mean
drift (Layer 1's age profile times τ̄ for players under 25; no personal factor, which no model can know) and the
variance grows by SPEC-L1's profile;
then the month's games update it by one Newton step of the D1 likelihood with the opponents' estimates held,
using the game information of layer1.model.game_terms, and the level is fixed by the anchor panel's zero drift
(annex T2.4). A new player starts from the entrants' mean for the age, a player rated at the start from the
published rating (SPEC-L1 §3.4). Standard library only.
"""
from __future__ import annotations

import math

from layer1 import model

from . import config as C
from .pool import age_band, to_lat

S0, S_LIST = 250.0, 120.0
ENTRANT_GROUP_MAX = (9, 14, 19, 29, 49, 200)


def mu0(age: int) -> float:
    """The prior mean of a new player: the entrants' median first rating for the age [E1], in latent units."""
    for g, hi in enumerate(ENTRANT_GROUP_MAX):
        if age <= hi:
            return to_lat(C.ENTRANT_MEDIAN[g])
    return to_lat(C.ENTRANT_MEDIAN[-1])


class Proxy:
    def __init__(self, noise_scale: float, junior_factor: float = 1.0):
        self.noise = noise_scale
        self.jf = junior_factor               # the pool's mean junior drift factor τ̄, which a fitted Layer 1 estimates
        self.m: list[float | None] = []
        self.v: list[float] = []
        self.v_prior: list[float] = []         # the variance at the list date, before the month's games (R4L)
        self.grad: dict[int, float] = {}
        self.info: dict[int, float] = {}

    def grow(self, n: int) -> None:
        while len(self.m) < n:
            self.m.append(None)
            self.v.append(S0 * S0)
            self.v_prior.append(S0 * S0)

    def start_rated(self, i: int, rating: int) -> None:
        self.m[i] = 2000.0 + C.KAPPA0 * (rating - 2000.0)
        self.v[i] = self.v_prior[i] = S_LIST * S_LIST

    def ensure(self, i: int, age: int) -> None:
        if self.m[i] is None:
            self.m[i] = mu0(age)
            self.v[i] = self.v_prior[i] = S0 * S0

    def predict(self, alive: list[bool], ages: list[int]) -> None:
        cap = S0 * S0
        for i, mi in enumerate(self.m):
            if mi is None or not alive[i]:
                continue
            b = age_band(ages[i])
            mu = C.DRIFT_A[b] + C.DRIFT_B[b] * (mi - 2000.0) / 400.0
            self.m[i] = mi + (mu * self.jf if b < 4 else mu if b > 4 else 0.0)
            s = self.noise * C.PROFILE[b]
            self.v[i] = min(self.v[i] + s * s, cap)
            self.v_prior[i] = self.v[i]

    def game(self, w: int, b: int, s2: int) -> None:
        mw, mb = self.m[w], self.m[b]
        z = C.Q * (mw - mb + C.ETA_L)
        level = 2000.0 + ((mw + mb) / 2.0 - 2000.0) / C.KAPPA0
        mid = 1450.0 if level < 1500 else 2850.0 if level >= 2800 else 1500.0 + 100.0 * ((level - 1500.0) // 100.0) + 50.0
        nu0 = math.exp(C.ALPHA + C.BETA * (mid - 2000.0) / 400.0)
        _lp, u, inf = model.game_terms(z, nu0, C.GAMMA, s2 / 2.0)
        g, h = C.Q * u, C.Q * C.Q * inf
        self.grad[w] = self.grad.get(w, 0.0) + g
        self.grad[b] = self.grad.get(b, 0.0) - g
        self.info[w] = self.info.get(w, 0.0) + h
        self.info[b] = self.info.get(b, 0.0) + h

    def update(self, panel: list[int] | None = None) -> float:
        """The month's Newton step; then the level is fixed as annex T2.4 defines it: the anchor panel's mean latent
        strength does not drift (ages 25-45 have zero drift), so the common shift the step gave the panel is removed
        from every estimate. Returns that shift."""
        mem = [i for i in (panel or []) if self.m[i] is not None]
        before = sum(self.m[i] for i in mem) / len(mem) if mem else 0.0
        for i in sorted(self.info):
            prec = 1.0 / self.v[i] + self.info[i]
            self.m[i] += self.grad[i] / prec
            self.v[i] = 1.0 / prec
        self.grad.clear()
        self.info.clear()
        if not mem:
            return 0.0
        shift = sum(self.m[i] for i in mem) / len(mem) - before
        for i, mi in enumerate(self.m):
            if mi is not None:
                self.m[i] = mi - shift
        return shift
