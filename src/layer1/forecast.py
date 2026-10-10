"""Layer 1 forecasts for months after a fit (SPEC-L1 §4.5) and warm starts for rolling fits.

A player's state at the last time point is propagated by the dynamics to the
forecast month; a player not in the fit gets the prior of SPEC-L1 §3.4.
Probabilities are computed at the propagated means (plug-in). Standard library only.
"""
from __future__ import annotations

import math

from . import fit, model
from .model import Q


def strength_for(f: fit.Fit, player: int, tc: int, month: int, prior_of) -> float:
    i = f.index.get(player)
    if i is None:
        return prior_of(player, month).mean + f.mu[tc]
    s = fit.state_at(f, i, month)
    return s[0] + f.mu[tc] + s[1 + tc]


def probabilities(f: fit.Fit, game: fit.Game, prior_of) -> tuple[float, float, float]:
    """(P_W, P_D, P_L) for White in a game after the fit."""
    sw = strength_for(f, game.white, game.tc, game.month, prior_of)
    sb = strength_for(f, game.black, game.tc, game.month, prior_of)
    z = Q * (sw - sb + f.eta[game.tc])
    nu0 = math.exp(f.alpha[game.tc] + f.beta[game.tc] * model.ell_of(game.level_mid))
    return model.probs(z, nu0, f.gamma[game.tc])


def log_loss(f: fit.Fit, games: list[fit.Game], prior_of) -> tuple[float, int]:
    """Mean three-outcome log-loss (nats a game) and the number of games."""
    total = 0.0
    for g in games:
        pw, pd, pl = probabilities(f, g, prior_of)
        total -= math.log(pw if g.score == 1.0 else pd if g.score == 0.5 else pl)
    return (total / len(games) if games else float("nan")), len(games)


def warm_start(new: fit.Fit, old: fit.Fit) -> int:
    """Start a fit from an earlier one: each state present in both takes the earlier mode; drift and μ carry over.
    Returns the number of players started warm."""
    new.A, new.B = list(old.A), list(old.B)
    n = 0
    for i, p in enumerate(new.players):
        j = old.index.get(p)
        if j is None:
            continue
        n += 1
        X = new.x[i]
        for k, m in enumerate(new.months[i]):
            s = fit.state_at(old, j, m)
            X[4 * k:4 * k + 4] = s
    return n
