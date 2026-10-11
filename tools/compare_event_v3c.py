#!/usr/bin/env python3
"""Freeze 3c (docs/decisions/D-0015_forecast-test-reading.md; ELO-8, Phase 6): how the pre-registered forecast test
(R54, D-0014) is read, fixed before any result is read, after the session's review (docs/review/REDTEAM_v1_0.md, ELO-8
addendum: ELO8-STAT-1, ELO8-STAT-2, ELO8-QC-1).

On top of tools/compare_event_v3b.py (Freeze 3b, unchanged), for the counted games of one or both events:
- **the primary endpoint**: the pooled expected-score Brier difference (b′) − (a), with its interval over games (games
  resampled within each event): the Brier score compares the two columns' expectations alone, with no draw model; and
  the sentence the result is read with, fixed here for each outcome;
- **a crossed interval over players**: in a round robin every game belongs to two players, so resampling players and
  counting each game for both (R54's "over players", reported as Freeze 3b computes it) is narrower than the sampling
  variation by construction; the crossed bootstrap draws the players of each event with replacement and weights each
  game by the product of its two players' multiplicities, 2,000 resamples, seed 20261009;
- **two secondary lines, not endpoints**: the log-loss with (a)'s expectation split by (b′)'s own draw probability, so
  that one draw model serves both columns; and every measure on rounds 3 to 11 only, the games played after Freeze 3b
  and this record;
- **what the pairings fix about the test**: if (b′)'s forecasts were exactly right, the expected log-loss advantage of
  (b′) (as frozen, and with one draw model) and the expected Brier advantage, (E_a − E_b′)² a game, assuming every game
  is played; no result enters them.
Python standard library only.

Usage:
  python3 tools/compare_event_v3c.py tools/events/us_championship_2026.json tools/events/us_womens_championship_2026.json
"""
from __future__ import annotations

import argparse
import dataclasses
import math
import random
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event as ce  # noqa: E402  (Freeze 1's tool, unchanged)
import compare_event_v3 as v3  # noqa: E402  (Freeze 3's tool, unchanged)
import compare_event_v3a as v3a  # noqa: E402  (Freeze 3a's tool, unchanged: the completion rule)
import compare_event_v3b as v3b  # noqa: E402  (Freeze 3b's tool, unchanged)
from layer2 import table_v2 as t2  # noqa: E402

SEED, RESAMPLES = v3b.SEED, v3b.RESAMPLES
FIRST_ROUND_AFTER = 3              # rounds 1 and 2 were played before Freeze 3b (D-0014, part A)
PRIMARY = "br_d"
SENTENCES = {
    "below": ("On the 2026 championships the main column's expectations forecast the results better than FIDE's: the "
              "Brier score is lower by {d} a game ({lo} to {hi} over games)."),
    "above": ("On the 2026 championships FIDE's expectations forecast the results better than the main column's: the "
              "Brier score is higher by {d} a game ({lo} to {hi} over games)."),
    "across": ("The 2026 championships cannot tell the two columns' expectations apart: the Brier difference is {d} a "
               "game ({lo} to {hi} over games), an interval that includes zero."),
}


@dataclasses.dataclass(frozen=True)
class Game:
    forecast: v3b.GameForecast
    round: int
    p_a_shared: tuple                # (a)'s expectation split by (b′)'s draw probability

    @property
    def values(self) -> dict[str, float]:
        v = dict(self.forecast.values)
        ll_s = v3b._ll(self.p_a_shared, self.forecast.s)
        v.update({"ll_a_shared": ll_s, "ll_d_shared": v["ll_bp"] - ll_s})
        return v


def games(event: dict, r2: v3.Rung2, rates: dict[int, float]) -> list[Game]:
    """Freeze 3b's forecasts of every counted game, with its round and (a)'s split by (b′)'s draw probability."""
    players = {p["fide_id"]: p for p in event["players"]}
    rounds = [g["round"] for g in event["games"] if g.get("result") in ce.SCORE]
    out = []
    for f, rnd in zip(v3b.game_forecasts(event, r2, rates), rounds):
        rw, rb = players[f.white]["rating"], players[f.black]["rating"]
        mid = t2.band_mid((rw + rb) // 2)
        d = v3b.v2_draw(r2, rw - rb + r2.eta_whole, mid)
        out.append(Game(f, rnd, v3b.three_way(f.e_a, d)))
    return out


def _interval(stats: list[float]) -> tuple[float, float]:
    return v3b._interval(stats)


def crossed(events: list[list[Game]], keys: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """The crossed bootstrap over players: within each event, players drawn with replacement; a game's weight is the
    product of its two players' multiplicities; the statistic is the weighted mean over the events' games."""
    per_event = []
    for ev in events:
        ids = sorted({g.forecast.white for g in ev} | {g.forecast.black for g in ev})
        per_event.append((ids, [(g.forecast.white, g.forecast.black, g.values) for g in ev]))
    rnd = random.Random(SEED)
    stats = {k: [] for k in keys}
    done = 0
    while done < RESAMPLES:
        num = {k: 0.0 for k in keys}
        den = 0.0
        for ids, rows in per_event:
            mult: dict[int, int] = {}
            for _ in ids:
                p = ids[rnd.randrange(len(ids))]
                mult[p] = mult.get(p, 0) + 1
            for w, b, v in rows:
                wt = mult.get(w, 0) * mult.get(b, 0)
                if wt:
                    den += wt
                    for k in keys:
                        num[k] += wt * v[k]
        if not den:                      # every draw the same player: no game has both players; drawn again
            continue
        for k in keys:
            stats[k].append(num[k] / den)
        done += 1
    return {k: _interval(stats[k]) for k in keys}


def reading(events: list[list[Game]]) -> dict:
    """D-0015's measures for the given events (pooled when two): Freeze 3b's means and intervals, the crossed players
    interval, the secondary lines, and the primary endpoint with its sentence."""
    fz = [[g.forecast for g in ev] for ev in events]
    base = v3b.forecast_test(fz)
    if base is None:
        return {}
    keys = v3b.MEASURES
    out = {"games": base["games"], "players": base["players"], "measures": base,
           "crossed": crossed(events, keys)}
    shared = [[g for g in ev] for ev in events]
    out["shared"] = _means_with_games_interval(shared, ("ll_a_shared", "ll_d_shared"))
    late = [[g for g in ev if g.round >= FIRST_ROUND_AFTER] for ev in events]
    if any(late):
        lb = v3b.forecast_test([[g.forecast for g in ev] for ev in late])
        out["rounds_3_11"] = {"games": lb["games"], "ll_d": lb["ll_d"], "br_d": lb["br_d"]}
    mean, (lo, hi), _p = base[PRIMARY]
    side = "below" if hi < 0 else "above" if lo > 0 else "across"
    out["primary"] = {"mean": mean, "lo": lo, "hi": hi, "side": side,
                      "sentence": SENTENCES[side].format(d=f"{abs(mean):.4f}" if side != "across" else f"{mean:+.4f}",
                                                         lo=f"{lo:+.4f}", hi=f"{hi:+.4f}")}
    return out


def _means_with_games_interval(events: list[list[Game]], keys: tuple[str, ...]) -> dict:
    rows = [[g.values for g in ev] for ev in events]
    allrows = [v for ev in rows for v in ev]
    means = {k: sum(v[k] for v in allrows) / len(allrows) for k in keys}
    rnd = random.Random(SEED)
    boot = {k: [] for k in keys}
    for _ in range(RESAMPLES):
        smp = [ev[rnd.randrange(len(ev))] for ev in rows for _j in range(len(ev))]
        for k in keys:
            boot[k].append(sum(v[k] for v in smp) / len(smp))
    return {k: (means[k], _interval(boot[k])) for k in keys}


def expected_if_bp_right(event: dict, r2: v3.Rung2, rates: dict[int, float]) -> dict:
    """What the pairings fix about the test: with every game not marked unplayed played and (b′)'s forecasts exactly
    right, the mean expected log-loss advantage of (b′) over (a) as frozen and over (a) split by (b′)'s draw
    probability, and the mean expected Brier advantage, (E_a - E_b′)^2; the mean draw probability of each split."""
    ev = v3b.played_copy(event, "1/2-1/2")
    gs = games(ev, r2, rates)
    if not gs:
        return {}
    kl = kl_s = br = d_a = d_bp = 0.0
    for g in gs:
        pb, pa, ps = g.forecast.p_bp, g.forecast.p_a, g.p_a_shared
        kl += sum(b * math.log(b / a) for b, a in zip(pb, pa))
        kl_s += sum(b * math.log(b / a) for b, a in zip(pb, ps))
        br += (g.forecast.e_a - g.forecast.e_bp) ** 2
        d_a += pa[1]
        d_bp += pb[1]
    n = len(gs)
    return {"games": n, "ll_advantage": kl / n, "ll_advantage_one_draw_model": kl_s / n, "brier_advantage": br / n,
            "draw_a": d_a / n, "draw_bp": d_bp / n}


def main() -> int:
    ap = argparse.ArgumentParser(description="The forecast test's reading (D-0015) for one or two events.")
    ap.add_argument("events", nargs="+")
    args = ap.parse_args()
    rates = v3b.load_draw_rates()
    evs = []
    for path in args.events:
        event, r2, _v1, _r5, _p = v3b.load(path)
        print(path, expected_if_bp_right(event, r2, rates))
        if not v3a.complete(event):
            print(path, "incomplete: the reading waits for the event's end")
            return 0
        evs.append(games(event, r2, rates))
    res = reading(evs)
    print(res.get("primary"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
