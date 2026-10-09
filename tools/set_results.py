#!/usr/bin/env python3
"""Record one round's results in an event file (tools/events/*.json), board by board.

Results are read from the organiser's official page (for the 2026 U.S. Championships:
https://saintlouischessclub.org/event/2026-us-chess-championships/) and entered in
board order: 1-0, 1/2-1/2 (or 0.5-0.5), 0-1, or - for a game not finished. The UTC
time of entry is recorded beside each result. Python standard library only.

Usage: python3 tools/set_results.py tools/events/us_championship_2026.json 2 1-0 1/2-1/2 0-1 - 1/2-1/2 1-0
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ALIASES = {"1-0": "1-0", "0-1": "0-1", "1/2-1/2": "1/2-1/2", "0.5-0.5": "1/2-1/2", "½-½": "1/2-1/2", "-": None}


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    path, rnd, given = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
    event = json.loads(path.read_text(encoding="utf-8"))
    boards = sorted((g for g in event["games"] if g["round"] == rnd), key=lambda g: g["board"])
    if len(given) != len(boards):
        print(f"round {rnd} has {len(boards)} boards; {len(given)} results given", file=sys.stderr)
        return 2
    if any(r not in ALIASES for r in given):
        print(f"results must be one of {sorted(ALIASES)}", file=sys.stderr)
        return 2
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    read = {(x["round"], x["board"]): x for x in event.get("results_read", [])}
    for g, r in zip(boards, given):
        g["result"] = ALIASES[r]
        if g["result"] is not None:
            read[(rnd, g["board"])] = {"round": rnd, "board": g["board"], "result": g["result"], "read_utc": now}
    event["results_read"] = [read[k] for k in sorted(read)]
    path.write_text(json.dumps(event, indent=1) + "\n", encoding="utf-8")
    done = sum(1 for g in event["games"] if g["result"])
    print(f"{path}: round {rnd} recorded; {done} of {len(event['games'])} games have a result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
