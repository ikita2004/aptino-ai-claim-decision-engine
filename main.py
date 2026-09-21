import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "src")
)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from claim_analyzer import ClaimAnalyzer


# ==========================================================
# Request Model
# ==========================================================

class ClaimRequest(BaseModel):
    """
    Flexible claim input model.

    Extra fields are allowed because the supplied public
    claim schema may contain additional attributes.
    """

    model_config = ConfigDict(extra="allow")

    claim_id: str = Field(
        ...,
        min_length=1,
        description="Unique claim identifier"
    )


# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title="Policy-Aware Multi-Agent RAG Claim Decision Engine",
    description=(
        "AI-powered health insurance claim analysis system "
        "using hybrid RAG, specialized agents, deterministic "
        "policy rules, citation validation, and abstention."
    ),
    version="1.0.0"
)


# ==========================================================
# Initialize Analyzer
# ==========================================================

try:
    analyzer = ClaimAnalyzer()
    analyzer_error = None

except Exception as error:
    analyzer = None
    analyzer_error = str(error)


# ==========================================================
# Helper Function
# ==========================================================

def build_response(result) -> Dict[str, Any]:
    """
    Convert ClaimState into a structured API response.
    """

    decision = result.decision_result or {}

    rule_findings = decision.get(
        "rule_findings",
        []
    )

    # Extract review-related missing evidence
    missing_evidence = []

    for finding in rule_findings:

        if finding.get("effect") == "REVIEW":

            missing_evidence.extend(
                finding.get(
                    "missing_evidence",
                    []
                )
            )

    # Remove duplicates while preserving order
    missing_evidence = list(
        dict.fromkeys(missing_evidence)
    )

    # Simple confidence mapping based on decision certainty.
    # This is deterministic and does not claim model confidence.
    if result.final_decision == "NEEDS_REVIEW":
        confidence = "LOW"

    elif result.final_decision in {
        "APPROVE",
        "REJECT"
    }:
        confidence = "HIGH"

    else:
        confidence = "MEDIUM"

    # Build concise key findings
    key_findings = []

    for finding in rule_findings:

        reason = finding.get("reason")

        if reason:
            key_findings.append(reason)

    if not key_findings and result.final_reason:
        key_findings.append(
            result.final_reason
        )

    # Execution trace
    trace = [
        {
            "agent": "hybrid_retriever",
            "action": "Retrieved relevant policy evidence",
            "retrieval_count": len(
                result.retrieved_chunks
            )
        },
        {
            "agent": "coverage_agent",
            "action": "Evaluated policy coverage"
        },
        {
            "agent": "exclusion_agent",
            "action": "Checked policy exclusions"
        },
        {
            "agent": "evidence_agent",
            "action": (
                "Validated policy and claim-level evidence"
            ),
            "status": result.evidence_result.get(
                "status"
            )
        },
        {
            "agent": "citation_validator",
            "action": "Validated policy citations",
            "status": result.citation_validation.get(
                "status"
            )
        },
        {
            "agent": "policy_rule_engine",
            "action": "Applied deterministic policy rules",
            "rule_count": len(rule_findings)
        },
        {
            "agent": "decision_engine",
            "action": "Generated final claim decision",
            "decision": result.final_decision
        }
    ]

    return {
        "case_id": result.claim_id,
        "claim_id": result.claim_id,

        "decision": result.final_decision,

        "confidence": confidence,

        "reason": result.final_reason,

        "key_findings": key_findings,

        "financial_summary": {
            "total_claimed_inr": decision.get(
                "total_claimed_inr",
                0
            ),
            "deductions_inr": decision.get(
                "deductions_inr",
                0
            ),
            "payable_amount_inr": decision.get(
                "payable_amount_inr",
                0
            )
        },

        "applicable_limits": decision.get(
            "applied_limits",
            []
        ),

        "applied_limits": decision.get(
            "applied_limits",
            []
        ),

        "missing_evidence": missing_evidence,

        "citations": result.citations,

        "citation_validation": (
            result.citation_validation
        ),

        "retrieved_documents": len(
            result.retrieved_chunks
        ),

        "rule_findings": rule_findings,

        "execution_trace": trace
    }


# ==========================================================
# Root Endpoint
# ==========================================================

@app.get("/")
def root():

    return {
        "message": (
            "Policy-Aware Claim Decision Engine API"
        ),
        "status": "running",
        "docs": "/docs"
    }


# ==========================================================
# Health Endpoint
# ==========================================================

@app.get("/health")
def health():

    if analyzer is None:

        return {
            "status": "error",
            "analyzer": "unavailable",
            "message": analyzer_error
        }

    return {
        "status": "healthy",
        "analyzer": "ready"
    }


# ==========================================================
# Main Analysis Endpoint
# ==========================================================

@app.post("/analyze")
def analyze(claim: ClaimRequest):

    if analyzer is None:

        raise HTTPException(
            status_code=500,
            detail=analyzer_error
        )

    try:

        # Convert validated request to dictionary
        claim_data = claim.model_dump(
            exclude_none=False
        )

        result = analyzer.analyze(
            claim_data
        )

        return build_response(result)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ==========================================================
# Backward-Compatible Endpoint
# ==========================================================

@app.post("/analyze-claim")
def analyze_claim(claim: ClaimRequest):

    if analyzer is None:

        raise HTTPException(
            status_code=500,
            detail=analyzer_error
        )

    try:

        claim_data = claim.model_dump(
            exclude_none=False
        )

        result = analyzer.analyze(
            claim_data
        )

        return build_response(result)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )