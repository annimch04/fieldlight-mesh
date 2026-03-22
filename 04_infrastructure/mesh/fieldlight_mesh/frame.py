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
    header = stream.read(4)
    if len(header) < 4:
        raise EOFError("short read on length prefix")
    (n,) = struct.unpack(">I", header)
    if n > _MAX_PAYLOAD:
        raise ValueError(f"invalid frame length: {n}")
    data = stream.read(n)
    if len(data) < n:
        raise EOFError("short read on payload")
    return data
