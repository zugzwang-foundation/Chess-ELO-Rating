# Chess-ELO-Rating

STATUS: DRAFT — nothing here is final or published

Zugzwang's proposal to modernise the FIDE Elo rating system. The project delivers two things: an exact, test-vector-verified, open-source reference implementation of FIDE's current rating regulations (standard, rapid and blitz), and a documented, explainable correction layer on top of it. A dynamic statistical model runs behind the scenes and is re-estimated monthly; the published rating stays a familiar, forward-only, Elo-style number on today's scale, moved only through named, published channels. The targets, in order, are the problems the chess world has the strongest evidence for: deflation and junior lag, federation isolation, top-level farming and inactivity, and a miscalibrated expectancy curve. Everything is deterministic, hand-checkable and open-source; it is a statistical model with machine-estimated parameters, not a black box.

## Repository layout

| Path | Contents |
|---|---|
| `docs/research/` | Evidence base: the research report (v1.0) and dated verification sweeps of primary sources |
| `docs/proposal/` | The proposal to FIDE, versioned drafts (`ELO-PROPOSAL_vX_Y.md`) |
| `docs/specs/` | Engineering specifications, starting with the Layer-0 FIDE reference engine (`SPEC-L0_*`) |
| `docs/decisions/` | Decision records (`D-NNNN_*.md`) |
| `CLAUDE.md` | Working rules for the humans and agents editing this repository |

There is no code yet. By project rule, no rating-engine code is written until the Layer-0 specification in `docs/specs/` is ratified.

## Spelling

It is "Elo": the system is named after Arpad Elo, a surname, not an acronym. The repository name is a historical exception recorded in `docs/decisions/D-0001_repo-licence-visibility-language.md`.

## Licences

- Code (everything outside `docs/`): Apache-2.0, see `LICENSE`.
- Documentation (everything under `docs/`): CC BY 4.0, see `docs/LICENSE-docs.md`.
