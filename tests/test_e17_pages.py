"""E17's pages carry the ELO-7 brief's fixed wording above every table (session ELO-7, Phases 2 and 3): the evidence
page, the one-page summary and the proposal's Appendix G.

"Every table carries the fixed wording 'under this rule, with the same results — not anyone's true strength'": the last
line of text before each table of each page must contain it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED = "Under this rule, with the same results — not anyone's true strength."
PAGES = ["docs/evidence/E17_top100-replay.md", "docs/evidence/E17_summary.md", "analysis/OUTPUT_E17_appendix.md"]


def tables_without_the_wording(text: str) -> list[str]:
    lines = text.split("\n")
    bad = []
    for i, s in enumerate(lines):
        if s.startswith("|") and (i == 0 or not lines[i - 1].startswith("|")):
            before = [x for x in lines[:i] if x.strip()]
            if not before or FIXED not in before[-1]:
                bad.append(s)
    return bad


def test_every_table_carries_the_fixed_wording():
    for page in PAGES:
        text = (ROOT / page).read_text(encoding="utf-8")
        assert "\n|" in text, page
        assert tables_without_the_wording(text) == [], page


def test_the_check_catches_a_table_without_it():
    assert tables_without_the_wording("Some text.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n") == ["| a | b |"]
    assert tables_without_the_wording(f"*{FIXED}*\n\n| a | b |\n|---|---|\n") == []
