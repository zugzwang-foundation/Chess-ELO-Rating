"""The rulings of docs/decisions/D-0018_rulings-on-elo-9-questions.md as the documents carry them (session ELO-10):
R81 (the backward replay without a headline, its caveat and its figures in E20 §5 only), R82 (the tie rule's asymmetry
stated), R83 (OlimpBase's label on every file holding figures derived from its transcription, and README's carve-out),
R84 (FIDE's written permission to be requested, no date), R86 (Appendix F.3, from E20 only) and R87 (annex T1's guard
row), with R81 (ii) and (iv) and R86 (2) as corrected on 12 October 2026 (session ELO-11; docs/DECISIONS.md, item 9).
Every check reads committed files only."""
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
LISTS = json.loads((ROOT / "analysis" / "aggregates" / "E20_greats_lists.json").read_text(encoding="utf-8"))
SELECTED = json.loads((ROOT / "analysis" / "aggregates" / "GREATS_players.json").read_text(encoding="utf-8"))
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
    # R81 (ii) and (iv) as corrected on 2026-10-12 (docs/DECISIONS.md, item 9): the check is read by when the players
    # were chosen, with its figures from the aggregate; the threshold and the premise that the players' results run
    # ahead of any forecast are gone, and nothing says that table 8.1.2 already fits these results
    o, g, cg = REPLAY["calibration"]["overall"], REPLAY["selection_groups"], REPLAY["calibration"]["by_selection"]
    early, late = cg["to_april_2000"], cg["from_july_2000"]
    assert ("The players were chosen for reaching the top three, and the check depends on when. For the "
            f"{g['to_april_2000']['players']} who reached it only on lists to April 2000, the 2025 table sits nearer their "
            f"results ({rep.sgn(early['table_812']['mean'], 3)} under table 8.1.2, "
            f"{rep.sgn(early['table_2025']['mean'], 3)} under the 2025 table); for the {g['from_july_2000']['players']} "
            f"others, FIDE's table does ({rep.sgn(late['table_812']['mean'], 3)} and "
            f"{rep.sgn(late['table_2025']['mean'], 3)}). Players chosen for success can score above any forecast around "
            "the years they were chosen, and players past their peak can score below their ratings; this check cannot "
            "separate the two, so it cannot say which table fits the era. Only an unselected sample of the era, which "
            "FIDE's tournament reports would provide, can.") in sec5
    assert abs(early["table_2025"]["mean"]) < abs(early["table_812"]["mean"])
    assert abs(late["table_812"]["mean"]) < abs(late["table_2025"]["mean"])
    assert (f"Pooled over all {o['players']} players, a table fitted on games of March to December 2024 sits further "
            "from these 2008-2019 results than FIDE's own; split by when the players were chosen, the order reverses for "
            f"the {g['to_april_2000']['players']}. That is consistent with calibration changing between eras, with the "
            "table's thin support at the top, or with how the players were chosen; it proves none of them.") in sec5
    assert (o["players"], g["to_april_2000"]["players"], g["from_july_2000"]["players"]) == (29, 14, 15)
    for text in (E20, APPENDIX):
        assert "run ahead of any forecast" not in text and "a lift above" not in text and "already fits" not in text
        assert "on the same results, which FIDE rated with table 8.1.2" in text
    assert "No estimate of the table's own error at the top" in sec5 and "a handful of games (E19 §3)" in sec5
    # ELO10-STAT-2: the mean difference and range under each reading of the rounding appear in §5 only
    outside = E20.replace(sec5, "")
    for x in REPLAY["readings"].values():
        mean2 = rep.sgn(x["mean_difference"], 2)
        rng = f"{rep.sgn(x['min_difference'])} to {rep.sgn(x['max_difference'])}"
        assert mean2 in sec5 and mean2 not in outside and mean2 not in APPENDIX
        assert rng in sec5 and f"| {rng} |" not in outside
    # ELO10-STAT-1: the check split by how the players were selected, below the check
    g, cg = REPLAY["selection_groups"], REPLAY["calibration"]["by_selection"]
    assert g["to_april_2000"]["players"] + g["from_july_2000"]["players"] == REPLAY["players_replayed"]
    assert cg["to_april_2000"]["games"] + cg["from_july_2000"]["games"] == REPLAY["calibration"]["overall"]["games"]
    for k in ("to_april_2000", "from_july_2000"):
        assert rep.ci(cg[k]["table_812"]) in sec5 and rep.sgn(g[k]["mean_difference"], 2) in sec5
    # Appendix I: two sentences on the backward replay, pointing to E20 §5
    para = next(x for x in APPENDIX.split("\n\n") if x.startswith("E20 §5 also replays"))
    assert para.count(". ") + 1 == 2 and "E20 §5 only" in para


def test_r82_the_tie_rules_asymmetry_and_its_source_are_stated():
    n = len(SELECTED["players"])
    tie_only = rep.surnames([p["name"] for p in LISTS["players"] if p["top3_only_by_a_shared_third"]])
    not_in = [t for t in LISTS["printed_ties_at_third"] if not t["selected"]]
    assert tie_only and not_in
    for text in (E20, APPENDIX):
        assert tie_only in text
        for t in not_in:
            assert (f"{t['name'].split(',')[0]}, printed {rep.ordinal(t['printed_rank'])} on the 3rd's rating in "
                    f"{rep.month(t['list'])}, is not among the {n}") in text
        assert "multiples of five" in text and "FIDE's printed order decides where a printed" in text
        # E20 names the ruling; the proposal's appendix says it in plain words (session ELO-12)
        assert ("R82" if text is E20 else "with no change after results") in text
        # ELO10-STAT-3: from July 2000 a shared place still counts on the lists computed without a printed copy
        late = sorted({d for p in LISTS["players"] for d in p["top3_lists_shared_third"] if d >= "2000-07"})
        assert late and all(rep.month(d) in text for d in late)


def test_r83_every_file_with_olimpbase_derived_figures_carries_the_label_and_readme_names_it():
    licence = (ROOT / "README.md").read_text(encoding="utf-8").split("## Licences")[1]
    assert LABEL in licence
    for f in DOCS + AGGREGATES:
        assert f"`{f}`" in licence, f
    for f in DOCS:
        assert LABEL in (ROOT / f).read_text(encoding="utf-8"), f
    # D-0018 reading 11 (d): the review record's verbatim reports are not edited; the ELO-10 addendum carries the label
    red = (ROOT / "docs" / "review" / "REDTEAM_v1_0.md").read_text(encoding="utf-8")
    addendum = red.split("## Addendum: session ELO-10")[1]
    assert LABEL in addendum.split("### The reviewer's report (verbatim)")[0]
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
    # R86 (2) as corrected on 2026-10-12 (docs/DECISIONS.md, item 9): which text was in force in 2018 is NOT VERIFIED
    assert ("FIDE's lists rounded a period's negative half point towards +∞ to the list of July 2018 and away from zero "
            "from November 2018; which text was in force in 2018 is NOT VERIFIED; the 2022 text says \"away from "
            "zero\"; the list of January 2009 is the exception") in f3
    assert "The same rounding words were applied two ways" not in f3
    assert "January 2009 is the exception" in f3 and "41 points" in f3 and "Nothing has been sent to FIDE" in f3
    assert "a date no text gives" in E20 and "before the text of 2022 said \"away from zero\"" in E20


def test_r87_annex_t1s_guard_row():
    annex = (ROOT / "docs" / "proposal" / "ELO-TECHNICAL-ANNEX_v1_0.md").read_text(encoding="utf-8")
    row = next(x for x in annex.split("\n") if x.startswith("| guard region |"))
    assert row.endswith("| 2300, 400, 50, 735 (fixed by ruling, R24; PROVISIONAL until set on FIDE's data, R47) |")
