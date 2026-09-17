#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.config/sue" "$HOME/.local/state/sue" "$HOME/.local/bin"
if [[ ! -f "$HOME/.config/sue/config.yaml" ]]; then
  cp "$ROOT/config.yaml.example" "$HOME/.config/sue/config.yaml" 2>/dev/null || true
fi
cat > "$HOME/.local/bin/sue" <<'EOF'
#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
# Prefer repo checkout if present via SUE_ROOT
export PYTHONPATH="${SUE_ROOT:-.}:${PYTHONPATH:-}"
exec python3 -m sue "$@"
EOF
chmod +x "$HOME/.local/bin/sue" "$ROOT/install.sh"
echo "SUE installed. Ensure $HOME/.local/bin is on PATH."
echo "Run from repo: PYTHONPATH=. python3 -m sue"
