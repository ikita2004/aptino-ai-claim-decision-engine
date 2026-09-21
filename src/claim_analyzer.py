import json
from pathlib import Path

from state import ClaimState
from hybrid_retrieval import HybridRetriever
from reranker import Reranker

from agents.coverage_agent import CoverageAgent
from agents.exclusion_agent import ExclusionAgent
from agents.evidence_agent import EvidenceAgent

from decision_engine import DecisionEngine
from citation_validator import CitationValidator
from policy_rules import PolicyRuleEngine


class ClaimAnalyzer:
    """
    Complete policy-aware claim analysis pipeline.

    Flow:

    Claim
      ↓
    Structured State
      ↓
    Hybrid Retrieval
      ↓
    Reranking
      ↓
    Coverage Agent
      ↓
    Exclusion Agent
      ↓
    Evidence Agent
      ↓
    Citation Validation
      ↓
    Deterministic Policy Rules
      ↓
    Decision Engine
      ↓
    Final Decision
    """

    def __init__(self):

        print("Loading policy chunks...")

        policy_path = Path("data/policy_chunks.json")

        if not policy_path.exists():
            raise FileNotFoundError(
                "Policy chunks not found. "
                "Run policy_ingestion.py first."
            )

        with open(
            policy_path,
            "r",
            encoding="utf-8"
        ) as file:
            chunks = json.load(file)

        print(f"Loaded {len(chunks)} policy chunks.")

        # ---------------------------------------------
        # Retrieval
        # ---------------------------------------------

        print("Initializing hybrid retriever...")

        self.retriever = HybridRetriever(chunks)

        # ---------------------------------------------
        # Reranker
        # ---------------------------------------------

        print("Initializing reranker...")

        self.reranker = Reranker()

        # ---------------------------------------------
        # Agents
        # ---------------------------------------------

        print("Initializing agents...")

        self.coverage_agent = CoverageAgent()
        self.exclusion_agent = ExclusionAgent()
        self.evidence_agent = EvidenceAgent()

        # ---------------------------------------------
        # Deterministic Policy Rule Engine
        # ---------------------------------------------

        print("Initializing policy rule engine...")

        self.policy_rule_engine = PolicyRuleEngine()

        # ---------------------------------------------
        # Decision Engine
        # ---------------------------------------------

        print("Initializing decision engine...")

        self.decision_engine = DecisionEngine()

        # ---------------------------------------------
        # Citation Validator
        # ---------------------------------------------

        print("Initializing citation validator...")

        self.citation_validator = CitationValidator(chunks)

        print("Claim Analyzer initialized successfully.")

    def analyze(self, claim):

        # ---------------------------------------------
        # 1. Create structured state
        # ---------------------------------------------

        state = ClaimState(**claim)

        # ---------------------------------------------
        # 2. Build detailed retrieval query
        # ---------------------------------------------

        query_parts = []

        if state.task:
            query_parts.append(state.task)

        if state.policy_id:
            query_parts.append(
                f"Policy: {state.policy_id}"
            )

        if state.treatment.type:
            query_parts.append(
                f"Treatment type: {state.treatment.type}"
            )

        if state.treatment.diagnosis:
            query_parts.append(
                f"Diagnosis: {state.treatment.diagnosis}"
            )

        if state.treatment.procedure:
            query_parts.append(
                f"Procedure: {state.treatment.procedure}"
            )

        if state.treatment.pre_existing is not None:
            query_parts.append(
                f"Pre-existing condition: "
                f"{state.treatment.pre_existing}"
            )

        if state.treatment.experimental is not None:
            query_parts.append(
                f"Experimental treatment: "
                f"{state.treatment.experimental}"
            )

        if state.treatment.admission_hours is not None:
            query_parts.append(
                f"Admission duration: "
                f"{state.treatment.admission_hours} hours"
            )

        if state.hospital.network_provider is not None:
            query_parts.append(
                f"Network hospital: "
                f"{state.hospital.network_provider}"
            )

        if state.continuous_coverage_months is not None:
            query_parts.append(
                f"Continuous coverage: "
                f"{state.continuous_coverage_months} months"
            )

        if state.prior_insurer_continuous_years is not None:
            query_parts.append(
                f"Prior insurer continuous coverage: "
                f"{state.prior_insurer_continuous_years} years"
            )

        if state.sum_insured_inr is not None:
            query_parts.append(
                f"Sum insured: "
                f"{state.sum_insured_inr} INR"
            )

        # Cleanly join query parts
        query = ". ".join(
            part.strip().rstrip(".")
            for part in query_parts
            if part and part.strip()
        )

        print("\nRetrieval Query:")
        print(query)

        # ---------------------------------------------
        # 3. Hybrid Retrieval
        # ---------------------------------------------

        print("\nSearching policy using hybrid retrieval...")

        retrieved = self.retriever.search(
            query,
            top_k=10
        )

        # ---------------------------------------------
        # 4. Reranking
        # ---------------------------------------------

        print("Reranking retrieved policy evidence...")

        reranked = self.reranker.rerank(
            query,
            retrieved,
            top_k=5
        )

        state.retrieved_chunks = reranked

        # ---------------------------------------------
        # 5. Coverage Agent
        # ---------------------------------------------

        print("Running Coverage Agent...")

        state.coverage_result = (
            self.coverage_agent.analyze(
                claim,
                reranked
            )
        )

        # ---------------------------------------------
        # 6. Exclusion Agent
        # ---------------------------------------------

        print("Running Exclusion Agent...")

        state.exclusion_result = (
            self.exclusion_agent.analyze(
                claim,
                reranked
            )
        )

        # ---------------------------------------------
        # 7. Evidence Agent
        # ---------------------------------------------

        print("Running Evidence Agent...")

        state.evidence_result = (
            self.evidence_agent.analyze(
                claim,
                reranked
            )
        )

        # ---------------------------------------------
        # 8. Get Citations
        # ---------------------------------------------

        citations = state.evidence_result.get(
            "citations",
            []
        )

        # ---------------------------------------------
        # 9. Validate Citations
        # ---------------------------------------------

        print("Validating citations...")

        citation_result = (
            self.citation_validator.validate(
                citations
            )
        )

        state.citation_validation = citation_result

        # Store only validated citations
        state.citations = citation_result.get(
            "valid_citations",
            []
        )

        # ---------------------------------------------
        # 10. Handle Citation Failure
        # ---------------------------------------------

        if citation_result.get("status") == "INVALID":

            state.final_decision = "NEEDS_REVIEW"

            state.final_reason = (
                "The retrieved policy evidence could not "
                "be validated with reliable citations."
            )

            state.decision_result = {
                "decision": "NEEDS_REVIEW",
                "reason": state.final_reason,
                "total_claimed_inr": 0,
                "payable_amount_inr": 0,
                "deductions_inr": 0,
                "applied_limits": [],
                "rule_findings": []
            }

            return state

        # ---------------------------------------------
        # 11. Run Deterministic Policy Rules
        # ---------------------------------------------

        print("Running deterministic policy rules...")

        rule_findings = self.policy_rule_engine.evaluate(
            claim
        )

                # ---------------------------------------------
        # 12. Combine All Findings
        # ---------------------------------------------

        findings = []

        coverage_findings = (
            state.coverage_result.get(
                "findings",
                []
            )
        )

        exclusion_findings = (
            state.exclusion_result.get(
                "findings",
                []
            )
        )

        evidence_findings = (
            state.evidence_result.get(
                "findings",
                []
            )
        )

        # Convert insufficient claim-level evidence
        # into an explicit REVIEW finding.
        if (
            state.evidence_result.get("status")
            == "INSUFFICIENT_EVIDENCE"
        ):

            evidence_findings.append({
                "effect": "REVIEW",
                "category": "evidence",
                "reason": (
                    state.evidence_result.get(
                        "reason",
                        "Insufficient evidence for a safe decision."
                    )
                ),
                "missing_evidence": (
                    state.evidence_result.get(
                        "missing_evidence",
                        []
                    )
                )
            })

        findings.extend(coverage_findings)
        findings.extend(exclusion_findings)
        findings.extend(evidence_findings)
        findings.extend(rule_findings)

        # Convert insufficient claim-level evidence
        # into an explicit REVIEW finding for the
        # deterministic decision engine.
        if (
            state.evidence_result.get("status")
            == "INSUFFICIENT_EVIDENCE"
        ):

            evidence_findings.append({
                "type": "REVIEW",
                "category": "evidence",
                "reason": (
                    state.evidence_result.get(
                        "reason",
                        "Insufficient evidence for a safe decision."
                    )
                ),
                "missing_evidence": (
                    state.evidence_result.get(
                        "missing_evidence",
                        []
                    )
                )
            })

        findings.extend(coverage_findings)
        findings.extend(exclusion_findings)
        findings.extend(evidence_findings)
        findings.extend(rule_findings)

        # ---------------------------------------------
        # 13. Decision Engine
        # ---------------------------------------------

        print("Running Decision Engine...")

        decision_result = self.decision_engine.decide(
            claim,
            findings
        )

        # ---------------------------------------------
        # 14. Store Decision Result
        # ---------------------------------------------

        state.final_decision = decision_result.get(
            "decision"
        )

        state.final_reason = decision_result.get(
            "reason"
        )

        state.decision_result = decision_result

        # ---------------------------------------------
        # 15. Return Final State
        # ---------------------------------------------

        return state


# ======================================================
# Manual Test
# ======================================================

if __name__ == "__main__":

    print("\nStarting Claim Analyzer test...\n")

    analyzer = ClaimAnalyzer()

    test_claim = {

        "claim_id": "TEST_ANALYZER_001",

        "policy_id": "USGIC-CSC-2017-2018",

        "policy_start_date": "2025-01-01",

        "claim_date": "2026-03-14",

        "sum_insured_inr": 500000,

        "continuous_coverage_months": 14,

        "prior_insurer_continuous_years": 0,

        "patient": {
            "age": 34
        },

        "hospital": {
            "name": "Sunrise Multispeciality",
            "network_provider": True
        },

        "treatment": {

            "type": "inpatient",

            "admission_hours": 96,

            "diagnosis": "Acute appendicitis",

            "procedure": "Appendectomy",

            "pre_existing": False,

            "experimental": False
        },

        "expenses_inr": {

            "room": 30000,

            "doctor_fees": 30000,

            "medicines_diagnostics": 90000,

            "pre_hospitalization": 5000,

            "post_hospitalization": 7000,

            "ambulance": 1200
        },

        "documents": [

            "claim_form",

            "discharge_summary",

            "itemized_bill",

            "doctor_prescription"
        ],

        "task": (
            "Determine whether the hospitalization is admissible, "
            "identify applicable policy limits, and explain "
            "any deductions."
        )
    }

    # Run analysis
    result = analyzer.analyze(test_claim)

    # ---------------------------------------------
    # Final Output
    # ---------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL CLAIM ANALYSIS")
    print("=" * 60)

    print(
        f"Claim ID       : "
        f"{result.claim_id}"
    )

    print(
        f"Decision       : "
        f"{result.final_decision}"
    )

    print(
        f"Reason         : "
        f"{result.final_reason}"
    )

    print(
        f"Citations      : "
        f"{len(result.citations)}"
    )

    print(
        f"Retrieved Docs : "
        f"{len(result.retrieved_chunks)}"
    )

    print(
        f"Citation Status: "
        f"{result.citation_validation.get('status')}"
    )

    # ---------------------------------------------
    # Financial Result
    # ---------------------------------------------

    decision = result.decision_result

    print("\nFinancial Summary:")

    print(
        f"Total Claimed  : "
        f"₹{decision.get('total_claimed_inr', 0):,.2f}"
    )

    print(
        f"Deductions      : "
        f"₹{decision.get('deductions_inr', 0):,.2f}"
    )

    print(
        f"Payable Amount  : "
        f"₹{decision.get('payable_amount_inr', 0):,.2f}"
    )

    # ---------------------------------------------
    # Applied Limits
    # ---------------------------------------------

    print("\nApplied Limits:")

    applied_limits = decision.get(
        "applied_limits",
        []
    )

    if applied_limits:

        for limit in applied_limits:
            print(f"- {limit}")

    else:

        print("- None")

    # ---------------------------------------------
    # Validated Citations
    # ---------------------------------------------

    print("\nValidated Citations:")

    for citation in result.citations:

        print(
            f"- {citation.get('citation')} "
            f"({citation.get('chunk_id')})"
        )

    print("\nClaim Analyzer test completed.")