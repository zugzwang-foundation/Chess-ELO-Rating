# CLAUDE.md — working rules for this repository

## Roles
- **Web Claude** — architect and reviewer. Writes the session briefs and owns the
  design decisions in them; those decisions are fixed unless the operator reopens them.
- **Claude Code** — executor. Produces exactly what the brief asks for, measures
  rather than asserts, and leaves a session log and close-out for every session.
- **Hrishikesh** (operator, commits as "Zugzwang/world") — runs the sessions and is
  the sole merge authority. Nothing is published, posted or announced without the operator.

## Hard rules
1. **No engine code before a ratified spec.** Rating code is written only once the
   Layer-0 specification in `docs/specs/` carries status RATIFIED. Until then this
   repository contains documents only.
2. **Spelling is "Elo"**, a surname (Arpad Elo), never "ELO" or "elo". The repository
   name is the one tolerated exception (see D-0001).
3. **Every empirical claim cites `docs/research/`** — the research report
   (`ELO-RESEARCH_v1_0.md`) or a dated verification sweep. A FIDE rule is either
   transcribed from the handbook (with URL and timestamp) or marked NOT VERIFIED.
   Never fill a rule or a number from memory.
4. **Commit identity**, set locally in this clone: `user.name "Zugzwang/world"`,
   `user.email "zugzwangworld@proton.me"`. No Co-authored-by trailers.
5. **Licences**: code Apache-2.0 (`LICENSE`); everything under `docs/` CC BY 4.0
   (`docs/LICENSE-docs.md`).
6. **Status lines.** Every document starts with a status line
   (DRAFT / REVIEW / RATIFIED). Drafts are not for publication.
7. **Parameters are PROVISIONAL** until estimated from data, and are labelled so
   wherever they appear.

## Layout
- `docs/research/` evidence base · `docs/proposal/` proposal drafts ·
  `docs/specs/` specifications · `docs/decisions/` decision records.

## Conventions
- Decision records: `docs/decisions/D-NNNN_slug.md`; never edited after the fact,
  superseded by a new record.
- Versioned documents: `NAME_vX_Y.md`; a new version is a new file.
- Commit messages use conventional prefixes: `chore:`, `docs:`, `feat:`, `fix:`, `test:`.
- Session artefacts (logs, close-outs) live in the operator's `~/Downloads`, not here.
