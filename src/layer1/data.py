"""Layer 1 inputs from the broadcast archive and FIDE's lists (SPEC-L1 §2).

Reads the converted files under data/ (never committed): the broadcast game
headers (data/interim/broadcast/YYYY-MM.tsv, tools/data/convert_broadcasts.py)
and FIDE's monthly lists (data/interim/fide/<tc>/YYYY-MM.tsv,
tools/data/convert_fide_lists.py). The rules for dates, duplicates and time
controls are those of SPEC-TABLE-FIT §1. The federation field is never read
(decision D4). The ELO-4 data cutoff is enforced here (no file later than
2026-09 is opened; games dated after 2026-09-30 are dropped and counted) and
again by the fitter (`layer1.fit.check_cutoff`). Standard library only.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .fit import CUTOFF, Game, month_index
from .model import band_mid

LAST_FILE = "2026-09"
TCS = ("standard", "rapid", "blitz")


@dataclass(frozen=True)
class RawGame:
    day: date
    tour: str
    round_url: str
    game_url: str
    white: str
    black: str
    white_name: str
    black_name: str
    result: str
    time_control: str
    clk_white: str
    clk_black: str


def to_date(d: str) -> date | None:
    """A PGN date "YYYY.MM.DD", or the forms "YYYY-MM-DD" and "DD.MM.YYYY" (SPEC-TABLE-FIT §1)."""
    m = re.fullmatch(r"(\d{4})[.-](\d\d)[.-](\d\d)", d)
    if m:
        y, mo, dd = m.groups()
    else:
        m = re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})", d)
        if not m:
            return None
        dd, mo, y = m.groups()
    try:
        return date(int(y), int(mo), int(dd))
    except ValueError:
        return None


def _parse_tc(tag: str) -> float | None:
    m = re.fullmatch(r"(?:\d+/)?(\d+)(?:\+(\d+))?(?::.*)?", tag.strip())
    if m and int(m.group(1)) >= 60:
        return int(m.group(1)) / 60.0 + (int(m.group(2)) if m.group(2) else 0)
    return None


def _parse_tc_text(tag: str) -> float | None:
    t = tag.lower()
    m = re.fullmatch(r"\s*g/?(\d+)\s*[+;]\s*(?:inc\s*)?(\d+)\s*", t)
    if m:
        return int(m.group(1)) + int(m.group(2))
    m = re.fullmatch(r"\s*(\d+)\s*(?:min|mins|minutes|m|')\s*\+\s*(\d+)\s*(?:s|sec|secs|seconds|\")\b.*", t)
    if m:
        return int(m.group(1)) + int(m.group(2))
    return None


def _by_total(tot: float) -> str | None:
    if tot >= 60:
        return "standard"
    if 10 < tot < 60:
        return "rapid"
    if 3 < tot <= 10:
        return "blitz"
    return None


def classify(tag: str, cw: str, cb: str) -> str | None:
    """Time control of one game: PGN tag, else the first clocks, else free text (SPEC-TABLE-FIT §1)."""
    tot = _parse_tc(tag) if tag else None
    if tot is not None:
        return _by_total(tot)
    clocks = [int(c) for c in (cw, cb) if c.isdigit()]
    if clocks:
        mins = max(clocks) / 60.0
        return "standard" if mins >= 55 else "rapid" if 13 <= mins < 55 else "blitz" if 2.5 < mins <= 10.5 else None
    tot = _parse_tc_text(tag) if tag else None
    return _by_total(tot) if tot is not None else None


def read_broadcasts(root: Path, last_file: str = LAST_FILE, cutoff: date = CUTOFF) -> tuple[list[RawGame], dict]:
    """Every standard-chess game with a result from the converted broadcast files, deduplicated; games dated after
    the cutoff are dropped and counted; a file later than last_file is refused."""
    files = sorted((root / "data" / "interim" / "broadcast").glob("*.tsv"))
    late_files = [f.name for f in files if f.stem > last_file]
    if late_files:
        raise ValueError(f"refusing broadcast files later than the data cutoff ({last_file}): {', '.join(late_files)}")
    games: list[RawGame] = []
    meta = Counter()
    for f in files:
        with f.open() as fh:
            cols = fh.readline().rstrip("\n").split("\t")
            ix = {c: i for i, c in enumerate(cols)}
            for line in fh:
                v = line.rstrip("\n").split("\t")
                meta["read"] += 1
                if v[ix["variant"]] not in ("Standard", "") or v[ix["result"]] not in ("1-0", "0-1", "1/2-1/2"):
                    continue
                d = to_date(v[ix["date"]]) or to_date(v[ix["utc_date"]]) or date(int(f.stem[:4]), int(f.stem[5:7]), 1)
                if d > cutoff:
                    meta["dropped_after_cutoff"] += 1
                    continue
                games.append(RawGame(d, v[ix["tour"]], v[ix["round_url"]], v[ix["game_url"]], v[ix["white_fide_id"]],
                                     v[ix["black_fide_id"]], v[ix["white"]], v[ix["black"]], v[ix["result"]],
                                     v[ix["time_control"]], v[ix["clk_white"]], v[ix["clk_black"]]))
    groups: dict[tuple, dict[str, list[RawGame]]] = {}
    for g in games:
        groups.setdefault((g.day, g.white or g.white_name, g.black or g.black_name, g.result), {}).setdefault(g.tour, []).append(g)
    kept = []
    for key in sorted(groups, key=lambda k: (k[0], k[1], k[2], k[3])):
        tours = groups[key]
        best = min(tours, key=lambda t: (-len(tours[t]), t))
        kept.extend(sorted(tours[best], key=lambda g: (g.round_url, g.game_url)))
    meta["duplicates_removed"] = len(games) - len(kept)
    return kept, dict(meta)


class Lists:
    """Published ratings, games and years of birth from FIDE's lists, for a given set of players (no federation)."""

    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[tuple[str, str], dict[str, tuple[int, int, int]]] = {}
        self.birth: dict[str, int] = {}

    def load(self, tc: str, month: str, ids: set[str] | None) -> dict[str, tuple[int, int, int]]:
        """Rating, games and K of each listed player (in ids, if given) on one list."""
        key = (tc, month)
        if key not in self.cache:
            out: dict[str, tuple[int, int, int]] = {}
            f = self.root / "data" / "interim" / "fide" / tc / f"{month}.tsv"
            if f.exists():
                with f.open() as fh:
                    next(fh)
                    for line in fh:
                        pid, r, g, k, by, _rest = line.split("\t", 5)
                        if not r.isdigit() or (ids is not None and pid not in ids):
                            continue
                        out[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0)
                        if by.isdigit() and by != "0":
                            self.birth[pid] = int(by)
            self.cache[key] = out
        return self.cache[key]

    def rating(self, tc: str, month: str, pid: str) -> int | None:
        v = self.cache.get((tc, month), {}).get(pid)
        return v[0] if v else None

    def games(self, tc: str, month: str, pid: str) -> int:
        v = self.cache.get((tc, month), {}).get(pid)
        return v[1] if v else 0

    def k(self, tc: str, month: str, pid: str) -> int | None:
        v = self.cache.get((tc, month), {}).get(pid)
        return v[2] if v and v[2] else None


def r11_batch(root: Path, tc: str) -> set[str]:
    """D-0008 R11: IDs first rated on the March 2026 list (since February 2015) and absent from the April 2026 list."""
    seen: set[str] = set()
    folder = root / "data" / "interim" / "fide" / tc
    march: set[str] = set()
    april: set[str] = set()
    for f in sorted(folder.glob("*.tsv")):
        if f.stem > "2026-04":
            break
        ids = set()
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, _ = line.split("\t", 2)
                if r.isdigit():
                    ids.add(pid)
        if f.stem == "2026-03":
            march = ids - seen
        if f.stem == "2026-04":
            april = ids
        seen |= ids
    return march - april


def month_label_of(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def build_games(root: Path, first_month: str = "2023-01", last_month: str = "2026-09") -> tuple[list[Game], Lists, dict]:
    """Layer 1's game records (SPEC-L1 §2.1): both FIDE IDs, classified tour, not a duplicate, on or before the cutoff,
    no player of the R11 batch; with the published ratings of the list in force (SPEC-L0 R-11a) for the level."""
    raw, meta0 = read_broadcasts(root)
    meta = Counter(meta0)
    span: dict[str, list[date]] = {}
    votes: dict[str, Counter] = {}
    for g in raw:
        s = span.setdefault(g.tour, [g.day, g.day])
        s[0], s[1] = min(s[0], g.day), max(s[1], g.day)
        c = classify(g.time_control, g.clk_white, g.clk_black)
        if c:
            votes.setdefault(g.tour, Counter())[c] += 1
    tour_tc = {t: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for t, v in votes.items()}
    batch = set().union(*(r11_batch(root, tc) for tc in TCS))
    lists = Lists(root)
    sel = []
    for g in raw:
        m = month_label_of(g.day)
        if not (first_month <= m <= last_month):
            continue
        tc = tour_tc.get(g.tour)
        if not tc or not (g.white.isdigit() and g.black.isdigit()) or g.white == g.black:
            meta["no_tc_or_ids"] += 1
            continue
        if g.white in batch or g.black in batch:
            meta["r11_batch"] += 1
            continue
        s0, s1 = span[g.tour]
        start = s0 if (s1 - s0).days <= 30 else g.day
        sel.append((g, tc, month_label_of(start)))
    ids = {g.white for g, _, _ in sel} | {g.black for g, _, _ in sel}
    for tc in TCS:
        for mm in sorted({lm for _, _, lm in sel}):
            lists.load(tc, mm, ids)
    games = []
    for g, tc, lm in sel:
        rw, rb = lists.rating(tc, lm, g.white), lists.rating(tc, lm, g.black)
        level = (rw + rb) // 2 if rw and rb else rw if rw else rb if rb else 1450
        score = 1.0 if g.result == "1-0" else 0.0 if g.result == "0-1" else 0.5
        games.append(Game(g.day, month_index(g.day.year, g.day.month), TCS.index(tc), int(g.white), int(g.black), score,
                          band_mid(level), g.tour, rw is not None, rb is not None, rw, rb,
                          lists.k(tc, lm, g.white), lists.k(tc, lm, g.black), lm))
    games.sort(key=lambda x: (x.day, x.tour, x.white, x.black))
    meta["games"] = len(games)
    meta["players"] = len(ids)
    meta["r11_batch_ids"] = len(batch)
    return games, lists, dict(meta)


def anchor_panel(root: Path, tc: str, t_ref: str, min_games: int = 10) -> dict[str, int]:
    """SPEC-L1 §3.5: aged 25–45 in t_ref's year, rated on the list of t_ref and 24 months earlier, at least min_games
    rated games in each of the two 12-month periods before t_ref (lists' games fields). Returns ID -> rating at t_ref."""
    y, m = int(t_ref[:4]), int(t_ref[5:7])
    months = [f"{(y * 12 + m - 1 - k) // 12:04d}-{(y * 12 + m - 1 - k) % 12 + 1:02d}" for k in range(24, -1, -1)]
    g1: Counter = Counter()
    g2: Counter = Counter()
    birth: dict[str, int] = {}
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    for k, mm in enumerate(months):
        f = root / "data" / "interim" / "fide" / tc / f"{mm}.tsv"
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, g, _k, by, _rest = line.split("\t", 5)
                if not r.isdigit():
                    continue
                if by.isdigit() and by != "0":
                    birth[pid] = int(by)
                if k == 0:
                    first[pid] = int(r)
                if k == 24:
                    last[pid] = int(r)
                n = int(g) if g.isdigit() else 0
                if 1 <= k <= 12:
                    g1[pid] += n
                elif k >= 13:
                    g2[pid] += n
    return {p: r for p, r in last.items() if p in first and p in birth and 25 <= y - birth[p] <= 45
            and g1[p] >= min_games and g2[p] >= min_games}
