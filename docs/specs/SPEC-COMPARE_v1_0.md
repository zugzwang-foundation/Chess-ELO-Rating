# SPEC-COMPARE — one event under FIDE's rules and under rung 2, v1.0

**Status: REVIEW — written before the tool (ELO-3 brief, Phase 5.1).** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09. Tool: `tools/compare_event.py`. Every rung-2 number it prints rests on PROVISIONAL-FITTED parameters.

## 1 Input: an event file

A JSON file (examples under `tools/events/`):
- **The event.** Name, start and end dates, time control (standard, rapid or blitz), the list on which FIDE rates it, the list in force at its start (SPEC-L0 R-11a), and the source of every value with URL and UTC time.
- **The players.** FIDE ID, and the rating and K published on the list in force. No names are needed, and the repository's event files carry none.
- **The games.** Round, board, White's and Black's FIDE IDs, and the result: 1-0, 1/2-1/2, 0-1, or null for a game not yet played. Only played games with a result count.

## 2 Output, per player

Games counted, score, and the rating change from the event under two rule sets, each unrounded (two decimals) and rounded once (R-25):

**(a) FIDE today: Layer 0.** The ratified engine (`src/layer0`, SPEC-L0 v1.0):
- PD from table 8.1.2;
- the 400-point rule with the 2650 exemption in standard from 1 October 2025 (R-14, R-14a), the plain cap in rapid and blitz;
- K = the list's K reduced under R-23 for the event's games.

Column (a) of a completed event equals FIDE's per-event calculation; the 2025 U.S. Championship is the test (§4).

**(b) Rung 2: the fitted table with colour and draws, the same K as (a).** For player i against j:
- x_i = R_i − R_j + w_i η, with w_i = +1 for White and −1 for Black (annex T4.2), and η rounded to a whole number because the published table has one row per whole-number gap (T3.4);
- E is the fitted function of annex T3.1 for the time control, evaluated at the midpoint of the 100-point level band of ⌊(R_W + R_B)/2⌋ and rounded to three decimals, with E(−x) = 1 − E(x);
- ΔR = K (S − E), summed over the event's games and rounded once.

Nothing else changes: no compensation (RX_j = R_j), no monthly adjustment, no change to K.

**The difference (b) − (a).** Unrounded.

**Rungs 4 and 5 are switches.** `--rung4` (K from certainty) and `--rung5` (junior compensation) accept only `off`. Both need Layer 1, which does not exist yet; the tool refuses `on` and says so.

## 3 Labelling

- Both outputs are labelled with the event, the number of games counted of the games scheduled, the parameter file used (with its status and fit window), and a one-paragraph statement of the method:
  - the markdown table carries the label as a header paragraph;
  - the CSV carries it as leading lines that begin with `#`.
- The CSV columns are FIDE ID, rating, K, games, score, then (a) and (b), each unrounded and rounded, then the difference.

## 4 Tests

`tests/test_compare_event.py` checks that:
- column (a) for the 2025 U.S. Championship equals FIDE's per-event calculation for all 12 players (`tests/fixtures/validation/us_championship_2025.json`, SPEC-L0 A-10);
- column (b) of a single game equals K (S − E) by hand from the parameter file;
- unplayed games are not counted;
- the switches refuse `on`.

## 5 Limits

- K reduced under R-23 counts only the event's games. FIDE counts every game of the rating period, so a player with other events in the period may get a smaller K from FIDE; the event file records the published K.
- Rung 2's values are illustrations on PROVISIONAL-FITTED parameters, not ratings. FIDE's official changes are those of the list on which the event is rated.
