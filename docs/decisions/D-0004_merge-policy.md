# D-0004 — Merge policy: the executor merges after a green check

Date: 2026-10-09 · Session: ELO-3 · Status: DECIDED (ELO-3 brief, relayed by the operator)

## Context

Until ELO-2 the operator was the sole merge authority (CLAUDE.md, Roles), so the executor's work waited in a draft pull request (#1, proposal v0.2). The ELO-3 brief states that this is not a core project: the executor does all the work and merges its own pull requests once the automated check passes; the operator neither reviews nor merges; the architect reviews the close-outs afterwards. The same brief replaces the versioning rule "a new version is a new file" with "versions are bumped with git mv; history lives in git".

## Decision

1. Every change reaches `main` through a pull request from a session branch (`elo-3/p<N>-<slug>` in ELO-3); nothing is pushed directly to `main`.
2. The automated check `.github/workflows/check.yml` runs on every pull request to `main`: (a) every analysis script reproduces its committed output exactly; (b) pytest, once tests exist; (c) every relative link and `[T n]` / `[V n]` / `[R n]` reference in `docs/` resolves; (d) the proposal body is at most 4,500 words by ELO-2's strict count. Python standard library and pytest only; the commands are in `tools/README.md`.
3. The executor merges (`gh pr merge --squash --delete-branch`) only when the check is green. On a red check it fixes and pushes again; it never merges on red.
4. The architect reviews each session's close-out after the merges; findings return as the next brief, not as a hold on a merge.
5. Versioned documents are bumped with `git mv`: a version bump is a rename and the earlier versions live in git history.
6. Unchanged: nothing is published, posted or announced without the operator; no change to the repository's name or visibility (D-0001); commit identity, licences and the other rules of CLAUDE.md.

## Consequences

- PR #1 was verified locally (`python3 analysis/v02_calculations.py | diff - analysis/OUTPUT_v0_2.md` empty under Python 3.9.6 and 3.12.13), marked ready and merged by the executor on 2026-10-09 with a merge commit, so that the ten ELO-2 commits cited by the ELO-2 close-out stay on `main`; every later pull request is squash-merged.
- The check is the only gate, so what it does not test is not guaranteed. In particular it cannot rerun scripts that read raw data under `data/` (gitignored, never committed): those are registered with `needs_data` in `analysis/outputs.json`, rerun locally before merging, and only their aggregate outputs are committed.
- "ELO-2's strict count" is defined in `tools/checks/check_wordcount.py`: body from the `## 1` heading to the first `## Appendix` heading, without fenced code, table rows, headings and horizontal rules, counting whitespace-separated tokens. It reproduces the 4,751 words that the ELO-2 close-out records for the proposal at commit 7a94622.
- To make the first run green, the v0.2 proposal body was trimmed from 4,751 to 4,492 words (redundant wording only; no rule or parameter changed), and five stale or incomplete paths were corrected in the proposal, SPEC-L0 and `analysis/README.md`.
