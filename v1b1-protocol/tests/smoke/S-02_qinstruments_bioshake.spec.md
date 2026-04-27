---
spec_id: S-02
vendor: QInstruments
device: BioShake
mode: bytestream
input_path: tests/smoke/inputs/bioshake-session-1.pcap
intent_text: "I sent: start_shake at 500 RPM, stop_shake, set_temperature 37, lock_plate, unlock_plate, query_status — in that order, three times each."
expected_entry_count: 6
expected_transport_form: command-class
expected_outcome: clean-pass
expected_files:
  - <contributor-repo>/docs/v1b1-protocol/qinstruments-bioshake-commands.md
expected_catalog:
  path: tests/fixtures/S-02-expected/qinstruments-bioshake-commands.md
  entry_names_in_order: [LockPlate, QueryStatus, SetTemperature, StartShake, StopShake, UnlockPlate]
expected_review_skill_outcome: "transport_form lookup PASS — command-class is in shared reference.md P-21 list"
confirmation_answers:
  - "A"
  - "Little"
  - "BCD"
  - "Confirmed — both lock and unlock are parameterless; opcodes 0x30 / 0x31"
  - "High nibble = motion_state (0=idle, 1=shaking); low nibble = lock_state (0=unlocked, 1=locked); next byte = temperature (BCD)"
expected_qa_turn_count: 5
expected_evidence_blocks: 6
---

# Smoke spec S-02: QInstruments BioShake (bytestream mode)

Exercises the bytestream-mode 7-step Q&A loop on a synthesized pcap of 36 packets (6 commands × 3 repetitions × request+response). The replay uses the pre-canned `confirmation_answers` above so the run is deterministic without interactive input.

## Verbatim contributor invocation (replay this for the audit)

```
/v1b1-protocol QInstruments BioShake bytestream ~/.claude/skills/v1b1-protocol/tests/smoke/inputs/bioshake-session-1.pcap "I sent: start_shake at 500 RPM, stop_shake, set_temperature 37, lock_plate, unlock_plate, query_status — in that order, three times each."
```

The audit re-run feeds `confirmation_answers` (in order) at each Q&A turn instead of prompting interactively (per `contracts/bytestream-qa-contract.md` "Replay path").

## Expected behavior summary

- 36 packets parsed; clustered into 12 distinct shapes (6 request + 6 response).
- Q&A loop walks 5 confirmation prompts (meets SC-003 ≤ 5 prompts for a 6-command device) and terminates on **full coverage** (every shape has one consistent framing AND one consistent field-encoding hypothesis).
- All 6 entries emit with `confidence: confirmed`.
- Each entry carries a non-empty `Evidence` block (capture timestamp range + packet indices + which Q&A turn(s) disambiguated each hypothesis) per FR-015 / VR-4.
- Default `transport_form = command-class` (bytestream + opcode-framed payload matches Nimbus shape).
- 0 Open Questions on emit.
- Pre-emit lint passes all 3 stages on first try.

## Q&A turn map (matches `confirmation_answers` order)

| Turn | Skill question | Contributor answer | Hypothesis-set delta |
|---|---|---|---|
| 1 | Shape #1 (StartShake) framing: candidate A (start `0xAA`, length byte at idx 1, CRC-16, end `0xFE`) vs candidate B (no start byte, length idx 0, no checksum, end `0xFE`) | `A` | Locks framing for all 6 shapes (propagated). |
| 2 | StartShake speed bytes (`0xF4 0x01`): little-endian (500) vs big-endian (62465) | `Little` | Locks numeric endianness for all multi-byte fields. |
| 3 | SetTemperature byte (`0x37`): BCD (37) vs binary uint8 (55) | `BCD` | Locks SetTemperature's temperature encoding. |
| 4 | LockPlate / UnlockPlate parameterless shape: confirm the two paired opcodes | `Confirmed — both lock and unlock are parameterless; opcodes 0x30 / 0x31` | Locks LockPlate / UnlockPlate as fire-and-forget commands with ack response. |
| 5 | QueryStatus response status byte decomposition (bitfield candidates) | `High nibble = motion_state (0=idle, 1=shaking); low nibble = lock_state (0=unlocked, 1=locked); next byte = temperature (BCD)` | Locks QueryStatus response field decomposition. |

After turn 5: full-coverage termination fires. All hypotheses are uniquely consistent. Loop emits.

## Source of the pcap fixture

The pcap is synthesized deterministically by `tests/smoke/inputs/build_bioshake_pcap.py`. The script uses fixed timestamps (base = `2026-04-25T12:34:56.000000Z` = epoch `1714048496.000000`), fixed inter-packet gaps (request+response burst within 5ms; 100ms between bursts; 1s between repetitions), and the documented BioShake framing (start `0xAA`, length uint8, opcode uint8, payload, CRC-16/XMODEM little-endian, end `0xFE`). Re-running the script produces a byte-identical `bioshake-session-1.pcap`.
