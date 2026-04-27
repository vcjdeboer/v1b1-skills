# v1b1-protocol

A Claude Code skill that extracts a structured **command catalog** from a vendor device's communication protocol — DLL, server API, or bytestream sniff — so the catalog drops cleanly into a `v1b1-author`-emitted scaffold's command-class slot. Third sibling to `v1b1-capability` (review) and `v1b1-author` (scaffold) — together the trio covers the full v1b1 device-authoring lifecycle for PLR community contributors.

**Version**: v0.9-RC (graduates to v1.0 after first field run across all three modes per spec SC-009).

## Install

```bash
cp -r v1b1-protocol ~/.claude/skills/
```

Restart Claude Code.

**Prerequisites**: `~/.claude/skills/v1b1-capability/` (v1.0+) and `~/.claude/skills/v1b1-author/` (v0.9-RC+) must be installed. The protocol skill reads `reference.md` and `vocabulary-lockdown.md` from the review skill's bundle by path — never duplicates them. The P-21 transport-form list is parsed at runtime from the shared `reference.md`.

## Invoke

```
/v1b1-protocol <Vendor> <Device> <mode> <input-path-or-url> [free-text intent]
```

Mode is one of `dll | server | bytestream`. Examples:

```
/v1b1-protocol Opentrons Flex server https://docs.opentrons.com/openapi/v3.0
/v1b1-protocol QInstruments BioShake bytestream ~/captures/bioshake.pcap "I sent: start_shake @500 RPM, stop_shake, ..."
/v1b1-protocol UFactory XArm6 dll ~/venv/lib/python3.11/site-packages/xarm/wrapper/__init__.pyi
```

The skill writes a single markdown catalog to `<your-repo>/docs/v1b1-protocol/<vendor>-<device>-commands.md` and emits a hand-off block naming the scaffold slot the catalog drops into.

## Reading the Catalog

The catalog has YAML frontmatter (mode, transport_form, entry_count, input_source) plus a `# Commands` section with one subsection per command, an `## Open Questions` section, and a References block.

Per-entry fields: `name` (PascalCase Python class), `verb_or_opcode`, `transport_form`, `confidence` (`confirmed | hypothesized | unresolved`), `request_shape`, `response_shape`, `side_effects`, plus `evidence` for bytestream-mode entries.

The catalog is deterministic: same input + same shared `reference.md` state → byte-identical output. Bytestream determinism is path-conditional on identical contributor confirmation answers.

## Hand-off

After the catalog lands:

1. Open the catalog. Each entry maps to one Backend method body in the corresponding `v1b1-author`-emitted scaffold.
2. Paste the request shape + response shape into the Backend method that matches each entry's `name`.
3. Re-run `/v1b1-capability <scaffold-path>` to confirm the protocol implementation didn't introduce new findings.

## Maintainer Path (audit cadence)

If you maintain the skill, the audit procedure (`audit.md`) shares a cadence with `v1b1-capability` and `v1b1-author`. Before each release: vendored prose parity (shared), reference doc citation walk (shared), catalog-template + parsing.md parity (protocol-only), smoke-catalog corpus runs, vocabulary-leak grep, advance state. The Audit Trail entry in `~/.claude/skills/v1b1-capability/reference.md` covers ALL THREE skills together when each passes.

## See Also

- `~/.claude/skills/v1b1-capability/` — sibling review skill
- `~/.claude/skills/v1b1-author/` — sibling scaffold skill
