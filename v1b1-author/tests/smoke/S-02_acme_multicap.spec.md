---
spec_id: S-02
vendor: ACME
device: MultiCap
intent: "Multi-capability device with shaker + temperature controller + a door subsystem. HTTP transport. Runtime discovery (queries /info to determine which modules are installed). Modules vary across units. One door per device."
expected_form: complex_multi_file
expected_capabilities:
  - kind: existing_implementation
    name: Shaker
    abstract_methods: [shake, start_shaking, stop_shaking]
  - kind: existing_implementation
    name: TemperatureController
    abstract_methods: [set_temperature, get_temperature]
expected_helpers:
  - name: ACMEDoorBackend
    methods: [is_locked, lock, unlock]
    lifecycle_form: standalone
    device_attribute: door
    device_convenience_method: null
expected_discovery: true
expected_setup_params: false
expected_chatterbox_form: discovery_exception
expected_files:
  - pylabrobot/acme/multi_cap/__init__.py
  - pylabrobot/acme/multi_cap/driver.py
  - pylabrobot/acme/multi_cap/shaker_backend.py
  - pylabrobot/acme/multi_cap/temperature_backend.py
  - pylabrobot/acme/multi_cap/door_backend.py
  - pylabrobot/acme/multi_cap/chatterbox_driver.py
  - pylabrobot/acme/multi_cap/multi_cap.py
expected_decision_record:
  path: docs/v1b1-authoring/acme-multicap-decisions.md
  step_1_choice: existing-implementation (Shaker, TemperatureController) + device-specific-helper (ACMEDoorBackend)
  step_2_choice: complex-multi-file
  step_3_transport: send_command(command_object) — command-class organization (Nimbus-style for HTTP)
  step_3_discovery: true
  step_3_setup_params: false
  step_4_workflow_placement: backend
  step_5_resource_integration: false
expected_review_skill_outcome: 0 findings — compliant with v1b1 patterns
---

# Smoke spec S-02: ACME MultiCap (complex form)

Exercises the multi-file split, runtime discovery, the chatterbox-extends-Driver discovery exception (P-04), and the device-specific helper subsystem (P-16). Mirrors the Nimbus-shape complexity at scale.

## Verbatim contributor intent (replay this string)

```
Multi-capability device with shaker + temperature controller + a door subsystem.
HTTP transport. Runtime discovery (queries /info to determine which modules are installed).
Modules vary across units. One door per device.
```

## Expected behavior summary

- 5 Capability/Helper-shaped operations → 2 existing-implementation Capabilities (Shaker, TemperatureController) + 1 helper subsystem (ACMEDoorBackend per recommended P-16 naming).
- Multi-file form because >2 capabilities + helper present.
- HTTP transport → command-class organization picked.
- Discovery in setup() → P-04 chatterbox exception → chatterbox_driver.py form.
- No SetupParams (device probes; doesn't need caller config).
- No Resource integration (the device holds nothing as a child resource).
