"""Matrix aesthetic renderer."""

from __future__ import annotations

import random

from sue.mood import MoodEngine
from sue.terminal import TerminalManager

BANNER = [
    "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557",
    "\u2551              S U E   C O R E                \u2551",
    "\u2551          NEURAL LINK // ONLINE              \u2551",
    "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d",
]

class MatrixRenderer:
    def __init__(self, term: TerminalManager, mood: MoodEngine, rain: bool = True):
        self.term = term
        self.mood = mood
        self.rain = rain and term.ansi

    def color(self, text: str, key: str = "fg") -> str:
        pal = self.mood.current_palette()
        if self.term.truecolor and "rgb" in pal:
            r, g, b = pal["rgb"]
            if key == "accent":
                r, g, b = min(255, r + 30), min(255, g + 30), min(255, b + 20)
            return self.term.rgb(r, g, b, text)
        return self.term.fg256(pal.get(key, 46), text)

    def bits(self, n: int = 10) -> str:
        return " ".join(random.choice(("01", "10", "11", "00")) for _ in range(n))

    def splash(self, model_name: str, template: str, context: int) -> str:
        w = min(self.term.width, 56)
        lines = []
        if self.rain:
            lines.append(self.color("MATRIX LINK ESTABLISHED", "accent"))
            lines.append(self.term.dim(self.color(self.bits(12))))
            lines.append("")
        for row in BANNER:
            lines.append(self.color(row[:w]))
        lines.append("")
        rows = [
            ("MODEL", model_name),
            ("TEMPLATE", template.upper()),
            ("CONTEXT", str(context)),
            ("MOOD", self.mood.mood.upper()),
            ("LINK", "LOCAL"),
        ]
        for k, v in rows:
            lines.append(f"  {self.color(k.ljust(12), 'accent')}{self.color(v)}")
        lines.append("")
        lines.append("  " + self.term.dim(self.color(self.bits(10))))
        lines.append("")
        return "\n".join(lines)
