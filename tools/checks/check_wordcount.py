#!/usr/bin/env python3
"""Check (d): the proposal body is at most 4,500 words by ELO-2's strict count,
and the plain-language brief is at most 900 words (D15, D-0005).

The strict count, as reconstructed so that it reproduces the 4,751 words the
ELO-2 close-out records for the proposal at commit 7a94622:
  - the body runs from the "## 1 " heading to the first "## Appendix" heading;
  - fenced code (the system diagram), table rows, headings and horizontal rules
    are excluded;
  - every other whitespace-separated token counts as one word, citations and
    formula symbols included.
The proposal checked is the highest-versioned docs/proposal/ELO-PROPOSAL_vX_Y.md.
The brief (highest-versioned docs/proposal/ELO-BRIEF_vX_Y.md) is counted whole:
every line except headings, horizontal rules and table separator rows, with
table cells included, so that no part of it escapes the cap.
Python standard library only.
"""
from __future__ import annotations

import re
import sys

from _repo import latest, rel

BODY_CAP = 4500
BRIEF_CAP = 900


def strict_words(text: str, start: str, end: str | None) -> int:
    words, on, fenced = 0, False, False
    for line in text.split("\n"):
        if re.match(start, line):
            on = True
        if end and on and re.match(end, line):
            break
        if not on:
            continue
        s = line.strip()
        if s.startswith("```"):
            fenced = not fenced
            continue
        if fenced or s.startswith("|") or s.startswith("#") or s == "---":
            continue
        words += len(line.split())
    return words


def brief_words(text: str) -> int:
    words = 0
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#") or s == "---" or re.fullmatch(r"\|[-:| ]+\|", s):
            continue
        words += len(s.replace("|", " ").split())
    return words


def main() -> int:
    proposal = latest("docs/proposal/ELO-PROPOSAL_v*_*.md")
    if proposal is None:
        print("check_wordcount: no proposal found")
        return 1
    text = proposal.read_text(encoding="utf-8")
    body = strict_words(text, r"^## 1 ", r"^## Appendix")
    summary = strict_words(text, r"^## 1 ", r"^## 2 ")
    ok = body <= BODY_CAP
    print(f"{rel(proposal)}: body {body} words (cap {BODY_CAP}) {'OK' if ok else 'FAIL'}; summary {summary} words (for information)")
    brief = latest("docs/proposal/ELO-BRIEF_v*_*.md")
    if brief is not None:
        n = brief_words(brief.read_text(encoding="utf-8"))
        print(f"{rel(brief)}: {n} words (cap {BRIEF_CAP}) {'OK' if n <= BRIEF_CAP else 'FAIL'}")
        ok = ok and n <= BRIEF_CAP
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
