"""GGUF metadata inspection (stdlib)."""

from __future__ import annotations

import struct
from pathlib import Path

GGUF_MAGIC = b"GGUF"


def read_gguf_text_keys(path: Path, limit_keys: int = 256) -> dict[str, str]:
    path = Path(path)
    out: dict[str, str] = {}
    if not path.exists() or path.stat().st_size < 24:
        return out
    with path.open("rb") as f:
        if f.read(4) != GGUF_MAGIC:
            return out
        version = struct.unpack("<I", f.read(4))[0]
        if version < 2:
            return out
        struct.unpack("<Q", f.read(8))
        kv_count = struct.unpack("<Q", f.read(8))[0]
        for _ in range(min(int(kv_count), limit_keys)):
            try:
                key = _read_string(f)
                typ = struct.unpack("<I", f.read(4))[0]
                val = _read_value(f, typ)
                if isinstance(val, str) and val:
                    out[key] = val
                elif val is not None:
                    out[key] = str(val)
            except Exception:
                break
    return out


def _read_string(f) -> str:
    n = struct.unpack("<Q", f.read(8))[0]
    if n > 10_000_000:
        raise ValueError("string too large")
    return f.read(int(n)).decode("utf-8", errors="replace")


def _read_value(f, typ: int):
    if typ == 0:
        return struct.unpack("<B", f.read(1))[0]
    if typ == 1:
        return struct.unpack("<b", f.read(1))[0]
    if typ == 2:
        return struct.unpack("<H", f.read(2))[0]
    if typ == 3:
        return struct.unpack("<h", f.read(2))[0]
    if typ == 4:
        return struct.unpack("<I", f.read(4))[0]
    if typ == 5:
        return struct.unpack("<i", f.read(4))[0]
    if typ == 6:
        return struct.unpack("<f", f.read(4))[0]
    if typ == 7:
        return bool(struct.unpack("<B", f.read(1))[0])
    if typ == 8:
        return _read_string(f)
    if typ == 9:
        at = struct.unpack("<I", f.read(4))[0]
        n = min(int(struct.unpack("<Q", f.read(8))[0]), 64)
        items = [_read_value(f, at) for _ in range(n)]
        if at == 8:
            return ",".join(str(x) for x in items if x)
        return items
    if typ == 10:
        return struct.unpack("<Q", f.read(8))[0]
    if typ == 11:
        return struct.unpack("<q", f.read(8))[0]
    if typ == 12:
        return struct.unpack("<d", f.read(8))[0]
    return None


def model_info(path: Path) -> dict:
    keys = read_gguf_text_keys(path)
    name = keys.get("general.name") or path.name
    arch = keys.get("general.architecture") or "unknown"
    ctx = keys.get(f"{arch}.context_length") or keys.get("llama.context_length") or "?"
    tmpl = keys.get("tokenizer.chat_template") or keys.get("chat_template") or "(none declared)"
    return {
        "path": str(path),
        "name": name,
        "architecture": arch,
        "context_length": ctx,
        "tokenizer": keys.get("tokenizer.ggml.model") or "?",
        "chat_template": tmpl[:200] if isinstance(tmpl, str) else tmpl,
        "quantization": keys.get("general.file_type") or path.suffix,
        "parameter_count": keys.get("general.parameter_count") or "?",
        "keys": keys,
    }
