"""In-process conversation history with context trimming."""

from __future__ import annotations

import json
from pathlib import Path

from sue.config import SueConfig


class ConversationManager:
    def __init__(self, cfg: SueConfig):
        self.cfg = cfg
        self.messages: list[dict] = []
        if cfg.system:
            self.messages.append({"role": "system", "content": cfg.system})

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.trim()

    def set_system(self, text: str) -> None:
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = text
        else:
            self.messages.insert(0, {"role": "system", "content": text})
        self.cfg.system = text

    def clear(self) -> None:
        sys = self.messages[0] if self.messages and self.messages[0]["role"] == "system" else None
        self.messages = [sys] if sys else []

    def trim(self) -> None:
        budget = max(1024, int(self.cfg.context_size * 3 * 0.7))
        sys = None
        rest = list(self.messages)
        if rest and rest[0]["role"] == "system":
            sys = rest.pop(0)
        while rest and self._size(([sys] if sys else []) + rest) > budget:
            rest.pop(0)
        self.messages = ([sys] if sys else []) + rest

    def _size(self, msgs: list) -> int:
        return sum(len(m.get("content") or "") + 16 for m in msgs)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.messages, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            self.messages = data
