"""FIDE's monthly lists as a panel of per-month arrays (needs data/, never committed).

A module, not a script: analysis scripts import it (registered under "modules"
in analysis/outputs.json). It reads data/interim/fide/<tc>/YYYY-MM.tsv, written
by tools/data/convert_fide_lists.py, into arrays indexed by player, one array
per list, so that a cohort over many lists is a loop over integers. FIDE's lists
are analysed and never redistributed [V 3]: nothing here writes player data.

Fields per list t (index into Panel.periods) and player i:
  rating[t][i]   published rating, 0 if not rated on list t
  games[t][i]    rated games in the period ending at list t ("Gms")
  k[t][i]        published K (255 if blank)
  inactive[t][i] 1 if the list flags the player inactive ("i" in Flag)
  fed[t][i]      index into Panel.feds of the federation on list t (0 = none)
Per player: birth (latest non-zero year of birth on any list), first (index of
the first list on which the player is rated, -1 if never).

The April 2026 list event (D-0008, R11): batch_r11() returns the IDs whose first
rated appearance since February 2015 is the March 2026 list and which are absent
from the April 2026 list; cohort analyses exclude them.

Python standard library only.
"""
from __future__ import annotations

from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def shift(period: str, months: int) -> str:
    y, m = map(int, period.split("-"))
    m0 = y * 12 + (m - 1) + months
    return f"{m0 // 12:04d}-{m0 % 12 + 1:02d}"


class Panel:
    def __init__(self, tc: str, periods: list[str]):
        self.tc = tc
        self.periods = periods
        self.pos = {p: t for t, p in enumerate(periods)}
        self.index: dict[str, int] = {}
        self.ids: list[str] = []
        self.feds: list[str] = [""]
        self.rating: list[array] = []
        self.games: list[array] = []
        self.k: list[bytearray] = []
        self.inactive: list[bytearray] = []
        self.fed: list[bytearray] = []
        self.birth = array("H")
        self.first = array("h")

    @property
    def n(self) -> int:
        return len(self.ids)

    def window_games(self, t: int, length: int = 12) -> array:
        """Games on lists t-length+1 .. t, per player (lists before the first are counted as 0)."""
        out = array("l", bytes(8 * self.n))
        for u in range(max(0, t - length + 1), t + 1):
            g = self.games[u]
            for i in range(self.n):
                v = g[i]
                if v:
                    out[i] += v
        return out

    def age(self, i: int, year: int) -> int | None:
        b = self.birth[i]
        return year - b if b else None


def load_panel(tc: str, first: str | None = None, last: str | None = None) -> Panel:
    """Every list of one time control between first and last (inclusive), in month order."""
    files = sorted((ROOT / "data" / "interim" / "fide" / tc).glob("*.tsv"))
    files = [f for f in files if (first is None or f.stem >= first) and (last is None or f.stem <= last)]
    pan = Panel(tc, [f.stem for f in files])
    for f in files:                                       # pass 1: every ID rated on some list
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, _ = line.split("\t", 2)
                if r.isdigit() and pid not in pan.index:
                    pan.index[pid] = len(pan.ids)
                    pan.ids.append(pid)
    n = len(pan.ids)
    fed_ix: dict[str, int] = {"": 0}
    pan.birth = array("H", bytes(2 * n))
    pan.first = array("h", [-1]) * n
    for t, f in enumerate(files):                         # pass 2: one set of arrays per list
        R = array("H", bytes(2 * n))
        G = array("H", bytes(2 * n))
        K = bytearray(n)
        I = bytearray(n)
        F = bytearray(n)
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, g, k, by, _sex, fd, flag, _title = line.rstrip("\n").split("\t")
                if not r.isdigit():
                    continue
                i = pan.index[pid]
                R[i] = int(r)
                if g.isdigit():
                    G[i] = min(int(g), 65535)
                K[i] = min(int(k), 254) if k.isdigit() else 255
                if "i" in flag:
                    I[i] = 1
                fx = fed_ix.get(fd)
                if fx is None:
                    fx = fed_ix[fd] = len(pan.feds)
                    pan.feds.append(fd)
                    if fx > 255:
                        raise ValueError("more than 255 federation codes")
                F[i] = fx
                if by.isdigit() and by != "0":
                    pan.birth[i] = int(by)
                if pan.first[i] < 0:
                    pan.first[i] = t
        pan.rating.append(R)
        pan.games.append(G)
        pan.k.append(K)
        pan.inactive.append(I)
        pan.fed.append(F)
    return pan


def batch_r11(pan: Panel) -> set[int]:
    """D-0008 R11: first rated on the March 2026 list (since February 2015) and absent from the April 2026 list."""
    if "2026-03" not in pan.pos or "2026-04" not in pan.pos or pan.periods[0] > "2015-02":
        return set()
    tm, ta = pan.pos["2026-03"], pan.pos["2026-04"]
    Rm, Ra = pan.rating[tm], pan.rating[ta]
    return {i for i in range(pan.n) if Rm[i] and not Ra[i] and pan.first[i] == tm}
