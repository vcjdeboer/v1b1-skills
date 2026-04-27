---
spec_id: S-01
vendor: ACME
device: WidgetShaker
intent: "Single-capability shaker, serial port, no discovery, simple device. One physical model only. Operations: shake at speed for duration, stop shaking."
expected_form: simple_single_file
expected_capabilities:
  - kind: existing_implementation
    name: Shaker
    abstract_methods: [shake, start_shaking, stop_shaking]
expected_helpers: []
expected_discovery: false
expected_setup_params: false
expected_chatterbox_form: standard
expected_files:
  - pylabrobot/acme/widget_shaker.py
expected_decision_record:
  path: docs/v1b1-authoring/acme-widgetshaker-decisions.md
  step_1_choice: existing-implementation (Shaker)
  step_2_choice: simple-single-file
  step_3_transport: send_command(cmd: str)
  step_3_discovery: false
  step_3_setup_params: false
  step_4_workflow_placement: backend
  step_5_resource_integration: false
expected_review_skill_outcome: 0 findings — compliant with v1b1 patterns
---

# Smoke spec S-01: ACME WidgetShaker (simple form)

The contributor input below is replayed verbatim during the audit's "re-run skill on the spec" step. The frontmatter records the expected outcome — what the skill should produce given this exact input.

## Verbatim contributor intent (replay this string)

```
Single-capability shaker, serial port, no discovery, simple device.
One physical model only. Operations: shake at speed for duration, stop shaking.
```

## Expected Q&A walk

```
Skill: Step 1 — Capability identification.
       From your intent, I see one operation family: shaking. The Shaker Capability ABC
       already exists in pylabrobot.capabilities.shaking. Confirm?
You:   yes
Skill: Are there any operations the device performs that are NOT shaking?
You:   no

Skill: Step 2 — File layout.
       Single Capability, no discovery, no helpers, ≤500 expected lines.
       → simple single-file form (BioShake shape).
       File: pylabrobot/acme/widget_shaker.py

Skill: Step 3 — Driver shape.
       For serial transport, the standard P-21 form is `send_command(cmd: str)`. Confirm?
You:   yes
Skill: Discovery in setup()?
You:   no
Skill: Caller-supplied setup config?
You:   no

Skill: Step 4 — Backend shape. ACMEWidgetShakerShakerBackend implements Shaker's abstract methods.
       Workflow on Backend (P-20 wrong default: workflow on Capability frontend).

Skill: Step 5 — Device wiring. ACMEWidgetShaker(Device) wires one driver, one Shaker, _capabilities = [self.shaker].
       No Resource integration (the device doesn't physically hold a plate at this scope).

Skill: Generating scaffold + decision record... pre-emit lint... PASS.
       Scaffold: pylabrobot/acme/widget_shaker.py
       Decision record: docs/v1b1-authoring/acme-widgetshaker-decisions.md
```
