"""The simulator with rung 2 v2 (session ELO-6, Phase 5; docs/decisions/D-0011_rulings-and-freeze-3.md).

The pool's true outcome model is the v2 table (E11; params/table_fit_2026-10b.yaml, standard), applied to true
strengths on the published scale as E9 applied E2's table: z = κ(L) q (θᴾ_W − θᴾ_B + η), L the band of the true
level, with the draw tail γ(L). Layer 1's proxy uses the same model, as it used E2's in E9, so that it still knows
the pool's average dynamics (SPEC-SIM §5). Rung 2's ledgers read the published v2 table; "2" adds the narrowed guard
of R24 (src/layer2/guard_v2.py; params/guard_2026-10b.yaml), "2u" is without it; at today's K (no rung 4) every game's
K is multiplied by the printed slope ratio m(L) of the game's level band (R32). Rung 4's K uses the v2 table's κ(L)
and v(L) in the band of the player's rating (annex T4.3), the simulator's variances (in latent units of κ₀ times the
published scale, SPEC-SIM §5) carried to the v2 table's latent units at L by (κ(L)/κ₀)², so that K is the Kalman
gain on the published scale under the v2 table. The rulings that change a ledger: R25 (rung 4's K fixed per event,
n counting the period's games up to the event, n K(n) ≤ max(C, 700)), R33 (accrual ends three months after the last
rated game) and, for R29's cap, a per-player tally of line-2 creation (points created through unequal K, attributed
to the player with the larger K) over the trailing twelve months.

The frozen simulator (Freeze 2) is not modified: install() replaces, in the running process only, Pool.play, the
simulator's Proxy, Ledger and fit_table with the classes and functions here. Standard library only.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal
from pathlib import Path

from layer1 import model
from layer2 import guard_v2 as gv2
from layer2 import kactivity
from layer2 import table_v2 as t2

from . import config as C
from . import fide
from . import ledger as L
from . import pool as P
from . import proxy as X
from . import run as R

ROOT = Path(__file__).resolve().parents[2]
_V2 = t2.load((ROOT / "params" / "table_fit_2026-10b.yaml").read_text(encoding="utf-8"), "standard")
PAR = _V2["par"]                                             # (κ, λ, η, α, β, γ, μ) as printed
M100 = {mid: int(_V2["k_scale"][mid] * 100) for mid in t2.BAND_MIDS} if _V2["k_scale_applies"] else \
    {mid: 100 for mid in t2.BAND_MIDS}
_G = re.search(r"^standard:\n((?:  .*\n?)+)", (ROOT / "params" / "guard_2026-10b.yaml").read_text(encoding="utf-8"), re.M)
GUARD_APPLIES = re.search(r"^  applies: (\w+)$", _G.group(1), re.M).group(1) == "true"
KAPPA_V2, ETA_V2 = PAR[0], PAR[2]


def _mid(level: float) -> float:
    return 1450.0 if level < 1500 else 2850.0 if level >= 2800 else 1500.0 + 100.0 * ((level - 1500.0) // 100.0) + 50.0


def _kz(mid: float) -> tuple[float, float]:
    """κ(L) q and γ(L) of the v2 table at a band midpoint."""
    return t2.kappa_at(PAR, mid) * C.Q, t2.gamma_at(PAR, mid)


_KV: dict[int, tuple[float, float, float]] = {}


def _kv(rating: int) -> tuple[float, float, float]:
    """Rung 4 with the v2 table, in the band of a published rating: κ(L), v(L) = 1/(2(2 + ν₀(L))) and (κ(L)/κ₀)², the
    factor that carries a variance in the simulator's latent units to the v2 table's latent units at L."""
    mid = t2.band_mid(int(rating))
    out = _KV.get(mid)
    if out is None:
        kap = t2.kappa_at(PAR, mid)
        v = 1.0 / (2.0 * (2.0 + math.exp(PAR[3] + PAR[4] * t2.ell(mid))))
        out = _KV[mid] = (kap, v, (kap / C.KAPPA0) ** 2)
    return out


# ---------------------------------------------------------------------- the true model and Layer 1's proxy
def play_v2(self, w: int, b: int) -> int:
    """One game from the v2 table at the true strengths on the published scale; White's score in half points."""
    pw_, pb_ = P.to_pub(self.theta[w]), P.to_pub(self.theta[b])
    mid = _mid((pw_ + pb_) / 2.0)
    kq, gam = _kz(mid)
    z = kq * (pw_ - pb_ + ETA_V2)
    nu = math.exp(PAR[3] + PAR[4] * (mid - 2000.0) / 400.0 - gam * abs(z))
    a = math.exp(z / 2.0)
    d = a + 1.0 / a + nu
    u = self.rnd.random() * d
    if u < a:
        return 2
    if u < a + nu:
        return 1
    return 0


class ProxyV2(X.Proxy):
    """Layer 1's proxy with the v2 table's likelihood: in latent units z = κ(L) q ((m_W − m_B)/κ₀ + η)."""

    def game(self, w: int, b: int, s2: int) -> None:
        mw, mb = self.m[w], self.m[b]
        mid = _mid(2000.0 + ((mw + mb) / 2.0 - 2000.0) / C.KAPPA0)
        kq, gam = _kz(mid)
        dz = kq / C.KAPPA0
        z = dz * (mw - mb) + kq * ETA_V2
        nu0 = math.exp(PAR[3] + PAR[4] * (mid - 2000.0) / 400.0)
        _lp, u, inf = model.game_terms(z, nu0, gam, s2 / 2.0)
        g, h = dz * u, dz * dz * inf
        self.grad[w] = self.grad.get(w, 0.0) + g
        self.grad[b] = self.grad.get(b, 0.0) - g
        self.info[w] = self.info.get(w, 0.0) + h
        self.info[b] = self.info.get(b, 0.0) + h


# ---------------------------------------------------------------------- the published v2 table
def fit_table_v2(kappa: float) -> tuple[list[list[int]], int]:
    """The published three-decimal v2 table for every band midpoint and effective gap, in thousandths. The argument is
    the frozen simulator's κ: κ₀ gives the v2 table as fitted, and the ratchet's κ₀ − 0.05 k lowers the v2 table's κ by
    the same amount."""
    par = (KAPPA_V2 + (kappa - C.KAPPA0),) + PAR[1:]
    out = []
    for mid in L.MIDS:
        row = [0] * (2 * L.XOFF + 1)
        for x in range(0, L.XOFF + 1):
            e = int(t2.published(x, mid, par) * 1000)
            row[L.XOFF + x] = e
            row[L.XOFF - x] = 1000 - e
        out.append(row)
    return out, t2.eta_whole(ETA_V2)


# ---------------------------------------------------------------------- the ledgers
class LedgerV2(L.Ledger):
    """The frozen Ledger with rung 2 v2, R25, R33 and the line-2 tally (module docstring)."""

    def __init__(self, name: str, rungs: set, fit: tuple | None, ck: float):
        super().__init__(name, rungs, fit, ck)
        self.guard_v2 = "2" in rungs and GUARD_APPLIES
        self.guard = False                                     # R17's guard is replaced by the narrowed guard
        self.scale_k = self.fit and self.kmode == "fide"       # R32: rung 2 at today's K
        self.games_rec: list[tuple] = []                       # the month's rated games (R25, line 2)
        self.ev: dict[int, dict[int, list]] = {}               # player -> event -> [Σ m(S − E) thousandths·hundredths, games]
        self.l2_ring: dict[int, list[float]] = {}              # player -> line-2 creation in each of the last 12 months
        self.l2_ymax: dict[int, float] = {}                    # player -> the year's largest trailing twelve-month sum
        self.line2_years: list[dict] = []                      # per year of operation: player -> that largest sum

    # -- one game
    def expect(self, own: int, opp_eff: int, colour: int, mid: int, opp_pub: int | None = None) -> int:
        if not self.fit:
            return fide.pd100(own, opp_eff) * 10
        e = self.tables[mid][own - opp_eff + colour * self.eta + L.XOFF]
        if self.guard_v2:
            op = opp_eff if opp_pub is None else opp_pub
            w = gv2.weight(own, op)
            if w:
                x = own - opp_eff + colour * self.eta
                g, _b = gv2.guard_own(Decimal(e) / 1000, x, own > op, w)
                e = int(g * 1000)
        return e

    def game(self, w: int, b: int, s2: int, eid: int, month: int, jun, arranged: bool = False) -> None:
        rated = self.rated
        if not (rated[w] and rated[b]):
            super().game(w, b, s2, eid, month, jun, arranged)
            return
        R_ = self.R
        rw, rb = R_[w], R_[b]
        ow, ob = rb, rw
        if self.comp:
            ew_, eb_ = self.elig[w], self.elig[b]
            if eb_ and not ew_:
                ow = rb + self.cj[b]
            if ew_ and not eb_:
                ob = rw + self.cj[w]
        lv = (rw + rb) // 2
        mid = L.mid_index(lv) if self.fit else 0
        if self.fit_kappa_yearly:
            key = (rw - rb, L.MIDS[L.mid_index(lv)], s2)
            self.cells[key] = self.cells.get(key, 0) + 1
        ew = self.expect(rw, ow, 1, mid, rb)
        eb = self.expect(rb, ob, -1, mid, rw)
        e0w = ew if ow == rb else self.expect(rw, rb, 1, mid, rb)   # without compensation (line 2's E⁰, annex T6)
        e0b = eb if ob == rw else self.expect(rb, rw, -1, mid, rw)
        m = M100[L.MIDS[L.mid_index(lv)]] if self.scale_k else 100
        sw = 500 * s2
        for i, r in ((w, sw - ew), (b, 1000 - sw - eb)):
            self.ev.setdefault(i, {}).setdefault(eid, [0, 0])
            e_ = self.ev[i][eid]
            e_[0] += m * r
            e_[1] += 1
        self.acc[w] += m * (sw - ew)
        self.acc[b] += m * (1000 - sw - eb)
        self.ng[w] += 1
        self.ng[b] += 1
        self.touched.add(w)
        self.touched.add(b)
        jw, jb = jun[w], jun[b]
        if jw != jb:
            ad, s_ad, e_ad, r_ad = (w, sw, ew, rw) if jw == 2 else (b, 1000 - sw, eb, rb)
            band = "<1600" if r_ad < 1600 else "1600-1999" if r_ad < 2000 else "2000-2399" if r_ad < 2400 else "2400+"
            c = self.jd.setdefault(band, [0, 0])
            c[0] += 1
            c[1] += s_ad - e_ad
        self.games_rec.append((w, b, s2, e0w, e0b, ew, eb, m, eid, arranged))

    # -- the period's K
    def set_rated(self, i: int, r: int, games: int, year: int, birth: int, month: int) -> None:
        """The frozen first rating, with the activity variance's information per game from the v2 table."""
        super().set_rated(i, r, games, year, birth, month)
        _kap, v, f = _kv(r)
        self.p_act[i] = kactivity.newcomer_var(games, kactivity.Q * kactivity.Q * v * f)

    def k_event(self, i: int, n_cum: int, proxy, age: int) -> int:
        """R25 (D-0011, reading 9): K in tenths for an event with n_cum the period's games up to it, n K(n) ≤ max(C, 700),
        with the v2 table's κ(L) and v(L) in the band of the player's rating (annex T4.3)."""
        kap, v, f = _kv(self.R[i])
        if self.kmode == "activity":
            s2 = kactivity.period_sigma2(self.p_act[i], self.ck, age) * f
        else:
            s2 = proxy.v_prior[i] * f
        k = kactivity.k_printed(s2, n_cum, kap, v)
        c, _n = kactivity.published_form(s2, kap, v)
        k10 = int(round(k * 10))
        return min(k10, int(math.floor(max(c, 700.0) * 10 / n_cum)))

    def close(self, month: int, sim) -> None:
        pool, proxy = sim.pool, sim.proxy
        year_next = pool.year(month + 1)
        mi = month % 12
        lines = self.ledger_lines
        k_game: dict[tuple[int, int], float] = {}                      # (player, event) -> K
        for i in sorted(self.touched):
            n = self.ng[i]
            age = pool.age(i, month)
            if self.kmode == "fide":                                   # exact, as the frozen ledger: K x Σ m(S − E)
                k = fide.k_for_period(self.kpub[i], n)
                for eid in self.ev.get(i, {}):
                    k_game[(i, eid)] = float(k)
                num, den = k * self.acc[i], 100000
            else:                                                      # R25: K in tenths per event, n cumulative
                num, n_cum = 0, 0
                for eid in sorted(self.ev.get(i, {})):
                    s, g = self.ev[i][eid]
                    n_cum += g
                    k10 = self.k_event(i, n_cum, proxy, age)
                    k_game[(i, eid)] = k10 / 10.0
                    num += k10 * s
                den = 1000000
            if self.B[i] != 0.0:
                change = L.round_float(num / den + self.B[i])
                lines["posted"] += self.B[i]
                self.B[i] = 0.0
            else:
                change = fide.round_half_away(num, den)
            if self.kmode == "activity":
                s2 = kactivity.period_sigma2(self.p_act[i], self.ck, age)
                _kap, v, f = _kv(self.R[i])
                self.p_act[i] = 1.0 / (1.0 / s2 + n * kactivity.Q * kactivity.Q * v * f)
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
            if r < 1400:
                lines["leaving_floor"] += r
                self.rated[i] = False
                self.R[i] = 0
                self.pool.pop(i, None)
            self.acc[i] = 0
            self.ng[i] = 0
        month_l2: dict[int, float] = {}
        for (w, b, s2, e0w, e0b, ew, eb, m, eid, arranged) in self.games_rec:
            kw, kb = k_game.get((w, eid), 0.0), k_game.get((b, eid), 0.0)
            if arranged:
                self.created_arranged[0] += 1
                self.created_arranged[1] += m * (kw * (500 * s2 - ew) + kb * (500 * (2 - s2) - eb)) / 100000.0
            created = m * (kw * (500 * s2 - e0w) + kb * (500 * (2 - s2) - e0b)) / 100000.0
            if created and kw != kb:
                who = w if kw > kb else b
                month_l2[who] = month_l2.get(who, 0.0) + created
        self.games_rec.clear()
        self.ev.clear()
        for i in set(self.l2_ring) | set(month_l2):                   # R29: the trailing twelve months, per player
            ring = self.l2_ring.setdefault(i, [0.0] * 12)
            ring[mi] = month_l2.get(i, 0.0)
            s = sum(ring)
            if s > self.l2_ymax.get(i, 0.0):
                self.l2_ymax[i] = s
        if self.kmode == "activity":
            for i in range(len(self.R)):
                if self.rated[i] and i not in self.touched and pool.alive[i]:
                    self.p_act[i] = kactivity.period_sigma2(self.p_act[i], self.ck, pool.age(i, month))
        for i in sorted(self.pool_changed):
            if self.rated[i] or not pool.alive[i]:
                continue
            ev = [e for e in self.pool.get(i, []) if month - e[1] < 26]
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
        if mi == 11:
            if month >= sim.adopt:                                    # every player rated in the last twelve months
                self.line2_years.append({i: self.l2_ymax.get(i, 0.0) for i in range(len(self.R))
                                         if self.rated[i] and pool.alive[i] and month - self.last_rated[i] <= 11})
            self.l2_ymax = {}

    # -- R33
    def accrue(self, month: int, pool, amount_of) -> None:
        """Rungs 6 and 7 with R33: accrual only within three months of the player's last rated game."""
        mem = self.members(pool)
        nbar = sum(sum(self.g12[i]) for i in mem) / len(mem) if mem else 0.0
        for i in range(len(self.R)):
            if not self.rated[i] or not pool.alive[i] or month - self.last_rated[i] > 3:
                continue
            a = amount_of(i)
            if a == 0.0:
                continue
            g = sum(self.g12[i])
            self.B[i] += a * (min(1.0, g / nbar) if nbar > 0 else 1.0)


_INSTALLED = False


def install() -> None:
    """Replace, in this process, the frozen simulator's true model, proxy, ledger and published table."""
    global _INSTALLED
    if _INSTALLED:
        return
    P.Pool.play = play_v2
    R.Proxy = ProxyV2
    R.Ledger = LedgerV2
    R.fit_table = fit_table_v2
    _INSTALLED = True


def line2_stats(sim) -> dict:
    """R29's sizing (D-0011, reading 11): per ledger, each honest active player-year's largest trailing twelve-month
    line-2 creation (zero when none), its 99th and 99.9th percentiles, and the colluding juniors' values."""
    pool = sim.pool
    juniors = {a for a, _ in getattr(sim, "pairs", [])}
    res = {}
    for name, led in sim.ledgers.items():
        honest, col = [], []
        for year in led.line2_years:
            for i, v in year.items():
                if i in juniors:
                    col.append(round(v, 2))
                elif not pool.agent[i]:
                    honest.append(v)
        honest.sort()

        def q(p: float):
            return round(honest[min(len(honest) - 1, int(p * len(honest)))], 2) if honest else None
        res[name] = {"honest_player_years": len(honest), "honest_positive": sum(1 for v in honest if v > 0),
                     "p99": q(0.99), "p999": q(0.999), "max": round(honest[-1], 2) if honest else None,
                     "colluding_juniors": sorted(col)}
    return res


def run_v2(cfg: C.Config) -> dict:
    """One run of the simulator with the replacements of install(); the frozen run() plus R29's line-2 statistics."""
    install()
    sim = R.Sim(cfg)
    sim.start()
    for month in range(sim.end):
        sim.month(month)
    out = sim.finish()
    out["line2"] = line2_stats(sim)
    return out
