#!/usr/bin/env bash
# Remove lexi. Keeps the dictionary database unless --purge is given.
#
#   ./uninstall.sh [--purge]

set -euo pipefail

BIN_DIR="${LEXI_BIN_DIR:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/lexi"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/lexi"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lexi"
bindings="$HOME/.config/hypr/bindings.lua"

rm -f "$BIN_DIR/lexi"
rm -rf "$STATE_DIR"

if [[ -f $bindings ]] && grep -q -- '-- lexi' "$bindings"; then
  cp "$bindings" "$bindings.bak.$(date +%s)"
  grep -v -e '^-- lexi: ' -e '-- lexi$' "$bindings" >"$bindings.new" && mv "$bindings.new" "$bindings"
  hyprctl reload >/dev/null 2>&1 || true
  echo "Removed the keybinding from $bindings"
fi

if [[ ${1:-} == --purge ]]; then
  rm -rf "$DATA_DIR" "$CONFIG_DIR"
  echo "Removed lexi, its dictionary and its config."
else
  echo "Removed lexi. The dictionary is still in $DATA_DIR (use --purge to delete it)."
fi
