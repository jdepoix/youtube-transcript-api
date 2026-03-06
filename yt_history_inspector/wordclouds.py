from __future__ import annotations

import json
import re
from collections import Counter
from typing import Iterable

from wordcloud import WordCloud, STOPWORDS


EXTRA_STOPWORDS = {
    "und",
    "oder",
    "aber",
    "dass",
    "die",
    "der",
    "das",
    "ein",
    "eine",
    "ist",
    "im",
    "in",
    "mit",
    "auf",
    "für",
    "von",
    "zu",
    "wir",
    "ihr",
    "sie",
    "ich",
    "du",
    "you",
    "your",
    "the",
    "and",
    "this",
    "that",
    "there",
    "here",
    "have",
    "has",
    "was",
    "were",
    "are",
    "is",
    "to",
    "of",
    "it",
    "as",
    "be",
    "we",
    "they",
    "he",
    "she",
    "them",
    "with",
    "for",
    "on",
}


TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]{3,}")


def tokens_from_snippets(snippets_json: str) -> list[str]:
    snippets = json.loads(snippets_json)
    words: list[str] = []
    for snippet in snippets:
        text = snippet.get("text", "")
        words.extend(word.lower() for word in TOKEN_RE.findall(text))
    return words


def word_counts(snippets_jsons: Iterable[str]) -> Counter:
    stopwords = STOPWORDS.union(EXTRA_STOPWORDS)
    counts = Counter()
    for snippets_json in snippets_jsons:
        for word in tokens_from_snippets(snippets_json):
            if word in stopwords:
                continue
            counts[word] += 1
    return counts


def render_wordcloud(
    counts: Counter,
    width: int = 1200,
    height: int = 800,
    background_color: str = "#0a0a0f",
) -> WordCloud:
    if not counts:
        counts = Counter({"no_data_yet": 1})
    return WordCloud(
        width=width,
        height=height,
        background_color=background_color,
        colormap="cool",
        collocations=False,
    ).generate_from_frequencies(counts)
