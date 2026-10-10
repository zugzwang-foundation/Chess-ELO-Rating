"""A1-7, A1-8 (SPEC-L1 §7): the data cutoff and the absence of any federation input."""
import dataclasses
import inspect
from datetime import date

import pytest

layer1 = pytest.importorskip("layer1")
from layer1 import data, fit  # noqa: E402

HEADER = "tour\tround_url\tgame_url\tevent\tdate\tutc_date\twhite\tblack\twhite_fide_id\tblack_fide_id\twhite_elo\tblack_elo\tresult\tvariant\ttime_control\tclk_white\tclk_black\n"


def write(root, month, rows):
    d = root / "data" / "interim" / "broadcast"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{month}.tsv").write_text(HEADER + "".join("\t".join(r) + "\n" for r in rows))


def row(day, w, b, res="1-0"):
    return ["t1", "r1", f"g{w}{b}{day}", "e", day, day, f"P{w}", f"P{b}", w, b, "", "", res, "Standard", "5400+30", "", ""]


def test_a1_7_loader_refuses_a_late_file(tmp_path):
    write(tmp_path, "2026-09", [row("2026.09.10", "1", "2")])
    write(tmp_path, "2026-10", [row("2026.10.10", "1", "2")])
    with pytest.raises(ValueError):
        data.read_broadcasts(tmp_path)


def test_a1_7_loader_drops_games_after_the_cutoff(tmp_path):
    write(tmp_path, "2026-09", [row("2026.09.30", "1", "2"), row("2026.10.01", "3", "4"), row("2026.10.09", "5", "6")])
    games, meta = data.read_broadcasts(tmp_path)
    assert [g.day for g in games] == [date(2026, 9, 30)]
    assert meta["dropped_after_cutoff"] == 2


def test_a1_7_fitter_refuses_a_late_game():
    late = fit.Game(date(2026, 10, 1), fit.month_index(2026, 10), 0, 1, 2, 1.0, 2050)
    ok = fit.Game(date(2026, 9, 30), fit.month_index(2026, 9), 0, 1, 2, 1.0, 2050)
    with pytest.raises(ValueError):
        fit.check_cutoff([ok, late])
    with pytest.raises(ValueError):
        fit.build([ok, late], {}, lambda p, m: fit.Prior(2000.0, 1e4), fit.Hyper())


def test_a1_8_no_federation_anywhere():
    for cls in (fit.Game, data.RawGame):
        assert not any("fed" in f.name.lower() for f in dataclasses.fields(cls))
    for fn in (fit.build, fit.run, data.build_games, data.read_broadcasts, data.anchor_panel):
        assert not any("fed" in p.lower() for p in inspect.signature(fn).parameters)
    assert "fed" not in inspect.getsource(data.Lists.load).lower().replace("federation field", "")
