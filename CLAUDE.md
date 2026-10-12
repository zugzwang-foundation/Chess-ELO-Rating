# CLAUDE.md — working rules for this repository

## Roles
- **Web Claude** — architect and reviewer. Writes the session briefs and owns the
  design decisions in them; those decisions are fixed unless the operator reopens them.
  Reviews each session's close-out after its pull requests are merged.
- **Claude Code** — executor. Produces exactly what the brief asks for, measures
  rather than asserts, merges its own pull requests after a green check, and leaves
  a short close-out for every session.
- **Hrishikesh** (operator, commits as "Zugzwang/world") — runs the sessions. Nothing
  is published, posted or announced without the operator.

## Hard rules
1. **Rating code follows its specification in `docs/specs/`.**
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

## How we work
- Code tests and the automatic checks stay: every number regenerates from its
  committed script, references resolve, word limits hold.
- Championship lock: the files of the freeze-3d manifest stay unchanged until the
  2026 U.S. Championships comparison has run once, and no result of either event is
  read before the last round. After that run the freeze checks retire; the tags stay
  as history.
- No new freezes or pre-registrations. An analysis says plainly what was decided
  after seeing its data.
- Decisions: one dated line each in `docs/DECISIONS.md`; D-0001 to D-0018 stay as
  history.
- Mistakes are fixed in place, with a dated line saying what changed.
- One review of the proposal and brief before submission.
- Versions are bumped with git mv, except that a version a frozen file reads stays
  beside the new one (SPEC-L0 v1.4).
- At every close-out, build ~/Downloads/zz_ELO_PK_full_<HEAD7>/ with a PK-MANIFEST.md,
  as ELO-10b defined it (the operator's project knowledge).

## Layout
- `docs/research/` research report and verification sweeps · `docs/evidence/` evidence
  reports ([E n]) · `docs/proposal/` proposal drafts · `docs/specs/` specifications ·
  `docs/decisions/` decision records · `docs/review/` red-team reviews.

## Conventions
- Versioned documents: `NAME_vX_Y.md`; versions are bumped with git mv; history lives in git.
- Commit messages use conventional prefixes: `chore:`, `docs:`, `feat:`, `fix:`, `test:`.
- Session artefacts (logs, close-outs) live in the operator's `~/Downloads`, not here.
- Update STATUS.md at every close-out.
- After an interruption the operator sends "Continue ELO-N from the relay and the latest
  session log."; resume from the first phase not marked DONE.
