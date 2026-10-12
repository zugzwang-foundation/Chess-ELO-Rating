"""docs/DECISIONS.md, item 7 (session ELO-11): F-N01's FIDE ID, year of birth and event are placeholders, since the
computation (tests/test_l0_initial.py; analysis/l0_fixtures_report.py §5) reads only the games, the rating period and
the published rating. Kept apart from tests/test_l0_*.py, which analysis/l0_ratification_check.py counts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "fide_calculator" / "published_initial_rating.json"


def test_f_n01_keeps_no_identifier_the_computation_does_not_use():
    case = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"][0]
    assert case["id"] == "F-N01"
    for key in ("fide_id", "birth_year", "event_id", "event", "start", "end"):
        assert str(case[key]).startswith("<") and str(case[key]).endswith(">"), key
    assert "<FIDE ID>" in case["calculation_url"] and "<event ID>" in case["report_url"]
    assert case["rating_period"] == "2025-12" and case["published_list"]["2025-12"]["rating"] == 1922
