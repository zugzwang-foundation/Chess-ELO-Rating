"""Section 10's reading (session ELO-12): the paragraph after the forecast test's table, written before any result with
its content fixed in advance (D-0015, reading 2; D-0016, R66), and the body's cap once its blanks are filled.

Nothing fills the blanks but the results session, by hand, from the values E13 prints once both 2026 events are complete
(D-0012, item 4). Until then each blank counts one word in check (d); this test counts each at the most words its
printed value can take, so that the body stays within 4,500 words once the paragraph is filled. Once filled, the same
test reads the paragraph's fixed words around the values."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("tools/checks", "tools", "analysis"):
    sys.path.insert(0, str(ROOT / sub))

import check_wordcount as cw  # noqa: E402  (check (d), read only)
import compare_event_v3c as v3c  # noqa: E402  (Freeze 3c's tool: the three sentences, read only)
import e13_us_championships_freeze3c as e13c  # noqa: E402  (E13's page script: how an interval prints, read only)

BLANK = re.compile(r"\{\{(US26_[A-Z0-9_]+)\}\}")
LEAD = "**The reading, fixed in advance.**"
CROSSED = ("US26_POOLED_LL_DIFF_CROSSED", "US26_POOLED_LL_DIFF_SHARED_CROSSED", "US26_POOLED_R3_LL_DIFF_CROSSED")


def _latest(pattern: str) -> Path:
    def key(p: Path):
        m = re.search(r"_v(\d+)_(\d+)\.md$", p.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
    return max(ROOT.glob(pattern), key=key)


TEXT = _latest("docs/proposal/ELO-PROPOSAL_v*_*.md").read_text(encoding="utf-8")


def _section10() -> str:
    return TEXT.split("\n## 10 ")[1].split("\n## 11 ")[0]


def _paragraph() -> str:
    return next(x for x in _section10().split("\n") if x.startswith(LEAD))


def _counted_lines(text: str) -> list[str]:
    """The lines check (d) counts in the body: from "## 1 " to the first "## Appendix", without table rows, headings,
    fenced code and rules (tools/checks/check_wordcount.py)."""
    out, on, fenced = [], False, False
    for line in text.split("\n"):
        if re.match(r"^## 1 ", line):
            on = True
        if on and re.match(r"^## Appendix", line):
            break
        if not on:
            continue
        s = line.strip()
        if s.startswith("```"):
            fenced = not fenced
            continue
        if fenced or s.startswith("|") or s.startswith("#") or s == "---":
            continue
        out.append(line)
    return out


def _filled_words(name: str) -> int:
    """The most words a blank's printed value takes: D-0015's longest sentence, each number one word; an interval as
    E13 prints it, "lo to hi"."""
    if name == "US26_PRIMARY":
        return max(len(s.format(d="+0.0000", lo="+0.0000", hi="+0.0000").split()) for s in v3c.SENTENCES.values())
    if name in CROSSED:
        return len(e13c.iv((0.0, 0.0)).split())
    raise AssertionError(f"no filled length known for {{{{{name}}}}} in the body's counted text")


def test_the_paragraph_follows_the_forecast_tests_table_with_its_content_fixed_in_advance():
    sec = _section10()
    para = _paragraph()
    assert sec.index(para) > sec.index("| fixed by the pairings: were (b′)'s forecasts exactly right")
    assert "{{US26_READING}}" not in TEXT
    # the primary endpoint first, read with its interval over games and one of D-0015's three sentences
    lead = "The primary endpoint, the pooled Brier difference with its interval over games"
    assert para.index(lead) < para.index("Every log-loss line")
    if "{{US26_PRIMARY}}" in para:
        assert "one of three sentences fixed in advance: {{US26_PRIMARY}} Every log-loss line" in para
    else:
        assert sum(s.split("{d}")[0] in para for s in v3c.SENTENCES.values()) == 1
    # every log-loss line with its crossed interval over players, then the small-sample statement
    assert "Every log-loss line is read with its crossed interval over players" in para
    assert all(f"{{{{{b}}}}}" in para for b in CROSSED) or not BLANK.search(para)
    assert para.index("Every log-loss line") < para.index("As stated in advance, the sample is small")
    # the pre-registration named; 132 games illustrate and cannot test
    assert "pre-registered before any result was read" in para
    assert para.endswith("132 games illustrate the rungs and cannot test them.")


def test_the_body_stays_within_its_cap_once_section_10s_reading_is_filled():
    lines = _counted_lines(TEXT)
    body = sum(len(x.split()) for x in lines)
    assert body == cw.strict_words(TEXT, r"^## 1 ", r"^## Appendix")          # the same count as check (d)
    blanks = [b for x in lines for b in BLANK.findall(x)]
    assert set(blanks) <= {"US26_PRIMARY", *CROSSED}
    filled = body + sum(_filled_words(b) - 1 for b in blanks)
    assert filled <= cw.BODY_CAP, f"body {body}, {filled} once filled, cap {cw.BODY_CAP}"
