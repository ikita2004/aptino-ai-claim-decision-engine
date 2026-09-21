from pathlib import Path
from typing import List, Dict
import json
import re

from rank_bm25 import BM25Okapi


CHUNKS_PATH = Path("data/policy_chunks.json")


def tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]+\b", text)
    return tokens


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> List[Dict]:
    with open(chunks_path, "r", encoding="utf-8") as file:
        return json.load(file)


class BM25Retriever:

    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks

        self.tokenized_chunks = [
            tokenize(chunk["text"])
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:

        query_tokens = tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []

        for index in ranked_indexes:

            chunk = self.chunks[index].copy()

            chunk["score"] = round(
                float(scores[index]),
                4
            )

            results.append(chunk)

        return results


def print_results(query: str, results: List[Dict]):

    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    for rank, result in enumerate(results, start=1):

        print()
        print(f"Rank       : {rank}")
        print(f"Chunk ID   : {result['chunk_id']}")
        print(f"Page       : {result['page']}")
        print(f"Section    : {result['section']}")
        print(f"BM25 Score : {result['score']}")
        print(f"Text       : {result['text'][:500]}")

        print("-" * 80)


if __name__ == "__main__":

    print("Loading policy chunks...")

    chunks = load_chunks()

    print(f"Loaded {len(chunks)} policy chunks.")

    print("Building BM25 index...")

    retriever = BM25Retriever(chunks)

    print("BM25 index ready.")

    test_queries = [
        "pre-existing disease",
        "30 days waiting period",
        "cashless hospitalization",
        "critical illness",
        "multiple insurance policies",
    ]

    for query in test_queries:

        results = retriever.search(
            query,
            top_k=3
        )

        print_results(
            query,
            results
        )