# speckit.create-capability — PLR v1b1 Capability Skill

A Claude Code skill that reviews draft PyLabRobot capability/backend/driver code against the v1b1 capability-architecture patterns — the architecture set out by Rick Wierenga (PyLabRobot creator) in `creating-capabilities.md` and demonstrated across the merged device backends contributed by the PLR community. Produces a structured violation report. Warns; never blocks.

**Audience**: Anyone using Claude Code in a PyLabRobot-related repository — upstream contributors building devices for `pylabrobot/main` (or `v1b1` until the merge lands), and downstream users on forks of the capability-architecture branch.

## Install

Copy this directory to `~/.claude/skills/`:

```bash
cp -r v1b1-capability ~/.claude/skills/
```

Restart Claude Code (or open a new session). The skill becomes available.

## Invoke

Two ways:

**Auto-detect offer** — when Claude reads or edits Python code that imports `pylabrobot`, defines a class inheriting from `Driver` / `Device` / `Capability` / `CapabilityBackend`, or whose name matches Rick's naming convention, Claude surfaces a one-line offer:

> Want me to run the v1b1 review on this draft?

Reply "yes" to run; "no" to debounce for the session.

**Explicit slash command** — type at any time:

```
/speckit.create-capability /path/to/your/draft.py
```

```
/speckit.create-capability /path/to/your/device-package/
```

Accepts a single Python file or a device package directory.

## Reading the Report

Every report has the same structure:

```
# v1b1 Capability Review

**Invoked**: <timestamp>
**Input**: <paths>
**Context**: complete | partial — see skipped checks

**Result**: N findings — see details below.

## Skipped Checks (if partial)
[Cross-file checks not performed]

## Finding 1: <pattern name>
**Pattern**: P-NN
**Principle**: P-N
**Where**: <file:line>
**What's wrong**: ...
**v1b1 precedent**: ...
**Fix**: ...

## References
- Vendored prose, reference.md, vocabulary-lockdown.md
```

The full output contract lives in this skill's spec at `contracts/skill-output-contract.md`.

## Maintainer Path (Audit Cadence)

If you maintain this skill, before each release follow `audit.md`:

1. Verify vendored prose parity (sha256 against authoritative source)
2. Walk every citation in `reference.md`; verify file/class/method exists at recorded commit
3. Run smoke-test corpus (`tests/smoke/`); zero violations expected
4. Run anti-pattern corpus (`tests/anti-patterns/`); 100% catch with named principles
5. Vocabulary-leak grep across all output; zero hits expected
6. Advance `verified_against` hash; bump version; append Audit Trail entry in `reference.md`

Audit cadence is on-demand only. No scheduled CI in MVP.

## Bundle Contents

- `SKILL.md` — Claude Code skill definition
- `creating-capabilities.md` — vendored copy of Rick's prose
- `reference.md` — verified-against-v1b1 pattern → evidence map
- `vocabulary-lockdown.md` — allow-list of terms the skill is permitted to emit
- `audit.md` — runnable step list for the maintainer
- `tests/smoke/` — smoke-test fixtures from recently-merged v1b1 PRs
- `tests/anti-patterns/` — synthetic violation fixtures
- `README.md` — this file

## Contributing

This is a downstream-of-Rick artifact. The skill enforces Rick's patterns; it does not propose changes to them. To suggest a new pattern:

1. Find the v1b1 device that demonstrates it.
2. Author a Pattern Entry in `reference.md` per the contract (file path, class name, method name, commit hash).
3. Pair with an anti-pattern fixture in `tests/anti-patterns/` if the pattern has a clean signature.
4. Run the audit. If it passes, the pattern enters the next skill release.

To suggest a new term:

1. Confirm the term appears in Rick's prose or v1b1 code first (vocabulary-lockdown's term-addition policy).
2. Add to `vocabulary-lockdown.md`'s Emitted Terms table with precedent.
3. Re-run the audit.

The vocabulary lockdown is allow-list only: any term not in the Emitted Terms table fails the pre-emit self-check.
