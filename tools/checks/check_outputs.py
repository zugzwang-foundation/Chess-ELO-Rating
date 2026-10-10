#!/usr/bin/env python3
"""Check (a): every analysis script reproduces its committed output exactly.

The manifest analysis/outputs.json lists each script with its arguments and the
committed file its standard output must equal byte for byte. Scripts whose
input is raw data under data/ (gitignored, never committed) carry
"needs_data": true, and scripts that run for minutes (the simulator) carry
"slow": true; CI does not run either, so without --all it checks only that
their committed outputs exist. Every *.py under analysis/ must be registered,
as a script or under "modules", so that no script escapes the check.
Python standard library only.
"""
from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys

from _repo import ROOT, tracked

MANIFEST = ROOT / "analysis" / "outputs.json"


def main() -> int:
    run_all = "--all" in sys.argv[1:]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest["outputs"]
    registered = {e["script"] for e in entries} | set(manifest.get("modules", []))
    failures = 0
    for f in sorted(tracked()):
        if f.startswith("analysis/") and f.endswith(".py") and f not in registered:
            print(f"UNREGISTERED {f}: add it to analysis/outputs.json")
            failures += 1
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8", LC_ALL="C.UTF-8")
    for e in entries:
        out_path = ROOT / e["output"]
        if not out_path.exists():
            print(f"MISSING  {e['output']} (output of {e['script']})")
            failures += 1
            continue
        if e.get("needs_data") and not run_all:
            print(f"SKIPPED  {e['script']} -> {e['output']} (needs data/; run with --all locally)")
            continue
        if e.get("slow") and not run_all:
            print(f"SKIPPED  {e['script']} -> {e['output']} (slow; run with --all locally)")
            continue
        proc = subprocess.run([sys.executable, e["script"], *e.get("args", [])], cwd=ROOT,
                              capture_output=True, env=env)
        if proc.returncode != 0:
            print(f"ERROR    {e['script']} exited {proc.returncode}")
            print(proc.stderr.decode("utf-8", "replace")[-2000:])
            failures += 1
            continue
        produced = proc.stdout.decode("utf-8")
        committed = out_path.read_text(encoding="utf-8")
        if produced == committed:
            print(f"OK       {e['script']} -> {e['output']}")
            continue
        failures += 1
        print(f"DIFFERS  {e['script']} -> {e['output']}")
        diff = difflib.unified_diff(committed.splitlines(), produced.splitlines(),
                                    "committed", "produced", lineterm="", n=1)
        for i, line in enumerate(diff):
            if i == 60:
                print("  ...")
                break
            print("  " + line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
