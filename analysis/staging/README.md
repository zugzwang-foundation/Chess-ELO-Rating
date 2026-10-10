# analysis/staging/ — session ELO-6's new files until Freeze 3

Status: DRAFT — a working area, emptied in Phase 4 of session ELO-6 (`docs/decisions/D-0011_rulings-and-freeze-3.md`, part A, reading 1).

Freeze 2's check (`docs/decisions/D-0010_freeze-2.md`) hashes every tracked file under `params/`, `src/`, `tools/` and the top of `analysis/`, listed afresh on every run, so a new file there would fail check (a) although no frozen file changed. Until Freeze 3, the session's new code, parameter files, scripts and aggregates are committed here instead, every script registered in `analysis/outputs.json` like any other. Phase 4 moves them to their permanent paths (the v2 parameter file to `params/`, the comparison tool to `tools/`, the table and guard code to `src/layer2/`, the scripts to `analysis/` and the aggregates to `analysis/aggregates/`) and lists them in Freeze 3's manifest. Nothing here is the rating engine, and nothing here changes a frozen file.
