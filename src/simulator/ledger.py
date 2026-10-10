"""The rating ledgers: Layer 0 and each rung on the same games (docs/specs/SPEC-SIM_v1_0.md §4).

A ledger holds one published list. Expectations are in thousandths, K in tenths for the rungs that set it to
one decimal, so a period's change is exact before its single rounding, half away from zero (§8.3.4 [V 1]).
Rungs: "2" the fitted table with R17's guard, "2u" without it, "3" seeds from Layer 1's proxy, "4a" K from the
activity record (SPEC-K-ACTIVITY, R16), "4l" K from Layer 1's proxy (R16), "5" junior compensation (R5, R8),
"6" the monthly adjustment (R3), "7" the federation adjustment. Standard library only.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from layer2 import kactivity, table

from . import config as C
from . import fide

XOFF = 2600
MIDS = tuple(range(1450, 2851, 100))
D0, GAMMA_A, A_CAP = 2.0, 1.0 / 6.0, 1.5
TAU, C_CAP, Z90 = 25, 300, 1.2816
S0 = 250.0
PDU10 = [fide.pd100_uncapped(d) * 10 for d in range(0, fide.DMAX + 1)]


def fit_table(kappa: float) -> tuple[list[list[int]], int]:
    """The published three-decimal table (annex T3.4) for every band midpoint and effective gap, in thousandths."""
    par = (kappa, C.ETA, C.ALPHA, C.BETA, C.GAMMA)
    out = []
    for mid in MIDS:
        row = [0] * (2 * XOFF + 1)
        for x in range(0, XOFF + 1):
            e = int(table.published(x, mid, par) * 1000)
            row[XOFF + x] = e
            row[XOFF - x] = 1000 - e
        out.append(row)
    return out, table.eta_whole(C.ETA)


def mid_index(level: int) -> int:
    if level < 1500:
        return 0
    if level >= 2800:
        return len(MIDS) - 1
    return 1 + (level - 1500) // 100


def fit_kappa(cells: dict, start: float = C.KAPPA0) -> float | None:
    """Annex T3.3 restricted to the slope: maximum likelihood of κ on a year's rated games of one ledger, cells
    (White's published gap x, level band midpoint, White's score in halves) -> games; η, α, β, γ held at E2's."""
    if sum(cells.values()) < 2000:
        return None
    items = sorted(cells.items())

    def score(k: float) -> float:
        g = 0.0
        for (x, mid, s2), w in items:
            z = k * C.Q * (x + C.ETA)
            nu = math.exp(C.ALPHA + C.BETA * (mid - 2000.0) / 400.0 - C.GAMMA * abs(z))
            a = math.exp(z / 2.0)
            den = a + 1.0 / a + nu
            pw, pd = a / den, nu / den
            s = s2 / 2.0
            dr = 1.0 if s2 == 1 else 0.0
            sg = 1.0 if z > 0 else -1.0 if z < 0 else 0.0
            g += w * ((s - (pw + 0.5 * pd)) - C.GAMMA * sg * (dr - pd)) * C.Q * (x + C.ETA)
        return g
    k = start
    for _ in range(25):
        g = score(k)
        h = (score(k + 1e-4) - g) / 1e-4
        if h >= 0:
            break
        step = -g / h
        k = min(4.0, max(0.3, k + step))
        if abs(step) < 1e-6:
            break
    return k


def round_float(x: float) -> int:
    """Half away from zero for a total that carries a one-decimal adjustment balance."""
    d = Decimal(repr(x)).quantize(Decimal("0.0000001"))
    q = abs(d).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(q) if d >= 0 else -int(q)


class Ledger:
    def __init__(self, name: str, rungs: set, fit: tuple | None, ck: float):
        self.name, self.rungs = name, rungs
        self.fit = "2" in rungs or "2u" in rungs
        self.guard = "2" in rungs
        self.seeds = "3" in rungs
        self.kmode = "activity" if "4a" in rungs else "proxy" if "4l" in rungs else "fide"
        self.comp = "5" in rungs
        self.adjust = "6" in rungs
        self.fedadj = "7" in rungs
        self.tables, self.eta = fit if fit else (None, 0)
        self.kappa = C.KAPPA0
        self.ck = ck
        self.rated: list[bool] = []
        self.R: list[int] = []
        self.kpub: list[int] = []
        self.gcount: list[int] = []
        self.e24: list[bool] = []
        self.e23: list[bool] = []
        self.acc: list[int] = []
        self.ng: list[int] = []
        self.p_act: list[float] = []
        self.B: list[float] = []
        self.g12: list[list[int]] = []
        self.gy = [[], [], []]                    # rated games this calendar year, last year, the year before
        self.last_rated: list[int] = []
        self.had_event: list[bool] = []
        self.pool: dict[int, list] = {}
        self.elig: list[bool] = []
        self.cj: list[int] = []
        self.touched: set = set()
        self.pool_changed: set = set()
        self.first_rated: list[int] = []
        self.games_since_first: list[int] = []
        self.last_bad: list[int] = []
        self.anchor: list[int] = []
        self.d_link = 0.0        # chain links of d_t and of the level across the January re-basings (annex T2.4)
        self.level_link = 0.0
        self.jd: dict[str, list] = {}             # junior drain: adult's band -> [games, Σ(S − E) thousandths]
        self.tracked: list = []                   # arranged games: (i, j, s2_i, e_i, e_j)
        self.created_arranged = [0, 0.0]
        self.ledger_lines = {"entering": 0, "leaving_floor": 0, "changes": 0, "posted": 0.0}
        self.a_t = 0.0
        self.a_f: dict[int, float] = {}
        self.kappa_map = C.KAPPA0                 # the slope fitted on this list's published ratings (θ̃, annex T3.3)
        self.new_this_year = 0
        self.cells: dict = {}
        self.fit_kappa_yearly = not self.fit or bool(rungs & {"3", "5", "7"})

    # ------------------------------------------------------------------ players
    def add(self) -> None:
        for lst, v in ((self.rated, False), (self.R, 0), (self.kpub, 40), (self.gcount, 0), (self.e24, False),
                       (self.e23, False), (self.acc, 0), (self.ng, 0), (self.p_act, S0 * S0), (self.B, 0.0),
                       (self.last_rated, -999), (self.had_event, False), (self.elig, False), (self.cj, 0),
                       (self.first_rated, -1), (self.games_since_first, 0), (self.last_bad, 0)):
            lst.append(v)
        for g in self.gy:
            g.append(0)
        self.g12.append([0] * 12)

    def set_rated(self, i: int, r: int, games: int, year: int, birth: int, month: int) -> None:
        self.rated[i], self.R[i] = True, r
        self.gcount[i] += games
        self.e24[i] = self.e24[i] or r >= 2400
        self.e23[i] = self.e23[i] or r >= 2300
        self.kpub[i] = fide.published_k(r, self.gcount[i], self.e24[i], self.e23[i], year, birth)
        info = kactivity.Q * kactivity.Q * kactivity.score_variance(C.ALPHA, C.BETA, r)
        self.p_act[i] = kactivity.newcomer_var(games, info)
        self.B[i] = 0.0
        if self.first_rated[i] < 0:
            self.first_rated[i] = month

    def copy_from(self, other: "Ledger") -> None:
        """Adoption: start from another ledger's list as it stands (annex T11, stage 4: no one-off adjustment)."""
        for name in ("rated", "R", "kpub", "gcount", "e24", "e23", "p_act", "last_rated", "had_event", "first_rated",
                     "games_since_first", "last_bad"):
            setattr(self, name, list(getattr(other, name)))
        self.gy = [list(g) for g in other.gy]
        self.g12 = [list(g) for g in other.g12]
        self.pool = {i: [[e[0], e[1], list(e[2]), e[3]] for e in ev] for i, ev in other.pool.items()}
        self.anchor = list(other.anchor)
        self.kappa_map = other.kappa_map
        n = len(self.R)
        self.acc, self.ng, self.B = [0] * n, [0] * n, [0.0] * n
        self.elig, self.cj = [False] * n, [0] * n

    # ------------------------------------------------------------------ one game
    def expect(self, own: int, opp_eff: int, colour: int, mid: int, opp_pub: int | None = None) -> int:
        """Expectation in thousandths; with rung 2 the guard of R17, the favourite's 2300 read on its published rating
        (D-0009, reading 4; opp_pub is the opponent's published rating when opp_eff is a compensated RX)."""
        if not self.fit:
            return fide.pd100(own, opp_eff) * 10
        e = self.tables[mid][own - opp_eff + colour * self.eta + XOFF]
        if self.guard:
            g = own - opp_eff
            if g >= 400 and own >= 2300:
                v = PDU10[min(g, fide.DMAX)]
                if v > e:
                    e = v
            elif g <= -400 and (opp_eff if opp_pub is None else opp_pub) >= 2300:
                v = 1000 - PDU10[min(-g, fide.DMAX)]
                if v < e:
                    e = v
        return e

    def game(self, w: int, b: int, s2: int, eid: int, month: int, jun, arranged: bool = False) -> None:
        rated = self.rated
        rw_ok, rb_ok = rated[w], rated[b]
        if rw_ok and rb_ok:
            R = self.R
            rw, rb = R[w], R[b]
            ow, ob = rb, rw
            if self.comp:
                ew_, eb_ = self.elig[w], self.elig[b]
                if eb_ and not ew_:
                    ow = rb + self.cj[b]
                if ew_ and not eb_:
                    ob = rw + self.cj[w]
            lv = (rw + rb) // 2
            mid = mid_index(lv) if self.fit else 0
            if self.fit_kappa_yearly:
                key = (rw - rb, MIDS[mid_index(lv)], s2)
                self.cells[key] = self.cells.get(key, 0) + 1
            ew = self.expect(rw, ow, 1, mid, rb)
            eb = self.expect(rb, ob, -1, mid, rw)
            sw = 500 * s2
            self.acc[w] += sw - ew
            self.acc[b] += 1000 - sw - eb
            self.ng[w] += 1
            self.ng[b] += 1
            self.touched.add(w)
            self.touched.add(b)
            jw, jb = jun[w], jun[b]
            if jw != jb:                                   # an adult (2) against a junior (1)
                ad, s_ad, e_ad, r_ad = (w, sw, ew, rw) if jw == 2 else (b, 1000 - sw, eb, rb)
                band = "<1600" if r_ad < 1600 else "1600-1999" if r_ad < 2000 else "2000-2399" if r_ad < 2400 else "2400+"
                c = self.jd.setdefault(band, [0, 0])
                c[0] += 1
                c[1] += s_ad - e_ad
            if arranged:
                self.tracked.append((w, b, s2, ew, eb))
        elif rw_ok or rb_ok:
            new, opp, opp_r, s_new = (b, w, self.R[w], 2 - s2) if rw_ok else (w, b, self.R[b], s2)
            ev = self.pool.setdefault(new, [])
            if not ev or ev[-1][0] != eid:
                ev.append([eid, month, [], not self.had_event[new]])
                self.had_event[new] = True
            ev[-1][2].append((opp_r, s_new, opp))
            self.pool_changed.add(new)

    # ------------------------------------------------------------------ the month's close
    def k_and_scale(self, i: int, n: int, proxy, age: int) -> tuple[int, int, float]:
        """The period's K as an integer and its scale (K = k/scale), and K as a number."""
        if self.kmode == "fide":
            k = fide.k_for_period(self.kpub[i], n)
            return k, 1, float(k)
        if self.kmode == "activity":
            s2 = kactivity.period_sigma2(self.p_act[i], self.ck, age)
        else:
            s2 = proxy.v_prior[i]
        v = kactivity.score_variance(C.ALPHA, C.BETA, self.R[i])
        k10 = int(round(kactivity.k_printed(s2, n, self.kappa, v) * 10))
        return k10, 10, k10 / 10.0

    def close(self, month: int, sim) -> None:
        """Rate the month's games (one period), then newcomers and floor exits; the activity variance grows."""
        pool, proxy = sim.pool, sim.proxy
        year_next = pool.year(month + 1)
        mi = month % 12
        lines = self.ledger_lines
        k_used: dict[int, float] = {}
        for i in sorted(self.touched):
            n = self.ng[i]
            age = pool.age(i, month)
            k, sc, kf = self.k_and_scale(i, n, proxy, age)
            k_used[i] = kf
            if self.B[i] != 0.0:
                total = k * self.acc[i] / (1000 * sc) + self.B[i]
                change = round_float(total)
                lines["posted"] += self.B[i]
                self.B[i] = 0.0
            else:
                change = fide.round_half_away(k * self.acc[i], 1000 * sc)
            if self.kmode == "activity":
                s2 = kactivity.period_sigma2(self.p_act[i], self.ck, age)
                v = kactivity.score_variance(C.ALPHA, C.BETA, self.R[i])
                self.p_act[i] = 1.0 / (1.0 / s2 + n * kactivity.Q * kactivity.Q * v)
            self.R[i] += change
            lines["changes"] += change
            self.gcount[i] += n
            self.gy[0][i] += n
            self.g12[i][mi] += n
            self.last_rated[i] = month
            if self.first_rated[i] >= 0:
                self.games_since_first[i] += n
            r = self.R[i]
            self.e24[i] = self.e24[i] or r >= 2400
            self.e23[i] = self.e23[i] or r >= 2300
            self.kpub[i] = fide.published_k(r, self.gcount[i], self.e24[i], self.e23[i], year_next, pool.birth[i])
            if r < 1400:                                   # R-32: shown as unrated on the next list
                lines["leaving_floor"] += r
                self.rated[i] = False
                self.R[i] = 0
                self.pool.pop(i, None)
            self.acc[i] = 0
            self.ng[i] = 0
        for (w, b, s2, ew, eb) in self.tracked:
            kw, kb = k_used.get(w, 0.0), k_used.get(b, 0.0)
            self.created_arranged[0] += 1
            self.created_arranged[1] += (kw * (500 * s2 - ew) + kb * (500 * (2 - s2) - eb)) / 1000.0
        self.tracked.clear()
        if self.kmode == "activity":                      # idle rated players: the variance grows (SPEC-K-ACTIVITY §3)
            for i in range(len(self.R)):
                if self.rated[i] and i not in self.touched and pool.alive[i]:
                    self.p_act[i] = kactivity.period_sigma2(self.p_act[i], self.ck, pool.age(i, month))
        for i in sorted(self.pool_changed):
            if self.rated[i] or not pool.alive[i]:
                continue
            ev = [e for e in self.pool.get(i, []) if month - e[1] < 26]           # R-27: 26 periods
            self.pool[i] = ev
            r = (self.seed(i, ev, month, sim) if self.seeds
                 else fide.initial_rating([(e[3], [(rr, ss) for rr, ss, _ in e[2]]) for e in ev]))
            if r is not None:
                games = sum(len(e[2]) for e in ev)
                self.set_rated(i, r, games, year_next, pool.birth[i], month)
                lines["entering"] += r
                self.new_this_year += 1
                del self.pool[i]
        self.touched.clear()
        self.pool_changed.clear()
        self.g12_roll(month)

    def g12_roll(self, month: int) -> None:
        nxt = (month + 1) % 12
        for g in self.g12:
            g[nxt] = 0

    def seed(self, i: int, ev: list, month: int, sim) -> int | None:
        """Rung 3 (annex T4.7): min(round(θ̃), 2200) with the gates, from Layer 1's proxy."""
        res = [x for e in ev for x in e[2]]
        if len(res) < 5 or len(ev) < 2 or len({o for _, _, o in res}) < 3:
            return None
        th, sd = sim.theta_tilde(self, i)
        if th is None or sd > 120.0:
            return None
        r = int(Decimal(repr(th)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        if r < 1400:
            return None
        return min(r, 2200)

    # ------------------------------------------------------------------ the year, the anchor, adjustments
    def new_year(self, month: int, pool) -> None:
        """Every January: roll the yearly counts and re-form the anchor cohort (aged 25-45, 10 or more rated games in
        each of the two preceding calendar years; annex T2.4, SPEC-L1 §3.5)."""
        self.gy = [[0] * len(self.R), self.gy[0], self.gy[1]]
        if self.fit_kappa_yearly:
            k = fit_kappa(self.cells, self.kappa_map)
            if k is not None:
                self.kappa_map = k
            self.cells = {}
        y = pool.year(month)
        self.anchor = [i for i in range(len(self.R)) if self.rated[i] and pool.alive[i] and 25 <= y - pool.birth[i] <= 45
                       and self.gy[1][i] >= 10 and self.gy[2][i] >= 10]

    def members(self, pool) -> list[int]:
        return [i for i in self.anchor if self.rated[i] and pool.alive[i]]

    def accrue(self, month: int, pool, amount_of) -> None:
        """Rungs 6 and 7 (annex T4.5, R3): accrue to active players, scaled by min(1, g_i / n̄)."""
        mem = self.members(pool)
        nbar = sum(sum(self.g12[i]) for i in mem) / len(mem) if mem else 0.0
        for i in range(len(self.R)):
            if not self.rated[i] or not pool.alive[i] or month - self.last_rated[i] > 11:
                continue
            a = amount_of(i)
            if a == 0.0:
                continue
            g = sum(self.g12[i])
            self.B[i] += a * (min(1.0, g / nbar) if nbar > 0 else 1.0)

    def eligibility(self, month: int, sim) -> None:
        """Rung 5 (annex T4.6; R5, R8): eligible juniors and their c_j, from Layer 1's proxy."""
        pool = sim.pool
        y = pool.year(month)
        for i in range(len(self.R)):
            self.elig[i] = False
            self.cj[i] = 0
            if not self.rated[i] or not pool.alive[i] or y - pool.birth[i] > 19:
                continue
            st = sim.window.get(i)
            if not st or st[0] < 10 or len(st[1]) < 5 or len(st[2]) < 3:
                continue
            self.elig[i] = True
            th, sd = sim.theta_tilde(self, i)
            if th is None:
                continue
            c = th - Z90 * sd - self.R[i] - TAU
            d = Decimal(repr(c)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
            self.cj[i] = min(C_CAP, max(0, int(d)))


def adjustment(d_t: float) -> float:
    """Annex T4.5: a_t = clip(γ_a sign(d_t) max(0, |d_t| − d_0), ±a_cap), one decimal."""
    raw = GAMMA_A * (1.0 if d_t > 0 else -1.0 if d_t < 0 else 0.0) * max(0.0, abs(d_t) - D0)
    a = min(A_CAP, max(-A_CAP, raw))
    return float(Decimal(repr(a)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def fed_adjustment(phi: float, shrink: float) -> float:
    a = min(A_CAP, max(-A_CAP, GAMMA_A * shrink * phi))
    return float(Decimal(repr(a)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def anchor_gap(led: Ledger, pool, proxy, c_ref: float) -> tuple[float, float, float] | None:
    """d_t = m̂_t − m_t over the anchor's members on settled ratings R + B (annex T2.4), chain-linked across the
    January re-basings (led.d_link), with the current panel's m_t and m̂_t."""
    mem = [i for i in led.members(pool) if proxy.m[i] is not None]
    if not mem:
        return None
    m_t = sum(led.R[i] + led.B[i] for i in mem) / len(mem)
    m_hat = sum(proxy.m[i] + c_ref for i in mem) / len(mem)
    return m_hat - m_t + led.d_link, m_t, m_hat



def sd(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mu = sum(values) / n
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (n - 1))
