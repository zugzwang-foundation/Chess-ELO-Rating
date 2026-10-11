"""Ruling R85 (docs/decisions/D-0018_rulings-on-elo-9-questions.md, a founder decision): future fetches identify the
project with one User-Agent, with no email, set in the module the fetch tools share (tools/data/politeness.py); every
fetch tool outside the freezes takes it from there, and the frozen ones are not edited. The frozen tools are read from
the freeze records E3 and E13 print. The test reads the module and the tools' sources: it opens no connection and
fetches nothing."""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import politeness  # noqa: E402

UA = "Zugzwang-Elo-research (+https://github.com/zugzwang-foundation/Chess-ELO-Rating)"
FREEZE_PAGES = ("docs/evidence/E3_us-championship-2026.md", "docs/evidence/E13_us-championship-2026-freeze-3.md")


def frozen_fetch_tools() -> set[str]:
    """The fetch tools a freeze lists, by file name, from the hash tables of E3 (Freeze 1 and 2) and E13 (Freezes 3 to
    3d)."""
    names = set()
    for page in FREEZE_PAGES:
        text = (ROOT / page).read_text(encoding="utf-8")
        names |= set(re.findall(r"^\| `tools/data/(fetch_[a-z0-9_]+\.py)` \| `[0-9a-f]{64}` \|", text, re.M))
    return names


def test_the_user_agent_is_r85s_and_carries_no_email():
    assert politeness.USER_AGENT == UA
    assert "@" not in politeness.USER_AGENT and "mailto" not in politeness.USER_AGENT.lower()


def test_the_headers_helper_puts_the_user_agent_first():
    assert politeness.headers() == {"User-Agent": UA}
    extra = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://ratings.fide.com/"}
    assert politeness.headers(extra) == {"User-Agent": UA, **extra}
    assert list(politeness.headers(extra))[0] == "User-Agent"


def test_every_fetch_tool_outside_the_freezes_takes_its_user_agent_from_the_module():
    frozen = frozen_fetch_tools()
    assert frozen == {"fetch_fide_calculations.py", "fetch_fide_lists.py", "fetch_lichess_broadcasts.py"}
    tools = sorted((ROOT / "tools" / "data").glob("fetch_*.py"))
    outside = [t for t in tools if t.name not in frozen]
    assert len(outside) == 5
    for t in outside:
        src = t.read_text(encoding="utf-8")
        ast.parse(src)
        assert "Mozilla" not in src and "User-Agent\": \"" not in src, t.name
        assert "import politeness" in src, t.name
        assert re.search(r"politeness\.(headers\(|USER_AGENT)", src), t.name
