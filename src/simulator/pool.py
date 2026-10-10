"""The simulated players and their true strengths (docs/specs/SPEC-SIM_v1_0.md §3.1–§3.3). Standard library only."""
from __future__ import annotations

import math
import random

from . import config as C


def age_band(age: int) -> int:
    """SPEC-L1 §3.3's bands: under 12, 12-15, 16-19, 20-24, 25-45, 46-60, over 60."""
    if age < 12:
        return 0
    if age <= 15:
        return 1
    if age <= 19:
        return 2
    if age <= 24:
        return 3
    if age <= 45:
        return 4
    if age <= 60:
        return 5
    return 6


def to_pub(theta: float) -> float:
    """θᴾ = 2000 + (θ − 2000)/κ₀ (SPEC-SIM §2)."""
    return 2000.0 + (theta - 2000.0) / C.KAPPA0


def to_lat(theta_p: float) -> float:
    return 2000.0 + C.KAPPA0 * (theta_p - 2000.0)


def poisson(rnd: random.Random, lam: float) -> int:
    """Knuth's method; λ is small (events a month)."""
    if lam <= 0.0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= limit:
            return k
        k += 1


class Pool:
    def __init__(self, cfg: C.Config, rnd: random.Random):
        self.cfg, self.rnd = cfg, rnd
        self.theta: list[float] = []
        self.birth: list[int] = []
        self.fed: list[int] = []
        self.rate: list[float] = []          # games a year
        self.talent: list[float] = []        # the personal junior drift factor τ
        self.alive: list[bool] = []
        self.first_month: list[int] = []
        self.last_game: list[int] = []
        self.career: list[int] = []          # games played, rated or not
        self.agent: list[str] = []           # "" for ordinary players
        fed_total = sum(C.FED_SIZES)
        self.fed_cum = []
        acc = 0.0
        for s in C.FED_SIZES:
            acc += s / fed_total
            self.fed_cum.append(acc)
        sd = cfg.junior_factor_cv * cfg.junior_factor_mean
        self.tal_shape = (cfg.junior_factor_mean / sd) ** 2 if sd > 0 else 0.0
        self.tal_scale = sd * sd / cfg.junior_factor_mean if sd > 0 else 0.0

    @property
    def n(self) -> int:
        return len(self.theta)

    def year(self, month: int) -> int:
        return self.cfg.start_year + month // 12

    def age(self, i: int, month: int) -> int:
        return self.year(month) - self.birth[i]

    def theta_p(self, i: int) -> float:
        return to_pub(self.theta[i])

    def draw_fed(self) -> int:
        u = self.rnd.random()
        for f, c in enumerate(self.fed_cum):
            if u <= c:
                return f
        return len(self.fed_cum) - 1

    def draw_rate(self, theta_p: float) -> float:
        med = self.cfg.activity_median_1800 * math.exp(self.cfg.activity_slope * (theta_p - 1800.0))
        g = med * math.exp(self.rnd.gauss(0.0, self.cfg.activity_sd_log))
        return min(120.0, max(4.0, g))

    def draw_talent(self) -> float:
        if self.tal_shape <= 0:
            return self.cfg.junior_factor_mean
        return self.rnd.gammavariate(self.tal_shape, self.tal_scale)

    def add(self, theta_p: float, age: int, fed: int, month: int) -> int:
        i = self.n
        self.theta.append(to_lat(theta_p))
        self.birth.append(self.year(month) - age)
        self.fed.append(fed)
        self.rate.append(self.draw_rate(theta_p))
        self.talent.append(self.draw_talent())
        self.alive.append(True)
        self.first_month.append(month)
        self.last_game.append(-999)
        self.career.append(0)
        self.agent.append("")
        return i

    def initial(self, month: int) -> list[int]:
        """SPEC-SIM §3.1: N₀ players; juniors 35 % (8-17 uniform), adults 18-65 with a density falling to 0 at 65."""
        rnd, out = self.rnd, []
        for _ in range(self.cfg.n0):
            if rnd.random() < 0.35:
                age = rnd.randint(8, 17)
            else:
                age = min(64, int(65 - 47 * math.sqrt(rnd.random())))          # density ∝ 65 − age on [18, 65]
            th = rnd.gauss(1450.0, 250.0) if age <= 19 else rnd.gauss(1750.0, 280.0)
            out.append(self.add(max(800.0, th), age, self.draw_fed(), month))
        return out

    def entrants(self, month: int, active: int) -> list[int]:
        """SPEC-SIM §3.2: entry_rate × active entrants with E1's age shares and 2023 medians."""
        rnd, cfg = self.rnd, self.cfg
        k = poisson(rnd, cfg.entry_rate * active)
        out = []
        for _ in range(k):
            u, g = rnd.random(), 0
            acc = 0.0
            for g, s in enumerate(cfg.entrant_share):
                acc += s
                if u <= acc:
                    break
            lo, hi = C.ENTRANT_AGES[g]
            age = rnd.randint(lo, hi)
            th = rnd.gauss(C.ENTRANT_MEDIAN[g], cfg.entrant_sd)
            out.append(self.add(max(700.0, th), age, self.draw_fed(), month))
        return out

    def exits(self, month: int, rated_games) -> list[int]:
        """SPEC-SIM §3.2's hazards; rated_games(i) is the player's rated games so far on Layer 0's list."""
        rnd, cfg, out = self.rnd, self.cfg, []
        for i in range(self.n):
            if not self.alive[i] or self.agent[i]:
                continue
            a = self.age(i, month)
            h = cfg.exit_base if rated_games(i) >= 30 else cfg.exit_new
            if 18 <= a <= 20 or a > 60:
                h *= 2.0
            if month - self.last_game[i] > 12 and month - self.first_month[i] > 12:
                h = max(h, cfg.exit_inactive)
            if rnd.random() < h:
                self.alive[i] = False
                out.append(i)
        return out

    def evolve(self, month: int) -> None:
        """SPEC-SIM §3.2: a month's drift and noise for every live player."""
        rnd, cfg = self.rnd, self.cfg
        y = self.year(month)
        for i in range(self.n):
            if not self.alive[i]:
                continue
            a = y - self.birth[i]
            b = age_band(a)
            th = self.theta[i]
            mu = C.DRIFT_A[b] + C.DRIFT_B[b] * (th - 2000.0) / 400.0
            if b < 4:
                mu *= self.talent[i]
            elif b == 4:
                mu = 0.0
            self.theta[i] = th + mu + rnd.gauss(0.0, cfg.noise_scale * cfg.dgp_profile[b])

    def play(self, w: int, b: int) -> int:
        """One game from the D1 model with true strengths (SPEC-SIM §3.3); White's score in half points."""
        tw, tb = self.theta[w], self.theta[b]
        z = C.Q * (tw - tb + C.ETA_L)
        level = (to_pub(tw) + to_pub(tb)) / 2.0
        mid = 1450.0 if level < 1500 else 2850.0 if level >= 2800 else 1500.0 + 100.0 * ((level - 1500.0) // 100.0) + 50.0
        nu = math.exp(C.ALPHA + C.BETA * (mid - 2000.0) / 400.0 - C.GAMMA * abs(z))
        a = math.exp(z / 2.0)
        d = a + 1.0 / a + nu
        u = self.rnd.random() * d
        if u < a:
            return 2
        if u < a + nu:
            return 1
        return 0
