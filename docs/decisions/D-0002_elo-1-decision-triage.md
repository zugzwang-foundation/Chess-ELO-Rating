# D-0002 — Triage of the ELO-1 close-out decisions 1–13

Date: 2026-10-09 · Session: ELO-2 · Status: DECIDED for the TECHNICAL items (by the architect's ARCHITECTURE, recorded in D-0003); the FOUNDER items are listed, not decided

## Context

The ELO-1 close-out (`~/Downloads/zz_ELO-1_close-out_2026-10-09T1452.md`, §5) left thirteen numbered decisions. The ELO-2 brief classifies each as TECHNICAL (resolved here using the architecture of D-0003, one line of rationale each) or FOUNDER (publication, naming, visibility, licence, repository settings, political framing, contacting FIDE or anyone: not resolved, carried to the close-out for the operator).

## Triage

| # | Decision (ELO-1 wording, abridged) | Class | Resolution in v0.2 | Rationale |
|---|---|---|---|---|
| 1 | Assumptions A1–A7: confirm the reconstruction or supply the canonical list | TECHNICAL | Resolved: the canonical list supplied by the architect is used verbatim in proposal Appendix B | The architect supplied the list in the ELO-2 brief; the reconstruction in v0.1 is withdrawn |
| 2 | Junior-opponent compensation scope: juniors only, or every under-rated player | TECHNICAL | Resolved: juniors only, under 20 by birth year from the FIDE list, with the posterior-probability test of AR-4 | AR-4 fixes eligibility; the general form is harder to explain and invites gaming by adults |
| 3 | Floor policy: keep 1400 as a publication floor with the rating carried below it, lower it, or keep today's rule | TECHNICAL | Resolved: 1400 remains as a display rule; L1 keeps estimating players below it; the ledger records points leaving through the floor | AR-5 |
| 4 | Pool bonus sign: allow a negative bonus in an inflating pool, or constrain b ≥ 0 | TECHNICAL | Resolved: the per-game bonus is withdrawn; the monthly global adjustment a_t is signed and symmetric, with \|a_t\| ≤ a_cap | AR-3 derives a_t from anchor drift in either direction; a one-sided adjustment could not hold the anchor if the pool inflated |
| 5 | Publication of model estimates θ̂: public, player-only, or QC-only | FOUNDER (with one technical minimum) | Technical minimum resolved: the compensation c_j of every eligible junior and every player's K_i must be published, because arbiters need them to recompute an expectation by hand (AR-2, AR-4). Whether θ̂_i and σ_i are published for every player stays with the founder | Hand-checkability (AR-2) forces the minimum; wider visibility is a publication decision |
| 6 | Curve scale σ: fix at 400 for title-norm comparability or let it move within a cap | TECHNICAL | Resolved: σ is replaced by the per-time-control slope κ_tc of the Davidson function, re-estimated yearly within an annual change cap and published as the successor table to §8.1.2. Title-norm arithmetic is FIDE's and is not touched by this proposal; the interaction is logged as open for the QC | AR-1 |
| 7 | Rapid and blitz consistency: one clamp for all three time controls, replacing the plain 400 cap and the 600/2600 exclusion | TECHNICAL | Resolved: no caps and no clamps in any time control; one calibrated expected-score function per time control. The verified difference between the standard and rapid/blitz chapters [V 1] [V 2] is used in §7 as evidence for one framework | AR-1 |
| 8 | Pilot federation: which, and when | FOUNDER | Not resolved; listed in the close-out | Contacting a federation |
| 9 | Data handling: confirm "download, analyse, never redistribute" and the wording of the TRF request | FOUNDER | Not resolved; v0.2 keeps the v0.1 wording unchanged | Contacting FIDE; the policy itself is a founder decision |
| 10 | Repository name and visibility | FOUNDER | Not resolved (D-0001 stands) | Naming, visibility |
| 11 | Proposal length: accept about 5,400 words with tables, or trim to 4,500 | TECHNICAL | Resolved: body at most 4,500 words excluding tables; all mathematics moved to the technical annex and cross-referenced | Set by the ELO-2 brief |
| 12 | Spec open questions: authorise a verification session to capture FIDE-calculator fixtures (web reads, no code) | TECHNICAL | Resolved as a recommendation: no SPEC-L0 edit is needed for v0.2; the fixture-capture session is recommended as the next session | Read-only verification of a public page is not a founder category; scheduling stays with the operator |
| 13 | Repository description: confirm the step-0.5 text or revert it | FOUNDER | Not resolved | Repository settings |

## Consequences

- FOUNDER items carried to the ELO-2 close-out, numbered there: 5 (publication of θ̂ beyond the technical minimum), 8, 9, 10, 13.
- Every TECHNICAL resolution above is implemented in `docs/proposal/ELO-PROPOSAL_v0_2.md` and `docs/proposal/ELO-TECHNICAL-ANNEX_v0_2.md`.
- SPEC-L0 is not edited in this session; none of its open rules R-14, R-22, R-26, R-30, R-32 contradicts v0.2, because v0.2 leaves Layer 0 as the exact replica of today's rules.
