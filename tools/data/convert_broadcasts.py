#!/usr/bin/env python3
"""Convert the Lichess broadcast archive (PGN, zstd) into compact per-month TSV files of game headers.

Input:  data/raw/lichess_broadcast/lichess_db_broadcast_YYYY-MM.pgn.zst
Output: data/interim/broadcast/YYYY-MM.tsv, one line per game (no moves).
Both directories are gitignored: broadcast games are CC BY-SA 4.0 [V 4] and the
project commits aggregates only.

Fields: tour (the broadcast URL up to the tour slug), round_url, game_url, event,
date (PGN Date), utc_date, white, black, white_fide_id, black_fide_id, white_elo,
black_elo, result, variant, time_control (the tag verbatim, tabs removed),
clk_white, clk_black (the first [%clk] reading of each side, in seconds; empty if
absent). Decompression uses the zstd command (Python's standard library has no
zstd before 3.14). Python standard library otherwise.

Usage: python3 tools/data/convert_broadcasts.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "lichess_broadcast"
DST = ROOT / "data" / "interim" / "broadcast"
TAG = re.compile(r'^\[(\w+) "(.*)"\]$')
CLK = re.compile(r"\[%clk (\d+):(\d\d):(\d\d)\]")
COLS = ["tour", "round_url", "game_url", "event", "date", "utc_date", "white", "black", "white_fide_id",
        "black_fide_id", "white_elo", "black_elo", "result", "variant", "time_control", "clk_white", "clk_black"]


def clean(v: str) -> str:
    return v.replace("\t", " ").replace("\n", " ").strip()


def flush(tags: dict[str, str], moves: list[str], out) -> None:
    if not tags:
        return
    text = " ".join(moves)
    clks = [int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in CLK.findall(text[:4000])[:2]]
    url = tags.get("BroadcastURL", "")
    parts = url.split("/")
    tour = "/".join(parts[:5]) if len(parts) >= 5 else url        # https://lichess.org/broadcast/<tour-slug>
    row = [tour, url, tags.get("GameURL", ""), tags.get("Event", ""), tags.get("Date", ""), tags.get("UTCDate", ""),
           tags.get("White", ""), tags.get("Black", ""), tags.get("WhiteFideId", ""), tags.get("BlackFideId", ""),
           tags.get("WhiteElo", ""), tags.get("BlackElo", ""), tags.get("Result", ""), tags.get("Variant", ""),
           tags.get("TimeControl", ""), str(clks[0]) if len(clks) > 0 else "", str(clks[1]) if len(clks) > 1 else ""]
    out.write("\t".join(clean(v) for v in row) + "\n")


def convert_file(src: Path, dst: Path) -> int:
    n = 0
    proc = subprocess.Popen(["zstd", "-dc", str(src)], stdout=subprocess.PIPE, text=True, encoding="utf-8",
                            errors="replace")
    with dst.open("w") as out:
        out.write("\t".join(COLS) + "\n")
        tags: dict[str, str] = {}
        moves: list[str] = []
        in_moves = False
        for line in proc.stdout:
            line = line.rstrip("\n")
            if line.startswith("["):
                if in_moves:
                    flush(tags, moves, out)
                    n += 1
                    tags, moves, in_moves = {}, [], False
                m = TAG.match(line)
                if m:
                    tags[m.group(1)] = m.group(2)
            elif line.strip():
                in_moves = True
                if len(moves) < 3:
                    moves.append(line)
        if tags:
            flush(tags, moves, out)
            n += 1
    proc.wait()
    return n


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("lichess_db_broadcast_*.pgn.zst")):
        month = src.name[len("lichess_db_broadcast_"):len("lichess_db_broadcast_") + 7]
        dst = DST / f"{month}.tsv"
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        print(f"{month}: {convert_file(src, dst)} games", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
