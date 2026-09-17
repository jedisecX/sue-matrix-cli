"""Llama.cpp backend. Never hands the TTY to llama-cli's REPL."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

from sue.config import SueConfig
from sue.exceptions import BinaryNotFound, ModelNotFound


def find_binary(name: str) -> str | None:
    p = Path(os.path.expanduser(os.path.expandvars(name)))
    if p.is_file() and os.access(p, os.X_OK):
        return str(p)
    return shutil.which(name)


class LlamaRunner:
    def __init__(self, cfg: SueConfig):
        self.cfg = cfg
        self.proc: subprocess.Popen | None = None

    def resolve_binary(self) -> str:
        preferred = [self.cfg.llama_binary, "llama-completion", "llama-cli", "main", "llama"]
        seen = set()
        for name in preferred:
            if not name or name in seen:
                continue
            seen.add(name)
            b = find_binary(name)
            if b:
                return b
        raise BinaryNotFound(
            f"llama.cpp executable not found ({self.cfg.llama_binary}). "
            "Install llama.cpp (llama-completion or llama-cli) and put it on PATH."
        )

    def resolve_model(self) -> Path:
        p = self.cfg.model_path()
        if not p.exists():
            raise ModelNotFound(f"GGUF model not found: {p}")
        return p

    def build_args(self, prompt_file: str) -> list[str]:
        return [
            self.resolve_binary(),
            "-m", str(self.resolve_model()),
            "-f", prompt_file,
            "-n", str(self.cfg.max_tokens),
            "-c", str(self.cfg.context_size),
            "--temp", str(self.cfg.temperature),
            "--top-p", str(self.cfg.top_p),
            "--top-k", str(self.cfg.top_k),
            "--repeat-penalty", str(self.cfg.repeat_penalty),
            "--no-display-prompt",
            "-st",
            "-no-cnv",
            "--no-conversation",
        ]

    def generate(self, prompt: str) -> Iterator[str]:
        fd, path = tempfile.mkstemp(prefix="sue-prompt-", suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(prompt)
            args = self.build_args(path)
            self.proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            assert self.proc.stdout
            buf = ""
            while True:
                ch = self.proc.stdout.read(1)
                if not ch:
                    break
                buf += ch
                if ch in ("\n", " "):
                    low = buf.lower()
                    if any(n in low for n in ("available commands", "interactive mode")):
                        buf = ""
                        continue
                    if buf.strip() in ("/exit", "/regen", "/clear", "/read", "/glob"):
                        buf = ""
                        continue
                    yield buf
                    buf = ""
                elif len(buf) > 24:
                    yield buf
                    buf = ""
            if buf:
                yield buf
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
            self.terminate()

    def terminate(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
