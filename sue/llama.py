"""Safe llama-cli subprocess runner with streaming."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterator

from sue.config import SueConfig
from sue.exceptions import BinaryNotFound, LlamaError, ModelNotFound


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
        b = find_binary(self.cfg.llama_binary)
        if not b:
            for alt in ("llama-cli", "llama-completion", "main", "llama"):
                b = find_binary(alt)
                if b:
                    break
        if not b:
            raise BinaryNotFound(
                f"llama.cpp executable not found ({self.cfg.llama_binary}). "
                "Install llama.cpp and put llama-cli on PATH, or set llama_binary."
            )
        return b

    def resolve_model(self) -> Path:
        p = self.cfg.model_path()
        if not p.exists():
            raise ModelNotFound(f"GGUF model not found: {p}")
        return p

    def build_args(self, prompt: str) -> list[str]:
        return [
            self.resolve_binary(),
            "-m", str(self.resolve_model()),
            "-p", prompt,
            "-n", str(self.cfg.max_tokens),
            "-c", str(self.cfg.context_size),
            "--temp", str(self.cfg.temperature),
            "--top-p", str(self.cfg.top_p),
            "--top-k", str(self.cfg.top_k),
            "--repeat-penalty", str(self.cfg.repeat_penalty),
            "-ngl", "0",
            "--no-display-prompt",
        ]

    def generate(self, prompt: str) -> Iterator[str]:
        args = self.build_args(prompt)
        self.proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )
        assert self.proc.stdout
        try:
            while True:
                ch = self.proc.stdout.read(1)
                if not ch:
                    break
                yield ch
        finally:
            self.terminate()

    def terminate(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
