#!/usr/bin/env python3
"""Convert FIDE's standard lists of January 2001 to January 2015 (tools/data/fetch_fide_old_lists.py) into per-list TSV
files, and OlimpBase's transcription of FIDE's lists of July 1971 to October 2001 (fetched once by the data probe) into
the same form (session ELO-9; SPEC-GREATS).

Input:  data/raw/fide_old/standard/YYYY-MM.zip; data/raw/probe/olimpbase_elo1967-2001.zip.html
Output: data/interim/fide_old/standard/YYYY-MM.tsv and data/interim/olimpbase/YYYY-MM.tsv, columns
        id, name, fed, rating, games, flag, title
All gitignored: FIDE's lists are analysed, never redistributed; OlimpBase's are used as its terms allow (free of
charge, citing the source, non-commercial; docs/research/DATA-PROBE_greats.md §3) and likewise never committed.

FIDE's files are fixed-width. From January 2001 to September 2012 their lines share one layout (the ID, the name,
an optional title, the federation, the rating, the games, a birth date and the flag) under headers that change and
do not sit over their fields, and four files have no header at all; such a line is read by its federation code and
rating (`old_row`). From October 2012 the layout is today's ("ID Number Name Fed Sex Tit WTit OTit <monyy> Gms K
B-day Flag"), read by columns, every field running from its header's first character to the next header's. OlimpBase's file is semicolon-separated (name, the name's standard
form, list YYYYMM, FIDE ID, birth date, title, federation, rating, change, games, flag, remark, federation then,
provisional); its standard form of the name is written in the name column, so that one player keeps one name across
lists. Python standard library only.

Usage: python3 tools/data/convert_fide_old_lists.py
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "fide_old" / "standard"
DST = ROOT / "data" / "interim" / "fide_old" / "standard"
OB_SRC = ROOT / "data" / "raw" / "probe" / "olimpbase_elo1967-2001.zip.html"
OB_DST = ROOT / "data" / "interim" / "olimpbase"
HEAD = "id\tname\tfed\trating\tgames\tflag\ttitle"
MON = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


TITLE = r"(?:wg|wm|wf|wc|wh|g|m|f|c|h)"
OLD_LINE = re.compile(r"^\s*(\d{1,9})\s+(.+?)\s+(?:(" + TITLE + r")\s+)?([A-Z][A-Za-z]{2})\s+(\d{1,4})(?:\s+(\d+))?(.*)$")
NEW_FIELDS = ("ID Number", "Name", "Fed", "Sex", "Tit", "WTit", "OTit", "FOA", "RATING", "Gms", "K", "B-day", "Flag")


def old_row(line: str) -> list[str] | None:
    """A line of the layouts of 2001 to September 2012: the ID, the name, an optional title, the federation, the
    rating, the games, then the birth date and the flag; the fields are aligned, but not under their headers, and
    some files have no header line, so the line is read by its federation and rating rather than by columns."""
    m = OLD_LINE.match(line)
    if not m:
        return None
    pid, name, title, fed, rating, games, rest = m.groups()
    toks = rest.split()
    flag = toks[-1] if toks and toks[-1] in ("i", "w", "wi") else ""
    return [pid, name.strip(), fed.upper(), rating, games or "", flag, title or ""]


def new_spans(header: str) -> dict[str, tuple[int, int | None]]:
    """The layout from October 2012 (today's): every field from its header's first character to the next header's."""
    st = []
    for f in NEW_FIELDS:
        if f == "RATING":
            m = re.search(r"(?<=\s)[A-Za-z]{3,4}\d\d(?=\s)", header)
            pos = m.start() if m else -1
        elif f == "K":
            pos = header.find(" K ") + 1 if " K " in header else -1
        elif f == "Flag":
            pos = header.find("Flag")
        else:
            pos = header.find(f + " ")
        if pos >= 0:
            st.append((pos, f))
    st.sort()
    return {f: (a, st[i + 1][0] if i + 1 < len(st) else None) for i, (a, f) in enumerate(st)}


def convert_fide() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for z in sorted(SRC.glob("*.zip")):
        period = z.stem
        out = DST / f"{period}.tsv"
        if out.exists() and out.stat().st_mtime >= z.stat().st_mtime:
            continue
        with zipfile.ZipFile(z) as zf:
            lines = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
        rows = [HEAD]
        if lines[0].startswith("ID Number"):
            sp = new_spans(lines[0])

            def get(line: str, f: str) -> str:
                if f not in sp:
                    return ""
                a, b = sp[f]
                return line[a:b].strip()
            for line in lines[1:]:
                pid = get(line, "ID Number")
                if pid.isdigit():
                    rows.append("\t".join([pid, get(line, "Name"), get(line, "Fed"), get(line, "RATING"),
                                           get(line, "Gms"), get(line, "Flag"), get(line, "Tit")]))
        else:
            for line in lines:
                r = old_row(line)
                if r:
                    rows.append("\t".join(r))
        out.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"{period}: {len(rows) - 1} players of {len(lines)} lines", flush=True)


def convert_olimpbase() -> None:
    OB_DST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OB_SRC) as zf:
        lines = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
    by: dict[str, list[str]] = {}
    for line in lines:
        c = line.split(";")
        if len(c) < 15 or not re.fullmatch(r"\d{6}", c[3]):
            continue
        period = f"{c[3][:4]}-{c[3][4:]}"
        by.setdefault(period, []).append("\t".join([c[4].strip(), c[2].strip(), c[7].strip(), c[8].strip(),
                                                    c[10].strip(), c[11].strip(), c[6].strip()]))
    for period, rows in sorted(by.items()):
        (OB_DST / f"{period}.tsv").write_text("\n".join([HEAD] + rows) + "\n", encoding="utf-8")
        print(f"OlimpBase {period}: {len(rows)} players", flush=True)


if __name__ == "__main__":
    convert_fide()
    convert_olimpbase()
