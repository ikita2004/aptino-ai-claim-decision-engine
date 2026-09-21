from pathlib import Path
from typing import List, Dict
import json
import re

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("data/policy_chunks.json")


def tokenize(text: str) -> List[str]:
    text = text.lower()
    return re.findall(r"\b[a-z0-9]+\b", text)


def load_chunks(chunks_path: Path = CHUNKS_PATH) -> List[Dict]:
    with open(chunks_path, "r", encoding="utf-8") as file:
        return json.load(file)


class HybridRetriever:

    def __init__(self, chunks: List[Dict]):

        self.chunks = chunks

        # -------------------------
        # BM25 setup
        # -------------------------

        print("Building BM25 index...")

        self.tokenized_chunks = [
            tokenize(chunk["text"])
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(
            self.tokenized_chunks
        )

        # -------------------------
        # Dense setup
        # -------------------------

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Creating policy embeddings...")

        self.embeddings = self.model.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True,
            show_progress_bar=True
        )

        print("Hybrid retriever ready.")

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:

        # ==================================================
        # 1. BM25 retrieval
        # ==================================================

        query_tokens = tokenize(query)

        bm25_scores = self.bm25.get_scores(
            query_tokens
        )

        # ==================================================
        # 2. Dense retrieval
        # ==================================================

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )[0]

        dense_scores = np.dot(
            self.embeddings,
            query_embedding
        )

        # ==================================================
        # 3. Normalize both score types
        # ==================================================

        bm25_min = np.min(bm25_scores)
        bm25_max = np.max(bm25_scores)

        if bm25_max > bm25_min:
            bm25_normalized = (
                (bm25_scores - bm25_min)
                / (bm25_max - bm25_min)
            )
        else:
            bm25_normalized = np.zeros(
                len(bm25_scores)
            )

        dense_min = np.min(dense_scores)
        dense_max = np.max(dense_scores)

        if dense_max > dense_min:
            dense_normalized = (
                (dense_scores - dense_min)
                / (dense_max - dense_min)
            )
        else:
            dense_normalized = np.zeros(
                len(dense_scores)
            )

        # ==================================================
        # 4. Combine BM25 + Dense
        # ==================================================

        hybrid_scores = (
            0.5 * bm25_normalized
            + 0.5 * dense_normalized
        )

        ranked_indexes = np.argsort(
            hybrid_scores
        )[::-1][:top_k]

        # ==================================================
        # 5. Build results
        # ==================================================

        results = []

        for index in ranked_indexes:

            chunk = self.chunks[index].copy()

            chunk["bm25_score"] = round(
                float(bm25_scores[index]),
                4
            )

            chunk["dense_score"] = round(
                float(dense_scores[index]),
                4
            )

            chunk["hybrid_score"] = round(
                float(hybrid_scores[index]),
                4
            )

            results.append(chunk)

        return results


def print_results(
    query: str,
    results: List[Dict]
):

    print()
    print("=" * 90)
    print(f"QUERY: {query}")
    print("=" * 90)

    for rank, result in enumerate(
        results,
        start=1
    ):

        print()
        print(f"Rank          : {rank}")
        print(f"Chunk ID      : {result['chunk_id']}")
        print(f"Page          : {result['page']}")
        print(f"Section       : {result['section']}")
        print(f"BM25 Score    : {result['bm25_score']}")
        print(f"Dense Score   : {result['dense_score']}")
        print(f"Hybrid Score  : {result['hybrid_score']}")
        print(f"Text          : {result['text'][:500]}")

        print("-" * 90)


if __name__ == "__main__":

    print("Loading policy chunks...")

    chunks = load_chunks()

    print(
        f"Loaded {len(chunks)} policy chunks."
    )

    retriever = HybridRetriever(chunks)

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