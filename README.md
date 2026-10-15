# Chess-ELO-Rating

STATUS: DRAFT — nothing here is final or published

Zugzwang's proposal to modernise the FIDE Elo rating system. The project delivers two things: an exact, test-vector-verified, open-source reference implementation of FIDE's current rating regulations (standard, rapid and blitz), and a documented, explainable correction layer on top of it. A dynamic statistical model runs behind the scenes and is re-estimated monthly; the published rating stays a familiar, forward-only, Elo-style number on today's scale, moved only through named, published channels. The targets, in order, are the problems the chess world has the strongest evidence for: deflation and junior lag, federation isolation, top-level farming and inactivity, and a miscalibrated expectancy curve. Everything is deterministic, hand-checkable and open-source; it is a statistical model with machine-estimated parameters, not a black box.

## Repository layout

| Path | Contents |
|---|---|
| `docs/research/` | Evidence base: the research report (v1.0) and dated verification sweeps of primary sources |
| `docs/proposal/` | The proposal to FIDE, its technical annex and a plain-language brief (`ELO-PROPOSAL_vX_Y.md`, `ELO-TECHNICAL-ANNEX_vX_Y.md`, `ELO-BRIEF_vX_Y.md`) |
| `docs/specs/` | Engineering specifications, starting with the Layer-0 FIDE reference engine (`SPEC-L0_*`) |
| `docs/decisions/` | Decision records (`D-NNNN_*.md`) |
| `docs/evidence/` | Evidence reports, each the committed output of a script under `analysis/` |
| `docs/review/` | Red-team reviews of each proposal version |
| `analysis/` | Deterministic scripts that produce every number in the documents, with their committed outputs |
| `params/` | Fitted parameter files (`params/table_fit_2026-10.yaml`), PROVISIONAL-FITTED, each written by a script under `analysis/` |
| `src/layer0/` | The Layer-0 engine: FIDE's rating regulations exactly (SPEC-L0) |
| `tests/` | The SPEC-L0 acceptance tests and the fixtures recorded from FIDE's pages (`tests/fixtures/`) |
| `tools/` | The automated check run on every pull request, the data tools, and the event comparison tool with its event files (`tools/README.md`) |
| `CLAUDE.md` | Working rules for the humans and agents editing this repository |

The Layer-0 specification in `docs/specs/` is ratified (`docs/decisions/D-0006_spec-l0-ratified.md`). Its acceptance tests were written first, under `tests/`; the engine is the package `src/layer0/` (Python 3.12, standard library only), validated against FIDE in `docs/evidence/E0_l0-validation.md`.

## Spelling

It is "Elo": the system is named after Arpad Elo, a surname, not an acronym. The repository name is a historical exception recorded in `docs/decisions/D-0001_repo-licence-visibility-language.md`.

## Data

FIDE's own material is analysed from a local cache and never redistributed (`docs/DECISIONS.md`, items 6 and 43). No FIDE list file is published: what is committed of FIDE's data is aggregates and differences. Where this project's material shows a named player's FIDE rating, it is FIDE's published rating, credited to FIDE. FIDE IDs are committed only in the test fixtures that quote FIDE's published calculations (`tests/fixtures/`) and the evidence report printed from them, for the players of the U.S. Championships, in their event files (`tools/events/`) and the reports printed from them, and for the named players of today's top 100 and the greats; no sampled player's name or FIDE ID is committed. FIDE's written permission is to be requested for the analyses already made of its lists and calculations.

## Licences

- Code (everything outside `docs/`): Apache-2.0, see `LICENSE`.
- Documentation (everything under `docs/`): CC BY 4.0, see `docs/LICENSE-docs.md`.
- **Except the figures derived from OlimpBase's transcription of FIDE's lists** (ruling R83, a founder decision, `docs/decisions/D-0018_rulings-on-elo-9-questions.md`). OlimpBase's terms are free use, citing the source, non-commercial use only (`docs/research/DATA-PROBE_greats.md` §3), so every table or figure derived from its transcription carries this label, and neither licence above covers it: "Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences." The files that hold such figures:
  - documents: `docs/evidence/E20_greats.md` (its brief, §1 to §3, the selection's figures in §4 and §5, and §7), `docs/proposal/ELO-PROPOSAL_v1_0.md` (Appendix I), `analysis/OUTPUT_E20_appendix.md` (Appendix I as generated), `docs/specs/SPEC-GREATS_v1_0.md` (§2's table), `docs/research/DATA-PROBE_greats.md` (§3's account of OlimpBase's lists and §4's table), `docs/review/REDTEAM_v1_0.md` (the figures of its ELO-9 and ELO-10 addenda, labelled in the ELO-10 addendum; the reviewers' reports are reproduced verbatim), `docs/decisions/D-0018_rulings-on-elo-9-questions.md` (ruling R82's counts of the selection) and `docs/evidence/E21_sourcing.md` (§2's set of the greats replayed);
  - committed aggregates, each with the label in its field `terms`: `analysis/aggregates/GREATS_players.json`, `analysis/aggregates/E20_greats_lists.json` and `analysis/aggregates/PROBE_greats.json`.

  The greats' replay of 2008–2019 (E20 §4 and §5, Appendix I, Appendix F.3, E21 §2, `analysis/aggregates/E20_greats_replay.json` and `analysis/aggregates/E20_greats_replay_by_list.json`) is computed on FIDE's pages and files; its set of players is SPEC-GREATS §2's selection, which rests on OlimpBase's transcription for the players ranked 1st to 3rd only on the lists to April 2000. The selection's figures there (its counts and its groups) carry the label; the replay's values, computed on FIDE's material, do not.
