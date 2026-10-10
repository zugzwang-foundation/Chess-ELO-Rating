#!/usr/bin/env python3
"""Check (c): every relative link and every [T n] / [V n] / [VT n] / [VP n] / [R n] / [E n] reference resolves.

Scope: every tracked Markdown file under docs/, plus README.md, CLAUDE.md and the
README files of analysis/ and tools/.
1. A relative Markdown link [text](path) must point to a tracked file or directory.
2. A repository path written in a code span (`docs/...`, `analysis/...`,
   `src/...`, `tests/...`, `tools/...`, `params/...`, `.github/...`) must exist.
   Records (docs/decisions/, docs/review/, docs/research/), which are never
   edited after the fact, may also name a path that existed earlier in git
   history. Paths under data/ (raw data, never committed) are not checked.
3. [R n] must be a numbered source of docs/research/ELO-RESEARCH_v1_0.md,
   [R §x] one of its numbered sections and [R Name] one of its named headings.
4. [V k] must be an item of docs/research/VERIFICATION_2026-10-09.md,
   [VT k] an item of docs/research/VERIFICATION_TITLES.md and [VP k] an item
   of docs/research/VERIFICATION_PRIOR-WORK.md.
5. [E n] must name an evidence report docs/evidence/E{n}_*.md.
6. [T n] and [Tn.m] must be a section of the current technical annex (the
   highest-versioned docs/proposal/ELO-TECHNICAL-ANNEX_vX_Y.md). Checked in
   living documents only: records cite the annex as it was when they were written.
Placeholders in citation keys ([R n], [R §x], [V k], [VT k], [VP k], [T n]) are not references.
Python standard library only.
"""
from __future__ import annotations

import re
import sys

from _repo import ROOT, existed_in_history, exists_now, latest, rel, tracked

RESEARCH = "docs/research/ELO-RESEARCH_v1_0.md"
SWEEP = "docs/research/VERIFICATION_2026-10-09.md"
TITLES = "docs/research/VERIFICATION_TITLES.md"
PRIOR = "docs/research/VERIFICATION_PRIOR-WORK.md"
RECORDS = ("docs/decisions/", "docs/review/", "docs/research/")
EXTRA = {"README.md", "CLAUDE.md", "analysis/README.md", "tools/README.md"}

PATH_TOKEN = re.compile(r"^(?:\./)?((?:docs|analysis|src|tests|tools|params|\.github)(?:/[^\s`]*)?)$")
ROOT_FILES = {"README.md", "CLAUDE.md", "LICENSE", ".gitignore", "pyproject.toml"}
PLACEHOLDER_BITS = ("NNNN", "vX_Y", "X_Y", "<", ">", "*", "…", "...", "{", "}", "YYYY")
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_SPAN = re.compile(r"`([^`]+)`")
CITE_R = re.compile(r"\[R ([^\]]+)\]")
CITE_V = re.compile(r"\[V ([^\]]+)\]")
CITE_VT = re.compile(r"\[VT ([^\]]+)\]")
CITE_VP = re.compile(r"\[VP ([^\]]+)\]")
CITE_E = re.compile(r"\[E(\d+)\]")
CITE_T = re.compile(r"\[T ?(\d+(?:\.\d+)*)\]")
PLACEHOLDER_IDS = {"n", "k", "x", "§x", "§n"}


def research_ids() -> tuple[set[int], set[str], list[str]]:
    text = (ROOT / RESEARCH).read_text(encoding="utf-8")
    sources, sections, names = set(), set(), []
    in_sources = False
    for line in text.split("\n"):
        h = re.match(r"^#{2,3} (.+)$", line)
        if h:
            title = h.group(1).strip()
            in_sources = title == "Sources"
            num = re.match(r"^(\d+(?:\.\d+)*)\.?\s", title)
            if num:
                sections.add(num.group(1))
            else:
                names.append(title.lower())
            continue
        if in_sources:
            m = re.match(r"^(\d+)\. ", line)
            if m:
                sources.add(int(m.group(1)))
    return sources, sections, names


def sweep_ids(path: str = SWEEP) -> set[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"^\| (\d+|\+) \| ", text, re.M)}


def annex_ids(path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    ids = set(re.findall(r"^## (T\d+)\b", text, re.M))
    ids |= set(re.findall(r"^### (T\d+\.\d+)\b", text, re.M))
    ids |= set(re.findall(r"^\*\*(T\d+\.\d+)[ .*]", text, re.M))
    return ids


def strip_fences(text: str) -> list[tuple[int, str]]:
    """Lines outside fenced code blocks, with their line numbers."""
    out, fenced = [], False
    for n, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((n, line))
    return out


def main() -> int:
    files = sorted(f for f in tracked() if f.endswith(".md") and (f.startswith("docs/") or f in EXTRA))
    sources, sections, names = research_ids()
    v_items = sweep_ids()
    vt_items = sweep_ids(TITLES) if (ROOT / TITLES).exists() else set()
    vp_items = sweep_ids(PRIOR) if (ROOT / PRIOR).exists() else set()
    annex = latest("docs/proposal/ELO-TECHNICAL-ANNEX_v*_*.md")
    t_ids = annex_ids(annex) if annex else set()
    errors: list[str] = []
    counts = {"links": 0, "paths": 0, "R": 0, "V": 0, "VT": 0, "VP": 0, "E": 0, "T": 0}
    evidence = {f.split("/")[-1].split("_")[0] for f in tracked() if f.startswith("docs/evidence/E") and f.endswith(".md")}

    for f in files:
        record = f.startswith(RECORDS)
        base = (ROOT / f).parent
        text = (ROOT / f).read_text(encoding="utf-8")

        def path_ok(p: str) -> bool:
            return exists_now(p) or (record and existed_in_history(p))

        for n, line in strip_fences(text):
            for m in MD_LINK.finditer(line):
                target = m.group(1)
                if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0]
                counts["links"] += 1
                resolved = rel((base / target)) if (base / target).resolve().is_relative_to(ROOT) else target
                if not path_ok(resolved):
                    errors.append(f"{f}:{n}: link target not found: {target}")
            for span in CODE_SPAN.findall(line):
                for tok in span.split():
                    tok = re.sub(r"[.,;:)\]]+$", "", tok).split("#", 1)[0]
                    tok = re.sub(r":\d+.*$", "", tok)
                    if any(b in tok for b in PLACEHOLDER_BITS):
                        continue
                    m = PATH_TOKEN.match(tok)
                    if not m and tok not in ROOT_FILES:
                        continue
                    p = m.group(1) if m else tok
                    counts["paths"] += 1
                    if not path_ok(p):
                        errors.append(f"{f}:{n}: path not found: {p}")
            prose = CODE_SPAN.sub("", line)
            for m in CITE_R.finditer(prose):
                for item in (s.strip() for s in m.group(1).split(",")):
                    if item in PLACEHOLDER_IDS:
                        continue
                    counts["R"] += 1
                    if re.fullmatch(r"\d+", item):
                        ok = int(item) in sources
                    elif item.startswith("§"):
                        ok = item[1:] in sections
                    else:
                        ok = any(t.startswith(item.lower()) for t in names)
                    if not ok:
                        errors.append(f"{f}:{n}: [R {item}] not in {RESEARCH}")
            for m in CITE_V.finditer(prose):
                for item in (s.strip() for s in m.group(1).split(",")):
                    if item in PLACEHOLDER_IDS:
                        continue
                    counts["V"] += 1
                    if item not in v_items:
                        errors.append(f"{f}:{n}: [V {item}] not an item of {SWEEP}")
            for m in CITE_VT.finditer(prose):
                for item in (s.strip() for s in m.group(1).split(",")):
                    if item in PLACEHOLDER_IDS:
                        continue
                    counts["VT"] += 1
                    if item not in vt_items:
                        errors.append(f"{f}:{n}: [VT {item}] not an item of {TITLES}")
            for m in CITE_VP.finditer(prose):
                for item in (s.strip() for s in m.group(1).split(",")):
                    if item in PLACEHOLDER_IDS:
                        continue
                    counts["VP"] += 1
                    if item not in vp_items:
                        errors.append(f"{f}:{n}: [VP {item}] not an item of {PRIOR}")
            for m in CITE_E.finditer(prose):
                counts["E"] += 1
                if f"E{m.group(1)}" not in evidence:
                    errors.append(f"{f}:{n}: [E{m.group(1)}] names no report docs/evidence/E{m.group(1)}_*.md")
            if not record:
                for m in CITE_T.finditer(prose):
                    counts["T"] += 1
                    if "T" + m.group(1) not in t_ids:
                        errors.append(f"{f}:{n}: [T{m.group(1)}] not a section of {rel(annex) if annex else 'the annex'}")

    for e in errors:
        print(e)
    print(f"check_refs: {len(files)} files; {counts['links']} links, {counts['paths']} paths, "
          f"{counts['R']} [R], {counts['V']} [V], {counts['VT']} [VT], {counts['VP']} [VP], {counts['E']} [E], {counts['T']} [T] references; "
          f"{len(errors)} unresolved")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
