"""No generated document holds an unfilled template expression (session ELO-15c, after E21 §10.2 printed
"{applies('equal', r0910)}" where its number belonged, because a line of its renderer lacked the f of an f-string).

Every Markdown output that analysis/outputs.json registers (the evidence reports, the generated specifications and the
analysis outputs) is scanned for a single brace that opens a Python expression: a name followed by a call, an index, an
attribute, a format specification or the closing brace. Double braces are not template expressions: they are the blanks
that section 10 and E13 keep for the championship results ({{US26_...}}), filled by hand after the event, and are left
alone. Committed files only: no data/."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPRESSION = re.compile(r"(?<!\{)\{(?!\{)\s*[A-Za-z_][A-Za-z0-9_.]*\s*[(\[}:!]")


def _documents() -> list[str]:
    manifest = json.loads((ROOT / "analysis" / "outputs.json").read_text(encoding="utf-8"))
    return sorted({e["output"] for e in manifest["outputs"] if e["output"].endswith(".md")})


def test_the_generated_documents_are_found():
    docs = _documents()
    assert "docs/evidence/E21_sourcing.md" in docs and "docs/specs/SPEC-SOURCING_v1_1.md" in docs
    assert all((ROOT / d).exists() for d in docs)


@pytest.mark.parametrize("path", _documents())
def test_no_generated_document_holds_an_unfilled_template_expression(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    hits = [text[max(0, m.start() - 40):m.end() + 40].replace("\n", " ") for m in EXPRESSION.finditer(text)]
    assert not hits, f"{path}: unfilled template expression(s): {hits[:3]}"


def test_the_pattern_catches_the_slip_and_spares_the_blanks_and_the_mathematics():
    for slip in ("On {applies('equal', r0910)} matching pages", "{n(x)}", "{name}", "{d['k']}", "{x:,}", "{a.b}",
                 "{value!r}"):
        assert EXPRESSION.search(slip), slip
    for fine in ("{{US26_PRIMARY}}", "e^{z/2}", "e^{−z/2}", "{0, 1}", "10^{s/400}", "a set {W, D, L}"):
        assert not EXPRESSION.search(fine), fine
