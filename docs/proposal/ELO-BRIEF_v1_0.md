# Fixing the FIDE rating one step at a time: a brief

**Status: DRAFT v1.0 — not for publication**
The Zugzwang Authors · CC BY 4.0 · 2026-10-15. Contact: Hrishikesh, The Zugzwang Foundation. A plain-language summary of `docs/proposal/ELO-PROPOSAL_v1_0.md`. Every number below is PROVISIONAL unless quoted from FIDE's rules [V 1], our evidence reports [E n] or the research report [R n].

## What is wrong

Since FIDE's March 2024 reform a second drain has closed: in 2023–24 players rated 1600–2399 lost 0.37 to 0.93 points a game beyond the expected-score table's error; since, at most 0.08 [E5]. What remains is the top: players rated 2200 or more lose 4 to 7 points a year on FIDE's lists, about what that error implies at their own levels [E5]. On 352,737 broadcast standard games the table expects 0.02 to 0.05 points a game too much of favourites, which top players usually are [E2].

Juniors improve faster than their ratings follow, so adults who play them lose points they should not: an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior is [V 1] [R 5]. Federations are priced differently: an independent study's directions hold on our sample [R 5] [E7].

## What we propose

1. **An open replica of today's rules**: free code that reproduces FIDE's published calculations, so anyone can check a rating change.
2. **A model behind the scenes** that re-reads three years of games monthly to learn what today's system assumes away: how fast juniors improve, what White is worth, how often players draw. It never changes a rating directly.
3. **A familiar published rating**: you still gain or lose K × (score − expected score) per game, on today's scale, with numbers from a yearly table and a monthly file, both public and signed by FIDE's Qualification Commission.

## Seven steps, lowest risk first, with our verdict

1. **The open replica.** Nothing changes in the rules. *Recommended now, subject to a check against FIDE's 1 November list.*
2. **A better table**, self-calibrating (refitted each year on earlier games), with colour, draws and a slope by level: an extra White pays much less, and the 400-point rule goes. Where strong players meet far weaker ones, a temporary guard lifts the favourite's expected score to today's table read without its 400-point cap, so farming does not pay there; against moderately weaker players the table still slightly favours the stronger. *Recommended now in standard from 2000 (the players' average rating), below that once refitted on FIDE's own games: ready for a shadow list today, changing no official rating until a shadow year confirms it level by level on FIDE's data; rapid and blitz after a test on FIDE's games.*
3. **Better starting ratings.** A newcomer's first rating uses all their games instead of two imaginary draws against 1800-rated players; age is used, nationality never. *Test on FIDE data, with step 6.*
4. **K that follows certainty**: 40 for a newcomer, lower the more regularly you play, juniors included, and in a month with many games; no jumps at 30 games, 2300 or 2400; higher after years away. *Test on FIDE data, with step 2.*
5. **Fair games against juniors.** When the model is confident a junior is stronger than their rating, the opponent's expected score uses a higher number for the junior: with every step, an adult who draws a junior listed at 1500 but playing like an 1850 loses 4 points instead of 8. The junior's own rating is computed as before, so it still lags their strength. *Pilot.*
6. **A small monthly adjustment.** If stable adults' ratings drift, active players get a credit or deduction, at most 1.5 points a month, by how much they play. *Test on FIDE data.*
7. **A federation adjustment, last.** The same for whole federations, switched off until FIDE's game records show the effect is real, not a matter of who travels. *Test on FIDE data.*

Ideas proposed earlier by others: K from uncertainty (Glickman), the federation measure and an activity-linked bonus (Ghita), one strength across time controls (URS), junior additions (Chess Scotland), the shallower curve (Sonas).

## What stays the same

Ratings change only when you play. Nothing decays, nothing is rescaled, nothing published is edited. Every change can be checked by hand from public numbers; a monthly ledger shows where every point went. The title and norm rules are not touched, and norms keep their own table [VT 1, 3], though titles use ratings the steps change.

## How we test it

Each step is tested against today's rules on its problem and must not worsen predictions overall. The replica matches FIDE's published calculations; on broadcast games the new table passes its calibration tests, which can miss small errors, its guard stops farming paying, and the junior step removes most of adults' losses to juniors, unevenly by level [E0] [E6] [E11] [E12] [E16].

## What we ask of FIDE

Above all, FIDE's tournament reports, which hold every rated game, under a data agreement: only they can test steps 2 to 7 for the whole pool. Also a review by the Qualification Commission with public comment, and a twelve-month shadow list before anything changes. Federations are asked for nothing now; later, one volunteer federation would pilot the chosen steps on a domestic list. The Zugzwang Foundation computes both lists monthly, at no cost to FIDE or the federation.

## A comparison fixed before any result

For the 2026 U.S. Championships we fixed how today's rules and the new table would be compared, then amended it four times after round 1, always before reading any result. Its 132 games can illustrate the change, not test it.
