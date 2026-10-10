# CLAUDE.md — working rules for this repository

## Roles
- **Web Claude** — architect and reviewer. Writes the session briefs and owns the
  design decisions in them; those decisions are fixed unless the operator reopens them.
  Reviews each session's close-out after its pull requests are merged.
- **Claude Code** — executor. Produces exactly what the brief asks for, measures
  rather than asserts, merges its own pull requests after a green check, and leaves
  a session log and close-out for every session.
- **Hrishikesh** (operator, commits as "Zugzwang/world") — runs the sessions. Nothing
  is published, posted or announced without the operator.

## Hard rules
1. **No engine code before a ratified spec.** Rating code is written only once the
   Layer-0 specification in `docs/specs/` carries status RATIFIED. Until then this
   repository contains documents only.
2. **Spelling is "Elo"**, a surname (Arpad Elo), never "ELO" or "elo". The repository
   name is the one tolerated exception (see D-0001).
3. **Every empirical claim cites the evidence base: `docs/research/` and
   `docs/evidence/`** — the research report (`ELO-RESEARCH_v1_0.md`), a dated
   verification sweep, or an evidence report ([E n], each the output of a committed
   script) (D-0008, R13). A FIDE rule is either transcribed from the handbook (with
   URL and timestamp) or marked NOT VERIFIED. Never fill a rule or a number from memory.
4. **Commit identity**, set locally in this clone: `user.name "Zugzwang/world"`,
   `user.email "zugzwangworld@proton.me"`. No Co-authored-by trailers.
5. **Licences**: code Apache-2.0 (`LICENSE`); everything under `docs/` CC BY 4.0
   (`docs/LICENSE-docs.md`).
6. **Status lines.** Every document starts with a status line
   (DRAFT / REVIEW / RATIFIED). Drafts are not for publication.
7. **Parameters are PROVISIONAL** until estimated from data, and are labelled so
   wherever they appear.

## Merge rule (D-0004)
Every change reaches `main` through a pull request; never push directly to `main`.
The automated check (`.github/workflows/check.yml`) runs on every pull request; the
executor merges (squash) only when it is green, and on a red check fixes and pushes
again. The architect reviews the close-outs afterwards.

## Layout
- `docs/research/` research report and verification sweeps · `docs/evidence/` evidence
  reports ([E n]) · `docs/proposal/` proposal drafts · `docs/specs/` specifications ·
  `docs/decisions/` decision records · `docs/review/` red-team reviews.

## Conventions
- Decision records: `docs/decisions/D-NNNN_slug.md`; never edited after the fact,
  superseded by a new record.
- Versioned documents: `NAME_vX_Y.md`; versions are bumped with git mv; history lives in git.
- Commit messages use conventional prefixes: `chore:`, `docs:`, `feat:`, `fix:`, `test:`.
- Session artefacts (logs, close-outs) live in the operator's `~/Downloads`, not here.

## Active session — ELO-6
After any compaction, and at every phase boundary, re-read
~/Downloads/zz_ELO-6_relay.md and the latest ~/Downloads/zz_ELO-6_session_*.md;
resume from the first phase not marked DONE. Remove this section at close-out.
