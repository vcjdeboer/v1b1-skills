---
spec_id: S-03
vendor: UFactory
device: XArm6
mode: dll
input_path: tests/smoke/inputs/xarm-wrapper-init.pyi
intent_text: "(dll mode — intent_text omitted; not used in this mode)"
expected_entry_count: 5
expected_transport_form: sdk-wrapper
expected_outcome: clean-pass
expected_files:
  - <contributor-repo>/docs/v1b1-protocol/ufactory-xarm6-commands.md
expected_catalog:
  path: tests/fixtures/S-03-expected/ufactory-xarm6-commands.md
  entry_names_in_order: [MotionEnable, SetGripperPosition, SetMode, SetServoAngle, SetState]
expected_review_skill_outcome: "transport_form lookup PASS — sdk-wrapper is in shared reference.md P-21 list"
---

# Smoke spec S-03: UFactory XArm6 (dll mode)

Exercises the dll-mode mechanical extraction on a 5-method subset of the upstream xArm-Python-SDK `XArmAPI` class stub. Drops directly into a v1b1-author-scaffolded `XArm6Driver._call_sdk` slot for any UFactory XArm6 scaffold.

## Verbatim contributor invocation (replay this for the audit)

```
/v1b1-protocol UFactory XArm6 dll ~/.claude/skills/v1b1-protocol/tests/smoke/inputs/xarm-wrapper-init.pyi
```

## Expected behavior summary

- 5 public methods in the `.pyi` stub: `motion_enable`, `set_gripper_position`, `set_mode`, `set_servo_angle`, `set_state`. Each yields one Catalog Entry.
- Each entry's `verb_or_opcode` is the fully-qualified method name (`XArmAPI.<method>`).
- `request_shape` is the parameter list with types from the stub annotations; `response_shape` is the return type (`int` for the four code-returning methods; `int` for `set_servo_angle` likewise).
- `side_effects` is a one-sentence trim of each method's docstring.
- Default `transport_form = sdk-wrapper` (xArm6 idiom).
- Default `confidence = confirmed` (mechanical extraction; no Q&A).
- Pre-emit lint passes all 3 stages on first try.
- 0 Open Questions.
- No Q&A loop is invoked — dll mode is mechanical, not multi-turn.
