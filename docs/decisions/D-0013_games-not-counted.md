# D-0013 — Reading of R43 against §5.1 of the Rating Regulations: the games not counted

Date: 2026-10-11 (UTC; recorded at about 01:55) · Session: ELO-7, Phase 4 · Status: DECIDED — an executor's reading under ruling R43 (`docs/decisions/D-0012_pre-results-amendments.md`), which it extends and does not reopen, recorded before any result of either 2026 championship was read, after the red-team review of session ELO-7 (finding ELO7-QC-2, `docs/review/REDTEAM_v1_0.md`). D-0012 provides that "a later record can overrule a reading without reopening the ruling"; the architect may overrule this one the same way.

## Context

R43 leaves unplayed games out of every column "as FIDE does not rate them", and D-0012's reading 1 enters the marker `unplayed` for "any game the official page shows as not played". D-0012 quotes only the first sentence of §5.1. The section reads in full [V 1] (transcribed, with its URL and time of reading, in `docs/research/VERIFICATION_2026-10-09.md`):

> 5.1 Whether these occur because of forfeiture or any other reason, they are not counted. Except in case of force majeure, any game where both players have made at least one move will be rated, unless the regulations relating to Fair Play require otherwise.

The second sentence raises two cases that reading 1 does not settle: a game with a result in which a player made no move, and a game annulled for force majeure or under the Fair Play regulations. Left open, either could be decided after the results, and column (a) would then differ from FIDE's calculation. The review asked for both to be settled before any result is read.

## The reading

The marker `unplayed` is entered for every game of rounds 1 to 11 that §5.1 does not count or rate, and only for those:

1. **A game not played** (a forfeit, a withdrawal or a bye), as D-0012's reading 1 has it, whatever score the page awards.
2. **A game in which a player made no move**, judged from the official game score. A game whose published score shows no move by one of the players is not counted, whatever result the page shows.
3. **A game declared unrated** for force majeure or under the Fair Play regulations, as announced on the official page or by FIDE by the time the results are entered. A later decision is not entered. It is reported as a finding when column (a) is checked against FIDE's published calculations after the 1 November list (`{{US26_*_L0_MATCH}}`).

Every other game with a result of 1-0, 1/2-1/2 or 0-1 is counted. Where the official page and the game score disagree on whether a game was played, the game score decides.

## What changes and what does not

- **No frozen file and no manifest changes.** The marker, `tools/set_results.py`, the completion rule and every column stay as D-0012 fixed them.
- **Two places apply the reading.** The proposal's §10 calls its first row "games counted: played games, as §5.1 rates them (D-0013)". The steps for entering the results (in the session close-out) apply this reading.
- **R43 is not reopened.** This record says only which games R43's "as FIDE does not rate them" covers.

## The time, and the rounds completed

Recorded at about 01:55 UTC on 11 October 2026; the commit that merges it is its time of record. The official schedule, as D-0011 part B transcribed it (the page has not been opened in this session), shows rounds 1 and 2 as played (round 2 began at 17:00 UTC on 10 October) and round 3 starting at 17:00 UTC on 11 October. No result of any round has been read.
