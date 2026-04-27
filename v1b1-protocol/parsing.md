---
title: "v1b1-protocol Parsing Rules"
last_updated: 2026-04-25
---

# Parsing Rules

How the skill turns each input format into a normalized stream the catalog-extraction logic consumes. One section per built-in format; one section for the unrecognized-format dialect prompt.

The skill itself emits markdown only — these are *rules* the LLM applies during extraction, not parser code.

---

## Wireshark pcap (`.pcap`, `.pcapng`)

**Used in**: `bytestream` mode.

**Normalized output**: `[(timestamp, direction, bytes), ...]` where `direction` is `out` (host → device, request side) or `in` (device → host, response side).

**Rules**:

1. Open the pcap with `tshark -r <file> -Y "usb || tcp" -T json` (or equivalent). Each packet object yields one stream entry.
2. For USB captures (USBPcap, usbmon): `direction = out` if `usb.urb_type == "S"` (submit) AND endpoint is host-→-device; `direction = in` for completions on device-→-host endpoints.
3. For TCP captures: `direction` is inferred by socket-pair role — the side that initiates (SYN sender) is the host; subsequent packets follow that orientation.
4. `bytes` is the application-layer payload (USB data stage or TCP payload), with framing of the *transport* layer stripped — start-of-protocol / opcode / length live INSIDE these bytes; the skill's framing inference works on this slice.
5. Multi-device captures (USB hub with several devices): cluster by `usb.device_address`. Per FR's "multi-device capture" edge case, prompt the contributor to scope to one device address per run.

**Common pitfalls**: USB control-transfer setup packets (8 bytes) are NOT command bytes — skip records where `usb.transfer_type == 0x02` ("Control") setup stage. Bulk and interrupt transfers carry the actual command stream.

---

## Total Phase Beagle USB analyzer text/CSV exports

**Used in**: `bytestream` mode.

**Normalized output**: same `[(timestamp, direction, bytes), ...]`.

**Canonical Beagle CSV layout** (Total Phase's default export):

```
Index,m:s.ms.us,Rec.,USB Speed,Err,Dev,Ep,Record,Summary,...,Data,...
```

**Rules**:

1. Skip header row (column names).
2. `timestamp` from the `m:s.ms.us` column.
3. `direction = out` when the `Record` column = "OUT txn" or "OUT data"; `in` for "IN txn" or "IN data".
4. `bytes` parsed from the `Data` column (space-separated hex bytes by default; the dialect is configurable in Beagle export settings — if a contributor's export uses a non-default byte separator or representation, prompt for dialect per the "Unrecognized format" section below).
5. Filter out non-data records (`SOF`, `Setup`, `ACK` only, etc.) — keep records with non-empty `Data`.

**Multi-endpoint protocols**: Beagle exports always carry the endpoint number; cluster by `Ep` for distinct device interfaces.

---

## Raw serial-sniff text logs

**Used in**: `bytestream` mode.

**Normalized output**: same.

**Rules**:

The shape of these logs varies widely — there's no canonical format. Common dialects:

- **Hex dump with timestamp**: `2026-04-25 12:34:56.123 > AA 05 10 F4 01 ...` (timestamp, direction arrow, hex bytes).
- **Hex dump without timestamp**: `> AA 05 10 ...` / `< AA 03 10 ...` — direction by arrow, no timing.
- **Mixed hex and ASCII**: `> AA <STX> 0x10 ...` — printable bytes shown as ASCII, non-printable as escape.

**Default rules** (apply unless the dialect prompt overrides):

1. `timestamp`: parsed if present (any leading ISO-8601 or `mm:ss.ms` pattern); otherwise `None` (timing-based pairing falls back to packet ordering).
2. `direction`: `out` for `>` lines; `in` for `<` lines. If the dialect uses different markers, the contributor specifies them in the dialect prompt.
3. `bytes`: hex tokens parsed; ASCII tokens converted to their byte values; escape tokens (`<STX>`, `\x02`, etc.) decoded to single bytes.

When the format doesn't obviously match a default, fall through to the "Unrecognized format dialect prompt".

---

## OpenAPI 3.x and Swagger 2.x specs

**Used in**: `server` mode.

**Normalized output**: list of `Endpoint(operation_id, verb, path, request_body_schema, response_schema, summary, deprecated)`.

**Rules**:

1. Parse the spec (JSON or YAML). For Swagger 2.x, normalize to OpenAPI 3.x semantics first: `definitions` → `components.schemas`, `host` + `basePath` → `servers`.
2. Walk `paths.<path>.<method>` for each `(path, method)` pair.
3. `operation_id`: prefer `operationId`. Fall back to `<method>_<path-with-underscores>` if missing.
4. `name` (Catalog Entry): PascalCase derived from `operation_id` (e.g., `aspirate` → `Aspirate`; `getRunCommands` → `GetRunCommands`).
5. `verb_or_opcode`: `<METHOD> <path>` (e.g., `POST /runs/{run_id}/commands`).
6. `request_shape`: walk `requestBody.content.<media-type>.schema`; flatten to a list of `(field, type, notes)` rows. Nested objects become dotted-path field names (`params.wellLocation.offset.x`).
7. `response_shape`: walk `responses.200.content.<media-type>.schema` (or `201`, `default` if `200` absent). Same flattening as request.
8. `side_effects`: derived from `summary` or `description` (one-sentence trim).
9. Skip endpoints where `deprecated: true`.
10. Default `transport_form = command-class`.

**Reference**: OpenAPI 3.0.3 spec (https://spec.openapis.org/oas/v3.0.3) for canonical field semantics.

---

## Curl-examples directory

**Used in**: `server` mode.

**Normalized output**: same `Endpoint` shape.

**Rules**:

1. Each `.sh` / `.curl` / `.txt` file in the directory is one example.
2. Parse the curl invocation: `-X <METHOD>`, the URL, `-d <body>` or `--data <body>`, `-H` headers.
3. Run the example against the device (if reachable) OR read an adjacent `.response.json` / `.response.txt` file to get the response shape.
4. `name`: PascalCase from a filename suffix or a `# name: <Name>` comment line if the contributor supplied one. Fall back to `<METHOD>_<last-path-segment>` PascalCase.
5. `request_shape`: parsed from `-d` body (JSON), one row per top-level field (nested via dotted-path).
6. `response_shape`: parsed from `.response.*` companion file. Mark fields as `unknown — observe and update` when the response file is missing.
7. `side_effects`: parsed from a `# side_effects: <text>` comment line if supplied; else `[Provide side-effects note]` placeholder.

---

## Python `.pyi` stubs and Python wrapper modules

**Used in**: `dll` mode.

**Normalized output**: list of `Method(name, params, return_type, docstring)`.

**Rules**:

1. AST-walk the file (Python `ast` semantics — applies even though the skill itself emits markdown; the LLM applies these rules to its reading).
2. For `.pyi`: walk top-level `class` declarations; collect `def` methods (not `_private`) with their type annotations and any `"""docstring"""`.
3. For Python wrapper modules: same AST walk; `inspect.signature` semantics for parameter list.
4. `name` (Catalog Entry): PascalCase from method name (`set_servo_angle` → `SetServoAngle`).
5. `verb_or_opcode`: fully-qualified method name (`XArmAPI.set_servo_angle`).
6. `request_shape`: one row per parameter; type from annotation; `notes` from any `# inline comment` adjacent to the parameter, fallback empty.
7. `response_shape`: one row for the return type. If return type is a tuple or composite, expand by element.
8. `side_effects`: derived from the method's docstring (one-sentence trim of the first line). If no docstring, `[Provide side-effects note]` placeholder.
9. Default `transport_form = sdk-wrapper`.

**Skip**: dunder methods (`__init__`, `__repr__`, etc.); private methods (`_method`); deprecated decorators (`@deprecated`).

---

## C/C++ headers (`.h`, `.hpp`)

**Used in**: `dll` mode.

**Normalized output**: same `Method` shape, with type representations annotated for Python use.

**Rules**:

1. Parse the header. For each function declaration not in a `static` / `inline` block, collect the signature.
2. Type mapping:

   | C/C++ | Python representation |
   |-------|------------------------|
   | `int`, `long`, `int32_t` | `int` |
   | `short`, `int16_t` | `int` (annotate "16-bit") |
   | `unsigned int`, `uint32_t` | `int` (annotate "unsigned") |
   | `float`, `double` | `float` |
   | `bool` | `bool` |
   | `const char*` | `str` |
   | `void*` | `ctypes.c_void_p` (annotate "opaque pointer") |
   | `T*` (other) | `ctypes.POINTER(<T>)` (annotate the C type) |
   | `T[]` | `list[<T>]` (annotate "array") |
   | structures | `<StructName>` (annotate; treat as a sub-shape if simple, else opaque) |

3. `name`: PascalCase from function name.
4. `request_shape`: one row per parameter. Pointer parameters annotated as in/out per `const`-qualifier or context comments.
5. `response_shape`: one row for the return value.
6. `side_effects`: derived from preceding `/** ... */` doxygen comment if present; else placeholder.
7. Skip macros, typedefs, structs, and forward declarations — these don't surface as Catalog Entries.

---

## Unrecognized format dialect prompt

**Used in**: ALL modes when the input format is not in the built-in set.

**Rationale**: per FR-013, the skill prompts for a 4-axis dialect description rather than failing on an unfamiliar capture or spec format. Recorded inside the run; not persisted.

**Prompt template**:

```
The input format at <path> is not a recognized built-in. To proceed, describe its dialect:

1. Separator (how rows / records are delimited):
   - comma | tab | space | newline-only | custom (specify)

2. Byte representation (how bytes are encoded):
   - hex (e.g. "AA 05 10")
   - decimal (e.g. "170 5 16")
   - escaped-ascii (e.g. "\xAA\x05\x10")
   - mixed (specify)

3. Timestamp column (which column holds the timestamp; "none" if untimestamped):
   - <column index>
   - none

4. Direction column (which column indicates request/response direction; "inferred" defers to timing-based pairing):
   - <column index>
   - inferred

After the contributor answers, the skill applies these rules to parse the file. If the input is a server-spec format (not a capture), the prompt is reframed: separator → entry separator (newline / blank-line / file-per-endpoint); byte representation → params field encoding (JSON / YAML / form / query-string); timestamp column → "n/a"; direction column → "n/a" (request/response paired by spec structure).
```

The skill records the dialect choice in the run record (visible to the contributor in the hand-off block but NOT persisted to the catalog frontmatter).
