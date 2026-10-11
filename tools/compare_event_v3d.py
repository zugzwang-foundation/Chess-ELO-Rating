#!/usr/bin/env python3
"""Freeze 3d (docs/decisions/D-0016_rulings-on-elo-8-questions.md; ELO-9, Phase 0): every log-loss line of the
pre-registered forecast test is read with the crossed interval over players (ruling R66), fixed before any result is
read.

D-0015 (Freeze 3c) made the pooled Brier difference the primary endpoint, read with its interval over games, and added a
crossed interval over players for the measures R54 names. R66 confirms the primary endpoint and orders every log-loss
line to be read with the crossed interval (games × players): for the log-loss, which is skewed, the interval over games
covered the true mean in 0.83 of the review's simulated events and the crossed interval in 0.94
(analysis/OUTPUT_ELO8_review.md). Freeze 3c prints the crossed interval for R54's measures only; this file adds it, on
top of tools/compare_event_v3c.py (Freeze 3c, unchanged), for the two log-loss lines that lack it:
- **the log-loss with one draw model** (D-0015's secondary line): (a)'s mean with its expectation split by (b′)'s draw
  probability, and the difference (b′) − (a);
- **rounds 3 to 11 only** (D-0015's secondary line): the log-loss difference (b′) − (a).
The crossed bootstrap is Freeze 3c's own (tools/compare_event_v3c.py, `crossed`): within each event the players are
drawn with replacement and each game is weighted by the product of its two players' multiplicities; 2,000 resamples,
seed 20261009. Its draws do not depend on the measures, so the intervals it gives here for R54's measures equal Freeze
3c's. No result enters anything until both events are complete. Python standard library only.

Usage:
  python3 tools/compare_event_v3d.py tools/events/us_championship_2026.json tools/events/us_womens_championship_2026.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import compare_event_v3a as v3a  # noqa: E402  (Freeze 3a's tool, unchanged: the completion rule)
import compare_event_v3b as v3b  # noqa: E402  (Freeze 3b's tool, unchanged)
import compare_event_v3c as v3c  # noqa: E402  (Freeze 3c's tool, unchanged)

LL_KEYS = ("ll_a", "ll_bp", "ll_d")                  # R54's log-loss measures (Freeze 3c prints their crossed intervals)
SHARED_KEYS = ("ll_a_shared", "ll_d_shared")         # the log-loss with one draw model
R3_KEYS = ("ll_d",)                                  # rounds 3 to 11: the log-loss difference


def log_loss_lines(events: list[list[v3c.Game]]) -> dict:
    """The crossed interval over players of every log-loss line, for the given events (pooled when two): R54's means
    and difference, the one-draw-model mean and difference, and the rounds 3–11 difference."""
    events = [ev for ev in events if ev]
    if not events:
        return {}
    out = {"all": v3c.crossed(events, LL_KEYS + SHARED_KEYS)}
    late = [[g for g in ev if g.round >= v3c.FIRST_ROUND_AFTER] for ev in events]
    late = [ev for ev in late if ev]
    if late:
        out["rounds_3_11"] = v3c.crossed(late, R3_KEYS)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="The crossed interval of every log-loss line (D-0016, R66).")
    ap.add_argument("events", nargs="+")
    args = ap.parse_args()
    rates = v3b.load_draw_rates()
    evs = []
    for path in args.events:
        event, r2, _v1, _r5, _p = v3b.load(path)
        if not v3a.complete(event):
            print(path, "incomplete: the reading waits for the event's end")
            return 0
        evs.append(v3c.games(event, r2, rates))
    print(log_loss_lines(evs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
