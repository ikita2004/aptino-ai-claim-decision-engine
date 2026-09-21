import os
import streamlit as st
import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = st.secrets.get(
    "API_URL",
    os.getenv(
        "API_URL",
        "http://127.0.0.1:8000/analyze"
    )
)

st.set_page_config(
    page_title="AI Claim Decision Engine",
    page_icon="🏥",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🏥 Policy-Aware Multi-Agent RAG Claim Decision Engine"
)

st.write(
    "Analyze a health insurance claim using policy-grounded "
    "hybrid RAG, specialized agents, deterministic policy "
    "rules, and citation validation."
)

st.caption(
    "The system uses the supplied policy document as the "
    "authoritative source and abstains when evidence is insufficient."
)

st.divider()


# ============================================================
# CLAIM INPUT FORM
# ============================================================

with st.form("claim_form"):

    st.subheader("📋 Claim Information")

    col1, col2 = st.columns(2)

    # ========================================================
    # BASIC CLAIM DETAILS
    # ========================================================

    with col1:

        claim_id = st.text_input(
            "Claim ID",
            value="UI-TEST-001"
        )

        policy_id = st.text_input(
            "Policy ID",
            value="POL-001"
        )

        policy_start_date = st.text_input(
            "Policy Start Date",
            value="2025-01-01"
        )

        claim_date = st.text_input(
            "Claim Date",
            value="2026-04-10"
        )

        sum_insured = st.number_input(
            "Sum Insured (INR)",
            min_value=0.0,
            value=500000.0,
            step=10000.0
        )

        coverage_months = st.number_input(
            "Continuous Coverage (Months)",
            min_value=0,
            value=14,
            step=1
        )

        prior_insurer_years = st.number_input(
            "Prior Insurer Continuous Years",
            min_value=0,
            value=0,
            step=1
        )

    # ========================================================
    # PATIENT / TREATMENT DETAILS
    # ========================================================

    with col2:

        age = st.number_input(
            "Patient Age",
            min_value=0,
            max_value=120,
            value=30,
            step=1
        )

        hospital_name = st.text_input(
            "Hospital Name",
            value="City Hospital"
        )

        network_provider = st.checkbox(
            "Network Hospital",
            value=True
        )

        treatment_type = st.selectbox(
            "Treatment Type",
            [
                "inpatient",
                "day_care",
                "domiciliary",
                "outpatient"
            ]
        )

        admission_hours = st.number_input(
            "Admission Hours",
            min_value=0,
            value=96,
            step=1
        )

        diagnosis = st.text_input(
            "Diagnosis",
            value="acute appendicitis"
        )

        procedure = st.text_input(
            "Procedure",
            value="appendectomy"
        )

        pre_existing = st.checkbox(
            "Pre-existing Condition",
            value=False
        )

        experimental = st.checkbox(
            "Experimental Treatment",
            value=False
        )

    st.divider()

    # ========================================================
    # EXPENSES
    # ========================================================

    st.subheader("💰 Claim Expenses")

    col3, col4, col5 = st.columns(3)

    with col3:

        room = st.number_input(
            "Room Expense (INR)",
            min_value=0.0,
            value=30000.0,
            step=1000.0
        )

        doctor_fees = st.number_input(
            "Doctor Fees (INR)",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )

    with col4:

        medicines = st.number_input(
            "Medicines & Diagnostics (INR)",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )

        pre_hospitalization = st.number_input(
            "Pre-hospitalization (INR)",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )

    with col5:

        post_hospitalization = st.number_input(
            "Post-hospitalization (INR)",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )

        ambulance = st.number_input(
            "Ambulance (INR)",
            min_value=0.0,
            value=0.0,
            step=500.0
        )

    st.divider()

    # ========================================================
    # DOCUMENTS
    # ========================================================

    st.subheader("📄 Documents & Task")

    documents_text = st.text_input(
        "Documents",
        value="claim_form, discharge_summary"
    )

    task = st.text_input(
        "Task",
        value=(
            "Analyze claim eligibility and calculate "
            "payable amount"
        )
    )

    st.divider()

    submitted = st.form_submit_button(
        "🔍 Analyze Claim",
        use_container_width=True
    )


# ============================================================
# ANALYZE CLAIM
# ============================================================

if submitted:

    # ========================================================
    # CREATE CLAIM JSON
    # ========================================================

    claim = {

        "claim_id": claim_id,

        "policy_id": policy_id,

        "policy_start_date": policy_start_date,

        "claim_date": claim_date,

        "sum_insured_inr": sum_insured,

        "continuous_coverage_months": coverage_months,

        "prior_insurer_continuous_years": prior_insurer_years,

        "patient": {
            "age": age
        },

        "hospital": {
            "name": hospital_name,
            "network_provider": network_provider
        },

        "treatment": {

            "type": treatment_type,

            "admission_hours": admission_hours,

            "diagnosis": diagnosis,

            "procedure": procedure,

            "pre_existing": pre_existing,

            "experimental": experimental
        },

        "expenses_inr": {

            "room": room,

            "doctor_fees": doctor_fees,

            "medicines_diagnostics": medicines,

            "pre_hospitalization": pre_hospitalization,

            "post_hospitalization": post_hospitalization,

            "ambulance": ambulance
        },

        "documents": [
            document.strip()
            for document in documents_text.split(",")
            if document.strip()
        ],

        "task": task
    }

    # ========================================================
    # CALL FASTAPI
    # ========================================================

    with st.spinner(
        "🤖 Running hybrid RAG and multi-agent claim analysis..."
    ):

        try:

            response = requests.post(
                API_URL,
                json=claim,
                timeout=300
            )

            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code == 200:

                result = response.json()

                st.success(
                    "Claim analysis completed successfully."
                )

                st.divider()

                # =============================================
                # FINAL DECISION
                # =============================================

                st.subheader("⚖️ Final Decision")

                decision = result.get(
                    "decision",
                    "UNKNOWN"
                )

                confidence = result.get(
                    "confidence",
                    "UNKNOWN"
                )

                decision_col, confidence_col = st.columns(2)

                with decision_col:

                    if decision == "APPROVE":

                        st.success(
                            f"✅ {decision}"
                        )

                    elif decision == "REJECT":

                        st.error(
                            f"❌ {decision}"
                        )

                    elif decision == "NEEDS_REVIEW":

                        st.warning(
                            f"⚠️ {decision}"
                        )

                        st.info(
                            "ABSTENTION: The system has not "
                            "made a final approval/rejection "
                            "decision because additional "
                            "evidence is required."
                        )

                    else:

                        st.warning(
                            f"⚠️ {decision}"
                        )

                with confidence_col:

                    st.metric(
                        "Decision Confidence",
                        confidence
                    )

                reason = result.get(
                    "reason",
                    "No reason available."
                )

                st.write(
                    f"**Reason:** {reason}"
                )

                st.divider()

                # =============================================
                # KEY FINDINGS
                # =============================================

                st.subheader("🔎 Key Findings")

                key_findings = result.get(
                    "key_findings",
                    []
                )

                if key_findings:

                    for finding in key_findings:

                        st.write(
                            f"• {finding}"
                        )

                else:

                    st.info(
                        "No additional findings returned."
                    )

                # =============================================
                # MISSING EVIDENCE
                # =============================================

                missing_evidence = result.get(
                    "missing_evidence",
                    []
                )

                if missing_evidence:

                    st.subheader(
                        "📌 Missing Evidence"
                    )

                    st.warning(
                        "Additional evidence is required "
                        "before a safe final decision."
                    )

                    for item in missing_evidence:

                        st.write(
                            f"• {item}"
                        )

                st.divider()
                
                # =============================================
                # FINANCIAL SUMMARY
                # =============================================

                st.subheader(
                    "💰 Financial Summary"
                )

                financial = result.get(
                    "financial_summary",
                    {}
                )

                col6, col7, col8 = st.columns(3)

                with col6:
                    st.metric(
                        "Total Claimed",
                        f"₹{financial.get('total_claimed_inr', 0):,.2f}"
                    )

                with col7:
                    st.metric(
                        "Deductions",
                        f"₹{financial.get('deductions_inr', 0):,.2f}"
                    )

                with col8:
                    st.metric(
                        "Payable Amount",
                        f"₹{financial.get('payable_amount_inr', 0):,.2f}"
                    )

                st.divider()

                # =============================================
                # APPLIED POLICY LIMITS
                # =============================================

                st.subheader(
                    "📊 Applicable Policy Limits"
                )

                applied_limits = result.get(
                    "applicable_limits",
                    []
                )

                if applied_limits:

                    st.dataframe(
                        applied_limits,
                        use_container_width=True
                    )

                else:

                    st.info(
                        "No category-specific financial "
                        "limits were applied."
                    )

                st.divider()

                # =============================================
                # POLICY CITATIONS
                # =============================================

                st.subheader(
                    "📚 Policy-Grounded Evidence"
                )

                citations = result.get(
                    "citations",
                    []
                )

                if citations:

                    for index, citation in enumerate(
                        citations,
                        start=1
                    ):

                        page = citation.get(
                            "page",
                            "N/A"
                        )

                        section = citation.get(
                            "section",
                            "Policy"
                        )

                        chunk_id = citation.get(
                            "chunk_id",
                            "N/A"
                        )

                        evidence = citation.get(
                            "evidence",
                            ""
                        )

                        with st.expander(
                            f"Citation {index} | "
                            f"Page {page} | "
                            f"{section} | "
                            f"{chunk_id}"
                        ):

                            st.write(
                                evidence
                            )

                            st.caption(
                                f"Source: Policy PDF | "
                                f"Page: {page} | "
                                f"Section: {section} | "
                                f"Chunk: {chunk_id}"
                            )

                else:

                    st.info(
                        "No policy citations returned."
                    )

                st.divider()

                # =============================================
                # CITATION VALIDATION
                # =============================================

                st.subheader(
                    "🔎 Citation Validation"
                )

                citation_validation = result.get(
                    "citation_validation",
                    {}
                )

                validation_status = (
                    citation_validation.get(
                        "status",
                        "UNKNOWN"
                    )
                )

                if validation_status == "VALID":

                    st.success(
                        "✅ All returned policy citations "
                        "passed validation."
                    )

                elif validation_status == "INVALID":

                    st.error(
                        "❌ Citation validation failed."
                    )

                else:

                    st.warning(
                        f"Validation status: "
                        f"{validation_status}"
                    )

                with st.expander(
                    "View Validation Details"
                ):

                    st.json(
                        citation_validation
                    )

                st.divider()

                # =============================================
                # POLICY RULE FINDINGS
                # =============================================

                st.subheader(
                    "📋 Deterministic Policy Rules"
                )

                rule_findings = result.get(
                    "rule_findings",
                    []
                )

                if rule_findings:

                    for finding in rule_findings:

                        rule_name = finding.get(
                            "rule",
                            finding.get(
                                "category",
                                "Policy Rule"
                            )
                        )

                        status = finding.get(
                            "status",
                            ""
                        )

                        effect = finding.get(
                            "effect",
                            ""
                        )

                        reason = finding.get(
                            "reason",
                            ""
                        )

                        st.write(
                            f"**{rule_name}**"
                        )

                        if status:

                            st.write(
                                f"Status: {status}"
                            )

                        if effect:

                            st.write(
                                f"Effect: {effect}"
                            )

                        if reason:

                            st.write(reason)

                        if finding.get(
                            "missing_evidence"
                        ):

                            st.write(
                                "**Missing evidence:**"
                            )

                            for item in finding[
                                "missing_evidence"
                            ]:

                                st.write(
                                    f"• {item}"
                                )

                        st.divider()

                else:

                    st.info(
                        "No additional deterministic "
                        "policy-rule findings."
                    )

                # =============================================
                # RAG RETRIEVAL
                # =============================================

                st.subheader(
                    "🔍 RAG Retrieval"
                )

                retrieved_documents = result.get(
                    "retrieved_documents",
                    0
                )

                st.metric(
                    "Retrieved Policy Chunks",
                    retrieved_documents
                )

                st.caption(
                    "Policy evidence is retrieved using "
                    "hybrid sparse + dense retrieval and "
                    "reranked before agent analysis."
                )

                st.divider()

                # =============================================
                # EXECUTION TRACE
                # =============================================

                st.subheader(
                    "🧠 Multi-Agent Execution Trace"
                )

                trace = result.get(
                    "execution_trace",
                    []
                )

                if trace:

                    for index, step in enumerate(
                        trace,
                        start=1
                    ):

                        agent = step.get(
                            "agent",
                            "Unknown Agent"
                        )

                        action = step.get(
                            "action",
                            "No action recorded"
                        )

                        status = step.get(
                            "status"
                        )

                        retrieval_count = step.get(
                            "retrieval_count"
                        )

                        rule_count = step.get(
                            "rule_count"
                        )

                        decision_value = step.get(
                            "decision"
                        )

                        with st.expander(
                            f"{index}. {agent}"
                        ):

                            st.write(
                                f"**Action:** {action}"
                            )

                            if status:

                                st.write(
                                    f"**Status:** {status}"
                                )

                            if retrieval_count is not None:

                                st.write(
                                    f"**Retrieved:** "
                                    f"{retrieval_count}"
                                )

                            if rule_count is not None:

                                st.write(
                                    f"**Rules evaluated:** "
                                    f"{rule_count}"
                                )

                            if decision_value:

                                st.write(
                                    f"**Decision:** "
                                    f"{decision_value}"
                                )

                else:

                    st.info(
                        "No execution trace returned."
                    )

                # =============================================
                # RAW API RESPONSE
                # =============================================

                with st.expander(
                    "🧾 View Complete API Response"
                ):

                    st.json(result)

            # =================================================
            # API ERROR
            # =================================================

            else:

                st.error(
                    f"FastAPI returned HTTP "
                    f"{response.status_code}"
                )

                try:

                    st.json(
                        response.json()
                    )

                except Exception:

                    st.write(
                        response.text
                    )

        # =====================================================
        # CONNECTION ERROR
        # =====================================================

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Could not connect to FastAPI."
            )

            st.write(
                "Make sure FastAPI is running in another terminal:"
            )

            st.code(
                "uvicorn main:app --reload"
            )

        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout:

            st.error(
                "⏱️ The request took too long."
            )

            st.write(
                "The RAG pipeline may still be processing. "
                "Please try again."
            )

        # =====================================================
        # OTHER ERROR
        # =====================================================

        except Exception as error:

            st.error(
                f"Unexpected error: {error}"
            )
