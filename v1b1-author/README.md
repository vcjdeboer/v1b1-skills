# v1b1-author

A Claude Code skill that scaffolds a new PyLabRobot device under the v1b1 capability-architecture patterns — the architecture set out by Rick Wierenga (PyLabRobot creator) in `creating-capabilities.md` and demonstrated across the merged device backends contributed by the PLR community. Sibling to `v1b1-capability` (the review skill). Generates two artifacts: a structurally-conformant Python scaffold and a markdown decision record. Calls `v1b1-capability` at hand-off as pre-emit lint stage 3.

**Version**: v0.9-RC (graduates to v1.0 after first real authoring session per spec SC-010).

## Install

Copy the skill bundle to your user-level skills directory. Restart Claude Code.

```bash
cp -r v1b1-author ~/.claude/skills/
ls ~/.claude/skills/v1b1-author/
# Expected: SKILL.md, README.md, audit.md, decision-record-template.md, templates/, tests/
```

**Prerequisite**: `~/.claude/skills/v1b1-capability/` must be installed (v1.0+). The authoring skill reads `reference.md` and `vocabulary-lockdown.md` from the sibling bundle by path — never duplicates them.

## Invoke

```
/v1b1-author <Vendor> <Device> [free-text intent]
```

Example:

```
/v1b1-author ACME WidgetShaker "single-capability shaker, serial port, no discovery"
```

The skill walks a 5-step decision flow as Q&A in chat, generates a scaffold under your repo's `pylabrobot/<vendor>/<device>/` (or single-file path for simple devices), writes a decision record under `docs/v1b1-authoring/`, and runs the review skill on the scaffold to confirm zero Findings before declaring done.

## Reading the Decision Record

The decision record lives at `<your-repo>/docs/v1b1-authoring/<vendor>-<device>-decisions.md`. Five step sections, each with: Decision, Principle, v1b1 precedent, Wrong default avoided, Files this decision shapes. Plus a cross-reference summary mapping each step to its wrong-default and the past-PR violation that documents it.

The "Wrong default avoided" line is load-bearing — keep it open while you're filling in protocol bodies; it's the LLM's reference for staying inside the scaffold's pattern shape.

## Hand-off

After the scaffold lands:

1. Open the scaffold files. Each Backend method body has a `# TODO: build wire payload here` marker — that's where vendor-specific protocol encoding goes.
2. Driver class is generic transport — do NOT add domain-named methods (the scaffold is constructed to make this hard).
3. Capability frontend methods are thin `@need_capability_ready` forwards — do NOT add multi-step orchestration here; workflow goes on the Backend.
4. After each Capability operation: `/v1b1-capability <scaffold-path>` → expect 0 Findings.

## Maintainer Path (audit cadence)

If you maintain the skill, the audit procedure (`audit.md`) shares a cadence with `v1b1-capability`. Before each release: vendored prose parity (shared), reference doc citation walk (shared), template parity (authoring skill only), smoke-scaffold corpus runs, vocabulary-leak grep, advance state. The Audit Trail entry in `~/.claude/skills/v1b1-capability/reference.md` covers BOTH skills together when both pass.

## See Also

- `~/.claude/skills/v1b1-capability/` — sibling review skill
