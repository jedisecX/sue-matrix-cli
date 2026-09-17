"""Slash-command processor. Unknown commands do not crash."""

from __future__ import annotations

from sue.config import SueConfig
from sue.conversation import ConversationManager
from sue.prompts import TemplateDetector, TEMPLATES

HELP = """
/clear              reset conversation (keep system)
/model              show model path
/template [name]    auto|generic|chatml|llama2
/system <text>      set system prompt
/temp <float>       temperature
/context <int>      context size
/save [path]        save history json
/load <path>        load history json
/help               this help
/quit               exit
""".strip()

class CommandProcessor:
    def __init__(self, cfg: SueConfig, convo: ConversationManager, detector: TemplateDetector):
        self.cfg = cfg
        self.convo = convo
        self.detector = detector
        self.template_name = cfg.template
        self.quit = False

    def handle(self, line: str) -> str | None:
        if not line.startswith("/"):
            return None
        parts = line.strip().split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        handlers = {
            "/clear": self._clear,
            "/model": self._model,
            "/template": self._template,
            "/system": self._system,
            "/temp": self._temp,
            "/context": self._context,
            "/save": self._save,
            "/load": self._load,
            "/help": lambda _a: HELP,
            "/quit": self._quit,
            "/exit": self._quit,
            "/q": self._quit,
        }
        fn = handlers.get(cmd)
        if not fn:
            return f"unknown command: {cmd}  (/help)"
        return fn(arg)

    def _clear(self, _a: str) -> str:
        self.convo.clear()
        return "conversation cleared"

    def _model(self, _a: str) -> str:
        return str(self.cfg.model_path())

    def _template(self, arg: str) -> str:
        if arg:
            name = arg.strip().lower()
            if name != "auto" and name not in TEMPLATES:
                return f"unknown template {name}"
            self.cfg.template = name
            self.template_name = name
        return f"template = {self.cfg.template}"

    def _system(self, arg: str) -> str:
        if not arg:
            return self.cfg.system
        self.convo.set_system(arg)
        return "system updated"

    def _temp(self, arg: str) -> str:
        if arg:
            try:
                self.cfg.temperature = float(arg)
            except ValueError:
                return "invalid temperature"
        return f"temperature = {self.cfg.temperature}"

    def _context(self, arg: str) -> str:
        if arg:
            try:
                self.cfg.context_size = int(arg)
            except ValueError:
                return "invalid context"
        return f"context = {self.cfg.context_size}"

    def _save(self, arg: str) -> str:
        path = arg.strip() or "sue-session.json"
        self.convo.save(path)
        return f"saved {path}"

    def _load(self, arg: str) -> str:
        if not arg:
            return "usage: /load <path>"
        self.convo.load(arg.strip())
        return f"loaded {arg}"

    def _quit(self, _a: str) -> str:
        self.quit = True
        return "link closed"
