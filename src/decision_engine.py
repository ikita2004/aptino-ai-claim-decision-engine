class DecisionEngine:
    """
    Converts deterministic policy-rule findings into a final
    claim decision and calculates the payable amount.
    """

    def decide(self, claim, findings):

        expenses = claim.get("expenses_inr", {})

        sum_insured = claim.get("sum_insured_inr")

        # --------------------------------------------------
        # Calculate total submitted expenses
        # --------------------------------------------------

        expense_categories = [
            "room",
            "doctor_fees",
            "medicines_diagnostics",
            "pre_hospitalization",
            "post_hospitalization",
            "ambulance",
            "domiciliary",
            "package_charges"
        ]

        total_claimed = sum(
            float(expenses.get(category, 0) or 0)
            for category in expense_categories
        )

        # --------------------------------------------------
        # Check for explicit rejection
        # --------------------------------------------------

        rejection_findings = [
            finding
            for finding in findings
            if finding.get("effect") == "REJECT"
        ]

        if rejection_findings:

            reasons = [
                finding.get("reason", "")
                for finding in rejection_findings
            ]

            return {
                "decision": "REJECT",
                "reason": " ".join(reasons),
                "total_claimed_inr": total_claimed,
                "payable_amount_inr": 0.0,
                "deductions_inr": total_claimed,
                "applied_limits": [],
                "rule_findings": findings
            }

        # --------------------------------------------------
        # Calculate category-specific payable amounts
        # --------------------------------------------------

        payable = total_claimed
        deductions = 0.0
        applied_limits = []

        # --------------------------------------------------
        # Room rent
        # --------------------------------------------------

        room_expense = float(
            expenses.get("room", 0) or 0
        )

        room_limit_finding = next(
            (
                finding
                for finding in findings
                if finding.get("rule") == "ROOM_RENT_LIMIT"
            ),
            None
        )

        if room_limit_finding and sum_insured is not None:

            admission_hours = claim.get(
                "treatment", {}
            ).get("admission_hours")

            if admission_hours:
                admission_days = admission_hours / 24
            else:
                admission_days = 1

            room_limit = (
                float(sum_insured) * 0.01 * admission_days
            )

            room_payable = min(
                room_expense,
                room_limit
            )

            deduction = room_expense - room_payable

            payable -= deduction
            deductions += deduction

            applied_limits.append({
                "category": "room",
                "claimed_inr": room_expense,
                "allowed_inr": room_payable,
                "limit_inr": room_limit,
                "deduction_inr": deduction
            })

        # --------------------------------------------------
        # Doctor / surgeon fees
        # --------------------------------------------------

        doctor_fees = float(
            expenses.get("doctor_fees", 0) or 0
        )

        doctor_limit_finding = next(
            (
                finding
                for finding in findings
                if finding.get("rule")
                == "MEDICAL_PRACTITIONER_FEE_LIMIT"
            ),
            None
        )

        if doctor_limit_finding and sum_insured is not None:

            doctor_limit = float(sum_insured) * 0.25

            doctor_payable = min(
                doctor_fees,
                doctor_limit
            )

            deduction = doctor_fees - doctor_payable

            payable -= deduction
            deductions += deduction

            applied_limits.append({
                "category": "doctor_fees",
                "claimed_inr": doctor_fees,
                "allowed_inr": doctor_payable,
                "limit_inr": doctor_limit,
                "deduction_inr": deduction
            })

        # --------------------------------------------------
        # Medicines / diagnostics
        # --------------------------------------------------

        medicines = float(
            expenses.get(
                "medicines_diagnostics",
                0
            ) or 0
        )

        medicines_limit_finding = next(
            (
                finding
                for finding in findings
                if finding.get("rule")
                == "MEDICINES_DIAGNOSTICS_LIMIT"
            ),
            None
        )

        if medicines_limit_finding and sum_insured is not None:

            medicines_limit = (
                float(sum_insured) * 0.40
            )

            medicines_payable = min(
                medicines,
                medicines_limit
            )

            deduction = (
                medicines - medicines_payable
            )

            payable -= deduction
            deductions += deduction

            applied_limits.append({
                "category": "medicines_diagnostics",
                "claimed_inr": medicines,
                "allowed_inr": medicines_payable,
                "limit_inr": medicines_limit,
                "deduction_inr": deduction
            })

        # --------------------------------------------------
        # Domiciliary treatment
        # --------------------------------------------------

        domiciliary = float(
            expenses.get("domiciliary", 0) or 0
        )

        domiciliary_limit_finding = next(
            (
                finding
                for finding in findings
                if finding.get("rule")
                == "DOMICILIARY_SUB_LIMIT"
            ),
            None
        )

        if (
            domiciliary_limit_finding
            and sum_insured is not None
        ):

            domiciliary_limit = (
                float(sum_insured) * 0.20
            )

            domiciliary_payable = min(
                domiciliary,
                domiciliary_limit
            )

            deduction = (
                domiciliary - domiciliary_payable
            )

            payable -= deduction
            deductions += deduction

            applied_limits.append({
                "category": "domiciliary",
                "claimed_inr": domiciliary,
                "allowed_inr": domiciliary_payable,
                "limit_inr": domiciliary_limit,
                "deduction_inr": deduction
            })

        # --------------------------------------------------
        # Package charges
        # --------------------------------------------------

        package_charges = float(
            expenses.get("package_charges", 0) or 0
        )

        package_limit_finding = next(
            (
                finding
                for finding in findings
                if finding.get("rule")
                == "ANY_ONE_ILLNESS_PACKAGE_LIMIT"
            ),
            None
        )

        if (
            package_limit_finding
            and sum_insured is not None
        ):

            package_limit = (
                float(sum_insured) * 0.75
            )

            package_payable = min(
                package_charges,
                package_limit
            )

            deduction = (
                package_charges - package_payable
            )

            payable -= deduction
            deductions += deduction

            applied_limits.append({
                "category": "package_charges",
                "claimed_inr": package_charges,
                "allowed_inr": package_payable,
                "limit_inr": package_limit,
                "deduction_inr": deduction
            })

        # --------------------------------------------------
        # Determine whether evidence is insufficient
        # --------------------------------------------------

        review_findings = [
            finding
            for finding in findings
            if finding.get("effect") == "REVIEW"
        ]

        # --------------------------------------------------
        # Final decision
        # --------------------------------------------------

        if review_findings:

            review_reasons = [
                finding.get("reason", "")
                for finding in review_findings
            ]

            return {
                "decision": "NEEDS_REVIEW",
                "reason": " ".join(review_reasons),
                "total_claimed_inr": total_claimed,
                "payable_amount_inr": round(
                    max(payable, 0),
                    2
                ),
                "deductions_inr": round(
                    deductions,
                    2
                ),
                "applied_limits": applied_limits,
                "rule_findings": findings
            }

        # --------------------------------------------------
        # Approved claim
        # --------------------------------------------------

        if sum_insured is not None:

            payable = min(
                payable,
                float(sum_insured)
            )

        return {
            "decision": "APPROVE",
            "reason": (
                "The claim satisfies the evaluated policy "
                "rules and no exclusion or unresolved evidence "
                "issue was identified."
            ),
            "total_claimed_inr": total_claimed,
            "payable_amount_inr": round(
                max(payable, 0),
                2
            ),
            "deductions_inr": round(
                deductions,
                2
            ),
            "applied_limits": applied_limits,
            "rule_findings": findings
        }