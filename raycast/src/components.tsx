import { Action, ActionPanel, Detail, Icon, Keyboard } from "@raycast/api";
import { useCachedPromise } from "@raycast/utils";
import {
  DictionaryMissingError,
  LexiMissingError,
  LookupResult,
  lookup,
  toMarkdown,
  toPlainText,
  wiktionaryUrl,
} from "./lexi";

const REPO = "https://github.com/rallevondalle/lexi";

export function WordActions({ word, result }: { word: string; result?: LookupResult }) {
  const headword = result?.headword ?? word;
  const references = result?.sections.filter((s) => s.kind === "reference").map((s) => s.title) ?? [];
  const related = [...references, ...(result?.suggestions.slice(1) ?? [])];
  return (
    <>
      {result?.found ? <Action.CopyToClipboard title="Copy Definition" content={toPlainText(result)} /> : null}
      <Action.OpenInBrowser title="Open in Wiktionary" url={wiktionaryUrl(headword)} />
      <Action.CopyToClipboard title="Copy Word" content={headword} shortcut={Keyboard.Shortcut.Common.Copy} />
      {related.length ? (
        <ActionPanel.Submenu title="Look up Related Word" icon={Icon.MagnifyingGlass}>
          {related.map((other) => (
            <Action.Push key={other} title={other} target={<WordDetail word={other} />} />
          ))}
        </ActionPanel.Submenu>
      ) : null}
    </>
  );
}

export function WordDetail({ word }: { word: string }) {
  const { data, isLoading, error } = useCachedPromise(lookup, [word]);
  if (error) {
    return <SetupHelp error={error} />;
  }
  const sources = data?.sections.map((s) => (s.kind === "wordnet" ? "WordNet" : "Wiktionary")) ?? [];
  return (
    <Detail
      isLoading={isLoading}
      navigationTitle={data?.headword ?? word}
      markdown={data ? toMarkdown(data) : ""}
      metadata={
        data?.found ? (
          <Detail.Metadata>
            <Detail.Metadata.Label title="Word" text={data.headword ?? word} />
            {data.ipa ? <Detail.Metadata.Label title="Pronunciation" text={data.ipa} /> : null}
            <Detail.Metadata.TagList title="Part of Speech">
              {[...new Set(data.sections.flatMap((s) => s.entries.map((e) => e.pos ?? "")))]
                .filter(Boolean)
                .map((pos) => (
                  <Detail.Metadata.TagList.Item key={pos} text={pos} />
                ))}
            </Detail.Metadata.TagList>
            <Detail.Metadata.Separator />
            <Detail.Metadata.Label title="Sources" text={[...new Set(sources)].join(", ")} />
            <Detail.Metadata.Link title="Wiktionary" text="Open entry" target={wiktionaryUrl(data.headword ?? word)} />
          </Detail.Metadata>
        ) : null
      }
      actions={
        <ActionPanel>
          <WordActions word={word} result={data} />
        </ActionPanel>
      }
    />
  );
}

export function SetupHelp({ error }: { error: Error }) {
  let markdown: string;
  let command: string;
  if (error instanceof LexiMissingError) {
    command = `git clone ${REPO}.git && cd lexi && ./install.sh`;
    markdown = `# Install lexi

This extension uses the **lexi** command-line dictionary, which isn't installed yet.

Run this in Terminal. It downloads the dictionaries (about 540 MB) and builds a local database, which takes a few minutes:

\`\`\`
${command}
\`\`\`

If lexi is installed somewhere else, set its path in this extension's preferences.`;
  } else if (error instanceof DictionaryMissingError) {
    command = "lexi update";
    markdown = `# Build the dictionary

lexi is installed, but its dictionary hasn't been built yet. Run this in Terminal:

\`\`\`
${command}
\`\`\``;
  } else {
    command = "lexi --version";
    markdown = `# Something went wrong\n\n\`\`\`\n${error.message}\n\`\`\``;
  }
  return (
    <Detail
      markdown={markdown}
      actions={
        <ActionPanel>
          <Action.CopyToClipboard title="Copy Command" content={command} />
          <Action.OpenInBrowser title="Open Lexi on GitHub" url={REPO} />
        </ActionPanel>
      }
    />
  );
}
