#!/usr/bin/env python3
"""Deterministic synthesis script for the S-02 BioShake bytestream fixture.

Run: `python3 build_bioshake_pcap.py` from this directory.
Output: `bioshake-session-1.pcap` (classic libpcap format, DLT_USER0 link layer).

The pcap contains 36 packets — 6 commands x 3 repetitions x (request + response) —
covering: start_shake @ 500 RPM, stop_shake, set_temperature 37, lock_plate,
unlock_plate, query_status. Framing matches the documented BioShake shape:
0xAA <len> <opcode> <payload> <crc16_lo> <crc16_hi> 0xFE
where CRC-16 is the XMODEM polynomial (0x1021, init 0x0000, no reflection,
no XOR-out), serialized little-endian.

Determinism: the script seeds nothing random. Timestamps and bytes are fixed
constants. Re-running yields a byte-identical file.
"""

from __future__ import annotations

import struct
from pathlib import Path

# ----- Constants -----

PCAP_MAGIC = 0xA1B2C3D4  # classic pcap, microsecond resolution
SNAPLEN = 65535
DLT_USER0 = 147

START_BYTE = 0xAA
END_BYTE = 0xFE

# Opcodes
OP_START_SHAKE = 0x10
OP_STOP_SHAKE = 0x11
OP_SET_TEMPERATURE = 0x20
OP_LOCK_PLATE = 0x30
OP_UNLOCK_PLATE = 0x31
OP_QUERY_STATUS = 0x40

# Status-byte values
STATUS_ACK = 0x00


def crc16_xmodem(data: bytes) -> int:
    """CRC-16/XMODEM: poly 0x1021, init 0x0000, no reflection, no XOR-out."""
    crc = 0x0000
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def frame(opcode: int, payload: bytes) -> bytes:
    """Build a BioShake frame: start | len | opcode | payload | crc(LE) | end.

    `len` counts bytes from `opcode` through the last byte before `end_byte`,
    i.e. opcode (1) + payload (n) + crc (2) = n + 3.
    """
    body = bytes([opcode]) + payload
    length = len(body) + 2  # +2 for CRC
    crc = crc16_xmodem(body)
    crc_lo = crc & 0xFF
    crc_hi = (crc >> 8) & 0xFF
    return bytes([START_BYTE, length]) + body + bytes([crc_lo, crc_hi, END_BYTE])


# ----- Per-command request + response builders -----

def start_shake_req(speed_rpm: int = 500) -> bytes:
    # speed as uint16 little-endian
    payload = struct.pack("<H", speed_rpm)
    return frame(OP_START_SHAKE, payload)


def start_shake_resp() -> bytes:
    # ack: opcode echo + status byte
    return frame(OP_START_SHAKE, bytes([STATUS_ACK]))


def stop_shake_req() -> bytes:
    return frame(OP_STOP_SHAKE, b"")


def stop_shake_resp() -> bytes:
    return frame(OP_STOP_SHAKE, bytes([STATUS_ACK]))


def set_temperature_req(temp_c: int = 37) -> bytes:
    # BCD encoding: each decimal digit in a nibble. 37 -> 0x37.
    tens, ones = divmod(temp_c, 10)
    bcd_byte = (tens << 4) | ones
    return frame(OP_SET_TEMPERATURE, bytes([bcd_byte]))


def set_temperature_resp() -> bytes:
    return frame(OP_SET_TEMPERATURE, bytes([STATUS_ACK]))


def lock_plate_req() -> bytes:
    return frame(OP_LOCK_PLATE, b"")


def lock_plate_resp() -> bytes:
    return frame(OP_LOCK_PLATE, bytes([STATUS_ACK]))


def unlock_plate_req() -> bytes:
    return frame(OP_UNLOCK_PLATE, b"")


def unlock_plate_resp() -> bytes:
    return frame(OP_UNLOCK_PLATE, bytes([STATUS_ACK]))


def query_status_req() -> bytes:
    return frame(OP_QUERY_STATUS, b"")


def query_status_resp(motion_state: int = 1, lock_state: int = 1, temp_c: int = 37) -> bytes:
    # status byte: high nibble = motion_state, low nibble = lock_state
    status_byte = ((motion_state & 0x0F) << 4) | (lock_state & 0x0F)
    tens, ones = divmod(temp_c, 10)
    temp_byte = (tens << 4) | ones
    return frame(OP_QUERY_STATUS, bytes([status_byte, temp_byte]))


# ----- Session script: 6 commands x 3 repetitions, fixed order -----

# Each tuple: (request bytes, response bytes)
ONE_BURST = [
    (start_shake_req(500), start_shake_resp()),
    (stop_shake_req(), stop_shake_resp()),
    (set_temperature_req(37), set_temperature_resp()),
    (lock_plate_req(), lock_plate_resp()),
    (unlock_plate_req(), unlock_plate_resp()),
    (query_status_req(), query_status_resp(motion_state=1, lock_state=1, temp_c=37)),
]

# 3 repetitions
SESSION = ONE_BURST * 3


# ----- Timestamps -----

# Base = 2026-04-25T12:34:56.000000Z = epoch 1714048496.000000
BASE_TS_SEC = 1714048496
BASE_TS_USEC = 0

# Per-burst layout:
#   request:        t + 0 ms
#   response:       t + 5 ms
#   next request:   t + 100 ms (within same repetition)
# Between repetitions: +1000 ms gap after the 6th burst's response.

REQ_OFFSET_US = 0
RESP_OFFSET_US = 5_000        # 5 ms
INTER_BURST_US = 100_000      # 100 ms
INTER_REPETITION_US = 1_000_000  # 1 s


def session_packet_records():
    """Yield (ts_sec, ts_usec, direction, bytes) for the full 36-packet session."""
    cursor_us = 0
    for rep in range(3):
        for burst_idx, (req, resp) in enumerate(ONE_BURST):
            # request packet (host -> device)
            req_us = cursor_us + REQ_OFFSET_US
            yield (
                BASE_TS_SEC + req_us // 1_000_000,
                BASE_TS_USEC + req_us % 1_000_000,
                "out",
                req,
            )
            # response packet (device -> host)
            resp_us = cursor_us + RESP_OFFSET_US
            yield (
                BASE_TS_SEC + resp_us // 1_000_000,
                BASE_TS_USEC + resp_us % 1_000_000,
                "in",
                resp,
            )
            # advance cursor to next burst
            cursor_us += INTER_BURST_US
        # gap between repetitions (subtract one inter-burst since we advanced past last)
        cursor_us += INTER_REPETITION_US - INTER_BURST_US


# ----- pcap writer -----

def write_pcap(path: Path) -> None:
    """Write classic-libpcap with DLT_USER0 link-layer."""
    with path.open("wb") as f:
        # Global header (24 bytes)
        f.write(struct.pack(
            "<IHHiIII",
            PCAP_MAGIC,    # magic
            2,             # version major
            4,             # version minor
            0,             # thiszone
            0,             # sigfigs
            SNAPLEN,       # snaplen
            DLT_USER0,     # network (link-layer type)
        ))
        # Per-record header + payload
        for ts_sec, ts_usec, _direction, payload in session_packet_records():
            incl_len = len(payload)
            orig_len = incl_len
            f.write(struct.pack(
                "<IIII",
                ts_sec,
                ts_usec,
                incl_len,
                orig_len,
            ))
            f.write(payload)


def main() -> None:
    here = Path(__file__).resolve().parent
    out = here / "bioshake-session-1.pcap"
    write_pcap(out)
    size = out.stat().st_size
    print(f"wrote {out.name} ({size} bytes, 36 packets, deterministic)")


if __name__ == "__main__":
    main()
