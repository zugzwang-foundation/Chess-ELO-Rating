"""Events and pairings (docs/specs/SPEC-SIM_v1_0.md §3.4): a simplified Dutch Swiss system and round-robins with
Berger-style colours. Ratings for seeding come from Layer 0's list (the official list). Standard library only."""
from __future__ import annotations

import random


def round_robin(players: list[int]) -> list[list[tuple[int, int]]]:
    """Circle method for an even field (a dummy for an odd one, its games dropped); colours alternate by round."""
    ps = list(players)
    if len(ps) % 2:
        ps.append(-1)
    n = len(ps)
    rounds = []
    for r in range(n - 1):
        pairs = []
        for k in range(n // 2):
            a, b = ps[k], ps[n - 1 - k]
            if a < 0 or b < 0:
                continue
            if (k == 0 and r % 2 == 1) or (k > 0 and k % 2 == 1):
                a, b = b, a
            pairs.append((a, b))
        rounds.append(pairs)
        ps = [ps[0]] + [ps[-1]] + ps[1:-1]
    return rounds


class Swiss:
    """One Swiss event. pair() returns the next round's (White, Black) pairs; record() takes the results."""

    def __init__(self, players: list[int], rating: dict[int, int]):
        self.players = list(players)
        self.rating = rating
        self.score = {p: 0 for p in players}          # half points
        self.colours: dict[int, list[int]] = {p: [] for p in players}
        self.met: dict[int, set] = {p: set() for p in players}
        self.had_bye: set = set()
        self.round = 0

    def _rank(self) -> list[int]:
        return sorted(self.players, key=lambda p: (-self.score[p], -self.rating.get(p, 0), p))

    def _colour(self, a: int, b: int) -> tuple[int, int]:
        """The player with the stronger claim to White gets it (more Blacks so far, then the last colour)."""
        ca, cb = self.colours[a], self.colours[b]
        da, db = sum(ca), sum(cb)                     # +1 White, −1 Black
        if da != db:
            return (a, b) if da < db else (b, a)
        la, lb = (ca[-1] if ca else 0), (cb[-1] if cb else 0)
        if la != lb:
            return (a, b) if la < lb else (b, a)
        return (a, b) if self.round % 2 == 0 else (b, a)

    def pair(self) -> list[tuple[int, int]]:
        self.round += 1
        order = self._rank() if self.round > 1 else sorted(self.players, key=lambda p: (-self.rating.get(p, 0), p))
        if len(order) % 2:
            bye = next((p for p in reversed(order) if p not in self.had_bye), order[-1])
            self.had_bye.add(bye)
            self.score[bye] += 2                      # a bye scores a point and is not a rated game
            order = [p for p in order if p != bye]
        pairs: list[tuple[int, int]] = []
        if self.round == 1:
            h = len(order) // 2
            for k in range(h):
                a, b = order[k], order[k + h]
                pairs.append((a, b) if k % 2 == 0 else (b, a))
        else:
            # greedy Dutch: the highest unpaired player meets the player half its score group below it, else the
            # nearest unmet player in its group or below, else (a repeat being unavoidable) the next player
            left = list(order)
            while left:
                a = left.pop(0)
                same = [x for x in left if self.score[x] == self.score[a]]
                h = (len(same) + 1) // 2 - 1 if same else 0
                cands = same[h:] + same[:h][::-1] + [x for x in left if self.score[x] < self.score[a]]
                cands += [x for x in left if x not in cands]
                b = next((x for x in cands if x not in self.met[a]), cands[0])
                left.remove(b)
                pairs.append(self._colour(a, b))
        for w, b in pairs:
            self.colours[w].append(1)
            self.colours[b].append(-1)
            self.met[w].add(b)
            self.met[b].add(w)
        return pairs

    def record(self, w: int, b: int, s2: int) -> None:
        self.score[w] += s2
        self.score[b] += 2 - s2


def form_events(slots: list[tuple[int, int]], rating: dict[int, int], cfg, rnd: random.Random) -> list[tuple[str, list[int], int]]:
    """Group a month's entries into events. slots: (player, pool key: federation or −1 for international).
    Returns (kind, players, rounds): round-robins of 10 by rating (rr_share of the entries), the rest Swiss events
    of 16 to 64 players with 9, 7 or 5 rounds."""
    pools: dict[int, list[int]] = {}
    for p, key in slots:
        pools.setdefault(key, []).append(p)
    events = []
    for key in sorted(pools):
        ps = pools[key]
        rnd.shuffle(ps)
        n_rr = int(len(ps) * cfg.rr_share) // 10 * 10
        rr, sw = ps[:n_rr], ps[n_rr:]
        rr.sort(key=lambda p: (-rating.get(p, 0), p))
        for k in range(0, len(rr), 10):
            grp = list(dict.fromkeys(rr[k:k + 10]))
            if len(grp) >= 6:
                events.append(("rr", grp, len(grp) - 1 + len(grp) % 2))
            else:
                sw.extend(grp)
        k = 0
        while k < len(sw):
            size = rnd.randint(16, 64)
            grp = sw[k:k + size]
            k += size
            if len(sw) - k < 8:
                grp += sw[k:]
                k = len(sw)
            grp = list(dict.fromkeys(grp))
            if len(grp) < 4:
                continue
            u = rnd.random()
            rounds = 9 if u < 0.70 else 7 if u < 0.85 else 5
            events.append(("swiss", grp, min(rounds, len(grp) - 1)))
    return events
