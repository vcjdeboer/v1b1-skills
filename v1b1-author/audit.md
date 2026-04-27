---
title: "v1b1-author Skill — Audit Procedure"
last_updated: 2026-04-25
audit_version: 1.0
shared_with: v1b1-capability (Audit Trail entries cover both skills together)
---

# v1b1-author Skill — Audit Procedure

Runnable step list for the skill maintainer. Audit cadence is on-demand only — same cadence as `v1b1-capability`. Before each release, walk every step. On any FAIL, repair before release; failures block release.

## Owner

Whoever maintains the v1b1 skill bundle.

## Prerequisites

- Local PLR mirror at `references/repos/pylabrobot/` checked out at the `verified_against` commit hash recorded in `~/.claude/skills/v1b1-capability/reference.md` frontmatter.
- `~/.claude/skills/v1b1-capability/` installed and operational (the review skill is invoked in step 4).
- `gh` CLI (inherited from `v1b1-capability`).

## Step 1 — Vendored prose parity (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 1. The authoring skill does NOT separately vendor `creating-capabilities.md`; it reads the sibling's vendored copy.

**PASS criterion**: The `v1b1-capability` audit step 1 passed (no separate work).

## Step 2 — Walk reference.md citations (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 2.

**PASS criterion**: Shared.

## Step 3 — Template parity

For each of the 8 templates in `~/.claude/skills/v1b1-author/templates/`:

1. Read the template's header-block (declared placeholders + invariants + reference pointers).
2. Verify every placeholder declared in the header is actually used in the template body, AND every placeholder used in the body is declared.
3. Verify each declared invariant is statically true given valid placeholder substitution. (Manual review against `contracts/scaffold-template-contract.md` per-template invariant set.)
4. Verify the reference pointers (e.g., "Reference: pylabrobot/qinstruments/bioshake.py") still resolve in the local PLR mirror at the recorded commit hash.

**PASS criterion**: All 8 templates pass all 4 sub-checks.
**FAIL action**: Name the diverged template; do not advance to step 6.

## Step 4 — Smoke-scaffold corpus

For each `tests/smoke/S-NN_*.spec.md`:

1. Invoke `/v1b1-author <Vendor> <Device> <intent_text from spec>` in a clean working directory.
2. Compare the produced scaffold byte-for-byte against `tests/fixtures/S-NN-expected/`.
3. Read the produced decision record; verify all `expected_*` fields in the spec frontmatter match the record's frontmatter and section content.
4. Confirm the pre-emit lint stage 3 result is `**Result**: 0 findings — compliant with v1b1 patterns.` (the review skill's clean-pass signal).

**PASS criterion**: All smoke specs produce identical scaffolds (templates are deterministic) AND pre-emit lint stage 3 returns 0 Findings on each.
**FAIL action**: Diff the produced output against the expected fixture; identify which template substitution diverged; do not advance to step 6.

## Step 5 — Vocabulary-leak grep (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 5.

Grep all skill-authored output produced by step 4 (rendered decision records + scaffold docstrings/comments) for any term in `~/.claude/skills/v1b1-capability/vocabulary-lockdown.md` Excluded Terms.

**PASS criterion**: Zero hits.
**FAIL action**: Name the leaked term and the artifact it appeared in; do not advance to step 6.

## Step 6 — Advance state and append SHARED Audit Trail entry

On all-pass:

1. The shared `verified_against` commit hash (in `~/.claude/skills/v1b1-capability/reference.md` frontmatter) is advanced as part of the SHARED audit run — single advancement covers both skills.
2. Bump `~/.claude/skills/v1b1-capability/reference.md` frontmatter `last_audited` date.
3. Bump skill version on the authoring skill side (recorded in `project_v1b1_skill.md` memory entry); the review skill's version is bumped if its audit also passes.
4. Append a single SHARED Audit Trail entry to the Audit Trail section of `~/.claude/skills/v1b1-capability/reference.md` covering BOTH skills together. Use the existing audit-trail format (frontmatter fields, evidence citations, smoke-corpus result, anti-pattern-corpus result, template-parity result, vocab-leak result, version tags). Mark the entry with `audit_kind: shared` to distinguish from review-skill-only entries.

On any FAIL: do not advance any state. Record blockers in the audit working notes; remediate; re-run the affected step.
