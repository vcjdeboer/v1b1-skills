---
title: "v1b1-protocol Skill — Audit Procedure"
last_updated: 2026-04-25
audit_version: 1.0
shared_with: v1b1-capability, v1b1-author (Audit Trail entries cover all three skills together)
---

# v1b1-protocol Skill — Audit Procedure

Runnable step list for the skill maintainer. Audit cadence is on-demand only — same cadence as the two siblings. Before each release, walk every step. On any FAIL, repair before release.

## Owner

Whoever maintains the v1b1 skill trio.

## Prerequisites

- Local PLR mirror checked out at the `verified_against` commit hash recorded in `~/.claude/skills/v1b1-capability/reference.md` frontmatter.
- `~/.claude/skills/v1b1-capability/` and `~/.claude/skills/v1b1-author/` installed and operational.
- `gh` CLI (inherited from `v1b1-capability`).

## Step 1 — Vendored prose parity (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 1. The protocol skill does NOT separately vendor `creating-capabilities.md`; it reads the sibling's vendored copy.

**PASS criterion**: The `v1b1-capability` audit step 1 passed.

## Step 2 — Walk reference.md citations (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 2.

**PASS criterion**: Shared.

## Step 3 — Catalog-template + parsing.md parity

Verify:

1. Every placeholder declared in `~/.claude/skills/v1b1-protocol/catalog-template.md` matches the documented catalog shape (frontmatter + per-entry block).
2. Every parsing-rule section in `~/.claude/skills/v1b1-protocol/parsing.md` covers a built-in format (pcap, Beagle CSV, raw serial text, OpenAPI/Swagger, .pyi/Python wrapper, C/C++ headers).
3. The "Unrecognized format dialect prompt" section in `parsing.md` matches the 4-question prompt template.

**PASS criterion**: All three sub-checks pass.
**FAIL action**: Name the diverged file; do not advance to step 6.

## Step 4 — Smoke-catalog corpus

For each `tests/smoke/S-NN_*.spec.md`:

1. Invoke `/v1b1-protocol <Vendor> <Device> <mode> <input>` in a clean working directory. For S-02 (bytestream), use the `confirmation_answers` field from the spec for replay.
2. Compare the produced catalog byte-for-byte against `tests/fixtures/S-NN-expected/<vendor>-<device>-commands.md`.
3. Read the produced catalog; verify all `expected_*` fields in the spec frontmatter match the catalog's frontmatter and section content.
4. Confirm the pre-emit lint chain returned zero issues at all three stages.

**PASS criterion**: All smoke specs produce identical catalogs (deterministic) AND pre-emit lint clean on each. SC-001, SC-006 satisfied.
**FAIL action**: Diff the produced output against the expected fixture; identify which step in the skill's mode-dispatch produced the divergence.

## Step 5 — Vocabulary-leak grep (SHARED)

Pointer to `~/.claude/skills/v1b1-capability/audit.md` step 5.

Grep all skill-authored output produced by step 4 (rendered catalogs) for any term in `~/.claude/skills/v1b1-capability/vocabulary-lockdown.md` Excluded Terms.

**PASS criterion**: Zero hits (SC-004).
**FAIL action**: Name the leaked term and the catalog it appeared in; do not advance to step 6.

## Step 6 — Advance state and append SHARED Audit Trail entry

On all-pass:

1. The shared `verified_against` commit hash advances as part of the SHARED audit run — single advancement covers all three skills.
2. Bump `~/.claude/skills/v1b1-capability/reference.md` frontmatter `last_audited` AND `last_shared_audit` dates.
3. Bump skill version on the protocol-skill side; sibling versions bumped per their own audits or together when all three pass.
4. Append a single SHARED Audit Trail entry to the Audit Trail section of `~/.claude/skills/v1b1-capability/reference.md` covering all three skills. Use the existing audit-trail format. Mark the entry with `audit_kind: shared`.

On any FAIL: do not advance any state. Record blockers in the audit working notes; remediate; re-run the affected step.
