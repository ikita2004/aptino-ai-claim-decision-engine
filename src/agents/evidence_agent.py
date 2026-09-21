class EvidenceAgent:
    """
    Validates whether retrieved policy evidence and
    claim-level evidence are sufficient for a safe decision.
    """

    def analyze(self, claim, retrieved_chunks):

        if not retrieved_chunks:

            return {
                "agent": "evidence_agent",
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": "No policy evidence was retrieved.",
                "missing_evidence": [
                    "Relevant policy evidence"
                ],
                "citations": []
            }

        citations = []

        for chunk in retrieved_chunks:

            text = chunk.get("text", "").strip()

            if not text:
                continue

            page = chunk.get("page")
            section = chunk.get("section")
            chunk_id = chunk.get("chunk_id")

            # Basic citation validation
            if page is None or not chunk_id:
                continue

            citations.append({
                "chunk_id": chunk_id,
                "page": page,
                "section": section,
                "citation": f"Policy Page {page}",
                "evidence": text
            })

        if not citations:

            return {
                "agent": "evidence_agent",
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": (
                    "Retrieved chunks did not contain "
                    "valid citation metadata."
                ),
                "missing_evidence": [
                    "Valid policy citations"
                ],
                "citations": []
            }

        # --------------------------------------------------
        # CLAIM-LEVEL EVIDENCE CHECK
        # --------------------------------------------------

        hospital = claim.get("hospital", {})
        treatment = claim.get("treatment", {})
        documents = claim.get("documents", [])

        missing_evidence = []

        # Hospital registration / facility evidence
        hospital_registered = hospital.get(
            "network_provider"
        )

        if hospital_registered is None:

            missing_evidence.append(
                "Hospital registration/provider status"
            )

        # Medical necessity evidence
        medical_necessity = claim.get(
            "evidence_context",
            {}
        ).get(
            "medical_necessity_confirmed"
        )

        if (
            medical_necessity is None
            and treatment.get("type") == "inpatient"
        ):

            # A discharge summary or equivalent clinical
            # evidence can establish that hospitalization
            # actually occurred, but a claim form alone
            # is not sufficient.
            clinical_documents = {
                "discharge_summary",
                "medical_report",
                "hospitalization_record",
                "medical_necessity_certificate"
            }

            has_clinical_document = any(
                str(document).lower()
                in clinical_documents
                for document in documents
            )

            if not has_clinical_document:

                missing_evidence.append(
                    "Evidence establishing medical necessity "
                    "for inpatient hospitalization"
                )

        # --------------------------------------------------
        # ABSTAIN WHEN CLAIM-LEVEL EVIDENCE IS INSUFFICIENT
        # --------------------------------------------------

        if missing_evidence:

            return {
                "agent": "evidence_agent",
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": (
                    "Policy evidence was retrieved, but the "
                    "claim does not contain sufficient "
                    "claim-level evidence for a safe final decision."
                ),
                "missing_evidence": missing_evidence,
                "citations": citations
            }

        return {
            "agent": "evidence_agent",
            "status": "SUFFICIENT_EVIDENCE",
            "reason": (
                "Retrieved policy evidence and required "
                "claim-level evidence are available."
            ),
            "missing_evidence": [],
            "citations": citations
        }


if __name__ == "__main__":

    agent = EvidenceAgent()

    test_claim = {
        "claim_id": "TEST003",
        "claim_type": "hospitalization",
        "description": "Hospitalization claim",
        "hospital": {
            "network_provider": True
        },
        "treatment": {
            "type": "inpatient"
        },
        "documents": [
            "claim_form",
            "discharge_summary"
        ]
    }

    test_chunks = [
        {
            "chunk_id": "page_9_chunk_1",
            "page": 9,
            "section": "What We Exclude",
            "text": (
                "A waiting period of 30 days will apply "
                "to all claims unless certain conditions apply."
            )
        }
    ]

    result = agent.analyze(
        test_claim,
        test_chunks
    )

    print("\nEvidence Agent Result:")
    print(result)