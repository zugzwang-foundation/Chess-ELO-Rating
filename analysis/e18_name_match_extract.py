#!/usr/bin/env python3
"""E18, R70: name matching of the broadcast archive's games of 2020 to 2023, a labelled sensitivity (D-0016; session
ELO-9, Phase 0b; needs data/).

Ruling R70 allows name matching only as a labelled sensitivity: a player of a game without a FIDE ID is matched when
exactly one player on the FIDE list in force has the same name, the same federation and a rating within 10 points of the
game's Elo tag; a game counts when both its players match; unmatched games are dropped. If the matched games give a table
for 2023 or 2024, the three-way test and E19 are reported with it beside the headline, which keeps R65's sample rule.

The games are E2's (analysis/e2_broadcast_extract.py, `load_games`: a result, the standard variant, dated as E2 reads
them), the years 2020 to 2023 by E2's date, as E18 §1 counts them. The interim files keep no federation, so the PGN
headers of every archive file holding such a game are read again (data/raw/lichess_broadcast/, through the zstd command)
and joined on the game's URL. Counted per year: the games; those without both FIDE IDs; of these, those with both Elo
tags; with both federation tags (a tag White… or Black… naming a federation, a country or a nation); and those both of
whose players match by R70's rule on the standard list E2 reads for the game (the month the broadcast tour starts, or the
game's month when the tour spans more than 30 days). Every player tag the files carry is counted too. If any game
matched, the script stops: the sensitivity's sample and tables would then have to be built (D-0016, reading 11).
Writes analysis/aggregates/E18_name_match.json: counts only. Python standard library only.

Usage: python3 analysis/e18_name_match_extract.py > analysis/aggregates/E18_name_match.json
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e17_top100_extract as ex  # noqa: E402  (E17's name key, unchanged)
import e2_broadcast_extract as e2x  # noqa: E402  (E2's games and dates, unchanged)

YEARS = ("2020", "2021", "2022", "2023")
RAW = ROOT / "data" / "raw" / "lichess_broadcast"
LISTS = ROOT / "data" / "interim" / "fide" / "standard"
TAG = re.compile(r'^\[(\w+) "(.*)"\]$')
FED_TAG = re.compile(r"^(White|Black)(Fed|Federation|Country|Nation)$")
ELO_TOLERANCE = 10


def headers(stem: str):
    """Each game's PGN tags in one archive file, in order."""
    proc = subprocess.Popen(["zstd", "-dc", str(RAW / f"lichess_db_broadcast_{stem}.pgn.zst")], stdout=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace")
    tags: dict[str, str] = {}
    in_moves = False
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.startswith("["):
            if in_moves:
                yield tags
                tags, in_moves = {}, False
            m = TAG.match(line)
            if m:
                tags[m.group(1)] = m.group(2)
        elif line.strip():
            in_moves = True
    if tags:
        yield tags
    proc.wait()


def federations(tags: dict[str, str]) -> tuple[str | None, str | None]:
    """The federation each player's tags name, if any."""
    out = {"White": None, "Black": None}
    for k, v in tags.items():
        m = FED_TAG.match(k)
        if m and v.strip():
            out[m.group(1)] = v.strip().upper()
    return out["White"], out["Black"]


NAMES: dict[str, str] = {}


def roster(month: str) -> dict[tuple[str, str], list[tuple[str, int]]]:
    """FIDE's standard list of a month by (name key, federation): the players' IDs and ratings."""
    if not NAMES:
        NAMES.update(ex.load_names()[0])
    names = NAMES
    out: dict = defaultdict(list)
    with (LISTS / f"{month}.tsv").open(encoding="utf-8") as fh:
        rows = csv.reader(fh, delimiter="\t")
        next(rows)
        for pid, rating, _g, _k, _by, _sex, fed, _flag, _title in rows:
            if rating.isdigit() and pid in names:
                out[(ex.norm(names[pid]), fed)].append((pid, int(rating)))
    return out


def match(name: str, fed: str | None, elo: str, players: dict) -> str | None:
    """R70: the one player on the list with this name, this federation and a rating within 10 points of the Elo tag."""
    if not fed or not elo.isdigit():
        return None
    hits = [pid for pid, r in players.get((ex.norm(name), fed), []) if abs(r - int(elo)) <= ELO_TOLERANCE]
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    games, _raw = e2x.load_games()
    games = [g for g in games if e2x.month_of(g.date_used)[:4] in YEARS]
    span: dict[str, list] = {}
    for g in games:
        d = e2x.to_date(g.date_used)
        s = span.setdefault(g.tour, [d, d])
        s[0], s[1] = min(s[0], d), max(s[1], d)
    files = sorted({g.file_month for g in games})
    fed_by_url: dict[str, tuple] = {}
    tag_counts: Counter = Counter()
    for stem in files:
        for tags in headers(stem):
            for k in tags:
                if k.startswith(("White", "Black")):
                    tag_counts[k] += 1
            url = tags.get("GameURL", "")
            if url:
                fed_by_url[url] = federations(tags)
    by_year = {y: Counter() for y in YEARS}
    rosters: dict[str, dict] = {}
    matched = []
    for g in games:
        y = e2x.month_of(g.date_used)[:4]
        c = by_year[y]
        c["games"] += 1
        if g.white_fide_id.isdigit() and g.black_fide_id.isdigit():
            continue
        c["without_both_fide_ids"] += 1
        if not (g.white_elo.isdigit() and g.black_elo.isdigit()):
            continue
        c["both_elo_tags"] += 1
        fw, fb = fed_by_url.get(g.game_url, (None, None))
        if not (fw and fb):
            continue
        c["both_federation_tags"] += 1
        s0, s1 = span[g.tour]
        start = s0 if (s1 - s0).days <= 30 else e2x.to_date(g.date_used)
        month = f"{start.year:04d}-{start.month:02d}"
        if month not in rosters:
            rosters[month] = roster(month)
        w = match(g.white, fw, g.white_elo, rosters[month])
        b = match(g.black, fb, g.black_elo, rosters[month])
        if w and b:
            c["matched"] += 1
            matched.append(g.game_url)
    if matched:
        raise SystemExit(f"{len(matched)} games matched under R70: build the sensitivity's sample and tables "
                         "(D-0016, reading 11) before reporting")
    out = {"rule": {"ruling": "R70 (docs/decisions/D-0016_rulings-on-elo-8-questions.md)",
                    "match": "the one player on the standard list in force with the same name (E17's name key), the "
                             "same federation and a rating within 10 points of the game's Elo tag; a game counts when "
                             "both players match; unmatched games are dropped",
                    "elo_tolerance": ELO_TOLERANCE, "federation_tags": FED_TAG.pattern},
           "years": list(YEARS), "files_read": files,
           "player_tags_in_files": dict(sorted(tag_counts.items())),
           "by_year": {y: {k: c.get(k, 0) for k in ("games", "without_both_fide_ids", "both_elo_tags",
                                                     "both_federation_tags", "matched")} for y, c in by_year.items()},
           "matched_games": len(matched),
           "tables": "none: no game matched, so no window of 2023 or 2024 gains a game and no table results"}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
