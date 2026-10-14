"""Session ELO-D1's sourcing (docs/DECISIONS.md, items 24 to 32): the fetch tool's championship lock, its reading of
robots.txt and its one site for FIDE's hosts; the pilot's allocation over level bands; the rule that no committed
aggregate of the session carries a player's name or FIDE ID, the greats excepted; and the greats' replay list by list
against E20's committed year-end values. The tests read the tool and the committed aggregates: they open no connection
and need no data/."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import fetch_sourcing as fs  # noqa: E402

AGG = ROOT / "analysis" / "aggregates"


def test_the_lock_refuses_a_period_after_the_october_2026_list():
    fs.check_lock("calc", "1503014:2026-10")                 # the October 2026 list itself is allowed
    with pytest.raises(SystemExit):
        fs.check_lock("calc", "1503014:2026-11")


@pytest.mark.parametrize("name", ["2026 U.S. Championship", "U.S. Women's Championship 2026",
                                  "US Championship 2026", "United States Championship 2026"])
def test_the_lock_names_a_us_championship(name):
    assert fs.LOCKED_NAME.search(name)
    with pytest.raises(SystemExit):
        fs.check_lock("get", "https://example.org/" + name.replace(" ", "%20") + " page.html")


def test_the_lock_refuses_a_report_not_read_from_the_pilots_pages(monkeypatch):
    monkeypatch.setattr(fs, "report_events_known", lambda period=None: {
        "1": {"name": "Open", "start": "2026-09-20", "end": "2026-10-02"},
        "2": {"name": "2026 U.S. Championship", "start": "2026-09-01", "end": "2026-09-12"},
        "3": {"name": "Open", "start": "2025-01-10", "end": "2025-01-15"}})
    for event in ("1", "2", "4"):
        with pytest.raises(SystemExit):
            fs.check_lock("report", event)
    fs.check_lock("report", "3")


def test_fides_hosts_are_one_site():
    assert {fs.site_of(h) for h in ("ratings.fide.com", "www.fide.com", "fide.com", "qc.fide.com")} == {"fide.com"}
    assert fs.site_of("web.archive.org") == "web.archive.org"
    assert fs.site_of("notfide.com") == "notfide.com"


def test_robots_txt_is_obeyed(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "ROBOTS", tmp_path)
    (tmp_path / "robots_a.example_20261014T000000Z_200.txt").write_text(
        "User-agent: *\nDisallow: /private/\nAllow: /private/open\n", encoding="utf-8")
    assert fs.allowed("https://a.example/public/page")
    assert not fs.allowed("https://a.example/private/page")
    assert fs.allowed("https://a.example/private/open/page")
    (tmp_path / "robots_b.example_20261014T000000Z_404.txt").write_text("<html>not found</html>", encoding="utf-8")
    assert fs.allowed("https://b.example/anything")           # no robots.txt: no rules
    (tmp_path / "robots_c.example_20261014T000000Z_503.txt").write_text("", encoding="utf-8")
    assert not fs.allowed("https://c.example/anything")       # robots.txt unreachable: nothing fetched
    with pytest.raises(SystemExit):
        fs.allowed("https://d.example/")                      # robots.txt not read yet


@pytest.mark.parametrize("n,sizes", [(26, {"a": 10, "b": 400, "c": 3, "d": 0, "e": 5000}),
                                     (27, {"a": 1, "b": 1}), (3, {"a": 50, "b": 50, "c": 50, "d": 50})])
def test_the_allocation_spreads_a_federations_pages_over_its_level_bands(n, sizes):
    out = fs.allocate(n, sizes)
    assert sum(out.values()) == min(n, sum(sizes.values()))
    assert all(out[b] <= sizes[b] for b in sizes)
    bands = [b for b in sizes if sizes[b]]
    if n >= len(bands):
        assert all(out[b] >= 1 for b in bands)
    else:
        assert [b for b in bands if out[b]] == bands[:n]       # from the floor up


def _keys(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield path + "/" + str(k)
            yield from _keys(v, path + "/" + str(k))
    elif isinstance(x, list):
        for v in x:
            yield from _keys(v, path + "[]")


@pytest.mark.parametrize("name", ["E21_lists.json", "E21_pilot.json"])
def test_no_committed_aggregate_of_the_session_names_or_identifies_a_player(name):
    data = json.loads((AGG / name).read_text(encoding="utf-8"))
    for k in _keys(data):
        leaf = k.rsplit("/", 1)[-1].lower()
        assert leaf not in ("id", "fide_id", "name", "names", "ids", "player", "players_list"), k


def test_the_greats_list_by_list_equal_e20s_year_ends():
    by_list = json.loads((AGG / "E20_greats_replay_by_list.json").read_text(encoding="utf-8"))
    e20 = {p["fide_id"]: p for p in json.loads((AGG / "E20_greats_replay.json").read_text(encoding="utf-8"))["players"]}
    assert by_list["players_replayed"] == len(e20)
    compared = 0
    for p in by_list["players"]:
        old = e20[p["fide_id"]]
        for year, v in old["year_end_difference"].items():
            assert p["difference_by_list"][f"{year}-12"] == v
            compared += 1
        assert p["difference_by_list"][p["last_list"]] == old["difference"]
        compared += 1
    assert compared == by_list["check"]["year_end_and_last_list_values_compared"] == by_list["check"]["equal"]
