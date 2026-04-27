# Audit Procedure — speckit.create-capability

**Purpose**: Re-verify every citation in `reference.md`, the vendored prose parity, the smoke-test corpus, the anti-pattern corpus, and the vocabulary-leak self-check before each skill release. Stale citations or any failure block release per FR-025 of the spec.

**When to run**: On-demand, before each skill release. No scheduled automation in MVP (clarification Q4 → A: on-demand only).

**Owner**: Skill maintainer (whoever publishes the next release of this bundle).

**Prerequisites**:

- Local read access to Rick's v1b1 branch on the upstream PyLabRobot repository (target_branch field in `reference.md` frontmatter; switches to `main` post-merge).
- Local copy of the authoritative source for `creating-capabilities.md` (path varies — record the path you used in the audit-trail entry).
- The full bundled skill package at `~/.claude/skills/v1b1-capability/`.

---

## Step 1 — Verify vendored prose parity

**Action**: Compute the SHA-256 of `~/.claude/skills/v1b1-capability/creating-capabilities.md` and compare against the authoritative source.

```bash
sha256sum ~/.claude/skills/v1b1-capability/creating-capabilities.md
sha256sum "<path-to-authoritative-creating-capabilities.md>"
```

**Pass**: hashes match.

**Fail action**:
1. Diff the two files (`diff -u` or `git diff --no-index`).
2. Refresh the bundled copy from the authoritative source.
3. Re-validate every Pattern entry whose `source` field includes `prose` against the new prose; update affected entries if the prose has changed in ways that affect the pattern.
4. Update the SHA-256 record in the bundled copy's header comment.
5. Append a "vendored prose refresh" line to the next Audit Trail entry.

**Rationale**: Per FR-025a — the audit also re-verifies the bundled prose, not just the v1b1 citations.

---

## Step 2 — Walk reference.md citations

**Action**: For every Pattern entry in `reference.md`, verify each Evidence Citation:

- File at `<file_path>` exists on `<target_branch>` at `<commit_hash>`.
- Class `<class_name>` is defined in the file at the recorded position.
- Method `<method_name>` (where present) exists on the class at the recorded position.

**Pass**: All citations resolve.

**Fail action**: For each failing citation, report PASS / FAIL with reason per FR-024:

- "file not found" → check renames / moves; update `file_path`.
- "class renamed to X" → update `class_name` if Rick has renamed it.
- "method removed" → either find the renamed method, or retire the pattern if Rick has removed it.

Stop the audit; fix all citations before continuing. Resume from Step 1.

**Rationale**: FR-023, FR-024.

---

## Step 3 — Run smoke-test corpus

**Action**: For each fixture in `~/.claude/skills/v1b1-capability/tests/smoke/`, invoke the skill on the fixture and verify zero Violation Findings.

```bash
for fixture in ~/.claude/skills/v1b1-capability/tests/smoke/*.py; do
  echo "=== $fixture ==="
  # invoke skill on $fixture and capture output
done
```

**Pass**: every fixture produces zero findings.

**Fail action**: A finding on a smoke-test fixture means one of:

1. A citation in `reference.md` is incorrect or over-broad.
2. A pattern signature is too aggressive.
3. The merged code Rick approved actually has the violation (rare; raise upstream — do not silently update the skill to ignore it).

Investigate the specific finding; correct the pattern or citation; re-run.

**Rationale**: SC-001.

---

## Step 4 — Run anti-pattern corpus

**Action**: For each fixture in `~/.claude/skills/v1b1-capability/tests/anti-patterns/`, invoke the skill and verify exactly one Violation Finding matches the planted `pattern_id` with the named principle.

```bash
for fixture in ~/.claude/skills/v1b1-capability/tests/anti-patterns/*.py; do
  echo "=== $fixture ==="
  # invoke skill; expected output: exactly one finding with the planted pattern_id
done
```

**Pass**: every fixture produces a finding with the correct `pattern_id` and the correct `principle_id`.

**Fail action**:
- Missed catch → pattern signature is too narrow; broaden it without overshooting (re-run Step 3 to confirm no smoke-test regression).
- Wrong pattern matched → signature collision; tighten the matcher.
- Missing principle citation → fix the Pattern entry in `reference.md` to point at the correct principle.

**Rationale**: SC-002.

---

## Step 5 — Vocabulary-leak grep

**Action**: Across all skill output examples produced by Steps 3 and 4, grep for every Excluded Term in `vocabulary-lockdown.md`.

```bash
EXCLUDED_TERMS="Locality|Internality|EYES/I4S|three-layer|Resource Trust|Device Card"
# Plus capitalized Contract and Signal as standalone tokens (context-sensitive)

# Run skill on each fixture, capture output, grep for excluded terms
```

**Pass**: zero hits.

**Fail action**: A leaked term means one of:

1. A Pattern entry in `reference.md` has language that uses an Excluded Term.
2. The skill's authoring step for the report introduced a leak.
3. The vocabulary lockdown is missing a term that should be excluded.

Identify the source; remove the term from the skill-authored output; if the term is genuinely needed, raise it as a vocabulary-policy question (the term may need to enter the Emitted Terms set with a precedent — see vocabulary-lockdown's Term Addition Policy).

Verbatim contributor input that uses an Excluded Term is preserved unchanged; the grep applies only to skill-authored output. Where doubt exists, a manual review pass distinguishes contributor-quoted text from skill-authored text.

**Rationale**: SC-003, FR-028.

---

## Step 6 — Advance state and append Audit Trail

**Action** (only on all-pass):

1. Advance `verified_against` in `reference.md` frontmatter to the latest commit hash on `target_branch`.
2. Update `last_audited` to today's ISO date.
3. Bump the skill version in `SKILL.md` (semver: bump patch for citation-only refresh, minor for new patterns or terms, major for breaking output changes).
4. Append a new entry to `reference.md` Audit Trail per the reference-document-contract.md format:

```markdown
### Audit YYYY-MM-DD (<descriptor>)

- Target branch: v1b1 | main
- Verified against: <commit hash>
- Audit procedure version: 1.0
- Patterns verified: N / N
- Stale citations: 0
- Vendored prose drift: none | refreshed
- Smoke corpus: PASS (0 / 0 violations on N fixtures)
- Anti-pattern corpus: PASS (M / M catches)
- Vocabulary leak: PASS (0 leaks)
- Released: skill version X.Y.Z
```

**Action** (on any failure):

Do not advance `verified_against`. Do not bump version. Repair the failures and re-run from Step 1.

**Rationale**: FR-025 — pre-publication release requires zero failures; audit trail is append-only and authoritative.

---

## Procedure version

This audit procedure is version **1.0**. Increment when steps change. Old audit-trail entries reference the procedure version they were produced under.
