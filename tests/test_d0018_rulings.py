"""The rulings of docs/decisions/D-0018_rulings-on-elo-9-questions.md as the documents carry them (session ELO-10):
R81 (the backward replay without a headline, its caveat and its figures in E20 §5 only), R82 (the tie rule's asymmetry
stated), R83 (OlimpBase's label on every file holding figures derived from its transcription, and README's carve-out),
R84 (FIDE's written permission to be requested, no date), R86 (Appendix F.3, from E20 only) and R87 (annex T1's guard
row). Every check reads committed files only."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e20_greats_report as rep  # noqa: E402

LABEL = ("Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this "
         "repository's CC BY 4.0 or Apache-2.0 licences.")
REPLAY = json.loads((ROOT / "analysis" / "aggregates" / "E20_greats_replay.json").read_text(encoding="utf-8"))
E20 = (ROOT / "docs" / "evidence" / "E20_greats.md").read_text(encoding="utf-8")
APPENDIX = (ROOT / "analysis" / "OUTPUT_E20_appendix.md").read_text(encoding="utf-8")
DOCS = ("docs/evidence/E20_greats.md", "docs/proposal/ELO-PROPOSAL_v1_0.md", "analysis/OUTPUT_E20_appendix.md",
        "docs/specs/SPEC-GREATS_v1_0.md", "docs/research/DATA-PROBE_greats.md", "docs/review/REDTEAM_v1_0.md",
        "docs/decisions/D-0018_rulings-on-elo-9-questions.md")
AGGREGATES = ("analysis/aggregates/GREATS_players.json", "analysis/aggregates/E20_greats_lists.json",
              "analysis/aggregates/PROBE_greats.json")


def _brief(text: str) -> str:
    return text.split("**In brief.**")[1].split("\n## 1 ")[0]


def _section(text: str, n: int) -> str:
    return text.split(f"\n## {n} ")[1].split(f"\n## {n + 1} ")[0]


def test_r81_the_backward_replay_has_no_headline_and_its_figures_stay_in_section_5():
    s = REPLAY["summary"]
    mean = rep.sgn(s["mean_difference"], 1)
    top = max(r["highest_rung2"]["rating"] for r in REPLAY["players"])
    for text in (_brief(E20), APPENDIX):
        assert mean not in text and str(top) not in text
        assert "highest under the 2025 table" not in text                 # no per-player table under the 2025 table
    assert "The headlines are the lead over one's own era (§3) and the replay's validation and findings" in E20
    sec5 = _section(E20, 5)
    assert mean in sec5 and str(top) in sec5
    o = REPLAY["calibration"]["overall"]
    threshold = (o["table_812"]["mean"] + o["table_2025"]["mean"]) / 2
    assert ("The players were chosen because they reached the top three, so their results run ahead of any forecast. "
            f"That lifts both tables' residuals alike; a lift above {threshold:.3f} a game would reverse which table "
            "sits nearer the results. Only an unselected sample of the era, which FIDE's tournament reports would "
            "provide, can say which table fits it.") in sec5
    assert ("Here a table fitted on games of March to December 2024 sits further from these 2008-2019 results than "
            "FIDE's own. That is consistent with calibration changing between eras, with the table's thin support at "
            "the top, or with a sample chosen for success; it proves none of them.") in sec5
    assert "No estimate of the table's own error at the top" in sec5 and "a handful of games (E19 §3)" in sec5
    # Appendix I: two sentences on the backward replay, pointing to E20 §5
    para = next(x for x in APPENDIX.split("\n\n") if x.startswith("E20 §5 also replays"))
    assert para.count(". ") + 1 == 2 and "E20 §5 only" in para


def test_r82_the_tie_rules_asymmetry_and_its_source_are_stated():
    for text in (E20, APPENDIX):
        assert "Polugaevsky, Mecking, Beliavsky, Vaganian, Sokolov and Salov" in text
        assert "Svidler, printed 4th on the 3rd's rating in October 2006, is not among the 36" in text
        assert "R82" in text and "multiples of five" in text and "FIDE's printed order decides" in text


def test_r83_every_file_with_olimpbase_derived_figures_carries_the_label_and_readme_names_it():
    licence = (ROOT / "README.md").read_text(encoding="utf-8").split("## Licences")[1]
    assert LABEL in licence
    for f in DOCS + AGGREGATES:
        assert f"`{f}`" in licence, f
    for f in DOCS:
        if f == "docs/review/REDTEAM_v1_0.md":
            continue            # a verbatim record: the session's review addendum carries the label (D-0018, reading 11 (d))
        assert LABEL in (ROOT / f).read_text(encoding="utf-8"), f
    for f in AGGREGATES:
        assert json.loads((ROOT / f).read_text(encoding="utf-8"))["terms"] == LABEL, f
    # every table crediting OlimpBase (R77) carries the label on the same line (R83)
    for text in (E20, APPENDIX):
        credits = [x for x in text.split("\n") if x.startswith("Lists to 2000: OlimpBase's transcription")]
        assert credits and all(x.endswith(LABEL) for x in credits)


def test_r84_fides_permission_is_to_be_requested_and_the_row_gives_no_date():
    probe = (ROOT / "docs" / "research" / "DATA-PROBE_greats.md").read_text(encoding="utf-8")
    row = next(x for x in probe.split("\n") if x.startswith("| FIDE (ratings.fide.com"))
    status, why = row.split(" | ")[4:6]
    assert "FIDE's written permission to be requested" in status and "until FIDE answers nothing changes" in why
    assert not re.search(r"\d{4}-\d\d", status + why) and "not sought" not in row
    for text in (E20, APPENDIX):
        assert "its written permission is to be requested" in text and "has not been sought (FIDE" not in text


def test_r86_appendix_f3_cites_e20_only():
    prop = (ROOT / "docs" / "proposal" / "ELO-PROPOSAL_v1_0.md").read_text(encoding="utf-8")
    f3 = prop.split("**F.3 From the greats' replay, 2008–2019.**")[1].split("\n---\n")[0]
    assert set(re.findall(r"\[E(\d+)", f3)) == {"20"}
    assert "28 June 2009" in f3 and "9 July 2009" in f3 and "a date no text gives" in f3
    assert "towards +∞ on the lists to July 2018 and away from zero from November 2018" in f3
    assert "January 2009 is the exception" in f3 and "41 points" in f3 and "Nothing has been sent to FIDE" in f3
    assert "a date no text gives" in E20 and "before the text of 2022 said \"away from zero\"" in E20


def test_r87_annex_t1s_guard_row():
    annex = (ROOT / "docs" / "proposal" / "ELO-TECHNICAL-ANNEX_v1_0.md").read_text(encoding="utf-8")
    row = next(x for x in annex.split("\n") if x.startswith("| guard region |"))
    assert row.endswith("| 2300, 400, 50, 735 (fixed by ruling, R24; PROVISIONAL until set on FIDE's data, R47) |")
