"""Prompt templates. No assumed chat format."""

from __future__ import annotations

from typing import Protocol

class PromptTemplate(Protocol):
    name: str
    def format_system(self, system_prompt: str) -> str: ...
    def format_user(self, user_prompt: str) -> str: ...
    def format_assistant(self) -> str: ...
    def format_conversation(self, messages: list) -> str: ...

class GenericTemplate:
    name = "generic"
    def format_system(self, system_prompt: str) -> str:
        return f"### Instruction\n{system_prompt.strip()}\n\n"
    def format_user(self, user_prompt: str) -> str:
        return f"### User\n{user_prompt.strip()}\n\n"
    def format_assistant(self) -> str:
        return "### Assistant\n"
    def format_conversation(self, messages: list) -> str:
        parts = []
        for m in messages:
            role, content = m.get("role", ""), m.get("content", "")
            if role == "system":
                parts.append(self.format_system(content))
            elif role == "user":
                parts.append(self.format_user(content))
            elif role == "assistant":
                parts.append(f"### Assistant\n{content.strip()}\n\n")
        parts.append(self.format_assistant())
        return "".join(parts)

class ChatMLTemplate:
    name = "chatml"
    def format_system(self, system_prompt: str) -> str:
        return f"<|im_start|>system\n{system_prompt.strip()}<|im_end|>\n"
    def format_user(self, user_prompt: str) -> str:
        return f"<|im_start|>user\n{user_prompt.strip()}<|im_end|>\n"
    def format_assistant(self) -> str:
        return "<|im_start|>assistant\n"
    def format_conversation(self, messages: list) -> str:
        parts = []
        for m in messages:
            role, content = m.get("role", ""), m.get("content", "")
            if role == "system":
                parts.append(self.format_system(content))
            elif role == "user":
                parts.append(self.format_user(content))
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{content.strip()}<|im_end|>\n")
        parts.append(self.format_assistant())
        return "".join(parts)

class Llama2Template:
    name = "llama2"
    def format_system(self, system_prompt: str) -> str:
        return f"<<SYS>>\n{system_prompt.strip()}\n<</SYS>>\n\n"
    def format_user(self, user_prompt: str) -> str:
        return f"[INST] {user_prompt.strip()} [/INST] "
    def format_assistant(self) -> str:
        return ""
    def format_conversation(self, messages: list) -> str:
        sys_txt = ""
        parts = []
        pending_user = None
        for m in messages:
            role, content = m.get("role", ""), m.get("content", "")
            if role == "system":
                sys_txt = self.format_system(content)
            elif role == "user":
                pending_user = content
            elif role == "assistant" and pending_user is not None:
                prefix, sys_txt = sys_txt, ""
                parts.append(f"{prefix}[INST] {pending_user.strip()} [/INST] {content.strip()} </s>")
                pending_user = None
        if pending_user is not None:
            parts.append(f"{sys_txt}[INST] {pending_user.strip()} [/INST] ")
        elif not parts:
            parts.append(sys_txt)
        return "\n".join(parts)

TEMPLATES = {
    "generic": GenericTemplate(),
    "chatml": ChatMLTemplate(),
    "llama2": Llama2Template(),
}

class TemplateDetector:
    def detect_from_gguf(self, model_path) -> str | None:
        try:
            from sue.model import read_gguf_text_keys
            keys = read_gguf_text_keys(model_path)
        except Exception:
            return None
        tmpl = keys.get("tokenizer.chat_template") or keys.get("chat_template")
        if not tmpl:
            return None
        low = tmpl.lower()
        if "im_start" in low or "chatml" in low:
            return "chatml"
        if "[inst]" in low or "sys>>" in low:
            return "llama2"
        return None

    def resolve(self, name: str, model_path=None):
        name = (name or "auto").lower()
        if name == "auto":
            detected = self.detect_from_gguf(model_path) if model_path else None
            return TEMPLATES.get(detected or "generic")
        return TEMPLATES.get(name, TEMPLATES["generic"])
