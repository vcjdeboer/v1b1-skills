---
spec_id: S-01
vendor: Opentrons
device: Flex
mode: server
input_path: tests/smoke/inputs/opentrons-flex-openapi-snippet.yaml
intent_text: "(server mode — intent_text omitted; not used in this mode)"
expected_entry_count: 4
expected_transport_form: command-class
expected_outcome: clean-pass
expected_files:
  - <contributor-repo>/docs/v1b1-protocol/opentrons-flex-commands.md
expected_catalog:
  path: tests/fixtures/S-01-expected/opentrons-flex-commands.md
  entry_names_in_order: [Aspirate, Dispense, DropTip, PickUpTip]
expected_review_skill_outcome: "transport_form lookup PASS — command-class is in shared reference.md P-21 list"
---

# Smoke spec S-01: Opentrons Flex (server mode, MVP)

Exercises the server-mode dispatch on a 4-endpoint OpenAPI 3.0 subset of the Opentrons HTTP API. Drops directly into a `v1b1-author`-emitted `pylabrobot/opentrons/flex/pip_backend.py` scaffold.

## Verbatim contributor invocation (replay this for the audit)

```
/v1b1-protocol Opentrons Flex server ~/.claude/skills/v1b1-protocol/tests/smoke/inputs/opentrons-flex-openapi-snippet.yaml
```

## Expected behavior summary

- 4 endpoints in the OpenAPI snippet, one each for `Aspirate`, `Dispense`, `PickUpTip`, `DropTip` (the four PIP operations a Flex scaffold has TODO bodies for).
- Each endpoint is `POST /runs/{run_id}/commands` differentiated by `commandType` body field.
- Default `transport_form = command-class` (HTTP idiom).
- Default `confidence = confirmed` (server mode default).
- Pre-emit lint passes all 3 stages on first try.
- 0 Open Questions.
