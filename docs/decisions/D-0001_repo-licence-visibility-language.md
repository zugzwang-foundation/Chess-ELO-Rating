# D-0001 — Repository name, visibility, licences and Layer-0 language

Date: 2026-10-09 · Session: ELO-1 · Status: DECIDED (by the operator)

## Context

The repository `zugzwang-foundation/Chess-ELO-Rating` was created empty by the operator in the GitHub web UI. Session ELO-1 (brief step 0.2) asked the operator, verbatim:

> Before I touch the repo settings: rename it to Chess-Elo-Rating (Elo is a surname, not an acronym) and make it private until proposal v1.0 is ratified? Recommended: both. Reply: both / rename only / private only / neither.

## Decision

Operator's answer (2026-10-09 14:25 UTC): **neither**.

| Item | Decided | What was actually done |
|---|---|---|
| Repository name | Stays `Chess-ELO-Rating` | Step 0.3 (rename) skipped; no rename command run |
| Visibility | Stays **public** | Step 0.4 (private) skipped; no visibility command run |
| Description | — (step 0.5, not gated by the question) | Set to: "Zugzwang's proposal to modernise the FIDE Elo rating system: an exact reference implementation of FIDE's rules plus a dynamic, explainable correction layer" |
| Code licence | **Apache-2.0** | `LICENSE`, copyright "The Zugzwang Authors" |
| Documentation licence | **CC BY 4.0** for everything under `docs/` | `docs/LICENSE-docs.md` |
| Layer-0 implementation language | **Python** (target 3.12; tooling TODO in the Layer-0 spec) | Recorded here and in `docs/specs/` |

## Consequences

- Because the repository is public, every document carries a status line ("DRAFT — not for publication") until it is ratified, and nothing is announced or linked from anywhere.
- The spelling rule ("Elo", a surname) applies to all content. The repository name is the one tolerated exception; a rename can be taken up in a later decision record.
- Session artefacts (session log, close-out) stay in the operator's `~/Downloads`, outside the repository.
