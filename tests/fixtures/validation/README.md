# Validation events for Layer 0

Status: REVIEW — recorded 2026-10-09 (session ELO-3, Phase 3) for SPEC-L0 §6.4 and acceptance criterion A-10.

## `us_championship_2025.json`

The 2025 US Championship: FIDE event 432532, St. Louis, 12–24 October 2025, a 12-player round robin rated on the November 2025 standard list.

**Source.** FIDE's tournament report (`https://ratings.fide.com/report.phtml?event=432532&t=0`) and the twelve players' published calculations for the November 2025 period (`https://ratings.fide.com/a_indv_calculation.php`). That is 13 requests, one at a time and at least 6 seconds apart; each URL and UTC time is in the file.

**Why FIDE's pages.** The brief names the event's Lichess broadcast or the official crosstable. The Lichess broadcast archive has no record of this event: the tour slugs, event names and a participant's FIDE ID were searched in the September to November 2025 files. FIDE's published calculations carry, for every game, the opponent, the colour (FIDE's white and black markers), the result and the rating FIDE used, and FIDE's per-game, per-tournament and per-period changes.

**Rounds.** Each player's page lists the games in the same order. Every pairing appears at the same position for both players, with opposite colours. That position is taken as the round (66 games, 11 rounds).

**What the file holds.**
- Per player:
  - the FIDE ID;
  - single values from the October and November 2025 lists: rating, K and games;
  - FIDE's calculation for this event;
  - FIDE's figures for any other event in the period;
  - the total change FIDE shows.
- Per game: the round, white, black, the result, and for each side the rating FIDE used for the opponent and FIDE's change.

**Privacy.** Players are identified by FIDE ID as in FIDE's report. No names or birth data are recorded. The lists themselves are not redistributed.
