"""SPEC-L0 v1.5 meets the pre-agreed ratification rule (the review of session ELO-10, ELO10-QC-3).

Check (a)'s ratification output, analysis/OUTPUT_L0_ratification.md, is written by analysis/l0_ratification_check.py, a
file of Freeze 2 that reads SPEC-L0 v1.4 by its path and is not edited (D-0018, reading 5). This test applies the same
rule, with the same code, to v1.5: every rule of §3 has a verbatim citation or a fixture whose identifiers exist, and
every acceptance criterion of §7 is an executable test module. The module is imported, never changed; only its SPEC is
pointed at v1.5 for the run."""
import contextlib
import importlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V15 = ROOT / "docs" / "specs" / "SPEC-L0_fide-reference-engine_v1_5.md"


def _report_on(spec: Path) -> str:
    sys.path.insert(0, str(ROOT / "analysis"))
    try:
        rc = importlib.import_module("l0_ratification_check")
        frozen_spec = rc.SPEC
        rc.SPEC = spec
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc.main()
        finally:
            rc.SPEC = frozen_spec
    finally:
        sys.path.remove(str(ROOT / "analysis"))
    return out.getvalue()


def test_v1_5_meets_the_ratification_rule():
    report = _report_on(V15)
    assert "The pre-agreed ratification rule is met: True." in report


def test_v1_5_labels_r12_not_verified_and_changes_no_other_rule_row():
    v15 = _report_on(V15).split("\n")
    v14 = _report_on(ROOT / "docs" / "specs" / "SPEC-L0_fide-reference-engine_v1_4.md").split("\n")
    rows15 = {r.split(" | ")[0]: r for r in v15 if r.startswith("| R-")}
    rows14 = {r.split(" | ")[0]: r for r in v14 if r.startswith("| R-")}
    assert set(rows15) == set(rows14)
    changed = sorted(k for k in rows15 if rows15[k] != rows14[k])
    assert changed == ["| R-12"]
    assert rows15["| R-12"].split(" | ")[5] == "True" and rows14["| R-12"].split(" | ")[5] == "False"
