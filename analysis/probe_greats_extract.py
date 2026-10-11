#!/usr/bin/env python3
"""The data probe for the greats (session ELO-9, Phase 1; needs data/): what FIDE's own sources hold, how far back, on
what terms, and what every other candidate source of historical results with ratings says about its use.

Reads only pages already fetched once by tools/data/fetch_probe.py (data/raw/probe/, with its MANIFEST.tsv), the
handbook chapters of tools/data/fetch_fide_handbook.py (data/raw/fide_site/handbook/), the robots.txt answers cached
there, and FIDE's list manifest (data/raw/fide/MANIFEST.tsv); it fetches nothing. Writes
analysis/aggregates/PROBE_greats.json: dates, counts, statuses and the sources' terms quoted verbatim (short passages,
extracted by fixed anchors from the cached pages), never a rating list, a rating series or a game. No analysis of any
player is done here (the ELO-9 brief, Phase 1). Python standard library only.

Usage: python3 analysis/probe_greats_extract.py > analysis/aggregates/PROBE_greats.json
"""
from __future__ import annotations

import csv
import gzip
import html
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "data" / "raw" / "probe"
SITE = ROOT / "data" / "raw" / "fide_site"
FIDE_HOSTS = {"ratings.fide.com", "handbook.fide.com", "old.fide.com", "www.fide.com"}
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                                       "Dec"), 1)}


def raw(key: str) -> bytes:
    b = (PROBE / f"{key}.html").read_bytes()
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b


def page(key: str) -> str:
    return raw(key).decode("utf-8", "replace").lstrip("﻿")


def text(s: str) -> str:
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def quote(key: str, start: str, end: str) -> str:
    """The passage of a cached page's text from `start` to the end of `end`, verbatim (whitespace normalised)."""
    t = text(page(key))
    i = t.index(start)
    j = t.index(end, i) + len(end)
    return t[i:j]


def manifest() -> list[dict]:
    with (PROBE / "MANIFEST.tsv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def fetched(key: str) -> dict:
    rows = [r for r in manifest() if r["key"] == key]
    r = rows[-1]
    return {"url": r["url"], "fetched_utc": r["fetched_utc"], "status": r["status"], "bytes": int(r["bytes"])}


def ym(label: str) -> str:
    """'2003-Apr' or 'Apr 2003' -> '2003-04'."""
    m = re.match(r"(\d{4})-([A-Z][a-z]{2})$", label) or re.match(r"([A-Z][a-z]{2}) (\d{4})$", label)
    y, mon = (m.group(1), m.group(2)) if label[0].isdigit() else (m.group(2), m.group(1))
    return f"{y}-{MONTHS[mon]:02d}"


def periods_in(s: str) -> list[str]:
    return sorted({v[:7] for v in re.findall(r'<option[^>]*value="(\d{4}-\d\d-\d\d)"', s)})


def list_file(key: str) -> dict:
    with zipfile.ZipFile(PROBE / f"{key}.html") as z:
        name = z.namelist()[0]
        lines = z.read(name).decode("latin-1").splitlines()
    return {**fetched(key), "file": name, "players": len(lines) - 1,
            "columns": re.sub(r"\s+", " ", lines[0]).strip()}


def calc_page(key: str) -> dict:
    s = page(key)
    t = text(s)
    period = re.search(r"Standard Ratings (\w+ \d{4})", t).group(1)
    tournaments = len(re.findall(r"\bRc\b", t))
    rows = len(re.findall(r'class="(?:white|black)_note"', s))
    return {**fetched(key), "list": period, "tournaments": tournaments, "game_rows": rows,
            "white_marks": len(re.findall(r'class="white_note"', s)),
            "black_marks": len(re.findall(r'class="black_note"', s)),
            "format": "per game" if rows else "tournament level (Rc, Ro, w, n, chg, K)"}


def cdx(key: str) -> list[list[str]]:
    return json.loads(page(key))[1:]


def fide() -> dict:
    out: dict = {}
    dl = page("fide_download_lists")
    per = periods_in(dl)
    out["download_page"] = {**fetched("fide_download_lists"), "periods": len(per), "first": per[0], "last": per[-1]}
    old = page("wayback_fide_download_2022")
    per = periods_in(old)
    out["download_page_2022"] = {**fetched("wayback_fide_download_2022"), "periods": len(per), "first": per[0],
                                 "last": per[-1], "per_year": dict(sorted(Counter(p[:4] for p in per).items()))}
    out["lists_probed"] = [list_file(k) for k in ("fide_list_jan01frl.zip", "fide_list_jul08frl.zip",
                                                  "fide_list_jul12frl.zip", "fide_list_standard_jan13frl.zip")]
    with (ROOT / "data" / "raw" / "fide" / "MANIFEST.tsv").open(encoding="utf-8") as fh:
        std = sorted(r["period"] for r in csv.DictReader(fh, delimiter="\t") if r["tc"] == "standard")
    out["lists_on_disk"] = {"first": std[0], "last": std[-1], "count": len(std)}
    names = sorted({u.split("/")[-1].lower() for _t, u, st in cdx("wayback_cdx_download") if st == "200"})
    old_names = [n for n in names if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d\dfrl\.zip", n)]
    out["old_file_names_in_wayback"] = {"count": len(old_names), "first_year": "20" + min(n[3:5] for n in old_names),
                                        "last_year": "20" + max(n[3:5] for n in old_names)}
    top = page("fide_top_lists")
    out["top_lists"] = {
        **fetched("fide_top_lists"),
        "tabs": len(re.findall(r"/a_top\.php\?list=", top)),
        "archive_periods": len(periods_in(top)),
        "toparc_live": fetched("fide_toparc_index"),
        "toparc_wayback": {"snapshots": len(cdx("wayback_cdx_toparc")),
                           "answered_200": sum(1 for _t, _u, st in cdx("wayback_cdx_toparc") if st == "200"),
                           "first_snapshot": min(t for t, _u, st in cdx("wayback_cdx_toparc") if st == "200")[:8],
                           "last_snapshot": max(t for t, _u, st in cdx("wayback_cdx_toparc") if st == "200")[:8],
                           "cod1": {**fetched("wayback_toparc_cod1_2008"),
                                    "title": re.search(r"Top 100 Players \w+ \d{4}", text(page("wayback_toparc_cod1_2008"))).group(0)}}}
    hist = {}
    for pid in ("1503014", "4100018", "4100026", "600024"):
        d = json.loads(page(f"fide_chart_{pid}_all") or "[]")
        hist[pid] = {**fetched(f"fide_chart_{pid}_all"), "points": len(d),
                     "first": ym(d[0]["date_2"]) if d else None, "last": ym(d[-1]["date_2"]) if d else None,
                     "name": d[0]["name"] if d else None}
    out["histories"] = hist
    idx = page("fide_calcs_more_5000017")
    std_periods = sorted({m for m in re.findall(r"period=(\d{4}-\d\d)-\d\d&rating=0", idx)})
    out["calculations"] = {"index": {**fetched("fide_calcs_more_5000017"), "player": "5000017",
                                     "standard_periods": len(std_periods), "first": std_periods[0],
                                     "last": std_periods[-1]},
                           "pages": [calc_page(f"fide_calc_5000017_{p}") for p in
                                     ("2001-07", "2005-07", "2007-07", "2007-10", "2008-01", "2008-04", "2008-07",
                                      "2010-01")]}
    hb = (SITE / "handbook" / "B022024.html").read_text(encoding="utf-8", errors="replace")
    versions = re.findall(r'<a href=/chapter/(B02\d{4})\s*>(FIDE Rating Regulations[^<]*)</a>', hb)
    snaps73 = [t for t, _u, s, _d in cdx("wayback_cdx_handbook_id73") if s == "200"]
    b02 = [(t, u) for t, u, s in cdx("wayback_cdx_official_handbook") if s == "200" and re.search(r"level=B02", u)]
    out["handbook"] = {"live_versions": [{"code": c, "title": t.strip()} for c, t in dict(versions).items()],
                       "b022014": {"fetched_utc": _hb_manifest("B022014")},
                       "wayback_section8_2010s": {"original": "http://www.fide.com/fide/handbook.html?id=73&view=article",
                                                  "snapshots": len(snaps73), "first": min(snaps73)[:8],
                                                  "last": max(snaps73)[:8]},
                       "wayback_handbook_2003": {"original": "http://www.fide.com/official/handbook.asp?level=B02..",
                                                 "pages": len(b02), "first": min(t for t, _u in b02)[:8],
                                                 "last": max(t for t, _u in b02)[:8]}}
    out["robots"] = {"ratings.fide.com": "HTTP 404, cached 2026-10-10 under data/raw/fide_site/",
                     "handbook.fide.com": "HTTP 404, cached 2026-10-10 under data/raw/fide_site/",
                     "old.fide.com": "disallows only " + ", ".join(
                         re.findall(r"Disallow: (\S+)", (PROBE / "robots_old.fide.com.txt").read_text(encoding="utf-8")))}
    out["footer"] = quote("fide_ratings_home", "© 2026 FIDE International Chess Federation. All Rights Reserved.",
                          "without the written permission of FIDE International Chess Federation.")
    out["requests"] = requests_to_fide()
    return out


def _hb_manifest(code: str) -> str:
    with (SITE / "handbook" / "MANIFEST.tsv").open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r["code"] == code][-1]["fetched_utc"]


def requests_to_fide() -> dict:
    rows = [r for r in manifest() if urlparse(r["url"].split(" ")[0]).netloc in FIDE_HOSTS]
    times = [datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in rows]
    hosts = [urlparse(r["url"].split(" ")[0]).netloc for r in rows]
    gaps = []
    for i in range(1, len(rows)):
        same = [j for j in range(i) if hosts[j] == hosts[i]]
        if same:
            g = (times[i] - times[same[-1]]).total_seconds()
            if g < 2:
                gaps.append({"from": rows[same[-1]]["key"], "to": rows[i]["key"], "at": rows[i]["fetched_utc"],
                             "seconds": g})
    return {"count": len(rows), "statuses": dict(Counter(r["status"] for r in rows)), "hosts": dict(Counter(hosts)),
            "first": rows[0]["fetched_utc"], "last": rows[-1]["fetched_utc"], "gaps_under_2s": gaps}


def olimpbase_lists() -> dict:
    s = page("olimpbase_elo_summary")
    lists = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S):
        c = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()
             for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        if c and re.fullmatch(r"[A-Z][a-z]{2} \d{4}", c[0]) and len(c) >= 4 and c[3].replace(",", "").isdigit():
            lists.append({"list": ym(c[0]), "players": int(c[3].replace(",", "")), "remark": c[-1]})
    official = [x for x in lists if x["list"] >= "1971-07"]
    with zipfile.ZipFile(PROBE / "olimpbase_elo1967-2001.zip.html") as z:
        rows = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    return {"summary": fetched("olimpbase_elo_summary"), "file": fetched("olimpbase_elo1967-2001.zip"),
            "file_rows": len(rows), "lists": len(lists), "official_lists": len(official),
            "first_official": official[0]["list"], "last": official[-1]["list"],
            "per_decade": {d: sum(1 for x in official if x["list"][:3] == d[:3]) for d in ("1970s", "1980s", "1990s",
                                                                                           "2000s")},
            "remarks": [x for x in official if x["remark"] and x["list"] in ("1971-07", "1985-07", "1990-01",
                                                                            "1992-07", "1999-01", "2000-10")],
            "jan_2001_players": next(x["players"] for x in official if x["list"] == "2001-01"),
            "supplementary": [x for x in official if "supplementary" in x["remark"]],
            "official_list_dates": [{"list": x["list"], "players": x["players"]} for x in official]}


# The other candidate sources: what each holds, the passage of its terms quoted verbatim (fixed anchors in the cached
# page), and the status the executor gives it under the brief ("use none that needs permission").
OTHERS = [
    {"key": "twic", "name": "The Week in Chess (TWIC)", "holds": "weekly game files of elite and open events since 1994",
     "page": "wayback_twic_2026", "anchors": ("TWIC magazine is free for personal use only.", "All rights are reserved."),
     "also": "twic_archive", "status": "needs permission",
     "why": "free for personal use only, all rights reserved; excluded by the brief without the operator's written permission"},
    {"key": "chessbase", "name": "ChessBase (Mega Database and online database)",
     "holds": "commercial game databases from the 19th century to date", "page": "chessbase_agb",
     "anchors": ("The customer can select products from the shop's range,", "and collect them in a so-called \"shopping cart\""),
     "status": "needs permission",
     "why": "commercial products sold under the shop's terms; excluded by the brief without written permission"},
    {"key": "chessmetrics", "name": "Chessmetrics (Jeff Sonas)",
     "holds": "historical ratings of Sonas's own system and their source data", "page": "chessmetrics_sourcedata",
     "anchors": ("Right now, my data from 1901 through 2002 is taken from the ChessBase BigBase 2003", "BigBase 2003"),
     "status": "needs permission",
     "why": "no licence stated on the pages read; its data are taken from ChessBase's databases; not FIDE's ratings"},
    {"key": "olimpbase_lists", "name": "OlimpBase: History of Elo ratings 1971-2001 (Wojciech Bartelski)",
     "holds": "FIDE's rating lists from July 1971, transcribed from Chess Informant and other publications",
     "page": "olimpbase_copyright",
     "anchors": ("OlimpBase lets anyone use its large archives free of charge.", "without citing the source."),
     "footer": ("olimpbase_index", "© Free for non-commercial use only.", "Please cite the source."),
     "status": "usable",
     "why": "free of charge, citing the source, non-commercial use only: this project's use is non-commercial analysis, "
            "cites the source and commits aggregates only"},
    {"key": "olimpbase_games", "name": "OlimpBase: Olympiad results and game files",
     "holds": "Olympiad pairings, results and PGN game files, 1927-2026", "page": "olimpbase_credits",
     "anchors": ("The ChessBase team - for making their game database freely available to the public.",
                 "freely available to the public."),
     "also_quote": ("olimpbase_credits", "Mark Crowther (UK) - for making his huge archives available to me.",
                    "available to me."),
     "status": "needs permission",
     "why": "its credits name ChessBase's database and the archives of TWIC's editor among the sources of the games, "
            "which the brief excludes without written permission"},
    {"key": "pgnmentor", "name": "PGN Mentor", "holds": "game files by player, opening and event",
     "page": "pgnmentor_files", "anchors": ("Copyright © 2025 64 Squares.", "64 Squares."), "status": "needs permission",
     "why": "a copyright notice and no licence"},
    {"key": "kingbase", "name": "KingBase", "holds": "a discontinued game database (copies of 2018 and 2019)",
     "page": None, "status": "needs permission",
     "why": "discontinued, no licence stated, compiled from sources that include TWIC (SPEC-SELFCAL §2, checked on "
            "2026-10-11; not fetched again)"},
    {"key": "caissabase", "name": "Caissabase", "holds": "formerly a free game database", "page": "wayback_caissabase_2026",
     "anchors": ("No KYC Crypto Casinos:", "Best in 2026"), "also": "caissabase_home", "status": "unusable",
     "why": "the live site refused (HTTP 403) and its domain's archived page of May 2026 carries unrelated content"},
    {"key": "chessgames", "name": "Chessgames.com", "holds": "a game database with player pages",
     "page": "chessgames_home", "anchors": ("Copyright 2001-2025, Chessgames Services LLC", "Chessgames Services LLC"),
     "status": "needs permission", "why": "a copyright notice and no licence"},
    {"key": "365chess", "name": "365Chess.com", "holds": "a game database", "page": "chess365_home",
     "anchors": ("© 2026 365Chess.com", "365Chess.com"), "terms_robots": "chess365_terms", "status": "needs permission",
     "why": "a copyright notice; its terms page is closed to robots, so it was not read"},
    {"key": "chess-results", "name": "Chess-Results.com", "holds": "tournament pairings, results and ratings, from 2006",
     "page": "chessresults_impressum",
     "anchors": ("Die Turnierdaten und Partien dürfen nicht kopiert und auf anderen Seiten publiziert werden.",
                 "auf anderen Seiten publiziert werden."),
     "translation": "The tournament data and games may not be copied and published on other pages.",
     "status": "needs permission", "why": "copying the tournament data is not allowed without the author's consent"},
    {"key": "chess.com", "name": "Chess.com", "holds": "a master-game database among its services",
     "page": "chesscom_user_agreement",
     "anchors": ("use any robot, spider, site search/retrieval application,", "or its contents;"),
     "status": "unusable", "why": "automated retrieval is prohibited"},
    {"key": "kaggle", "name": "Kaggle, Deloitte/FIDE Chess Rating Challenge (2011)",
     "holds": "anonymised FIDE games prepared for the contest", "page": "wayback_kaggle_rules_2015",
     "anchors": ("Deloitte/FIDE Chess Rating Challenge Mon 7 Feb 2011", "Wed 4 May 2011"), "also": "kaggle_chessratings2_rules",
     "status": "unusable", "why": "the rules could not be read (the live page needs JavaScript; the archived copy holds no "
                                  "rules text): NOT VERIFIED; and the players are anonymised, so no player can be named"},
    {"key": "lichess", "name": "Lichess broadcast archive", "holds": "broadcast over-the-board games from January 2020",
     "page": None, "status": "usable",
     "why": "CC BY-SA 4.0 [V 4]; already used by E2, E18 and E19; it starts in 2020, after the periods probed here"},
    {"key": "wikipedia", "name": "Wikipedia", "holds": "articles with crosstables of selected events",
     "page": "wikipedia_fide_rankings",
     "anchors": ("Text is available under the Creative Commons Attribution-ShareAlike 4.0 License", "additional terms may apply."),
     "status": "usable", "why": "CC BY-SA 4.0, but it is no game archive: selected events, no systematic results with ratings"},
    {"key": "internet-archive", "name": "Internet Archive (Wayback Machine)",
     "holds": "archived copies of FIDE's pages: the top-list archive from July 2000, the handbook from 2003",
     "page": "wayback_ia_terms_2024",
     "anchors": ("Access to the Archive’s Collections is provided at no cost to you and is granted for scholarship and research purposes only.",
                 "research purposes only."),
     "status": "usable",
     "why": "for scholarship and research; used here to establish what FIDE published and, in Phase 3, to transcribe "
            "FIDE's regulations in force before July 2014 (the content is FIDE's)"},
]


def others() -> list[dict]:
    out = []
    for s in OTHERS:
        row = {k: v for k, v in s.items() if k not in ("anchors", "footer", "also_quote", "also", "terms_robots")}
        if s.get("page"):
            row["source"] = fetched(s["page"])
            row["quote"] = quote(s["page"], *s["anchors"])
        if s.get("footer"):
            row["footer_quote"] = quote(*s["footer"])
        if s.get("also_quote"):
            row["second_quote"] = quote(*s["also_quote"])
        if s.get("also"):
            row["live"] = fetched(s["also"])
        if s.get("terms_robots"):
            row["terms_page"] = fetched(s["terms_robots"])
        out.append(row)
    return out


def main() -> int:
    out = {"brief": "ELO-9, Phase 1: the data probe for the greats (no analysis)",
           "fetcher": "tools/data/fetch_probe.py", "fide": fide(), "olimpbase_lists": olimpbase_lists(),
           "others": others(),
           "probe_requests": {"count": len(manifest()), "first": manifest()[0]["fetched_utc"],
                              "last": manifest()[-1]["fetched_utc"]}}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
