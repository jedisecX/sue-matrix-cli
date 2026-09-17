"""Terminal capability detection and ANSI helpers."""

from __future__ import annotations

import os
import shutil
import sys


class TerminalManager:
    def __init__(self, no_color: bool = False, prefer_truecolor: bool = True):
        self.no_color = no_color or not sys.stdout.isatty()
        self.width, self.height = shutil.get_terminal_size((80, 24))
        self.term = os.environ.get("TERM", "xterm")
        self.is_termux = "TERMUX_VERSION" in os.environ or "com.termux" in os.environ.get("PREFIX", "")
        colorterm = os.environ.get("COLORTERM", "")
        colors = os.environ.get("TERM", "")
        self.truecolor = prefer_truecolor and not self.no_color
        self.ansi = not self.no_color and self.term not in ("dumb", "")

    def refresh_size(self) -> None:
        self.width, self.height = shutil.get_terminal_size((80, 24))

    def fg256(self, n: int, text: str) -> str:
        if not self.ansi:
            return text
        return f"\033[38;5;{n}m{text}\033[0m"

    def rgb(self, r: int, g: int, b: int, text: str) -> str:
        if not self.ansi:
            return text
        if self.truecolor:
            return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
        return self.fg256(46, text)

    def bold(self, text: str) -> str:
        if not self.ansi:
            return text
        return f"\033[1m{text}\033[0m"

    def dim(self, text: str) -> str:
        if not self.ansi:
            return text
        return f"\033[2m{text}\033[0m"

    def clear_line(self) -> str:
        return "\033[2K\r" if self.ansi else "\r"
