# Lexi Dictionary for Raycast

A Raycast front end for [lexi](https://github.com/rallevondalle/lexi), a fast, offline English dictionary built from Wiktionary and Open English WordNet.

- **Look up Word:** type and see matching words instantly. The selected word's definition shows in the detail pane, with pronunciation, senses, examples and etymology.
- **Look up Selected Text:** select a word in any app and run the command, or give it a hotkey, to see its definition.

Words that only point elsewhere, such as "Alternative spelling of tessellate", show the full definition of the word they point to. Typos get suggestions.

## Requirements

The extension calls the `lexi` command, which needs Python 3 (included with the Xcode Command Line Tools) and a one-time download of the dictionaries:

```bash
git clone https://github.com/rallevondalle/lexi.git
cd lexi
./install.sh
```

This installs `lexi` to `~/.local/bin` and builds the dictionary database in `~/.local/share/lexi` (about 360 MB). If you install lexi somewhere else, set **Path to lexi** in the extension's preferences.

## Install the extension

Until it is in the Raycast Store:

```bash
cd lexi/raycast
npm install
npm run dev
```

`npm run dev` imports the extension into Raycast. It stays installed after you stop the command.

## Suggested hotkeys

- **Look up Word:** ⌥⌘D
- **Look up Selected Text:** ⌃⌥⌘D
