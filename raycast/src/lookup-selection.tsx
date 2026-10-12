import { Detail, getSelectedText } from "@raycast/api";
import { usePromise } from "@raycast/utils";
import { WordDetail } from "./components";

async function selectedWord(): Promise<string> {
  const text = (await getSelectedText()).trim();
  // Keep a short phrase ("kick the bucket") and drop surrounding punctuation.
  return text
    .split(/\s+/)
    .slice(0, 4)
    .join(" ")
    .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
}

export default function Command() {
  const { data: word, isLoading, error } = usePromise(selectedWord);
  if (error || (!isLoading && !word)) {
    return <Detail markdown={"# No text selected\n\nSelect a word in any app, then run **Look up Selected Text**."} />;
  }
  if (!word) {
    return <Detail isLoading />;
  }
  return <WordDetail word={word} />;
}
