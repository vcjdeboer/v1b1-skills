---
description: Review draft PyLabRobot Driver / CapabilityBackend / Capability / Device code against Rick Wierenga's v1b1 patterns and the principles those patterns embody. Produces a structured violation report with named principle, v1b1 evidence, and suggested fix per finding. Warns; never blocks.
handoffs:
  - label: Plan a follow-up
    agent: speckit.plan
    prompt: Plan how to address the violations found
---

## User Input

```text
$ARGUMENTS
```

## Outline

The `speckit.create-capability` skill enforces Rick Wierenga's PyLabRobot v1b1 patterns on draft code. The skill is **review/lint mode only**: it reads code, produces a structured violation report per the contract, and never blocks the contributor's workflow.

Audience: any contributor using Claude Code in a PyLabRobot-related repo — upstream contributors building devices for `pylabrobot/main` (or `v1b1` until the merge lands), and downstream users on forks of the capability-architecture branch.

**Input**: One of four forms, parsed from `$ARGUMENTS`:

1. **Absolute path to a single Python file** (`*.py`) — partial input; cross-file checks skipped and listed.
2. **Absolute path to a device package directory** — folder containing the driver, backends, device class, and optional chatterbox/commands files. Complete input.
3. **GitHub PR URL** — `https://github.com/<org>/<repo>/pull/<N>`. The skill fetches the PR's HEAD SHA and the changed Python files via `gh` (`gh pr view <N> --repo <org>/<repo> --json headRefOid,files,baseRefName,title,author`, then `gh api repos/<org>/<repo>/contents/<path>?ref=<sha>` per Python file). Treats the union of changed Python files as the review scope. Complete iff both Driver class(es) and Capability class(es) appear in the union; partial otherwise (note which side is missing under Skipped Checks). Multi-package PRs (e.g., a new Capability package + a new Device package in one PR) are handled naturally by this mode.
4. **GitHub branch URL** — `https://github.com/<owner>/<repo>/tree/<branch>`. Use when reviewing work-in-progress on a fork branch that hasn't been opened as a PR yet. The skill fetches the branch HEAD SHA, then computes the diff against the canonical upstream PLR base branch (default: `PyLabRobot/pylabrobot:v1b1`; the skill detects this by walking the branch's parent / source repo metadata, and may ask the user when the base is ambiguous). Same per-file fetch and completeness rules as PR mode. The base used for the diff is recorded in the report header alongside the branch HEAD SHA so the run is reproducible.

**Output**: A markdown violation report per the `skill-output-contract.md` shape. Rendered inline in the Claude Code chat.

## Activation

The skill is triggered two ways:

### Way 1 — Explicit slash command

Contributor types `/speckit.create-capability <path>`. The skill runs the review on the given input.

### Way 2 — Auto-detect offer (hybrid trigger)

When Claude reads or edits Python code matching ANY of the following heuristics, surface a single one-line offer:

> Want me to run the v1b1 review on this draft?

**Detection heuristics** (any one is sufficient):

1. The file imports from `pylabrobot` or any subpackage (`from pylabrobot... import ...`, `import pylabrobot...`).
2. The file defines a class whose base classes include `Driver`, `Device`, `Capability`, `CapabilityBackend`, or any of the known mixin ABCs (`HasJoints`, `CanFreedrive`, `HasContinuousShaking`, `CanGrip`, etc. — see `vocabulary-lockdown.md` Emitted Terms / `Has...` / `Can...` row).
3. The file defines a class whose name matches Rick's naming conventions: ends in `Driver`, ends in `Backend` (and starts with a `<Vendor><Device>` prefix), or matches `<Vendor><Device>` device-class form.

**Debounce**: Once the contributor accepts, declines, or explicitly runs the review in the current editing session, do not surface the offer again for the same input or any input the contributor is actively editing in this session.

The offer never runs the review without consent. It is an offer, not a side-effect.

## Execution Steps

### 1. Validate input

- Parse `$ARGUMENTS`. Determine which input form applies:
  - **GitHub PR URL** if `$ARGUMENTS` matches `https://github.com/<org>/<repo>/pull/<N>`.
  - **GitHub branch URL** if `$ARGUMENTS` matches `https://github.com/<owner>/<repo>/tree/<branch>`.
  - **Single file** if `$ARGUMENTS` is an absolute path to a `*.py` file that exists. Partial input — cross-file checks skipped.
  - **Device package** if `$ARGUMENTS` is an absolute path to an existing directory. Complete input.
- For **PR URL**:
  1. `gh pr view <N> --repo <org>/<repo> --json headRefOid,files,baseRefName,title,author` — capture HEAD SHA, file list, base branch.
  2. Filter the file list to Python files, excluding tests (`*_tests.py`, `tests/`) and docs (`docs/`).
  3. For each remaining Python file: `gh api repos/<org>/<repo>/contents/<path>?ref=<sha> -q .content | base64 -d > /tmp/<sanitized-name>.py`.
  4. Treat the union of fetched files as the review scope. Determine completeness: if both at least one `Driver` subclass and at least one `Capability` subclass appear in the union, mark `complete`; otherwise `partial` and note which side is missing under Skipped Checks.
  5. Record the HEAD SHA in the Header block alongside the PR URL so the run is reproducible.
- For **branch URL**:
  1. `gh api repos/<owner>/<repo>/branches/<branch>` — capture HEAD SHA, parent SHA, and last commit message.
  2. Resolve the comparison base. Default for `pylabrobot` repos is `PyLabRobot/pylabrobot:v1b1` (the active capability-architecture branch). For other PLR-related repos or for non-default bases, prompt the user to confirm or override. Record the resolved base.
  3. `gh api repos/<owner>/<repo>/compare/<base-org>:<base-branch>...<owner>:<branch>` — enumerate changed files (a `.files[]` list with `path`, `status`, `additions`, `deletions`). Filter to Python files, excluding tests and docs.
  4. For each Python file in the diff: `gh api repos/<owner>/<repo>/contents/<path>?ref=<sha> -q .content | base64 -d > /tmp/<sanitized-name>.py` (same fetch as PR mode).
  5. Same completeness rule as PR mode: complete iff both Driver and Capability classes appear in the union; partial otherwise.
  6. Record the branch HEAD SHA AND the resolved comparison base in the Header block so the diff scope is reproducible.
- If invalid (file not found, not a `.py` file, not a directory, PR or branch URL but `gh` fails or returns no Python files), ERROR with: "Invalid input. Provide an absolute path to a Python file, a device package directory, a GitHub PR URL (`/pull/<N>`), or a GitHub branch URL (`/tree/<branch>`)."

### 2. Detect PLR context

- Walk the input file(s) and check for any of:
  - `pylabrobot` imports
  - Class definitions inheriting from `Driver`, `Device`, `Capability`, `CapabilityBackend`, or known mixin ABCs
  - Class names matching Rick's naming conventions
- If no PLR context found, exit gracefully with: "This input does not look like PyLabRobot code (no `pylabrobot` imports, no `Driver`/`Capability`/`CapabilityBackend` classes, no Rick-naming-convention classes). The v1b1 review skill is intended for PLR contributor code. Skipping review."

### 3. Load patterns

- Read the vendored prose at `~/.claude/skills/v1b1-capability/creating-capabilities.md` for prose-source patterns.
- Read `~/.claude/skills/v1b1-capability/reference.md` for the full pattern set (prose + code-archaeology gaps).
- Build the in-memory pattern table from the Pattern entries.

### 4. Walk the input and apply pattern signatures

For each file in the input:
- Parse the file (Python AST).
- For each Pattern entry in the loaded set, check whether the file matches the pattern's `anti_pattern_signature`.
- Record matches as candidate Violation Findings.

For device-package input, also run cross-file checks:
- P-01 — Driver-Capability method-name collision: requires both Driver and Capability classes in scope.
- Multi-capability shared-driver wiring (P-13): requires Device class plus its referenced backends.
- Lifecycle hook ordering (P-07): requires `_capabilities` registration on the Device.

For single-file input, mark cross-file checks as **skipped** (with a list of which checks were skipped, per FR-001).

### 5. Assemble findings per the output contract

For each candidate Violation Finding, construct a Finding block per `skill-output-contract.md`:

- **Pattern**: primary `pattern_id` and pattern name (from reference.md). When the same code site triggers multiple patterns (e.g., P-01 and P-20 on a domain-named driver method), list the dominant pattern first and append `(with P-NN — <name>)` for up to two secondaries.
- **Principle**: `principle_id` and principle name (from reference.md Principles section). Always singular — pick the dominant principle for the primary pattern.
- **Severity**: `hard`, `soft`, or `informational`. Apply the rubric in `skill-output-contract.md` "Severity rubric": `hard` for explicit prose anti-patterns or unambiguous signature matches with no documented v1b1 exception; `soft` for divergence from the dominant v1b1 shape with a defensible variant or design-shaping concerns; `informational` for documented variants Rick himself uses. Default to `soft` when the principle and v1b1 evidence don't clearly map to a severity.
- **Where**: contributor's file path, line range, class.method
- **What's wrong**: one paragraph describing the violation in Rick's vocabulary
- **v1b1 precedent**: one Evidence Citation pointing to the v1b1 example of the correct pattern (file path, class name, brief explanation)
- **Fix**: concrete edit guidance

Order findings deterministically: by Severity (hard → soft → informational), then by source line number, ties broken by primary `pattern_id`.

### 6. List skipped cross-file checks (when input is partial)

If the input was a single file, append a `## Skipped Checks (partial input)` section listing each cross-file check that was not run, naming the pattern_id and the missing context (e.g., "Driver-Capability method-name collision check (P-01) — requires the matching Capability class").

### 7. Emit the report

Render the full violation report per the contract:

- Header block (Invoked, Input, Context — and HEAD SHA when in PR mode)
- Compliance summary (count of findings + per-severity breakdown `hard, soft, informational`)
- Skipped Checks (if partial input)
- Findings (zero or more, in deterministic order: Severity → source line → primary `pattern_id`)
- References block (vendored prose, reference.md, vocabulary-lockdown.md)
- Optional closing summary, constrained per the contract's "Closing summary" section

**Warn, never block.** The skill never refuses to write code or aborts the contributor's workflow. The output is annotated information, not a gate.

### 7a. Pre-emit structural lint

Before emitting, grep the rendered report for the required headings and field labels per `skill-output-contract.md` "Validation (pre-emit checklist)":

- `# v1b1 Capability Review` exactly once at top
- `**Invoked**:`, `**Input**:`, `**Context**:` each exactly once in the header
- `**Result**:` exactly once
- `## References` exactly once
- For each `## Finding ` heading: `**Pattern**:`, `**Principle**:`, `**Severity**:`, `**Where**:`, `**What's wrong**:`, `**v1b1 precedent**:`, `**Fix**:` each exactly once
- Each `**Severity**:` value is one of `hard`, `soft`, `informational`
- Findings are ordered by Severity (hard → soft → informational) then source line then primary `pattern_id`
- The `**Result**:` severity counts equal the per-Finding `Severity:` tally
- Every `**Pattern**:` cites a `pattern_id` that exists in `reference.md`; every `**Principle**:` cites a `principle_id` from the Principles section
- If `## Skipped Checks` is present, every bullet cites a `pattern_id`

If any check fails: do not emit. Re-render with the missing fields filled in, then re-lint. If a structural lint failure persists across two re-renders, emit a self-error naming the missing field rather than a malformed report.

### 8. Vocabulary-lockdown self-check

Before emitting, scan the rendered report for any term in `vocabulary-lockdown.md` Excluded Terms set. If any leaked term is detected:

- **Do not emit** the report.
- Emit a self-error instead, naming the leaked term and the section where it appeared.
- The maintainer's audit catches this on the smoke-test corpus, not in production output. A leaked report in production is a defect.

The check applies only to text the skill itself authored. Verbatim contributor input quoted in the report (e.g., a class name the contributor wrote that happens to use a term) is not synthesized output and is preserved unchanged.

## Key References

- **Vendored prose**: `~/.claude/skills/v1b1-capability/creating-capabilities.md` — Rick's authoritative prose, refreshed during the audit cadence.
- **Pattern reference**: `~/.claude/skills/v1b1-capability/reference.md` — verified-against-v1b1 pattern → evidence map.
- **Vocabulary lockdown**: `~/.claude/skills/v1b1-capability/vocabulary-lockdown.md` — allow-list of terms the skill is permitted to emit.
- **Audit procedure**: `~/.claude/skills/v1b1-capability/audit.md` — runnable step list for the maintainer.
- **Output contract**: `contracts/skill-output-contract.md` — violation-report structure (the format this skill produces).

## Notes

- The skill is downstream of Rick's prose and code. It does not propose changes to either. Patterns are added to `reference.md` only with v1b1 precedent (file path, class name, commit hash).
- The skill uses Rick's terminology only. See `vocabulary-lockdown.md` for the emit / exclude lists.
- Single-file input produces partial coverage with explicit skip notes. Device-package input produces full coverage.
- Pattern set is currently a skeleton — full pattern population happens in tasks T006–T020 of the implementation plan. Until those tasks complete, the skill enforces only the patterns that have been authored.
