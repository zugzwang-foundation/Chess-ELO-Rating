#!/usr/bin/env python3
"""E20, part 1: the greats on FIDE's lists (SPEC-GREATS v1.0 §3 to §5; session ELO-9, Phase 3; needs data/).

For the players SPEC-GREATS §2 fixed (analysis/aggregates/GREATS_players.json), on the lists the data probe found
legitimately available (docs/research/DATA-PROBE_greats.md):
- **the sources checked first** (§3): OlimpBase's transcription of FIDE's four lists of 2001 against FIDE's own files of
  the same dates, player by player; FIDE's old files, as converted, against FIDE's per-player histories the probe read;
  FIDE's printed top lists against the top three computed by SPEC-GREATS §2's rule on the same dates; the requests of
  the old lists' first run, whose send times the tool logged before its wait, reconstructed; and every request of the
  session's fetch tools to ratings.fide.com and the Internet Archive, with both slips and the gaps since (R75,
  analysis/probe_greats_extract.py);
- **(i) the published series** (§4): per player, the first and last list on which the player appears, their number, the
  peak published rating and the lists on which it stood, and the lists ranked 1st, 1st to 3rd and 1st to 10th by §2's
  rule (printed ranks where FIDE's top list survives, computed otherwise), July 1971 to December 2019; the series itself
  goes to the local cache data/interim/greats/series.json (gitignored, R72);
- **(ii) dominance** (§5): on every list date from July 1971 to December 2019, the ratings of the list's #1, #2 and #10
  (printed or computed), each ranked player's gap to #2 and to #10, and each player's best three consecutive years
  (36 months, ranked on every list of the window, so that a window reaching past December 2019, where §2 defines no
  rank, does not count) by the mean gap to #2, with the mean gap to #10 in it, beside the best window by the mean gap
  to #10.
Writes analysis/aggregates/E20_greats_lists.json: per player one published rating (the peak) and counts, gaps and
dates; no list and no series. Python standard library only.

Usage: python3 analysis/e20_greats_lists_extract.py > analysis/aggregates/E20_greats_lists.json
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import greats_select as gs  # noqa: E402  (SPEC-GREATS §2's lists, keys and activity rule)
import probe_greats_extract as pg  # noqa: E402  (the session's requests and their gaps, R75)

SELECTED = ROOT / "analysis" / "aggregates" / "GREATS_players.json"
PROBE = ROOT / "data" / "raw" / "probe"
OLD_MAN = ROOT / "data" / "raw" / "fide_old" / "MANIFEST.tsv"
CACHE = ROOT / "data" / "interim" / "greats" / "series.json"
SERIES_LAST = "2026-10"
WINDOW = 36
RANKS_END = "2020-01"                                # the month after the last ranked list (SPEC-GREATS §2)
MON = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
                                   1)}


def check_olimpbase() -> list[dict]:
    """OlimpBase's lists of 2001 against FIDE's own files of the same dates, player by player."""
    out = []
    for p in ("2001-01", "2001-04", "2001-07", "2001-10"):
        ob = {r["id"]: r for r in gs.rows(gs.OB / f"{p}.tsv") if r["id"]}
        fd = {r["id"]: r for r in gs.rows(gs.OLD / f"{p}.tsv")}
        common = set(ob) & set(fd)
        out.append({"list": p, "olimpbase": len(ob), "fide": len(fd), "common": len(common),
                    "rating_equal": sum(1 for k in common if ob[k]["rating"] == fd[k]["rating"]),
                    "flag_equal": sum(1 for k in common if ob[k]["flag"] == fd[k]["flag"])})
    return out


def check_histories() -> dict:
    """FIDE's old files, as converted, against the per-player histories FIDE's profile pages gave the probe."""
    checked, differ = 0, []
    for pid in ("1503014", "4100018", "4100026"):
        for x in json.loads((PROBE / f"fide_chart_{pid}_all.html").read_text(encoding="utf-8-sig")):
            y, m = x["date_2"].split("-")
            period = f"{y}-{MON[m]:02d}"
            path = gs.OLD / f"{period}.tsv"
            if not path.exists():
                continue
            row = next((r for r in gs.rows(path) if r["id"] == pid), None)
            checked += 1
            if row is None or row["rating"] != x["rating"]:            # the size of the difference only (ELO9-QC-4)
                differ.append({"id": pid, "list": period,
                               "history_minus_file": int(x["rating"]) - int(row["rating"]) if row else None})
    return {"points": checked, "differ": differ}


def fetch_slip() -> dict:
    """The old lists' first run logged each request's time before its wait (SPEC-GREATS §3): the send time of request k
    is reconstructed as max(logged k, logged k-1 + 4 s), and the gaps between sends are counted."""
    with OLD_MAN.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    t = [datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in rows]
    first_run = [i for i in range(len(rows)) if t[i] <= datetime(2026, 10, 11, 11, 6, 18)]
    send = []
    for j, i in enumerate(first_run):
        send.append(t[i] if j == 0 else max(t[i], t[first_run[j - 1]] + timedelta(seconds=4)))
    gaps = [(send[j] - send[j - 1]).total_seconds() for j in range(1, len(send))]
    return {"requests": len(first_run), "first": rows[first_run[0]]["fetched_utc"],
            "last": rows[first_run[-1]]["fetched_utc"], "gaps_under_2s": sum(1 for g in gaps if g < 2),
            "smallest_gap_s": min(gaps) if gaps else None}


def main() -> int:
    sel = json.loads(SELECTED.read_text(encoding="utf-8"))
    keys = {p["key"]: p for p in sel["players"]}
    lists = gs.full_lists() + [(p.stem, "FIDE", p) for p in sorted(gs.NEW.glob("*.tsv"))
                               if gs.LAST < p.stem <= SERIES_LAST]
    link: dict[str, str] = {}
    for path in sorted(gs.OB.glob("2001-*.tsv")):
        for r in gs.rows(path):
            if r["id"]:
                link[r["name"]] = r["id"]
    series: dict[str, dict[str, int]] = defaultdict(dict)
    entries: dict[str, list[tuple]] = {}
    games: dict[str, dict[str, int]] = defaultdict(dict)
    for period, src, path in lists:
        es = []
        for r in gs.rows(path):
            key = (link.get(r["name"]) or f"name:{r['name']}") if src == "OlimpBase" else r["id"]
            g = r.get("games", "")
            games[key][period] = int(g) if g.isdigit() else 0
            rating = r.get("rating", "")
            if rating.isdigit() and int(rating) > 0:
                es.append((key, int(rating), r.get("flag", "")))
                if key in keys:
                    series[key][period] = int(rating)
        entries[period] = es
    dates = [p for p, _s, _f in lists]
    rank_dates = [d for d in dates if d <= gs.LAST]

    def ranked_on(period: str) -> list[tuple[str, int]]:
        """(key, rating) of the players ranked on a full list by SPEC-GREATS §2's rule."""
        recent = [d for d in dates if 0 <= gs.months_between(d, period) < 12]
        need = 0 if period < gs.TOP_RULE_FROM else (4 if period < gs.ONE_GAME_FROM else 1)
        return [(k, r) for k, r, fl in entries[period] if fl not in gs.INACTIVE
                and (need == 0 or sum(games[k].get(d, 0) for d in recent) >= need)]

    printed = {p.stem: gs.rows(p) for p in sorted(gs.TOP.glob("*.tsv")) if gs.PRINTED_FROM <= p.stem <= gs.LAST}
    board: dict[str, dict] = {}                      # list date -> #1, #2, #10 and each selected player's rank
    for period in sorted(set(rank_dates) | set(printed)):
        if period in printed:
            top = printed[period]
            ratings = [int(r["rating"]) for r in top]
            ranks = {r["id"]: int(r["rank"]) for r in top if r["id"] in keys}
            vals = {r["id"]: int(r["rating"]) for r in top if r["id"] in keys}
            src = "printed"
        else:
            rk = ranked_on(period)
            ratings = sorted((r for _k, r in rk), reverse=True)
            ranks = {k: 1 + sum(1 for x in ratings if x > r) for k, r in rk if k in keys}
            vals = {k: r for k, r in rk if k in keys}
            src = "computed"
        tie3 = src == "computed" and sum(1 for x in ratings if x >= ratings[2]) > 3     # several share 3rd
        board[period] = {"source": src, "r1": ratings[0], "r2": ratings[1], "r10": ratings[9], "ranks": ranks,
                         "ratings": vals, "tie3": tie3, "third": ratings[2]}
    board_dates = sorted(board)
    players = []
    for key, p in sorted(keys.items(), key=lambda kv: (kv[1]["first_top3"], kv[1]["name"])):
        s = series.get(key, {})
        peak = max(s.values()) if s else None
        ranks = {d: board[d]["ranks"][key] for d in board_dates if key in board[d]["ranks"]}
        gap2 = {d: board[d]["ratings"][key] - board[d]["r2"] for d in ranks}
        gap10 = {d: board[d]["ratings"][key] - board[d]["r10"] for d in ranks}

        def best(gap: dict[str, int]) -> dict | None:
            top, scores = None, []
            for t in board_dates:
                # a window reaching past December 2019 holds lists on which no rank is defined (SPEC-GREATS §2, §5)
                if t not in gap or gs.months_between(t, RANKS_END) < WINDOW:
                    continue
                win = [d for d in board_dates if 0 <= gs.months_between(t, d) < WINDOW]
                if any(d not in gap for d in win):
                    continue
                score = sum(gap[d] for d in win) / len(win)
                scores.append(score)
                if top is None or score > top["mean"]:
                    top = {"first": win[0], "last": win[-1], "lists": len(win), "mean": round(score, 1),
                           "mean_gap2": round(sum(gap2[d] for d in win) / len(win), 1),
                           "mean_gap10": round(sum(gap10[d] for d in win) / len(win), 1),
                           "lists_at_1": sum(1 for d in win if ranks[d] == 1)}
            if top is not None:                  # ELO9-STAT-5: the maximum over how many windows, and their median
                ss = sorted(scores)
                mid = len(ss) // 2
                top["windows"] = len(ss)
                top["median_window_mean"] = round(ss[mid] if len(ss) % 2 else (ss[mid - 1] + ss[mid]) / 2, 1)
            return top
        top3 = [d for d, r in ranks.items() if r <= 3]
        span = [d for d in rank_dates if s and min(s) <= d <= max(s)]
        players.append({
            "key": key, "fide_id": p["fide_id"], "name": p["name"], "federation": p["federation"],
            "top3_only_by_a_shared_third": bool(top3) and all(ranks[d] == 3 and board[d]["tie3"] for d in top3),
            "top3_lists_shared_third": sorted(d for d in top3 if ranks[d] == 3 and board[d]["tie3"]),
            "absent_from_lists_in_span": [d for d in span if d not in s and d in entries],
            "first_list": min(s) if s else None, "last_list": max(s) if s else None, "lists": len(s),
            "peak": peak, "peak_lists": [d for d, r in sorted(s.items()) if r == peak],
            "lists_rank1": sum(1 for r in ranks.values() if r == 1),
            "lists_top3": sum(1 for r in ranks.values() if r <= 3),
            "lists_top10": sum(1 for r in ranks.values() if r <= 10),
            "best_by_gap2": best(gap2), "best_by_gap10": best(gap10)})
    # ELO9-STAT-3: lists that lack a player ranked 1st to 3rd on the ranked lists either side of them
    names = {k: v["name"] for k, v in keys.items()}
    missing_top3 = []
    for key in keys:
        rk = {d: board[d]["ranks"][key] for d in board_dates if key in board[d]["ranks"]}
        for d in board_dates:
            if key in board[d]["ranks"] or not rk:
                continue
            before = [x for x in rk if x < d]
            after = [x for x in rk if x > d]
            if before and after and rk[max(before)] <= 3 and rk[min(after)] <= 3:
                missing_top3.append({"list": d, "absent": names[key], "ranked_before": rk[max(before)],
                                     "ranked_after": rk[min(after)],
                                     "top3_on_the_list": sorted([[names[k], r] for k, r in board[d]["ranks"].items()
                                                                 if r <= 3], key=lambda x: (x[1], x[0]))})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({k: series.get(k, {}) for k in keys}, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    out = {"spec": "docs/specs/SPEC-GREATS_v1_0.md", "selected": "analysis/aggregates/GREATS_players.json",
           "checks": {"olimpbase_vs_fide_2001": check_olimpbase(), "fide_files_vs_histories": check_histories(),
                      "printed_vs_computed_top3": {k: v for k, v in sel["printed_vs_computed"].items() if k != "unequal"}
                      | {"unequal": [a["list"] for a in sel["printed_vs_computed"]["unequal"]]},
                      "old_lists_fetch_slip": fetch_slip(), "session_politeness": pg.session_politeness()},
           "lists": {"series": {"first": dates[0], "last": dates[-1], "dates": len(dates)},
                     "ranks": {"first": board_dates[0], "last": board_dates[-1], "dates": len(board_dates),
                               "printed": sum(1 for d in board_dates if board[d]["source"] == "printed")}},
           "window_months": WINDOW, "players": players,
           "lists_missing_a_top3_player": sorted(missing_top3, key=lambda x: (x["list"], x["absent"])),
           # ELO9-STAT-3: on FIDE's printed lists ties are broken in FIDE's order; who shared the 3rd's rating there
           "printed_ties_at_third": [{"list": d, "name": r["name"], "printed_rank": int(r["rank"]),
                                      "selected": (r["id"] or f"name:{r['name']}") in keys}
                                     for d, top in sorted(printed.items())
                                     for r in top if int(r["rank"]) > 3 and int(r["rating"]) == board[d]["third"]]}
    json.dump(out, sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
