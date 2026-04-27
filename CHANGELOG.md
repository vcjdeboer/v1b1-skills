# Changelog

All notable changes to the v1b1-skills bundle. The bundle versions all three skills together; per-skill versions are recorded in each skill's frontmatter.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) at the bundle level.

## [Unreleased]

### Per-skill versions

- `v1b1-capability` — 1.0
- `v1b1-author` — 0.9-RC
- `v1b1-protocol` — 0.9-RC

## [v1.0.0] — Initial public release

### Added

- `v1b1-capability` v1.0 — review skill enforcing 23 patterns and 6 principles extracted from Rick Wierenga's `creating-capabilities.md` prose and v1b1-merged device code (xArm6, BioShake, Nimbus, STAR, Tecan Infinite, Opentrons OT2 capability-migration). Allow-list-only vocabulary lockdown with pre-emit self-check.
- `v1b1-author` v0.9-RC — scaffold skill that walks contributors through a 5-step decision flow and emits a structurally-conformant Python scaffold + decision record. Calls `v1b1-capability` automatically as the final pre-emit lint check.
- `v1b1-protocol` v0.9-RC — protocol-extraction skill that produces a structured command catalog from DLL / server-API / bytestream-sniff inputs. The catalog drops directly into a `v1b1-author` scaffold's command-class slot.
- Shared audit cadence across the trio (see `v1b1-capability/audit.md`); audit-trail entries cover all three skills together.
