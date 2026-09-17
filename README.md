# SUE — Neural Link CLI

Matrix-style wrapper around local llama.cpp (`llama-cli`) for a GGUF model.

```
python3 -m sue
python3 -m sue --model ~/models/2b.gguf --template auto
python3 -m sue --diagnose
python3 -m sue --model-info
```

## Layout

```
sue/
  main.py cli.py config.py model.py llama.py
  prompts.py conversation.py mood.py
  terminal.py matrix.py commands.py exceptions.py
```

## Config

`~/.config/sue/config.yaml` (created on first run). CLI flags override.

## Templates

`auto` (GGUF metadata → chatml/llama2 else generic), `generic`, `chatml`, `llama2`.

## Commands

`/clear /model /template /system /temp /context /save /load /help /quit`

## Deps

Stdlib only. Optional PyYAML. Requires `llama-cli` on PATH and a GGUF at `~/models/2b.gguf` (or `--model`).

## Install

```
bash install.sh
```
