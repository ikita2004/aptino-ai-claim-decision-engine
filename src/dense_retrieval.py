from pathlib import Path
from typing import List, Dict
import json

from sentence_transformers import SentenceTransformer
import numpy as np


CHUNKS_PATH = Path("data/policy_chunks.json")


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> List[Dict]:
    with open(chunks_path, "r", encoding="utf-8") as file:
        return json.load(file)


class DenseRetriever:

    def __init__(self, chunks: List[Dict]):

        self.chunks = chunks

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Embedding policy chunks...")

        self.embeddings = self.model.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True,
            show_progress_bar=True
        )

        print("Embeddings created successfully.")

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )[0]

        scores = np.dot(
            self.embeddings,
            query_embedding
        )

        ranked_indexes = np.argsort(
            scores
        )[::-1][:top_k]

        results = []

        for index in ranked_indexes:

            chunk = self.chunks[index].copy()

            chunk["score"] = round(
                float(scores[index]),
                4
            )

            results.append(chunk)

        return results


def print_results(
    query: str,
    results: List[Dict]
):

    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    for rank, result in enumerate(
        results,
        start=1
    ):

        print()
        print(f"Rank          : {rank}")
        print(f"Chunk ID      : {result['chunk_id']}")
        print(f"Page          : {result['page']}")
        print(f"Section       : {result['section']}")
        print(f"Dense Score   : {result['score']}")
        print(f"Text          : {result['text'][:500]}")

        print("-" * 80)


if __name__ == "__main__":

    print("Loading policy chunks...")

    chunks = load_chunks()

    print(
        f"Loaded {len(chunks)} policy chunks."
    )

    retriever = DenseRetriever(chunks)

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