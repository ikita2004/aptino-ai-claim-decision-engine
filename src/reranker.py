from sentence_transformers import CrossEncoder
import json


class Reranker:

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        print("Loading reranker model...")

        self.model = CrossEncoder(model_name)

        print("Reranker model loaded successfully.")

    def rerank(self, query, candidates, top_k=5):

        if not candidates:
            return []

        pairs = [
            (query, candidate["text"])
            for candidate in candidates
        ]

        scores = self.model.predict(pairs)

        reranked = []

        for candidate, score in zip(candidates, scores):

            item = candidate.copy()

            item["reranker_score"] = float(score)

            reranked.append(item)

        reranked.sort(
            key=lambda x: x["reranker_score"],
            reverse=True
        )

        return reranked[:top_k]


if __name__ == "__main__":

    from hybrid_retrieval import HybridRetriever

    print("\nStarting hybrid retrieval + reranking...\n")

    # Load policy chunks
    print("Loading policy chunks...")

    with open(
        "data/policy_chunks.json",
        "r",
        encoding="utf-8"
    ) as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} policy chunks.")

    # Create hybrid retriever
    hybrid = HybridRetriever(chunks)

    # Create reranker
    reranker = Reranker()

    query = "What is the waiting period for hospitalization?"

    print("\nSearching policy...")

    # First retrieve candidates
    candidates = hybrid.search(
        query,
        top_k=10
    )

    # Then rerank candidates
    results = reranker.rerank(
        query,
        candidates,
        top_k=5
    )

    print("\n" + "=" * 90)
    print("QUERY:", query)
    print("=" * 90)

    for i, result in enumerate(results, start=1):

        print(f"\nRank          : {i}")
        print(f"Chunk ID      : {result['chunk_id']}")
        print(f"Page          : {result['page']}")
        print(f"Section       : {result['section']}")
        print(f"Hybrid Score  : {result['hybrid_score']:.4f}")
        print(f"Reranker Score: {result['reranker_score']:.4f}")

        print(
            f"Text          : "
            f"{result['text'][:500]}..."
        )

        print("-" * 90)