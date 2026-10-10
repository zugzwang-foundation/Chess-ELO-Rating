"""One simulation run (docs/specs/SPEC-SIM_v1_0.md): the pool, the events, Layer 1's proxy, every ledger, the
adversaries and the measurements of §6–§8. run(cfg) returns aggregates only. Deterministic for a given seed.
Standard library only."""
from __future__ import annotations

import math
import random
from collections import deque

from . import config as C
from . import events as EV
from . import fide
from .ledger import Ledger, adjustment, anchor_gap, fed_adjustment, fit_table, sd
from .pool import Pool, poisson, to_pub
from .proxy import Proxy

RUNG_SETS = {"L0": set(), "R2": {"2"}, "R2U": {"2u"}, "R3": {"3"}, "R4A": {"4a"}, "R4L": {"4l"}, "R5": {"5"},
             "R6": {"6"}, "R7": {"7"}, "ALL": {"2", "3", "4a", "5", "6"}}
TRUE_BANDS = ((0, 1600, "<1600"), (1600, 2000, "1600-1999"), (2000, 2400, "2000-2399"), (2400, 9999, "2400+"))
AGE_GROUPS = ((0, 19, "19 or less"), (20, 24, "20-24"), (25, 45, "25-45"), (46, 200, "46 or more"))
N_AGENTS = 30


class Sim:
    def __init__(self, cfg: C.Config):
        self.cfg = cfg
        self.rnd = random.Random(cfg.seed)
        self.pool = Pool(cfg, self.rnd)
        self.proxy = Proxy(cfg.noise_scale, cfg.junior_factor_mean)
        self.fit0 = fit_table(C.KAPPA0)
        self.L0 = Ledger("L0", set(), None, cfg.k_activity_ck)
        self.ledgers: dict[str, Ledger] = {"L0": self.L0}
        self.window: dict[int, tuple] = {}
        self.hist: dict[int, deque] = {}
        self.c_ref = 0.0
        self.anchor_stats: dict[str, tuple] = {}
        self.eid = 0
        self.adopt = cfg.burn_in
        self.end = cfg.burn_in + cfg.months
        self.jun: list[int] = []
        self.out: dict = {"name": cfg.name, "seed": cfg.seed}
        self.series: dict[str, dict[str, list]] = {}
        self.agents: dict[str, list[int]] = {}
        self.protect: dict[int, dict] = {}
        self.cross36: deque = deque()
        self.fed_cross: dict[int, int] = {}

    # ------------------------------------------------------------------ helpers
    def add_player(self, i: int) -> None:
        for led in self.ledgers.values():
            led.add()
        self.proxy.grow(i + 1)
        self.jun.append(1)

    def theta_tilde(self, led: Ledger, i: int) -> tuple[float | None, float]:
        m = self.proxy.m[i]
        st = self.anchor_stats.get(led.name)
        if m is None or st is None:
            return None, 1e9
        m_t, m_hat = st
        k = led.kappa_map
        return m_t + (m + self.c_ref - m_hat) / k, math.sqrt(self.proxy.v[i]) / k

    def active(self, month: int) -> int:
        p = self.pool
        return sum(1 for i in range(p.n) if p.alive[i] and month - p.last_game[i] <= 12)

    # ------------------------------------------------------------------ the start
    def start(self) -> None:
        cfg, pool, rnd = self.cfg, self.pool, self.rnd
        offs = cfg.fed_offsets or tuple(rnd.gauss(0.0, cfg.fed_offset_sd) for _ in C.FED_SIZES)
        self.out["fed_offsets_start"] = [round(o, 1) for o in offs]
        for i in pool.initial(0):
            self.add_player(i)
            r = int(round(to_pub(pool.theta[i]) + rnd.gauss(0.0, 50.0) + offs[pool.fed[i]]))
            r = max(1400, r)
            age = pool.age(i, 0)
            games = 30 + rnd.randint(0, 200) if age >= 20 else rnd.randint(5, 80)
            self.L0.set_rated(i, r, games, pool.year(0), pool.birth[i], 0)
            self.L0.first_rated[i] = -1
            self.proxy.start_rated(i, r)

    def adopt_ledgers(self, month: int) -> None:
        for name in self.cfg.ledgers:
            if name == "L0":
                continue
            led = Ledger(name, RUNG_SETS[name], self.fit0 if RUNG_SETS[name] & {"2", "2u"} else None, self.cfg.k_activity_ck)
            led.copy_from(self.L0)
            self.ledgers[name] = led
        mem = [i for i in self.L0.members(self.pool) if self.proxy.m[i] is not None]
        self.c_ref = (sum(self.L0.R[i] for i in mem) - sum(self.proxy.m[i] for i in mem)) / len(mem) if mem else 0.0
        for led in self.ledgers.values():
            led.jd.clear()
            led.created_arranged = [0, 0.0]
            led.ledger_lines = {"entering": 0, "leaving_floor": 0, "changes": 0, "posted": 0.0}
        if self.cfg.adversaries:
            self.pick_agents(month)
        self.top_cohort = [i for i in range(self.pool.n) if self.pool.alive[i] and self.L0.rated[i]
                           and 25 <= self.pool.age(i, month) <= 45 and to_pub(self.pool.theta[i]) >= 2400]
        self.snap_start = {name: {i: led.R[i] for i in self.top_cohort} for name, led in self.ledgers.items()}
        self.theta_start = {i: to_pub(self.pool.theta[i]) for i in self.top_cohort}
        self.out["fed_offsets_at_adoption"] = self.fed_offsets()

    # ------------------------------------------------------------------ adversaries (SPEC-SIM §7)
    def pick_agents(self, month: int) -> None:
        pool, L0, rnd = self.pool, self.L0, self.rnd

        def cands(pred) -> list[int]:
            c = [i for i in range(pool.n) if pool.alive[i] and L0.rated[i] and not pool.agent[i] and pred(i)]
            c.sort(key=lambda i: (to_pub(pool.theta[i]), i))
            return c

        def split(c: list[int], k: int, tag: str) -> None:
            take = c[-2 * k:] if len(c) >= 2 * k else c
            ag, ct = take[0::2], take[1::2]
            for i in ag:
                pool.agent[i] = tag
            for i in ct:
                pool.agent[i] = tag + "_control"
            self.agents[tag], self.agents[tag + "_control"] = ag, ct

        adult = lambda i: 25 <= pool.age(i, month) <= 45  # noqa: E731
        split(cands(lambda i: adult(i) and to_pub(pool.theta[i]) >= 2400), N_AGENTS, "farmer")
        split(cands(lambda i: adult(i) and 2000 <= L0.R[i] <= 2300), N_AGENTS, "sandbagger")
        jun = cands(lambda i: pool.age(i, month) <= 17 and 1800 <= L0.R[i] <= 2200)
        top = cands(lambda i: pool.age(i, month) >= 20 and L0.R[i] >= 2400)
        pairs = list(zip(jun[-15:], top[-15:]))
        for a, b in pairs:
            pool.agent[a] = pool.agent[b] = "colluder"
        self.agents["colluder_pairs"] = [a for a, _ in pairs] + [b for _, b in pairs]
        self.pairs = pairs
        prot = cands(lambda i: adult(i) and not pool.agent[i])
        rnd.shuffle(prot)
        for i in prot[:N_AGENTS]:
            pool.agent[i] = "protector"
            self.protect[i] = {"state": "watch"}
        self.agents["protector"] = prot[:N_AGENTS]
        self.agent_start = {name: {i: led.R[i] for g in self.agents.values() for i in g} for name, led in self.ledgers.items()}
        self.agent_theta_start = {i: to_pub(pool.theta[i]) for g in self.agents.values() for i in g}
        self.agent_games_start = {name: {i: led.gcount[i] for g in self.agents.values() for i in g}
                                  for name, led in self.ledgers.items()}

    # ------------------------------------------------------------------ the month
    def month(self, month: int) -> None:
        cfg, pool, proxy, rnd = self.cfg, self.pool, self.proxy, self.rnd
        operating = month >= self.adopt
        if month % 12 == 0:
            # the anchor panel is re-formed every January; after adoption d_t and the level are chain-linked across the
            # re-basing (annex T2.4): the new panel's values are set equal to the old panel's in the re-basing month,
            # so that who is in the panel does not move them (REDTEAM_v1_0, V10-STAT-5)
            link = month > self.adopt
            old = {n: (anchor_gap(led, pool, proxy, self.c_ref), level_of(led, pool)) for n, led in self.ledgers.items()} \
                if link else {}
            for led in self.ledgers.values():
                led.new_year(month, pool)
            for n, led in (self.ledgers.items() if link else ()):
                g_new, l_new = anchor_gap(led, pool, proxy, self.c_ref), level_of(led, pool)
                if old[n][0] is not None and g_new is not None:
                    led.d_link += old[n][0][0] - g_new[0]
                if old[n][1] is not None and l_new is not None:
                    led.level_link += old[n][1] - l_new
            self.calibration_year(month)
        if month == self.adopt:
            self.adopt_ledgers(month)
        if cfg.ratchet and operating and (month - self.adopt) % 12 == 0 and month > self.adopt and "R2" in self.ledgers:
            k = C.KAPPA0 - 0.05 * ((month - self.adopt) // 12)
            led = self.ledgers["R2"]
            led.tables, led.eta = fit_table(k)
            led.kappa = k
        ages = [pool.age(i, month) for i in range(pool.n)]
        proxy.predict(pool.alive, ages)
        for i in range(pool.n):
            self.jun[i] = 1 if ages[i] <= 19 else 2
        # list t: anchor statistics, rungs 5, 6, 7
        if operating and any(led.comp for led in self.ledgers.values()):
            self.update_window(month)
        for name, led in self.ledgers.items():
            g = anchor_gap(led, pool, proxy, self.c_ref)
            if g is not None:
                self.anchor_stats[name] = (g[1], g[2])
            if not operating:
                continue
            if led.comp:
                led.eligibility(month, self)
            if led.adjust and g is not None:
                led.a_t = adjustment(g[0])
                led.accrue(month, pool, lambda i, a=led.a_t: a)
            if led.fedadj:
                led.a_f = self.fed_amounts(led, month)
                led.accrue(month, pool, lambda i, af=led.a_f: af.get(pool.fed[i], 0.0))
        # entries
        for i in pool.entrants(month, max(1, self.active(month - 1))):
            self.add_player(i)
            proxy.ensure(i, pool.age(i, month))
        ages = [pool.age(i, month) for i in range(pool.n)]
        for i in range(len(self.jun)):
            self.jun[i] = 1 if ages[i] <= 19 else 2
        # events
        slots = []
        for i in range(pool.n):
            if not pool.alive[i]:
                continue
            ag = pool.agent[i]
            if ag == "farmer" and operating:
                continue
            if ag == "protector" and self.protect[i]["state"] == "away":
                continue
            k = poisson(rnd, pool.rate[i] / (12.0 * cfg.rounds_mean))
            for _ in range(k):
                intl = rnd.random() < (0.01 if pool.fed[i] in cfg.isolated else 1.0 - cfg.domestic_share)
                slots.append((i, -1 if intl else pool.fed[i]))
        rating = {i: (self.L0.R[i] if self.L0.rated[i] else 0) for i, _ in slots}
        games: list[tuple[int, int, int, int, bool]] = []
        for kind, ps, rounds in EV.form_events(slots, rating, cfg, rnd):
            self.eid += 1
            if kind == "rr":
                for rnd_pairs in EV.round_robin(ps)[:rounds]:
                    for w, b in rnd_pairs:
                        games.append((w, b, self.result(w, b, month), self.eid, False))
            else:
                sw = EV.Swiss(ps, rating)
                for _ in range(rounds):
                    for w, b in sw.pair():
                        s2 = self.result(w, b, month)
                        sw.record(w, b, s2)
                        games.append((w, b, s2, self.eid, False))
        if operating and cfg.adversaries:
            games.extend(self.agent_games(month))
        # rate the games
        for w, b, s2, eid, arranged in games:
            if proxy.m[w] is None:
                proxy.ensure(w, ages[w])
            if proxy.m[b] is None:
                proxy.ensure(b, ages[b])
            proxy.game(w, b, s2)
            pool.last_game[w] = pool.last_game[b] = month
            pool.career[w] += 1
            pool.career[b] += 1
            if pool.fed[w] != pool.fed[b]:
                self.fed_cross[pool.fed[w]] = self.fed_cross.get(pool.fed[w], 0) + 1
                self.fed_cross[pool.fed[b]] = self.fed_cross.get(pool.fed[b], 0) + 1
            hw, hb = self.hist.setdefault(w, deque()), self.hist.setdefault(b, deque())
            hw.append((month, b, eid))
            hb.append((month, w, eid))
            for led in self.ledgers.values():
                led.game(w, b, s2, eid, month, self.jun, arranged)
        self.out.setdefault("proxy_shift", []).append(round(proxy.update(self.L0.members(pool)), 3))
        for led in self.ledgers.values():
            led.close(month, self)
        if operating:
            self.measure(month)
            if cfg.adversaries:
                self.watch_protectors(month)
                if month - self.adopt in (11, 23):
                    self.checkpoint(month - self.adopt + 1)
        self.cross36.append(dict(self.fed_cross))
        self.fed_cross = {}
        if len(self.cross36) > 36:
            self.cross36.popleft()
        pool.exits(month, lambda i: self.L0.gcount[i])
        pool.evolve(month)

    def calibration_year(self, month: int) -> None:
        """The simulated Layer 0 list against FIDE's (E1, E5): yearly, as E5 measures them."""
        pool, L0 = self.pool, self.L0
        cal = self.out.setdefault("calibration", [])
        snap = getattr(self, "_snap", None)
        rated_active = [i for i in range(pool.n) if pool.alive[i] and L0.rated[i] and month - L0.last_rated[i] <= 12]
        row = {"month": month, "active_rated": len(rated_active), "entering_year": L0.new_this_year}
        L0.new_this_year = 0
        if snap is not None:
            by_age: dict[str, list] = {}
            by_band: dict[str, list] = {}
            for i, (r0, g0, age0) in snap.items():
                if not (pool.alive[i] and L0.rated[i]):
                    continue
                games = L0.gcount[i] - g0
                if games <= 0:
                    continue
                d = L0.R[i] - r0
                ag = "18 or less" if age0 <= 18 else "19-24" if age0 <= 24 else "25-45" if age0 <= 45 else "46-64" if age0 <= 64 else "65+"
                bd = ("<1600" if r0 < 1600 else "1600-1999" if r0 < 2000 else "2000-2199" if r0 < 2200 else "2200-2399" if r0 < 2400
                      else "2400-2599" if r0 < 2600 else "2600+")
                by_age.setdefault(ag, []).append((d, games))
                by_band.setdefault(bd, []).append((d, games))

            def summ(v: list) -> dict:
                ds = sorted(x for x, _ in v)
                return {"n": len(v), "median": ds[len(ds) // 2], "mean": round(sum(ds) / len(ds), 2),
                        "per_game": round(sum(ds) / max(1, sum(g for _, g in v)), 3), "games": round(sum(g for _, g in v) / len(v), 1)}
            row["by_age"] = {k: summ(v) for k, v in sorted(by_age.items())}
            row["by_band"] = {k: summ(v) for k, v in sorted(by_band.items())}
        cal.append(row)
        self._snap = {i: (L0.R[i], L0.gcount[i], pool.age(i, month)) for i in rated_active}

    def result(self, w: int, b: int, month: int) -> int:
        s2 = self.pool.play(w, b)
        if month >= self.adopt and month < self.adopt + 12 and self.cfg.adversaries:
            aw, ab = self.pool.agent[w], self.pool.agent[b]
            if aw == "sandbagger" and ab != "sandbagger":
                return 0
            if ab == "sandbagger" and aw != "sandbagger":
                return 2
        return s2

    def agent_games(self, month: int) -> list:
        """Farmers' monthly events against fields 400-800 below them, and the colluders' two arranged games."""
        pool, L0, rnd, out = self.pool, self.L0, self.rnd, []
        by_r = sorted((L0.R[i], i) for i in range(pool.n) if pool.alive[i] and L0.rated[i] and not pool.agent[i])
        rs = [r for r, _ in by_r]
        import bisect
        for f in self.agents.get("farmer", []):
            if not L0.rated[f]:
                continue
            lo, hi = bisect.bisect_left(rs, L0.R[f] - 800), bisect.bisect_right(rs, L0.R[f] - 400)
            if hi - lo < 9:
                continue
            self.eid += 1
            opps = rnd.sample(range(lo, hi), 9)
            for k, j in enumerate(opps):
                o = by_r[j][1]
                w, b = (f, o) if k % 2 == 0 else (o, f)
                out.append((w, b, self.pool.play(w, b), self.eid, False))
        for a, b in self.pairs:
            self.eid += 1
            out.append((a, b, 2, self.eid, True))
            out.append((b, a, 0, self.eid, True))
        return out

    def checkpoint(self, k: int) -> None:
        """Sandbaggers and their controls after the dumping year (12) and the year after (24); collusion's first year."""
        pool = self.pool
        for name, led in self.ledgers.items():
            cp = self.out.setdefault("checkpoints", {}).setdefault(name, {})
            for grp in ("sandbagger", "sandbagger_control"):
                ids = [i for i in self.agents.get(grp, []) if led.rated[i]]
                dr = [led.R[i] - self.agent_start[name][i] - (to_pub(pool.theta[i]) - self.agent_theta_start[i]) for i in ids]
                cp[f"{grp}_{k}"] = round(sum(dr) / max(1, len(ids)), 2)
            if k == 12:
                cp["collusion_first_year"] = round(led.created_arranged[1] / max(1, led.created_arranged[0]), 3)

    def watch_protectors(self, month: int) -> None:
        pool = self.pool
        for i, st in self.protect.items():
            if st["state"] == "watch" and self.L0.rated[i] and self.L0.R[i] - to_pub(pool.theta[i]) > 40:
                st.update(state="away", stop=month, err_stop={n: led.R[i] - to_pub(pool.theta[i]) for n, led in self.ledgers.items()})
            elif st["state"] == "away" and month - st["stop"] >= 24:
                st.update(state="back", back=month)
            elif st["state"] == "back" and "err_back" not in st and month > st["back"]:
                st["err_back"] = {n: led.R[i] - to_pub(pool.theta[i]) for n, led in self.ledgers.items()}
            elif st["state"] == "back" and "err_back12" not in st and month >= st["back"] + 12:
                st["err_back12"] = {n: led.R[i] - to_pub(pool.theta[i]) for n, led in self.ledgers.items()}

    def update_window(self, month: int) -> None:
        """Rung 5's gates over the last 36 months: games, distinct opponents, distinct events (annex T4.6)."""
        self.window = {}
        y = self.pool.year(month)
        for i, h in self.hist.items():
            while h and h[0][0] < month - 36:
                h.popleft()
            if y - self.pool.birth[i] <= 19 and h:
                self.window[i] = (len(h), {o for _, o, _ in h}, {e for _, _, e in h})

    def fed_amounts(self, led: Ledger, month: int) -> dict[int, float]:
        """Rung 7 (annex T4.5): a_f = clip(γ_a · shrink · φ_f, ±a_cap), φ_f = mean(θ̃ − R − B) over the federation's
        members of the anchor cohort (steadily active adults aged 25-45), relative to the anchor, whose own mean is 0
        by construction (annex T2.5): over all its players, a federation's juniors and newly rated players would be
        read as an offset. shrink = n×/(n× + 2000), n× the federation's cross-border games in 36 months."""
        pool, out = self.pool, {}
        cross: dict[int, int] = {}
        for d in self.cross36:
            for f, n in d.items():
                cross[f] = cross.get(f, 0) + n
        mem = led.members(pool)
        for f in range(len(C.FED_SIZES)):
            vals = []
            for i in mem:
                if pool.fed[i] == f:
                    th, _sd = self.theta_tilde(led, i)
                    if th is not None:
                        vals.append(th - led.R[i] - led.B[i])
            if vals:
                nx = cross.get(f, 0)
                out[f] = fed_adjustment(sum(vals) / len(vals), nx / (nx + 2000.0))
        return out

    # ------------------------------------------------------------------ measurements (SPEC-SIM §6)
    def fed_offsets(self) -> dict[str, list[float]]:
        pool, out = self.pool, {}
        for name, led in self.ledgers.items():
            per = [[0, 0.0] for _ in C.FED_SIZES]
            for i in range(pool.n):
                if pool.alive[i] and led.rated[i]:
                    e = led.R[i] - to_pub(pool.theta[i])
                    per[pool.fed[i]][0] += 1
                    per[pool.fed[i]][1] += e
            tot = sum(p[1] for p in per) / max(1, sum(p[0] for p in per))
            out[name] = [round(p[1] / p[0] - tot, 1) if p[0] else None for p in per]
        return out

    def measure(self, month: int) -> None:
        pool, proxy = self.pool, self.proxy
        k = month - self.adopt
        last24 = month >= self.end - 24
        act_adult = [i for i in range(pool.n) if pool.alive[i] and 25 <= pool.age(i, month) <= 45
                     and month - pool.last_game[i] <= 11]
        n_true_2600 = sum(1 for i in range(pool.n) if pool.alive[i] and month - pool.last_game[i] <= 11
                          and to_pub(pool.theta[i]) >= 2600)
        for name, led in self.ledgers.items():
            s = self.series.setdefault(name, {})
            lvl = level_of(led, pool)
            lvl = 0.0 if lvl is None else lvl
            g = anchor_gap(led, pool, proxy, self.c_ref)
            s.setdefault("level", []).append(round(lvl, 2))
            s.setdefault("d_t", []).append(round(g[0], 2) if g else None)
            s.setdefault("a_t", []).append(led.a_t)
            adults = [i for i in act_adult if led.rated[i]]
            rr = [led.R[i] for i in adults]
            tt = [to_pub(pool.theta[i]) for i in adults]
            ss = [proxy.m[i] for i in adults if proxy.m[i] is not None]
            vv = [proxy.v[i] for i in adults if proxy.m[i] is not None]
            s.setdefault("spread_true", []).append(round(sd(rr) / sd(tt), 4) if len(rr) > 2 else None)
            den = math.sqrt(sd(ss) ** 2 + sum(vv) / len(vv)) if len(ss) > 2 else 0.0
            s.setdefault("spread_r1", []).append(round(sd(rr) / den, 4) if den else None)
            s.setdefault("n_2600_pub", []).append(sum(1 for i in range(pool.n) if pool.alive[i] and led.rated[i]
                                                      and month - led.last_rated[i] <= 11 and led.R[i] >= 2600))
            s.setdefault("n_2600_true", []).append(n_true_2600)
            if k % 12 == 11:
                alive_top = [i for i in self.top_cohort if pool.alive[i] and led.rated[i]]
                s.setdefault("top_change", []).append(round(sum(led.R[i] - self.snap_start[name][i] for i in alive_top)
                                                            / max(1, len(alive_top)), 2))
                s.setdefault("top_true_change", []).append(round(sum(to_pub(pool.theta[i]) - self.theta_start[i]
                                                                     for i in alive_top) / max(1, len(alive_top)), 2))
            # newcomer convergence and error by band
            acc = self.out.setdefault("err", {}).setdefault(name, {})
            for i in range(pool.n):
                if not (pool.alive[i] and led.rated[i]):
                    continue
                th = to_pub(pool.theta[i])
                e_raw = led.R[i] - th
                e = e_raw - lvl
                if led.first_rated[i] >= self.adopt and abs(e) >= 50:
                    led.last_bad[i] = led.games_since_first[i]
                if last24 and month - led.last_rated[i] <= 11:
                    band = next(lbl for lo, hi, lbl in TRUE_BANDS if lo <= th < hi)
                    age = pool.age(i, month)
                    grp = next(lbl for lo, hi, lbl in AGE_GROUPS if lo <= age <= hi)
                    for key in ("band|" + band, "age|" + grp, "all"):
                        a = acc.setdefault(key, [0, 0.0, 0.0, 0.0])
                        a[0] += 1
                        a[1] += e_raw
                        a[2] += e
                        a[3] += e * e

    def finish(self) -> dict:
        pool, out = self.pool, self.out
        out["series"] = self.series
        out["fed_offsets_end"] = self.fed_offsets()
        out["junior_drain"] = {n: led.jd for n, led in self.ledgers.items()}
        out["ledger_lines"] = {n: led.ledger_lines for n, led in self.ledgers.items()}
        conv = {}
        for name, led in self.ledgers.items():
            vals = sorted(led.last_bad[i] for i in range(pool.n)
                          if led.first_rated[i] >= self.adopt and led.first_rated[i] <= self.end - 24 and pool.alive[i])
            conv[name] = {"n": len(vals), "q1": vals[len(vals) // 4] if vals else None,
                          "median": vals[len(vals) // 2] if vals else None, "q3": vals[3 * len(vals) // 4] if vals else None}
        out["newcomer_n50"] = conv
        out["pool"] = {"players_end": sum(pool.alive), "ever": pool.n,
                       "active_end": self.active(self.end - 1)}
        if self.cfg.adversaries:
            out["adversaries"] = self.adversary_results()
        return out

    def adversary_results(self) -> dict:
        pool, res = self.pool, {}
        for name, led in self.ledgers.items():
            r = {}
            for grp in ("farmer", "farmer_control", "sandbagger", "sandbagger_control"):
                ids = [i for i in self.agents.get(grp, []) if led.rated[i]]
                dr = [led.R[i] - self.agent_start[name][i] - (to_pub(pool.theta[i]) - self.agent_theta_start[i]) for i in ids]
                dg = [led.gcount[i] - self.agent_games_start[name][i] for i in ids]
                r[grp] = {"n": len(ids), "excess_change": round(sum(dr) / max(1, len(ids)), 2),
                          "games": round(sum(dg) / max(1, len(ids)), 1),
                          "per_game": round(sum(dr) / max(1, sum(dg)), 4)}
            r["collusion"] = {"arranged_games": led.created_arranged[0],
                              "created_per_game": round(led.created_arranged[1] / max(1, led.created_arranged[0]), 3)}
            back = [st for st in self.protect.values() if "err_back12" in st]
            r["protector"] = {"returned_and_followed_12_months": len(back),
                              "err_at_stop": round(sum(st["err_stop"][name] for st in back) / max(1, len(back)), 1),
                              "err_at_return": round(sum(st["err_back"][name] for st in back) / max(1, len(back)), 1),
                              "err_12_months_after_return": round(sum(st["err_back12"][name] for st in back) / max(1, len(back)), 1)}
            r["farming_advantage_per_game"] = round(r["farmer"]["per_game"] - r["farmer_control"]["per_game"], 4)
            r["checkpoints"] = self.out.get("checkpoints", {}).get(name, {})
            res[name] = r
        return res


def level_of(led: Ledger, pool) -> float | None:
    """The level: the anchor panel's mean R − θᴾ on the published scale, chain-linked across the January re-basings."""
    mem = led.members(pool)
    if not mem:
        return None
    return sum(led.R[i] - to_pub(pool.theta[i]) for i in mem) / len(mem) + led.level_link


def run(cfg: C.Config) -> dict:
    sim = Sim(cfg)
    sim.start()
    for month in range(sim.end):
        sim.month(month)
    return sim.finish()
