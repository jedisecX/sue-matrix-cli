"""Entry: python3 -m sue"""

from __future__ import annotations

import sys

from sue.config import load_config
from sue.cli import diagnose, print_model_info, run_repl


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cfg = load_config(argv)
    if getattr(cfg, "_diagnose", False):
        return diagnose(cfg)
    if getattr(cfg, "_model_info", False):
        return print_model_info(cfg)
    return run_repl(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
