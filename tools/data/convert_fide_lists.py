#!/usr/bin/env python3
"""Convert downloaded FIDE monthly lists (TXT in zip) into compact per-month TSV files.

Input:  data/raw/fide/<tc>/<tc>_<mon><yy>frl.zip   (tools/data/fetch_fide_lists.py)
Output: data/interim/fide/<tc>/YYYY-MM.tsv with columns
        id, rating, games, k, birth_year, sex, fed, flag, title
Both directories are gitignored: FIDE lists are analysed, never redistributed.

The list files are fixed-width; columns are located from the header line by
name (the "FOA" column first appears in late 2016), so every field runs from its
header's first character to the next header's first character. A birth year of
0000 is written as an empty field. Python standard library only.

Usage: python3 tools/data/convert_fide_lists.py standard
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
FIELDS = ["ID Number", "Name", "Fed", "Sex", "Tit", "WTit", "OTit", "FOA", "RATING", "Gms", "K", "B-day", "Flag"]


def spans(header: str, rating_col: str) -> dict[str, tuple[int, int | None]]:
    starts = []
    for f in FIELDS:
        key = rating_col if f == "RATING" else f
        pos = header.find(key + " ") if key != "Flag" else header.find("Flag")
        if f == "K":
            pos = header.find(" K ") + 1
        if pos >= 0:
            starts.append((pos, f))
    starts.sort()
    out = {}
    for i, (pos, f) in enumerate(starts):
        out[f] = (pos, starts[i + 1][0] if i + 1 < len(starts) else None)
    return out


def convert(tc: str) -> None:
    src = ROOT / "data" / "raw" / "fide" / tc
    dst = ROOT / "data" / "interim" / "fide" / tc
    dst.mkdir(parents=True, exist_ok=True)
    for z in sorted(src.glob(f"{tc}_*frl.zip")):
        tag = z.name[len(tc) + 1:len(tc) + 6]          # e.g. oct26
        mon, yy = tag[:3], tag[3:5]
        period = f"20{yy}-{MONTHS.index(mon) + 1:02d}"
        out = dst / f"{period}.tsv"
        if out.exists() and out.stat().st_mtime >= z.stat().st_mtime:
            continue
        with zipfile.ZipFile(z) as zf:
            raw = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
        sp = spans(raw[0], tag.upper())

        def get(line: str, f: str) -> str:
            if f not in sp:
                return ""
            a, b = sp[f]
            return line[a:b].strip()

        rows = ["id\trating\tgames\tk\tbirth_year\tsex\tfed\tflag\ttitle"]
        for line in raw[1:]:
            pid = get(line, "ID Number")
            if not pid.isdigit():
                continue
            by = get(line, "B-day")
            rows.append("\t".join([pid, get(line, "RATING"), get(line, "Gms"), get(line, "K"),
                                   "" if by in ("", "0000") else by, get(line, "Sex"), get(line, "Fed"),
                                   get(line, "Flag"), get(line, "Tit")]))
        out.write_text("\n".join(rows) + "\n")
        print(f"{period}: {len(rows) - 1} players", flush=True)


if __name__ == "__main__":
    convert(sys.argv[1])
