"""Session ELO-D2's shared reading of FIDE's per-player calculation pages: a module of the club-level extractions, not a
script (docs/specs/SPEC-SOURCING_v1_1.md).

- **The parser** is E17's (analysis/e17_top100_extract.py, parse_page), extended as SPEC-SOURCING v1.1 §4 asks: it reads
  a tournament whose player FIDE prints with Ro 0 and without K (the pilot's seven pages that E17's parser rejects), and a
  game row printed without a colour mark (one row of the pilot), each counted apart. A game row is a row of the
  tournament's table with ten cells whose sixth is a score (1.00, 0.50, 0.00) and seventh the games, 1; its colour is
  White's or Black's mark when FIDE prints one, else none. The tournament's summary is read by the labels of its
  header row, which differ between the two layouts FIDE prints. On every page E17's parser reads, this parser gives the
  same tournaments and the same marked games (tests/test_club.py).
- **The opponent** is identified on FIDE's list in force at the tournament's start, as E17 and E21 do, but by name and
  federation with the rating FIDE prints within 50 points (beyond the cap on the same side for a row FIDE marks under
  the 400-point rule), the nearest if several, else on the lists up to three months either side; the pilot showed that
  the ratings FIDE prints on its pages today often differ by a few points from the lists as published (decided after
  seeing the pilot; E21).
- **Groups**: juniors as E6 defines them (list year minus year of birth at most 19; annex T2.2: a player without a year
  of birth counts as an adult); newcomers first rated on a list from January 2023.
Python standard library only.
"""
from __future__ import annotations

import re
import sys
import zipfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _sub in ("analysis", "tools", "tools/data", "src"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))
import convert_fide_lists as cfl  # noqa: E402  (the lists' fixed-width columns, for names)
import e17_top100_extract as ex  # noqa: E402  (FIDE's page cells and the name key, unchanged)
import fetch_sourcing as fs  # noqa: E402  (the frame, strata and cache: one rule for fetch and analysis)

RAW_LISTS = ROOT / "data" / "raw" / "fide" / "standard"
SCORE = {"1.00": Decimal(1), "0.50": Decimal("0.5"), "0.00": Decimal(0)}
TOLERANCE = 50                   # points between the printed rating and the list's (decided after seeing the pilot)
NEARBY = (-1, 1, -2, 2, -3, 3)   # the lists tried, in this order, when the list in force has no such name
AGE_BANDS = ((0, 11, "<12"), (12, 15, "12-15"), (16, 19, "16-19"), (20, 24, "20-24"), (25, 45, "25-45"),
             (46, 60, "46-60"), (61, 200, ">60"))


def age_band(age: int) -> str:
    return next(lab for lo, hi, lab in AGE_BANDS if lo <= age <= hi)


def is_junior(birth_year: int | None, year: int = fs.CLUB_YEAR) -> bool:
    """E6: a junior is at most 19, list year minus year of birth; no year of birth counts as an adult."""
    return bool(birth_year) and year - birth_year <= fs.CLUB_JUNIOR_MAX_AGE


# ------------------------------------------------------------------ the page
def _summary(header: list[str], row: list[str]) -> dict:
    """A tournament's summary row, read by the labels of the header row above it."""
    at = {lab: i for i, lab in enumerate(header) if lab}
    k = row[at["K"]] if "K" in at else ""
    kc = row[at["K*chg"]] if "K*chg" in at else ""
    return {"rc": int(row[at["Rc"]]), "ro": int(row[at["Ro"]]), "w": Decimal(row[at["w"]]), "n": int(row[at["n"]]),
            "chg": Decimal(row[at["chg"]]), "k": int(k) if k else None, "k_chg": Decimal(kc) if kc else None,
            "rp": int(row[at["Rp"]]) if "Rp" in at and row[at["Rp"]] else None}


def parse_page_club(text: str) -> dict:
    """FIDE's calculation page, per tournament its fields and games (the opponent's name kept for identification only):
    E17's reading, with the tournaments printed without K and the game rows printed without a colour mark."""
    total = re.search(r"Total change:&nbsp;<b>([^<]*)</b>", text)
    out = []
    for b in re.split(r'<div class="rtng_line01"><a href=/report\.phtml\?event=', text)[1:]:
        event = int(re.match(r"(\d+)", b).group(1))
        dates = re.findall(r'<span class="dates_span">([0-9-]+)</span>', b)
        header, summary, games = None, None, []
        for r in re.findall(r"(<tr[^>]*>.*?</tr>)", b, re.S):
            c = ex.cells(r)
            if "bgcolor=#b7b7b7" in r and len(c) >= 10:
                header = c
            elif "bgcolor=#e6e6e6" in r and len(c) >= 10:
                summary = _summary(header or ["Rc", "Ro", "", "", "", "w", "n", "chg", "K", "K*chg"], c)
            elif len(c) >= 10 and c[5] in SCORE and c[6] == "1" and re.fullmatch(r"\d+\s*\*?", c[3].strip()):
                mark = "white" if "white_note" in r else "black" if "black_note" in r else None
                games.append({"mark": mark, "name": c[0], "title": c[1],
                              "rating": int(c[3].replace("*", "").strip()), "capped": "*" in c[3], "fed": c[4],
                              "score": SCORE[c[5]], "chg": Decimal(c[7]), "k": int(c[8]) if c[8] else None,
                              "k_chg": Decimal(c[9]) if c[9] else None})
        if summary is None:
            raise ValueError(f"event {event}: no summary row")
        out.append({"event": event, "start": dates[0] if dates else None, "end": dates[1] if len(dates) > 1 else None,
                    **summary, "unrated": summary["ro"] == 0 or summary["k"] is None, "games": games})
    return {"total": Decimal(total.group(1).strip()) if total and total.group(1).strip() else None, "tournaments": out}


# ------------------------------------------------------------------ the lists
def read_lists(months: list[str], want: set[str] | None = None) -> dict[str, dict]:
    """FIDE ID -> (rating, games, K, year of birth or None, federation, flag) on each converted standard list."""
    out = {}
    for m in months:
        d = {}
        path = fs.LISTS / f"{m}.tsv"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            next(fh)
            for line in fh:
                pid, r, g, k, by, _sex, fed, flag, _title = line.rstrip("\n").split("\t")
                if r.isdigit() and (want is None or pid in want):
                    d[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0,
                              int(by) if by.isdigit() and int(by) > 1900 else None, fed, flag)
        out[m] = d
    return out


def names_index(months: list[str], keys: set[str]) -> dict[str, dict[str, list[tuple]]]:
    """Per list: name key -> [(FIDE ID, federation, rating)] for the wanted keys (E21's index, every list asked)."""
    out = {}
    for m in months:
        ratings = {pid: v[0] for pid, v in read_lists([m]).get(m, {}).items()}
        tag = f"{cfl.MONTHS[int(m[5:]) - 1]}{m[2:4]}"
        z = RAW_LISTS / f"standard_{tag}frl.zip"
        if not z.exists():
            continue
        with zipfile.ZipFile(z) as zf:
            raw = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
        sp = cfl.spans(raw[0], tag.upper())
        (ia, ib), (na, nb), (fa, fb) = sp["ID Number"], sp["Name"], sp["Fed"]
        idx: dict[str, list] = defaultdict(list)
        memo: dict[str, str] = {}
        for line in raw[1:]:
            pid = line[ia:ib].strip()
            if pid not in ratings:
                continue
            name = line[na:nb].strip()
            k = memo.get(name)
            if k is None:
                k = memo[name] = ex.norm(name)
            if k in keys:
                idx[k].append((pid, line[fa:fb].strip(), ratings[pid]))
        out[m] = idx
    return out


def list_in_force(start: str | None, period: str) -> str:
    """As E17 and E21: the list in force at the tournament's start, at most the list before the one that rates it."""
    prev = fs.month_add(period, -1)
    return prev if not start else min(start[:7], prev)


def lists_to_try(m0: str) -> list[str]:
    return [m0] + [fs.month_add(m0, d) for d in NEARBY]


def resolve(g: dict, ro: int, m0: str, index: dict) -> tuple[str | None, str]:
    """The opponent's FIDE ID and how it was found: on the list in force (or the nearest list that has the name), the
    one player of the printed name key, with the printed federation if any has it, whose rating lies within TOLERANCE
    of the printed one (or beyond it on the same side, for a row FIDE marks under the 400-point rule); the nearest if
    several and strictly nearest; else none."""
    k = ex.norm(g["name"])
    for m in lists_to_try(m0):
        cands = index.get(m, {}).get(k, [])
        if not cands:
            continue
        for pool in ([x for x in cands if x[1] == g["fed"]], cands):
            if not pool:
                continue
            if g["capped"]:
                ok = [x for x in pool if ((x[2] < g["rating"]) if g["rating"] < ro else (x[2] > g["rating"]))]
            else:
                ok = [x for x in pool if abs(x[2] - g["rating"]) <= TOLERANCE]
            ids = {x[0] for x in ok}
            if len(ids) == 1:
                return next(iter(ids)), "list in force" if m == m0 else "a nearby list"
            if len(ids) > 1:
                best = sorted(ok, key=lambda x: (abs(x[2] - g["rating"]), x[0]))
                if abs(best[0][2] - g["rating"]) < abs(best[1][2] - g["rating"]):
                    return best[0][0], "list in force" if m == m0 else "a nearby list"
                return None, "several"
        return None, "no rating within the tolerance"
    return None, "name not on the lists"


def wanted_keys(pages: dict) -> dict[str, set]:
    """The name keys each list must index for the pages' opponents."""
    need: dict[str, set] = defaultdict(set)
    for (_pid, period), pg in pages.items():
        for t in pg["tournaments"]:
            m0 = list_in_force(t["start"], period)
            keys = {ex.norm(g["name"]) for g in t["games"]}
            for m in lists_to_try(m0):
                need[m] |= keys
    return need


def resolve_all(pages: dict) -> tuple[dict, dict]:
    """Every game row's opponent: {(page key, tournament, game): FIDE ID or None} and how each was found."""
    need = wanted_keys(pages)
    index = names_index(sorted(need), set().union(*need.values()) if need else set())
    ids, how = {}, defaultdict(int)
    for key, pg in pages.items():
        for ti, t in enumerate(pg["tournaments"]):
            m0 = list_in_force(t["start"], key[1])
            for gi, g in enumerate(t["games"]):
                oid, why = resolve(g, t["ro"], m0, index)
                ids[(key, ti, gi)] = oid
                how[why if oid is None else f"identified on {why}"] += 1
    return ids, dict(how)


def births_of(ids: set[str], months: list[str]) -> dict[str, int]:
    """Year of birth of each wanted player: from the first of `months` that carries one."""
    out: dict[str, int] = {}
    for m in months:
        for pid, v in read_lists([m], ids - set(out)).get(m, {}).items():
            if v[3]:
                out[pid] = v[3]
    return out


def months_after(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])
