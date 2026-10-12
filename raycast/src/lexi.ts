import { getPreferenceValues } from "@raycast/api";
import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

export interface Sense {
  depth: number;
  gloss: string;
  example: string | null;
}

export interface Entry {
  word: string;
  pos: string | null;
  senses: Sense[];
}

export interface Section {
  title: string;
  kind: "main" | "reference" | "wordnet";
  ipa: string | null;
  entries: Entry[];
}

export interface LookupResult {
  query: string;
  found: boolean;
  suggestions: string[];
  headword: string | null;
  ipa: string | null;
  sections: Section[];
  origins: string[];
  error?: "no_db";
}

export class LexiMissingError extends Error {
  constructor() {
    super("lexi is not installed");
  }
}

export class DictionaryMissingError extends Error {
  constructor() {
    super("The lexi dictionary hasn't been built");
  }
}

function expandHome(path: string): string {
  return path.startsWith("~/") ? join(homedir(), path.slice(2)) : path;
}

export function lexiPath(): string {
  const { lexiPath } = getPreferenceValues<{ lexiPath?: string }>();
  const candidates = [lexiPath?.trim(), "~/.local/bin/lexi", "/opt/homebrew/bin/lexi", "/usr/local/bin/lexi"].filter(
    (p): p is string => Boolean(p),
  );
  const found = candidates.map(expandHome).find((p) => existsSync(p));
  if (!found) {
    throw new LexiMissingError();
  }
  return found;
}

async function lexi(args: string[]): Promise<string> {
  // Raycast starts commands with a minimal PATH; lexi needs to find python3.
  const env = {
    ...process.env,
    PATH: ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", process.env.PATH].filter(Boolean).join(":"),
  };
  const { stdout } = await run(lexiPath(), args, { env, maxBuffer: 32 * 1024 * 1024 });
  return stdout;
}

export async function complete(prefix: string): Promise<string[]> {
  if (!prefix.trim()) {
    return [];
  }
  return JSON.parse(await lexi(["--complete", prefix])) as string[];
}

export async function lookup(word: string): Promise<LookupResult> {
  const result = JSON.parse(await lexi(["--json", word])) as LookupResult;
  if (result.error === "no_db") {
    throw new DictionaryMissingError();
  }
  return result;
}

export function wiktionaryUrl(word: string): string {
  return `https://en.wiktionary.org/wiki/${encodeURIComponent(word.replace(/ /g, "_"))}`;
}

// ---------- markdown ----------

function escape(text: string): string {
  return text.replace(/([\\`*_[\]<>#])/g, "\\$1");
}

/** Italicise a leading "(label)" the way the terminal version colours it. */
function gloss(text: string): string {
  const m = text.match(/^(\([^)]*\))\s*(.*)$/);
  return m ? `*${escape(m[1])}* ${escape(m[2])}` : escape(text);
}

function entriesMarkdown(entries: Entry[]): string[] {
  const out: string[] = [];
  for (const entry of entries) {
    out.push("", `**${(entry.pos ?? "").toUpperCase()}**`, "");
    let num = 0;
    for (const sense of entry.senses) {
      if (sense.depth === 0) {
        num += 1;
        out.push(`${num}. ${gloss(sense.gloss)}`);
      } else {
        out.push(`    - ${gloss(sense.gloss)}`);
      }
      if (sense.example) {
        const indent = sense.depth === 0 ? "    " : "        ";
        out.push(`${indent}*“${escape(sense.example)}”*`);
      }
    }
  }
  return out;
}

export function toMarkdown(result: LookupResult): string {
  if (!result.found) {
    return `# ${escape(result.query)}\n\nNo definition found.`;
  }
  const out: string[] = [];
  if (result.suggestions.length) {
    out.push(`*${escape(result.query)} wasn't found. Did you mean: ${result.suggestions.map(escape).join(", ")}?*`, "");
  }
  out.push(`# ${escape(result.headword ?? result.query)}`);
  if (result.ipa) {
    out.push("", `\`${result.ipa}\``);
  }
  for (const section of result.sections) {
    if (result.sections.length > 1) {
      if (section.kind === "reference") {
        out.push("", "---", "", `## ${escape(section.title)}`);
        if (section.ipa) {
          out.push("", `\`${section.ipa}\``);
        }
      } else {
        out.push("", "---", "", `#### ${section.title}`);
      }
    }
    out.push(...entriesMarkdown(section.entries));
  }
  if (result.origins.length) {
    out.push("", "---", "", "#### Origin", "");
    out.push(result.origins.map(escape).join("\n\n"));
  }
  return out.join("\n");
}

export function toPlainText(result: LookupResult): string {
  if (!result.found) {
    return result.query;
  }
  const out: string[] = [result.headword ?? result.query];
  for (const section of result.sections) {
    if (section.kind === "reference") {
      out.push("", `→ ${section.title}`);
    }
    for (const entry of section.entries) {
      out.push("", (entry.pos ?? "").toUpperCase());
      let num = 0;
      for (const sense of entry.senses) {
        if (sense.depth === 0) {
          num += 1;
          out.push(`${num}. ${sense.gloss}`);
        } else {
          out.push(`   - ${sense.gloss}`);
        }
      }
    }
  }
  return out.join("\n");
}
