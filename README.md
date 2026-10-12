# lexi

A fast, offline English dictionary for Linux and macOS. Press a key, type a word and get a clean popup with definitions, pronunciation, examples and etymology. It also works as a plain terminal command, and on macOS as a [Raycast extension](raycast/).

![lexi showing "tesselate"](docs/screenshot.png)

- **Offline:** about 1.5 million entries from [Wiktionary](https://en.wiktionary.org) and [Open English WordNet](https://en-word.net). Lookups take well under 0.1 seconds.
- **Modern:** Wiktionary is current, so it has words like *doomscrolling* and *rizz*.
- **Follows references:** a word that only says "Alternative spelling of X" or "past tense of X" shows X's full definitions underneath.
- **Forgives typos:** *arbitrtion* suggests *arbitration* and shows it.
- **Fits the window to the content** on Hyprland and [Omarchy](https://omarchy.org): floating, centered and as tall as the entry needs.
- **No dependencies** beyond Python 3, which is already on most systems.

## Install

```bash
git clone https://github.com/rallevondalle/lexi.git
cd lexi
./install.sh
```

The installer:

1. Copies `lexi` to `~/.local/bin`.
2. Downloads the dictionaries (about 540 MB) and builds a local database (about 360 MB). This takes a few minutes, and the downloads are not kept.
3. On Omarchy, binds **SUPER + ALT + D** to the popup. On other desktops it tells you what to bind.

Options: `--lang da` for a Danish interface, `--no-data` to skip the download, and `--no-keybinding`.

## Usage

```bash
lexi serendipity        # print the definition in the terminal
lexi                    # ask for a word and show it in a popup
lexi --open serendipity # open the popup for a word directly
lexi update             # refresh the dictionaries from the latest Wiktionary dump
lexi --json serendipity # the lookup as JSON, for integrations
lexi --complete seren   # words starting with "seren", as JSON
```

In the popup, scroll with the arrow keys or the mouse, search with `/` and close with `q` or `Esc`.

## Works with

| | Terminal lookups | Popup | Popup sized to content |
|---|---|---|---|
| Omarchy | ✓ | ✓ | ✓ |
| Hyprland | ✓ | ✓ | ✓ |
| Other Linux desktops | ✓ | ✓ (normal terminal window) | |
| macOS | ✓ | ✓ with [Raycast](raycast/), or Terminal.app | Raycast |

lexi asks for the word using the first of these it finds: `omarchy-menu-input`, `fuzzel`, `wofi`, `tofi`, `rofi`, `bemenu`, `zenity`, `kdialog` or, on macOS, a native dialog. If none is available, it asks inside the popup.

The popup opens in the first available terminal: `foot`, `kitty`, `alacritty`, `ghostty`, `wezterm`, `xdg-terminal-exec`, `gnome-terminal`, `konsole` or `xterm`, and on macOS Terminal.app.

### macOS and Raycast

On macOS the nicest way to use lexi is the [Raycast extension](raycast/): words appear as you type, and the definition shows in Raycast's detail pane. It can also look up the word you have selected in any app. Install lexi with `./install.sh` first, then see [raycast/README.md](raycast/README.md).

## Configuration

`~/.config/lexi/config`:

```ini
lang = en          # interface language: en or da
font_size = 12     # popup font size
width = 76         # text column width
terminal = kitty   # preferred terminal for the popup
```

Each setting can also be set as an environment variable, e.g. `LEXI_LANG=da`.

## Uninstall

```bash
./uninstall.sh          # keeps the dictionary database
./uninstall.sh --purge  # removes everything
```

## Data and licenses

lexi is MIT licensed. The dictionary data is downloaded from its sources and is not part of this repository:

- Wiktionary content via [kaikki.org](https://kaikki.org) (Wiktextract), licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and GFDL.
- [Open English WordNet](https://github.com/globalwordnet/english-wordnet), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
