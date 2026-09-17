"""Configuration manager. YAML optional; stdlib fallback."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path


def expand(path: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path))).resolve()


@dataclass
class UIConfig:
    matrix_rain: bool = True
    animations: bool = True
    truecolor: bool = True
    mood_colors: bool = True


@dataclass
class SueConfig:
    model: str = "~/models/2b.gguf"
    llama_binary: str = "llama-cli"
    context_size: int = 8192
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 1024
    template: str = "auto"
    system: str = "You are SUE, a local neural assistant."
    ui: UIConfig = field(default_factory=UIConfig)
    debug: bool = False
    no_rain: bool = False
    no_color: bool = False

    def model_path(self) -> Path:
        return expand(self.model)

    def config_dir(self) -> Path:
        return expand("~/.config/sue")

    def log_path(self) -> Path:
        return expand("~/.local/state/sue/sue.log")


def _coerce(v: str):
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        return v


def _parse_simple_yaml(text: str) -> dict:
    out: dict = {}
    ui: dict = {}
    in_ui = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.strip() == "ui:":
            in_ui = True
            continue
        if in_ui and not line.startswith((" ", "\t")):
            in_ui = False
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        (ui if in_ui else out)[k] = _coerce(v)
    if ui:
        out["ui"] = ui
    return out


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return _parse_simple_yaml(text)


def load_config(argv: list[str] | None = None) -> SueConfig:
    cfg = SueConfig()
    cfg.config_dir().mkdir(parents=True, exist_ok=True)
    data = _load_yaml(cfg.config_dir() / "config.yaml")
    if "ui" in data and isinstance(data["ui"], dict):
        cfg.ui = UIConfig(**{k: v for k, v in data["ui"].items() if k in UIConfig.__dataclass_fields__})
        data = {k: v for k, v in data.items() if k != "ui"}
    for k, v in data.items():
        if hasattr(cfg, k) and k != "ui":
            setattr(cfg, k, v)
    p = argparse.ArgumentParser(prog="sue")
    p.add_argument("--model")
    p.add_argument("--llama-binary")
    p.add_argument("--template")
    p.add_argument("--context", type=int)
    p.add_argument("--temperature", type=float)
    p.add_argument("--top-p", type=float)
    p.add_argument("--top-k", type=int)
    p.add_argument("--repeat-penalty", type=float)
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--system")
    p.add_argument("--no-rain", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--diagnose", action="store_true")
    p.add_argument("--model-info", action="store_true")
    args, _ = p.parse_known_args(argv)
    if args.model:
        cfg.model = args.model
    if args.llama_binary:
        cfg.llama_binary = args.llama_binary
    if args.template:
        cfg.template = args.template
    if args.context:
        cfg.context_size = args.context
    if args.temperature is not None:
        cfg.temperature = args.temperature
    if args.top_p is not None:
        cfg.top_p = args.top_p
    if args.top_k is not None:
        cfg.top_k = args.top_k
    if args.repeat_penalty is not None:
        cfg.repeat_penalty = args.repeat_penalty
    if args.max_tokens:
        cfg.max_tokens = args.max_tokens
    if args.system:
        cfg.system = args.system
    if args.no_rain:
        cfg.no_rain = True
        cfg.ui.matrix_rain = False
    if args.no_color:
        cfg.no_color = True
    if args.debug:
        cfg.debug = True
    cfg._diagnose = bool(args.diagnose)
    cfg._model_info = bool(args.model_info)
    return cfg


def write_default_config(path: Path | None = None) -> Path:
    cfg = SueConfig()
    path = path or (cfg.config_dir() / "config.yaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            'model: "~/models/2b.gguf"\nllama_binary: "llama-cli"\ncontext_size: 8192\n'
            "temperature: 0.8\ntop_p: 0.95\ntop_k: 40\nrepeat_penalty: 1.1\nmax_tokens: 1024\n"
            'template: auto\nsystem: "You are SUE, a local neural assistant."\n\n'
            "ui:\n  matrix_rain: true\n  animations: true\n  truecolor: true\n  mood_colors: true\n",
            encoding="utf-8",
        )
    return path
