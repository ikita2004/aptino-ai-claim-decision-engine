class ExclusionAgent:
    """
    Identifies policy exclusions and restrictions that are
    potentially applicable to the specific claim.
    """

    def analyze(self, claim, retrieved_chunks):

        if not retrieved_chunks:
            return {
                "agent": "exclusion_agent",
                "status": "NO_EXCLUSION_FOUND",
                "reason": "No policy evidence was retrieved.",
                "evidence": []
            }

        treatment = claim.get("treatment", {})

        pre_existing = treatment.get(
            "pre_existing"
        )

        experimental = treatment.get(
            "experimental"
        )

        claim_description = (
            f"{treatment.get('diagnosis', '')} "
            f"{treatment.get('procedure', '')}"
        ).lower()

        evidence = []

        for chunk in retrieved_chunks:

            text = chunk.get("text", "")
            text_lower = text.lower()

            matched_rule = None
            applicable = False

            # ==================================================
            # RULE 1: PRE-EXISTING DISEASE
            # ==================================================

            if (
                "pre-existing" in text_lower
                or "pre existing" in text_lower
            ):

                if pre_existing is True:

                    applicable = True
                    matched_rule = "PRE_EXISTING_DISEASE"

                else:
                    # Explicitly not pre-existing.
                    # Therefore this exclusion does not apply.
                    applicable = False

            # ==================================================
            # RULE 2: EXPERIMENTAL TREATMENT
            # ==================================================

            if "experimental" in text_lower:

                if experimental is True:

                    applicable = True
                    matched_rule = "EXPERIMENTAL_TREATMENT"

                else:
                    applicable = False

            # ==================================================
            # RULE 3: WAITING PERIOD
            # ==================================================

            if "waiting period" in text_lower:

                coverage_months = claim.get(
                    "continuous_coverage_months"
                )

                # A waiting-period rule requires the claim
                # to provide enough information to evaluate it.

                if coverage_months is None:

                    applicable = True
                    matched_rule = "WAITING_PERIOD_INFORMATION_MISSING"

                elif coverage_months < 1:

                    applicable = True
                    matched_rule = "WAITING_PERIOD"

            # ==================================================
            # RULE 4: EXPLICIT EXCLUSION
            # ==================================================

            explicit_exclusion_phrases = [
                "shall not cover",
                "will not be covered"
            ]

            if any(
                phrase in text_lower
                for phrase in explicit_exclusion_phrases
            ):

                # Only apply an explicit exclusion when we can
                # associate it with the claim.

                if (
                    "pre-existing" not in text_lower
                    and "pre existing" not in text_lower
                    and "experimental" not in text_lower
                ):

                    # Look for claim-specific terminology.
                    if any(
                        keyword in text_lower
                        for keyword in claim_description.split()
                        if len(keyword) > 4
                    ):
                        applicable = True
                        matched_rule = "CLAIM_SPECIFIC_EXCLUSION"

            # ==================================================
            # Store only applicable evidence
            # ==================================================

            if applicable:

                evidence.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "page": chunk.get("page"),
                    "section": chunk.get("section"),
                    "matched_rule": matched_rule,
                    "text": text
                })

        # ======================================================
        # Final result
        # ======================================================

        if not evidence:

            return {
                "agent": "exclusion_agent",
                "status": "NO_EXCLUSION_FOUND",
                "reason": (
                    "No retrieved policy restriction was found "
                    "to clearly apply to the claim."
                ),
                "evidence": []
            }

        return {
            "agent": "exclusion_agent",
            "status": "EXCLUSION_OR_RESTRICTION_FOUND",
            "reason": (
                "A policy exclusion or restriction appears "
                "applicable to the claim."
            ),
            "evidence": evidence
        }


if __name__ == "__main__":

    agent = ExclusionAgent()

    # ------------------------------------------------------
    # Test 1: Non-pre-existing hospitalization
    # ------------------------------------------------------

    claim_1 = {
        "claim_id": "TEST_EXCLUSION_001",

        "treatment": {
            "diagnosis": "Acute appendicitis",
            "procedure": "Appendectomy",
            "pre_existing": False,
            "experimental": False
        },

        "continuous_coverage_months": 14
    }

    chunks_1 = [
        {
            "chunk_id": "page_8_chunk_1",
            "page": 8,
            "section": "What We Exclude",
            "text": (
                "Pre-existing diseases will not be covered "
                "until 48 months of continuous coverage "
                "have elapsed."
            )
        }
    ]

    result_1 = agent.analyze(
        claim_1,
        chunks_1
    )

    print("\nTEST 1 - NON PRE-EXISTING CLAIM")
    print(result_1)

    # ------------------------------------------------------
    # Test 2: Pre-existing hospitalization
    # ------------------------------------------------------

    claim_2 = {
        "claim_id": "TEST_EXCLUSION_002",

        "treatment": {
            "diagnosis": "Chronic disease",
            "procedure": "Treatment",
            "pre_existing": True,
            "experimental": False
        },

        "continuous_coverage_months": 14
    }

    result_2 = agent.analyze(
        claim_2,
        chunks_1
    )

    print("\nTEST 2 - PRE-EXISTING CLAIM")
    print(result_2)