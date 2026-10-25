"""Alfred front end for lexi.

  lexi_alfred.py filter QUERY   Script Filter JSON: matching words, each with its first definition
  lexi_alfred.py view [WORD]    Text View JSON: the full entry as Markdown (WORD, else $word)
  lexi_alfred.py settings QUERY Script Filter JSON: interface language, WordNet and dictionaries
  lexi_alfred.py apply ACTION   carry out a settings row (set:KEY:VALUE, add:NAME, remove:NAME, stop)

lexi is loaded as a module rather than run once per word: starting Python is what costs time,
so one process answers a whole keystroke.

Every word opened in the Text View is added to history.tsv in lexi's data folder (time, tab, word),
and an empty query lists those words, newest first: a record of the vocabulary looked up.
"""

import importlib.machinery
import importlib.util
import json
import os
import re
import sys
import time

LEXI = os.path.expanduser(os.environ.get("lexi_path") or "~/.local/bin/lexi")
SUGGESTIONS = 8  # words that get a definition as their subtitle; the rest show the word only
HISTORY_SHOWN = 50
STRINGS = {
    "en": {
        "missing": "lexi isn't installed",
        "missing_sub": "Install it with ./install.sh from the lexi repository, or set its path in the workflow",
        "type": "Type a word",
        "type_sub": "Definitions appear as you type",
        "open": "↩ full entry · ⌘↩ Wiktionary · ⌥↩ copy definition",
        "footer": "↑↓ PgUp PgDn scroll · ↩ next word · esc close",
        "copy": "Copy the definition",
        "looked_up": "{n}× · last {when}",
        "switch_to": "↵ switch to {}",
        "always_en": "English · always there",
        "more": "Type to find more of Wiktionary's {} languages",
        "size": "about 550 MB, a few minutes",
    },
    "da": {
        "missing": "lexi er ikke installeret",
        "missing_sub": "Installér den med ./install.sh fra lexi-repoet, eller angiv stien i workflowen",
        "type": "Skriv et ord",
        "type_sub": "Forklaringerne kommer, mens du skriver",
        "open": "↩ hele opslaget · ⌘↩ Wiktionary · ⌥↩ kopiér forklaringen",
        "footer": "↑↓ PgUp PgDn ruller · ↩ nyt ord · esc luk",
        "copy": "Kopiér forklaringen",
        "looked_up": "{n}× · senest {when}",
        "switch_to": "↵ skift til {}",
        "always_en": "Engelsk · altid med",
        "more": "Skriv for at finde flere af Wiktionarys {} sprog",
        "size": "ca. 550 MB, et par minutter",
    },
}


def load_lexi():
    if not os.path.exists(LEXI):
        return None
    loader = importlib.machinery.SourceFileLoader("lexi", LEXI)
    spec = importlib.util.spec_from_loader("lexi", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


lexi = load_lexi()
LANG = lexi.CFG["lang"] if lexi else "en"
S = STRINGS.get(LANG, STRINGS["en"])
T = lexi.T if lexi else {}
HISTORY = os.path.join(lexi.DATA_DIR, "history.tsv") if lexi else None


def wiktionary_url(word):
    from urllib.parse import quote
    return "https://en.wiktionary.org/wiki/" + quote(word.replace(" ", "_"))


def first_gloss(result):
    """The first sense, prefixed with the section it comes from when that isn't plain English."""
    for section in result["sections"]:
        for entry in section["entries"]:
            if entry["senses"]:
                gloss = entry["senses"][0]["gloss"]
                if section["kind"] in ("translation", "foreign", "native", "explained"):
                    return f"{section['title']}: {gloss}"
                return gloss
    return ""


def plain_text(result):
    if not result["found"]:
        return result["query"]
    out = [result["headword"]]
    for section in result["sections"]:
        out += ["", section["title"]]
        for entry in section["entries"]:
            out.append((entry["pos"] or "").upper())
            num = 0
            for sense in entry["senses"]:
                if sense["depth"] == 0:
                    num += 1
                    out.append(f"{num}. {sense['gloss']}")
                else:
                    out.append(f"   - {sense['gloss']}")
    return "\n".join(out)


# ---------- Script Filter ----------

def item(word, result=None):
    found = result is not None and result["found"]
    entry = {
        "uid": word,
        "title": word,
        "subtitle": first_gloss(result) if found else S["open"],
        "arg": word,
        "autocomplete": word,
        "quicklookurl": wiktionary_url(word),
        "text": {"copy": word, "largetype": plain_text(result) if found else word},
        "variables": {"word": word},
        "mods": {
            "cmd": {"arg": wiktionary_url(word), "subtitle": wiktionary_url(word)},
            "alt": {"arg": plain_text(result) if found else word, "subtitle": S["copy"]},
        },
    }
    if result and result["ipa"]:
        # Wiktionary often lists several pronunciations; the first fits in the title.
        entry["title"] += "   " + result["ipa"].split(" ")[0]
    return entry


def script_filter(query):
    query = query.strip()
    if lexi is None:
        return {"items": [{"title": S["missing"], "subtitle": S["missing_sub"], "valid": False}]}
    if not query:
        return {"items": history_items() or [{"title": S["type"], "subtitle": S["type_sub"], "valid": False}]}
    # complete() falls back to spelling suggestions, so "arbitrtion" offers "arbitration".
    words = lexi.complete(query)
    items = []
    for i, word in enumerate(words):
        result = lexi.collect(word) if i < SUGGESTIONS else None
        if result is not None and not result["found"]:
            continue
        if result is not None and result["suggestions"]:
            word = result["headword"]
        if any(it["uid"] == word for it in items):
            continue
        items.append(item(word, result))
    if not items:
        items = [{"title": query, "subtitle": T["nothing"], "valid": False}]
    return {"items": items}


# ---------- history ----------

def record(word):
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{word}\n")


def history():
    """[(word, times looked up, last time)], the most recent first."""
    words = {}
    try:
        with open(HISTORY, encoding="utf-8") as f:
            for line in f:
                when, _, word = line.rstrip("\n").partition("\t")
                if word:
                    count = words.pop(word, (0, None))[0]
                    words[word] = (count + 1, when)  # popping first keeps the dict in order of last use
    except OSError:
        return []
    return [(word, count, when) for word, (count, when) in reversed(words.items())]


def history_items():
    items = []
    for i, (word, count, when) in enumerate(history()[:HISTORY_SHOWN]):
        result = lexi.collect(word) if i < SUGGESTIONS else None
        entry = item(word, result)
        try:
            when = time.strftime("%-d/%-m %H:%M", time.strptime(when, "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            pass
        looked_up = S["looked_up"].format(n=count, when=when)
        gloss = first_gloss(result) if result and result["found"] else ""
        entry["subtitle"] = f"{looked_up} · {gloss}" if gloss else looked_up
        items.append(entry)
    return items


# ---------- Text View ----------

def escape(text):
    return re.sub(r"([\\`*_\[\]<>#])", r"\\\1", text)


def gloss_md(text):
    """Italicise a leading "(label)" the way the terminal version colours it."""
    m = re.match(r"^(\([^)]*\))\s*(.*)$", text)
    return f"*{escape(m.group(1))}* {escape(m.group(2))}" if m else escape(text)


def entries_md(entries, base):
    out = []
    for entry in entries:
        label = (entry["pos"] or "").upper()
        if entry["word"].lower() == base.lower() and entry["word"] != base:
            label += f"  {escape(entry['word'])}"
        forms = f"  {escape(entry['forms'])}" if entry.get("forms") else ""
        out += ["", f"**{label}**{forms}", ""]
        num = 0
        for sense in entry["senses"]:
            if sense["depth"] == 0:
                num += 1
                out.append(f"{num}. {gloss_md(sense['gloss'])}")
            else:
                out.append(f"    - {gloss_md(sense['gloss'])}")
            if sense["example"]:
                indent = "    " if sense["depth"] == 0 else "        "
                out.append(f"{indent}*“{escape(sense['example'])}”*")
    return out


def markdown(result):
    if result.get("error") == "no_db":
        return f"# {T['no_db']}\n\n{T['run_update']}"
    if not result["found"]:
        return f"# {escape(result['query'])}\n\n{T['nothing']}"
    out = []
    if result["suggestions"]:
        out += [f"*{escape(result['query'])} {T['not_found']}. {T['did_you_mean']}"
                f"{', '.join(map(escape, result['suggestions']))}*", ""]
    headword = result["headword"]
    out.append(f"# {escape(headword)}")
    if result["ipa"]:
        out += ["", f"`{result['ipa']}`"]
    if result["untranslated"]:
        out += ["", f"*{T['no_translation'].format(', '.join(result['untranslated']))}*"]
    sections = result["sections"]
    for section in sections:
        if len(sections) > 1 or section["kind"] in ("foreign", "translation", "native"):
            out += ["", "---", "", f"### {escape(section['title'])}"]
            if section["ipa"]:
                out += ["", f"`{section['ipa']}`"]
        base = headword if section["kind"] != "reference" else section["entries"][0]["word"]
        out += entries_md(section["entries"], base)
    if result["origins"]:
        out += ["", "---", "", f"### {T['origin'].capitalize()}", ""]
        out.append("\n\n".join(map(escape, result["origins"])))
    return "\n".join(out)


def text_view(typed):
    word = (typed or os.environ.get("word") or "").strip()
    footer = S["footer"]
    if lexi is None:
        return {"response": f"# {S['missing']}\n\n{S['missing_sub']}", "footer": footer}
    if not word:
        return {"response": f"# {S['type']}", "footer": footer}
    result = lexi.collect(word)
    if result["found"]:
        record(result["headword"])
    return {
        "response": markdown(result),
        "footer": footer,
        "behaviour": {"response": "replace", "scroll": "start", "inputfield": "clear"},
        "variables": {"word": result["headword"] or word},
    }


# ---------- settings ----------

LANGUAGES_SHOWN = 40  # languages listed before you type, the ones with the most senses first


def row(title, subtitle, arg, match=""):
    return {"uid": arg, "title": title, "subtitle": subtitle, "arg": arg, "match": match or title}


def matches(query, *names):
    return not query or any(query in n.lower() for n in names if n)


def settings(query):
    query = query.strip().lower()
    if lexi is None:
        return {"items": [{"title": S["missing"], "subtitle": S["missing_sub"], "valid": False}]}
    rows = []
    other = "da" if LANG == "en" else "en"
    title = f"{T['interface']}: {lexi.INTERFACES.get(LANG, LANG)}"
    if matches(query, title, "lexi", "sprog", "language"):
        rows.append(row(title, S["switch_to"].format(lexi.INTERFACES[other]), f"set:lang:{other}"))
    wordnet = lexi.wordnet_on()
    title = f"{T['wordnet']}: {T['on'] if wordnet else T['off']}"
    if matches(query, title, "wordnet"):
        rows.append(row(title, f"↵ {T['off'] if wordnet else T['on']}", f"set:wordnet:{'off' if wordnet else 'on'}"))

    progress = lexi.job_progress()
    downloading = (progress or {}).get("names", [])
    if lexi.job_running():
        label = T["indexing"] if (progress or {}).get("phase") == "indexing" else T["downloading"]
        pct = f" · {progress['pct']} %" if progress else ""
        names = ", ".join(map(lexi.lang_label, downloading)) or "…"
        rows.append(row(f"{label} {names}{pct}", T["will_stop"], "stop"))
    else:
        status = lexi.job_status()
        if status:
            rows.append({"title": status, "subtitle": lexi.JOB_LOG, "valid": False})

    installed = {lang["name"] for lang in lexi.installed_languages()}
    if matches(query, "english", "engelsk"):
        rows.append({"title": f"{S['always_en']}  ✓", "valid": False})
    for name in sorted(installed):
        if matches(query, name, lexi.lang_label(name)):
            rows.append(row(f"{lexi.lang_label(name)}  ✓ {T['installed']}", T["will_remove"], f"remove:{name}"))
    index = [lang for lang in lexi.language_index() if lang["name"] not in installed]
    shown = [lang for lang in index if matches(query, lang["name"], lexi.DA_NAMES.get(lang["name"]))]
    for lang in shown[:LANGUAGES_SHOWN if not query else 200]:
        name = lang["name"]
        if name in downloading:
            continue
        senses = T["senses"].format(max(1, round(lang["senses"] / 1000)))
        rows.append(row(lexi.lang_label(name), f"{T['will_add']} · {senses} · {S['size']}", f"add:{name}"))
    if not query and len(index) > LANGUAGES_SHOWN:
        rows.append({"title": S["more"].format(len(index) + len(installed)), "valid": False})
    out = {"items": rows}
    if lexi.job_running():
        out["rerun"] = 1  # the progress row counts up while the list is open
    return out


def apply(action):
    """Carry out one settings row and return what to tell the user."""
    kind, _, value = action.partition(":")
    if kind == "set":
        key, _, value = value.partition(":")
        lexi.save_config(key, value)
        if key == "lang":
            lexi.T = lexi.STRINGS[value]
            return f"{lexi.T['interface']}: {lexi.INTERFACES[value]}"
        return f"{lexi.T['wordnet']}: {lexi.T['on'] if value == 'on' else lexi.T['off']}"
    if kind == "remove":
        return T["removed"].format(lexi.lang_label(lexi.remove_language(value) or value))
    # Languages share the English download, so adding or stopping restarts it with the new set.
    running = (lexi.job_progress() or {}).get("names", [])
    lexi.stop_job()
    names = list(dict.fromkeys(running + [value])) if kind == "add" else []
    if names:
        lexi.start_job(names)
        return T["started"].format(", ".join(map(lexi.lang_label, names)))
    return T["stopped"].format(", ".join(map(lexi.lang_label, running)))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = " ".join(sys.argv[2:])
    if mode == "filter":
        out = script_filter(arg)
    elif mode == "view":
        out = text_view(arg)
    elif mode == "settings":
        out = settings(arg)
    elif mode == "apply":
        print(apply(arg))
        return
    else:
        sys.exit(__doc__)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
