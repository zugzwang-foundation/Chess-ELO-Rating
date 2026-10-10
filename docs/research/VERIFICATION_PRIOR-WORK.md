# Verification sweep — prior work (Ghita, Sonas, Glickman, URS, the Kaggle contests, WHR), 2026-10-10
Status: VERIFICATION RECORD (primary-source reading). Session ELO-4, Phase 5. Author: The Zugzwang Authors. Licence: CC BY 4.0 (see `docs/LICENSE-docs.md`); quoted third-party text remains its owners' and is reproduced for verification only, in phrases of at most 15 words; everything else is paraphrase. Citation key: `[VP k]` is item k of this file. A record: never edited after the fact.

**Method.** The sweep was run by a research subagent of the executor, on the operator's machine, and reviewed by the executor against the fetched texts before commit; the raw files and conversions stayed in the session's temporary folder and are not committed. Every source was fetched (macOS, curl 8.7.1) with the prescribed command `curl -sS -L -A "Mozilla/5.0" -o <file> -w "%{http_code} %{size_download}\n" <url>`. The only addition was `-D <file>.headers`, so that the response headers and redirect chain were kept. The status and byte count reported are those of the final response after redirects. A wrapper script waited 2.5 s before every request, so at least 2 s passed between requests to any host. It ran `date -u +%Y-%m-%dT%H:%M:%SZ` immediately before each request and appended the timestamp, URL, status, bytes and local file to a fetch log. HTML was converted to text with a short script that uses the Python 3.9 standard-library `html.parser`. It drops script, style, noscript, svg and template content, drops head content except the title, and breaks lines at block elements. PDFs were converted with `pdftotext -layout` (poppler, `/opt/homebrew/bin/pdftotext`); one two-column slide was re-extracted with `-raw` to recover reading order. Text was split into pages at form feeds. Page numbers below are therefore PDF page (or slide) indices; where a document prints page numbers, they coincide. The subagent read every converted text; the executor checked against the texts the passages this record's users rely on most (items 1, 3, 4, 6, 9 and 12). Nothing below comes from a search snippet, a summary tool or memory. WebSearch was not used, because this session's search budget was already exhausted. The three URLs not given in the executor's instructions were taken either from the repository's own evidence base (`docs/evidence/E4_community-register.md`, entry CB10; `docs/research/ELO-RESEARCH_v1_0.md`, refs [60] and [63]) or from links in fetched pages; each was then fetched and read like the others. Two archived copies were tried (web.archive.org), one for each of two refused pages; this is stated under items 10 and 12. All raw files, text conversions, response headers and the three helper scripts were kept in that temporary folder. FIDE rules mentioned below are reported as the named author states them. None was checked against the FIDE Handbook in this sweep, so under hard rule 3 each is NOT VERIFIED as a FIDE rule.

| # | Item | Status | Fetched (UTC) |
|---|---|---|---|
| 1 | Ghita, Lichess blog post, 17 Feb 2026 | PARTLY VERIFIED (the "travel adjustment" is named but not defined; the post proposes no repair) | 2026-10-10T00:49:58Z |
| 2 | Ghita, "FIDE Ratings Revisited", June 2025 (Substack original; FRBE copy of the revised version) | VERIFIED | 2026-10-10T00:50:29Z (FRBE 00:50:49Z) |
| 3 | Sonas, "Repairing the FIDE Standard Elo rating system", 20 Jul 2023 (fide.com) | VERIFIED | 2026-10-10T00:51:17Z |
| 4 | Sonas, "Compression and Calculation Improvements: Supplemental Report", 29 Oct 2023 (fide.com) | VERIFIED | 2026-10-10T00:52:13Z |
| 5 | Sonas, "Compression and Calculation Improvements: Final Report", 11 Jan 2024 (qc.fide.com) | PARTLY VERIFIED (found and read, but it predates March 2024 and so holds no post-March-2024 measurement) | 2026-10-10T00:53:36Z |
| 6 | Glickman, "The Glicko system" (glicko.pdf) | VERIFIED | 2026-10-10T00:54:52Z |
| 7 | Glickman, "Example of the Glicko-2 system" | VERIFIED | 2026-10-10T00:54:57Z |
| 8 | Universal Rating System (Wikipedia; universalrating.com) | PARTLY VERIFIED (https site refused the connection; the 2017 GCT press release returned HTTP 403; no numeric weights published) | 2026-10-10T00:55:34Z (site 00:55:40Z–00:57:09Z) |
| 9 | Kaggle 2010; Sismanis, Elo++ (arXiv:1012.4571) | VERIFIED (Elo's rank comes from the ChessBase announcement under item 10; the Kaggle page is a JS-only shell) | 2026-10-10T00:57:29Z |
| 10 | Kaggle 2011, Deloitte/FIDE Chess Rating Challenge | PARTLY VERIFIED (FIDE-prize winner and his system NOT VERIFIED: Kaggle blog HTTP 403, no archived copy; FIDE adoption not found; the chessmetrics index does not exist) | 2026-10-10T00:58:21Z |
| 11 | Coulom, "Whole-History Rating" (WHR.pdf) | VERIFIED | 2026-10-10T01:00:31Z |
| 12 | Glickman, US Chess ratings workshop, 18 Jul 2024 | VERIFIED from a web.archive.org copy (live URL HTTP 403, Cloudflare challenge) | 2026-10-10T01:01:01Z (archive 01:01:15Z) |

---

## 1. Vlad Ghita, "Why chess ratings don't mean what they used to" (Lichess blog) — PARTLY VERIFIED
- URL: https://lichess.org/@/vlad_g92/blog/why-chess-ratings-dont-mean-what-they-used-to/tVDQ1LiL
- Fetched: 2026-10-10T00:49:58Z, HTTP 200, 40,217 bytes. No mirror.
- Facts (paraphrased; short quotes ≤ 15 words with section):
  - Author handle **Vlad_G92** (byline and profile links); the cover-image caption names the author as Vlad Ghita. Published **17 Feb 2026, 18:35 UTC** (`<time datetime="2026-02-17T18:35:06.497Z">`). Lichess flags the post as containing sponsored content, affiliate links or advertising. The post summarises the author's book *The Rating Revolution* (foreword by GM Levon Aronian).
  - Scope (page description): a data investigation into the FIDE rating list for 2021–2025.
  - **Cross-border sample:** a "recursive, travel-adjusted model on nearly ~200k cross-border classical games from 2025" (section "When a 1900 isn't a 1900 everywhere"). The wording "nearly ~200k" is the author's; no exact count is given. Same section: in 2025 more than 80% of FIDE-rated chess was played between players of the same federation.
  - **Per-game weight:** logistic weighting "W = E(1-E), capped at 90%-10% odds", so that even very lopsided pairings carry some information (section "Why travel exposes the truth", step 1). E is not defined explicitly in the post.
  - **Recursion:** federation estimates are updated jointly ("checking rulers against other rulers") until stable; the algorithm "converged after 5 iterations to a deviation of less than 0.1 Elo" (step 2). It is also said to have "performed better than a first-order model on a held-out set" (step 2).
  - **Output scaling:** deviations from expected score are converted to Elo units; for example, scoring 12% above expectation is presented as about 100 Elo under-rated (step 3).
  - **Travel adjustment:** the model is called "travel-adjusted", but the post gives no definition, formula or parameter for the adjustment.
  - **Federations named.** Under-rated (outperforming their ratings against foreign opposition): Vietnam +101, China +100, Uzbekistan +96. Over-rated (underperforming against foreign opposition): Switzerland −64, Austria −64. The author says poorly connected federations lack reliable signals and that he "erred on the side of caution" when plotting them. The pattern is said to persist over longer horizons (no figures given). Serbia case study: gaps of −8 against Germany (about 300 games), −127 against Turkey, −101 against India and −171 against Mongolia; Serbia is described as a "convergence corridor".
  - Other illustrations: a 1900 who draws a 1500 loses 8.4 points, because Elo expects 92% at a 400-point gap. Age-cohort directions (charts not in the text): under-18 gain; 19–34 near zero; 35–49 slightly negative; 50+ steepest decline.
  - **Repair:** none is specified. The post says the book proposes a repair system and asks whether a global rating should be historically stable or continuously recalibrated.
- Not found in the text: a definition of the travel adjustment; a definition of E; an exact game count; any concrete repair (activity bonus, recalibration of the logistic scale, resets, safeguards), which the post defers to the book.

## 2. Vlad Ghita, "FIDE Ratings Revisited" (June 2025) — VERIFIED
- URLs: Substack original https://vladchess.substack.com/p/fide-ratings-revisited (single attempt); FRBE republication https://blog.frbe-kbsb-ksb.be/blog/fide-ratings-revisited/ (cross-check).
- Fetched: Substack 2026-10-10T00:50:29Z, HTTP 200, 350,044 bytes. FRBE 2026-10-10T00:50:49Z, HTTP 200, 157,413 bytes. No mirror needed.
- Facts:
  - **Two versions.** The Substack original is by Vlad Ghita, dated Jun 24, 2025 (`datePublished` 2025-06-24T15:28:36Z). The FRBE page was posted on 25.06.2025 by Steven Bellens and copies the author's Lichess post (Vlad_G92, `BN89yF7d`; not fetched here). Its closing note says the original appeared on Substack on June 24 and that this is "an upgraded write-up". The main suggestion is worded identically in both versions.
  - **Data:** FIDE standard data from March 2024 to June 2025 (introduction). For the federation chart, the June 2025 FIDE standard list was merged with the URS dataset, keeping players present in both. Federations with fewer than 500 such players were dropped, and the top 15 over- and under-rated were plotted (Substack footnote 7). Pre-pandemic activity figures come from a FIDE rating-analytics article (footnote 4). The age segmentation is taken from Sonas's Supplemental Report, p. 8.
  - **Main findings (paraphrased):**
    - Players are clustering around 1500, with a pile-up at the 1400 floor that the author attributes to the floor rule.
    - About 3,500 new standard-rated players arrive each month, yet the average rating falls about 1 Elo a month.
    - Deflation shows at fixed percentiles, including the top 1%. The distribution has become more skewed, more sharply peaked and narrower, and the 1800–1999 band is giving way to 1400–1599.
    - Juniors ("improvers") gain consistently. The K-factor asymmetry (K=40 against K=20) ought to be inflationary, yet deflation persists.
    - FIDE-versus-URS gaps by federation: Denmark over-rated by 162 points on average and Sri Lanka under-rated by 227 on average. These figures appear in the FRBE/Lichess text; in the Substack text they are only in a chart.
    - Elo's three "blind spots": the logistic assumption (the author argues for log-normal); static K (he argues for a context-dependent volatility parameter, and the FRBE version names Glicko); and geographic and economic disparities.
  - **What it suggests FIDE do:** "start tracking URS ratings and display them prominently on each player" page for about one year as an evaluation. Later, "running a Glicko-2 type algorithm in parallel might be desirable" (Substack footnote 8; FRBE conclusion).
  - The author's account of the 2024 reforms is his own secondary statement and is NOT VERIFIED as FIDE rules here. He lists a one-time 0.4 × (2000 − rating) increase below 2000, the floor raised from 1000 to 1400, two fictitious draws against 1800 in the initial rating, and the 400-point rule restored. The same caveat applies to his K-factor history.
- Not found in the text: none of the requested facts is missing.

## 3. Jeff Sonas, "Sonas Proposal: Repairing the FIDE Standard Elo rating system" — VERIFIED
- URL: https://www.fide.com/docs/presentations/Sonas%20Proposal%20-%20Repairing%20the%20FIDE%20Standard%20Elo%20Rating%20System.pdf
- Fetched: 2026-10-10T00:51:17Z, HTTP 200, 2,305,001 bytes (19 pp.; server Last-Modified 21 Jul 2023). No mirror.
- Facts:
  - **Date/version:** "by Jeff Sonas (20 July 2023)" (p. 1); the PDF metadata title carries "(20-JUL-2023)". No version number is given.
  - **Diagnosis, and where the deflation is.**
    - The past decade brought "extreme rating deflation"; ratings are spread too far apart, and it is getting worse every year (p. 1).
    - The system still works reasonably for grandmasters, but 99% of players are below 2400 (p. 3).
    - Deflation spreads outward from new players, and grandmasters are the most shielded (p. 3). It has crept up through master level and is starting to reach grandmasters (p. 9).
    - For players rated 1000–2400 the list spans 1,400 points, but their strength spans only about 1,000 (p. 9). Sonas suggests "rating expansion" may describe it better (p. 5).
  - **Cause, as he sees it.**
    - The successive lowering of the minimum rating brought in many young, fast-improving players with very low initial ratings (pp. 2–3). He dates the steps as 2000 in Jan 1993, 1800 in Oct 2001, then 1600, 1400 and 1200, and 1000 in Aug 2012.
    - The 2014 K-factor increases were not enough (p. 3). The active pool doubled in 2013–2020 (p. 3), and COVID made matters worse (p. 4).
    - The initial-rating formula is a "primary contributor" (p. 15).
  - **Changes proposed (two corrective measures; pp. 1–2, 10–12):**
    - **(a) Compression.** On the January 2024 list, every player rated below 2000 receives a one-time increase of "(0.40) x (2000 – Rating)" (p. 10). It is applied after that month's normal calculation, to active and inactive players alike, whether or not they played (p. 10).
      - Range: 1000–2000 is mapped onto 1400–2000, with increases of 0–400 points. The order of players is preserved, and the change touches the bottom 85% (pp. 1, 10).
      - Worked examples include a newcomer whose initial rating of 1900 becomes 1940 (p. 11).
      - The Compression must come one month before the calculation changes. Jan/Feb 2024 is proposed; Oct/Nov 2023 or Mar/Apr 2024 would also do (p. 10).
    - **(b) Calculation Improvements,** from the February 2024 list onward (p. 12):
      - (1) minimum rating 1400 instead of 1000;
      - (2) the 400-point rule restored, with no limit on how often it applies in one tournament;
      - (3) initial ratings include two additional hypothetical draws against 1800-rated opponents, with at least 5 actual games against rated players still required;
      - (4) plus scores rated as a performance rating, like minus scores, instead of the plus score × (K/2), capped at 2200;
      - (5) partial unrated results from before the Compression discarded (a "fresh start").
  - **K:** no change to K is proposed. The examples use the existing K values, e.g. K=40 on p. 13.
  - **Expectancy curve and the 400-point rule.**
    - Empirical curves of score against rating difference, for 2008–12, 2013–16, 2017–20 and 2021–23, are all shallower than the Elo-table curve, and grow shallower over time (pp. 5–6). For example, in ~1500 vs ~2100 games the lower-rated side scored 8% ten years ago and 15% recently, while the table predicts about 2% (p. 5).
    - No change to the table itself is proposed; the remedy acts on the ratings.
    - The 400-point rule caps the expected score at 92%, and FIDE had recently limited it to once per event. Favourites by 400 points score under 80%, and about 650–700 points are needed before a favourite reaches 90% (pp. 15–16).
    - He recommends reinstating the rule for all games. If the changes work, the rule could be weakened to 500 or 600 points or removed: "Perhaps it can be re-assessed after a year." (p. 16).
  - **Evidence.**
    - More than 140,000 games since 2012 for the 1500/2100 comparison (p. 4), and more than 13 million standard games over 15 years for the curves (p. 6).
    - Summary crosstables of rating group against rating group for 2008–12 and 2021–23 (pp. 7–9).
    - A database tool that replicates 15 years of monthly FIDE calculations (pp. 9–10).
    - Simulations of deployment in mid-2023 and in January 2017 (p. 10; pp. 16–19). In the 2017 scenario, the simulated favourites' curve for 2017–19 almost perfectly overlays the Elo curve (p. 19). COVID complicates the simulations (pp. 10, 19).
  - **One-off or ongoing:** the Compression is one-time. The Calculation Improvements are permanent and are meant to stop deflation returning by "introducing some mild inflationary effects into the rating regulations" (p. 2; also p. 15).
  - **Monitoring:** no monitoring programme is recommended. The text offers only the one-year re-assessment of the 400-point rule and an acknowledgement that success is not guaranteed (p. 16).
  - Sonas notes that his analysis pointed to compressing above 2000 as well, but he stopped at 2000 to avoid effects on titles and professional players (p. 18).
- Not found in the text: a version number; any change to K; any change to the expectancy table; a general monitoring regime.

## 4. Jeff Sonas, "Compression and Calculation Improvements: Supplemental Report" — VERIFIED
- URL: https://www.fide.com/docs/presentations/Sonas%20Supplemental%20Report.pdf
- Fetched: 2026-10-10T00:52:13Z, HTTP 200, 16,226,237 bytes (47 pp.; server Last-Modified 02 Jan 2024; metadata "(as of 29-OCT-2023)"). No mirror.
- Facts:
  - **Date:** "(29 October 2023)" (p. 1). FIDE published the July proposal and invited public comment through July, August and September (p. 1).
  - **Alternatives weighed: amount of compression.**
    - A Compression to 1400 Elo would solve about two-thirds of the problem. A lesser "Compression to 1200 Elo", which had some support within FIDE, would solve about one-third (pp. 1–2).
    - Compressing to 1400 adds about 70 million rating points and compressing to 1200 about 35 million, against an estimated total deflation of about 110 million. That is 64% against 32% of the problem (p. 5).
    - His recommendation is unchanged: 1400 (p. 3).
    - A complete fix would require touching ratings above 2000. "It would be appropriate mathematically to lower the ratings of the highest-rated players", but that would be a big practical problem (p. 39; see also p. 2).
  - The Compression is "intended as a one-time intervention", not a recurring adjustment for improving juniors (p. 6).
  - **Justification of the 40%.** The analysis is restricted to a "stable" age group, 20–38, defined from 2015–21 data, with peak age 29 (pp. 7–8), and to games from 2022–23.
    - Adjacent 200-point groups 188–196 points apart on average score as if about 117 apart, which implies roughly 40% compression (pp. 9–10).
    - A class-interval analysis using the handbook table (200 points gives 24%) finds three 200-point classes between 1000 and 2000, not five (pp. 10–12).
    - An iterative group adjustment, anchored by leaving 2000+ unchanged, gives a linear slope of 37.7% on Jan 2022–Mar 2023 data. The slope is 32% on 2019–21 data, and about 42% if juniors and seniors are included (pp. 13–15).
  - **Deflation at elite level** (pp. 16–21): the number of players rated 2200+ has fallen every year since 2018, to 20,303 in Jan 2023 (p. 17). Players rated 2600+ fell from 269 in Nov 2020 to 234 in Oct 2023 (p. 19).
  - **Inflation risk:** he expects no inflation from the compression. Simulations place it in Jan 2017 and Jan 2022 (pp. 22–29). The simulator replicates FIDE's calculations for 2008–2023, starting from the Jan 2008 list (pp. 23–24).
  - **Calculation improvements in this report:**
    - Two hypothetical draws against 1800 for newcomers, a mild inflationary factor (p. 3).
    - Revert the 400-point rule to its pre-2022 form, unlimited per event (pp. 3, 30–39). Three variants are weighed: the original rule, the 2022 "1-upgrade" rule, and no rule. The analysis uses games with gaps of 412 points or more; their share of all games rose from 6% in 2010–11 to 14% in 2020–23 (p. 36).
    - Apply the rule to the lower-rated player as well (expected score 0.08); since Jan 2022 it was apparently not being applied to them (pp. 3, 40–42).
    - Compress rapid and blitz at the same time, by the same formula (pp. 3, 43–45).
    - Keep 5 games, not 9, for an initial rating. A 9-game simulation produced 75,000 fewer rated players by Apr 2023 and no better ratings (pp. 3, 46–47).
  - **URS as an auxiliary rating:** this appears only in a quoted community comment by Vlad Ghita. He proposes showing URS as an "auxiliary rating" on FIDE player pages from 1 Jan 2023 to 31 Dec 2024, followed by a final report (p. 4). Sonas does not analyse it; he writes "I hope that FIDE will be able to consider these ideas and others" (p. 4).
  - **K:** Sonas proposes no change to K. The quoted community suggestions (p. 4) are:
    - cut junior K from 40 to 32 or 30 (Ghita);
    - use K=5 for adults playing under-18s (Compton);
    - raise the threshold where K drops from 20 to 10 from 2400 to 2600 (Arkell);
    - add points to juniors' ratings when computing their opponents' expectations ("junior additions"), as Chess Scotland does (Bryson).
  - **Expectancy table:** the handbook table (8.1.2) serves as the yardstick (pp. 10, 30). The report says the Elo tables "aren't really functioning very well anymore" (p. 1), but proposes no change to them.
- Not found in the text: any evaluation by Sonas of URS as an auxiliary rating; any K proposal of his own; any change to the expectancy table.

## 5. Jeff Sonas, "Compression and Calculation Improvements: Final Report" (2024) — PARTLY VERIFIED
- URL: https://qc.fide.com/wp-content/uploads/2024/03/Sonas-Final-Report-as-of-11-JAN-2024.pdf. The file is on FIDE's Qualification Commission site, a fide.com subdomain. The URL was located in the repository's evidence register (`docs/evidence/E4_community-register.md`, CB10) because WebSearch was unavailable. Provenance: the QC post "New Rating Regulations and Compression: the data behind the change" (13 Mar 2024, https://qc.fide.com/2024/03/13/new-rating-regulation-the-data-behind-the-change/) shares "the final report from Jeff Sonas" and links this exact file.
- Fetched: 2026-10-10T00:53:36Z, HTTP 200, 4,102,695 bytes (19 pp.; server Last-Modified 13 Mar 2024). QC pages: home 00:54:13Z (HTTP 200, 82,053 bytes); "Ratings" category 00:54:24Z (200, 74,572); the 13 Mar 2024 post 00:54:41Z (200, 56,676).
- Facts:
  - Title page: "Compression and Calculation Improvements: Final Report -- by Jeff Sonas (11 January 2024)" (p. 1). It is a written version of his presentation at the QC open meeting on 12 Dec 2023.
  - Timeline (p. 1): QC "health check" in spring 2023, the July proposal, a ten-week consultation, the October supplemental report, the December QC meeting, then FIDE Management Board and Council approval, effective March 2024.
  - **Measured after March 2024: nothing.** The report predates the change. Its data are standard games from the past five years (pp. 2, 4), simulations of a compression in Jan 2022 (pp. 17–19), and the January 2024 list, which had 20,088 players rated 2200+ (p. 9).
  - **Diagnosis restated:** "FIDE Elo ratings are too spread out." (p. 3). Between 1000 and 2000, differences in performance are about 60% of differences in published rating (p. 7). "Downward expansion" is more accurate than "deflation" (p. 7). The initial-rating formula is the major culprit, a "deflation engine" (pp. 11–13).
  - **Expectancy table:** he looked into changing the Elo tables, and "it turns out that wouldn't help either" (p. 3).
  - **Newcomers.** The two hypothetical draws against 1800 were chosen by simulation; he notes 1800 is more like 1667 by today's standards (p. 13). A dozen or more years earlier he had suggested two draws against 1600, which was not adopted (p. 12). The minimum stays at 1400 because simulations showed deflation returning quickly if lower floors stayed open (p. 13). Plus scores are rated as a performance rating with a 2200 cap (p. 14).
  - **400-point rule:** revert to the pre-2022 form (pp. 14–17). A simulated compression cuts games with gaps of 412 points or more from 14% to 4% of all games, and the original rule still fits best (p. 17). Rapid and blitz should get the same changes at the same time (p. 18).
  - **Further steps:** it is possible "we will eventually need to take additional steps" (p. 14).
    - The biggest vulnerability is K=40 juniors mostly exchanging points with other K=40 juniors, so that no points enter the pool. Chess Scotland-style junior additions may become necessary (p. 14).
    - FIDE may need further steps "if these measures prove inadequate" (p. 19).
    - His understanding is that "the QC will keep monitoring the situation" (p. 19).
    - Expected effect: the full compression closes about two-thirds of the gap, the halfway one about one-third (p. 19).
  - **No later Sonas report found:** the first page of the QC "Ratings" category listing (posts dated 26 Oct 2023 to 9 Sep 2026) shows no later Sonas report. This check is not exhaustive.
- Not found in the text: any measurement after March 2024, which the document predates; any later Sonas report on qc.fide.com.

## 6. Mark Glickman, "The Glicko system" (glicko.pdf) — VERIFIED
- URL: http://www.glicko.net/glicko/glicko.pdf (301 redirect to https, then 200). The document's own title is "The Glicko system", by Dr. Mark E. Glickman, Harvard University.
- Fetched: 2026-10-10T00:54:52Z, HTTP 200, 136,230 bytes (6 pp.). No date in the text; server Last-Modified and PDF creation are both 11 Sep 2016.
- Facts:
  - **Purpose:** Glickman created the system in 1995 to address rating reliability, which Elo ignores (p. 1). He illustrates it with a player returning after years away against a player who plays every weekend. Elo turns out to be a special case of Glicko (p. 1).
  - **RD:** the "ratings deviation", a standard deviation that measures uncertainty in a rating. It is high for players who compete rarely or have played few games (p. 2). The 95% interval is given as rating ± 2 RD on p. 2 and as ± 1.96 RD on p. 5.
  - Ratings change only through games. RD falls with games and rises with time spent not playing (p. 2). Changes are not zero-sum: the opponent's loss depends on both players' RDs (p. 2).
  - **Update (p. 3):** r′ = r + [q / (1/RD² + 1/d²)] · Σ_j g(RD_j)(s_j − E_j), with q = ln 10/400, and RD′ = (1/RD² + 1/d²)^(−1/2). Here 1/d² measures the information in the period's games.
    - *My reading of the p. 3 formula, not a sentence in the text:* the multiplier q/(1/RD² + 1/d²), equivalently q·RD′², plays the role of K.
    - The multiplier is larger when the player's own RD is larger, and smaller the more informative the period's games are. Each game's surprise is damped by g(RD_j), which is smaller when the opponent's RD is large.
  - **Unrated players:** rating 1500, RD 350 (p. 3).
  - **Growth of RD without games:** before each period, RD = min(√(RD_old² + c²), 350), "where c is a constant that governs the increase in uncertainty between rating" periods (p. 3). Over t idle periods, RD = min(√(RD_old² + c²t), 350) (p. 6).
    - c can be chosen for predictive accuracy (per his 1999 Applied Statistics paper), or by how long an RD takes to return to the unrated level. Example: RD 50, two-month periods and 5 years give c = 63.2 (pp. 5–6).
  - **Practical notes:** the system works best with 5–10 games per player per period (p. 2). He recommends an RD floor, such as 30, so that improving players can still move (p. 6).
  - **Worked example:** a 1500 player with RD 200 meets 1400/30 (win), 1550/100 (loss) and 1700/300 (loss), ending at 1464 with RD 151.4 (p. 4).
- Not found in the text: none of the requested facts is missing (the "role of K" phrasing is a reading of the formula, as noted).

## 7. Mark Glickman, "Example of the Glicko-2 system" — VERIFIED
- URL: http://www.glicko.net/glicko/glicko2.pdf (301 redirect to https, then 200).
- Fetched: 2026-10-10T00:54:57Z, HTTP 200, 124,065 bytes (6 pp.; dated March 22, 2022, Boston University, p. 1).
- Facts:
  - **Volatility σ:** it "indicates the degree of expected fluctuation in a player" rating. It is high when performances are erratic, for example exceptionally strong results after a stable period, and low for consistent play. It does not enter the 95% interval (p. 1).
  - **System constant τ:** τ "constrains the change in volatility over time". Reasonable values are 0.3–1.2, to be tested for predictive accuracy. A smaller τ keeps volatility, and hence ratings, from changing a lot after very improbable results; τ can be as small as 0.2 if such results are expected (pp. 1–2).
  - **Role in the update:** each period the RD is first inflated by the new volatility, φ* = √(φ² + σ′²) (Step 6). A player who does not compete gets only this step, so their RD grows by the volatility (p. 4). The rating step is φ′² · Σ g(φ_j)(s_j − E_j) (Step 7, p. 4).
    - *Reading, not stated in the text:* σ takes the place of Glicko's fixed c, per player and updated each period.
  - σ′ is found by an iterative Illinois (regula falsi) procedure, revised on Feb 22, 2012 (pp. 2–4).
  - **Defaults:** unrated players start at 1500, RD 350 and σ 0.06, the last depending on the application (p. 2). The scale factor is 173.7178 (p. 2). The system works best with at least 10–15 games per player per period (p. 1).
  - **Worked example:** σ′ = 0.05999, r′ = 1464.06, RD′ = 151.52 (pp. 5–6).
- Not found in the text: none of the requested facts is missing.

## 8. Universal Rating System (URS) — PARTLY VERIFIED
- URLs and outcomes:
  - Wikipedia https://en.wikipedia.org/wiki/Universal_Rating_System: 2026-10-10T00:55:34Z, HTTP 200, 85,836 bytes. Page last edited 27 Apr 2026 (oldid 1351439509); flagged since June 2017 as relying excessively on primary sources.
  - https://www.universalrating.com: 00:55:38Z, 301 to https://universalrating.com/, then the connection to port 443 failed (curl exit 7). No content.
  - http://www.universalrating.com: 00:55:40Z, 301 to http://universalrating.com/, then HTTP 200, 135,814 bytes (home page with news items).
  - Linked FAQ page http://universalrating.com/faqs.php: 00:56:28Z, 200, 15,407 bytes.
  - Linked About page http://universalrating.com/about-us.php: 00:56:31Z, 200, 17,479 bytes.
  - Linked press release "GCT announces formal launch of URS and 2017 wildcards.pdf": 00:57:09Z, HTTP 403 (nginx), not read.
  - No mirror tried.
- Facts:
  - **Who:** Wikipedia names Jeff Sonas, Mark Glickman, J. Isaac Miller and Maxime Rischard. The site's About page (§4) describes a research team working since 2015, led by Glickman (Harvard; chair of the US Chess ratings committee since 1992) and Sonas (inventor of Chessmetrics), with major contributions from Miller (University of Missouri-Columbia) and Rischard (Harvard).
  - **Funding:** a collaborative research project funded by the Grand Chess Tour, the Kasparov Chess Foundation and the Chess Club and Scholastic Center of Saint Louis, after more than two years of research (About §1).
  - **When:** the first list was for January 2017 (home page). Wikipedia says the first list followed two years of research, with monthly lists from August 2016 published retroactively. A pilot phase was to run through 2017 (About §5).
    - Two later news items on the home page refer to the inception of the lists in "January 2018" and to the first lists in "March 2018". This conflicts with January 2017 and is unresolved.
  - **How time controls are combined.**
    - URS publishes one rating per player, meant as classical strength (at least 2 hours for the first 60 moves). It is informed by every over-the-board game no faster than game-in-5, and faster games count for less (FAQ Q1, Q4–Q6).
    - The model "treats faster games as progressively more chaotic" (About §6).
    - Each player also gets a Rapid "Gap" and a Blitz "Gap": the rating advantage needed for 50% at G/30 or G/5 against an opponent whose play does not degrade (About §7).
    - No numeric weights are published.
  - **Method.**
    - URS is a weighted performance rating over several years, with older games discounted "by applying an exponential decay rate". All players are re-estimated together, searching for the most likely current ratings (FAQ Q1).
    - Each list pools "all games within the previous 72 months (6 years)". The ratings are self-consistent and do not depend on any earlier list (FAQ Q2).
    - Ratings can change without new games (Q8). Players inactive for more than a year are removed from the lists (Q9); after the 2020 COVID date-compression this became 18 months (home page, Nov 2020).
    - For players with few recent results, more weight goes on their earlier established strength or, for new players, on the typical strength of players their age (home page, Nov 2020).
    - The About page says URS considers the "entire history" of over-the-board games going back several years, and iteratively computes performance ratings for all players at once (§6).
    - Online games were excluded in the pilot (Q7). Over-the-board Chess960 has been rated since 2018, with a further reduced weight (home page).
    - The algorithm was revised in May 2017, after concerns that isolated juniors were rated too high, and again in October 2017, each time with historical ratings recalculated (home page).
  - **Use:** Wikipedia says URS was introduced to determine seedings and qualifications for the 2017 Grand Chess Tour. The site's own news confirms later use: Nakamura, Grischuk and Mamedyarov were invited to the 2018 GCT on their URS ratings of 31 Jan 2018, and URS lists fed 2019 and 2020 GCT selection and wildcards.
- Not found in the text: the labels "Bayesian" or "whole-history" for the method (the site says "entire history ... going back several years"); numeric time-control weights or the decay rate; primary confirmation of the 2017 GCT use (press release HTTP 403; only Wikipedia states it).

## 9. Kaggle 2010, "Chess ratings – Elo versus the Rest of the World"; Sismanis, Elo++ — VERIFIED
- URLs: https://arxiv.org/abs/1012.4571; https://arxiv.org/pdf/1012.4571; https://www.kaggle.com/c/chess
- Fetched: abstract page 2026-10-10T00:57:29Z, HTTP 200, 42,573 bytes. PDF 00:57:32Z, HTTP 200, 248,872 bytes (8 pp.). Kaggle 00:57:35Z, HTTP 200, 6,072 bytes, a JS-only shell: only the title "Chess ratings - Elo versus the Rest of the World | Kaggle" rendered, with no competition content.
- Facts:
  - Yannis Sismanis, "How I won the 'Chess Ratings – Elo vs the Rest of the World' Competition", December 2010; arXiv v1 submitted 21 Dec 2010 (abstract page; p. 1).
  - **Data:** more than 73 thousand month-stamped game outcomes between roughly 8 thousand players. The hold-out set was about 8 thousand games from the last five months; 20% of it scored the public leaderboard and the rest was private (p. 1). The time-weight definition takes the earliest game as month 1 and the latest as month 100 (p. 3). The metric is a player/month-aggregated RMSE (PM-RMSE) (pp. 1, 3).
  - **Elo++.**
    - One rating per player, with a logistic (base-e) prediction and a White-advantage parameter γ added to White's rating (p. 3).
    - Time weighting: w = ((1 + t − t_min)/(1 + t_max − t_min))², inspired by Chessmetrics (p. 3).
    - Regularisation pulls each rating toward the time-weighted average of the player's opponents' ratings, which "is used as a neutral prior for regularization" (p. 4).
    - The loss is the weighted squared error plus λ Σ (r_i − a_i)² (p. 4). In each update the pull is scaled by λ/|N_i|, where N_i is the player's set of opponents (p. 5).
    - Fitted by stochastic gradient descent, about 50 iterations, in about 100 lines of R (pp. 2, 5–6).
  - **Parameters:** "only two global parameters (white's advantage and regularization constant)" (abstract), besides one rating per player. Cross-validation gave γ = 0.2 and λ = 0.77 (p. 6). Rescaled, White's advantage is about 34.7 Elo points (p. 6).
  - **Result:** PM-RMSE 0.693561 on the private set after a post-contest bug fix; 0.69477 was reported on Kaggle (p. 6 and footnote). Elo++ beat TrueSkill, Chessmetrics, Glicko, Elo and the other approaches tested (pp. 2, 6). Sismanis calls it the most popular Kaggle competition to that date (p. 7).
  - **Where plain Elo ranked:** not stated in the paper. The ChessBase announcement of 20 Feb 2011 (item 10) says the Elo benchmark finished "141st place out of 258", in a contest of more than 3,500 submissions from teams in 41 countries.
- Not found in the text (paper): Elo's rank (found in the item 10 announcement instead).

## 10. Kaggle 2011, "Deloitte/FIDE Chess Rating Challenge" — PARTLY VERIFIED
- URLs and outcomes:
  - http://www.chessmetrics.com/KaggleComp/1-TimSalimans.pdf: 2026-10-10T00:58:21Z, HTTP 200, 63,261 bytes (4 pp.; Last-Modified 14 May 2011).
  - http://www.chessmetrics.com/KaggleComp/: 00:58:26Z, HTTP 403.14 (IIS: directory listing disabled, no default document), 5,110 bytes. No index page exists at this URL.
  - https://en.chessbase.com/post/sonas-the-deloitte-fide-che-rating-challenge: 00:58:29Z, HTTP 200, 135,596 bytes (published 2011-06-08, by Jeff Sonas).
  - https://www.kaggle.com/c/ChessRatings2: 00:58:32Z, HTTP 200, 6,140 bytes, a JS-only shell (title only).
  - Supplementary, URLs taken from repo `ELO-RESEARCH_v1_0.md` refs [60] and [63]:
    - ChessBase announcement https://en.chessbase.com/post/the-deloitte-fide-che-rating-challenge: 00:59:42Z, HTTP 200, 106,185 bytes (published 2011-02-20, by Jeff Sonas).
    - Kaggle blog on Medium, "Could World Chess Ratings be decided by the 'Stephenson System'?": 00:59:39Z, HTTP 403 (Cloudflare block). The one archived-copy attempt (web.archive.org) at 01:00:15Z returned 404: not archived.
- Facts:
  - **Data:** a dataset prepared by Sonas from FIDE's archives, covering all known game outcomes among 54,000 players in FIDE-rated events from Jan 1999 to Dec 2009. That is about two million games, with players identified only by anonymous IDs. Contestants predicted 88,000 matchups from Jan–Mar 2010 (results article, 8 Jun 2011).
    - The 20 Feb 2011 announcement instead says "over 1.84 million" games, more than 54,000 players, eleven years, and "a further 100,000 games" to predict. The two articles differ (88,000 vs 100,000 games to predict; about 2 million vs 1.84 million in training). Unresolved.
  - **Timing:** the contest ran Feb–May 2011, 12 weeks (results article). The announcement says it runs until May 3; Salimans gives February 7 to May 4 (p. 1). Two submissions per team per day were allowed.
  - **Scoring:** game by game, using a "log-likelihood" score, later named binomial deviance (results article). The 2010 contest had scored at the player/month level.
  - **Winner:** Tim Salimans, a PhD student in econometrics at Erasmus University Rotterdam, won the $10,000 first prize from Deloitte Australia, out of 189 teams (results article).
    - His model was an ordered probit with factorised approximate Bayesian inference (expectation propagation) and a White advantage (Salimans pp. 1–2).
    - Normal skill priors were centred on a weighted average of the opponents' skills, "as was first done by Yannis Sismanis" (p. 2).
    - A time-weighted likelihood used weights specific to each player (pp. 2–3).
    - Post-processing exploited the match schedule (Swiss-pairing information), including a rooted-PageRank variable (pp. 3–4). He calls this "less than ideal for the original goal of finding a good rating system" (p. 4).
  - **Other finishers (results article):** 2nd "Sami"; 3rd Andy Cotter, who blended logistic regression with a modified Glicko; 4th Jason Tigg and David Clague; 5th Vladimir Nikulin; 6th the 2010 winner, Sismanis. Sonas calls the schedule loophole a flaw in his contest design.
  - **Follow-up stage:** contestants predicted Apr–Jun 2010 games. Salimans and Tigg/Clague finished top two. Over 112,837 games, their averaged "winners' ensemble" scored 0.248 against Elo's 0.257.
  - **Plain Elo** "finished in 80th place out of 189 in the latest contest". Sonas judges the winners' systems about 15% more accurate than Elo (results article).
  - **FIDE prize:** a separate category for the most promising practical enhancement or alternative to Elo. FIDE representatives were to choose it from the ten most accurate entries meeting a restrictive "practical chess rating system" definition. The winner would present the system at a FIDE meeting in Athens (announcement). On 8 Jun 2011 the finalists were "currently being evaluated" by FIDE representatives (results article).
- Not found in the text / not verified:
  - The identity of the FIDE-prize winner: Alec Stephenson is not named in any text read.
  - What his system adds to Glicko: NOT VERIFIED (Kaggle blog HTTP 403; no archived copy).
  - Whether FIDE adopted anything: NOT FOUND.
  - The Kaggle pages render no content.

## 11. Rémi Coulom, "Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength" — VERIFIED
- URL: https://www.remi-coulom.fr/WHR/WHR.pdf
- Fetched: 2026-10-10T01:00:31Z, HTTP 200, 118,886 bytes (12 pp.; p. 1 marked "Draft"; PDF created 11 Apr 2008; no year printed in the text; server Last-Modified 20 Aug 2024).
- Facts:
  - **Model:** the dynamic Bradley–Terry model, P(i beats j at t) = γ_i(t)/(γ_i(t) + γ_j(t)), with natural rating r = ln γ (p. 3). Inference is Bayesian, with a prior (p. 3). The prior on rating change over time is a Wiener process, r(t₂) − r(t₁) ~ N(0, |t₂ − t₁| w²); w = 0 gives static ratings (p. 4).
  - **Fit:** WHR "directly computes the exact maximum a posteriori over the whole rating history of all players" (abstract, p. 1).
    - Newton's method is applied to each player's vector of ratings. Because the Wiener process is Markovian, the Hessian is tridiagonal, so the cost is linear in the number of ratings (p. 5).
    - One Newton step is applied to each player in turn, iterated to convergence.
    - In incremental use, one Newton step goes to the two players of each new game, with a full pass every 1,000 games in the experiments (pp. 5–6).
  - **Uncertainty:** the covariance is "approximated by the opposite of the inverse of the Hessian" (p. 6). It is computed per player with opponents fixed at their MAP ratings. The diagonal and sub-diagonal of Σ = −H⁻¹ are obtained in linear time (p. 6; App. B.2, p. 11). The text does not use the word "Laplace".
  - **Past estimates revised:** whole rating histories are re-estimated. The motivation is the A/B example on p. 2: two newcomers play only each other; when A's rating later moves against established players, an incremental system leaves B unchanged, whereas WHR moves B too. Coulom argues that estimating past ratings more accurately improves current ones (p. 2).
  - **Evidence:**
    - KGS Go server data, 2000 to October 2007: 213,426 players, 10.8 million games (p. 6).
    - Test-set prediction rate: 55.793% for WHR against 55.121% for Elo (Table 1, p. 7), with WHR also ahead of Glicko, TrueSkill, Bayeselo and decayed history.
    - A new game is added in under 0.001 s (abstract).
    - Stated limitation: the model ignores that beginners progress faster than experts (p. 8).
- Not found in the text: the year of the paper (only in the PDF metadata); the term "Laplace approximation" (the method is described but not named).

## 12. Mark Glickman, US Chess Ratings Workshop, 18 July 2024 — VERIFIED from archived copy (live URL HTTP 403)
- URL: https://new.uschess.org/sites/default/files/media/documents/7-18-2024-ratings-workshop-2024.pdf
- Fetched: 2026-10-10T01:01:01Z, **HTTP 403**, 5,661 bytes: a Cloudflare JS challenge (`cf-mitigated: challenge`), no content. **Archived copy used** (the one attempt): https://web.archive.org/web/2024id_/https://new.uschess.org/sites/default/files/media/documents/7-18-2024-ratings-workshop-2024.pdf. It redirected (302) to the memento of 8 Aug 2024, 21:35:20 UTC and was fetched at 01:01:15Z: HTTP 200, application/pdf, 737,191 bytes (29 slides; PDF created 19 Jul 2024). The copy could not be compared byte-for-byte with the live file, which was unreachable.
- Facts (slide numbers):
  - **Title slide:** "US Chess Ratings Workshop", July 18, 2024; Mark E. Glickman, Chair, US Chess Ratings Committee (slide 1). Topics: an annual rating-monitoring analysis, a rating variance measure, and the FIDE-to-US-Chess conversion (slide 2).
  - **Drift anchor:** "Mean ratings of 'stable' players over time" (slide 3).
    - "Stable" players are active in the current and previous 3 years, aged 35–45, and hold an established rating in all four years.
    - Finding: "Ratings continue to deflate."
    - Target: "Goal is to maintain rating levels roughly to where they were in 1997."
    - The percentile charts (5th–95th) on slides 4–6 contain no extractable numbers.
  - **Bonus threshold:** "The RC" (the ratings committee, per the slides' context) voted last year to "lower the bonus point threshold by 2 points to 12", with no recommendation for further changes (slide 3, confirmed in raw reading order).
  - **Rating-floor check:** without floors, about 1% of established players would hold a rating ending in "00". The actual excess shows how much floors distort ratings (slide 7). The charts on slides 8–9 carry no text.
  - **Other topics:**
    - A proposed variance measure, built from tournament performance ratings over 3 years weighted by recency and games played, was submitted to "the EB" (abbreviation as on the slide) on 24 Feb 2024 (slides 10–23).
    - The FIDE-to-US-Chess conversion was re-fitted, effective 1 Mar 2024, after FIDE's compression (stated as Old + 0.4 × (2000 − Old)). New formulas: 932 + 0.564 × FIDE for FIDE ratings ≤ 2000, and 20 + 1.02 × FIDE above 2000. Separate youth-event formulas are also given (slides 24–28).
- Not found in the text: the numeric trend of the stable-player mean (charts only); the definition or formula of the bonus threshold (only its value, 12, and the 2-point cut).
