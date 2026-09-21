class CoverageAgent:
    """
    Determines whether a claim has potential coverage
    based on retrieved policy evidence.
    """

    def analyze(self, claim, retrieved_chunks):
        """
        Parameters:
            claim: Dictionary containing claim information.
            retrieved_chunks: Policy chunks retrieved by RAG.

        Returns:
            Structured coverage analysis.
        """

        evidence = []

        for chunk in retrieved_chunks:
            evidence.append({
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "section": chunk["section"],
                "text": chunk["text"]
            })

        if not evidence:
            return {
                "agent": "coverage_agent",
                "status": "NEEDS_REVIEW",
                "reason": "No relevant policy evidence was retrieved.",
                "evidence": []
            }

        return {
            "agent": "coverage_agent",
            "status": "POTENTIAL_COVERAGE",
            "reason": "Relevant policy evidence was retrieved for the claim.",
            "evidence": evidence
        }


if __name__ == "__main__":

    agent = CoverageAgent()

    test_claim = {
        "claim_id": "TEST001",
        "claim_type": "hospitalization",
        "description": "Hospitalization due to illness"
    }

    test_chunks = [
        {
            "chunk_id": "page_9_chunk_1",
            "page": 9,
            "section": "What We Exclude",
            "text": "A waiting period of 30 days will apply to all claims."
        }
    ]

    result = agent.analyze(
        test_claim,
        test_chunks
    )

    print("\nCoverage Agent Result:")
    print(result)