# Fixing the FIDE rating one step at a time: a brief

**Status: DRAFT v0.4 — not for publication**
The Zugzwang Authors · CC BY 4.0 · 2026-10-10. A plain-language summary of `docs/proposal/ELO-PROPOSAL_v0_4.md`; the mathematics is in `docs/proposal/ELO-TECHNICAL-ANNEX_v0_4.md`. Every number below is PROVISIONAL unless it is quoted from FIDE's rules [V 1], from our evidence reports [E n] or from the research report [R n].

## What is wrong

The FIDE rating is chess's common currency. The table that turns a rating gap into an expected score expects too much of favourites, by 2 to 5 percentage points on broadcast games [E2], which steadily drains the strongest players [E5]. Juniors improve faster than their ratings follow, so the adults who play them lose points they should not: an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior really is [V 1] [R 5]. Federations are priced differently: an independent study's directions hold on our own sample [R 5] [E7]. And because the table ignores colour, an extra White is worth about 0.8 points in expectation at K = 20.

One worry has eased: since the 2024 reset the ratings of steadily active adults have stopped falling in standard and rapid; the median of the list falls only because newcomers enter below the players who stop [E5].

FIDE has fixed problems one amendment at a time, and the amendments now differ between standard and rapid or blitz [V 1] [V 2].

## What we propose

Three layers.

1. **An open replica of today's rules.** Free code that reproduces FIDE's rating changes exactly, checked against FIDE's own published calculations. Anyone can rerun any list.
2. **A model behind the scenes.** Every month it re-reads three years of games and estimates how strong each player is and how sure it is. It learns what today's system assumes away: how fast juniors improve, how much White is worth, how often players draw. It never changes anyone's rating directly.
3. **A familiar published rating.** You still gain or lose K × (score − expected score) per game, on today's scale. What changes is where the numbers come from: a yearly table and a monthly file, both public, both signed by FIDE's Qualification Commission.

## Seven steps, each adoptable alone

A ladder, lowest risk first; FIDE can stop at any rung.

1. **The open replica.** Nothing changes in the rules; the list becomes reproducible.
2. **A better table.** The expected-score table is refitted each year on real results, with colour and draws in it. An extra White no longer pays, and the 400-point and 600-point special rules disappear.
3. **Better starting ratings.** A newcomer's first rating uses all their games, including rapid and blitz, instead of two imaginary draws against 1800-rated players. Age is used; nationality never is.
4. **K that follows certainty.** K comes from how sure the model is about you: 40 for a newcomer, then lower the more regularly you play. No jumps at 30 games, 2300 or 2400; a player back after years away gets a higher K.
5. **Fair games against juniors.** When the model is confident, from the junior's games in that time control, that a junior is stronger than their rating, the opponent's expected score uses a higher number for the junior. An adult who draws a junior listed at 1500 but playing like an 1850 then loses 4 points instead of 8. The junior's own rating is computed as before.
6. **A small monthly adjustment.** If the ratings of stable adults drift, active players get a small credit, at most 1.5 points a month, or a small deduction if ratings inflate, in proportion to how much they play up to the average. It is added when you next play.
7. **A federation adjustment, last.** The same idea for whole federations, switched off until FIDE's own game records show that the effect is real and not just a matter of who travels.

Several ideas came first from others, and we credit them: K from uncertainty (Glickman), the federation measure and an activity-linked bonus (Ghita), one strength across time controls (URS), junior additions (Chess Scotland), the shallower curve (Sonas).

## What stays the same

Ratings change only when you play. Nothing decays, nothing is rescaled, nothing is edited after it is published. Every change can be checked with a calculator from public numbers, and a monthly ledger shows where every point went. The title and norm rules are not touched: norms use their own table, which the new table does not replace [VT 1, 3].

## How we will prove it

Each step is tested against today's rules on the problem it is meant to fix, and must not make predictions worse overall. So far, on broadcast over-the-board games: the replica matches FIDE's published calculations game by game; the new table passes, except for big favourites at the top, which FIDE's data must check; the junior step removes most of adults' losses to juniors but needs tuning by level; starting ratings and the K rule do not yet pass [E6]. FIDE's tournament records will settle them. Online games are not evidence.

## What we ask of FIDE

Three things: a review by the Qualification Commission with public comment; access to the tournament reports under a data agreement; and a twelve-month shadow list, published beside the official one, before anything changes for anyone.

This is not a black-box artificial intelligence: it is a statistical model whose only power is to set the numbers in two public files, within published limits.
