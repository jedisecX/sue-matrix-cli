"""REPL, diagnostics, model-info."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sue.config import SueConfig, write_default_config
from sue.conversation import ConversationManager
from sue.exceptions import BinaryNotFound, LlamaError, ModelNotFound
from sue.llama import LlamaRunner, find_binary
from sue.matrix import MatrixRenderer
from sue.model import model_info
from sue.mood import MoodEngine
from sue.prompts import TemplateDetector
from sue.commands import CommandProcessor
from sue.terminal import TerminalManager


def diagnose(cfg: SueConfig) -> int:
    rows = []

    def check(label, ok, fix=""):
        rows.append(("OK" if ok else "FAIL", label, fix if not ok else ""))

    check("Python", sys.version_info >= (3, 9), "Need Python 3.9+")
    binp = find_binary(cfg.llama_binary)
    check("llama-cli", bool(binp), f"Install llama.cpp; set llama_binary (now {cfg.llama_binary})")
    check("llama.cpp", bool(binp or find_binary("llama")), "Build llama.cpp and add to PATH")
    mp = cfg.model_path()
    check("GGUF model", mp.exists(), f"Place model at {mp} or --model PATH")
    term = os.environ.get("TERM", "")
    check("terminal ANSI", term not in ("dumb", ""), "Use a real TTY / TERM=xterm")
    check("true color", True, "")
    conf = Path.home() / ".config" / "sue" / "config.yaml"
    if not conf.exists():
        write_default_config()
    check("configuration", True, "")
    for tag, label, fix in rows:
        mark = "[OK]  " if tag == "OK" else "[FAIL]"
        print(f"{mark} {label}" + (f"  → {fix}" if fix else ""))
    return 0 if all(t == "OK" for t, _, _ in rows) else 1


def print_model_info(cfg: SueConfig) -> int:
    path = cfg.model_path()
    if not path.exists():
        print(f"model not found: {path}")
        return 1
    info = model_info(path)
    for k in ("name", "architecture", "context_length", "tokenizer", "chat_template", "quantization", "parameter_count", "path"):
        print(f"{k:18} {info.get(k)}")
    return 0


def run_repl(cfg: SueConfig) -> int:
    write_default_config()
    term = TerminalManager(no_color=cfg.no_color, prefer_truecolor=cfg.ui.truecolor)
    mood = MoodEngine()
    mx = MatrixRenderer(term, mood, rain=cfg.ui.matrix_rain and not cfg.no_rain)
    convo = ConversationManager(cfg)
    detector = TemplateDetector()
    cmds = CommandProcessor(cfg, convo, detector)
    runner = LlamaRunner(cfg)
    model_ok = cfg.model_path().exists()
    try:
        tmpl = detector.resolve(cfg.template, cfg.model_path() if model_ok else None)
        resolved = tmpl.name
        shown = f"{cfg.template} → {resolved}" if cfg.template == "auto" else resolved
    except Exception:
        shown = "auto → generic"
    print(mx.splash(cfg.model_path().name, shown, cfg.context_size))
    print(term.dim("[system] neural interface initialized"))
    print(term.dim(f"[model] {cfg.model}"))
    print(term.dim(f"[template] {shown}"))
    print(term.dim(f"[context] {cfg.context_size}"))
    print()
    while True:
        try:
            line = input(mx.color("you > ") + "\033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\nlink closed")
            runner.terminate()
            return 0
        line = line.strip()
        if not line:
            continue
        out = cmds.handle(line)
        if out is not None:
            print(mx.color(out, "accent"))
            if cmds.quit:
                runner.terminate()
                return 0
            continue
        convo.add("user", line)
        prompt = detector.resolve(cfg.template, cfg.model_path() if model_ok else None).format_conversation(convo.messages)
        print(mx.color("SUE >"), end=" ", flush=True)
        buf = []
        try:
            for ch in runner.generate(prompt):
                buf.append(ch)
                sys.stdout.write(mx.color(ch))
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n[interrupt]")
            runner.terminate()
            continue
        except (BinaryNotFound, ModelNotFound, LlamaError) as e:
            print(term.fg256(196, f"\n{e}"))
            demo = "(offline) install llama-cli and the GGUF to stream."
            print(mx.color(demo))
            buf = [demo]
        print()
        reply = "".join(buf).strip()
        if reply:
            convo.add("assistant", reply)
            mood.update(line + " " + reply)
    return 0
