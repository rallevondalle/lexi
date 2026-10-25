#!/usr/bin/env python3
"""Build Lexi.alfredworkflow: writes info.plist and zips it with the scripts and icon.

  ./build.py            build alfred/dist/Lexi.alfredworkflow
  ./build.py --install  build it and open it, which asks Alfred to import it
"""

import os
import plistlib
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["info.plist", "icon.png", "run.sh", "lexi-view", "lexi_alfred.py"]
CMD, ALT = 1 << 20, 1 << 19
CTRL_ALT_CMD = (1 << 18) | ALT | CMD
KEY_D = 2

(FILTER, WORD, VIEW, WIKTIONARY, COPY, HOTKEY, UNIVERSAL, SETTINGS, APPLY, NOTIFY, REOPEN, REOPENED,
 BACK, SEARCH, SEARCHED) = (f"6C1E0A3B-0000-4000-8000-0000000000{i:02}" for i in range(1, 16))

objects = [
    {"uid": FILTER, "type": "alfred.workflow.input.scriptfilter", "version": 3, "config": {
        "keyword": "{var:keyword}",
        "title": "lexi",
        "subtext": "",
        "runningsubtext": "…",
        "withspace": True,
        "argumenttype": 1,
        "argumenttrimmode": 0,
        "argumenttreatemptyqueryasnil": False,
        "alfredfiltersresults": False,
        "alfredfiltersresultsmatchmode": 0,
        "queuemode": 1,
        "queuedelaymode": 0,
        "queuedelaycustom": 3,
        "queuedelayimmediatelyinitially": True,
        "type": 0,
        "scriptargtype": 1,
        "escaping": 102,
        "script": './run.sh filter "$1"',
        "scriptfile": "",
        "skipuniversalaction": True,
    }},
    {"uid": WORD, "type": "alfred.workflow.utility.argument", "version": 1, "config": {
        "argument": "{query}",
        "passthroughargument": False,
        "variables": {"word": "{query}"},
    }},
    {"uid": VIEW, "type": "alfred.workflow.userinterface.text", "version": 1, "config": {
        "inputtype": 1,
        "inputfile": "lexi-view",
        # No input field, so the text has focus and ↑↓ PgUp PgDn scroll it.
        "scriptinput": 0,
        "outputmode": 1,
        "behaviour": 2,
        "fontmode": 0,
        "fontsizing": 0,
        "spellchecking": 0,
        "stackview": False,
        "loadingtext": "…",
        "footertext": "",
    }},
    # ↩ in the view goes back to an empty search, which lists the words looked up so far.
    {"uid": BACK, "type": "alfred.workflow.utility.argument", "version": 1, "config": {
        "argument": "",
        "passthroughargument": False,
        "variables": {},
    }},
    {"uid": SEARCH, "type": "alfred.workflow.output.callexternaltrigger", "version": 1, "config": {
        "externaltriggerid": "search",
        "workflowbundleid": "self",
        "passinputasargument": True,
        "passvariables": False,
    }},
    {"uid": SEARCHED, "type": "alfred.workflow.trigger.external", "version": 1, "config": {
        "triggerid": "search",
        "availableviaurlhandler": False,
    }},
    {"uid": WIKTIONARY, "type": "alfred.workflow.action.openurl", "version": 1, "config": {
        "url": "{query}",
        "browser": "",
        "spaces": "",
        "skipqueryencode": True,
        "skipvarencode": False,
    }},
    {"uid": COPY, "type": "alfred.workflow.output.clipboard", "version": 3, "config": {
        "clipboardtext": "{query}",
        "autopaste": False,
        "ignoredynamicplaceholders": True,
        "transient": False,
    }},
    {"uid": HOTKEY, "type": "alfred.workflow.trigger.hotkey", "version": 2, "config": {
        "hotkey": KEY_D,
        "hotmod": CTRL_ALT_CMD,
        "hotstring": "D",
        "action": 0,
        "argument": 1,
        "modsmode": 0,
        "relatedAppsMode": 0,
        "leftcursor": False,
    }},
    {"uid": SETTINGS, "type": "alfred.workflow.input.scriptfilter", "version": 3, "config": {
        "keyword": "{var:settings_keyword}",
        "title": "lexi",
        "subtext": "",
        "runningsubtext": "…",
        "withspace": True,
        "argumenttype": 1,
        "argumenttrimmode": 0,
        "argumenttreatemptyqueryasnil": False,
        "alfredfiltersresults": False,
        "alfredfiltersresultsmatchmode": 0,
        "queuemode": 1,
        "queuedelaymode": 0,
        "queuedelaycustom": 3,
        "queuedelayimmediatelyinitially": True,
        "type": 0,
        "scriptargtype": 1,
        "escaping": 102,
        "script": './run.sh settings "$1"',
        "scriptfile": "",
        "skipuniversalaction": True,
    }},
    {"uid": APPLY, "type": "alfred.workflow.action.script", "version": 2, "config": {
        "type": 0,
        "scriptargtype": 1,
        "escaping": 102,
        "script": './run.sh apply "$1"',
        "scriptfile": "",
        "concurrently": False,
    }},
    {"uid": NOTIFY, "type": "alfred.workflow.output.notification", "version": 1, "config": {
        "title": "lexi",
        "text": "{query}",
        "onlyshowifquerypopulated": True,
        "lastpathcomponent": False,
        "removeextension": False,
    }},
    # After a change the settings open again, so several can be made in a row.
    {"uid": REOPEN, "type": "alfred.workflow.output.callexternaltrigger", "version": 1, "config": {
        "externaltriggerid": "settings",
        "workflowbundleid": "self",
        "passinputasargument": False,
        "passvariables": False,
    }},
    {"uid": REOPENED, "type": "alfred.workflow.trigger.external", "version": 1, "config": {
        "triggerid": "settings",
        "availableviaurlhandler": False,
    }},
    {"uid": UNIVERSAL, "type": "alfred.workflow.trigger.universalaction", "version": 1, "config": {
        "name": "lexi",
        "acceptstext": True,
        "acceptsfiles": False,
        "acceptsurls": False,
        "acceptsmulti": 0,
    }},
]


def link(dest, modifiers=0):
    return {"destinationuid": dest, "modifiers": modifiers, "modifiersubtext": "", "vitoclose": False}


connections = {
    FILTER: [link(WORD), link(WIKTIONARY, CMD), link(COPY, ALT)],
    # The selected word goes into the search, so nothing selected still lands somewhere useful.
    HOTKEY: [link(SEARCH)],
    UNIVERSAL: [link(WORD)],
    WORD: [link(VIEW)],
    VIEW: [link(BACK)],
    BACK: [link(SEARCH)],
    SEARCHED: [link(FILTER)],
    SETTINGS: [link(APPLY)],
    APPLY: [link(NOTIFY), link(REOPEN)],
    REOPENED: [link(SETTINGS)],
}

positions = {FILTER: (50, 50), HOTKEY: (50, 200), UNIVERSAL: (50, 330), WORD: (300, 200),
             VIEW: (470, 180), WIKTIONARY: (300, 50), COPY: (470, 50),
             SETTINGS: (50, 480), APPLY: (300, 480), NOTIFY: (470, 430), REOPEN: (470, 560), REOPENED: (50, 610),
             BACK: (640, 180), SEARCH: (800, 180), SEARCHED: (50, -80)}

README = """Offline dictionary from Wiktionary and Open English WordNet, using lexi.

Keyword (default "ord"): words appear as you type, each with its first definition.
  ↩ full entry, scrolled with ↑↓ PgUp PgDn; ↩ again goes back for the next word

Every word opened is saved to ~/.local/share/lexi/history.tsv, and the keyword on its own
lists them, newest first, with how often and when you looked each one up.
  ⌘↩ open in Wiktionary · ⌥↩ copy the definition · ⌘L large type · ⌘Y Quick Look

⌃⌥⌘D searches for the selected text (nothing selected: the words looked up so far).
The Universal Action "lexi" looks up any text.

Settings keyword (default "lexi"): the interface language, WordNet on or off, and the dictionaries.
Type to find any of Wiktionary's languages; ↵ downloads it in the background or removes it.

Needs lexi: https://github.com/rallevondalle/lexi (./install.sh).
The interface follows lexi's language setting (lexi settings)."""

info = {
    "bundleid": "com.rallevondalle.lexi",
    "name": "lexi",
    "description": "Offline dictionary: Wiktionary and WordNet",
    "createdby": "Rasmus Kjærbo",
    "webaddress": "https://github.com/rallevondalle/lexi",
    "version": "1.0",
    "category": "Productivity",
    "readme": README,
    "disabled": False,
    "objects": objects,
    "connections": connections,
    "uidata": {uid: {"xpos": x, "ypos": y} for uid, (x, y) in positions.items()},
    "variablesdontexport": [],
    "userconfigurationconfig": [
        {"type": "textfield", "variable": "keyword", "label": "Keyword",
         "description": "Type this in Alfred, then the word",
         "config": {"default": "ord", "placeholder": "ord", "required": True, "trim": True}},
        {"type": "textfield", "variable": "settings_keyword", "label": "Settings keyword",
         "description": "Interface language, WordNet and dictionaries",
         "config": {"default": "lexi", "placeholder": "lexi", "required": True, "trim": True}},
        {"type": "textfield", "variable": "lexi_path", "label": "Path to lexi",
         "description": "Leave empty for ~/.local/bin/lexi",
         "config": {"default": "", "placeholder": "~/.local/bin/lexi", "required": False, "trim": True}},
    ],
}


def main():
    with open(os.path.join(HERE, "info.plist"), "wb") as f:
        plistlib.dump(info, f)
    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    target = os.path.join(dist, "Lexi.alfredworkflow")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            path = os.path.join(HERE, name)
            info_ = zipfile.ZipInfo.from_file(path, name)
            with open(path, "rb") as f:
                z.writestr(info_, f.read(), zipfile.ZIP_DEFLATED)
    print(target)
    if "--install" in sys.argv[1:]:
        subprocess.run(["open", target], check=True)


if __name__ == "__main__":
    main()
