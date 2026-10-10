"""Layer 1, the maximum a posteriori fit (SPEC-L1 §3–§4; annex T2.2–T2.4).

Every player has states at the months in which they have games: (θ, δ_standard,
δ_rapid, δ_blitz). The fit sweeps over players in ascending FIDE ID and takes one
Newton step on each player's whole trajectory with the opponents held fixed; the
system is solved exactly (`layer1.solver`). The drift parameters are refitted every
fifth sweep; the outcome parameters are the published table's in latent units and stay
fixed (SPEC-L1 §3.2); the anchor constraint is imposed exactly at the end.
Deterministic: no step is random. Standard library only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

from . import model, solver
from .model import ANCHOR_BAND, Q

CUTOFF = date(2026, 9, 30)


def month_index(y: int, m: int) -> int:
    return y * 12 + (m - 1)


def month_label(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


@dataclass(frozen=True)
class Game:
    """One game. month is the month index of the game's date; tc 0 standard, 1 rapid, 2 blitz;
    score is White's (1, 0.5, 0); level_mid the midpoint of the level band (SPEC-L1 §3.2)."""
    day: date
    month: int
    tc: int
    white: int
    black: int
    score: float
    level_mid: int
    tour: str = ""
    white_rated: bool = True
    black_rated: bool = True
    white_r: int | None = None        # published ratings and K on the list in force (SPEC-L0 R-11a), for Layer 0
    black_r: int | None = None
    white_k: int | None = None
    black_k: int | None = None
    list_month: str = ""


@dataclass
class Hyper:
    """SPEC-L1 §3.7 (PROVISIONAL)."""
    c_theta: float = 1.0
    sigma_profile: tuple = (25.0, 25.0, 20.0, 14.0, 12.0, 15.0, 15.0)
    rho: float = 0.97
    omega: float = 8.0
    s0: float = 250.0
    s_list: float = 120.0
    max_sweeps: int = 80
    tol: float = 0.1
    refit_every: int = 5
    max_drift_rounds: int = 6
    drift_tol: float = 0.05
    ridge_a: float = 10.0          # prior SD of A_a, points a month (weak)
    ridge_b: float = 2.0           # prior SD of B_a, points a month per 400 points

    def sigma2(self, band: int) -> float:
        return (self.c_theta * self.sigma_profile[band]) ** 2

    def delta_stationary_var(self) -> float:
        return self.omega ** 2 / (1.0 - self.rho ** 2)

    def delta_innov_var(self, dt: int) -> float:
        return self.omega ** 2 * (1.0 - self.rho ** (2 * dt)) / (1.0 - self.rho ** 2)


@dataclass
class Prior:
    """Prior of a player's first θ (SPEC-L1 §3.4): mean and variance on the latent scale."""
    mean: float
    var: float


@dataclass
class Fit:
    players: list[int]
    months: list[list[int]]
    x: list[list[float]]
    cov_last: list[list[float]]
    prior: list[Prior]
    bands: list[list[int]]
    eta: list[float]
    alpha: list[float]
    beta: list[float]
    gamma: list[float]
    mu: list[float]
    A: list[float]
    B: list[float]
    hyper: Hyper
    sweeps: int = 0
    max_move: float = 0.0
    log_post: float = 0.0
    games_used: int = 0
    shifts: list[float] = field(default_factory=list)
    drift_rounds: int = 0
    index: dict = field(default_factory=dict)
    birth: dict = field(default_factory=dict)
    glist: list = field(default_factory=list)


# --------------------------------------------------------------------------------------------- building
def check_cutoff(games: list[Game], cutoff: date = CUTOFF) -> None:
    """ELO-4 data cutoff (SPEC-L1 §2.4): refuse any game dated after it."""
    late = [g for g in games if g.day > cutoff]
    if late:
        raise ValueError(f"{len(late)} game(s) dated after the data cutoff {cutoff.isoformat()}; the first is {late[0].day}")


def build(games: list[Game], birth: dict[int, int | None], prior_of, hyper: Hyper,
          outcome: dict | None = None) -> Fit:
    """Index players and games. prior_of(player, first_month) -> Prior; birth: FIDE ID -> year of birth."""
    check_cutoff(games)
    pl = sorted({g.white for g in games} | {g.black for g in games})
    index = {p: i for i, p in enumerate(pl)}
    months: list[set] = [set() for _ in pl]
    for g in games:
        months[index[g.white]].add(g.month)
        months[index[g.black]].add(g.month)
    mlist = [sorted(m) for m in months]
    kpos = [{m: k for k, m in enumerate(ms)} for ms in mlist]
    glist: list[list[tuple]] = [[] for _ in pl]
    for g in games:
        w, b = index[g.white], index[g.black]
        ell = model.ell_of(g.level_mid)
        kw, kb = kpos[w][g.month], kpos[b][g.month]
        glist[w].append((kw, g.tc, b, kb, 1.0, g.score, ell))
        glist[b].append((kb, g.tc, w, kw, -1.0, g.score, ell))
    bands = []
    for i, p in enumerate(pl):
        by = birth.get(p)
        bands.append([model.age_band((m // 12) - by if by else None) for m in mlist[i]])
    priors = [prior_of(p, mlist[i][0]) for i, p in enumerate(pl)]
    x = []
    for i in range(len(pl)):
        th = priors[i].mean
        x.append([v for _ in mlist[i] for v in (th, 0.0, 0.0, 0.0)])
    oc = outcome or {}
    return Fit(players=pl, months=mlist, x=x, cov_last=[[] for _ in pl], prior=priors, bands=bands,
               eta=list(oc.get("eta", (30.0, 30.0, 25.0))), alpha=list(oc.get("alpha", (0.0, -0.3, -0.8))),
               beta=list(oc.get("beta", (0.5, 0.5, 0.45))), gamma=list(oc.get("gamma", (0.3, 0.2, 0.3))),
               mu=[0.0, 0.0, 0.0], A=[0.0] * 7, B=[0.0] * 7, hyper=hyper, games_used=len(games),
               index=index, birth=dict(birth), glist=glist)


# --------------------------------------------------------------------------------------------- one player
def _assemble(f: Fit, i: int, X: list[float], drop_tc: tuple = (), with_games: bool = True):
    """Negative log posterior F, gradient and Hessian blocks of player i at states X."""
    hp = f.hyper
    ms, bands = f.months[i], f.bands[i]
    T = len(ms)
    D = [[0.0] * 16 for _ in range(T)]
    G = [[0.0] * 4 for _ in range(T)]
    U = [[0.0] * 4 for _ in range(T - 1)]
    pr = f.prior[i]
    r = X[0] - pr.mean
    F = 0.5 * r * r / pr.var
    G[0][0] += r / pr.var
    D[0][0] += 1.0 / pr.var
    vd = hp.delta_stationary_var()
    for c in (1, 2, 3):
        d = X[c]
        F += 0.5 * d * d / vd
        G[0][c] += d / vd
        D[0][5 * c] += 1.0 / vd
    for k in range(T - 1):
        dt = ms[k + 1] - ms[k]
        a = bands[k]
        cth = 1.0 + dt * f.B[a] / 400.0
        m0 = dt * (f.A[a] - 5.0 * f.B[a])
        V = dt * hp.sigma2(a)
        b4, n4 = 4 * k, 4 * (k + 1)
        r = X[n4] - cth * X[b4] - m0
        F += 0.5 * r * r / V
        G[k + 1][0] += r / V
        G[k][0] -= cth * r / V
        D[k + 1][0] += 1.0 / V
        D[k][0] += cth * cth / V
        U[k][0] = -cth / V
        rd = hp.rho ** dt
        W = hp.delta_innov_var(dt)
        for c in (1, 2, 3):
            r = X[n4 + c] - rd * X[b4 + c]
            F += 0.5 * r * r / W
            G[k + 1][c] += r / W
            G[k][c] -= rd * r / W
            D[k + 1][5 * c] += 1.0 / W
            D[k][5 * c] += rd * rd / W
            U[k][c] = -rd / W
    if with_games:
        xs, mu, eta, alpha, beta, gamma = f.x, f.mu, f.eta, f.alpha, f.beta, f.gamma
        qq = Q * Q
        for k, tc, j, jk, sign, s_w, ell in f.glist[i]:
            if tc in drop_tc:
                continue
            c = 1 + tc
            own = X[4 * k] + X[4 * k + c]
            Xj = xs[j]
            opp = Xj[4 * jk] + Xj[4 * jk + c]
            xw = (own - opp) if sign > 0 else (opp - own)
            z = Q * (xw + eta[tc])
            nu0 = math.exp(alpha[tc] + beta[tc] * ell)
            lp, u, info = model.game_terms(z, nu0, gamma[tc], s_w)
            F -= lp
            gq = -sign * Q * u
            Gk = G[k]
            Gk[0] += gq
            Gk[c] += gq
            h = qq * info
            Dk = D[k]
            Dk[0] += h
            Dk[c] += h
            Dk[4 * c] += h
            Dk[5 * c] += h
    return F, G, D, U


def _value(f: Fit, i: int, X: list[float]) -> float:
    return _assemble(f, i, X)[0]


def _step(f: Fit, i: int) -> float:
    """One Newton step on player i; returns the largest move of any strength."""
    X = f.x[i]
    F0, G, D, U = _assemble(f, i, X)
    y, _ = solver.solve(D, U, G)
    T = len(X) // 4
    t = 1.0
    for _ in range(6):
        Xn = [X[4 * k + c] - t * y[k][c] for k in range(T) for c in range(4)]
        if _value(f, i, Xn) <= F0 + 1e-9:
            mv = max(max(abs(t * y[k][0] + t * y[k][c]) for c in (1, 2, 3)) for k in range(T))
            f.x[i] = Xn
            return mv
        t *= 0.5
    return 0.0


# --------------------------------------------------------------------------------------------- states in time
def state_at(f: Fit, i: int, month: int) -> list[float]:
    """Modal (θ, δ_s, δ_r, δ_b) of player i at a month (SPEC-L1 §4.5): propagated beyond the last time point,
    the first state before the first (offsets decayed), linear between time points."""
    ms, X, hp = f.months[i], f.x[i], f.hyper
    T = len(ms)
    if month >= ms[-1]:
        dt = month - ms[-1]
        a = f.bands[i][-1]
        th = (1.0 + dt * f.B[a] / 400.0) * X[4 * (T - 1)] + dt * (f.A[a] - 5.0 * f.B[a])
        rd = hp.rho ** dt
        return [th, rd * X[4 * (T - 1) + 1], rd * X[4 * (T - 1) + 2], rd * X[4 * (T - 1) + 3]]
    if month <= ms[0]:
        rd = hp.rho ** (ms[0] - month)
        return [X[0], rd * X[1], rd * X[2], rd * X[3]]
    lo = max(k for k in range(T) if ms[k] <= month)
    w = (month - ms[lo]) / (ms[lo + 1] - ms[lo])
    return [(1 - w) * X[4 * lo + c] + w * X[4 * (lo + 1) + c] for c in range(4)]


def strength(f: Fit, i: int, tc: int, month: int) -> float:
    s = state_at(f, i, month)
    return s[0] + f.mu[tc] + s[1 + tc]


def covariance_at(f: Fit, i: int, month: int, cov_last: list[float] | None = None) -> list[float]:
    """Laplace covariance of the 4-state at a month at or after the last time point (SPEC-L1 §4.3)."""
    ms, hp = f.months[i], f.hyper
    C = cov_last if cov_last is not None else f.cov_last[i]
    dt = max(0, month - ms[-1])
    if dt == 0:
        return list(C)
    a = f.bands[i][-1]
    av = [1.0 + dt * f.B[a] / 400.0] + [hp.rho ** dt] * 3
    out = [av[r] * C[4 * r + c] * av[c] for r in range(4) for c in range(4)]
    out[0] += dt * hp.sigma2(a)
    w = hp.delta_innov_var(dt)
    for c in (1, 2, 3):
        out[5 * c] += w
    return out


def sigma_tc(cov: list[float], tc: int) -> float:
    c = 1 + tc
    return math.sqrt(max(cov[0] + cov[5 * c] + 2.0 * cov[c], 0.0))


# --------------------------------------------------------------------------------------------- global steps
def global_shift_step(f: Fit) -> float:
    """One exact Newton step along "add c to every θ" (SPEC-L1 §4.2). The likelihood is invariant along this
    direction, so only the priors and the level-dependent drift move it; the step lowers the posterior."""
    hp = f.hyper
    g = h = 0.0
    for i, ms in enumerate(f.months):
        X, pr = f.x[i], f.prior[i]
        g += (X[0] - pr.mean) / pr.var
        h += 1.0 / pr.var
        for k in range(len(ms) - 1):
            dt = ms[k + 1] - ms[k]
            a = f.bands[i][k]
            if f.B[a] == 0.0:
                continue
            cth = 1.0 + dt * f.B[a] / 400.0
            V = dt * hp.sigma2(a)
            r = X[4 * (k + 1)] - cth * X[4 * k] - dt * (f.A[a] - 5.0 * f.B[a])
            g += r / V * (1.0 - cth)
            h += (1.0 - cth) ** 2 / V
    c = -g / h if h > 0 else 0.0
    if c:
        for X in f.x:
            for k in range(0, len(X), 4):
                X[k] += c
    return c


def impose_anchor(f: Fit, panels: dict[int, list[tuple[int, float]]], t_ref: int, move_priors: bool = False) -> float:
    """SPEC-L1 §3.5: panel mean ŝ at t_ref = panel's published mean. panels[tc] = [(player index, published rating)].
    Standard shifts every θ (and, at the end of a fit, every prior mean, so that the posterior is unchanged up to the
    level-dependent drift); rapid and blitz set μ_tc. Returns the standard shift."""
    shift = 0.0
    std = panels.get(0, [])
    if std:
        cur = sum(sum(state_at(f, i, t_ref)[:2]) for i, _ in std) / len(std)
        shift = sum(r for _, r in std) / len(std) - cur
        if shift:
            for X in f.x:
                for k in range(0, len(X), 4):
                    X[k] += shift
            if move_priors:
                for pr in f.prior:
                    pr.mean += shift
    for tc in (1, 2):
        pan = panels.get(tc, [])
        if pan:
            cur = sum(state_at(f, i, t_ref)[0] + state_at(f, i, t_ref)[1 + tc] for i, _ in pan) / len(pan)
            f.mu[tc] = sum(r for _, r in pan) / len(pan) - cur
    return shift


def refit_drift(f: Fit, min_transitions: int = 50) -> float:
    """Weighted least squares of the modal θ increments on [1, (θ − 2000)/400] by age band, with weak ridge priors
    on A_a and B_a (SPEC-L1 §4.2); ages 25–45 stay at zero (T2.4). Returns the largest change of A or B."""
    hp = f.hyper
    acc = [[0.0] * 6 for _ in range(7)]     # sw, swx, swxx, swy, swxy, n
    for i, ms in enumerate(f.months):
        X = f.x[i]
        for k in range(len(ms) - 1):
            a = f.bands[i][k]
            if a == ANCHOR_BAND:
                continue
            dt = ms[k + 1] - ms[k]
            w = dt / hp.sigma2(a)
            xv = (X[4 * k] - 2000.0) / 400.0
            yv = (X[4 * (k + 1)] - X[4 * k]) / dt
            s = acc[a]
            s[0] += w
            s[1] += w * xv
            s[2] += w * xv * xv
            s[3] += w * yv
            s[4] += w * xv * yv
            s[5] += 1
    change = 0.0
    for a in range(7):
        if a == ANCHOR_BAND:
            continue
        sw, swx, swxx, swy, swxy, n = acc[a]
        if n < min_transitions:
            continue
        sw += 1.0 / hp.ridge_a ** 2
        swxx += 1.0 / hp.ridge_b ** 2
        det = sw * swxx - swx * swx
        A = (swxx * swy - swx * swxy) / det
        B = (sw * swxy - swx * swy) / det
        change = max(change, abs(A - f.A[a]), abs(B - f.B[a]))
        f.A[a], f.B[a] = A, B
    return change


def finalise(f: Fit) -> None:
    """Laplace covariance of every player's last state at the mode, and the log posterior."""
    total = 0.0
    for i in range(len(f.players)):
        F, G, D, U = _assemble(f, i, f.x[i])
        _, last = solver.solve(D, U, G)
        f.cov_last[i] = last
        total -= F
    f.log_post = total


def smoothed_covariances(f: Fit, i: int) -> list[list[float]]:
    """Laplace covariance of every state of player i at the mode (SPEC-L1 §4.3, §5.3)."""
    F, G, D, U = _assemble(f, i, f.x[i])
    return solver.marginal_covariances(D, U)


def last_cov_variant(f: Fit, i: int, drop_tc: tuple = (), with_games: bool = True) -> list[float]:
    """The last state's covariance with some game terms removed, at the same mode (SPEC-L1 §4.4)."""
    F, G, D, U = _assemble(f, i, f.x[i], drop_tc=drop_tc, with_games=with_games)
    return solver.solve(D, U, G)[1]


def run(f: Fit, panels: dict[int, list[tuple[int, float]]], t_ref: int, refit: bool = True, log=None) -> Fit:
    """Sweeps to convergence (SPEC-L1 §4.2): the drift is refitted every refit_every sweeps until it changes by less
    than drift_tol (at most max_drift_rounds times), then the sweeps run until no strength moves by more than tol;
    the anchor is imposed exactly at the end (§3.5)."""
    hp = f.hyper
    rounds, drift_done = 0, not refit
    for sweep in range(1, hp.max_sweeps + 1):
        mv = 0.0
        for i in range(len(f.players)):
            mv = max(mv, _step(f, i))
        gs = global_shift_step(f)
        mv = max(mv, abs(gs))
        refitted = False
        if not drift_done and sweep % hp.refit_every == 0:
            change = refit_drift(f)
            rounds += 1
            drift_done = change < hp.drift_tol or rounds >= hp.max_drift_rounds
            refitted = True
        f.sweeps, f.max_move = sweep, mv
        f.drift_rounds = rounds
        if log:
            log(f"sweep {sweep}: max move {mv:.3f}, global step {gs:+.3f}")
        if mv < hp.tol and not refitted and drift_done:
            break
    f.shifts.append(impose_anchor(f, panels, t_ref, move_priors=True))
    finalise(f)
    return f
