class CitationValidator:
    """
    Validates citations produced from retrieved policy evidence.
    """

    def __init__(self, policy_chunks):
        self.policy_chunks = policy_chunks

        # Create a lookup table for fast validation
        self.valid_chunks = {
            chunk["chunk_id"]: chunk
            for chunk in policy_chunks
            if "chunk_id" in chunk
        }

    def validate(self, citations):
        """
        Validate a list of citations.

        Returns:
            {
                "status": "VALID" / "INVALID",
                "valid_citations": [...],
                "invalid_citations": [...],
                "reason": "..."
            }
        """

        if not citations:
            return {
                "status": "INVALID",
                "valid_citations": [],
                "invalid_citations": [],
                "reason": "No citations were provided."
            }

        valid_citations = []
        invalid_citations = []

        for citation in citations:

            chunk_id = citation.get("chunk_id")
            page = citation.get("page")
            evidence = citation.get("evidence", "")

            # ---------------------------------------------
            # Check 1: chunk ID exists
            # ---------------------------------------------

            if not chunk_id or chunk_id not in self.valid_chunks:
                invalid_citations.append({
                    "citation": citation,
                    "reason": "Chunk ID does not exist in policy index."
                })
                continue

            original_chunk = self.valid_chunks[chunk_id]

            # ---------------------------------------------
            # Check 2: page number exists
            # ---------------------------------------------

            if page is None:
                invalid_citations.append({
                    "citation": citation,
                    "reason": "Citation does not contain a page number."
                })
                continue

            # ---------------------------------------------
            # Check 3: page matches original policy chunk
            # ---------------------------------------------

            if page != original_chunk.get("page"):
                invalid_citations.append({
                    "citation": citation,
                    "reason": "Citation page does not match policy chunk."
                })
                continue

            # ---------------------------------------------
            # Check 4: evidence is not empty
            # ---------------------------------------------

            if not evidence or not evidence.strip():
                invalid_citations.append({
                    "citation": citation,
                    "reason": "Citation contains empty evidence."
                })
                continue

            # ---------------------------------------------
            # Check 5: evidence exists in original chunk
            # ---------------------------------------------

            original_text = original_chunk.get("text", "")

            if evidence.strip() not in original_text:
                invalid_citations.append({
                    "citation": citation,
                    "reason": (
                        "Citation evidence does not match "
                        "the original policy chunk."
                    )
                })
                continue

            # ---------------------------------------------
            # Citation passed all validation checks
            # ---------------------------------------------

            valid_citations.append(citation)

        # ---------------------------------------------
        # Final validation status
        # ---------------------------------------------

        if valid_citations and not invalid_citations:
            status = "VALID"
            reason = "All citations passed validation."

        elif valid_citations and invalid_citations:
            status = "PARTIALLY_VALID"
            reason = (
                "Some citations passed validation while "
                "others were invalid."
            )

        else:
            status = "INVALID"
            reason = "No citations passed validation."

        return {
            "status": status,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "reason": reason
        }


if __name__ == "__main__":

    import json

    print("\nStarting Citation Validator test...\n")

    # Load policy chunks
    with open(
        "data/policy_chunks.json",
        "r",
        encoding="utf-8"
    ) as file:
        chunks = json.load(file)

    validator = CitationValidator(chunks)

    # ---------------------------------------------
    # Test 1: Valid citation
    # ---------------------------------------------

    valid_test = [{
        "chunk_id": chunks[0]["chunk_id"],
        "page": chunks[0]["page"],
        "citation": f"Policy Page {chunks[0]['page']}",
        "evidence": chunks[0]["text"]
    }]

    result = validator.validate(valid_test)

    print("TEST 1 - VALID CITATION")
    print(result)

    # ---------------------------------------------
    # Test 2: Invalid chunk
    # ---------------------------------------------

    invalid_test = [{
        "chunk_id": "fake_chunk_999",
        "page": 99,
        "citation": "Policy Page 99",
        "evidence": "Fake policy evidence."
    }]

    result = validator.validate(invalid_test)

    print("\nTEST 2 - INVALID CITATION")
    print(result)

    print("\nCitation Validator test completed.")