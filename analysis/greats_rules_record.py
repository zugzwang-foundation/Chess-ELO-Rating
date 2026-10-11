#!/usr/bin/env python3
"""The FIDE Rating Regulations in force from 2001 to June 2017, for the greats' replay (SPEC-GREATS v1.0 §6; session
ELO-9, Phase 3; needs data/): writes docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md.

FIDE's handbook online holds the rating regulations from 1 July 2014 only (docs/research/DATA-PROBE_greats.md §2.5); the
earlier texts are read from the Internet Archive's copies of FIDE's handbook, each fetched once by tools/data/fetch_probe.py
(data/raw/probe/, with its manifest), and the 2014 text from FIDE's handbook (tools/data/fetch_fide_handbook.py). The
passages the replay needs (how a rating change is computed, the 350- and 400-point rules, K, rounding) are copied from
each page's text by fixed anchors, not retyped; each version's score-probability table is read from its page and compared
entry by entry with Layer 0's table 8.1.2 (src/layer0/tables.py). Nothing is filled from memory: what the texts leave
open is marked NOT VERIFIED. Python standard library only.

Usage: python3 analysis/greats_rules_record.py > docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md
"""
from __future__ import annotations

import csv
import gzip
import html
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import layer0  # noqa: E402

PROBE = ROOT / "data" / "raw" / "probe"
HB = ROOT / "data" / "raw" / "fide_site" / "handbook"
VERSIONS = [
    {"key": "2003", "file": PROBE / "wayback_hb2003_B0210.html", "manifest": "wayback_hb2003_B0210",
     "original": "http://www.fide.com/official/handbook.asp?level=B0210", "snapshot": "2003-06-09",
     "title": "B.02.10 The working of the FIDE Rating System, as FIDE's handbook carried it in June 2003",
     "passages": [("10.32 R n for the FIDE Rating list (FRL) is rounded off", "Only R n >= 2005 are considered."),
                  ("10.6 Determining the rating change for a rated player:", "Thereafter it remains permanently at 10."),
                  ("10.66", "nearest 1 or 0.")]},
    {"key": "2007", "file": PROBE / "wayback_hb2007_B0210.html", "manifest": "wayback_hb2007_B0210",
     "original": "http://fide.com/official/handbook.asp?level=B0210", "snapshot": "2007-10-14",
     "title": "B.02.10 The working of the FIDE Rating System, as FIDE's handbook carried it in October 2007",
     "passages": [("10.32 R n for the FIDE Rating list (FRL) is rounded off", "rounded off to the nearest 1 or zero."),
                  ("10.5 Determining the rating change for a rated player:", "Thereafter it remains permanently at 10."),
                  ("10.53", "nearest 1 or 0.")]},
    {"key": "2010", "file": PROBE / "wayback_hb2010_id73.html", "manifest": "wayback_hb2010_id73",
     "original": "http://www.fide.com/fide/handbook.html?id=73&view=article", "snapshot": "2010-06-09",
     "title": "B.02 §8 The working of the FIDE Rating System, as FIDE's handbook carried it in June 2010",
     "passages": [("8.32 R n for the FIDE Rating list (FRL) is rounded off", "0.5 is rounded up."),
                  ("8.5 Determining the rating change for a rated player", "even if the rating drops below 2400."),
                  ("8.57", "0.5 is rounded to 1.")]},
    {"key": "2014", "file": HB / "B022014.html", "manifest": None,
     "original": "https://handbook.fide.com/chapter/B022014", "snapshot": None,
     "title": "FIDE Rating Regulations effective from 1 July 2014 till 30 June 2017, §8.5 (FIDE's handbook online)",
     "passages": [("8.51 For each game played against a rated player", "0.5 is rounded up ( whether the change is positive or negative ).")]},
]


def text(path: Path) -> str:
    b = path.read_bytes()
    if b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    s = b.decode("utf-8", "replace") if b"utf-8" in b[:5000].lower() else b.decode("latin-1")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).replace("\xa0", " ").strip()


def passage(t: str, start: str, end: str) -> str:
    i = t.index(start)
    return t[i:t.index(end, i) + len(end)]


def table(t: str) -> set[tuple]:
    """The score-probability table of a page: (lo, hi, H, L) for each D range, and 'over 735'."""
    rows = {(int(a), int(b), Decimal("0." + h), Decimal("0." + low))
            for a, b, h, low in re.findall(r"\b(\d{1,3})\s*-\s*(\d{1,3})\s+\.(\d\d)\s+\.(\d\d)\b", t)}
    rows = {r for r in rows if r[2] + r[3] == 1 and r[2] >= Decimal("0.5")}   # not table 8.1(a)'s p and dp
    if re.search(r"(?:over|>) 735\s+1\.0\s+\.00", t):
        rows.add((736, None, Decimal("1.00"), Decimal("0.00")))
    return rows


def manifest_row(key: str) -> dict:
    with (PROBE / "MANIFEST.tsv").open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r["key"] == key][-1]


def handbook_row(code: str) -> dict:
    with (HB / "MANIFEST.tsv").open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r["code"] == code][-1]


def main() -> int:
    layer0_table = {(lo, hi if hi is not None else None, h, low) for lo, hi, h, low in layer0.TABLE_812}
    layer0_table = {(lo, hi, h, low) if hi is not None else (736, None, h, low) for lo, hi, h, low in layer0_table}
    out = ["# Verification sweep — the FIDE Rating Regulations in force from 2001 to June 2017, for the greats' replay",
           "",
           "Status: VERIFICATION RECORD (primary-source transcription). Session ELO-9, Phase 3 (§5 as ruling R74 "
           "amends the reading of the rounding, and as the ELO-9 review corrects the description of the texts' rounding "
           "clauses, ELO9-QC-1). Generated by "
           "`analysis/greats_rules_record.py` from pages fetched once each and cached under `data/` (never committed); do "
           "not edit by hand. Author: The Zugzwang Authors. Licence: CC BY 4.0 (see `docs/LICENSE-docs.md`); quoted "
           "third-party text remains its owners' and is reproduced for verification only.",
           "",
           "**Why.** SPEC-GREATS v1.0 §6 replays the greats' games from the list of April 2008 to December 2019 under "
           "FIDE's rules in force at each date. `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md` transcribes "
           "the versions from 1 July 2017; FIDE's handbook online holds one earlier version, from 1 July 2014, and the "
           "earlier texts survive only in the Internet Archive's copies of FIDE's handbook "
           "(`docs/research/DATA-PROBE_greats.md` §2.5). This record transcribes, from each, the passages the replay "
           "needs: how a rating change is computed, the 350- and 400-point rules, K and rounding.",
           "",
           "**Method.** Each page's text is taken from its HTML by a Python standard-library parser and each passage is "
           "copied from that text between fixed anchors by the script, not retyped (whitespace normalised; the archived "
           "pages lose the subscripts of P_D, Sigma and Delta, which are kept as they come). Each version's table of "
           "score probabilities is read from the same text and compared entry by entry with Layer 0's table 8.1.2.",
           "",
           "| # | Version | Source | Fetched (UTC) | Table equal to Layer 0's |",
           "|---|---|---|---|---|"]
    texts = {}
    for i, v in enumerate(VERSIONS, 1):
        t = text(v["file"])
        texts[v["key"]] = t
        row = manifest_row(v["manifest"]) if v["manifest"] else handbook_row("B022014")
        src = (f"{v['original']}, the Internet Archive's copy of {v['snapshot']} ({row['url']})" if v["snapshot"]
               else v["original"])
        tab = table(t)
        v["table"] = tab
        v["fetched"] = row["fetched_utc"]
        v["equal"] = tab == layer0_table
        out.append(f"| {i} | {v['title']} | {src} | {row['fetched_utc']} | "
                   f"{'yes, all ' + str(len(tab)) + ' rows' if v['equal'] else 'no: ' + str(len(tab ^ layer0_table)) + ' rows differ'} |")
    out += ["", "---", ""]
    for i, v in enumerate(VERSIONS, 1):
        out += [f"## {i}. {v['title']}", ""]
        for a, b in v["passages"]:
            out += [f"> {passage(texts[v['key']], a, b)}", ""]
    out += ["## 5. What differs, and what the texts leave open", "",
            "| Rule | 2003 text (§10.6) | 2007 text (§10.5) | 2010 text (§8.5) | 2014 text (§8.5) |",
            "|---|---|---|---|---|",
            "| How the change is computed | from the average rating of the opponents (Rc): W − We, We = PD × n, the "
            "difference R − Rc | for each game: ΔR = score − PD, ΣΔR × K | for each game, as 2007 | for each game, as 2007 |",
            "| The rating-difference rule | 350 points, for the difference to the opponents' average | 350 points, "
            "for each game | 400 points, for each game | 400 points, for each game |",
            "| K | 25 new / 15 / 10 (2400 and 30 games, then permanently) | as 2003 | 25 new / 15 / 10 (2400, "
            "\"remains at that level subsequently, even if the rating drops below 2400\") | 40 new / 20 / 10 / 40 "
            "juniors under 2300 |",
            "| Rounding | the rated player's new rating Rn = Ro + ΣΔR: \"rounded off to the nearest 1 or 0\" (§10.66); a new "
            "player's to the nearest 5 (§10.32) | the rated player's new rating Rn: \"rounded off to the nearest 1 or 0\" "
            "(§10.53, in §10.5 for a rated player; the half point not stated); a new player's Rn the same (§10.32) | the "
            "rated player's new rating Rn: \"rounded off to the nearest 1 or 0, 0.5 is rounded to 1\" (§8.57, in §8.5 "
            "for a rated player); a new player's Rn, \"0.5 is rounded up\" (§8.32) | the change: \"rounded to the "
            "nearest whole number. 0.5 is rounded up (whether the change is positive or negative)\" (§8.57) |",
            "| Score-probability table | " + " | ".join(
                "equal to table 8.1.2" if v["equal"] else "differs" for v in VERSIONS) + " |",
            "",
            "**What the texts leave open, read from FIDE's own calculations by the replay** (SPEC-GREATS §6 asks Layer 0 "
            "to reproduce FIDE's published changes period by period; E20 §4.2 reports the counts):",
            "",
            "- **the date the 350-point rule became the 400-point rule**: between the copy of October 2007 and the copy "
            "of June 2010 the texts do not say (NOT VERIFIED by the texts); read as tournaments starting from 1 July 2009 "
            "and tested on every game whose gap exceeds 350 points, which FIDE's pages bear out (E20 §4.2);",
            "- **rounding before July 2014**: the 2003, 2007 and 2010 texts round the rated player's new rating Rn, the old "
            "rating plus the change, \"to the nearest 1 or 0\" (§10.66, §10.53), the 2010 text adding \"0.5 is rounded to "
            "1\" (§8.57); with a whole old rating, a new rating rounded with 0.5 up rounds the change with 0.5 towards "
            "+infinity. This record first described §10.53 and §8.57 as rounding a new player's rating, said the texts "
            "had no clause for a rated player, and read the lists before July 2014 as the 2014 clause applied as E17 found "
            "FIDE's lists apply the 2017 wording, 0.5 away from zero; FIDE's pages contradicted that reading, ruling R74 "
            "(`docs/decisions/D-0017_rulings-on-the-greats.md`; SPEC-L0 §11, F-H09) adopts 0.5 towards +infinity for the "
            "lists before July 2014, a change made after partial pages had been seen and before the full replay, and the "
            "review of session ELO-9 (`docs/review/REDTEAM_v1_0.md`, ELO9-QC-1) corrected the description of the texts. "
            "The reading of Rn as the rated player's new rating, and of the 2007 text's half point, is NOT VERIFIED "
            "(E20 §4.2 gives the counts under both readings);",
            "- **the date per-game computation replaced the 2003 method**: FIDE's calculations give every game from "
            "the list of April 2008 (DATA-PROBE §2.4); the replay starts there.",
            ""]
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
