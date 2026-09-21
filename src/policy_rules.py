class PolicyRuleEngine:
    """
    Deterministic policy rule engine.

    Rules are based on the supplied Universal Sompo
    CSC Individual Health Insurance 2017-2018
    policy wording.
    """

    def evaluate(self, claim):

        findings = []

        treatment = claim.get("treatment", {})
        hospital = claim.get("hospital", {})
        expenses = claim.get("expenses_inr", {})

        coverage_months = claim.get(
            "continuous_coverage_months"
        )

        prior_years = claim.get(
            "prior_insurer_continuous_years"
        )

        treatment_type = treatment.get(
            "type"
        )

        admission_hours = treatment.get(
            "admission_hours"
        )

        pre_existing = treatment.get(
            "pre_existing"
        )

        experimental = treatment.get(
            "experimental"
        )

        diagnosis = (
            treatment.get("diagnosis") or ""
        ).lower()

        procedure = (
            treatment.get("procedure") or ""
        ).lower()

                # ==================================================
        # RULE 1
        # 30 DAYS INITIAL WAITING PERIOD
        # Policy Page 9
        # ==================================================

        if coverage_months is not None:

            if coverage_months == 0:

                if (
                    prior_years is not None
                    and prior_years >= 1
                ):

                    findings.append({
                        "rule": "INITIAL_WAITING_PERIOD",
                        "status": "WAIVED",
                        "effect": "NO_RESTRICTION",
                        "reason": (
                            "The policy provides an exception "
                            "to the 30-day waiting period where "
                            "the insured has been continuously "
                            "covered for at least one year under "
                            "a qualifying Indian individual health "
                            "insurance policy."
                        ),
                        "citation": "Policy Page 9"
                    })

                else:

                    findings.append({
                        "rule": "INITIAL_WAITING_PERIOD",
                        "status": "TRIGGERED",
                        "effect": "REVIEW",
                        "reason": (
                            "A 30-day waiting period applies "
                            "to claims unless a stated policy "
                            "exception applies."
                        ),
                        "citation": "Policy Page 9"
                    })


        # ==================================================
        # RULE 2
        # PRE-EXISTING DISEASE / LISTED DISEASE WAITING
        # Policy Pages 8 and 9
        # ==================================================

        if pre_existing is True:

            if coverage_months is None:

                findings.append({
                    "rule": "PRE_EXISTING_DISEASE",
                    "status": "INSUFFICIENT_INFORMATION",
                    "effect": "REVIEW",
                    "reason": (
                        "The claim identifies a pre-existing "
                        "disease, but continuous coverage "
                        "duration is missing."
                    ),
                    "citation": "Policy Page 8"
                })

            elif coverage_months < 48:

                findings.append({
                    "rule": "PRE_EXISTING_DISEASE",
                    "status": "TRIGGERED",
                    "effect": "REVIEW",
                    "reason": (
                        "Pre-existing diseases are not covered "
                        "until 48 months of continuous coverage "
                        "have elapsed, subject to the policy's "
                        "prior-coverage provisions."
                    ),
                    "citation": "Policy Page 8"
                })

            else:

                findings.append({
                    "rule": "PRE_EXISTING_DISEASE",
                    "status": "NOT_TRIGGERED",
                    "effect": "NO_RESTRICTION",
                    "reason": (
                        "The claim indicates at least 48 months "
                        "of continuous coverage."
                    ),
                    "citation": "Policy Page 8"
                })


        # --------------------------------------------------
        # LISTED DISEASES WITH ONE-YEAR WAITING PERIOD
        # Policy Page 9
        # --------------------------------------------------

        listed_disease_keywords = [
            "cataract",
            "bph",
            "myomectomy",
            "hysterectomy",
            "hernia",
            "hydrocele",
            "fistula",
            "piles",
            "arthritis",
            "gout",
            "rheumatism",
            "joint replacement",
            "sinusitis",
            "urinary stone",
            "urinary stones",
            "biliary stone",
            "biliary stones",
            "d&c",
            "skin tumor",
            "internal tumor",
            "cyst",
            "nodule",
            "polyp",
            "dialysis",
            "tonsil",
            "sinus surgery",
            "gastric ulcer",
            "duodenal ulcer"
        ]

        listed_disease = any(
            keyword in diagnosis
            or keyword in procedure
            for keyword in listed_disease_keywords
        )

        if listed_disease:

            prior_policy = claim.get(
                "prior_policy",
                {}
            )

            prior_insurer_type = (
                prior_policy.get(
                    "insurer_type"
                ) or ""
            ).lower()

            prior_policy_years = prior_policy.get(
                "continuous_years",
                prior_years
            )

            database_history_received = prior_policy.get(
                "database_and_claim_history_received",
                False
            )

            previous_sum_insured = prior_policy.get(
                "previous_sum_insured_inr"
            )

            current_sum_insured = claim.get(
                "sum_insured_inr"
            )

            qualifying_prior_coverage = (
                prior_insurer_type
                == "indian individual health insurer"
                and prior_policy_years is not None
                and prior_policy_years >= 1
                and database_history_received is True
            )

            if qualifying_prior_coverage:

                # Previous Sum Insured is equal to or greater
                # than current Sum Insured.
                if (
                    previous_sum_insured is not None
                    and current_sum_insured is not None
                    and previous_sum_insured >= current_sum_insured
                ):

                    findings.append({
                        "rule": "LISTED_DISEASE_WAITING_PERIOD",
                        "status": "WAIVED",
                        "effect": "NO_RESTRICTION",
                        "reason": (
                            f"{diagnosis.title()} is subject to "
                            "a one-year waiting period. However, "
                            f"the insured has {prior_policy_years} "
                            "year(s) of continuous qualifying "
                            "prior coverage with an Indian "
                            "individual health insurer. The "
                            f"previous Sum Insured of INR "
                            f"{previous_sum_insured:,.2f} is equal "
                            f"to or greater than the current Sum "
                            f"Insured of INR "
                            f"{current_sum_insured:,.2f}, so the "
                            "waiting-period reduction applies "
                            "to the full current Sum Insured."
                        ),
                        "citation": "Policy Page 9"
                    })

                # Current Sum Insured is greater than the
                # previous Sum Insured.
                elif (
                    previous_sum_insured is not None
                    and current_sum_insured is not None
                    and current_sum_insured > previous_sum_insured
                ):

                    excess_sum_insured = (
                        current_sum_insured
                        - previous_sum_insured
                    )

                    findings.append({
                        "rule": "LISTED_DISEASE_WAITING_PERIOD",
                        "status": "PARTIALLY_WAIVED",
                        "effect": "REVIEW",
                        "reason": (
                            f"{diagnosis.title()} is subject to "
                            "a one-year waiting period. The "
                            f"insured has {prior_policy_years} "
                            "year(s) of qualifying continuous "
                            "prior coverage. The waiting-period "
                            "reduction applies only up to the "
                            f"previous Sum Insured of INR "
                            f"{previous_sum_insured:,.2f}. The "
                            f"additional current Sum Insured of "
                            f"INR {excess_sum_insured:,.2f} remains "
                            "subject to the applicable waiting "
                            "period."
                        ),
                        "citation": "Policy Page 9"
                    })

                else:

                    findings.append({
                        "rule": "LISTED_DISEASE_WAITING_PERIOD",
                        "status": "WAIVED",
                        "effect": "NO_RESTRICTION",
                        "reason": (
                            f"{diagnosis.title()} is subject to "
                            "a one-year waiting period, but the "
                            "claim provides qualifying continuous "
                            f"prior coverage of {prior_policy_years} "
                            "year(s)."
                        ),
                        "citation": "Policy Page 9"
                    })

            elif (
                coverage_months is not None
                and coverage_months < 12
            ):

                findings.append({
                    "rule": "LISTED_DISEASE_WAITING_PERIOD",
                    "status": "TRIGGERED",
                    "effect": "REVIEW",
                    "reason": (
                        f"{diagnosis.title()} is subject to "
                        "a one-year waiting period and the "
                        f"current continuous coverage is only "
                        f"{coverage_months} month(s). No "
                        "qualifying prior coverage exception "
                        "has been established."
                    ),
                    "citation": "Policy Page 9"
                })


        # ==================================================
        # RULE 3
        # PRIOR INSURER COVERAGE / WAITING PERIOD REDUCTION
        # Policy Page 8
        # ==================================================

        if (
            prior_years is not None
            and prior_years >= 1
        ):

            prior_policy = claim.get(
                "prior_policy",
                {}
            )

            prior_insurer_type = (
                prior_policy.get(
                    "insurer_type"
                ) or ""
            ).lower()

            prior_policy_years = prior_policy.get(
                "continuous_years",
                prior_years
            )

            database_history_received = prior_policy.get(
                "database_and_claim_history_received",
                False
            )

            previous_sum_insured = prior_policy.get(
                "previous_sum_insured_inr"
            )

            current_sum_insured = claim.get(
                "sum_insured_inr"
            )

            qualifying_prior_coverage = (
                prior_insurer_type
                == "indian individual health insurer"
                and prior_policy_years is not None
                and prior_policy_years >= 1
                and database_history_received is True
            )

            if qualifying_prior_coverage:

                if (
                    previous_sum_insured is not None
                    and current_sum_insured is not None
                    and previous_sum_insured >= current_sum_insured
                ):

                    findings.append({
                        "rule": "PRIOR_INSURER_COVERAGE",
                        "status": "APPLICABLE",
                        "effect": "WAITING_PERIOD_REDUCED",
                        "reason": (
                            f"The insured has {prior_policy_years} "
                            "year(s) of continuous prior coverage "
                            "with a qualifying Indian individual "
                            "health insurer. The previous Sum "
                            f"Insured of INR "
                            f"{previous_sum_insured:,.2f} covers "
                            f"the current Sum Insured of INR "
                            f"{current_sum_insured:,.2f}. The "
                            "applicable waiting period can therefore "
                            "be reduced for the full current Sum "
                            "Insured, subject to verification of "
                            "prior coverage and claim history."
                        ),
                        "citation": "Policy Page 8"
                    })

                elif (
                    previous_sum_insured is not None
                    and current_sum_insured is not None
                    and current_sum_insured > previous_sum_insured
                ):

                    excess_sum_insured = (
                        current_sum_insured
                        - previous_sum_insured
                    )

                    findings.append({
                        "rule": "PRIOR_INSURER_COVERAGE",
                        "status": "PARTIALLY_APPLICABLE",
                        "effect": "WAITING_PERIOD_REDUCED_PARTIALLY",
                        "reason": (
                            f"The insured has {prior_policy_years} "
                            "year(s) of qualifying continuous "
                            "prior coverage. The waiting-period "
                            f"reduction applies up to the previous "
                            f"Sum Insured of INR "
                            f"{previous_sum_insured:,.2f}. The "
                            f"additional Sum Insured of INR "
                            f"{excess_sum_insured:,.2f} remains "
                            "subject to the applicable waiting "
                            "period."
                        ),
                        "citation": "Policy Page 8"
                    })

                else:

                    findings.append({
                        "rule": "PRIOR_INSURER_COVERAGE",
                        "status": "APPLICABLE",
                        "effect": "WAITING_PERIOD_REDUCED",
                        "reason": (
                            f"The insured has {prior_policy_years} "
                            "year(s) of qualifying continuous "
                            "prior coverage. The waiting-period "
                            "reduction is applicable subject to "
                            "verification of prior coverage and "
                            "claim history."
                        ),
                        "citation": "Policy Page 8"
                    })

            else:

                findings.append({
                    "rule": "PRIOR_INSURER_COVERAGE",
                    "status": "NOT_ESTABLISHED",
                    "effect": "REVIEW",
                    "reason": (
                        "Prior continuous coverage is reported, "
                        "but the available prior-policy details "
                        "do not establish all qualifying conditions "
                        "for the waiting-period reduction."
                    ),
                    "citation": "Policy Page 8"
                })

        # ==================================================
        # RULE 4
        # EXPERIMENTAL / UNPROVEN TREATMENT
        # Policy Pages 6 and 10
        # ==================================================

        if experimental is True:

            findings.append({
                "rule": "EXPERIMENTAL_TREATMENT",
                "status": "TRIGGERED",
                "effect": "REJECT",
                "reason": (
                    "The policy excludes treatment that is "
                    "experimental or unproven and is not "
                    "based on established medical practice "
                    "in India."
                ),
                "citation": "Policy Pages 6 and 10"
            })

        # ==================================================
        # RULE 5
        # COSMETIC / AESTHETIC TREATMENT
        # Policy Page 9
        # ==================================================

        cosmetic_keywords = [
            "cosmetic",
            "aesthetic"
        ]

        injury_or_disease_keywords = [
            "injury",
            "disease",
            "trauma",
            "accident"
        ]

        is_cosmetic = any(
            keyword in diagnosis
            or keyword in procedure
            for keyword in cosmetic_keywords
        )

        is_plastic_surgery = (
            "plastic surgery" in procedure
        )

        has_injury_or_disease_exception = any(
            keyword in diagnosis
            or keyword in procedure
            for keyword in injury_or_disease_keywords
        )

        if is_cosmetic:

            findings.append({
                "rule": "COSMETIC_TREATMENT",
                "status": "TRIGGERED",
                "effect": "REJECT",
                "reason": (
                    "The claim identifies cosmetic or "
                    "aesthetic treatment, which is excluded "
                    "under the policy."
                ),
                "citation": "Policy Page 9"
            })

        elif (
            is_plastic_surgery
            and not has_injury_or_disease_exception
        ):

            findings.append({
                "rule": "PLASTIC_SURGERY_EXCLUSION",
                "status": "REVIEW_REQUIRED",
                "effect": "REVIEW",
                "reason": (
                    "Plastic surgery is identified, but the "
                    "claim does not establish the policy "
                    "exception relating to treatment of "
                    "injury or disease."
                ),
                "citation": "Policy Page 9"
            })

        # ==================================================
        # RULE 6
        # OUTPATIENT TREATMENT
        # Policy Page 10
        # ==================================================

        if treatment_type == "outpatient":

            findings.append({
                "rule": "OUTPATIENT_TREATMENT",
                "status": "TRIGGERED",
                "effect": "REJECT",
                "reason": (
                    "The policy excludes expenses for "
                    "treatment as an outpatient in a hospital."
                ),
                "citation": "Policy Page 10"
            })

        # ==================================================
        # RULE 7
        # TREATMENT NOT EXCEEDING 3 DAYS
        # Policy Page 10
        # ==================================================

        if (
            admission_hours is not None
            and admission_hours < 72
            and treatment_type == "inpatient"
        ):

            findings.append({
                "rule": "THREE_DAY_EXCLUSION",
                "status": "POTENTIALLY_TRIGGERED",
                "effect": "REVIEW",
                "reason": (
                    "The policy contains an exclusion for "
                    "any treatment not exceeding three days. "
                    "The claim requires policy-specific "
                    "assessment."
                ),
                "citation": "Policy Page 10"
            })

         # ==================================================
        # RULE 8
        # DAY CARE TREATMENT
        # Policy Pages 2 and 7
        # ==================================================

        if treatment_type == "day_care":

            admission_hours = treatment.get(
                "admission_hours"
            )

            diagnosis = (
                treatment.get("diagnosis") or ""
            ).lower()

            procedure = (
                treatment.get("procedure") or ""
            ).lower()

            day_care_text = (
                diagnosis + " " + procedure
            )

            # Procedures specifically mentioned
            # in the policy as Day Care Procedures
            listed_day_care_keywords = [
                "dialysis",
                "chemotherapy",
                "chemo",
                "radiotherapy",
                "radiation therapy",
                "eye surgery",
                "cataract",
                "lithotripsy",
                "tonsillectomy",
                "d&c",
                "dilation and curettage"
            ]

            is_listed_day_care = any(
                keyword in day_care_text
                for keyword in listed_day_care_keywords
            )

            if admission_hours is None:

                findings.append({
                    "rule": "DAY_CARE_DEFINITION",
                    "status": "INSUFFICIENT_INFORMATION",
                    "effect": "REVIEW",
                    "reason": (
                        "Admission duration is missing. "
                        "Day Care Treatment requires assessment "
                        "of the treatment and hospitalization "
                        "requirement."
                    ),
                    "citation": "Policy Page 2"
                })

            elif admission_hours < 24:

                if is_listed_day_care:

                    findings.append({
                        "rule": "DAY_CARE_DEFINITION",
                        "status": "POTENTIALLY_ELIGIBLE",
                        "effect": "REVIEW",
                        "reason": (
                            "The treatment is a listed Day Care "
                            "Procedure and was completed in less "
                            "than 24 hours. Final eligibility "
                            "requires confirmation that the "
                            "treatment satisfies the policy's "
                            "Day Care Treatment definition."
                        ),
                        "citation": "Policy Pages 2 and 7"
                    })

                else:

                    findings.append({
                        "rule": "DAY_CARE_DEFINITION",
                        "status": "REVIEW_REQUIRED",
                        "effect": "REVIEW",
                        "reason": (
                            "The treatment was completed in less "
                            "than 24 hours. The policy's Day Care "
                            "Treatment conditions must be verified, "
                            "including whether the treatment would "
                            "otherwise require hospitalization "
                            "exceeding 24 hours."
                        ),
                        "citation": "Policy Page 2"
                    })

            else:

                findings.append({
                    "rule": "DAY_CARE_DEFINITION",
                    "status": "REVIEW_REQUIRED",
                    "effect": "REVIEW",
                    "reason": (
                        "The treatment duration is 24 hours or "
                        "more. Verify whether the treatment should "
                        "instead be assessed under inpatient "
                        "hospitalization provisions."
                    ),
                    "citation": "Policy Page 2"
                })
                
        # ==================================================
        # RULE 9
        # DOMICILIARY TREATMENT
        # Policy Page 2
        # ==================================================

        if treatment_type == "domiciliary":

            room_unavailable = treatment.get(
                "hospital_room_unavailable"
            )

            patient_cannot_move = treatment.get(
                "patient_cannot_be_moved"
            )

            if (
                room_unavailable is True
                or patient_cannot_move is True
            ):

                findings.append({
                    "rule": "DOMICILIARY_TREATMENT",
                    "status": "CONDITION_SATISFIED",
                    "effect": "REVIEW",
                    "reason": (
                        "The policy definition allows "
                        "domiciliary treatment where the "
                        "patient cannot be removed to a "
                        "Hospital or treatment is taken "
                        "at home because a Hospital room "
                        "is unavailable."
                    ),
                    "citation": "Policy Page 2"
                })

            else:

                findings.append({
                    "rule": "DOMICILIARY_TREATMENT",
                    "status": "CONDITION_NOT_ESTABLISHED",
                    "effect": "REVIEW",
                    "reason": (
                        "The policy requires either the "
                        "patient's condition to prevent "
                        "removal to a Hospital or "
                        "non-availability of a Hospital room."
                    ),
                    "citation": "Policy Page 2"
                })

        # ==================================================
        # RULE 10
        # PRE-HOSPITALIZATION WINDOW
        # Policy Page 8
        # ==================================================

        expense_timing = claim.get(
            "expense_timing",
            {}
        )

        pre_days = expense_timing.get(
            "pre_hospitalization_days_before_admission"
        )

        pre_expense = expenses.get(
            "pre_hospitalization",
            0
        )

        if pre_days is not None and pre_expense > 0:

            if pre_days <= 30:

                findings.append({
                    "rule": "PRE_HOSPITALIZATION_WINDOW",
                    "status": "WITHIN_LIMIT",
                    "effect": "ALLOW",
                    "reason": (
                        f"Pre-hospitalization expenses were "
                        f"incurred {pre_days} day(s) before "
                        "admission, which is within the "
                        "policy maximum of 30 days."
                    ),
                    "citation": "Policy Page 8"
                })

            else:

                findings.append({
                    "rule": "PRE_HOSPITALIZATION_WINDOW",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Pre-hospitalization expenses were "
                        f"incurred {pre_days} day(s) before "
                        "admission, exceeding the policy "
                        "maximum of 30 days."
                    ),
                    "citation": "Policy Page 8"
                })

        # ==================================================
        # RULE 11
        # POST-HOSPITALIZATION WINDOW
        # Policy Page 8
        # ==================================================

        post_days = expense_timing.get(
            "post_hospitalization_days_after_discharge"
        )

        post_expense = expenses.get(
            "post_hospitalization",
            0
        )

        same_condition = expense_timing.get(
            "same_condition_confirmed"
        )

        if post_days is not None and post_expense > 0:

            if post_days > 60:

                findings.append({
                    "rule": "POST_HOSPITALIZATION_WINDOW",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Post-hospitalization expenses were "
                        f"incurred {post_days} day(s) after "
                        "discharge, exceeding the policy "
                        "maximum of 60 days."
                    ),
                    "citation": "Policy Page 8"
                })

            elif same_condition is not True:

                findings.append({
                    "rule": "POST_HOSPITALIZATION_CONDITION",
                    "status": "REVIEW_REQUIRED",
                    "effect": "REVIEW",
                    "reason": (
                        "Post-hospitalization expenses are "
                        "present, but the claim does not "
                        "confirm that they relate to the same "
                        "condition for which hospitalization "
                        "was admissible."
                    ),
                    "citation": "Policy Page 8"
                })

            else:

                findings.append({
                    "rule": "POST_HOSPITALIZATION_WINDOW",
                    "status": "WITHIN_LIMIT",
                    "effect": "ALLOW",
                    "reason": (
                        f"Post-hospitalization expenses were "
                        f"incurred {post_days} day(s) after "
                        "discharge and are within the policy "
                        "maximum of 60 days. The same condition "
                        "is confirmed."
                    ),
                    "citation": "Policy Page 8"
                })

        # ==================================================
        # RULE 12
        # EVIDENCE SUFFICIENCY
        # ==================================================

        if "evidence_context" in claim:

            evidence_context = claim.get(
                "evidence_context",
                {}
            )

            hospital_registered = evidence_context.get(
                "hospital_registered"
            )

            medical_necessity_confirmed = evidence_context.get(
                "medical_necessity_confirmed"
            )

            minimum_criteria = evidence_context.get(
                "hospital_minimum_criteria_documented"
            )

            if (
                hospital_registered is None
                or medical_necessity_confirmed is None
            ):

                findings.append({
                    "rule": "EVIDENCE_SUFFICIENCY",
                    "status": "INSUFFICIENT_INFORMATION",
                    "effect": "REVIEW",
                    "reason": (
                        "Required claim evidence is missing. "
                        "Hospital registration and/or medical "
                        "necessity has not been established."
                    ),
                    "citation": "Policy Pages 2 and 5"
                })

            if (
                hospital_registered is None
                and minimum_criteria is None
            ):

                findings.append({
                    "rule": "HOSPITAL_EVIDENCE",
                    "status": "INSUFFICIENT_INFORMATION",
                    "effect": "REVIEW",
                    "reason": (
                        "The claim does not contain sufficient "
                        "evidence to establish that the facility "
                        "satisfies the required Hospital criteria."
                    ),
                    "citation": "Policy Pages 2 and 5"
                })

        # ==================================================
        # RULE 13
        # CATEGORY-SPECIFIC FINANCIAL LIMITS
        # Policy Page 7
        # ==================================================

        sum_insured = claim.get(
            "sum_insured_inr"
        )

        if sum_insured is not None:

            # ------------------------------------------------
            # ROOM RENT LIMIT
            # Normal room = 1% of Basic Sum Insured per day
            # ------------------------------------------------

            room_expense = expenses.get(
                "room",
                0
            )

            room_daily_limit = (
                sum_insured * 0.01
            )

            if admission_hours is not None:
                admission_days = admission_hours / 24
            else:
                admission_days = 1

            room_total_limit = (
                room_daily_limit * admission_days
            )

            if room_expense > room_total_limit:

                findings.append({
                    "rule": "ROOM_RENT_LIMIT",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Room rent expense of INR "
                        f"{room_expense:.2f} exceeds the "
                        f"calculated normal room limit of "
                        f"INR {room_total_limit:.2f} for "
                        f"{admission_days:.2f} day(s)."
                    ),
                    "citation": "Policy Page 7"
                })

            # ------------------------------------------------
            # MEDICAL PRACTITIONER / SURGEON FEES
            # Maximum 25% of Sum Insured
            # ------------------------------------------------

            doctor_fees = expenses.get(
                "doctor_fees",
                0
            )

            doctor_fee_limit = (
                sum_insured * 0.25
            )

            if doctor_fees > doctor_fee_limit:

                findings.append({
                    "rule": "MEDICAL_PRACTITIONER_FEE_LIMIT",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Doctor and surgeon-related "
                        f"expenses of INR {doctor_fees:.2f} "
                        f"exceed the policy category limit "
                        f"of INR {doctor_fee_limit:.2f}."
                    ),
                    "citation": "Policy Page 7"
                })

            # ------------------------------------------------
            # MEDICINES / DIAGNOSTICS
            # Maximum 40% of Sum Insured
            # ------------------------------------------------

            medicines_diagnostics = expenses.get(
                "medicines_diagnostics",
                0
            )

            medicines_limit = (
                sum_insured * 0.40
            )

            if medicines_diagnostics > medicines_limit:

                findings.append({
                    "rule": "MEDICINES_DIAGNOSTICS_LIMIT",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Medicines and diagnostic "
                        f"expenses of INR "
                        f"{medicines_diagnostics:.2f} "
                        f"exceed the policy category "
                        f"limit of INR "
                        f"{medicines_limit:.2f}."
                    ),
                    "citation": "Policy Page 7"
                })

            # ------------------------------------------------
            # DOMICILIARY TREATMENT SUB-LIMIT
            # Maximum 20% of Basic Sum Insured
            # ------------------------------------------------

            domiciliary_expense = expenses.get(
                "domiciliary",
                0
            )

            domiciliary_limit = (
                sum_insured * 0.20
            )

            if domiciliary_expense > domiciliary_limit:

                findings.append({
                    "rule": "DOMICILIARY_SUB_LIMIT",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Domiciliary expenses of INR "
                        f"{domiciliary_expense:.2f} exceed "
                        f"the policy aggregate sub-limit "
                        f"of INR {domiciliary_limit:.2f}."
                    ),
                    "citation": "Policy Page 7"
                })

            # ------------------------------------------------
            # ANY ONE ILLNESS PACKAGE LIMIT
            # Maximum 75% of Sum Insured
            # ------------------------------------------------

            package_charges = expenses.get(
                "package_charges",
                0
            )

            package_limit = (
                sum_insured * 0.75
            )

            if package_charges > package_limit:

                findings.append({
                    "rule": "ANY_ONE_ILLNESS_PACKAGE_LIMIT",
                    "status": "LIMIT_EXCEEDED",
                    "effect": "LIMIT",
                    "reason": (
                        f"Package charges of INR "
                        f"{package_charges:.2f} exceed "
                        "the policy limit of INR "
                        f"{package_limit:.2f}, subject "
                        "to the actual charges if lower."
                    ),
                    "citation": "Policy Page 7"
                })

        return findings