import { Action, ActionPanel, Icon, LaunchProps, List } from "@raycast/api";
import { useCachedPromise } from "@raycast/utils";
import { useState } from "react";
import { SetupHelp, WordActions, WordDetail } from "./components";
import { complete, lookup, toMarkdown } from "./lexi";

export default function Command(props: LaunchProps<{ arguments: { word?: string } }>) {
  const [search, setSearch] = useState(props.arguments.word ?? "");
  const [selected, setSelected] = useState<string | null>(null);

  const completions = useCachedPromise(complete, [search], { keepPreviousData: true });
  // Only the selected word is looked up in full; the others just list their names.
  const detail = useCachedPromise(lookup, [selected ?? ""], { execute: Boolean(selected) });

  const error = completions.error ?? detail.error;
  if (error) {
    return <SetupHelp error={error} />;
  }

  // An exact match goes first, even if it is a rarer word.
  const query = search.trim().toLowerCase();
  const words = completions.data ?? [];
  const ordered = words.includes(query) ? [query, ...words.filter((w) => w !== query)] : words;

  return (
    <List
      searchText={search}
      onSearchTextChange={setSearch}
      onSelectionChange={(id) => setSelected(id ?? null)}
      isLoading={completions.isLoading}
      isShowingDetail={ordered.length > 0}
      searchBarPlaceholder="Look up a word…"
      throttle
    >
      {query === "" ? (
        <List.EmptyView
          icon={{ source: "icon.png" }}
          title="Type a word"
          description="Definitions from Wiktionary and Open English WordNet, offline."
        />
      ) : (
        <List.EmptyView icon={Icon.MagnifyingGlass} title="No matching words" />
      )}
      {ordered.map((word) => {
        const result = word === selected ? detail.data : undefined;
        return (
          <List.Item
            key={word}
            id={word}
            title={word}
            detail={
              <List.Item.Detail
                isLoading={word === selected && detail.isLoading}
                markdown={result ? toMarkdown(result) : ""}
              />
            }
            actions={
              <ActionPanel>
                <Action.Push title="Show Definition" icon={Icon.Book} target={<WordDetail word={word} />} />
                <WordActions word={word} result={result} />
              </ActionPanel>
            }
          />
        );
      })}
    </List>
  );
}
