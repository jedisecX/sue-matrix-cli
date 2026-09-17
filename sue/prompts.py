"""GGUF-first prompt construction. Do not guess ### Instruction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TemplateInfo:
    name: str
    source: str
    confidence: str
    state: str
    raw: str = ""
    architecture: str = ""
    model_name: str = ""
    tokenizer: str = ""

    def label(self) -> str:
        if self.state == "DETECTED":
            return f"DETECTED ({self.name})"
        if self.state == "UNKNOWN":
            return "UNKNOWN \u2192 FALLBACK"
        return "GENERIC_FALLBACK"


class ChatTemplate:
    def __init__(self, info: TemplateInfo):
        self.info = info

    def format_conversation(self, messages: list) -> str:
        raw = self.info.raw or ""
        kind = self.info.name
        if kind == "chatml" or "<|im_start|>" in raw:
            return _chatml(messages)
        if kind == "llama3" or "<|start_header_id|>" in raw:
            return _llama3(messages)
        if kind == "llama2" or "[INST]" in raw.upper():
            return _llama2(messages)
        if kind == "gemma" or "<start_of_turn>" in raw:
            return _gemma(messages)
        if kind == "phi3" or "<|user|>" in raw:
            return _phi3(messages)
        if raw.strip():
            return _apply_simple_jinja(raw, messages)
        return _plain(messages)


def _plain(messages: list) -> str:
    parts = []
    for m in messages:
        role, content = m.get("role", ""), (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            parts.append(content + "\n")
        elif role == "user":
            parts.append(f"User: {content}\n")
        elif role == "assistant":
            parts.append(f"Assistant: {content}\n")
    parts.append("Assistant:")
    return "\n".join(parts)


def _chatml(messages: list) -> str:
    parts = []
    for m in messages:
        role, content = m.get("role", "user"), (m.get("content") or "").strip()
        parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
    parts.append("<|im_start|>assistant\n")
    return "".join(parts)


def _llama3(messages: list) -> str:
    parts = ["<|begin_of_text|>"]
    for m in messages:
        role, content = m.get("role", "user"), (m.get("content") or "").strip()
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
    return "".join(parts)


def _llama2(messages: list) -> str:
    sys_txt = ""
    out = []
    pending = None
    for m in messages:
        role, content = m.get("role", ""), (m.get("content") or "").strip()
        if role == "system":
            sys_txt = f"<<SYS>>\n{content}\n<</SYS>>\n\n"
        elif role == "user":
            pending = content
        elif role == "assistant" and pending is not None:
            prefix, sys_txt = sys_txt, ""
            out.append(f"{prefix}[INST] {pending} [/INST] {content} </s>")
            pending = None
    if pending is not None:
        out.append(f"{sys_txt}[INST] {pending} [/INST] ")
    return "\n".join(out) if out else sys_txt


def _gemma(messages: list) -> str:
    parts = []
    for m in messages:
        role, content = m.get("role", "user"), (m.get("content") or "").strip()
        if role == "system":
            parts.append(f"<start_of_turn>user\nSYSTEM: {content}<end_of_turn>\n")
        else:
            tag = "model" if role == "assistant" else "user"
            parts.append(f"<start_of_turn>{tag}\n{content}<end_of_turn>\n")
    parts.append("<start_of_turn>model\n")
    return "".join(parts)


def _phi3(messages: list) -> str:
    parts = []
    for m in messages:
        role, content = m.get("role", "user"), (m.get("content") or "").strip()
        if role == "system":
            parts.append(f"<|system|>\n{content}<|end|>\n")
        elif role == "user":
            parts.append(f"<|user|>\n{content}<|end|>\n")
        else:
            parts.append(f"<|assistant|>\n{content}<|end|>\n")
    parts.append("<|assistant|>\n")
    return "".join(parts)


def _apply_simple_jinja(tmpl: str, messages: list) -> str:
    if "<|im_start|>" in tmpl:
        return _chatml(messages)
    if "<|start_header_id|>" in tmpl:
        return _llama3(messages)
    if "<start_of_turn>" in tmpl:
        return _gemma(messages)
    if "<|user|>" in tmpl:
        return _phi3(messages)
    if "[INST]" in tmpl:
        return _llama2(messages)
    return _plain(messages)


class TemplateDetector:
    def __init__(self):
        self.last: TemplateInfo | None = None

    def inspect(self, model_path) -> dict:
        from sue.model import read_gguf_text_keys, model_info
        path = Path(model_path) if model_path else None
        if not path or not path.exists():
            return {}
        info = model_info(path)
        keys = info.get("keys") or read_gguf_text_keys(path)
        return {
            "general.architecture": keys.get("general.architecture") or info.get("architecture"),
            "general.name": keys.get("general.name") or info.get("name"),
            "tokenizer.chat_template": keys.get("tokenizer.chat_template") or keys.get("chat_template") or "",
            "tokenizer.ggml.model": keys.get("tokenizer.ggml.model") or keys.get("tokenizer.model") or "",
            "keys": keys,
        }

    def detect(self, metadata: dict) -> TemplateInfo:
        raw = (metadata.get("tokenizer.chat_template") or "").strip()
        arch = (metadata.get("general.architecture") or "").lower()
        name = metadata.get("general.name") or ""
        tok = metadata.get("tokenizer.ggml.model") or ""
        if raw:
            info = TemplateInfo(self._classify(raw, arch), "gguf_metadata", "high", "DETECTED", raw, arch, name, tok)
            self.last = info
            return info
        if arch:
            kind = self._classify("", arch)
            if kind != "unknown":
                info = TemplateInfo(kind, "general.architecture", "medium", "DETECTED", "", arch, name, tok)
                self.last = info
                return info
        info = TemplateInfo("plain", "none", "low", "UNKNOWN", "", arch, name, tok)
        self.last = info
        return info

    def _classify(self, raw: str, arch: str) -> str:
        low = (raw or "").lower()
        if "<|im_start|>" in low or "chatml" in low:
            return "chatml"
        if "<|start_header_id|>" in low or "llama3" in arch:
            return "llama3"
        if "[inst]" in low or arch in ("llama", "llama2"):
            return "llama2"
        if "<start_of_turn>" in low or "gemma" in arch:
            return "gemma"
        if "<|user|>" in low or "phi" in arch:
            return "phi3"
        if "qwen" in arch:
            return "chatml"
        if raw.strip():
            return "embedded"
        return "unknown"

    def resolve(self, name: str, model_path=None) -> ChatTemplate:
        meta = self.inspect(model_path) if model_path else {}
        if (name or "auto").lower() in ("auto", "", "detect"):
            return ChatTemplate(self.detect(meta))
        forced = TemplateInfo(name.lower(), "cli", "high", "DETECTED", meta.get("tokenizer.chat_template") or "", meta.get("general.architecture") or "", meta.get("general.name") or "", "")
        self.last = forced
        return ChatTemplate(forced)

    def explain(self) -> str:
        if not self.last:
            return "no inspection yet"
        i = self.last
        return f"state={i.state} name={i.name} source={i.source} confidence={i.confidence} arch={i.architecture or '-'} model={i.model_name or '-'} tokenizer={i.tokenizer or '-'}"


TEMPLATES = {"generic": "plain", "chatml": "chatml", "llama2": "llama2", "llama3": "llama3"}
