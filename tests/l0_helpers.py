"""Shared helpers for the SPEC-L0 acceptance tests A-1 to A-10 (docs/specs/SPEC-L0_fide-reference-engine_v1_0.md, §7).

The tests are written before the engine. While src/layer0/ does not exist, every
test that needs the engine is skipped; once the package exists it is imported
unconditionally, so that an import error fails the run instead of skipping it.
Tables are read from the transcription at test time, never retyped.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SWEEP = ROOT / "docs" / "research" / "VERIFICATION_2026-10-09.md"
TITLES = ROOT / "docs" / "research" / "VERIFICATION_TITLES.md"


def require_layer0():
    if not (ROOT / "src" / "layer0" / "__init__.py").exists():
        pytest.skip("src/layer0 is not written yet: the SPEC-L0 acceptance tests precede the engine",
                    allow_module_level=True)
    import layer0
    return layer0


def fixture(*parts: str) -> dict:
    return json.loads(FIXTURES.joinpath(*parts).read_text(encoding="utf-8"))


def dec(s: str) -> Decimal:
    return Decimal("0" + s if s.startswith(".") else s)


def month_before(month: str) -> str:
    y, m = int(month[:4]), int(month[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _table_after(text: str, marker: str) -> list[list[str]]:
    lines = text[text.index(marker):].split("\n")[1:]
    rows: list[list[str]] = []
    for line in lines:
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    return rows[2:]


def _p_dp(rows: list[list[str]]) -> dict[Decimal, int]:
    out = {}
    for r in rows:
        for i in range(0, len(r) - 1, 2):
            if r[i]:
                out[dec(r[i])] = int(r[i + 1])
    return out


def transcribed_811() -> dict[Decimal, int]:
    """Table 8.1.1, p -> dp, as transcribed in [V 1]."""
    return _p_dp(_table_after(SWEEP.read_text(encoding="utf-8"), "**Table 8.1.1 (verbatim layout"))


def transcribed_149() -> dict[Decimal, int]:
    """Table 1.4.9 of the Title Regulations, as transcribed in [VT 1]."""
    return _p_dp(_table_after(TITLES.read_text(encoding="utf-8"), "> 1.4.9 Table"))


def transcribed_812() -> list[tuple[int, int | None, Decimal, Decimal]]:
    """Table 8.1.2 as (lowest D, highest D or None for '> 735', PD of H, PD of L), as transcribed in [V 1]."""
    out = []
    for r in _table_after(SWEEP.read_text(encoding="utf-8"), "**Table 8.1.2 (verbatim layout"):
        for i in range(0, len(r) - 2, 3):
            if not r[i]:
                continue
            if r[i].startswith(">"):
                lo, hi = int(r[i][1:].strip()) + 1, None
            else:
                a, b = r[i].split("-")
                lo, hi = int(a), int(b)
            out.append((lo, hi, dec(r[i + 1]), dec(r[i + 2])))
    return sorted(out, key=lambda t: t[0])


def uscc_2025_inputs(layer0):
    """The 2025 US Championship from tests/fixtures/validation/us_championship_2025.json as next_list inputs:
    (period, lists, tournaments, games) with the October 2025 list as the list in force and the previous list."""
    from datetime import date

    fx = fixture("validation", "us_championship_2025.json")
    ev = fx["event"]
    lists = {"2025-10": {p["fide_id"]: layer0.ListEntry(rating=p["list_2025_10"]["rating"], k=p["list_2025_10"]["k"])
                         for p in fx["players"]}}
    tid = str(ev["event_id"])
    tournaments = [layer0.Tournament(tid, date.fromisoformat(ev["start"]), date.fromisoformat(ev["end"]),
                                     ev["rating_period"], ev["chapter"])]
    games = [layer0.Game(tid, g["round"], g["white"], g["black"], g["result"]) for g in fx["games"]]
    return ev["rating_period"], lists, tournaments, games
