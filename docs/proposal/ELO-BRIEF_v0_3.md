# Fixing the FIDE rating one step at a time: a brief

**Status: DRAFT v0.3 — not for publication**
The Zugzwang Authors · CC BY 4.0 · 2026-10-09. A plain-language summary of `docs/proposal/ELO-PROPOSAL_v0_3.md`; the mathematics is in `docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md`. Every number below is PROVISIONAL unless it is quoted from FIDE's rules [V 1] or from the research report [R n].

## What is wrong

The FIDE rating is chess's common currency, and it is losing value. After the 2024 reset the typical active player still loses about 16 points a year [R 5]. Juniors improve faster than their ratings can follow, so the adults who play them lose points they should not: today an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior really is [V 1] [R 5]. Players from different countries rarely meet, and one independent study finds that the same number can mean strengths about 100 points apart between federations [R 6]. The table that turns a rating gap into an expected score overrates favourites at large gaps [R 44]. And because the table ignores colour, a player who gets an extra White gains about 0.8 points in expectation at K = 20.

FIDE has fixed problems one amendment at a time, and the amendments now differ between standard and rapid or blitz [V 1] [V 2].

## What we propose

Three layers.

1. **An open replica of today's rules.** Free code that reproduces FIDE's rating changes exactly, checked against FIDE's own calculator. Anyone can rerun any list.
2. **A model behind the scenes.** Every month it re-reads the last three years of games and estimates how strong each player is and how sure it is of that. It learns what today's system assumes away: how fast juniors improve, how much White is worth, how often players draw. It never changes anyone's rating directly.
3. **A familiar published rating.** You still gain or lose K × (score − expected score) per game, on today's scale. What changes is where the numbers come from: a yearly table and a monthly file, both public, both signed by FIDE's Qualification Commission.

## Seven steps, each adoptable alone

The improvements come as a ladder, lowest risk first. FIDE can stop at any rung.

1. **The open replica.** Nothing changes in the rules; the list becomes reproducible.
2. **A better table.** The expected-score table is refitted each year on real results, with colour and draws in it. An extra White no longer pays, and the 400-point and 600-point special rules disappear.
3. **Better starting ratings.** A newcomer's first rating uses all their games, including rapid and blitz, instead of two imaginary draws against 1800-rated players. Age is used; nationality never is.
4. **K that follows certainty.** The step size K comes from how sure the model is about you: 40 for a newcomer, about 17 for an established adult, about 11.5 for a long-standing top player. No more jumps at 30 games, 2300 or 2400. A player back after years away gets a higher K, so the rating catches up faster.
5. **Fair games against juniors.** When the model is confident a junior is stronger than their rating, the opponent's expected score uses a higher number for the junior. With all steps in place, an adult who draws a junior listed at 1500 but playing like an 1850 loses 5 points instead of 8. The junior's own rating is computed as before, from published ratings.
6. **A small monthly adjustment.** If the ratings of stable adults drift, every active player gets the same small credit, at most 1.5 points a month, or a small deduction if ratings inflate. It is added when you next play, so it cannot be farmed by playing more.
7. **A federation adjustment, last.** The same idea for whole federations, switched off until FIDE's own game records show that the effect is real and not just a matter of who travels.

## What stays the same

Ratings change only when you play. Nothing decays, nothing is rescaled, nothing is edited after it is published. Every change can be checked with a calculator from public numbers, and a monthly ledger shows where every point came from and where it went. The title and norm rules are not touched; whether their arithmetic would be affected by a new table has not been verified, and the trial below would answer it with numbers.

## How we will prove it

Each step is tested against today's rules on the problem it is meant to fix, and must not make predictions worse overall. The evidence comes from FIDE's monthly rating lists, from broadcast over-the-board games, and later from FIDE's own tournament records. Online games are not used as evidence.

## What we ask of FIDE

Three things: a review by the Qualification Commission with public comment; access to the tournament reports under a data agreement; and a twelve-month shadow list, published beside the official one, before anything changes for anyone.

This is not artificial intelligence in the sense of a black box. It is a statistical model whose only power is to set the numbers in two public files, within published limits.
