---
name: v1b1-protocol
description: Extract a structured command catalog from a vendor device's communication protocol (DLL, server API, or bytestream sniff) so the catalog drops cleanly into a v1b1-author scaffold's command-class slot. Third sibling to v1b1-capability (review) and v1b1-author (scaffold) — the trio covers the full PLR device-authoring lifecycle. Reads reference.md and vocabulary-lockdown.md from v1b1-capability by path; never duplicates.
handoffs:
  - "/v1b1-capability <scaffold-path> — verify the Backend bodies pasted from this catalog don't introduce new findings"
---

# v1b1-protocol Skill

Walks a contributor through extracting a **command catalog** from a vendor device's protocol. Output: a single markdown file at `<contributor-repo>/docs/v1b1-protocol/<vendor>-<device>-commands.md` with one entry per command, keyed to a v1b1 P-21 transport form.

The skill is the **third sibling** in the v1b1 trio:

- `v1b1-capability` — reviews draft Driver/Capability/Backend/Device code against the v1b1 patterns set out by Rick Wierenga and demonstrated across PLR community device backends. Lint mode.
- `v1b1-author` — scaffolds a new device through a 5-step decision flow. Authoring mode.
- **`v1b1-protocol` (this skill)** — extracts the command catalog the scaffolded Backend bodies need. Catalog mode.

## Outline

Audience: any contributor using Claude Code in a PLR fork (upstream `pylabrobot/main` or `pylabrobot/v1b1`) who has a vendor protocol surface and wants the command catalog for it. Three input modes (`dll | server | bytestream`); each produces the same catalog shape.

The skill **does not**:

- Emit Python source code into `pylabrobot/` (FR-016) — output is markdown only.
- Recommend changes to the vendor's protocol design (FR-017) — it catalogs what's there.
- Do live capture / packet sniffing (FR-018) — input is files only.
- Auto-detect inputs (FR-019) — explicit slash command only at v1.0.

## Activation

v1.0 ships **explicit slash command only**. Contributor types:

```
/v1b1-protocol <Vendor> <Device> <mode> <input-path-or-url> [free-text intent]
```

Mode is one of `dll | server | bytestream`. The free-text intent is required for bytestream mode (passed to the Q&A loop) and optional otherwise.

## Execution Steps

### 1. Validate input + check sibling skills

- Parse `<Vendor>` and `<Device>` as PascalCase Python identifiers per FR-002. ERROR if not: "Vendor and Device must be PascalCase Python identifiers (e.g., `Opentrons` `Flex`)."
- Validate mode ∈ {`dll`, `server`, `bytestream`}. ERROR otherwise.
- Verify the sibling skills are installed:

  ```bash
  test -f ~/.claude/skills/v1b1-capability/reference.md \
    && test -f ~/.claude/skills/v1b1-capability/vocabulary-lockdown.md \
    && test -f ~/.claude/skills/v1b1-author/SKILL.md \
    && echo OK || echo MISSING
  ```

  If `MISSING`: ERROR "v1b1-protocol requires sibling skills v1b1-capability AND v1b1-author. Install features 023 and 024 first."

- Load the **shared data** (path-reference contract per FR-003 / FR-004):

  ```bash
  # Read at runtime — DO NOT cache; DO NOT copy:
  cat ~/.claude/skills/v1b1-capability/reference.md         # P-21 transport-form catalog
  cat ~/.claude/skills/v1b1-capability/vocabulary-lockdown.md  # Excluded Terms list
  ```

  Parse the P-21 transport-form list from `reference.md`'s `## Pattern Index` table — the row(s) for P-21 list the recognized form names (`inline-string-command`, `command-class`, `module-command-kwargs`, `sdk-wrapper`, `rpc`). The list is the source of truth for stage-3 round-trip lint; when sibling adds a new form, the skill picks it up on next run.

### 2. Detect existing catalog + present re-extract / abort choice

- Compute the target catalog path: `<contributor-repo>/docs/v1b1-protocol/<vendor>-<device>-commands.md` (lowercase; snake-cased). For a second-or-later mode on the same device, the path takes a mode suffix: `<vendor>-<device>-<mode>-commands.md` (per Assumptions in spec).
- If the file exists, surface it and prompt:

  ```
  Existing catalog detected at <path> (generated <generated_at>, <entry_count> entries).

  Diff against new extraction:
  <diff summary — added entries, removed entries, modified entries>

  Choose:
  (a) re-extract (overwrite)
  (b) abort

  Default: abort
  ```

  Default to (b) on no answer. Do NOT overwrite without explicit confirmation (FR-006).

### 3. Mode dispatch — extract Catalog Entries

Read parsing rules from `~/.claude/skills/v1b1-protocol/parsing.md` for the chosen mode.

#### Mode `server` (US1 — MVP path)

Accepts: OpenAPI 3.x specs (JSON or YAML), Swagger 2.x specs, curl-examples directory, Postman collections, gRPC `.proto` files, AsyncAPI specs, OR an unrecognized format (prompt for dialect per FR-013).

Per `parsing.md` "OpenAPI 3.x and Swagger 2.x specs":

- Walk `paths.<path>.<method>` for each operation.
- `name`: PascalCase from `operationId` (or fallback `<METHOD>_<path>`).
- `verb_or_opcode`: `<METHOD> <path>`.
- `request_shape`: flatten `requestBody.content.<media>.schema` to (field, type, notes); nested objects → dotted-path field names.
- `response_shape`: flatten `responses.200.content.<media>.schema` (or `201`/`default`).
- `side_effects`: derived from `summary` or `description` (one-sentence trim).
- Skip endpoints with `deprecated: true`.
- Default `transport_form = command-class` (HTTP → Nimbus-shape).
- Default `confidence = confirmed`.

For curl-examples / Postman / proto / AsyncAPI: per the relevant parsing.md section. For unrecognized formats: prompt the dialect template from parsing.md "Unrecognized format dialect prompt", then proceed with the contributor-supplied dialect.

#### Mode `bytestream` (US2)

Accepts: Wireshark pcap (`.pcap`, `.pcapng`), Total Phase Beagle USB analyzer text/CSV exports, raw serial-sniff text logs, OR an unrecognized capture format (prompt for dialect per FR-013).

Free-text intent is **required** for this mode. The intent text names the operations the contributor sent during capture (e.g., `"start_shake at 500 RPM, stop_shake, set_temperature 37, lock_plate, unlock_plate, query_status"`). The Q&A loop uses the intent to assign Catalog Entry names and to bound coverage.

The branch walks the **7-step Q&A loop** in fixed order (per `contracts/bytestream-qa-contract.md`). Later steps may revisit earlier ones when new evidence contradicts a prior hypothesis.

##### Step (a) — Parse

Decode the capture into the normalized stream `[(timestamp, direction, bytes), ...]`:

- For built-in formats: read parsing rules from `~/.claude/skills/v1b1-protocol/parsing.md` (sections "Wireshark pcap", "Total Phase Beagle ...", "Raw serial-sniff text logs").
- For an unrecognized format: read the prompt from `parsing.md` "Unrecognized format dialect prompt" section and surface its 4 questions verbatim (separator, byte representation, timestamp column, direction column). Record the dialect in run state; do not persist.
- Multi-device captures (e.g., USB hub): cluster by device address; if more than one device address is present, prompt the contributor to scope to a single device per run.

##### Step (b) — Cluster

Group packets into candidate shapes. A shape is a tuple `(direction, length-class, prefix-byte-pattern)`; two packets share a shape iff all three match. Output: an enumerated list of candidate request shapes and response shapes.

##### Step (c) — Propose framing hypotheses

For each shape, emit ALL framing hypotheses consistent with the captured packets across these classes:

| Hypothesis class | Examples |
|---|---|
| Start byte | `0xAA`, `0x02` (STX), `<` (ASCII), or "no start byte" |
| Length field | "byte 1, big-endian uint8", "bytes 2–3, little-endian uint16", "no explicit length" |
| Checksum scheme | "CRC-16 over bytes 0..N-3", "XOR over bytes 1..N-2", "no checksum" |
| End byte | `0xFE`, `0x03` (ETX), `\r\n` (ASCII), or "no end byte" |

A shape is `confirmed`-eligible when exactly one hypothesis fits each class.

##### Step (d) — Ask for confirmation (framing)

When ≥ 2 hypotheses fit within a single class for a single shape, surface the ambiguity:

```
Shape <id>: I see <N> framing candidates that all fit the captured packets.

A: <hypothesis A>
B: <hypothesis B>
...

To narrow:
- Send the same command twice with <suggested differentiator> — capture both. Drop the new capture into <input>.
- OR confirm the right one: A | B | ...

Your call: __
```

The "suggested differentiator" depends on the ambiguity:

| Ambiguity | Differentiator |
|---|---|
| Length field position | Send the command with two different parameter sizes |
| Endianness | Send a command with a parameter > 255 |
| Checksum vs no-checksum | Modify a single byte mid-packet; the device should reject |
| Start byte vs no start byte | Compare across multiple distinct command initiations |

Reuse the same prompt shape for any later ambiguity surfaced by step (f).

##### Step (e) — Pair

Match request packets to response packets by direction + timing window. Default window: ≤ 50ms. Override per dialect (some serial protocols use ≤ 500ms; allow the dialect prompt to set this).

Output: `(request_shape_id, response_shape_id, pair_count)` triples. Unpaired shapes are flagged as either fire-and-forget commands (request only) or unsolicited reports (response only).

##### Step (f) — Propose field-encoding hypotheses

Per request shape (and per response shape with a paired body), emit hypotheses for each non-framing field:

| Hypothesis class | Examples |
|---|---|
| Endianness | big \| little |
| Bitfield decomposition | "byte 4 high nibble = mode; low nibble = channel" |
| Numeric encoding | uint16 \| int16 \| BCD \| float32 |
| String encoding | ASCII \| UTF-8 \| null-terminated \| length-prefixed |
| Magic constants | "byte 5 always 0x00 in observed captures" |

When ≥ 2 hypotheses fit within a class for a single field, surface using the same prompt shape as step (d).

##### Step (g) — Narrow

Apply the contributor's intent text + accumulated confirmation answers to converge:

- Match each command-shape cluster to a verb in the intent text (e.g., "`start_shake @ 500 RPM`" → the shape whose payload contains `0x01F4` somewhere is `StartShake`, not `StopShake`).
- Assign each Catalog Entry's `name` in PascalCase derived from the intent text.
- Set `confidence` per shape: `confirmed` (one framing + one field-encoding hypothesis remains); `hypothesized` (ambiguity remains but the loop is not yet terminated, the favored hypothesis is emitted, alternates noted in Open Questions); `unresolved` (cannot disambiguate even with help OR safety bound hit; emit best guess + a prominent Open Question).

##### Termination

The loop terminates on the FIRST condition that holds (per FR-014):

1. **Contributor confirms**: any obvious closure phrase (`done`, `stop`, `ship it`, `looks good`). Loop emits whatever has been narrowed.
2. **Full coverage**: every distinct packet shape has been clustered AND has at most one consistent framing hypothesis AND at most one consistent field-encoding hypothesis. Loop emits all entries with `confirmed` confidence.
3. **Safety bound**: 10 consecutive Q&A turns with no contributor input that shifts a hypothesis. Loop emits with `unresolved` confidence on still-ambiguous entries; Open Questions are appended for each.

Confidence assignment on emit:

- `confirmed`: only one framing hypothesis AND only one field-encoding hypothesis fit; OR contributor explicitly confirms.
- `hypothesized`: ≥ 2 framings or ≥ 2 field encodings fit, but enough evidence exists to favor one. The favored one is emitted; alternates are noted in Open Questions.
- `unresolved`: cannot disambiguate even with help OR safety bound hit. Emit best guess + a prominent Open Question.

Each emitted bytestream entry carries an `Evidence` block (FR-015 / VR-4): capture timestamp range, packet indices, and which Q&A turn(s) disambiguated each hypothesis.

##### Replay path (for smoke tests)

When invoked with a `confirmation_answers` runtime input (a list of strings, one per expected Q&A turn — typical for smoke replay against `tests/smoke/S-02_*.spec.md`), use those answers in order at each Q&A turn instead of prompting interactively. The list MUST have at least as many entries as turns the loop walks; if exhausted before termination, fall back to interactive prompting for remaining turns.

Defaults on emit: `transport_form = command-class` (the typical bytestream idiom — opcode + payload framed by start/length/checksum/end). Override per shape only when the intent text or evidence indicates a different P-21 form (e.g., a Hamilton-shape `module-command-kwargs` clearly inferrable from the capture).

#### Mode `dll` (US3)

Accepts: Python `.pyi` stubs, introspectable Python wrapper modules (`.py` files exporting a vendor SDK class), C/C++ headers (`.h`, `.hpp`), OR an unrecognized type-bearing surface (prompt for dialect per FR-013, reframed for server-spec formats per `parsing.md` "Unrecognized format dialect prompt" trailing note).

Per `parsing.md` "Python `.pyi` stubs and Python wrapper modules" and "C/C++ headers":

- AST-walk the file. For `.pyi` and Python wrapper modules: walk top-level `class` declarations; collect `def` methods. For C/C++ headers: parse function declarations.
- Skip dunder methods (`__init__`, `__repr__`, etc.), private methods (`_method`), `@deprecated`-decorated methods, macros, typedefs, structs, and forward declarations.
- One Catalog Entry per surviving public callable, in alphabetical order by entry `name`.
- `name`: PascalCase from method/function name (`set_servo_angle` → `SetServoAngle`).
- `verb_or_opcode`: fully-qualified method name from the source surface (`XArmAPI.set_servo_angle` for the Python case; bare function name for C/C++).
- `request_shape`: one row per parameter, type from annotation (Python) or mapped from the C/C++ type table in `parsing.md` (C/C++); `notes` from any inline comment adjacent to the parameter.
- `response_shape`: one row for the return type. Tuple / composite return values expand by element.
- `side_effects`: derived from the method's docstring (Python) or preceding `/** ... */` doxygen comment (C/C++) — one-sentence trim of the first line. If neither is present, render the placeholder `[Provide side-effects note]` so the contributor can fill it in post-emit.
- Default `transport_form = sdk-wrapper` (the canonical P-21 form when the catalog backs an SDK call rather than a wire payload).
- Default `confidence = confirmed` (signatures and types are mechanically extracted; ambiguity is rare and surfaces as a `[Provide …]` placeholder rather than a hypothesis-set Q&A).

The dll branch does NOT walk a Q&A loop — extraction is mechanical. If the input file fails to parse (unbalanced braces, syntax error, etc.), surface the parse error and halt before emitting; the contributor fixes the input and re-runs.

### 4. Render catalog

- Read `~/.claude/skills/v1b1-protocol/catalog-template.md`.
- Substitute frontmatter placeholders from the run state (`vendor`, `device`, `mode`, `transport_form`, `generated_at`, `generated_by`, `input_source`, `entry_count`, plus `intent_text` and `confirmation_answers` for bytestream mode).
- Render one `## <name>` block per Catalog Entry, in deterministic order: alphabetical by `name`, ties broken by `verb_or_opcode` (FR-009 / VR-6).
- Render the `## Open Questions` section (header mandatory; body 0..N items). Empty list renders as `_No open questions — catalog is fully resolved._`.
- Render the References block.
- Write the rendered catalog to the target path computed in step 2 (creating `docs/v1b1-protocol/` if missing per FR-005). Per FR-006, refuse overwrite unless step 2's confirmation was (a).

### 5. Pre-emit lint chain

Three stages, fixed order, halt on failure (per `contracts/pre-emit-lint-contract.md`):

#### Stage 1 — Structural lint

Verify the rendered catalog has:

- YAML frontmatter parseable; all required fields present.
- Title `# Commands: <Vendor> <Device>` exactly once.
- `# Commands` heading exactly once.
- One `## ` subsection per Catalog Entry; each entry has all 7 required fields (`Verb / Opcode`, `Transport form`, `Confidence`, `Request shape`, `Response shape`, `Side effects`, plus `Evidence` for bytestream mode entries).
- Subsections alphabetically ordered.
- `entry_count` frontmatter equals actual `## ` subsection count.
- `## Open Questions` heading exactly once.
- Every Open Question `affects` list references entry names that exist (VR-3).

**On failure**: re-render once with the missing field(s); if still failing, emit self-error naming the field. Halt.

#### Stage 2 — Vocabulary self-check

Grep the rendered catalog for any term in the shared `vocabulary-lockdown.md` Excluded Terms set (`Locality`, `Internality`, `Contract` capitalized, `EYES/I4S`, `three-layer`, `Resource Trust`, `Signal` capitalized, `Device Card`).

Verbatim contributor input quoted in `intent_text` is preserved unchanged.

**On failure**: do not emit; surface the leaked term and section. Halt.

#### Stage 3 — Sibling round-trip on `transport_form`

Verify the catalog's frontmatter `transport_form` AND every entry's `transport_form` appears in the P-21 form list parsed in step 1 from shared `reference.md`.

**On failure**: do not emit; surface the offending value and the source-of-truth list. Halt with self-error per the contract's "Self-error format" section.

### 6. Hand-off

Emit a clear hand-off block per FR-022:

```
Catalog: <catalog-path>
Mode: <mode>
Transport form: <transport_form>
Entry count: <N>

Drops into a v1b1-author-emitted scaffold's command-class slot at:
  <target_scaffold_slot string for the chosen transport form>

Open Questions: <count>
<list each pending Q1, Q2, ... with its affects list>

Next:
1. Open the catalog. For each entry, paste the `Request shape` table into the matching Backend method body in your scaffold; build the `send_command(...)` call from the verb/opcode + request fields.
2. After each Capability operation: /v1b1-capability <scaffold-path> to confirm the protocol implementation didn't introduce new findings.
3. When all done: /v1b1-capability one final time on the full path; expect 0 findings.
```

For each `transport_form`, the target scaffold slot string is:

| transport_form | Target slot |
|---|---|
| `inline-string-command` | `<Vendor><Device>Driver.send_command(cmd: str)` body — backends format strings here |
| `command-class` | `<Vendor><Device><Capability>Backend.<method>` bodies — build a Command instance and call `self.driver.send_command(command)` |
| `module-command-kwargs` | `<Vendor><Device><Capability>Backend.<method>` bodies — call `self.driver.send_command(module=..., command=..., **fw_params)` |
| `sdk-wrapper` | `<Vendor><Device><Capability>Backend.<method>` bodies — call `self.driver._call_sdk(self._arm.<sdk-method>, ..., op="<op-name>")` |
| `rpc` | `<Vendor><Device><Capability>Backend.<method>` bodies — call `self.driver._request(verb, path, json=...)` |

## Key References

- **Shared pattern catalog** (READ at runtime; never copied): `~/.claude/skills/v1b1-capability/reference.md` — Principles P1–P6, Patterns P-01..P-27, P-21 transport-form list (the round-trip target for stage-3 lint).
- **Shared vocabulary lockdown** (READ at runtime): `~/.claude/skills/v1b1-capability/vocabulary-lockdown.md` — Emit / Excluded term lists.
- **Shared vendored prose**: `~/.claude/skills/v1b1-capability/creating-capabilities.md` — Rick's authoritative prose; consulted for phrasing in skill output.
- **Sibling scaffold skill**: `~/.claude/skills/v1b1-author/SKILL.md` — the catalog this skill emits drops into a scaffold the sibling emits; the contract is the `transport_form` keying.
- **Local catalog template**: `~/.claude/skills/v1b1-protocol/catalog-template.md` — the substitution template for catalog rendering.
- **Local parsing rules**: `~/.claude/skills/v1b1-protocol/parsing.md` — per-format extraction rules + unrecognized-format dialect prompt.
- **Local audit procedure**: `~/.claude/skills/v1b1-protocol/audit.md` — runnable step list; SHARED Audit Trail with siblings.
- **Spec contracts**: `contracts/` (in this skill bundle) — catalog-shape, pre-emit-lint, bytestream-qa.

## Notes

- The skill is downstream of Rick's prose and code. It does not propose new patterns; new patterns enter via the SHARED v1b1 audit cadence.
- The skill uses Rick's terminology only (vocabulary lockdown enforced via stage 2 of the pre-emit lint).
- Same input → byte-identical catalog (FR-009 → SC-006). Bytestream determinism is path-conditional on identical contributor confirmation answers.
- v0.9-RC ships all three modes end-to-end: server (US1), bytestream (US2), dll (US3). Smoke fixtures S-01 / S-02 / S-03 cover each.
- v1.0 graduates separately when SC-009 holds — the first three real-world catalog runs across the three modes produce content with < 10% post-emit correction.
