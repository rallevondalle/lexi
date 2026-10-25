# lexi for Alfred

An [Alfred](https://www.alfredapp.com) workflow for [lexi](https://github.com/rallevondalle/lexi), a fast, offline dictionary built from Wiktionary and Open English WordNet.

- **Look up a word:** type `ord` and a word. Matching words appear as you type, each with its pronunciation and first definition. Typos get suggestions.
- **Full entry:** ↩ opens the whole entry with senses, examples, translations and etymology. ↑↓ and PgUp PgDn scroll it, and ↩ again goes back for the next word.
- **Your words:** every word you open is saved, and `ord` on its own lists them, newest first, with how often and when you looked each one up. A record of the vocabulary you are building.
- **Selected text:** select a word in any app and press ⌃⌥⌘D to search for it, or use the Universal Action "lexi" on any text.
- **Settings:** type `lexi` to switch the interface between English and Danish, turn WordNet on or off, and download or remove dictionaries for any language Wiktionary has.

The workflow needs Alfred 5.5 or newer with the Powerpack.

## Requirements

The workflow calls lexi, which needs Python 3 (included with the Xcode Command Line Tools) and a one-time download of the dictionaries:

```bash
git clone https://github.com/rallevondalle/lexi.git
cd lexi
./install.sh            # or ./install.sh --lang da for a Danish interface and dictionary
```

This installs `lexi` to `~/.local/bin` and builds the dictionary database in `~/.local/share/lexi` (about 360 MB). If you install lexi somewhere else, set **Path to lexi** in the workflow's configuration.

## Install the workflow

```bash
cd lexi/alfred
./build.py --install
```

This builds `dist/Lexi.alfredworkflow` and opens it, and Alfred asks to import it.

Alfred removes hotkeys from workflows it imports, so set ⌃⌥⌘D (or any other) yourself: open the workflow in Alfred Preferences, double-click the Hotkey object and press the keys.

## Keys

| | |
|---|---|
| ↩ | full entry |
| ⌘↩ | open in Wiktionary |
| ⌥↩ | copy the definition |
| ⌘C | copy the word |
| ⌘L | the definition in large type |
| ⌘Y | Quick Look the Wiktionary page |

In the full entry, ↑↓ and PgUp PgDn scroll, ↩ goes back to the search and Esc closes Alfred.

## The word list

Each word you open is a line in `~/.local/share/lexi/history.tsv`: the time, a tab and the word. It is plain text, so it can be turned into flash cards or read in any editor. `./uninstall.sh` keeps it; `./uninstall.sh --purge` deletes it with the dictionaries.

## Configuration

| | |
|---|---|
| Keyword | `ord` by default |
| Settings keyword | `lexi` by default |
| Path to lexi | empty means `~/.local/bin/lexi` |

The interface language follows lexi's own setting, which the settings keyword changes.

Downloading a language runs in the background, and the settings list shows its progress. It takes a few minutes, because lexi downloads the English Wiktionary again for the translations, and a notification says when it is done.
