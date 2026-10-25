#!/usr/bin/env bash
# Install lexi: copies the script, builds the dictionary, and on Omarchy adds a SUPER+ALT+D keybinding.
#
#   ./install.sh [--lang en|da] [--language NAME]... [--no-data] [--no-keybinding]

set -euo pipefail

BIN_DIR="${LEXI_BIN_DIR:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lexi"
DATA_DB="${XDG_DATA_HOME:-$HOME/.local/share}/lexi/lexi.db"
KEY="SUPER + ALT + D"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

lang=""
languages=()
build_data=true
keybinding=true
while (( $# )); do
  case "$1" in
    --lang) lang="${2:?--lang needs a value}"; shift ;;
    --language) languages+=("${2:?--language needs a value}"); shift ;;
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

say "Installing lexi to $BIN_DIR/lexi"
mkdir -p "$BIN_DIR"
install -m 755 "$HERE/lexi" "$BIN_DIR/lexi"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) note "$BIN_DIR is not on your PATH. Add it, or call lexi as $BIN_DIR/lexi." ;;
esac

set_config() {
  mkdir -p "$CONFIG_DIR"
  # Rewrite without sed -i, which differs between GNU and macOS.
  touch "$CONFIG_DIR/config"
  { grep -v "^$1" "$CONFIG_DIR/config" || true; echo "$1 = $2"; } >"$CONFIG_DIR/config.new"
  mv "$CONFIG_DIR/config.new" "$CONFIG_DIR/config"
}

if [[ -n $lang ]]; then
  set_config lang "$lang"
  say "Interface language set to '$lang' in $CONFIG_DIR/config"
fi
# A Danish interface comes with the Danish dictionary unless other languages were asked for.
if [[ $lang == da && ${#languages[@]} -eq 0 ]]; then
  languages=(Danish)
fi

if $build_data; then
  if [[ ! -f $DATA_DB ]]; then
    say "Building the dictionary"
    "$BIN_DIR/lexi" update "${languages[@]}"
  elif (( ${#languages[@]} )); then
    say "Adding ${languages[*]}"
    "$BIN_DIR/lexi" add "${languages[@]}"
  else
    say "Dictionary already built ($DATA_DB). Run 'lexi update' to refresh it."
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
  elif [[ $(uname) == Darwin ]]; then
    say "On macOS, use the Alfred workflow or the Raycast extension: see alfred/README.md or raycast/README.md"
  else
    say "Bind a key to '$BIN_DIR/lexi' in your desktop's keyboard shortcut settings to get the popup."
  fi
fi

say "Done. Try: lexi serendipity"
