#!/usr/bin/env bash
# Install lexi: copies the script, builds the dictionary, and on Omarchy adds a SUPER+ALT+D keybinding.
#
#   ./install.sh [--lang en|da] [--no-data] [--no-keybinding]

set -euo pipefail

BIN_DIR="${LEXI_BIN_DIR:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lexi"
DATA_DB="${XDG_DATA_HOME:-$HOME/.local/share}/lexi/lexi.db"
KEY="SUPER + ALT + D"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

lang=""
build_data=true
keybinding=true
while (( $# )); do
  case "$1" in
    --lang) lang="${2:?--lang needs a value}"; shift ;;
    --no-data) build_data=false ;;
    --no-keybinding) keybinding=false ;;
    -h|--help) sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }

if ! command -v python3 >/dev/null; then
  echo "lexi needs Python 3. Install it with your package manager and run this again." >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
  echo "lexi needs Python 3.8 or newer." >&2
  exit 1
fi
command -v less >/dev/null || note "Tip: install 'less' for scrolling in the popup."

say "Installing lexi to $BIN_DIR/lexi"
mkdir -p "$BIN_DIR"
install -m 755 "$HERE/lexi" "$BIN_DIR/lexi"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) note "$BIN_DIR is not on your PATH. Add it, or call lexi as $BIN_DIR/lexi." ;;
esac

if [[ -n $lang ]]; then
  mkdir -p "$CONFIG_DIR"
  if [[ -f $CONFIG_DIR/config ]] && grep -q '^lang' "$CONFIG_DIR/config"; then
    sed -i "s/^lang.*/lang = $lang/" "$CONFIG_DIR/config"
  else
    echo "lang = $lang" >>"$CONFIG_DIR/config"
  fi
  say "Interface language set to '$lang' in $CONFIG_DIR/config"
fi

if $build_data; then
  if [[ -f $DATA_DB ]]; then
    say "Dictionary already built ($DATA_DB). Run 'lexi update' to refresh it."
  else
    say "Building the dictionary"
    "$BIN_DIR/lexi" update
  fi
fi

if $keybinding; then
  bindings="$HOME/.config/hypr/bindings.lua"
  if command -v omarchy >/dev/null && [[ -f $bindings ]]; then
    if grep -q -- '-- lexi$' "$bindings"; then
      say "Omarchy keybinding already present."
    elif omarchy menu keybindings --print 2>/dev/null | grep -q "^SUPER ALT + D "; then
      say "SUPER+ALT+D is already taken, so no keybinding was added."
      note "Add one to $bindings, for example:"
      note "o.bind(\"SUPER + CTRL + D\", \"Dictionary\", \"$BIN_DIR/lexi\") -- lexi"
    else
      cp "$bindings" "$bindings.bak.$(date +%s)"
      printf '\n-- lexi: offline dictionary\no.bind("%s", "Dictionary", "%s") -- lexi\n' "$KEY" "$BIN_DIR/lexi" >>"$bindings"
      hyprctl reload >/dev/null 2>&1 || true
      say "Added $KEY to $bindings"
    fi
  elif [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    say "Hyprland detected. Add a keybinding yourself, e.g. in hyprland.conf:"
    note "bind = SUPER ALT, D, exec, $BIN_DIR/lexi"
  else
    say "Bind a key to '$BIN_DIR/lexi' in your desktop's keyboard shortcut settings to get the popup."
  fi
fi

say "Done. Try: lexi serendipity"
