"""Local heuristic mood engine. Presentation only."""

from __future__ import annotations

import re

MOODS = {
    "neutral": {"fg": 46, "accent": 34, "rgb": (0, 220, 70)},
    "happy": {"fg": 82, "accent": 118, "rgb": (80, 255, 120)},
    "sad": {"fg": 39, "accent": 27, "rgb": (40, 90, 200)},
    "angry": {"fg": 196, "accent": 160, "rgb": (255, 50, 50)},
    "curious": {"fg": 51, "accent": 45, "rgb": (0, 230, 230)},
    "excited": {"fg": 226, "accent": 220, "rgb": (255, 230, 40)},
    "focused": {"fg": 45, "accent": 33, "rgb": (20, 180, 220)},
    "warning": {"fg": 208, "accent": 214, "rgb": (255, 160, 20)},
    "error": {"fg": 196, "accent": 124, "rgb": (220, 20, 20)},
}

_RULES = [
    ("error", r"error|fail|crash|exception|traceback"),
    ("warning", r"warn|caution|danger|risk|alert"),
    ("angry", r"angry|rage|hate|furious"),
    ("sad", r"sad|sorry|grief|lonely|hurt|pain|loss"),
    ("excited", r"wow|awesome|fire|insane"),
    ("happy", r"happy|glad|love|great|nice|good"),
    ("curious", r"why|how|curious|wonder|explain"),
    ("focused", r"plan|build|implement|code|fix|analyze"),
]

class MoodEngine:
    def __init__(self):
        self.mood = "neutral"
        self._blend = 0.0

    def detect(self, text: str) -> str:
        t = (text or "").lower()
        scores = {k: 0 for k in MOODS}
        scores["neutral"] = 1
        for mood, pat in _RULES:
            if re.search(pat, t, re.I):
                scores[mood] += 2
        return max(scores, key=scores.get)

    def transition(self, old_mood: str, new_mood: str) -> str:
        if old_mood == new_mood:
            self._blend = min(1.0, self._blend + 0.25)
            self.mood = new_mood
            return new_mood
        if self._blend < 0.5:
            self._blend += 0.35
            self.mood = old_mood
            return old_mood
        self._blend = 0.0
        self.mood = new_mood
        return new_mood

    def update(self, text: str) -> str:
        return self.transition(self.mood, self.detect(text))

    def current_palette(self) -> dict:
        return MOODS.get(self.mood, MOODS["neutral"])
