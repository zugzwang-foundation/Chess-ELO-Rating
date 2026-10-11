#!/usr/bin/env python3
"""Convert FIDE's open top-100 lists of July 2000 to December 2019, as the Internet Archive keeps FIDE's top-list archive
(ratings.fide.com/toparc.phtml, no longer served by FIDE; docs/research/DATA-PROBE_greats.md §2.2), into per-list TSV
files with each player's FIDE ID (session ELO-9; SPEC-GREATS §2).

Input:  the archived pages fetched once by tools/data/fetch_probe.py (data/raw/probe/toparc_cod<N>.html, and the four
        pages the probe fetched under other keys); FIDE's full lists of the same dates (data/interim/fide_old/standard/,
        data/raw/fide/standard/ for the names from February 2015) and OlimpBase's lists of 2000 (data/interim/olimpbase/)
Output: data/interim/fide_toparc/YYYY-MM.tsv, columns rank, id, name, fed, rating, games
All gitignored: FIDE's lists are analysed, never redistributed.

A page is FIDE's open list of a month when its heading reads "Top 100 Players <Month> <Year>"; the rank, name, title,
federation, rating and games are read from its table as FIDE printed them. The FIDE ID is the one the full list of the
same date gives the same name and federation (one candidate), else the same name alone (one candidate), else none.
Python standard library only.

Usage: python3 tools/data/convert_fide_toparc.py
"""
from __future__ import annotations

import csv
import gzip
import html
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import convert_fide_lists as cfl  # noqa: E402  (today's list layout)

PROBE = ROOT / "data" / "raw" / "probe"
OLD = ROOT / "data" / "interim" / "fide_old" / "standard"
RAW_NEW = ROOT / "data" / "raw" / "fide" / "standard"
OB = ROOT / "data" / "interim" / "olimpbase"
DST = ROOT / "data" / "interim" / "fide_toparc"
EXTRA = {1: "wayback_toparc_cod1_2008", 93: "wayback_toparc_cod93", 101: "wayback_toparc_cod101",
         537: "wayback_toparc_cod537"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")


def page(path: Path) -> str:
    b = path.read_bytes()
    return (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("latin-1")


def top_list(s: str) -> tuple[str, list[list[str]]] | None:
    m = re.search(r"Top 100 Players (" + "|".join(MONTHS) + r") (\d{4})", s)
    if not m:
        return None
    period = f"{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}"
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S | re.I):
        c = [html.unescape(re.sub(r"<[^>]+>", "", x)).replace("\xa0", " ").strip()
             for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        if len(c) >= 6 and c[0].isdigit() and c[4].isdigit():
            rows.append(c[:6])
    return period, rows


def full_list(period: str) -> list[tuple[str, str, str]]:
    """(id, name, federation) of every player on FIDE's full list of the date (OlimpBase's for 2000)."""
    if period < "2001-01":
        path = OB / f"{period}.tsv"
    elif period <= "2015-01":
        path = OLD / f"{period}.tsv"
    else:
        tag = f"{MONTHS[int(period[5:]) - 1][:3].lower()}{period[2:4]}"
        with zipfile.ZipFile(RAW_NEW / f"standard_{tag}frl.zip") as zf:
            lines = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
        sp = cfl.spans(lines[0], tag.upper())

        def get(line: str, f: str) -> str:
            a, b = sp[f]
            return line[a:b].strip()
        return [(get(x, "ID Number"), get(x, "Name"), get(x, "Fed")) for x in lines[1:] if get(x, "ID Number").isdigit()]
    with path.open(encoding="utf-8") as fh:
        return [(r["id"], r["name"], r["fed"]) for r in csv.DictReader(fh, delimiter="\t")]


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    pages = {n: PROBE / f"toparc_cod{n}.html" for n in range(1, 574, 4)}
    pages.update({n: PROBE / f"{k}.html" for n, k in EXTRA.items()})
    for n, path in sorted(pages.items()):
        if not path.exists():
            print(f"cod {n}: not fetched", flush=True)
            continue
        t = top_list(page(path))
        if t is None:
            print(f"cod {n}: not an open top list", flush=True)
            continue
        period, rows = t
        by_nf, by_n = defaultdict(set), defaultdict(set)
        for pid, name, fed in full_list(period):
            by_nf[(name, fed)].add(pid)
            by_n[name].add(pid)
        out = ["rank\tid\tname\tfed\trating\tgames"]
        for rank, name, _title, fed, rating, games in rows:
            ids = by_nf.get((name, fed)) or by_n.get(name) or set()
            out.append("\t".join([rank, next(iter(ids)) if len(ids) == 1 else "", name, fed, rating, games]))
        (DST / f"{period}.tsv").write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"cod {n}: {period}, {len(rows)} players, {sum(1 for x in out[1:] if x.split(chr(9))[1])} with an ID",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
