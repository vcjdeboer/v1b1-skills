---
title: "v1b1 Capability Patterns — Reference Document"
target_branch: v1b1
verified_against: d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa
last_audited: 2026-04-25
audit_version: 1.0
last_shared_audit: 2026-04-25 (run 6; covers v1b1-capability v1.0 + v1b1-author v0.9-RC + v1b1-protocol v0.9-RC)
skill_version: 1.0
status: COMPLETE for v1.0 — 23 patterns populated (P-01..P-14, P-16..P-27); P-15 deferred. Tecan EVO and Echo (PR #1001) deferred — not on local branches at this audit. Smoke corpus + anti-pattern corpus run 2026-04-25 with Phase 8 contract (PR-URL input, Severity field, pre-emit lint).
secondary_branches:
  - branch: upstream/ot2-capability-migration-v2
    verified_against: 2e6191674b33ebb69c43381f784e67ee6980913d
    used_for: Opentrons OT2 citations (P-19 shared driver state; P-17 multi-instance via backend constructor parameter)
---

# v1b1 Capability Patterns — Reference Document

Audit artifact and source of truth for the patterns the skill enforces. Each Pattern entry carries a v1b1 evidence reference (file path, class name, commit hash). The audit walks every citation pre-release.

The vendored prose (`creating-capabilities.md`, SHA-256 `3767edbf47b582c111efbca8370e917d6714dfc6c301eae96ce88152c0e73a15`) is byte-identical to `pylabrobot/creating-capabilities.md` on v1b1 at commit `d3c6d0a5`. Parity check passes with zero drift.

---

## Principles

Six principles derived from v1b1's revealed behavior across xArm6, BioShake, Nimbus, STAR, Tecan Infinite, and Opentrons OT2 (all verified at the commit hashes in frontmatter). The architecture and prose are Rick Wierenga's; the device implementations from which these principles are extracted are work contributed across the PLR community over many merged PRs. Pattern entries below reference these principles by ID. The skill's violation reports cite the principle behind each finding so contributors can reason about cases the skill hasn't anticipated.

### P1 — Capability transferability

**Statement**: A Capability with a Backend ABC is a contract that other devices should be able to implement. ABCs exist when at least two devices have implemented the same operation; ABCs are not designed in advance from a single device's needs.

**Revealed behavior**:

- `LoadingTrayBackend` (`pylabrobot.capabilities.loading_tray`) — Tecan Infinite implements it (`pylabrobot/tecan/infinite/loading_tray_backend.py`); BioTek Cytation implements it (per spec evidence references). Two real precedents preceded the ABC.
- `ShakerBackend` (`pylabrobot.capabilities.shaking`) — BioShake (`pylabrobot/qinstruments/bioshake.py:141`) is one implementation; the existence of HamiltonHeaterShaker and other shakers implies prior implementations that triggered ABC extraction.
- *Counter-example*: STAR's `STARCover`, `STARAutoload`, `STARWashStation`, `STARXArm`, and Nimbus's `NimbusDoor` are device-specific helpers attached to the driver as plain classes (P-16). No Backend ABC has been extracted for cover-locking, wash-station-filling, or arm-positioning, because no second device has needed the same operation. This is the principle in action — Rick has *not* prematurely created `CoverBackend` / `WashStationBackend`.

**Patterns serving this principle**: P-13 (multi-capability shared driver — only when capabilities transfer), P-16 (device-specific helpers stay device-specific until a second device needs them), P-17 (multi-instance shapes can vary; the *contract* is what transfers, not the wiring).

---

### P2 — Hardware agnosticity at the capability frontend

**Statement**: Code that uses a Capability frontend (`device.absorbance.read(...)`, `device.left.aspirate(...)`) runs unchanged across vendors. The Capability frontend exposes the abstract operation; the Backend ABC defines what every backend must implement; the concrete backend translates to the vendor-specific protocol. Vendor-specific assumptions never appear in the Capability frontend.

**Revealed behavior**:

- `Absorbance(backend=...)` is the same Capability frontend regardless of vendor. Tecan Infinite wires it via `Absorbance(backend=TecanInfiniteAbsorbanceBackend(driver))` (`pylabrobot/tecan/infinite/infinite.py:58`). A user calling `reader.absorbance.read(plate=..., wavelength=600)` does not need to know which vendor's plate reader is wired underneath.
- `PIP(backend=...)` works the same across Hamilton STAR (`pylabrobot/hamilton/liquid_handlers/star/star.py:42`), Hamilton Nimbus (`pylabrobot/hamilton/liquid_handlers/nimbus/nimbus.py:49`), and Opentrons OT2 (`pylabrobot/opentrons/ot2/ot2.py:42-43` on the OT2 branch). Same Capability class, three vendor backends.
- Vendor-specific extensions go in `BackendParams` (P-22) — `NimbusPIPAspirateParams`, `TecanInfiniteAbsorbanceParams`, `XArm6ArmBackend.CartesianMoveParams`. The Capability method signature stays generic.

**Patterns serving this principle**: P-06 (four-layer architecture — the agnostic frontend is the user-facing layer), P-08, P-09, P-10, P-11 (consistent naming so contributors recognize the layers), P-22 (vendor specifics live in `BackendParams`, never in the Capability frontend).

---

### P3 — ABC extraction trigger

**Statement**: A Backend ABC is born when a second device needs the same operation. The ABC is extracted from both implementations together, so it represents what's actually shared, not what someone speculated would be shared.

**Revealed behavior**:

- Rick has *not* extracted ABCs for one-device operations on v1b1. STAR's four helpers (`STARCover`, `STARWashStation`, `STARXArm`, `STARAutoload`) and Nimbus's `NimbusDoor` remain plain classes. The cover-locking interfaces between STAR and Nimbus are similar (both have `lock`, `unlock`, status query) but no `CoverBackend` ABC exists at `d3c6d0a5` — the second-device threshold for cover specifically has not yet pulled the trigger.
- *Positive example*: `LoadingTrayBackend` was extracted only after multiple plate readers needed it. Per the spec, the Tecan Infinite migration (PR #989-area) added the third or fourth implementation and consolidated the ABC.
- *Behaviour vs prose*: Rick's prose (`creating-capabilities.md`) presents the four-layer architecture as if Backend ABCs always pre-exist. The code reveals the practice: ABCs are added when reuse is proven, not when the device is first written.

**Patterns serving this principle**: P-13 (multi-capability shared driver — when capabilities exist as ABCs they share a driver), P-16 (helpers without Backend ABCs are the visible result of "no second device yet").

---

### P4 — Keep the ABC small, grow through mixins

**Statement**: Adding a method to a Backend ABC is an N-device breaking change — every existing concrete backend must implement it. Adding a mixin breaks zero devices because backends opt in. When a method is supported by some backends but not all, use a mixin (`Has...` / `Can...`). Promote a mixin method to the ABC only when all backends support it.

**Revealed behavior**:

- xArm6: `XArm6ArmBackend(ArticulatedGripperArmBackend, HasJoints, CanFreedrive)` (`pylabrobot/ufactory/xarm6/backend.py:16`). Joint-space control and freedrive mode are optional behaviors; the backend explicitly opts in. Not every robotic arm has joints exposed or supports freedrive — the mixin pattern lets xArm6 declare what it supports without forcing other arms to comply.
- BioShake: `BioShakeShakerBackend(ShakerBackend, HasContinuousShaking)` (`pylabrobot/qinstruments/bioshake.py:141`). Continuous shaking (start/stop without duration) is optional; not every shaker has it.
- *Counter-example (legacy)*: BioShake's `supports_locking: bool` and `supports_active_cooling: bool` flags (`pylabrobot/qinstruments/bioshake.py:223,243`) are the older `supports_X` pattern Rick has signaled he wants to retire. Both patterns coexist on v1b1; mixins are the recommended replacement.

**Patterns serving this principle**: P-14 (backend-mixin pattern), P-26 (Device-attribute marker mixin — a separate, parallel mixin tier on the Device class).

---

### P5 — Discovery before wiring

**Statement**: When a device's hardware varies at runtime — pipette type, installed modules, firmware version, optional accessories — the Driver discovers what's actually present in `setup()`, and then the Device wires capabilities conditionally based on what was discovered. The Device class does not assume hardware that isn't there.

**Revealed behavior**:

- STAR (`pylabrobot/hamilton/liquid_handlers/star/driver.py:268-319`) — the strongest precedent. `STARDriver.setup` issues `RM` and `QM` firmware commands, populates typed `MachineConfiguration` and `ExtendedConfiguration` dataclasses, then conditionally creates `STARPIPBackend` (always), `STARHead96Backend` (if `core_96_head_installed`), `iSWAPBackend` (if `iswap_installed`), `STARAutoload` (if `auto_load_installed`), `STARXArm` left and right (right only if `right_x_drive_large`), `STARCover` (always), `STARWashStation` (if installed). The Device then wires the corresponding Capability frontends in `_HamiltonSTAR.setup` only for backends that exist.
- Nimbus (`pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:61-101`) — `NimbusDriver.setup` calls `_discover_instrument_objects()` (introspection over the protocol), extracts pipette and door addresses, conditionally constructs `NimbusPIPBackend` (always) and `NimbusDoor` (only if `door_address` was discovered).
- OT2 (`pylabrobot/opentrons/ot2/driver.py:53-58` on the OT2 branch) — `OpentronsOT2Driver.setup` calls `ot_api.lh.add_mounted_pipettes()` to discover left and right pipettes. `OpentronsOT2.__init__` wires both `left` and `right` PIP capabilities at construction time and `set_deck` distributes the deck.

**Patterns serving this principle**: P-18 (runtime configuration discovery — the canonical implementation pattern), P-13 (multi-capability shared driver — discovery decides which capabilities exist), P-16 (helpers conditionally created from discovery).

---

### P6 — Driver is the wire, backend is the protocol

**Statement**: The Driver owns transport — opening the connection, sending bytes, receiving responses. The Backend owns the protocol — encoding capability operations into wire payloads, parsing responses, sequencing multi-step commands. Driver methods are generic (`send`, `send_command`, `run_measurement`); same-named methods on driver and backend mean the driver has been asked to encode protocol meaning, which belongs in the backend.

**Revealed behavior**:

- STAR (`pylabrobot/hamilton/liquid_handlers/star/driver.py`) — the public driver surface is `send_command(module=..., command=..., **fw_params)` (transport) plus instrument-config / EEPROM / area-reservation / firmware-query methods (cross-capability device-level ops, never named after a Capability operation). The PIP backend builds firmware payloads inline and calls `send_command`; the wire format encoding lives in the backend.
- BioShake (`pylabrobot/qinstruments/bioshake.py`) — `BioShakeDriver.send_command(cmd: str)` is the wire transport. `BioShakeShakerBackend.start_shaking` builds `f"setShakeTargetSpeed{speed}"` and calls `send_command` (lines 170-194). Same with `BioShakeTemperatureBackend.set_temperature` building `f"setTempTarget{temperature_tenths}"` (line 264).
- Nimbus (`pylabrobot/hamilton/liquid_handlers/nimbus/`) — driver uses `send_command(command_object)`; command objects in `commands.py` encapsulate the wire format. Same separation: driver is wire, backend (and command objects) are protocol.
- xArm6 (`pylabrobot/ufactory/xarm6/driver.py:50-86`) — `_call_sdk(func, *args, op="...")` is the SDK transport. Backend methods call `_call_sdk` to issue specific SDK calls.
- *Anti-pattern documented in `creating-capabilities.md`*: a `Driver.set_temperature(temperature)` method that mirrors a Capability operation. The driver is now encoding protocol meaning, the backend's same-named method becomes a pointless delegation, and the wire-format string lives one layer too low. Pattern P-01.

**Patterns serving this principle**: P-01 (the canonical anti-pattern — driver mirroring capability), P-02–P-05 (the other four "Common Mistakes" all relate to lifecycle and integration discipline that keep the wire/protocol separation honest), P-07 (lifecycle hook ordering), P-19 (shared state on driver — the wire layer holds discovery output for backends to read), P-20 (workflow methods belong on the backend, never on the driver), P-25 (lifecycle hook scope: driver opens connection, backend does post-connection capability init).

---

The skill's violation reports cite a principle by ID and name on every finding. Contributors who hit edge cases the skill hasn't anticipated can read the principle and decide for their own case whether the same logic applies.

---

## Pattern Index

| Pattern | Name | Principle | Source | Anti-pattern fixture |
|---------|------|-----------|--------|---------------------|
| P-01 | Driver-Capability method-name collision | P6 | prose | A-01 |
| P-02 | Backend uses `setup`/`stop` instead of `_on_setup`/`_on_stop` | P6 | prose | A-02 |
| P-03 | Hardware-specific init in `driver.setup()` | P6 | prose | A-03 |
| P-04 | Chatterbox backend inherits from `Driver` | P6 | prose | A-04 |
| P-05 | Backend does not hold `self._driver` | P6 | prose | A-05 |
| P-06 | Four-layer architecture (Device / Driver / Capability / CapabilityBackend) | P2 | prose+code | — |
| P-07 | Lifecycle hook ordering | P6 | prose+code | — |
| P-08 | `<Vendor><Device>Driver` naming | P2 | prose+code | — |
| P-09 | `<Vendor><Device><Capability>Backend` naming (with documented shorthand variant) | P2 | prose+code | — |
| P-10 | Capability frontend `<Name>` naming (no suffix) | P2 | prose+code | — |
| P-11 | Backend ABC `<Name>Backend` naming | P2 | prose+code | — |
| P-12 | File layout (simple single-file vs complex split) | — | prose+code | — |
| P-13 | Multi-capability shared driver | P1 | prose+code | — |
| P-14 | Backend-mixin pattern (`Has...` / `Can...` ABCs) | P4 | code | A-06 |
| P-16 | Device-specific helper subsystems | P3 | code | A-07 |
| P-17 | Multi-instance / runtime-assembled capabilities (adapter or context-manager) | — | code | — |
| P-18 | Runtime configuration discovery | P5 | code | pending |
| P-19 | Shared state on the driver | P6 | code | — |
| P-20 | Workflow methods sequencing vendor calls belong on the backend | P6 | code | A-08 |
| P-21 | Driver-internal protocol organization is free choice | — | code | — (multi-precedent) |
| P-22 | `BackendParams` for typed vendor parameters | P2 | code | — (multi-form) |
| P-23 | Resource integration via multiple inheritance | — | code | — |
| P-24 | Concurrency primitives are device-author's choice | — | code | — |
| P-25 | Lifecycle hook scope (driver setup opens connection; backend `_on_setup` does hardware-specific init) | P6 | prose+code | — |
| P-26 | Device-attribute marker mixin (`Has<Capability>` on the Device class) | — | code | — |
| P-27 | `Driver.setup` signature convention (`backend_params: Optional[BackendParams] = None` + nested `SetupParams`) | P6 | code | — |

Patterns pending later slices: P-15 (internal `_method` pattern auto-triggered by Capability — likely surfaces in Shaking / Heating backends, not in liquid-handling).

**A-07 audit conclusion**: Capability-*frontend* mixins (mixins on the `Capability` class itself, not on the backend ABC) are NOT observed on v1b1 across xArm6, BioShake, Nimbus, STAR, or Tecan Infinite. The closest pattern is the Device-attribute marker mixin (P-26 — `HasLoadingTray` mixed into the Device class). The skill therefore does not emit Capability-frontend mixin shapes.

---

## Patterns

### P-01 — Driver-Capability method-name collision

**Source**: prose
**Principle**: P6 — Driver is the wire, backend is the protocol
**First documented in**: `creating-capabilities.md` "Common mistakes" section, "Driver mirrors capability interface (WRONG)" example.

**Anti-pattern signature**: A `Driver` subclass defines a method whose name matches a Capability operation (e.g., `set_temperature`, `aspirate`, `shake`). The matching backend's same-named method then becomes a pointless delegation through the driver, and the wire-format encoding lives in the wrong place.

**Recognized form**: Driver exposes generic transport (`send_command`, `send`); backend builds the wire payload and calls the transport directly.

```python
# CORRECT
class STARDriver(Driver):
  async def send_command(self, module: str, command: str, **fw_params): ...

class STARPIPBackend(PIPBackend):
  async def aspirate(self, ...):
    # builds firmware params, calls send_command
    ...
```

**Fix**: Rename driver method to underscore-prefixed private wire method (1-to-1 with vendor endpoint) OR move the encoding to the backend.

**Anti-pattern fixture**: `tests/anti-patterns/A-01_driver_mirrors_capability.py`

---

### P-02 — Backend uses `setup`/`stop` instead of `_on_setup`/`_on_stop`

**Source**: prose
**Principle**: P6
**First documented in**: `creating-capabilities.md` Lifecycle section.

**Anti-pattern signature**: A `CapabilityBackend` subclass overrides `setup()` or `stop()` (the Device/Driver public lifecycle methods). The Capability lifecycle never calls these, so the override is dead code.

**Recognized form**: Backend overrides `_on_setup()` / `_on_stop()`. These are called automatically by `Capability._on_setup()` / `_on_stop()` during `Device.setup()` / `Device.stop()`.

**Fix**: Rename the methods. `setup` → `_on_setup`; `stop` → `_on_stop`.

**Anti-pattern fixture**: `tests/anti-patterns/A-02_backend_lifecycle_naming.py`

---

### P-03 — Hardware-specific init in `driver.setup()` instead of `backend._on_setup()`

**Source**: prose
**Principle**: P6
**First documented in**: `creating-capabilities.md` "Backend `_on_setup` / `_on_stop`" section.

**Anti-pattern signature**: Capability-specific hardware initialization (configure objectives, configure filter cubes, calibrate shaker drive) appears in `Driver.setup()`. The driver's `setup()` should only open the connection.

**Recognized form**: Driver `setup` opens connection; backend `_on_setup` does capability-specific init that requires the connection to be open.

```python
class PicoMicroscopyBackend(MicroscopyBackend):
  async def _on_setup(self):
    for pos, obj in self._objectives.items():
      await self.change_objective(pos, obj)
```

**Fix**: Move the hardware-specific work from `Driver.setup` to `Backend._on_setup`.

**Anti-pattern fixture**: `tests/anti-patterns/A-03_init_in_driver.py`

**Inconsistency note**: xArm6's `XArm6Driver.setup` does call `set_gripper_mode` / `set_gripper_enable` (gripper-specific init), with a `skip_gripper_init: bool` escape hatch in `SetupParams`. Borderline: the gripper is the arm capability's hardware, but it's wired in driver setup. The skill flags this as a soft warning (not a hard violation) when the same shape appears.

---

### P-04 — Chatterbox backend inherits from `Driver`

**Source**: prose
**Principle**: P6 (chatterbox replaces the backend, not the driver)
**First documented in**: `creating-capabilities.md` "Chatterbox backends (testing)" section.

**Anti-pattern signature**: A class with "Chatterbox" in its name inherits from `Driver` (or co-inherits Driver alongside a backend ABC).

**Recognized form**: `class MyFanChatterboxBackend(FanBackend):` — inherits *only* from the capability's backend ABC.

**Fix**: Remove `Driver` from the bases. Chatterbox provides backend stubs only.

**Anti-pattern fixture**: `tests/anti-patterns/A-04_chatterbox_extends_driver.py`

**Inconsistency note**: Two devices on v1b1 ship a `*ChatterboxDriver` that extends the `Driver` (not a backend ABC):

- `NimbusChatterboxDriver(NimbusDriver)` — `pylabrobot/hamilton/liquid_handlers/nimbus/chatterbox.py:18` at commit `d3c6d0a5`. Selected via `chatterbox: bool` flag in `Nimbus.__init__`.
- `STARChatterboxDriver(STARDriver)` — `pylabrobot/hamilton/liquid_handlers/star/chatterbox.py:43` at commit `d3c6d0a5`. Selected via `chatterbox: bool` flag in `_HamiltonSTAR.__init__`. Carries pre-built `_DEFAULT_MACHINE_CONF` and `_DEFAULT_EXTENDED_CONF` to substitute for runtime discovery.

The justification, common to both: these drivers do runtime discovery in `setup()`, and a chatterbox backend cannot fake discovery — the chatterbox has to live at the driver layer to substitute the discovery output. The skill treats `*ChatterboxDriver` (extends Driver) as a documented exception when the device's `setup()` performs discovery; for simpler devices without discovery the prose pattern (`*ChatterboxBackend` extending the backend ABC) applies.

---

### P-05 — Backend does not hold `self._driver`

**Source**: prose
**Principle**: P6
**First documented in**: `creating-capabilities.md` "Implementing a vendor device" section examples.

**Anti-pattern signature**: A `CapabilityBackend` subclass either does not store the driver reference at all, or constructs a fresh driver per call. Either way, the backend cannot share the Device's wired driver and lifecycle is broken.

**Recognized form**: Backend `__init__` accepts `driver: <Vendor><Device>Driver` and stores `self._driver = driver`.

**Fix**: Add `driver` parameter to `__init__`, store on `self._driver`, and use it for transport.

**Anti-pattern fixture**: `tests/anti-patterns/A-05_backend_missing_driver_ref.py`

**Note on attribute name**: Some backends use `self.driver` (no underscore) — see Nimbus and BioShake examples. The Device class also exposes `self.driver` for user access. This is consistent across v1b1; the prose's `self._driver` is a stricter convention not universally followed. The skill enforces "the backend stores SOME reference to the driver named `driver` or `_driver`," not a specific underscore prefix.

---

### P-06 — Four-layer architecture (Device / Driver / Capability / CapabilityBackend)

**Source**: prose+code
**Principle**: P2
**First documented in**: `creating-capabilities.md` Architecture section.

**Recognized form**:

```
Device
  ├── _driver: Driver
  └── _capabilities: [Capability, ...]
        └── backend: CapabilityBackend (holds reference to _driver)
```

**Evidence citations** (verified at `d3c6d0a5`):

- `pylabrobot/ufactory/xarm6/xarm6.py` — `XArm6` (Device) wires `XArm6Driver` (Driver), `XArm6ArmBackend` (CapabilityBackend), `ArticulatedArm` (Capability).
- `pylabrobot/qinstruments/bioshake.py` — `BioShake` (Device) wires `BioShakeDriver` (Driver), `BioShakeShakerBackend` and `BioShakeTemperatureBackend` (CapabilityBackend×2), `Shaker` and `TemperatureController` (Capability×2).
- `pylabrobot/hamilton/liquid_handlers/nimbus/nimbus.py` — `Nimbus` (Device) wires `NimbusDriver` (Driver), `NimbusPIPBackend` (CapabilityBackend), `PIP` (Capability).

---

### P-07 — Lifecycle hook ordering

**Source**: prose+code
**Principle**: P6
**First documented in**: `creating-capabilities.md` Lifecycle section.

**Recognized form**: `Device.setup()` → `driver.setup()` → for each cap in `_capabilities`: `cap._on_setup()` → `cap.backend._on_setup()` → set `_setup_finished`. `Device.stop()` walks `_capabilities` reversed, then `driver.stop()`.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/nimbus/nimbus.py:38-67` — `Nimbus.setup` and `Nimbus.stop` follow this exactly: `await self.driver.setup()`, then `self._capabilities = [self.pip]`, `await self.pip._on_setup()`, set `_setup_finished = True`. `stop()` reverses.
- `pylabrobot/hamilton/liquid_handlers/nimbus/pip_backend.py:154-167` — `NimbusPIPBackend._on_setup` runs SmartRoll initialization (capability-specific work after driver setup).
- `pylabrobot/hamilton/liquid_handlers/nimbus/door.py:29-40` — `NimbusDoor._on_setup` and `_on_stop` use the leading-underscore hook convention even though Door is a helper, not a CapabilityBackend.

---

### P-08 — `<Vendor><Device>Driver` naming

**Source**: prose+code
**Principle**: P2
**First documented in**: `creating-capabilities.md` "Naming conventions" table.

**Recognized form**: Driver class is named `<Vendor><Device>Driver`.

**Evidence citations**:

- `XArm6Driver` — `pylabrobot/ufactory/xarm6/driver.py:17`.
- `BioShakeDriver` — `pylabrobot/qinstruments/bioshake.py:29`.
- `NimbusDriver` — `pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:23`.

**Inconsistency note**: xArm6 uses the model name as both vendor and device prefix (`XArm6Driver` rather than `UFACTORYXArm6Driver`). This is shorthand for devices whose model name is well-known. The skill accepts either form.

---

### P-09 — `<Vendor><Device><Capability>Backend` naming

**Source**: prose+code
**Principle**: P2
**First documented in**: `creating-capabilities.md` "Naming conventions" table.

**Recognized form**: Concrete backend is named `<Vendor><Device><Capability>Backend`.

**Evidence citations**:

- `BioShakeShakerBackend` — `pylabrobot/qinstruments/bioshake.py:141`.
- `BioShakeTemperatureBackend` — `pylabrobot/qinstruments/bioshake.py:236`.
- `NimbusPIPBackend` — `pylabrobot/hamilton/liquid_handlers/nimbus/pip_backend.py:122`.
- `XArm6ArmBackend` — `pylabrobot/ufactory/xarm6/backend.py:16`.

**Inconsistency note**: `XArm6ArmBackend` uses the shorthand `Arm` rather than the full Capability name `ArticulatedArm`. The skill accepts a documented shorthand when the abbreviation is unambiguous in the device's context.

---

### P-10 — Capability frontend `<Name>` naming (no suffix)

**Source**: prose+code
**Principle**: P2
**First documented in**: `creating-capabilities.md` "Naming conventions" table.

**Recognized form**: Capability frontend class has no suffix.

**Evidence citations**:

- `Shaker` — `pylabrobot/capabilities/shaking/__init__.py` (re-export).
- `TemperatureController` — `pylabrobot/capabilities/temperature_controlling/__init__.py`.
- `PIP` — `pylabrobot/capabilities/liquid_handling/pip.py`.
- `ArticulatedArm` — `pylabrobot/capabilities/arms/articulated_arm.py`.

---

### P-11 — Backend ABC `<Name>Backend` naming

**Source**: prose+code
**Principle**: P2
**First documented in**: `creating-capabilities.md` "Naming conventions" table.

**Recognized form**: Abstract Backend class is named `<Name>Backend` where `<Name>` is the capability noun.

**Evidence citations**:

- `ShakerBackend` — `pylabrobot/capabilities/shaking/backend.py`.
- `TemperatureControllerBackend` — `pylabrobot/capabilities/temperature_controlling/...`.
- `PIPBackend` — `pylabrobot/capabilities/liquid_handling/pip_backend.py`.
- `ArticulatedGripperArmBackend` — `pylabrobot/capabilities/arms/backend.py`.

**Inconsistency note**: `ArticulatedGripperArmBackend` includes a device-shape qualifier (`Gripper`). Backend ABCs may include such qualifiers when a single capability has multiple shape variants — the skill does not flag qualifiers in ABC names.

---

### P-12 — File layout (simple single-file vs complex split)

**Source**: prose+code
**Principle**: —
**First documented in**: `creating-capabilities.md` "File layout" section.

**Recognized forms**:

**Simple (single-file)**: One file containing Driver + Backend(s) + Device.

```
pylabrobot/qinstruments/
├── __init__.py
└── bioshake.py            # BioShakeDriver + BioShakeShakerBackend + BioShakeTemperatureBackend + BioShake
```

**Complex (split)**: One file per major class.

```
pylabrobot/hamilton/liquid_handlers/nimbus/
├── __init__.py
├── driver.py              # NimbusDriver
├── pip_backend.py         # NimbusPIPBackend
├── door.py                # NimbusDoor (helper)
├── commands.py            # Command classes
├── chatterbox.py          # NimbusChatterboxDriver
└── nimbus.py              # Nimbus device
```

**Multi-file alternative**: Driver + per-feature files + main backend in one file, used by xArm6.

```
pylabrobot/ufactory/xarm6/
├── __init__.py
├── driver.py              # XArm6Driver
├── backend.py             # XArm6ArmBackend
├── joints.py              # XArm6Axis enum
└── xarm6.py               # XArm6 device
```

---

### P-13 — Multi-capability shared driver

**Source**: prose+code
**Principle**: P1
**First documented in**: `creating-capabilities.md` "Multi-capability device (shared driver)" section.

**Recognized form**: One `Driver`, multiple `CapabilityBackend` instances each holding the same driver, all wired into `_capabilities` on the device.

**Evidence citations**:

- `pylabrobot/qinstruments/bioshake.py:300-326` — `BioShake.__init__` constructs `BioShakeDriver(port=port)` once, then conditionally wires `Shaker(backend=BioShakeShakerBackend(driver))` and `TemperatureController(backend=BioShakeTemperatureBackend(driver))` based on `has_shaking` / `has_temperature` flags.
- `pylabrobot/hamilton/liquid_handlers/star/star.py:38-53` — `_HamiltonSTAR.setup` wires `PIP`, `Head96`, and `OrientableArm` (iSWAP) onto the same `STARDriver`. Three capabilities share one driver. The Head96 and iSWAP wiring is conditional on discovery results (P-18).
- `pylabrobot/tecan/infinite/infinite.py:31-75` — `TecanInfinite200Pro.__init__` wires four capabilities (`Absorbance`, `Fluorescence`, `Luminescence`, `LoadingTray`) onto the same `TecanInfiniteDriver`. All four backends take the same driver in their constructor. The most fully-realized multi-capability shared-driver precedent on v1b1.

**Note**: Use of constructor flags (`has_shaking=True`) here is a constructor-time form of P-18 (discovery before wiring). Stronger forms (runtime hardware introspection) are documented separately under P-18.

---

### P-14 — Backend-mixin pattern (`Has...` / `Can...` ABCs)

**Source**: code
**Principle**: P4
**First documented in**: not in prose. v1b1 code only.

**Recognized form**: Backend ABCs that some — but not all — implementations support are defined as separate `Has...` or `Can...` mixin classes. Concrete backends explicitly inherit them. The Capability frontend checks `isinstance(backend, MixinABC)` before calling the optional method.

**Evidence citations**:

- `pylabrobot/ufactory/xarm6/backend.py:16` — `class XArm6ArmBackend(ArticulatedGripperArmBackend, HasJoints, CanFreedrive)`. Explicit opt-in.
- `pylabrobot/ufactory/xarm6/backend.py:227-293` — `move_to_joint_position`, `request_joint_position`, `pick_up_at_joint_position`, `drop_at_joint_position` (HasJoints methods); `start_freedrive_mode`, `stop_freedrive_mode` (CanFreedrive methods).
- Mixin ABCs imported from `pylabrobot.capabilities.arms.backend` — `HasJoints`, `CanFreedrive`.
- `pylabrobot/qinstruments/bioshake.py:141` — `class BioShakeShakerBackend(ShakerBackend, HasContinuousShaking)`. Mixin ABC imported from `pylabrobot.capabilities.shaking.backend`.

**Fix when violated**: If a backend is implementing methods that exist as a mixin ABC, the backend should explicitly inherit the mixin so the Capability's `isinstance` check resolves correctly.

**Anti-pattern fixture**: `tests/anti-patterns/A-06_backend_implements_mixin_without_opt_in.py` — `ACMEShakerBackend(ShakerBackend)` defines `start_shaking` and `stop_shaking` (matching the `HasContinuousShaking` interface) without inheriting `HasContinuousShaking`. The Capability's `isinstance` check fails; the optional capability is invisible to the framework.

---

### P-16 — Device-specific helper subsystems

**Source**: code (with explicit "STARCover pattern" docstring reference)
**Principle**: P3 (these are localities-without-an-ABC; promote when a second device needs the same operation)
**First documented in**: not in prose. Acknowledged by Rick in code comments and Discord.

**Recognized form**: Plain class (not a `CapabilityBackend`), attached to the `Driver` as a public attribute, with `_on_setup` / `_on_stop` lifecycle hooks. Provides user-facing operations through Device convenience methods.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/nimbus/door.py:18-56` — `class NimbusDoor`. Class docstring: *"Plain helper class (not a CapabilityBackend), following the STARCover pattern."* Has `_on_setup` (lock door if available) and `_on_stop` (no-op). Methods: `is_locked`, `lock`, `unlock`.
- `pylabrobot/hamilton/liquid_handlers/star/cover.py:14-78` — `class STARCover`. Docstring: *"plain helper class (not a CapabilityBackend)."* `_on_setup` / `_on_stop` are no-ops. Methods: `lock`, `unlock`, `disable`, `enable`, `set_output`, `reset_output`, `is_open`.
- `pylabrobot/hamilton/liquid_handlers/star/wash_station.py:15-136` — `class STARWashStation`. Same docstring. Methods: `request_settings`, `initialize_valves`, `fill_chamber`, `drain`. Includes nested enum `Type`.
- `pylabrobot/hamilton/liquid_handlers/star/x_arm.py:14-216` — `class STARXArm`. Same docstring. Methods: `move_to`, `move_to_safe`, `request_position`, `last_collision_type`, `clld_probe_x_position`. `__init__` takes a `side: Literal["left", "right"]` so the SAME class is instantiated twice on the same driver (`driver.left_x_arm`, `driver.right_x_arm`) — multi-instance helper.
- `pylabrobot/hamilton/liquid_handlers/star/autoload.py:17-666` — `class STARAutoload`. Same docstring. Has a non-trivial `_on_setup` that checks initialization status, runs the `II` command if not initialized, and parks. Methods include barcode reading, carrier loading, LED control, `verify_and_wait_for_carriers` (interactive prompt with LED flashing).
- Helper instances live as Driver attributes (`driver.cover`, `driver.left_x_arm`, `driver.right_x_arm`, `driver.wash_station`, `driver.autoload`, `driver.door` on Nimbus), conditionally created during `setup()` based on discovery (P-18).
- Device convenience methods at `pylabrobot/hamilton/liquid_handlers/nimbus/nimbus.py:75-91` — `Nimbus.lock_door`, `Nimbus.unlock_door`, `Nimbus.is_door_locked` delegate to `self.driver.door.lock()` etc.

**Registration of helper lifecycle** (multi-form pattern, all verified at `d3c6d0a5`):

- **STAR** uses a `@property _subsystems` returning a computed list at `pylabrobot/hamilton/liquid_handlers/star/driver.py:321-336`. Returns `[self.cover]` plus optional left/right x_arm and wash_station. Importantly, the property *deliberately excludes* PIP, Head96, iSWAP, and autoload — their lifecycle is managed at the *Device* layer (`_HamiltonSTAR.setup`) so they can run in parallel and receive Device-level context (deck). The driver walks `for sub in self._subsystems: await sub._on_setup()` and `for sub in reversed(self._subsystems): await sub._on_stop()`.
- **Nimbus** has no `_subsystems` list. The single helper (`NimbusDoor`) is on `driver.door` and lifecycle is invoked inline in `NimbusDriver.setup` and `NimbusDriver.stop`.
- **The hybrid case (STAR autoload)**: a helper attached to the driver but whose lifecycle is invoked from the Device, so it can run `await asyncio.gather(setup_autoload(), setup_arm_modules())` for parallelism. Documented in the comment at `star/driver.py:321-328`.

**Inconsistency note (Backend suffix)** — confirmed at `d3c6d0a5`: `STARCover`, `STARWashStation`, `STARXArm`, `STARAutoload`, and `NimbusDoor` ALL lack the `Backend` suffix. Rick's "oversight" acknowledgment for `STARCover` (per project memory) has not been applied to v1b1 code at this commit. The skill accepts unsuffixed names on existing helpers as legacy precedent but recommends `<Vendor><Helper>Backend` (e.g., `STARCoverBackend`, `NimbusDoorBackend`) for new code.

**Inconsistency note (registration)**: STAR uses a `@property _subsystems` (computed list); Nimbus has no list and invokes inline. Both forms accepted. The skill enforces only that helpers have lifecycle invoked *somewhere* — driver-level walk, Device-level invocation, or inline.

**Anti-pattern fixture**: `tests/anti-patterns/A-07_helper_without_lifecycle_hooks.py` — `ACMECover` is attached to `ACMEDriver` and registered in `_subsystems`, but lacks `_on_setup` and `_on_stop`. The driver's lifecycle walk fails (`AttributeError`) or silently skips initialization. Both modes are unacceptable — helpers must declare lifecycle hooks even when they're no-ops.

---

### P-17 — Multi-instance / runtime-assembled capabilities

**Source**: code
**Principle**: — (not in Rick's prose; pattern observed only in v1b1 code)
**First documented in**: not in prose. v1b1 code only.

**Recognized forms** (any one is valid):

- **Multi-instance helper class**: the same helper class instantiated twice on the same driver, distinguished by an `__init__` parameter. Verified at `pylabrobot/hamilton/liquid_handlers/star/x_arm.py:25` — `STARXArm.__init__(driver, side: Literal["left", "right"])` is constructed twice in `STARDriver.setup` (`star/driver.py:304-308`) as `driver.left_x_arm` and `driver.right_x_arm`.
- **Multi-instance Capability with separate backends**: two `Capability` instances on the same Device, each with its own backend constructed with a distinguishing parameter. Verified at `pylabrobot/opentrons/ot2/ot2.py:31-46` (branch `upstream/ot2-capability-migration-v2`, commit `2e619167`) — `OpentronsOT2.__init__` constructs `OpentronsOT2PIPBackend(driver, mount="left")` and `OpentronsOT2PIPBackend(driver, mount="right")`, then exposes them as `self.left = PIP(backend=...)` and `self.right = PIP(backend=...)`. Both wired into `_capabilities = [self.left, self.right]`. The driver is shared.
- **Runtime-assembled capability via context manager**: a transient backend constructed inside an `@asynccontextmanager` on the Device, yielded as a Capability scoped to the context. Verified at `pylabrobot/hamilton/liquid_handlers/star/star.py:81-136` (`_HamiltonSTAR.core_grippers`). On enter, the Device picks up gripper tools via the driver and constructs `CoreGripper(driver=self.driver)` plus a `GripperArm(backend=backend, reference_resource=self.deck, grip_axis="y")` capability frontend. On exit, the gripper tools are returned. The `CoreGripper` backend itself is at `pylabrobot/hamilton/liquid_handlers/star/core.py:15-99`.

**Note**: A potential third "adapter" form (a thin wrapper around a shared backend with a distinguishing parameter, like `EVOArmAdapter(backend, arm_id=0)`) is pending verification — Tecan EVO is not on local branches at this audit.

**Anti-pattern fixture**: pending.

---

### P-18 — Runtime configuration discovery

**Source**: code
**Principle**: P5
**First documented in**: not in prose. v1b1 code only.

**Recognized form**: When a device's hardware varies at runtime, the Driver discovers in `setup()` (introspection / firmware queries / SDK enumeration), then conditionally wires capabilities and helpers based on what was discovered. The Device class does not assume hardware that isn't there.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:61-101` — `NimbusDriver.setup` calls `await super().setup()` (TCP + protocol init), then `_discover_instrument_objects()` (introspection), extracts `pipette_address` and `door_address`, queries channel configuration via `GetChannelConfiguration_1`, conditionally constructs `NimbusPIPBackend` (always) and `NimbusDoor` (only if `door_address` is not None).
- `pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:103-138` — `_discover_instrument_objects` walks the introspection subobject tree.
- `pylabrobot/hamilton/liquid_handlers/star/driver.py:268-319` — `STARDriver.setup` calls `_request_machine_configuration` (firmware command `RM`) and `_request_extended_configuration` (firmware command `QM`), populating typed `MachineConfiguration` and `ExtendedConfiguration` dataclasses (defined in the same file, lines 35-110). Then conditionally creates: `STARPIPBackend` (always), `STARHead96Backend` (if `core_96_head_installed`), `iSWAPBackend` (if `iswap_installed`), `STARAutoload` (if `auto_load_installed`), `STARXArm` left (always) and right (if `right_x_drive_large`), `STARCover` (always), `STARWashStation` (if either wash station installed). Strongest discovery precedent on v1b1.

**Fix when violated**: A Device that hardcodes which backend to construct (without checking the actual hardware) breaks when the unit configuration differs. Move construction into `setup()` after discovery.

**Anti-pattern fixture**: pending (planned A-NN).

**Note on weaker forms**: BioShake uses constructor flags (`has_shaking`, `has_temperature`, `supports_active_cooling`) instead of runtime discovery — equivalent to a per-unit "device card" supplied by the user. Both forms are acceptable; runtime discovery is preferred when the protocol supports it.

---

### P-19 — Shared state on the driver

**Source**: code
**Principle**: P6 (state shared across multiple capabilities/backends belongs on the driver, not duplicated in each backend)
**First documented in**: not in prose. v1b1 code only.

**Recognized form**: The driver holds state populated during `setup()` (typically discovery results) that multiple backends and helpers read from. Backends do not duplicate or re-discover this state.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/star/driver.py:148-159` (v1b1, `d3c6d0a5`) — `STARDriver` declares `machine_conf`, `extended_conf`, `_channels_minimum_y_spacing` as instance attributes populated during `setup()`. These are read by `STARPIPBackend`, `STARHead96Backend`, `iSWAPBackend`, and helpers (`STARXArm.clld_probe_x_position` reads `extended_conf.instrument_size_slots` at `x_arm.py:167-168`).
- `pylabrobot/hamilton/liquid_handlers/star/driver.py:1071-1144` (v1b1, `d3c6d0a5`) — `STARDriver.channel_request_y_minimum_spacing`, `channels_request_y_minimum_spacing`, `_min_spacing_between` are driver methods that read the shared `_channels_minimum_y_spacing` list.
- `pylabrobot/opentrons/ot2/driver.py:51-58` (branch `upstream/ot2-capability-migration-v2`, commit `2e619167`) — `OpentronsOT2Driver` declares `_tip_racks: Dict[str, int]` and `_plr_name_to_load_name: Dict[str, str]` as the canonical shared-state registry on the driver. Cleared on stop.
- `pylabrobot/opentrons/ot2/driver.py:84-93` (same ref) — `get_ot_name(plr_resource_name) -> str` and `assign_tip_rack(tip_rack, tip)` are public driver methods that read/write the shared registry. Backends call these to register tip racks once, regardless of which mount picks up tips.

**Anti-pattern fixture**: pending.

---

### P-20 — Workflow methods sequencing vendor calls belong on the backend

**Source**: code
**Principle**: P6
**First documented in**: not in prose explicitly; consistent with the prose's "driver is the wire" rule.

**Recognized form**: When a single user-level operation requires sequencing multiple vendor commands or branching on operation kind (e.g., trash drop vs return-to-rack), that sequencing logic lives in the backend method, not in the driver. Driver methods are 1-to-1 with vendor endpoints when private (underscore-prefixed); public driver methods are transport-only.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/nimbus/pip_backend.py:455-568` — `NimbusPIPBackend.drop_tips` decides between `DropTips` (return to rack) and `DropTipsRoll` (trash) based on whether `op.resource` is a `Trash`. Both code paths build full firmware payloads and call `self.driver.send_command(command)`. The driver does not branch.

**Fix when violated**: Move the sequencing into the corresponding backend method. Driver retains 1:1 wire methods (private, underscore-prefixed when accepting typed parameters); the backend calls them in the right order.

**Anti-pattern fixture**: `tests/anti-patterns/A-08_workflow_method_on_driver.py` — `ACMEFlexDriver.drop_tip_in_trash` sequences `_move_to_addressable_area` + `_drop_tip_in_place(alternate_drop_location=True)` on the driver. The `alternate_drop_location` decision encodes domain meaning (trash vs rack). Both belong on the backend's `drop_tips` method. The fixture also plants `request_tip_presence` parsing `state.tipDetected` out of an `/instruments` response — same anti-pattern, semantic parsing on the driver.

---

### P-21 — Driver-internal protocol organization is free choice

**Source**: code
**Principle**: — (this is an explicit non-rule)
**First documented in**: not in prose explicitly. Three coexisting precedents in v1b1 establish the freedom.

**Recognized forms** (any one is valid):

- **Command classes**: Driver uses `send_command(command_object)` where command objects encapsulate wire format. Verified at `pylabrobot/hamilton/liquid_handlers/nimbus/commands.py` (Aspirate, Dispense, PickupTips, DropTips, etc.).
- **Inline string commands**: Driver uses `send_command(cmd: str)` and backends build the string inline. Verified at `pylabrobot/qinstruments/bioshake.py:54-85` (`BioShakeDriver.send_command`).
- **Module + command + kwargs**: Driver uses `send_command(module=..., command=..., **fw_params)` where the firmware module ID and command code are separate from named parameters. Verified at `pylabrobot/hamilton/liquid_handlers/star/driver.py` and inherited from `HamiltonLiquidHandler`. Backends (e.g., `STARCover.lock` at `cover.py:34-36`) build inline calls like `await self.driver.send_command(module="C0", command="CO")`.
- **SDK wrapper**: Driver wraps a vendor SDK behind a `_call_sdk(func, ..., op="...")` helper. Verified at `pylabrobot/ufactory/xarm6/driver.py:50-86` (`XArm6Driver._call_sdk`).

**The skill does not enforce a specific internal organization.** It only enforces that the driver's *public surface* is generic transport, not domain methods (P-01).

---

### P-22 — `BackendParams` for typed vendor parameters

**Source**: code
**Principle**: P2
**First documented in**: not in prose explicitly. Multiple shapes coexist on v1b1.

**Recognized forms** (multi-form pattern):

- **Nested in backend class**: `XArm6ArmBackend.CartesianMoveParams`, `XArm6ArmBackend.JointMoveParams` (`pylabrobot/ufactory/xarm6/backend.py:45-69`); `CoreGripper.PickUpParams` (`pylabrobot/hamilton/liquid_handlers/star/core.py:32-51`).
- **Nested in driver class**: `XArm6Driver.SetupParams`, `BioShakeDriver.SetupParams` (`pylabrobot/ufactory/xarm6/driver.py:89-97`, `pylabrobot/qinstruments/bioshake.py:87-95`).
- **Module-level**: `NimbusPIPPickUpTipsParams`, `NimbusPIPDropTipsParams`, `NimbusPIPAspirateParams`, `NimbusPIPDispenseParams` (`pylabrobot/hamilton/liquid_handlers/nimbus/pip_backend.py:64-114`); `TecanInfiniteAbsorbanceParams`, `TecanInfiniteFluorescenceParams`, `TecanInfiniteLuminescenceParams` (`pylabrobot/tecan/infinite/absorbance_backend.py:23-34` and sibling files). Both Hamilton Nimbus and Tecan Infinite plate readers prefer the module-level shape over the nested shape used by xArm6 / STAR `CoreGripper`.

All three forms inherit `BackendParams` from `pylabrobot.capabilities.capability`. Capability methods accept `backend_params: Optional[BackendParams] = None`; the backend's coercion helper (e.g., `_cart_params`) checks `isinstance` and applies defaults.

**Inconsistency note**: The location is the inconsistency. The skill does not enforce a specific location — nested or module-level both work — but flags backends that accept untyped `**kwargs` instead of a typed `BackendParams` subclass.

---

### P-23 — Resource integration via multiple inheritance

**Source**: code
**Principle**: —
**First documented in**: not in prose explicitly.

**Recognized form**: Devices that physically hold a resource (a plate, a tip rack) inherit from both `Device` and the appropriate Resource type, calling each `__init__` separately.

**Evidence citations**:

- `pylabrobot/qinstruments/bioshake.py:278` — `class BioShake(PlateHolder, Device)`. `__init__` calls `PlateHolder.__init__(self, name=..., ...)` and `Device.__init__(self, driver=driver)` separately. Custom `serialize` merges both representations.
- `pylabrobot/ufactory/xarm6/xarm6.py:8` — `class XArm6(Device)` (no resource holder; arm holds nothing). The capability accepts a `reference_resource: Resource` argument for spatial context.
- `pylabrobot/tecan/infinite/infinite.py:19-78` — `class TecanInfinite200Pro(Resource, Device, HasLoadingTray)`. Triple inheritance: Resource + Device + Device-attribute marker mixin (P-26). `__init__` calls `Resource.__init__` (with name/dimensions/model/category) and `Device.__init__` (with driver) separately. The `LoadingTray` capability is itself a Resource (instantiated with `name`, `size_x`, `size_y`, `size_z`, `child_location`) and is `assign_child_resource`'d onto the device. Custom `serialize` merges Resource and Device serialization.

**Note on Capability + ResourceHolder**: Tecan Infinite confirms the spec's claim that `LoadingTray` is `Capability + ResourceHolder` — the `LoadingTray` constructor accepts Resource fields (name, size, child_location) and is treated as a child resource of the Device.

---

### P-24 — Concurrency primitives are device-author's choice

**Source**: code
**Principle**: — (this is an explicit non-rule)
**First documented in**: not in prose explicitly.

**Recognized form**: Device authors choose what concurrency primitives are appropriate for their protocol. The skill does not enforce a specific shape. Locks, semaphores, daemon threads, and per-channel coordination are all valid when the protocol justifies them.

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/star/pip_backend.py:44-75` — `_FirmwareLock` coordinates `Px` (per-channel) commands and `C0` (master) commands. Multiple `Px` commands can run in parallel; `C0` requires exclusive access. Backend-internal concurrency primitive, named and documented.
- `pylabrobot/hamilton/liquid_handlers/star/pip_backend.py:5` — uses `asyncio.Lock` and `asynccontextmanager` from stdlib.
- `pylabrobot/tecan/infinite/driver.py:75` — `TecanInfiniteDriver._setup_lock = asyncio.Lock()`. The `setup()` and `stop()` methods are wrapped in `async with self._setup_lock:` so concurrent setups are serialized and idempotent. Driver-level concurrency primitive.

**Note**: Background reader threads, polling loops, and `STARConnection.lock` are additional shapes that appear in v1b1 device code. The skill does not enforce or forbid any of them; it only flags the absence of necessary coordination if a backend's concurrent access pattern is obviously broken (which is hard to detect statically and is treated as a soft warning, not a hard rule).

---

### P-25 — Lifecycle hook scope (driver setup opens connection; backend `_on_setup` does hardware-specific init)

**Source**: prose+code
**Principle**: P6
**First documented in**: `creating-capabilities.md` "Backend `_on_setup` / `_on_stop`" section.

**Recognized form**:

- `Driver.setup` opens the connection, performs device-level initialization that doesn't belong to any capability (reset, home), and runs hardware *discovery*.
- `CapabilityBackend._on_setup` performs capability-specific initialization that requires the connection to be open (configure objectives, initialize SmartRoll, query channel configuration).

**Evidence citations**:

- `pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:61-95` — `NimbusDriver.setup`: TCP connection (super), discovery, backend creation. Capability-specific work (SmartRoll init) lives in `NimbusPIPBackend._on_setup`.
- `pylabrobot/hamilton/liquid_handlers/nimbus/pip_backend.py:154-205` — `NimbusPIPBackend._on_setup` runs `_initialize_smart_roll` if not already initialized. This is the textbook "post-connection init" pattern.
- `pylabrobot/qinstruments/bioshake.py:97-110` — `BioShakeDriver.setup` does `await self.io.setup()` then optionally `reset()` and `home()`. The reset/home are device-level (no capability ownership), so they live on the driver. The `skip_home` SetupParam allows the user to defer.
- `pylabrobot/hamilton/liquid_handlers/star/head96_backend.py:71-97` — `STARHead96Backend._on_setup` checks initialization status, runs `initialize` if needed, caches firmware version. `_on_stop` performs **safety shutdown**: `move_to_z_safety` then `park`, each in a try/except so a failure of one doesn't block the other. This is the canonical "safety shutdown in `_on_stop`" pattern from `creating-capabilities.md` Lifecycle section, in production form.
- `pylabrobot/hamilton/liquid_handlers/star/iswap.py:90-101` — `iSWAPBackend._on_setup` checks initialization status, runs `initialize` + `park` if needed, caches firmware version. Same shape as Head96.
- `pylabrobot/hamilton/liquid_handlers/star/autoload.py:58-66` — `STARAutoload._on_setup` checks status, runs the `II` initialization command if needed, parks. `_on_stop` is no-op (no specific safety shutdown needed for the autoload subsystem).

**Inconsistency note**: xArm6's `XArm6Driver.setup` performs gripper init (`set_gripper_mode`, `set_gripper_enable`) inside the driver, with a `skip_gripper_init: bool` escape hatch. Borderline — gripper is the arm capability's hardware. The skill flags this as a soft warning (informational) rather than a hard violation; the `skip_*` parameter is the documented bypass.

---

### P-26 — Device-attribute marker mixin (`Has<Capability>` on the Device class)

**Source**: code
**Principle**: — (this is a class-organization pattern, not a behavior rule)
**First documented in**: not in prose. v1b1 code only. File-naming convention: `has_{name}.py` → `Has<Name>`.

**Recognized form**: A capability package may export a third class alongside the frontend and the Backend ABC: a Device-attribute marker mixin named `Has<Capability>` that is mixed into the Device class. The mixin has no methods (or a small marker interface); it signals at the type level that the Device has a `<capability>` attribute.

**Evidence citations**:

- `pylabrobot/tecan/infinite/infinite.py:5-19` (v1b1, `d3c6d0a5`) — `from pylabrobot.capabilities.loading_tray import HasLoadingTray, LoadingTray`. `class TecanInfinite200Pro(Resource, Device, HasLoadingTray)`. The `HasLoadingTray` mixin is co-located with the `LoadingTray` capability in the `loading_tray` package.
- `pylabrobot/capabilities/loading_tray/has_loading_tray.py` — the marker mixin file. Naming convention: `has_<name>.py` → `Has<Name>`.

**This is NOT the same as a Capability-frontend mixin** (e.g., a hypothetical `class SomeCapability(Capability, SomeMixin)`). `HasLoadingTray` is mixed into the *Device* class, not the *Capability frontend*. Capability-frontend mixins are not observed on v1b1 (audit-task A-07 conclusion).

**This is NOT the same as a Backend mixin** (e.g., `HasJoints`, `CanFreedrive`). Backend mixins are ABCs that the *backend* class explicitly inherits to opt into optional methods. Device-attribute marker mixins are simpler markers on the Device class.

**Three mixin tiers exist on v1b1**:

| Mixin tier | Where mixed in | Purpose | Examples |
|---|---|---|---|
| Backend mixin (P-14) | Concrete `<Capability>Backend` | Opt-in to optional methods on the backend | `HasJoints`, `CanFreedrive`, `HasContinuousShaking`, `CanGrip` |
| Device-attribute marker mixin (P-26) | Device class | Type-level signal that the device has a capability attribute | `HasLoadingTray` |
| Capability-frontend mixin | `<Capability>` frontend class | (would add optional user-facing methods on the Capability) | NONE on v1b1 |

**Anti-pattern fixture**: pending.

---

### P-27 — `Driver.setup` signature convention (`backend_params: Optional[BackendParams] = None` + nested `SetupParams`)

**Source**: code
**Principle**: P6 — Driver is the wire, backend is the protocol
**First documented in**: not in prose. v1b1 code only. Surfaced during the PR #1009 (Micronic Code Reader) skill run on 2026-04-25 — the contributor's signature looked unusual but verification at `d3c6d0a5` showed it is the dominant convention.

**Recognized forms** (any one is valid):

- **Lighter form (no params)**: `async def setup(self) -> None`. Used when the driver's setup needs no caller-supplied configuration.
- **Standard form (with SetupParams)**: `async def setup(self, backend_params: Optional[BackendParams] = None) -> None`, where the driver subclass defines a nested `class SetupParams(BackendParams)` dataclass and the body isinstance-checks the parameter, falling back to `<Driver>.SetupParams()` if missing or wrong type.

The `BackendParams` type on the parameter is the base class re-exported from `pylabrobot.capabilities.capability`; the actual contract is "isinstance check for the driver's nested `SetupParams` and substitute defaults if not". The parameter name `backend_params` is consistent across v1b1 even though the receiver is the driver, not a backend — it's the same `BackendParams` lineage `CapabilityBackend._on_setup` uses.

**Evidence citations** (verified at `d3c6d0a5`):

- `pylabrobot/qinstruments/bioshake.py:88,97-110` — `BioShakeDriver.SetupParams(BackendParams)` with `skip_home: bool`. `setup(self, backend_params: Optional[BackendParams] = None)` isinstance-checks and substitutes `BioShakeDriver.SetupParams()` if needed; reads `backend_params.skip_home` to decide whether to home.
- `pylabrobot/ufactory/xarm6/driver.py:90,112-129` — `XArm6Driver.SetupParams(BackendParams)` with `skip_gripper_init: bool`. Same shape — isinstance-check + default substitution.
- `pylabrobot/hamilton/liquid_handlers/star/driver.py:268-270` — `STARDriver.setup(self, backend_params: Optional[BackendParams] = None)` and forwards via `await super().setup(backend_params=backend_params)`. Inherits from `HamiltonLiquidHandler`.
- `pylabrobot/hamilton/liquid_handlers/nimbus/driver.py:61` — `NimbusDriver.setup(self)` (lighter form, no params).

**Anti-pattern signature**: `Driver.setup` signature that uses an entirely different parameter name (e.g., `setup_options`, `config`) or accepts arbitrary `**kwargs` for setup configuration instead of the `BackendParams`-typed parameter, when caller-supplied configuration is needed. Pure-no-params (`async def setup(self) -> None`) is also acceptable and should NOT be flagged.

**Fix when violated**: Either drop to the lighter form (`async def setup(self) -> None`) if no caller config is needed, or define a nested `<Driver>.SetupParams(BackendParams)` dataclass with the typed fields and rename the parameter to `backend_params: Optional[BackendParams] = None`, isinstance-checking inside the body.

**Inconsistency note**: `BackendParams` originates in the Capability layer (`pylabrobot.capabilities.capability`) but is re-used as the base for driver-side `SetupParams`. The naming asymmetry — `backend_params` on a Driver method — is the v1b1 status quo and should not be "corrected" to `setup_params`. If Rick later renames the base type or splits it into `DriverSetupParams` / `BackendParams`, this pattern entry needs revision.

**Anti-pattern fixture**: pending.

**Audit trail addition**: Surfaced during PR #1009 (Micronic Code Reader) skill run, 2026-04-25; verified across BioShake, xArm6, STAR, Nimbus at `d3c6d0a5`.

---

## Inconsistencies and Resolutions

### `Backend` suffix on subsystem helpers

**Conflict**: STAR's four helpers (`STARCover`, `STARWashStation`, `STARXArm`, `STARAutoload`) and Nimbus's helper (`NimbusDoor`) all lack the `Backend` suffix at v1b1 commit `d3c6d0a5`. Each helper class explicitly documents itself as "plain helper class (not a CapabilityBackend)" in its docstring. Rick acknowledged this for `STARCover` as a "simple oversight" (per project memory; specific Discord pointer pending), but the correction has not been applied to v1b1 code at this commit — neither for `STARCover` nor for the four other helpers that follow the same pattern.

**Chosen** (for new code): `<Vendor><Helper>Backend` (e.g., `STARCoverBackend`, `NimbusDoorBackend`).
**Rejected** (legacy precedent, not recommended for new code): `<Vendor><Helper>` without suffix.
**Affected patterns**: P-09 naming, P-16 device-specific helpers.

### `BackendParams` location

**Conflict**: Three shapes coexist — nested in backend (xArm6), nested in driver (xArm6 SetupParams, BioShake SetupParams), module-level (Nimbus PIP).

**Chosen**: All three forms are accepted. The skill does not flag location.
**Rejected**: untyped `**kwargs` on capability methods (no `BackendParams` subclass at all).
**Affected patterns**: P-22.

### Chatterbox layer

**Conflict**: Rick's prose says chatterbox extends `CapabilityBackend`. Nimbus's `NimbusChatterboxDriver` extends `NimbusDriver` (the Driver).

**Chosen**: When a driver does runtime discovery (P-18), `*ChatterboxDriver` (extends Driver) is the documented exception. For drivers without discovery, the prose pattern (`*ChatterboxBackend`) applies.
**Rejected**: chatterbox classes that mix `Driver` and `CapabilityBackend` inheritance (anti-pattern A-04).
**Affected patterns**: P-04.

### `_subsystems` registration

**Conflict**: STAR (verified at `d3c6d0a5`, `pylabrobot/hamilton/liquid_handlers/star/driver.py:321-336`) uses a **`@property`** that returns a computed list `[self.cover]` plus optional left/right x_arm and wash_station. The driver walks the property in `setup()` and `stop()`. Nimbus does not have a `_subsystems` list at all — the single helper (`NimbusDoor`) is on `driver.door` and lifecycle is invoked inline. STAR also has a documented hybrid: `STARAutoload` is on the driver but its lifecycle is invoked from the *Device* layer (not from `_subsystems`) so it can run in parallel with the arm modules' setup.

**Chosen**: All three forms accepted. A `@property _subsystems` is recommended for drivers with ≥2 helpers whose `_on_setup`/`_on_stop` is independent. Drivers with a single helper or with helpers that need Device-level context (deck, parallelism with capabilities) can invoke lifecycle inline or from the Device layer.
**Rejected**: helpers without lifecycle invocation at all (no `_on_setup` / `_on_stop` calls anywhere).
**Affected patterns**: P-16.

### `supports_X` flags coexist with mixin ABCs

**Conflict**: BioShake's `BioShakeShakerBackend` defines both `HasContinuousShaking` (mixin opt-in) AND `supports_locking: bool = True` (legacy flag). Both patterns coexist on v1b1.

**Chosen**: Mixin ABCs (P-14) are preferred for new code. The skill does not flag legacy `supports_X` flags on existing devices but recommends mixin replacement.
**Affected patterns**: P-14.

### Backend driver-attribute name (`self.driver` vs `self._driver`)

**Conflict**: Prose example uses `self._driver = driver`. Code uses `self.driver = driver` (BioShake, Nimbus) AND `self._driver = driver` (xArm6).

**Chosen**: The skill enforces that the backend stores SOME driver reference under `driver` or `_driver`. It does not enforce the underscore.
**Affected patterns**: P-05.

### ABC class-name qualifiers

**Conflict**: Most ABCs use `<Name>Backend` (`ShakerBackend`, `PIPBackend`). `ArticulatedGripperArmBackend` includes a shape qualifier (`Gripper`).

**Chosen**: Qualifiers in ABC names are accepted when a single capability has multiple physical forms (gripper vs no-gripper).
**Affected patterns**: P-11.

### Capability-level mixins (audit-task A-07) — RESOLVED

**Status**: **Capability-frontend mixins are NOT observed on v1b1.** Verified across xArm6, BioShake, Nimbus, STAR (PIP, Head96, iSWAP), Tecan Infinite (Absorbance, Fluorescence, Luminescence, LoadingTray), and Opentrons OT2 (PIP × 2). All backends inherit only the main ABC plus optional Backend mixins (`HasJoints`, `CanFreedrive`, `HasContinuousShaking`); no Capability *frontend* class on v1b1 has a mixin.

The closest pattern observed is the **Device-attribute marker mixin** (`HasLoadingTray`), which is mixed into the *Device* class, not the Capability frontend. Documented as P-26.

Capability-frontend mixins are not observed on v1b1 and do not appear in skill output.

### `OrientableGripperArmBackend` qualifier

**Conflict** (already noted in P-11): `OrientableGripperArmBackend` (iSWAP's ABC) and `ArticulatedGripperArmBackend` (xArm6's ABC) both carry shape qualifiers (`Orientable`, `Articulated`, `Gripper`). Capability frontends are `OrientableArm` and `ArticulatedArm` (no `Gripper` qualifier). This is consistent across both arm devices.

**Chosen**: ABC-level qualifiers in arm backends are accepted; the matching frontend can omit the `Gripper` qualifier when the arm class is gripper-specific.
**Affected patterns**: P-11.

---

## Audit Trail

Append-only log of audit runs.

### Initial archaeology slice 1 — 2026-04-25 (xArm6 + BioShake + Nimbus)

- Target branch: `v1b1`
- Verified against: `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa`
- Audit procedure version: 1.0
- Patterns populated: 18 / 26 (P-01..P-14, P-16, P-18, P-20, P-21, P-22, P-23, P-25)
- Patterns deferred: 8 (P-15, P-17, P-19, P-26, plus three pending fixtures and refinement of inconsistencies)
- Vendored prose drift: none (SHA-256 `3767edbf...` matches v1b1 root)
- Smoke corpus: not yet run (no fixtures bundled — Echo PR #1001 deferred to next slice)
- Anti-pattern corpus: 5 / ~15 fixtures bundled (A-01..A-05); not yet run
- Vocabulary leak: not yet run
- Released: skill version PRE-RELEASE (no version tag yet)
- Notes: This is the first archaeology slice. STAR, Tecan EVO, Tecan Infinite, Opentrons OT2, Echo (#1001) remain. The next slice resolves the `STARCover` Backend-suffix question against actual STAR code and adds P-15 (internal `_method` pattern), P-17 (multi-instance adapter), P-19 (shared state on driver).

### Archaeology slice 2 — 2026-04-25 (STAR)

- Target branch: `v1b1`
- Verified against: `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa` (unchanged)
- Audit procedure version: 1.0
- Patterns added: 3 new (P-17 multi-instance / runtime-assembled, P-19 shared state on driver, P-24 concurrency primitives)
- Patterns refined with STAR evidence: P-04 (chatterbox-driver pattern confirmed on STAR — second precedent), P-13 (3-capability shared driver — strongest precedent), P-16 (4 helpers attached to driver, all unsuffixed; `@property _subsystems` confirmed; hybrid autoload lifecycle pattern documented), P-18 (RM/QM discovery dataclasses — strongest precedent), P-21 (module + command + kwargs as a fourth recognized form), P-22 (`CoreGripper.PickUpParams` adds nested-in-backend evidence), P-25 (Head96 `_on_stop` safety shutdown — canonical example of safety-on-stop)
- Patterns populated total: 21 / 26 (added P-17, P-19, P-24)
- Patterns deferred: P-15 (likely surfaces in Shaking/Heating backends, not in liquid handling — defer to slice 3 or omit), P-26 (Capability-level mixins — none observed across xArm6+BioShake+Nimbus+STAR, increasing confidence this stays out of the skill's emitted shapes)
- Inconsistencies refined: Backend suffix on helpers — confirmed across STAR's four helpers; `_subsystems` registration — STAR uses `@property`, Nimbus uses inline, hybrid case (autoload) added; new entry — `OrientableGripperArmBackend` / `ArticulatedGripperArmBackend` qualifier consistency.
- Vendored prose drift: none (no re-verification needed since slice 1)
- Smoke corpus: not yet run
- Anti-pattern corpus: 5 / ~15 fixtures bundled; not yet run
- Vocabulary leak: not yet run
- Released: skill version PRE-RELEASE (no version tag yet)
- Notes: Slice 2 confirms slice 1's calls and extends. STAR is the largest device on v1b1 (driver alone is 1145 lines), and its patterns set the baseline for the inconsistency-resolution rule. Remaining slices: Tecan EVO (RoMa adapter, internalities), Tecan Infinite (LoadingTray + nested BackendParams), Opentrons OT2 (`_tip_racks` shared registry — completes P-19 evidence). Echo PR #1001 will become the smoke fixture S-01.

### Archaeology slice 3 — 2026-04-25 (Tecan Infinite + Opentrons OT2)

- Target branches: `v1b1` for Tecan Infinite (commit `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa`); `upstream/ot2-capability-migration-v2` for Opentrons OT2 (commit `2e6191674b33ebb69c43381f784e67ee6980913d`). Two distinct refs in this slice — every OT2 citation tagged with the OT2 branch commit.
- Audit procedure version: 1.0
- Patterns added: 1 new (P-26 Device-attribute marker mixin)
- Patterns refined: P-13 (Tecan Infinite — 4-capability shared driver, fullest precedent), P-15 (still pending — Tecan Infinite has internal underscore methods like `_configure_absorbance`, but they're internal organization not Capability-auto-triggered), P-17 (OT2 multi-mount adds a third multi-instance shape: separate-backends-with-distinguishing-param), P-19 (OT2 `_tip_racks` and `_plr_name_to_load_name` are the canonical shared-state precedent), P-22 (Tecan Infinite confirms module-level for plate readers — Nimbus + Infinite agree), P-23 (Tecan Infinite triple-inheritance Resource+Device+HasLoadingTray, plus `LoadingTray` as `Capability + Resource` confirmed), P-24 (Tecan Infinite `asyncio.Lock` for setup ordering — second precedent).
- Patterns populated total: 22 / 26 (added P-26)
- A-07 audit conclusion: **RESOLVED**. Capability-frontend mixins NOT observed on any v1b1 device or on the OT2 capability-migration branch. The Device-attribute marker mixin (P-26) is the closest pattern.
- Inconsistencies refined: `LoadingTray` Capability is itself a Resource (confirmed); `HasLoadingTray` Device-attribute marker mixin is a third mixin tier (Backend / Device-attribute / Capability-frontend; only the third is absent on v1b1).
- Devices NOT covered in this slice (deferred):
  - **Tecan EVO** — not on local branches at this audit. Spec-named as the RoMa-adapter and Internalities reference. Pattern P-15 (internal `_method` auto-triggered by Capability) and the formal "adapter wrapping shared backend" form of P-17 remain pending until the EVO PR (#982) is checked out or merged.
  - **Echo PR #1001** — not on local branches; PR unmerged. Cannot serve as smoke-test fixture S-01 from v1b1 alone. Smoke corpus selection will pick from v1b1-merged devices in the next pass — Tecan Infinite (this slice) and xArm6 (slice 1) are the leading candidates given they're recent and clean.
- Vendored prose drift: none.
- Smoke corpus: not yet run. Candidates promoted to S-01 / S-02 selection: Tecan Infinite + xArm6 (Echo deferred).
- Anti-pattern corpus: 5 / ~15 fixtures bundled; not yet run.
- Vocabulary leak: not yet run.
- Released: skill version PRE-RELEASE.
- Notes: Slice 3 closes the audit-task A-07 question (Capability-frontend mixins not observed) and adds the canonical OT2 shared-state precedent for P-19. Tecan EVO and Echo are punted to a future slice when the maintainer checks out those branches. The skill is now substantively v1.0-ready for liquid-handlers + plate-readers + arm + shaker domains; remaining gaps are in the helper anti-pattern fixtures (A-06+), the smoke corpus runs (T037–T039), and the principles-section authoring (US2 phase).

### Audit run 4 — 2026-04-25 (initial pre-release audit + Phase 8 design revisions + v1.0 tag)

- Target branch: `v1b1` at commit `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa` (no advancement needed since slice 3).
- Audit procedure version: 1.0
- Trigger: First field run on PyLabRobot PR #1009 (Micronic Code Reader by Alex Godfrey, head SHA `a41f59bf`) surfaced four contract / SKILL.md / reference.md gaps (PR-URL input form, Severity field, P-27 Driver.setup signature, multi-pattern findings + pre-emit structural lint). All four resolved as Phase 8 in `tasks.md`. Then ran the deferred validation tasks (T037, T038, T039, T043, T062, T063) under the new contract.
- Patterns added: 1 new (P-27 — `Driver.setup` signature convention; verified across BioShake, xArm6, STAR; lighter form on Nimbus).
- Patterns refined: none (existing patterns held under the new Severity rubric).
- Patterns populated total: 23 / 26 (added P-27).
- Inconsistencies refined: none new; existing P-04 chatterbox-extends-Driver discovery exception confirmed by S-02 Nimbus walk; P-16 unsuffixed-helper legacy precedent confirmed by S-02 walk.
- Vendored prose drift: none.
- Smoke corpus: PASS — S-01 BioShake (`pylabrobot/qinstruments/bioshake.py`) and S-02 Nimbus (`pylabrobot/hamilton/liquid_handlers/nimbus/`) both produce 0 findings. SC-001 satisfied.
- Anti-pattern corpus: PASS — A-01..A-08 (8/8) each produce exactly one Finding matching the planted `pattern_id` with the named principle. SC-002 + SC-007 satisfied. Severity assigned per Phase 8 rubric (A-01..A-05 hard; A-06..A-07 soft; A-08 hard).
- Vocabulary leak: PASS — zero hits for `Locality`, `Internality`, `Contract` (capitalized), `EYES/I4S`, `three-layer`, `Resource Trust`, `Signal` (capitalized noun), `Device Card` across all skill output produced by this audit and the prior PR #1009 run. SC-003 satisfied.
- Released: skill version v1.0.
- Outstanding for v1.1: T065 quickstart.md update (worked PR-mode example, Severity field display, pre-emit lint failure shape); T008 Tecan EVO archaeology when the branch lands; broader Step 2 citation walk (the v1.0 walk was a spot-check, not exhaustive).
- Notes: First end-to-end audit. The PR #1009 run produced both the v1.0 release readiness and the Phase 8 contract revisions in the same session. P-27 closed a real false-alarm (Micronic's `Driver.setup` signature looked unusual but was conventional). The new Severity field + pre-emit structural lint are now part of the contract; future audits run them as Step 4 (lint over each anti-pattern Finding's structure) and Step 5 (vocabulary grep, unchanged).

### Audit run 5 (SHARED) — 2026-04-25 (sibling `v1b1-author` v0.9-RC release readiness)

- audit_kind: shared (covers both `v1b1-capability` and `v1b1-author`)
- Target branch: `v1b1` at commit `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa` (no advancement since run 4).
- Audit procedure version: 1.0 (review skill) + 1.0 (authoring skill, `~/.claude/skills/v1b1-author/audit.md`).
- Trigger: Authoring skill v0.9-RC release readiness. Authoring skill walk per its `audit.md`; review skill steps 1, 2, 5 inherited from run 4 (no source-of-truth advancement).
- Patterns added: none.
- Patterns refined: none.
- Patterns populated total: 23 / 26 (unchanged).
- Vendored prose drift: none.
- Template parity (authoring skill, audit step 3): PASS — all 8 templates (`simple_single_file`, `driver`, `capability_backend`, `helper_subsystem`, `device`, `chatterbox`, `chatterbox_driver`, `package_init`) declare placeholders that match their bodies; reference pointers (BioShake, Nimbus driver/pip_backend/chatterbox/door, STARCover) all resolve in the local PLR mirror at the recorded commit.
- Smoke corpus (authoring skill, audit step 4): PASS — S-01 (ACME WidgetShaker, simple form) byte-for-byte identical to `tests/fixtures/S-01-expected/widget_shaker.py` per `mvp-validation-2026-04-25.md`; pre-emit lint stage 3 returns 0 Findings. S-02 (ACME MultiCap, complex form): T032 + T034 completed in-session — `tests/fixtures/S-02-expected/` authored (7 files matching the spec's `expected_files`); `v1b1-capability` review on the fixture returns 0 findings. Both forms validated end-to-end.
- Smoke corpus (review skill): PASS, inherited from run 4.
- Anti-pattern corpus (review skill, run 4 result): PASS, inherited.
- Vocabulary leak (audit step 5, SHARED): PASS — grep across `~/.claude/skills/v1b1-author/SKILL.md`, `decision-record-template.md`, `audit.md`, `templates/*.tmpl`, `tests/smoke/*.md`, and `tests/fixtures/S-01-expected/*.py` returns one quoted occurrence (the lockdown listing inside SKILL.md describing the pre-emit vocab self-check — a meta-mention, not a leak). Same shape as the review skill's own SKILL.md.
- Field-authoring run (toward SC-010): the maintainer ran `/v1b1-author Opentrons Flex` against a live working tree on 2026-04-25; scaffold rendered to `pylabrobot/opentrons/flex/` (6 files); decision record rendered alongside; pre-emit lint stage 3 (review skill called on the scaffold) returned 0 findings on first invocation. First real-world authoring session by the maintainer on a chosen target device — SC-010 graduation criterion satisfied in spirit; v1.0 graduation pending confirmation when the Flex protocol bodies are filled in and the scaffold's review-skill clean-pass holds across the implementation increment.
- Released:
  - `v1b1-capability`: v1.0 (no version bump in this audit run).
  - `v1b1-author`: v0.9-RC.
- Outstanding for v1.0 graduation of `v1b1-author`: T040 + T041 (US2 integration walks in fresh Claude Code sessions); confirmation that the Opentrons Flex protocol-implementation phase doesn't drift back into anti-patterns. T032 + T034 closed in this session.
- Notes: First SHARED audit-trail entry. The two skills now graduate together. The authoring skill's audit reuses three of the review skill's six steps (vendored prose, reference.md citations, vocabulary leak) by pointer — no duplication. The decision-record template's wrong-default callouts and the device template's three-callout `# CAUTION` block (T039 expanded the prior single-callout block to cover all three documented Echo/Micronic anti-patterns) are the discipline-carrying surfaces that resist anti-pattern drift in the protocol-implementation phase.

### Audit run 6 (SHARED) — 2026-04-25 (sibling `v1b1-protocol` v0.9-RC release readiness)

- audit_kind: shared (covers `v1b1-capability`, `v1b1-author`, AND `v1b1-protocol` — the full v1b1 trio)
- Target branch: `v1b1` at commit `d3c6d0a520dcbb8bc5d0db19a382d31fc2c6f1aa` (no advancement since runs 4/5).
- Audit procedure version: 1.0 (review skill) + 1.0 (authoring skill) + 1.0 (protocol skill, `~/.claude/skills/v1b1-protocol/audit.md`).
- Trigger: Protocol skill v0.9-RC release readiness. Protocol skill walk per its `audit.md`; review-skill steps 1, 2, 5 inherited from runs 4/5 (no source-of-truth advancement).
- Patterns added: none.
- Patterns refined: none.
- Patterns populated total: 23 / 26 (unchanged).
- Vendored prose drift: none (no re-verification needed since runs 4/5).
- Catalog-template + parsing.md parity (protocol skill, audit step 3): PASS — every placeholder in `~/.claude/skills/v1b1-protocol/catalog-template.md` matches the documented catalog shape (frontmatter + per-entry block); every parsing-rule section in `~/.claude/skills/v1b1-protocol/parsing.md` covers a built-in format (pcap, Beagle CSV, raw serial text, OpenAPI/Swagger, curl-examples, .pyi/Python wrapper, C/C++ headers); the unrecognized-format dialect prompt matches the 4-question template.
- Smoke corpus (protocol skill, audit step 4): PASS — three smoke fixtures across the three modes:
  - S-01 Opentrons Flex (server): 4 entries, `transport_form=command-class`, pre-emit lint stages 1/2/3 PASS; paste-into-scaffold satisfied.
  - S-02 QInstruments BioShake (bytestream): 6 entries, `transport_form=command-class`, all `confidence: confirmed`, all 6 carry non-empty Evidence blocks; Q&A converged in 5 turns; pcap byte-identical across regenerations.
  - S-03 UFactory XArm6 (dll): 5 entries, `transport_form=sdk-wrapper`, mechanical AST-walk extraction.
- Smoke corpus (review skill + authoring skill): PASS, inherited from runs 4/5.
- Anti-pattern corpus (review skill, run 4 result): PASS, inherited.
- Vocabulary leak (audit step 5, SHARED): PASS — grep across the protocol skill's three expected catalogs (`tests/fixtures/S-01/02/03-expected/*.md`) returns zero hits. The single hit in `~/.claude/skills/v1b1-protocol/SKILL.md` (the meta-quote of the Excluded Terms list inside the stage-2 lockdown step description) is the documented false-positive shape shared with the two siblings — same exception, same justification.
- Released:
  - `v1b1-capability`: v1.0 (no version bump).
  - `v1b1-author`: v0.9-RC (no version bump).
  - `v1b1-protocol`: v0.9-RC (initial release tag — first audit-trail entry mentioning this skill).
- Outstanding for v1.0 graduation of `v1b1-protocol`: SC-009 — first three real-world catalog runs by the maintainer across all three modes (server / bytestream / dll), each producing content with < 10% post-emit correction. Opentrons Flex protocol-implementation is the natural first server-mode field run.
- Notes: Second SHARED audit-trail entry. The trio (review + author + protocol) now graduates as a single ship unit. The protocol skill's audit reuses three of the review skill's six steps (vendored prose, reference.md citations, vocabulary leak) by pointer — same shape as the authoring skill. Field-run gates: `v1b1-capability` graduated v1.0 on PR #1009 Micronic; `v1b1-author` graduated v0.9-RC on the Opentrons Flex authoring run on 2026-04-25; `v1b1-protocol` ships v0.9-RC pending the maintainer's first protocol-extraction run on a real device.
