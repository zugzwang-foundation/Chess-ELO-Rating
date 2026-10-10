#!/usr/bin/env python3
"""E3's page with its Freeze-2 section as a static record (R52); prints docs/evidence/E3_us-championship-2026.md.

Ruling R52 (docs/decisions/D-0012_pre-results-amendments.md) makes E3's Freeze-2 section a static record of the 89
hashes as they stood at the tag freeze-2 and stops regenerating its file list, which until now was recomputed from the
tracked files on every run, so that every new file changed the page. This script runs Freeze 2's page script,
analysis/e3_us_championships.py, unchanged (it is frozen in Freeze 3 and Freeze 3a), and replaces only that section by
the record below: the 89 lines "file, SHA-256" of the page at the tag freeze-2 (87 files and the two 2026 event files
with their results removed). It refuses to print unless the record's manifest equals the one D-0010 records. The rest
of the page (the 2025 check, the 2026 tables once the events are complete, the PILOT, Freeze 1's hashes) is generated
as before. Python standard library only.

Usage: python3 analysis/e3_freeze2_record.py > docs/evidence/E3_us-championship-2026.md
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e3_us_championships as e3  # noqa: E402  (Freeze 2's page script, unchanged)

D0010 = "docs/decisions/D-0010_freeze-2.md"
D0011 = "docs/decisions/D-0011_rulings-and-freeze-3.md"
D0012 = "docs/decisions/D-0012_pre-results-amendments.md"
SCRIPT = "analysis/e3_freeze2_record.py"
# The 89 lines of E3's Freeze-2 table at the tag freeze-2 (git show freeze-2:docs/evidence/E3_us-championship-2026.md),
# in the page's order: (file, SHA-256 at the tag).
FREEZE2_AT_TAG = (
    ("analysis/OUTPUT_L0_fixtures.md", "f391893efec3aa7b9aaef152f59f0921929ae434d90d97002be671acd220e59a"),
    ("analysis/OUTPUT_L0_k_rules.md", "418580c5a26f88e6e4a44b08c2a39fa531aea72ab60d0f01cb1a3f572d1a3718"),
    ("analysis/OUTPUT_L0_ratification.md", "030d9d43c6ba01d8d01830de4232ca794ae37aad805637b215f2833864affb00"),
    ("analysis/OUTPUT_L0_rounding.md", "1cc1b44f3c60c9471055275870e7a5da69f49106f51c3a5285fc834e390a83d5"),
    ("analysis/OUTPUT_L1_history.md", "55715cb91a4e453b5c7b448fec33e8dac5f9af70dcf205e0f13735daab22eab3"),
    ("analysis/OUTPUT_v1_0.md", "74aa3b3dcfa39a116ffc892c9745714b4174e1fd24851ba346fdc7474c96bfc6"),
    ("analysis/aggregates/E10_guard.json", "111f3a42ebfaf8fbc6719cd6749abc83e6c5dd6eb52843ba8b024399c781b8cf"),
    ("analysis/aggregates/E1_blitz.json", "9419d0311d235a539f0311ffbe448f359790a9b9a9c1729a28da3c56cbb8da44"),
    ("analysis/aggregates/E1_rapid.json", "cae310b51dc7913648ae865ce35b87fc026a0e9f9240f00234858f2b3201a57d"),
    ("analysis/aggregates/E1_standard.json", "6152e41ae6c32a1a35313277b993c66b7a604bc7444ac2a055d04d36df82a065"),
    ("analysis/aggregates/E2_broadcast.json", "c9bac3a4017b01eb6900aa09d77569ffe11cf0bb823b8f0a9a7ef1295b290389"),
    ("analysis/aggregates/E5_deflation.json", "250021cc5084f2925291a400d2dbdef36e31e041c94e47af6bf3c81233e284ad"),
    ("analysis/aggregates/E6_rungs.json", "10df0432ca31e784c5ce0aeda1965fe71f34b08eebe8ca2ed85e6d6d252c5450"),
    ("analysis/aggregates/E7_cross_border.json", "20dd9edd55e9602ef1bfc5ebe1bdf775eed31b5496287136add86e944878b916"),
    ("analysis/aggregates/E8_k_activity.json", "dc9645771e067cef4d448892c678466a98ceb217e3fe6a9b0974dfb12100caf2"),
    ("analysis/aggregates/E9_simulator.json", "c38963a465133e1c9d94bf77f17d580d389c4450966727bd40b698d887fd3e3a"),
    ("analysis/aggregates/L0_k_rules.json", "228cf6a68a348c1b2ac21efea09090822b165d3e1d9c0e1b156336e763aae089"),
    ("analysis/aggregates/L1_history.json", "28402ad6dcb8428b1663856bbf9d8cf5f563dd599c0474908ee61ea7a1b6474f"),
    ("analysis/e0_l0_validation.py", "1d188171027d92805285cdf0116b356553ce8084ae095d2716dca2465dd7d3fb"),
    ("analysis/e10_guard_extract.py", "31b63a315439a4d2ca776d75ca563438c3f7f918b4ed95f5d7532562a972da71"),
    ("analysis/e10_guard_report.py", "a48c31549dcc4ea81ec1cd940c4378f9c107ef2f080914f7c5e3dec16a10605c"),
    ("analysis/e1_fide_lists_extract.py", "185fdf9865f6f5efc7ac4a7b7eaf55101f94330bc4e0feba75f2152c052685c8"),
    ("analysis/e1_fide_lists_report.py", "a871398f3677237684f3d25022da0496f25c639166c2d1c6b36fdbec1f2af90e"),
    ("analysis/e2_broadcast_extract.py", "36c95141c6390fbfd1685a2f933067c10b2c59be199f55e6f30f0551721268a8"),
    ("analysis/e2_broadcast_report.py", "905c1ccb07c77429ec4e130190070dba8a84c02df09e4bc4a543d38842939344"),
    ("analysis/e3_us_championships.py", "e2d05a218201685f381ddcf8d0343400193ce4e8ca1177f2d5165b56a9e12d5f"),
    ("analysis/e4_community_report.py", "4292994a03e807fe6bf9b903ab63c513b18cd08c61d9e5da020bbe566f5e4b1c"),
    ("analysis/e5_deflation_extract.py", "498626cf11326d149113cf2752d7117f7c21bcd6031ffd793c4e208cda7c0533"),
    ("analysis/e5_deflation_report.py", "4651f1474703bbbf33c32db90f1e62891ca33c164b74a136a883e9e9337432c1"),
    ("analysis/e6_rungs_extract.py", "020bf29d253cb9571b0c37ff7ec4a1de113984b56b6ee79a4118cfab42e93e96"),
    ("analysis/e6_rungs_report.py", "159e80d6be562ebbe60d287566a568f277edeefb39808725edd18befa068a76e"),
    ("analysis/e7_cross_border_extract.py", "afcc7b18c234b2162a9ab54f755fd9f4711235f6fcc3677f24d09d61153c7eaf"),
    ("analysis/e7_cross_border_report.py", "685d608d70aec338ef4e5d89efd7580a5c67c9ef6e9b48540acc292c9e35cca9"),
    ("analysis/e8_k_activity_extract.py", "02cebfbd3060f45e3d2c1826cf7b050f74f30353afa71b0f0a98a1a11defa648"),
    ("analysis/e8_k_activity_report.py", "f79cb4e81062a60c191775bef58e0bc5b4a07d9cb86c57c05810dd2ada375e4a"),
    ("analysis/e9_simulator_report.py", "4cacd1581657ba7e6266b841c4f742b1e0285c1ef16c243b1d5a29918bf18db8"),
    ("analysis/e9_simulator_run.py", "270b3388892e88714108bde8bee538beebfa18f72939b230914c05788acd735b"),
    ("analysis/fide_panel.py", "a6a7a6be0b4da9a20fca16218d4c5c0ee6398391a30ac0660b73be729f55f9e1"),
    ("analysis/l0_fixtures_report.py", "4580b1a997abe3ac1455330c7aa41ce13e89e2b770029efea22fdfeb2ec9409f"),
    ("analysis/l0_k_rules_extract.py", "fd05b3a9ea7a0f5df254c7620aeef0c21681d11789cfe165bed3b8ec958f5db0"),
    ("analysis/l0_k_rules_report.py", "2c69353d7218869366c72c361c7ecf7e691f165d255d3530f5f4b7394c14e70f"),
    ("analysis/l0_ratification_check.py", "557884b2caff58ba5605db2c2d2d57fa07eb78679207eb7afb5646fffb155c5c"),
    ("analysis/l0_rounding_report.py", "0522d6f0340720a9bee43e19ca89d77c556a13f39e81b74992950f3c18d8c367"),
    ("analysis/l1_common.py", "8a92075d924730fa69a2ab8658741dba76ec77a763d01b2652aa22cc40350e67"),
    ("analysis/l1_history_extract.py", "cbf6937ffa09dbdcfe1ef9e42d4767c72d51c9c7a8f2d222a1901f77d61014fc"),
    ("analysis/l1_history_report.py", "6bdde0a95dcab8c091b34e7339f13f25651f6ccdf4b1588267dc8d605033c863"),
    ("analysis/us26_rung5_extract.py", "b70e2cd4b7d84471a23133b117ce3824c3e99c7444c195f3058f59317984d8a6"),
    ("analysis/v10_calculations.py", "f9b3836f11eda8dd7d459d0550ea7c2e11280e3593785b1fa37bd9e7be5a45d1"),
    ("params/rung5_us2026.json", "2b6a2cd97d28e897a3ca70ce5d8c619b23b553e3b64db5c6d7816e72eb4f7098"),
    ("params/table_fit_2026-10.yaml", "dcd0c56982e9b3fa4ad9b61993cb9f747ecc64a06975d335f00c2c9d117f3495"),
    ("src/layer0/__init__.py", "247b3d0451c58d32bb46c6cf861f8805740cc3283bc1575416058820560611e7"),
    ("src/layer0/lists.py", "d6fa39835b06eaba7eba6127afa9c87922572cb7dda3a21fb92d501345084aad"),
    ("src/layer0/records.py", "5148c337a8b36e69f46b9bd29265a65e3effd236c5d3e4293d407fe71b44480f"),
    ("src/layer0/rules.py", "fef4ac988d359066bc2e5bf51278556983a3cbf1b0972e791324e0bb1ff4e976"),
    ("src/layer0/tables.py", "e12b30c96fd833198e20ec37a0592e33165dc7c03f744ae66cba53b676e89739"),
    ("src/layer1/__init__.py", "6c10fb85515df6caf25d61e7c0b8a0790a8516863ff698b890ab10f353e5ea50"),
    ("src/layer1/data.py", "468713a17b1b81c7000f44ade83a71cced691f92c1d79a4adeaf30231896f4e6"),
    ("src/layer1/fit.py", "fc1655c4ed0c3cef7004c00cf75bd8b657a45ce87303b02e1783b2724d55d4c5"),
    ("src/layer1/forecast.py", "76109500f379895752424ad6e9ec95a068cd15a014df35f9f9ed7111a37f668d"),
    ("src/layer1/model.py", "6557ca8fbaf29c190427cae55514fa28ed4891d40128da4be66749fd27942f2f"),
    ("src/layer1/outputs.py", "32492e3b92bdd92b1bd35f0f4dadce6a1b6501aadbb235f1fe633765080cf13d"),
    ("src/layer1/solver.py", "d761a3c5f263bca4a41b560fa0d3c21ab9f5438adffc76f99d5f32364bc7e9df"),
    ("src/layer2/__init__.py", "3d13383bd237c23d3365ee8abbb94cdf1edb7bdd5f854e8403c8fbdafa7f77c4"),
    ("src/layer2/guard.py", "22762e15ca93cddca605bd1cb63ba41a24c5f790ff4b0951b6d7aed07077c45c"),
    ("src/layer2/kactivity.py", "6c2381fb9308299e83ed555d66e0d5ab99da70508ea8a682a92761578f910f02"),
    ("src/layer2/table.py", "54863b545939a7a008d3e9d2e11d46996633020d1081b56d0a7d51e1c3ea24b3"),
    ("src/simulator/__init__.py", "3c154983d0946ebd0d46a59716220169fa1310475e1a6b3360822d841a9d0d91"),
    ("src/simulator/config.py", "fd9bfe5c892de0355cb7346289e76b061e2e88d35deddbabb0938f192c0d932a"),
    ("src/simulator/events.py", "309b9e0ab56306d0798ddf1cfee73a13b58a67a6f0c949c01fa5552572f2a948"),
    ("src/simulator/fide.py", "98a205c0f51fa31fcf407fe647c4bceedbdaa1c26f8c7e4c538aa465b368b51a"),
    ("src/simulator/ledger.py", "0b9a0f66bab267c944d5407e888bbfef4be902e3ace6515490c796cdf9e2c315"),
    ("src/simulator/pool.py", "1f20542e1c56223223275218524aa8995b498d85e6efb11de17f05fc097c3954"),
    ("src/simulator/proxy.py", "0b794ed44db7ac8e0c6565ec52bc0742ef7a1dec56dde7b662abe7f10ae62bf3"),
    ("src/simulator/run.py", "ebd83041e48f553282495f18c78221363094f593e4a6b8b67bcd0820f8dbbf71"),
    ("tools/checks/_repo.py", "6219e885e1c1d484b23b8c015ab229f039189f7fdcfb8a64646ef6fcbcda60bb"),
    ("tools/checks/check_outputs.py", "24cb19c1ee1bb0c772cd27b666d2eedb940c8dbc7040ee1352efc826232fed2c"),
    ("tools/checks/check_refs.py", "303ba0c0c403c7b46ab7fa2a6867d5f40719702cce7358f62dabbb9e2bd378e8"),
    ("tools/checks/check_wordcount.py", "b980c72e4efdfacbe86f86179576ade45421d334d51651f758ca72589ad3b52c"),
    ("tools/compare_event.py", "3b517e345819b1f3d052e5e919c5f287ebd3d5c0c2d20c2f52f7ca45e5b9ec13"),
    ("tools/compare_pilot.py", "178cbc68a9041048a1446a8421a004b79a5680ae3eaa555c1948559625de8efe"),
    ("tools/data/convert_broadcasts.py", "7300ecf3195b93dcd7eac9a33c9e15b6d5f5cc0f9b948eca8983e3d0bb956711"),
    ("tools/data/convert_fide_lists.py", "dfd23e0533ceaf299fb4bc8f17f4013f526eb3b75925f98bf2a1a2077ef53695"),
    ("tools/data/fetch_fide_calculations.py", "af25e855e74a36306701b1f8aa3279816df020eaf6b314c5511ee2b11a8d1de4"),
    ("tools/data/fetch_fide_lists.py", "514fb0399262764a9fe770e3f2e70bdacd4f372af5f6d1b8937bebf8b00b980d"),
    ("tools/data/fetch_lichess_broadcasts.py", "bf29d74c1682a4998e056c257858a5600d49c9a18c2dcedca43d5881e9a6ab94"),
    ("tools/events/us_championship_2025.json", "dc6ea576b1969504d1b8e18fe846acfc469b644b24c60a1e8939716e35b2a291"),
    ("tools/set_results.py", "556bdc0e6c4cbf886971630fb719e14483df6c309143c249ed435af0b218815a"),
    ("tools/events/us_championship_2026.json (without results)", "0a4312e026cd6dcd49ce64492c89870ec59d44a741c36b4c67abdada91fba3a1"),
    ("tools/events/us_womens_championship_2026.json (without results)", "70ce5aa418a4ab527b7ad13121061de2d030ca25cc0ce19a6ca9ad741f47afb6"),
)


def manifest(lines: tuple[tuple[str, str], ...] = FREEZE2_AT_TAG) -> str:
    """SHA-256 of the lines "hash  file", as analysis/e3_us_championships.py computed D-0010's manifest."""
    return hashlib.sha256("".join(f"{h}  {f}\n" for f, h in lines).encode("utf-8")).hexdigest()


def recorded() -> str:
    m = re.search(r"Freeze-2 manifest: `([0-9a-f]{64})`", (ROOT / D0010).read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"{D0010} records no manifest")
    return m.group(1)


def static_section() -> str:
    if manifest() != recorded():
        raise SystemExit(f"the static record's manifest {manifest()} differs from D-0010's {recorded()}")
    out = io.StringIO()
    P = lambda s="": out.write(s + "\n")  # noqa: E731
    P("## Freeze 2 (D-0010): a static record\n")
    P(f"Recorded in `{D0010}` before any result of either event was read, as ruling R23 orders, and tagged `freeze-2`. "
      f"Freeze 3 (`{D0011}`, part B) superseded it for the comparison and Freeze 3a (`{D0012}`) amended Freeze 3; check "
      "(a) compares Freeze 3a's manifest, which `docs/evidence/E13_us-championship-2026-freeze-3.md` prints. By ruling "
      f"R52 (D-0012) this section is a static record: the SHA-256 of Freeze 2's {len(FREEZE2_AT_TAG)} entries, "
      f"{len(FREEZE2_AT_TAG) - 2} files and the two event files with their results removed, as they stood at the tag "
      f"`freeze-2`, printed from the record in `{SCRIPT}` and no longer recomputed from the tracked files, so that a new "
      "file no longer changes this page. The script refuses to print unless the record's manifest equals the one D-0010 "
      "records. As at D-0012, two of the files differ from their hash here: `tools/checks/check_outputs.py`, changed by "
      "Freeze 3 and again by Freeze 3a, and `tools/set_results.py`, changed by Freeze 3a (R43); both are in Freeze 3a's "
      "manifest.\n")
    P("| File | SHA-256 at the tag freeze-2 |")
    P("|---|---|")
    for f, h in FREEZE2_AT_TAG:
        tail = " (without results)" if f.endswith("(without results)") else ""
        P(f"| `{f.replace(' (without results)', '')}`{tail} | `{h}` |")
    P(f"\nManifest (SHA-256 of the {len(FREEZE2_AT_TAG)} lines \"hash  file\" above): `{manifest()}`, the manifest "
      "D-0010 records.\n")
    return out.getvalue()


def main() -> int:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e3.main()
    page = buf.getvalue()
    start, end = page.index("## Freeze 2 (D-0010)\n"), page.index("## Reminder\n")
    page = page[:start] + static_section() + page[end:]
    for old, new in (
        ("Generated by `analysis/e3_us_championships.py` with",
         f"Generated by `{SCRIPT}`, which runs `analysis/e3_us_championships.py` unchanged and prints its Freeze-2 "
         "section as a static record (R52, D-0012), with"),
        ("python3 analysis/e3_us_championships.py > docs/evidence/E3_us-championship-2026.md",
         f"python3 {SCRIPT} > docs/evidence/E3_us-championship-2026.md"),
    ):
        if page.count(old) != 1:
            raise SystemExit(f"E3's page no longer holds exactly one {old!r}")
        page = page.replace(old, new)
    sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
