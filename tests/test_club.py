"""Session ELO-D2's club-level sample (docs/specs/SPEC-SOURCING_v1_1.md): the extended parser on FIDE's two layouts of a
tournament and on a game row without a colour mark; the opponent's resolver; the groups and the 2025-only lock of the
fetch tool; the clustered estimators; the plan's allocation; and the rule that no committed aggregate of the session
carries a player's name or FIDE ID. Synthetic pages and the committed aggregates only: no connection, no data/."""
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("analysis", "tools/data", "src"):
    sys.path.insert(0, str(ROOT / sub))
import e17_top100_extract as ex  # noqa: E402
import e21_club_common as cc  # noqa: E402
import e21_club_extract as ce  # noqa: E402
import e21_club_plan_extract as cp  # noqa: E402
import fetch_sourcing as fs  # noqa: E402

AGG = ROOT / "analysis" / "aggregates"


def _row(cells: list[str], bg: str = "#efefef", mark: str | None = None) -> str:
    tds = []
    for i, c in enumerate(cells):
        note = f'<span class="{mark}_note"></span>' if (i == 0 and mark) else ""
        tds.append(f"<td class=list4>{note}{c}</td>")
    return f"<tr bgcolor={bg}>" + "".join(tds) + "</tr>"


def _page(tournaments: list[str], total: str) -> str:
    return "<html>" + "".join(tournaments) + f"Total change:&nbsp;<b>{total}</b></html>"


def _tournament(event: int, dates: tuple[str, str], header: list[str], summary: list[str], games: list[str]) -> str:
    return (f'<div class="rtng_line01"><a href=/report.phtml?event={event}&t=0 class=head1>Open</a>'
            + "".join(f'<span class="dates_span">{d}</span>' for d in dates)
            + "<table>" + _row(header, "#b7b7b7") + _row(summary, "#e6e6e6") + "<tr><td></td></tr>"
            + "".join(games) + "</table></div>")


RATED_HEADER = ["Rc", "Ro", "", "", "", "w", "n", "chg", "K", "K*chg"]
UNRATED_HEADER = ["", "", "", "Rc", "Ro", "w", "n", "chg", "Rp", "K"]


def _rated_page(with_unmarked: bool = False) -> str:
    games = [_row(["Player A", "", "", "1703", "LAT", "1.00", "1", "0.17", "40", "6.80"], mark="black"),
             _row(["Player B", "", "", "1791", "LAT", "0.50", "1", "-0.24", "40", "-9.60"], mark="white")]
    if with_unmarked:
        games.append(_row(["Player C", "", "", "1800", "BEL", "0.50", "1", "-0.08", "40", "-3.20"]))
    n = len(games)
    t = _tournament(1, ("2025-04-17", "2025-04-21"), RATED_HEADER,
                    ["1748", "1833", "", "", "", "2.00" if with_unmarked else "1.50", str(n),
                     "-0.15" if with_unmarked else "-0.07", "40", "-6.00" if with_unmarked else "-2.80"], games)
    return _page([t], "-6.00" if with_unmarked else "-2.80")


def test_the_parser_reads_a_rated_tournament_as_e17_does():
    text = _rated_page()
    new, old = cc.parse_page_club(text), ex.parse_page(text)
    assert new["total"] == old["total"] == Decimal("-2.80")
    a, b = old["tournaments"][0], new["tournaments"][0]
    for k in ("event", "start", "end", "rc", "ro", "w", "n", "chg", "k", "k_chg"):
        assert a[k] == b[k], k
    assert [{k: g[k] for k in a["games"][0]} for g in b["games"]] == a["games"]
    assert not b["unrated"]


def test_the_parser_counts_a_game_row_without_a_colour_mark():
    t = cc.parse_page_club(_rated_page(with_unmarked=True))["tournaments"][0]
    assert len(t["games"]) == 3 and t["n"] == 3
    assert [g["mark"] for g in t["games"]] == ["black", "white", None]
    assert len(ex.parse_page(_rated_page(with_unmarked=True))["tournaments"][0]["games"]) == 2   # E17 leaves it out


def test_the_parser_reads_a_tournament_printed_with_ro_0_and_without_k():
    games = [_row(["Player D", "", "", "1570", "PER", "1.00", "1", "0.00", "", "0.00"], mark="black"),
             _row(["Player E", "", "", "1544", "PER", "0.00", "1", "0.00", "", "0.00"], mark="white")]
    text = _page([_tournament(2, ("2025-05-01", "2025-05-02"), UNRATED_HEADER,
                              ["", "", "", "1557", "0", "1.00", "2", "0.00", "1457", ""], games)], "0.00")
    with pytest.raises(ValueError):
        ex.parse_page(text)                                   # E17's parser rejects the page
    t = cc.parse_page_club(text)["tournaments"][0]
    assert t["ro"] == 0 and t["k"] is None and t["rp"] == 1457 and t["unrated"]
    assert [g["k"] for g in t["games"]] == [None, None] and t["rc"] == 1557


def test_the_resolver_takes_the_federation_the_tolerance_and_the_nearest():
    key = ex.norm("Doe, John")
    index = {"2025-03": {key: [("1", "ESP", 1800), ("2", "FRA", 1790), ("3", "ESP", 1900)]}}
    g = {"name": "John Doe", "fed": "ESP", "rating": 1803, "capped": False}
    assert cc.resolve(g, 1700, "2025-03", index) == ("1", "list in force")
    assert cc.resolve({**g, "fed": "FRA"}, 1700, "2025-03", index)[0] == "2"
    assert cc.resolve({**g, "rating": 1990}, 1700, "2025-03", index) == (None, "no rating within the tolerance")
    assert cc.resolve({**g, "fed": "GER", "rating": 1794}, 1700, "2025-03", index)[0] == "2"   # nearest, any federation
    assert cc.resolve({**g, "fed": "GER", "rating": 1795}, 1700, "2025-03", index)[1] == "several"  # a tie
    capped = {"name": "John Doe", "fed": "ESP", "rating": 1850, "capped": True}       # Ro 2250: the cap at 1850
    assert cc.resolve(capped, 2250, "2025-03", index)[0] == "1"                       # beyond the cap, below it
    assert cc.resolve({**g, "name": "Jane Roe"}, 1700, "2025-03", index) == (None, "name not on the lists")
    near = {"2025-02": {key: [("4", "ESP", 1805)]}, "2025-03": {}}
    assert cc.resolve(g, 1700, "2025-03", near) == ("4", "a nearby list")


@pytest.mark.parametrize("birth,first,band,group", [
    (2006, "2019-01", "1600-1799", "junior"), (2005, "2024-05", "1600-1799", "newcomer"),
    (2005, "2022-12", "1600-1799", "other"), (0, "2023-01", "1400-1599", "newcomer"),
    (1990, "2024-01", "2200+", "other"), (2010, None, "2200+", "junior"), (0, None, "1800-1999", "other")])
def test_the_groups(birth, first, band, group):
    assert fs.club_group(birth, first, band) == group


def test_juniors_as_e6_defines_them():
    assert cc.is_junior(2006) and not cc.is_junior(2005) and not cc.is_junior(None)


def test_the_club_lock_takes_2025_calculation_pages_only():
    fs.check_lock_club("calc", "1:2025-01")
    fs.check_lock_club("calc", "1:2025-12")
    for kind, arg in (("calc", "1:2024-12"), ("calc", "1:2026-01"), ("report", "123"), ("get", "x y")):
        with pytest.raises(SystemExit):
            fs.check_lock_club(kind, arg)


def test_the_bands():
    assert [fs.club_band(r) for r in (1399, 1400, 1999, 2000, 2199, 2200, 2850)] == [
        None, "1400-1599", "1800-1999", "2000-2199", "2000-2199", "2200+", "2200+"]
    assert ce.level_of(1599.5) == "1400-1599" and ce.level_of(2200) == "2200+" and ce.gap_bin(49) == "0-49"


def test_the_clustered_mean():
    m = ce.Mean()
    for page, w, y in (("a", 1.0, 1.0), ("a", 1.0, 0.0), ("b", 3.0, 1.0), ("c", 1.0, 0.0)):
        m.add(page, w, y)
    u, wtd = m.summary(False), m.summary(True)
    assert u["games"] == 4 and u["pages"] == 3 and u["mean"] == 0.5
    assert wtd["mean"] == round(4 / 6, 4)
    z = [0.0, 0.5, -0.5]                                  # each page's sum of residuals about 0.5
    se = math.sqrt(sum(x * x for x in z) * 3 / 2) / 4
    assert u["lo"] == round(0.5 - 1.96 * se, 4) and u["hi"] == round(0.5 + 1.96 * se, 4)
    one = ce.Mean()
    one.add("a", 1.0, 0.25)
    assert one.summary(False)["lo"] == one.summary(False)["hi"] == 0.25


def test_the_edge_is_half_the_difference_as_white_and_as_black():
    e = ce.Edge()
    for page, y, white in (("a", 0.1, True), ("a", -0.1, False), ("b", 0.3, True), ("c", 0.0, False)):
        e.add(page, 1.0, y, white)
    s = e.summary(False)
    assert s["edge"] == round(((0.1 + 0.3) / 2 - (-0.1 + 0.0) / 2) / 2, 4)
    assert s["lo"] < s["edge"] < s["hi"]


def test_rule_a_tests_only_cells_of_1000_games_and_applies_holm():
    cells = {}
    for k, mean in (("big_out", 0.05), ("big_in", 0.0), ("small", 0.2)):
        m = ce.Mean()
        n = 50 if k == "small" else 2000
        for i in range(n):
            m.add(f"{k}{i % 400}", 1.0, mean + (0.3 if i % 2 else -0.3))
        cells[k] = m
    r = ce.rule_a(cells, False)
    assert r["cells_tested"] == 2 and r["outside"] == ["big_out"]


def test_the_largest_remainder_keeps_the_total():
    out = cp.largest_remainder(300, {"2200+|junior": 3516, "2200+|other": 6417})
    assert sum(out.values()) == 300 and out == {"2200+|junior": 106, "2200+|other": 194}


def test_the_committed_plan_holds_the_cap_and_meets_its_thresholds():
    plan = json.loads((AGG / "E21_club_plan.json").read_text(encoding="utf-8"))
    pages = plan["allocation"]["pages"]
    assert sum(pages.values()) == plan["rule"]["total_pages"] <= plan["rule"]["cap_requests"] - 1
    assert all(pages[s] <= plan["frame"][s]["players"] for s in pages)
    assert all(plan["allocation"]["thresholds_met"].values())


@pytest.mark.parametrize("name", ["E21_club_plan.json", "E21_tier0.json", "E21_club_pilot.json", "E21_club.json"])
def test_no_committed_aggregate_of_the_club_sample_names_or_identifies_a_player(name):
    path = AGG / name
    if not path.exists():
        pytest.skip(f"{name} is written once the fetch completes")
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)

    def keys(x, p=""):
        if isinstance(x, dict):
            for k, v in x.items():
                yield str(k)
                yield from keys(v)
        elif isinstance(x, list):
            for v in x:
                yield from keys(v)
    for k in keys(data):
        assert k.lower() not in ("id", "fide_id", "name", "names", "ids", "player", "players_list", "sample"), k


def test_the_manifest_verifies_every_page_before_any_is_deleted(tmp_path, monkeypatch):
    calcs = tmp_path / "calculations"
    calcs.mkdir()
    log = tmp_path / "ELO-D2.tsv"
    rows = ["fetched_utc\thost\tpath\tstatus\tbytes\tsha256\turl\titem"]
    import hashlib
    for pid, period, body in (("1", "2025-01", b"a"), ("2", "2025-02", b"bb")):
        (calcs / f"{pid}_{period}.html").write_bytes(body)
        url = fs.CALC_URL.format(id=pid, period=period)
        rows.append(f"2026-10-14T15:00:0{pid}Z\tratings.fide.com\t/x\t200\t{len(body)}\t"
                    f"{hashlib.sha256(body).hexdigest()}\t{url}\tcalc {pid}:{period}")
    log.write_text("\n".join(rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(fs, "CALCS", calcs)
    monkeypatch.setattr(fs, "MANIFEST", tmp_path / "MANIFEST")
    monkeypatch.setattr(fs, "MANIFEST_LOGS", (("ELO-D2", log),))
    monkeypatch.setattr(fs, "QUEUE", tmp_path / "none")
    monkeypatch.setattr(fs, "CLUB_QUEUE", tmp_path / "none")
    (calcs / "2_2025-02.html").write_bytes(b"changed")            # a page that no longer matches its log
    assert fs.write_manifest() == 1
    with pytest.raises(SystemExit):
        fs.delete_pages()                                         # nothing deleted while one page is not verified
    assert len(list(calcs.glob("*.html"))) == 2
    (calcs / "2_2025-02.html").write_bytes(b"bb")
    assert fs.write_manifest() == 0
    assert fs.delete_pages() == 0 and not list(calcs.glob("*"))
    assert (tmp_path / "MANIFEST").read_text(encoding="utf-8").count("verified") == 2


def test_the_club_run_writes_its_status_every_hour_and_completes(tmp_path, monkeypatch):
    """Regression (ELO-D2, 15:25 UTC): the status file is written at the first hourly mark after pages were fetched,
    and the run ends with COMPLETE. No connection: the request is replaced."""
    calcs = tmp_path / "calculations"
    queue = tmp_path / "queue.txt"
    queue.write_text("calc 1:2025-01\ncalc 2:2025-02\n", encoding="utf-8")
    log = tmp_path / "ELO-D2.tsv"
    log.write_text("fetched_utc\thost\tpath\tstatus\tbytes\tsha256\turl\titem\n", encoding="utf-8")

    class Clock:
        t = 1_000_000.0

        def time(self):
            self.t += 2000.0                      # every call moves the clock on: the hourly mark is passed
            return self.t

        def sleep(self, s):
            pass

    def fake_request(url, item, gap, headers=None, last=None):
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"2026-10-14T15:00:00Z\tratings.fide.com\t/x\t200\t5\t-\t{url}\t{item}\n")
        return 200, b"<tr bgcolor=#efefef></tr>", 0.0, "2026-10-14T15:00:00Z"
    monkeypatch.setattr(fs, "CALCS", calcs)
    monkeypatch.setattr(fs, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(fs, "LOG", log)
    monkeypatch.setattr(fs, "time", Clock())
    monkeypatch.setattr(fs, "request", fake_request)
    monkeypatch.setattr(fs, "allowed", lambda url: True)
    status = tmp_path / "status.md"
    assert fs.run(str(queue), club=True, status_file=status) == 0
    text = status.read_text(encoding="utf-8")
    assert "Pages done: 2 of 2" in text and text.rstrip().endswith("COMPLETE")
