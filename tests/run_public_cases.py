import json
import sys
from pathlib import Path

# Allow imports from src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from claim_analyzer import ClaimAnalyzer


PUBLIC_CASES_FILE = PROJECT_ROOT / "data" / "cases" / "public_test_cases.json"


def main():
    print("=" * 70)
    print("PUBLIC TEST CASES - CLAIM ANALYZER")
    print("=" * 70)

    # Load public test cases
    with open(PUBLIC_CASES_FILE, "r", encoding="utf-8") as file:
        public_cases = json.load(file)

    print(f"\nLoaded {len(public_cases)} public test cases.")

    # Initialize analyzer once
    print("\nInitializing Claim Analyzer...")
    analyzer = ClaimAnalyzer()

    results = []
    errors = []

    print("\n" + "=" * 70)
    print("RUNNING TEST CASES")
    print("=" * 70)

    for index, raw_case in enumerate(public_cases, start=1):

        # Copy the case so the original JSON is never modified
        case = dict(raw_case)

        case_id = case.get("case_id", f"CASE-{index}")

        # ClaimAnalyzer expects claim_id
        case["claim_id"] = case.pop("case_id", case_id)

        print(f"\n[{index}/{len(public_cases)}] Running {case_id}...")
        print("-" * 70)

        try:
            result = analyzer.analyze(case)

            decision = result.final_decision
            reason = result.final_reason

            decision_result = result.decision_result or {}

            total_claimed = decision_result.get(
                "total_claimed_inr", 0
            )

            payable = decision_result.get(
                "payable_amount_inr", 0
            )

            deductions = decision_result.get(
                "deductions_inr", 0
            )

            print(f"Decision       : {decision}")
            print(f"Reason         : {reason}")
            print(f"Total Claimed  : ₹{total_claimed:,.2f}")
            print(f"Deductions     : ₹{deductions:,.2f}")
            print(f"Payable Amount : ₹{payable:,.2f}")
            print(
                f"Citations      : {len(result.citations)}"
            )
            print(
                f"Retrieved Docs : {len(result.retrieved_chunks)}"
            )

            citation_status = (
                result.citation_validation.get(
                    "status", "UNKNOWN"
                )
            )

            print(
                f"Citation Status: {citation_status}"
            )

            results.append(
                {
                    "case_id": case_id,
                    "decision": decision,
                    "total_claimed": total_claimed,
                    "deductions": deductions,
                    "payable": payable,
                    "citation_status": citation_status,
                }
            )

        except Exception as error:
            print(f"ERROR: {error}")

            errors.append(
                {
                    "case_id": case_id,
                    "error": str(error),
                }
            )

    # Final summary
    print("\n")
    print("=" * 70)
    print("PUBLIC TEST CASE SUMMARY")
    print("=" * 70)

    print(
        f"{'Case ID':<12}"
        f"{'Decision':<18}"
        f"{'Payable':>15}"
        f"{'Citations':>12}"
    )

    print("-" * 70)

    for result in results:

        print(
            f"{result['case_id']:<12}"
            f"{result['decision']:<18}"
            f"₹{result['payable']:>13,.2f}"
            f"{result['citation_status']:>12}"
        )

    print("-" * 70)

    print(f"\nSuccessful cases : {len(results)}")
    print(f"Failed cases     : {len(errors)}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(
                f"- {error['case_id']}: "
                f"{error['error']}"
            )

    print("\n" + "=" * 70)
    print("TEST RUN COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()