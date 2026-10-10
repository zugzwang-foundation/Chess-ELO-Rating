# Fixing the FIDE rating one step at a time: a brief

**Status: DRAFT v1.0 — not for publication**
The Zugzwang Authors · CC BY 4.0 · 2026-10-10. A plain-language summary of `docs/proposal/ELO-PROPOSAL_v1_0.md`; the mathematics is in `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md`. Every number below is PROVISIONAL unless it is quoted from FIDE's rules [V 1], from our evidence reports [E n] or from the research report [R n].

## What is wrong

FIDE's expected-score table expects too much of favourites: by 2 to 5 percentage points in standard on broadcast games, almost 10 in rapid [E2] [E5]. The stronger player is usually the favourite, so points drain from the top: players rated 2400 or more lose 0.14 to 0.17 points a game this way, at least what the lists show them losing [E5].

Juniors improve faster than their ratings follow, so adults who play them lose points they should not: an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior really is [V 1] [R 5]. And federations are priced differently: an independent study's directions hold on our own sample [R 5] [E7].

One worry has eased: since the 2024 reset, steadily active adults' ratings have stopped falling in standard and rapid [E5].

## What we propose

1. **An open replica of today's rules**: free code that reproduces FIDE's rating changes exactly, so anyone can rerun any list.
2. **A model behind the scenes** that re-reads three years of games every month and learns what today's system assumes away: how fast juniors improve, what White is worth, how often players draw. It never changes a rating directly.
3. **A familiar published rating**: you still gain or lose K × (score − expected score) per game, on today's scale, with the numbers from a yearly table and a monthly file, both public and signed by FIDE's Qualification Commission.

## Seven steps, lowest risk first, each adoptable alone, with our verdict

1. **The open replica.** Nothing changes in the rules; the list becomes reproducible. *Recommended now, subject to a check on 1 November.*
2. **A better table**, refitted each year on real results, with colour, draws and a slope that changes with level: an extra White pays much less, and the 400-point rule goes; K is scaled up to match its gentler slope. Where strong players meet far weaker ones, a temporary guard lifts the favourite's expected score towards today's, so farming does not pay there; against moderately weaker players it still slightly favours the stronger, for FIDE's games to check. *Recommended now in standard; rapid and blitz after a test on FIDE's games.*
3. **Better starting ratings.** A newcomer's first rating uses all their games instead of two imaginary draws against 1800-rated players; age is used, nationality never. *Test on FIDE data.*
4. **K that follows certainty**: 40 for a newcomer, lower the more regularly you play, and lower in a month with many games; no jumps at 30 games, 2300 or 2400; higher after years away. *Test on FIDE data.*
5. **Fair games against juniors.** When the model is confident that a junior is stronger than their rating, the opponent's expected score uses a higher number for the junior: an adult who draws a junior listed at 1500 but playing like an 1850 loses 4 points instead of 8. The junior's own rating is computed as before. *Pilot.*
6. **A small monthly adjustment.** If stable adults' ratings drift, active players get a small credit or deduction, at most 1.5 points a month, by how much they play. *Test on FIDE data.*
7. **A federation adjustment, last.** The same for whole federations, switched off until FIDE's game records show the effect is real, not a matter of who travels. *Test on FIDE data.*

These ideas came first from others, whom we credit: K from uncertainty (Glickman), the federation measure and an activity-linked bonus (Ghita), one strength across time controls (URS), junior additions (Chess Scotland), the shallower curve (Sonas).

## What stays the same

Ratings change only when you play. Nothing decays, nothing is rescaled, nothing published is edited. Every change can be checked with a calculator from public numbers; a monthly ledger shows where every point went. The title and norm rules are not touched: norms use their own table, which the new table does not replace [VT 1, 3].

## How we test it

Each step is tested against today's rules on the problem it targets and must not make predictions worse overall. On broadcast over-the-board games the replica matches FIDE's published calculations, the new table passes its calibration tests and its guard makes farming lose, and the junior step removes most of adults' losses to juniors, unevenly by level [E0] [E6] [E11] [E12]. A simulated chess world with known true strengths shows today's rules draining the top [E14].

## What we ask of FIDE

Above all, FIDE's tournament reports, which hold every rated game, under a data agreement: only they can test steps 3 to 7 for the whole pool, not just broadcast games. Also a review by the Qualification Commission with public comment, and a twelve-month shadow list before anything changes for anyone.

## A test run blind

For the 2026 U.S. Championships we fixed the comparison of today's rules and the new table and locked the code before reading any result. After a review found the first table off at the top, we amended it before the second round and kept the first version beside it; the numbers are added once, after the last round.

This is not a black-box artificial intelligence: it is a statistical model whose only power is to set the numbers in two public files, within published limits.
