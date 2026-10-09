"""Shared helpers for the repository checks. Python standard library only."""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_VERSION = re.compile(r"_v(\d+)_(\d+)\.md$")


def latest(glob: str) -> Path | None:
    """Highest-versioned file matching a glob such as docs/proposal/ELO-PROPOSAL_v*_*.md."""
    best: tuple[tuple[int, int], Path] | None = None
    for path in ROOT.glob(glob):
        m = _VERSION.search(path.name)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            if best is None or key > best[0]:
                best = (key, path)
    return best[1] if best else None


@lru_cache(maxsize=1)
def tracked() -> frozenset[str]:
    """Paths tracked by git (staged files included), relative to the repository root."""
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return frozenset(out.stdout.splitlines())


@lru_cache(maxsize=1)
def tracked_dirs() -> frozenset[str]:
    dirs = set()
    for f in tracked():
        parts = f.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    return frozenset(dirs)


def exists_now(path: str) -> bool:
    p = path.rstrip("/")
    return p in tracked() or p in tracked_dirs()


@lru_cache(maxsize=None)
def existed_in_history(path: str) -> bool:
    out = subprocess.run(["git", "log", "--all", "--format=%H", "-1", "--", path.rstrip("/")],
                         cwd=ROOT, capture_output=True, text=True)
    return bool(out.stdout.strip())


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()
