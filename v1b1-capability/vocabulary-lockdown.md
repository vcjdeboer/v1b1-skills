---
title: "v1b1 Skill — Vocabulary Lockdown"
last_updated: 2026-04-25
audit_version: 1.0
status: allow-list only
---

# v1b1 Skill — Vocabulary Lockdown

## Policy

The v1b1 capability skill emits text in Rick Wierenga's vocabulary only. Terms appear in skill-authored output (violation reports, error messages, suggested fixes) only if they have a precedent in Rick's prose (`creating-capabilities.md`, vendored alongside this document) or in v1b1 code authored or merged by Rick.

This is an **allow-list**. The pre-emit self-check (see `skill-output-contract.md`) verifies that every term used in skill-authored output is covered by an entry in the **Emitted Terms** table below. Any term not on the allow-list fails the check, regardless of whether it has been explicitly enumerated as excluded — the skill does not need a deny-list.

Verbatim contributor input that uses an off-list term is preserved unchanged. The vocabulary lockdown applies to text the skill itself authors, not to text it quotes from the contributor's code.

---

## Emitted Terms

| Term | Type | Precedent (Rick's prose / v1b1 code) | Usage notes |
|------|------|--------------------------------------|-------------|
| `Driver` | Class name | `creating-capabilities.md` Architecture section; `pylabrobot/device.py` (`Driver` base class) | Capitalized when referring to the class; lowercase "driver" allowed in prose |
| `Device` | Class name | `creating-capabilities.md` Architecture section; `pylabrobot/device.py` (`Device` base class) | Capitalized for the class |
| `Capability` | Class name | `creating-capabilities.md` "Creating a new capability" section; `pylabrobot/capabilities/capability.py` | Capitalized for the class; lowercase as a noun ("the shaking capability") allowed in skill prose |
| `CapabilityBackend` | Class name | `creating-capabilities.md` "Creating a new capability" section; `pylabrobot/capabilities/capability.py` | — |
| `_capabilities` | Attribute | `creating-capabilities.md` Architecture section; `pylabrobot/device.py` | Always with leading underscore |
| `_on_setup` | Method | `creating-capabilities.md` Lifecycle section | Always with leading underscore; backend lifecycle hook |
| `_on_stop` | Method | `creating-capabilities.md` Lifecycle section | Always with leading underscore; backend lifecycle hook |
| `setup` | Method | `creating-capabilities.md` Lifecycle section | Refers to `Driver.setup()` / `Device.setup()` only; never on backends |
| `stop` | Method | `creating-capabilities.md` Lifecycle section | Refers to `Driver.stop()` / `Device.stop()` only; never on backends |
| `send_command` | Method | `creating-capabilities.md` "Common Mistakes" section example; `pylabrobot/hamilton/star/star_backend.py` (`STARDriver.send_command`) | Generic transport method on the driver |
| `send` | Method | `creating-capabilities.md` "Implementing a vendor device" section example | Alternative generic transport method on the driver |
| `BackendParams` | Pattern (nested class) | `pylabrobot/azenta/xpeel/xpeel_backend.py` (`XPeelPeelerBackend.PeelParams`); migration-guide-for-claude.md cross-reference instructions | Surfaced as `<Backend>.<Params>` nested classes |
| `Has...` | Mixin prefix | `pylabrobot/ufactory/xarm6/...` (`HasJoints`); `pylabrobot/qinstruments/...` (`HasContinuousShaking`) | Backend-mixin convention only; never as a standalone noun |
| `Can...` | Mixin prefix | `pylabrobot/ufactory/xarm6/...` (`CanFreedrive`); `CanGrip` precedent | Backend-mixin convention only |
| `Chatterbox` | Class type / role | `creating-capabilities.md` "Chatterbox backends" section; `<Capability>ChatterboxBackend` naming pattern | Capitalized when referring to the role |
| `<Vendor><Device>Driver` | Naming pattern | `creating-capabilities.md` "Naming conventions" table | Pattern, not a literal term; the skill uses real vendor/device names (e.g., `BioShakeDriver`) |
| `<Vendor><Device><Capability>Backend` | Naming pattern | `creating-capabilities.md` "Naming conventions" table | Pattern; e.g., `BioShakeShakerBackend`, `STARPIPBackend` |
| `<Name>Backend` | Naming pattern (abstract) | `creating-capabilities.md` "Naming conventions" table | Abstract Backend ABC convention, e.g., `ShakerBackend`, `LoadingTrayBackend` |
| `<Name>` | Naming pattern (capability frontend) | `creating-capabilities.md` "Naming conventions" table | Capability frontend, no suffix, e.g., `Shaker`, `LoadingTray` |
| `_subsystems` | Attribute | v1b1 STAR driver | Optional list pattern for device-specific helpers; usage varies across devices and is documented in `reference.md` Inconsistencies |
| `Resource` | Class name | `pylabrobot/resources/`; cross-cutting PLR concept | Used when discussing devices that inherit from `Resource` (e.g., `BioShake3000T(PlateHolder, Device)`); always capitalized for the class |
| `ResourceHolder` | Class name | v1b1 (e.g., `LoadingTray(Capability, ResourceHolder)`) | Same convention as Resource |

The table is exhaustive: every term the skill emits in synthesized output appears here. Adding a new term requires a new row.

---

## Term Addition Policy

A new term enters the **Emitted Terms** set when:

1. The term appears in Rick's prose (`creating-capabilities.md`) OR in v1b1 code authored or merged by Rick, AND
2. The term is needed by the skill to express a pattern, principle, or fix that the skill enforces, AND
3. The term is added to this document with all required fields (Term, Type, Precedent, Usage notes), AND
4. The audit procedure is re-run and reports zero vocabulary leaks across all skill output examples.

---

## Term Removal Policy

Terms are removed from **Emitted Terms** only when:

- Rick has explicitly retired the term in his prose or code, AND
- No remaining patterns in `reference.md` reference the term, AND
- The change is documented in the next audit trail entry.
