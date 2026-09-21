import json
import sys
from pathlib import Path


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src")
)

from claim_analyzer import ClaimAnalyzer


# ---------------------------------------------------------
# EXPECTED PUBLIC CASE RESULTS
# Supplied public cases must NOT be modified.
# These expected results come from the original
# successful public-case test.
# ---------------------------------------------------------

PUBLIC_EXPECTED = {
    "PUB-001": "APPROVE",
    "PUB-002": "NEEDS_REVIEW",
    "PUB-003": "NEEDS_REVIEW",
    "PUB-004": "NEEDS_REVIEW",
    "PUB-005": "NEEDS_REVIEW",
    "PUB-006": "NEEDS_REVIEW",
    "PUB-007": "APPROVE",
    "PUB-008": "REJECT",
    "PUB-009": "APPROVE",
    "PUB-010": "NEEDS_REVIEW",
    "PUB-011": "NEEDS_REVIEW",
    "PUB-012": "REJECT",
}


# ---------------------------------------------------------
# EXPECTED ADDITIONAL CASE RESULTS
# These are our separately created evaluation cases.
# ---------------------------------------------------------

ADDITIONAL_EXPECTED = {
    "ADD-001": "APPROVE",
    "ADD-002": "NEEDS_REVIEW",
    "ADD-003": "APPROVE",
    "ADD-004": "NEEDS_REVIEW",
    "ADD-005": "REJECT",
}


# ---------------------------------------------------------
# LOAD JSON
# ---------------------------------------------------------

def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ---------------------------------------------------------
# GET CASE ID
# Public cases use "case_id".
# Additional cases use "claim_id".
# ---------------------------------------------------------

def get_case_id(case):
    return (
        case.get("case_id")
        or case.get("claim_id")
    )


# ---------------------------------------------------------
# NORMALIZE CASE FOR CLAIM ANALYZER
#
# Public Aptino cases:
#     case_id
#
# ClaimState expects:
#     claim_id
#
# We create a copy and convert the field.
# The original JSON is NEVER modified.
# ---------------------------------------------------------

def prepare_case_for_analysis(case):
    case_for_analysis = dict(case)

    if "case_id" in case_for_analysis:
        case_for_analysis["claim_id"] = (
            case_for_analysis.pop("case_id")
        )

    return case_for_analysis


# ---------------------------------------------------------
# EVALUATE CASES
# ---------------------------------------------------------

def evaluate_cases(
    analyzer,
    cases,
    expected_map,
    label
):
    results = []

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    for case in cases:

        case_id = get_case_id(case)

        expected = expected_map.get(
            case_id
        )

        # Convert case_id -> claim_id
        # without changing the source JSON.
        case_for_analysis = (
            prepare_case_for_analysis(case)
        )

        try:

            # -------------------------------------------------
            # RUN FULL CLAIM ANALYSIS
            # -------------------------------------------------

            result = analyzer.analyze(
                case_for_analysis
            )

            actual = result.final_decision

                      # -------------------------------------------------
            # CITATIONS
            # -------------------------------------------------

            citations = (
                result.citations
                or []
            )

            citation_validation = (
                result.citation_validation
                or {}
            )

            valid_citations = 0

            if citation_validation.get("status") == "VALID":
                valid_citations = len(citations)

            else:
                valid_citations = len(
                    citation_validation.get(
                        "valid_citations",
                        []
                    )
                )

            # -------------------------------------------------
            # CITATION STATUS
            # -------------------------------------------------

            if not citations:
                citation_validation_status = (
                    "NO_CITATIONS"
                )

            else:
                citation_validation_status = (
                    "VALID"
                    if valid_citations == len(citations)
                    else "INVALID"
                )

            # -------------------------------------------------
            # DECISION CHECK
            # -------------------------------------------------

            passed = (
                actual == expected
            )

            # -------------------------------------------------
            # FINANCIAL INFORMATION
            # -------------------------------------------------

            decision_result = (
                result.decision_result
                or {}
            )

            total_claimed = (
                decision_result.get(
                    "total_claimed_inr",
                    0
                )
            )

            deductions = (
                decision_result.get(
                    "deductions_inr",
                    0
                )
            )

            payable = (
                decision_result.get(
                    "payable_amount_inr",
                    0
                )
            )

            # -------------------------------------------------
            # SAVE RESULT
            # -------------------------------------------------

            result_row = {

                "case_id": case_id,

                "expected_decision": expected,

                "actual_decision": actual,

                "passed": passed,

                "total_claimed_inr": (
                    total_claimed
                ),

                "deductions_inr": (
                    deductions
                ),

                "payable_amount_inr": (
                    payable
                ),

                "citation_count": (
                    len(citations)
                ),

                "valid_citation_count": (
                    valid_citations
                ),

                "citation_validation": (
                    citation_validation_status
                ),

                "citation_validation_details": (
                    citation_validation
                ),

                "retrieved_documents": (
                    len(
                        result.retrieved_chunks
                        or []
                    )
                ),

                "reason": (
                    result.final_reason
                ),
            }

            results.append(
                result_row
            )

            # -------------------------------------------------
            # PRINT RESULT
            # -------------------------------------------------

            status_text = (
                "PASS"
                if passed
                else "FAIL"
            )

            print(
                f"{case_id:<10} "
                f"Expected={expected:<14} "
                f"Actual={actual:<14} "
                f"{status_text}"
            )

        except Exception as error:

            # -------------------------------------------------
            # HANDLE CASE ERRORS
            # -------------------------------------------------

            results.append(
                {
                    "case_id": case_id,

                    "expected_decision": (
                        expected
                    ),

                    "actual_decision": None,

                    "passed": False,

                    "error": str(error),

                    "error_type": (
                        type(error).__name__
                    ),
                }
            )

            print(
                f"{case_id:<10} "
                f"ERROR "
                f"{type(error).__name__}: "
                f"{error}"
            )

    return results


# ---------------------------------------------------------
# CALCULATE METRICS
# ---------------------------------------------------------

def calculate_metrics(results):

    total = len(results)

    passed = sum(
        1
        for result in results
        if result.get("passed") is True
    )

    failed = (
        total - passed
    )

    # -----------------------------------------------------
    # CITATION METRICS
    # -----------------------------------------------------

    total_citations = sum(
        result.get(
            "citation_count",
            0
        )
        for result in results
    )

    valid_citations = sum(
        result.get(
            "valid_citation_count",
            0
        )
        for result in results
    )

    citation_rate = (

        valid_citations
        / total_citations

        if total_citations
        else 0
    )

    # -----------------------------------------------------
    # NEEDS REVIEW COUNT
    # -----------------------------------------------------

    review_cases = sum(

        1

        for result in results

        if result.get(
            "actual_decision"
        )
        == "NEEDS_REVIEW"
    )

    # -----------------------------------------------------
    # APPROVE COUNT
    # -----------------------------------------------------

    approve_cases = sum(

        1

        for result in results

        if result.get(
            "actual_decision"
        )
        == "APPROVE"
    )

    # -----------------------------------------------------
    # REJECT COUNT
    # -----------------------------------------------------

    reject_cases = sum(

        1

        for result in results

        if result.get(
            "actual_decision"
        )
        == "REJECT"
    )

    # -----------------------------------------------------
    # RETURN METRICS
    # -----------------------------------------------------

    return {

        "total_cases": total,

        "passed_cases": passed,

        "failed_cases": failed,

        "case_success_rate": (

            passed / total

            if total

            else 0
        ),

        "total_citations": (
            total_citations
        ),

        "valid_citations": (
            valid_citations
        ),

        "citation_validation_rate": (
            citation_rate
        ),

        "needs_review_cases": (
            review_cases
        ),

        "approve_cases": (
            approve_cases
        ),

        "reject_cases": (
            reject_cases
        ),
    }


# ---------------------------------------------------------
# PRINT METRICS
# ---------------------------------------------------------

def print_metrics(metrics):

    print()

    print("-" * 70)

    print("METRICS")

    print("-" * 70)

    print(
        f"Cases:                 "
        f"{metrics['passed_cases']}/"
        f"{metrics['total_cases']}"
    )

    print(
        f"Case success rate:     "
        f"{metrics['case_success_rate'] * 100:.2f}%"
    )

    print(
        f"Citations validated:   "
        f"{metrics['valid_citations']}/"
        f"{metrics['total_citations']}"
    )

    print(
        f"Citation validation:   "
        f"{metrics['citation_validation_rate'] * 100:.2f}%"
    )

    print(
        f"APPROVE cases:         "
        f"{metrics['approve_cases']}"
    )

    print(
        f"REJECT cases:          "
        f"{metrics['reject_cases']}"
    )

    print(
        f"NEEDS_REVIEW cases:    "
        f"{metrics['needs_review_cases']}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    # -----------------------------------------------------
    # FILE PATHS
    # -----------------------------------------------------

    public_path = (
        PROJECT_ROOT
        / "data"
        / "cases"
        / "public_test_cases.json"
    )

    additional_path = (
        PROJECT_ROOT
        / "data"
        / "cases"
        / "additional_test_cases.json"
    )

    output_path = (
        PROJECT_ROOT
        / "data"
        / "evaluation_results.json"
    )

    # -----------------------------------------------------
    # LOAD CASES
    # -----------------------------------------------------

    public_cases = load_json(
        public_path
    )

    additional_cases = load_json(
        additional_path
    )

    print(
        f"Public cases loaded: "
        f"{len(public_cases)}"
    )

    print(
        f"Additional cases loaded: "
        f"{len(additional_cases)}"
    )

    # -----------------------------------------------------
    # INITIALIZE ANALYZER
    # -----------------------------------------------------

    analyzer = ClaimAnalyzer()

    # -----------------------------------------------------
    # PUBLIC CASES
    # -----------------------------------------------------

    public_results = evaluate_cases(

        analyzer,

        public_cases,

        PUBLIC_EXPECTED,

        "PUBLIC CASES",
    )

    # -----------------------------------------------------
    # ADDITIONAL CASES
    # -----------------------------------------------------

    additional_results = evaluate_cases(

        analyzer,

        additional_cases,

        ADDITIONAL_EXPECTED,

        "ADDITIONAL CASES",
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    public_metrics = calculate_metrics(
        public_results
    )

    additional_metrics = calculate_metrics(
        additional_results
    )

    # -----------------------------------------------------
    # OVERALL RESULTS
    # -----------------------------------------------------

    all_results = (
        public_results
        + additional_results
    )

    overall_metrics = calculate_metrics(
        all_results
    )

    # -----------------------------------------------------
    # PRINT PUBLIC METRICS
    # -----------------------------------------------------

    print()

    print("=" * 70)

    print("PUBLIC CASE METRICS")

    print("=" * 70)

    print_metrics(
        public_metrics
    )

    # -----------------------------------------------------
    # PRINT ADDITIONAL METRICS
    # -----------------------------------------------------

    print()

    print("=" * 70)

    print("ADDITIONAL CASE METRICS")

    print("=" * 70)

    print_metrics(
        additional_metrics
    )

    # -----------------------------------------------------
    # PRINT OVERALL METRICS
    # -----------------------------------------------------

    print()

    print("=" * 70)

    print("OVERALL METRICS")

    print("=" * 70)

    print_metrics(
        overall_metrics
    )

    # -----------------------------------------------------
    # BUILD EVALUATION OUTPUT
    # -----------------------------------------------------

    evaluation_output = {

        "evaluation": {

            "public_cases": (
                public_results
            ),

            "additional_cases": (
                additional_results
            ),

            "metrics": {

                "public": (
                    public_metrics
                ),

                "additional": (
                    additional_metrics
                ),

                "overall": (
                    overall_metrics
                ),
            },
        }
    }

    # -----------------------------------------------------
    # SAVE RESULTS
    # -----------------------------------------------------

    with open(

        output_path,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            evaluation_output,

            file,

            indent=2,
        )

    # -----------------------------------------------------
    # FINAL MESSAGE
    # -----------------------------------------------------

    print()

    print(
        "Evaluation results saved to:"
    )

    print(
        output_path
    )


# ---------------------------------------------------------
# RUN SCRIPT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()

