"""A synthetic pool drawn from the Layer 1 model (SPEC-L1 §7, A1-4 to A1-6): known strengths, three time controls."""
from __future__ import annotations

import math
import random
from datetime import date

from layer1 import fit, model

ETA, ALPHA, BETA, GAMMA = (40.0, 35.0, 25.0), (0.3, 0.0, -0.8), (0.5, 0.5, 0.45), (0.3, 0.2, 0.3)
OUTCOME = {"eta": ETA, "alpha": ALPHA, "beta": BETA, "gamma": GAMMA}


def pool(n: int = 300, months: int = 24, games_per_month: int = 250, seed: int = 7):
    rnd = random.Random(seed)
    true, birth = {}, {}
    for p in range(1, n + 1):
        pid = 100000 + p
        th = rnd.gauss(1800, 300)
        dl = [0.0, rnd.gauss(0, 30), rnd.gauss(0, 30)]
        by = rnd.choice([1980, 1990, 2000, 2010])
        birth[pid] = by
        traj = []
        for m in range(months):
            th += rnd.gauss(0, 12) + (5.0 if (2023 + m // 12) - by < 16 else 0.0)
            dl = [0.0] + [0.97 * d + rnd.gauss(0, 8) for d in dl[1:]]
            traj.append((th, dl[:]))
        true[pid] = traj
    ids = sorted(true)
    games = []
    for m in range(months):
        for _ in range(games_per_month):
            w, b = rnd.sample(ids, 2)
            tc = rnd.choice([0, 0, 1, 2])
            sw = true[w][m][0] + true[w][m][1][tc]
            sb = true[b][m][0] + true[b][m][1][tc]
            lvl = model.band_mid(int((sw + sb) / 2))
            z = model.Q * (sw - sb + ETA[tc])
            pw, pd, _ = model.probs(z, math.exp(ALPHA[tc] + BETA[tc] * model.ell_of(lvl)), GAMMA[tc])
            u = rnd.random()
            s = 1.0 if u < pw else 0.5 if u < pw + pd else 0.0
            y, mo = 2023 + m // 12, m % 12 + 1
            games.append(fit.Game(date(y, mo, 15), fit.month_index(y, mo), tc, w, b, s, lvl, f"t{m}-{tc}"))
    rnd2 = random.Random(3)
    init = {p: true[p][0][0] + rnd2.gauss(0, 100) for p in true}
    return games, true, birth, init


def fitted(n: int = 300, months: int = 24, games_per_month: int = 250, seed: int = 7):
    games, true, birth, init = pool(n, months, games_per_month, seed)
    hp = fit.Hyper(max_sweeps=120)
    f = fit.build(games, birth, lambda p, m: fit.Prior(init[p], 120.0 ** 2), hp, outcome=OUTCOME)
    t_ref = fit.month_index(2024, 1)
    panel = [(f.index[p], true[p][12][0]) for p in sorted(true) if 25 <= 2024 - birth[p] <= 45]
    fit.run(f, {0: panel}, t_ref)
    return f, true, birth, panel, t_ref
