---
description: Walk an LLM through a 5-step decision flow to scaffold a new PyLabRobot device under Rick Wierenga's v1b1 patterns. Generates a structurally-conformant Python scaffold + a markdown decision record. Calls the v1b1-capability review skill at hand-off as pre-emit lint stage 3. Sibling skill to v1b1-capability — reuses its reference.md and vocabulary-lockdown.md by path; never duplicates.
handoffs:
  - label: Verify the scaffold (or, after protocol implementation, re-verify)
    agent: v1b1-capability
    prompt: Run the v1b1 review on the scaffolded path.
---

## User Input

```text
$ARGUMENTS
```

## Outline

The `v1b1-author` skill scaffolds a new PyLabRobot device under the v1b1 patterns set out by Rick Wierenga and demonstrated across the merged device backends contributed by the PLR community. It is **authoring mode** — the inverse of the `v1b1-capability` review skill. Where the review skill detects anti-patterns in finished code, the authoring skill makes pattern-conformant decisions BEFORE code exists, using the same pattern catalog as the source of truth.

Audience: any contributor using Claude Code in a PyLabRobot fork (upstream `pylabrobot/main` or `pylabrobot/v1b1`) who wants to add a new device. The skill is invoked via Claude — the LLM running the skill conducts the 5-step decision Q&A; the contributor answers in natural language.

**Input**: `/v1b1-author <Vendor> <Device> [free-text intent]` parsed from `$ARGUMENTS`.

**Outputs**: Two artifacts written into the contributor's working directory:

1. A **scaffold** at `<repo>/pylabrobot/<vendor_lower>/<device_snake>.py` (simple form) or `<repo>/pylabrobot/<vendor_lower>/<device_snake>/` (complex form). By construction the scaffold passes the `v1b1-capability` review skill with 0 Findings.
2. A **decision record** at `<repo>/docs/v1b1-authoring/<vendor>-<device>-decisions.md`. Five step sections each with a Decision, Principle, v1b1 precedent, Wrong-default-avoided callout, and Files-this-shapes list.

**Warn, never block.** Like the sibling review skill: the authoring skill never overwrites the contributor's working files without confirmation; on pre-emit lint failure it surfaces a self-error, never half-emits.

## Activation

v1.0 ships **explicit slash command only** (auto-detect deferred to v1.1). Contributor types `/v1b1-author <Vendor> <Device> [intent]`. The skill runs the 5-step decision flow.

## Execution Steps

### 1. Validate input + check sibling skill

- Parse `$ARGUMENTS` into `<Vendor>`, `<Device>`, and the remaining `<intent_text>` (free text).
- Validate `<Vendor>` and `<Device>` are valid Python identifiers, PascalCase preferred. If not, ERROR with: "Vendor and Device must be PascalCase Python identifiers (e.g., `Labcyte` `Echo`)."
- Verify the sibling skill is installed:

```bash
test -f ~/.claude/skills/v1b1-capability/reference.md \
  && test -f ~/.claude/skills/v1b1-capability/vocabulary-lockdown.md \
  && echo OK || echo MISSING
```

If `MISSING`, ERROR with: "v1b1-author requires the sibling skill v1b1-capability to be installed at ~/.claude/skills/v1b1-capability/. Install it first."

### 2. Detect existing scaffold + offer re-scaffold/augment/abort

- Compute the scaffold target path from `<Vendor>` + `<Device>` (lowercased + snake_cased per FR-005).
- Check if any of the following exist in the contributor's working directory:
  - `pylabrobot/<vendor_lower>/<device_snake>.py` (simple-form file)
  - `pylabrobot/<vendor_lower>/<device_snake>/` (complex-form directory)
  - `docs/v1b1-authoring/<vendor>-<device>-decisions.md` (decision record)
- If any exist, surface the existing decision record (if present), then prompt the contributor:

```
Existing scaffold detected at <path>. Choose:
(a) Re-scaffold (overwrite; existing protocol implementations LOST)
(b) Augment a specific Capability (preserve existing; add a new Backend)
(c) Abort
```

Default to (c) on no answer or anything other than `a` / `b`. Do NOT overwrite without explicit confirmation (FR-009).

### 3. Walk the 5-step decision flow (Q&A)

Read the shared pattern catalog and vocabulary lockdown:

```bash
# Read these at runtime — DO NOT cache; DO NOT copy:
cat ~/.claude/skills/v1b1-capability/reference.md         # Principles P1–P6, Patterns P-01..P-27
cat ~/.claude/skills/v1b1-capability/vocabulary-lockdown.md  # Excluded Terms list
```

The 5 steps run as Q&A in chat. Each step's branching tree is defined below. After each step, restate the chosen branch back to the contributor and confirm before proceeding.

#### Step 1 — Capability identification (Principle P3)

Ask the contributor to enumerate the operations the device performs. For each operation:

```
Is there an existing Capability ABC for this operation?
  YES → kind = "existing_implementation"; capability_name = <existing ABC name>;
        abstract_methods = <pulled from the ABC>
  NO  → Is there ALREADY a second device upstream that needs this same operation?
          YES → kind = "extract_new_ABC"; capability_name = <new name>;
                second_device_evidence = <required: file path + class name>
                If contributor cannot name the second device, downgrade to:
                kind = "device_specific_helper"
          NO  → kind = "device_specific_helper" (P-16; helper class; NO Backend ABC)
```

DEFAULT for novel operations: `device_specific_helper`. Bias is intentional — Principle P3: ABCs require two implementations. Over-extraction is the most common failure mode.

Existing Capability ABCs in the v1b1 catalog (read from `reference.md` Pattern Index for the current authoritative list): `Shaker`, `TemperatureController`, `PIP`, `Absorbance`, `Fluorescence`, `Luminescence`, `LoadingTray`, `ArticulatedArm`, `BarcodeScanner`, `RackReader`, `PlateAccess`, plus mixins `HasJoints`, `CanFreedrive`, `HasContinuousShaking`, `CanGrip`. Confirm against `reference.md` before answering — the catalog evolves.

#### Step 2 — File layout (Pattern P-12)

Estimate from step 1's outputs:

```
- 1 Driver + 1-2 Capability backends + 1 Device + 0 helpers + ≤500 estimated total lines
  → file_layout = "simple_single_file" (BioShake shape)
- Otherwise (multiple Capabilities, helpers present, command classes, or estimated >500 lines)
  → file_layout = "complex_multi_file" (Nimbus shape)
```

The 500-line threshold is the BioShake (440 lines) / Echo (2897 lines, too large) boundary. Encode as a hard branch; do not negotiate.

#### Step 3 — Driver shape (Patterns P-21, P-25, P-27)

Ask three sub-questions:

```
(a) Pick ONE transport form (P-21):
      a1) send_command(cmd: str)              — inline string commands (BioShake)
      a2) send_command(command_object)        — command-class organization (Nimbus)
      a3) send_command(module=..., command=..., **fw_params)  — module/command/kwargs (STAR)
      a4) _call_sdk(func, *args, op="...")    — SDK wrapper (xArm6)
      a5) _rpc(method, params, ...)           — RPC/SOAP (post-Echo extension)
    Pick by what your vendor protocol looks like. NO 6th form is acceptable.

(b) Discovery in setup()? (Principle P5 / P-18)
      YES → setup() runs introspection / firmware queries; backends conditionally constructed
            in Driver.setup; chatterbox extends Driver (P-04 documented exception)
      NO  → setup() opens connection only; chatterbox extends the Capability Backend ABC
            (P-04 standard form)

(c) Caller-supplied setup config? (P-22 / P-27)
      YES → nested <Driver>.SetupParams(BackendParams) + isinstance-check + default substitution;
            Driver.setup signature: async def setup(self, backend_params: Optional[BackendParams] = None)
      NO  → lighter form: async def setup(self) -> None
```

Constraint: `chatterbox_form == "discovery_exception"` REQUIRES `discovery == true` (P-04 exception only applies when discovery happens).

#### Step 4 — Backend shape (Principles P2, P6; Patterns P-20, P-25)

For each Capability identified in step 1 with `kind == existing_implementation`:

```
- Concrete Backend class: <Vendor><Device><Capability>Backend(<Capability>Backend)
- Stores driver: self.driver = driver (P-05 invariant)
- Per-operation method on Backend builds the wire payload (P-01 invariance — NEVER same-named on Driver)
- Workflow methods (multi-step trigger → poll → fetch) live on the Backend, NOT Capability frontend (P-20)
- _on_setup hook for capability-specific post-connection init (P-25)
```

CALL OUT EXPLICITLY (FR-013): "The wrong default for this step is workflow on the Capability frontend — putting `trigger → poll → fetch` orchestration in the Capability class instead of the Backend. Documented violation in PR #1009 (Micronic) Finding 2 and the Echo branch Finding 3 — both same contributor. We're avoiding that here."

#### Step 5 — Device wiring (Patterns P-07, P-13, P-23)

```
- Device.__init__: construct ONE driver
- For each Capability backend identified in step 1: construct Backend(driver) sharing the single driver (P-13)
- Assign as Device attribute (e.g., self.shaker = Shaker(backend=...))
- Append to self._capabilities

- Optional Resource integration (P-23):
  Does the Device physically hold a resource (plate, tip rack)?
    YES → resource_integration = true; multiple inheritance (Resource, Device); dual __init__ calls
    NO  → resource_integration = false; single-inheritance Device

- Convenience methods on Device (informational, not asked):
  Device convenience methods that map to Capability operations MUST go through self.<capability>.<method>,
  NEVER to self.driver.<method>. The wrong default — Capability bypass — is documented as Echo branch
  Finding 5; the scaffold places a # CAUTION: comment in the Device template warning the
  protocol-implementation phase against this.
```

### 4. Generate scaffold

Based on the Device Intent collected in step 3:

- Read `~/.claude/skills/v1b1-author/templates/` for the 8 scaffold templates.
- Select templates per intent:
  - `file_layout == simple_single_file` → instantiate `simple_single_file.py.tmpl` (1 file).
  - `file_layout == complex_multi_file` → instantiate `package_init.py.tmpl`, `driver.py.tmpl`, one `capability_backend.py.tmpl` per Capability with `kind == existing_implementation`, one `helper_subsystem.py.tmpl` per HelperChoice, `device.py.tmpl`, plus chatterbox (`chatterbox.py.tmpl` for standard form OR `chatterbox_driver.py.tmpl` for discovery exception).
- Substitute placeholders (full set per `contracts/scaffold-template-contract.md` Placeholder Set).
- Write each rendered file to its target path under the contributor's `pylabrobot/<vendor_lower>/<device_snake>/` (or single-file path for simple form per FR-005).
- Refuse to overwrite per step 2's earlier check (this catches the case where a re-scaffold was confirmed but a previously-unconfirmed file is in the way).

### 5. Generate decision record

- Read `~/.claude/skills/v1b1-author/decision-record-template.md`.
- Substitute the frontmatter fields from the Device Intent + each step section's Decision / Principle / v1b1 precedent / Wrong default avoided / Files-this-shapes content.
- Wrong-default callouts: ALWAYS present even when not visibly triggered. Use the template's documented Micronic + Echo references; tailor only the "Files this decision shapes" section.
- Write to `<contributor-repo>/docs/v1b1-authoring/<vendor>-<device>-decisions.md` per FR-008. Create the `docs/v1b1-authoring/` directory if it doesn't exist.

### 6. Pre-emit lint chain

Three stages, fixed order, halt on any failure (per `contracts/pre-emit-lint-contract.md`):

#### Stage 1 — Structural lint

Verify the rendered decision record contains:

- Frontmatter with all required fields (vendor, device, intent_text, file_layout, capabilities, helpers, discovery, chatterbox_form, review_skill_outcome — placeholder until stage 3 fills in)
- All 5 step sections, in order, with required sub-fields
- Cross-reference summary section
- References block
- Hand-off section

Verify the scaffold file list matches the file_layout choice (exactly the expected files; no extra; no missing).

Verify each Principle citation in the decision record matches a `principle_id` (P1..P6) in shared `reference.md`. Verify each v1b1 precedent file path exists in the local PLR mirror at the `verified_against` commit (skip if mirror not present).

**On failure**: re-render once with the missing field(s) inserted; if still failing, emit self-error naming the missing field. Halt.

#### Stage 2 — Vocabulary self-check

Grep skill-authored output (decision record + scaffold docstrings/comments) for any term in shared `vocabulary-lockdown.md` Excluded Terms set:

`Locality`, `Internality`, `Contract` (capitalized noun in skill prose), `EYES/I4S`, `three-layer`, `Resource Trust`, `Signal` (capitalized noun referring to the proposed pub/sub layer), `Device Card`.

Verbatim contributor input (intent_text echoed in the decision record's Intent block) is preserved unchanged — out of scope for the lockdown.

**On failure**: do not emit. Surface the leaked term and the section it appeared in. Halt.

#### Stage 3 — Review-skill call

Invoke the sibling skill on the scaffold:

```
/v1b1-capability <scaffold-path>
```

For simple form, `<scaffold-path>` is the single file. For complex form, it's the directory.

Read the review skill's Compliance summary line.

**Pass criterion**: `**Result**: 0 findings — compliant with v1b1 patterns.`

**Failure handling**:
- Any `hard` or `soft` Finding → enter repair mode. Read the Findings; identify which template emitted the offending shape. Re-render the affected files with stricter substitution. Re-call review skill.
- Maximum 1 repair attempt.
- If still failing after the repair attempt: emit self-error WITH the review report attached. Do NOT silently emit a non-conformant scaffold.
- `informational` Findings are allowed (Rick himself uses documented variants like model-as-prefix shorthand `XArm6Driver`); they do NOT fail stage 3.

On success: append the `review_skill_outcome: 0 findings (...)` line to the decision record's frontmatter.

### 7. Hand-off

Emit a clear next-step instruction (FR-019):

```
Scaffold: <path>
Decision record: <path>

Next:
1. Open the scaffold file(s) and fill in the # TODO: markers in <Backend>.
   - Backend method bodies: build wire payloads / parse responses (the protocol-encoding spots).
   - Driver: leave as generic transport — DO NOT add domain-named methods.
   - Capability frontend: leave as @need_capability_ready forwards — DO NOT add multi-step orchestration.
2. After each Capability operation: /v1b1-capability <scaffold-path> to verify.
3. When all done: /v1b1-capability one final time on the full path; expect 0 Findings.
```

Stop. The skill has done its job. Protocol-body filling is the contributor's domain expertise (FR-018).

## Key References

- **Shared pattern catalog**: `~/.claude/skills/v1b1-capability/reference.md` — Principles P1–P6, Patterns P-01..P-27, Audit Trail. READ at runtime; never copied.
- **Shared vocabulary lockdown**: `~/.claude/skills/v1b1-capability/vocabulary-lockdown.md` — Emit / Excluded term lists. READ at runtime.
- **Shared vendored prose**: `~/.claude/skills/v1b1-capability/creating-capabilities.md` — Rick's authoritative prose. READ at runtime for prose phrasing in step descriptions.
- **Local templates**: `~/.claude/skills/v1b1-author/templates/` — 8 scaffold templates per `contracts/scaffold-template-contract.md`.
- **Local decision-record template**: `~/.claude/skills/v1b1-author/decision-record-template.md` — frontmatter + 5 step sections + cross-reference + references + hand-off.
- **Local audit procedure**: `~/.claude/skills/v1b1-author/audit.md` — runnable step list; SHARED Audit Trail entry with v1b1-capability.
- **Spec contracts**: `contracts/` (in this skill bundle) — decision-record-contract, scaffold-template-contract, pre-emit-lint-contract.

## Notes

- The skill is downstream of the patterns Rick has documented and the device implementations the PLR community has contributed. It does not propose new patterns; new patterns enter via the `v1b1-capability` audit cadence (which this skill inherits via the SHARED Audit Trail).
- The skill uses Rick's terminology only (vocabulary lockdown enforced via stage 2 of the pre-emit lint).
- Same intent → same scaffold + same decision record (deterministic per `research.md` Decision 1). This is what makes the audit's "re-run + diff against reference fixture" check possible.
- v1.0 graduates separately from this v0.9-RC ship — SC-010 requires a real authoring session by the maintainer on a chosen target device with the scaffold passing the review skill on first invocation.
