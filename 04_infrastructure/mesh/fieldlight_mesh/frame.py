"""Binary framing for SIL payloads over a stream (TCP).

Wire format (v1):
  - 4 bytes: big-endian uint32 payload length N
  - N bytes: UTF-8 encoded YAML document (single SIL message)
"""

from __future__ import annotations

import struct
from typing import BinaryIO


_MAX_PAYLOAD = 4 * 1024 * 1024  # 4 MiB safety cap


def write_frame(stream: BinaryIO, body: bytes) -> None:
    if len(body) > _MAX_PAYLOAD:
        raise ValueError(f"payload too large: {len(body)} > {_MAX_PAYLOAD}")
    stream.write(struct.pack(">I", len(body)))
    stream.write(body)
    stream.flush()


def read_frame(stream: BinaryIO) -> bytes:
    header = _read_exact(stream, 4, "length prefix")
    (n,) = struct.unpack(">I", header)
    if n == 0:
        raise ValueError("empty frames are not allowed")
    if n > _MAX_PAYLOAD:
        raise ValueError(f"invalid frame length: {n}")
    return _read_exact(stream, n, "payload")


def _read_exact(stream: BinaryIO, size: int, label: str) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            received = size - remaining
            raise EOFError(f"short read on {label}: {received}/{size} bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)
