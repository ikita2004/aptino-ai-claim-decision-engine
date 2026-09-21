# Policy-Aware Multi-Agent RAG Claim Decision Engine

## Overview

This project implements a **Policy-Aware Multi-Agent RAG Claim Decision Engine** for automated health insurance claim analysis.

The system analyzes a synthetic claim against the provided health insurance policy using:

- Retrieval-Augmented Generation (RAG)
- Hybrid sparse + dense retrieval
- BM25 keyword retrieval
- Sentence Transformer embeddings
- Cross-encoder reranking
- Specialized multi-agent analysis
- Deterministic policy rules
- Financial limit calculations
- Evidence sufficiency checks
- Citation validation
- FastAPI REST API
- Streamlit web interface

The supplied insurance policy PDF is treated as the **authoritative source for policy evidence**.

The system produces one of three internal decision statuses:

- `APPROVE`
- `REJECT`
- `NEEDS_REVIEW`

`NEEDS_REVIEW` acts as an abstention state when the available claim evidence is insufficient to make a safe final decision.

---

## Problem Statement

Health insurance claim decisions can depend on multiple policy clauses, including:

- Waiting periods
- Pre-existing disease provisions
- Day-care treatment definitions
- Hospitalization requirements
- Exclusions
- Domiciliary treatment conditions
- Room-rent limits
- Professional-fee limits
- Medicines and diagnostics limits
- Pre- and post-hospitalization provisions

A simple keyword search is insufficient for cases where relevant information is distributed across multiple sections of a policy.

This system therefore combines retrieval, specialized agents, deterministic rules, and evidence validation to produce an explainable claim analysis.

---

# System Architecture

```text
                         ┌─────────────────────────┐
                         │      Streamlit UI        │
                         │       Port 8501          │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI API        │
                         │       Port 8000          │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      Claim Analyzer      │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
       │ Hybrid RAG   │       │ Multi-Agent  │       │ Policy Rules │
       │ Retrieval    │       │ Analysis     │       │ Engine       │
       └──────┬───────┘       └──────┬───────┘       └──────┬───────┘
              │                      │                      │
              ▼                      ▼                      ▼
        ┌───────────┐         Coverage Agent          Waiting Periods
        │   BM25    │         Exclusion Agent         Exclusions
        ├───────────┤         Evidence Agent          Financial Limits
        │   Dense   │
        └─────┬─────┘
              │
              ▼
       Cross-Encoder
        Reranking
              │
              └───────────────────────┐
                                      ▼
                         ┌─────────────────────────┐
                         │   Citation Validator    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Decision Engine      │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         APPROVE / REJECT /
                         NEEDS_REVIEW
```

---

# Project Structure

```text
Aptino_Submission/
│
├── app.py
├── main.py
├── README.md
├── requirements.txt
│
├── data/
│   ├── evaluation_results.json
│   ├── policy_chunks.json
│   │
│   ├── policy/
│   │   └── USGIC-CSCIndividualHealthInsurance_2017-2018.pdf
│   │
│   ├── cases/
│   │   ├── public_test_cases.json
│   │   └── additional_test_cases.json
│   │
│   └── schema/
│       └── claim_case_schema.md
│
├── src/
│   ├── agents/
│   │   ├── coverage_agent.py
│   │   ├── exclusion_agent.py
│   │   └── evidence_agent.py
│   │
│   ├── policy_ingestion.py
│   ├── retrieval.py
│   ├── dense_retrieval.py
│   ├── hybrid_retrieval.py
│   ├── reranker.py
│   ├── state.py
│   ├── decision_engine.py
│   ├── claim_analyzer.py
│   ├── citation_validator.py
│   └── policy_rules.py
│
└── tests/
    ├── run_public_cases.py
    ├── run_evaluation.py
    └── test_policy_rules.py
```

The local `venv/` directory is intentionally excluded from the submission.

Python cache files such as `__pycache__/` and `.pyc` files are also excluded.

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

## RAG / NLP

- Sentence Transformers
- `all-MiniLM-L6-v2`
- BM25
- `rank-bm25`
- Cross-Encoder reranking
- `cross-encoder/ms-marco-MiniLM-L-6-v2`

## Document Processing

- PyPDF

## Frontend

- Streamlit

## Testing / Development

- Python test scripts
- VS Code
- Git / GitHub

---

# Policy Ingestion

The supplied policy PDF is processed before claim analysis.

```text
Policy PDF
    ↓
PDF Text Extraction
    ↓
Section Detection
    ↓
Policy Chunking
    ↓
Metadata Attachment
    ↓
policy_chunks.json
```

The processed policy contains **49 searchable chunks across 17 pages**.

Each chunk preserves:

- `chunk_id`
- `page`
- `section`
- `text`

This metadata is used to maintain traceability between retrieved evidence and the source policy.

---

# Retrieval Pipeline

## Hybrid Retrieval

The system uses two complementary retrieval methods:

### BM25 Retrieval

BM25 provides keyword-based retrieval and is useful when claims contain policy terminology such as:

- pre-existing disease
- waiting period
- day care
- cosmetic treatment
- domiciliary treatment
- hospitalization

### Dense Retrieval

Sentence Transformers generate semantic embeddings to retrieve conceptually related policy passages even when the wording differs from the claim.

```text
                 Claim Query
                     │
             ┌───────┴────────┐
             │                │
             ▼                ▼
           BM25             Dense
        Retrieval          Retrieval
             │                │
             └───────┬────────┘
                     ▼
             Combined Candidates
                     │
                     ▼
              Cross-Encoder
                Reranking
                     │
                     ▼
              Top Policy Chunks
```

The combination reduces dependence on either exact keyword matching or semantic similarity alone.

---

# Cross-Encoder Reranking

Retrieved candidates are reranked using:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

The reranker evaluates the relationship between the claim query and retrieved policy text.

The highest-ranked evidence is then passed to the downstream agents.

This creates the following retrieval flow:

```text
BM25 + Dense Retrieval
          ↓
Candidate Pool
          ↓
Cross-Encoder Reranker
          ↓
Relevant Policy Evidence
```

---

# Multi-Agent Architecture

The system contains three specialized agents with separate responsibilities.

## 1. Coverage Agent

The Coverage Agent evaluates whether the treatment appears to fall within the covered scope of the policy.

It considers information such as:

- Treatment type
- Hospitalization
- Day-care treatment
- Domiciliary treatment
- Policy coverage conditions

The agent focuses on **coverage interpretation** rather than financial calculation.

---

## 2. Exclusion Agent

The Exclusion Agent checks whether the claim matches an explicit policy exclusion.

Examples include:

- Cosmetic or aesthetic treatment
- Experimental or unproven treatment
- Outpatient treatment
- Other policy-specific exclusions

The agent focuses on **exclusion identification**.

---

## 3. Evidence Agent

The Evidence Agent determines whether sufficient information is available to support a safe final decision.

It checks both:

### Policy evidence

Whether relevant policy chunks were successfully retrieved and contain valid citation metadata.

### Claim-level evidence

Whether required claim information is available, such as:

- Hospital/provider status
- Medical necessity
- Supporting clinical documents

If important evidence is missing, the system can abstain with:

```text
NEEDS_REVIEW
```

instead of assuming unsupported facts.

---

# Shared Structured State

The agents operate through a structured claim state.

The state contains claim information and intermediate results including:

```text
ClaimState
│
├── claim information
├── patient information
├── hospital information
├── treatment information
├── expenses
├── retrieved chunks
├── coverage result
├── exclusion result
├── evidence result
├── citation validation
├── rule findings
├── decision result
└── final decision
```

This keeps the agent responsibilities separated while allowing their findings to be combined by the analysis pipeline.

---

# Deterministic Policy Rule Engine

Critical policy conditions are implemented using explicit deterministic rules rather than relying entirely on an LLM.

This is particularly important for financial calculations and policy thresholds.

The rule engine evaluates conditions including:

## Waiting Periods

- Initial waiting period
- Pre-existing disease waiting period
- Listed disease waiting periods
- Prior-insurer continuity provisions

## Day-Care Treatment

The engine evaluates:

- Admission duration
- Listed day-care procedures
- Day-care definition
- Hospitalization requirements
- Conditions under which hospitalization duration requirements may be waived

## Domiciliary Treatment

The engine evaluates applicable policy conditions for home-based treatment.

## Financial Limits

The engine supports category-specific limits including:

- Room rent
- Medical practitioner fees
- Medicines and diagnostics
- Domiciliary treatment
- Package charges

## Hospitalization-Related Expenses

The engine also considers:

- Pre-hospitalization expenses
- Post-hospitalization expenses
- Ambulance expenses

---

# Financial Calculation

The financial calculation follows:

```text
Total Claimed
      -
Applicable Deductions
      =
Payable Amount
```

Category-specific policy limits are applied where relevant.

For example, room rent is evaluated against the policy's room-rent limit based on the Basic Sum Insured and hospitalization duration.

The system therefore does not automatically assume that the entire submitted hospital bill is payable.

---

# Decision Engine

The Decision Engine combines:

```text
Coverage Findings
       +
Exclusion Findings
       +
Evidence Findings
       +
Deterministic Rule Findings
       +
Financial Calculations
       ↓
Final Decision
```

The current implementation uses:

### `APPROVE`

The evaluated policy conditions are satisfied and no unresolved blocking issue is identified.

### `REJECT`

A policy exclusion or deterministic rejection condition applies.

### `NEEDS_REVIEW`

The system abstains because additional evidence or verification is required for a safe final decision.

---

# Abstention / Evidence-Aware Decision Making

A key reliability feature is the ability to abstain.

The system does not treat missing evidence as proof that a claim condition is satisfied.

For example, if an inpatient claim does not establish required claim-level evidence such as hospital/provider status or medical necessity, the Evidence Agent can produce:

```text
INSUFFICIENT_EVIDENCE
```

The Claim Analyzer converts this into a review finding:

```text
effect = REVIEW
```

The Decision Engine then returns:

```text
NEEDS_REVIEW
```

The API exposes the missing evidence so that a human reviewer can determine what additional documentation is required.

---

# Citation Validation

Every material policy-grounded analysis is associated with retrieved policy evidence.

Each citation contains metadata such as:

```json
{
  "chunk_id": "chunk_...",
  "page": 7,
  "section": "Policy Section",
  "citation": "Policy Page 7",
  "evidence": "Relevant policy text..."
}
```

The citation validator checks whether the returned citations correspond to valid retrieved policy evidence.

Example:

```json
{
  "status": "VALID",
  "valid_citations": [],
  "invalid_citations": [],
  "reason": "All citations passed validation."
}
```

Final evaluation produced:

```text
85 / 85 citations validated
100% citation validation rate
```

---

# API

The application exposes a FastAPI backend.

## Health Check

```http
GET /health
```

Example:

```json
{
  "status": "healthy",
  "analyzer": "ready"
}
```

## Claim Analysis

```http
POST /analyze
```

The API accepts a JSON claim object.

Example:

```json
{
  "claim_id": "API-TEST-001",
  "policy_id": "POL-001",
  "policy_start_date": "2025-01-01",
  "claim_date": "2026-04-10",
  "sum_insured_inr": 500000,
  "continuous_coverage_months": 14,
  "prior_insurer_continuous_years": 0,
  "patient": {
    "age": 30
  },
  "hospital": {
    "name": "City Hospital",
    "network_provider": true
  },
  "treatment": {
    "type": "inpatient",
    "admission_hours": 96,
    "diagnosis": "acute appendicitis",
    "procedure": "appendectomy",
    "pre_existing": false,
    "experimental": false
  },
  "expenses_inr": {
    "room": 30000,
    "doctor_fees": 0,
    "medicines_diagnostics": 0,
    "pre_hospitalization": 0,
    "post_hospitalization": 0,
    "ambulance": 0
  },
  "documents": ["claim_form", "discharge_summary"],
  "task": "Analyze claim eligibility and calculate payable amount"
}
```

The response contains:

- `case_id`
- `claim_id`
- `decision`
- `confidence`
- `reason`
- `key_findings`
- `financial_summary`
- `applicable_limits`
- `missing_evidence`
- `citations`
- `citation_validation`
- `retrieved_documents`
- `rule_findings`
- `execution_trace`

---

# Execution Trace

The API exposes a concise execution trace instead of hidden chain-of-thought.

Example:

```json
[
  {
    "agent": "hybrid_retriever",
    "action": "Retrieved relevant policy evidence",
    "retrieval_count": 5
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
    "action": "Validated policy and claim-level evidence",
    "status": "SUFFICIENT_EVIDENCE"
  },
  {
    "agent": "citation_validator",
    "action": "Validated policy citations",
    "status": "VALID"
  },
  {
    "agent": "policy_rule_engine",
    "action": "Applied deterministic policy rules",
    "rule_count": 0
  },
  {
    "agent": "decision_engine",
    "action": "Generated final claim decision",
    "decision": "APPROVE"
  }
]
```

The trace is designed to provide operational transparency without exposing private model reasoning.

---

# Streamlit Frontend

The Streamlit application provides a UI for entering:

- Claim information
- Policy information
- Patient information
- Hospital information
- Treatment information
- Coverage information
- Claim expenses
- Supporting documents

The UI displays:

- Final decision
- Decision confidence
- Key findings
- Abstention warning
- Missing evidence
- Financial summary
- Applicable policy limits
- Policy citations
- Citation validation
- Deterministic rule findings
- RAG retrieval count
- Multi-agent execution trace
- Complete API response

---

# Evaluation

The evaluation suite contains:

- 12 supplied public cases
- 5 additional candidate-created cases
- 17 total cases

The evaluation measures:

1. Case-level success
2. Citation validation
3. Decision distribution
4. Additional-case coverage
5. Abstention behavior

---

# Public Test Results

All 12 supplied public cases were evaluated.

| Case    | Expected Result |
| ------- | --------------- |
| PUB-001 | APPROVE         |
| PUB-002 | NEEDS_REVIEW    |
| PUB-003 | NEEDS_REVIEW    |
| PUB-004 | NEEDS_REVIEW    |
| PUB-005 | NEEDS_REVIEW    |
| PUB-006 | NEEDS_REVIEW    |
| PUB-007 | APPROVE         |
| PUB-008 | REJECT          |
| PUB-009 | APPROVE         |
| PUB-010 | NEEDS_REVIEW    |
| PUB-011 | NEEDS_REVIEW    |
| PUB-012 | REJECT          |

### Public Evaluation Summary

```text
Cases evaluated       : 12
Successful cases      : 12
Failed cases          : 0
Case success rate     : 100.00%

Citations validated   : 60 / 60
Citation validation   : 100.00%
```

Decision distribution:

```text
APPROVE        : 3
REJECT         : 2
NEEDS_REVIEW   : 7
```

---

# Additional Test Cases

Five additional cases were created to test boundary conditions and evidence-aware behavior.

| Case    | Expected Result | Purpose                                 |
| ------- | --------------- | --------------------------------------- |
| ADD-001 | APPROVE         | Tests exact 72-hour inpatient boundary  |
| ADD-002 | NEEDS_REVIEW    | Tests insufficient evidence             |
| ADD-003 | APPROVE         | Tests applicable policy conditions      |
| ADD-004 | NEEDS_REVIEW    | Tests missing hospital/medical evidence |
| ADD-005 | REJECT          | Tests explicit exclusion                |

### Additional Evaluation Summary

```text
Cases evaluated       : 5
Successful cases      : 5
Failed cases          : 0
Case success rate     : 100.00%

Citations validated   : 25 / 25
Citation validation   : 100.00%
```

Decision distribution:

```text
APPROVE        : 2
REJECT         : 1
NEEDS_REVIEW   : 2
```

---

# Overall Evaluation Results

Combining the public and additional cases:

```text
Total cases          : 17
Successful cases     : 17
Failed cases         : 0
Case success rate    : 100.00%

Citations validated  : 85 / 85
Citation validation  : 100.00%
```

Decision distribution:

```text
APPROVE        : 5
REJECT         : 3
NEEDS_REVIEW   : 9
```

The evaluation results are also stored in:

```text
data/evaluation_results.json
```

---

# Retrieval Quality / Citation Hit Rate

The evaluation includes citation validation as a grounding metric.

For the evaluated cases:

```text
Total citations returned       : 85
Valid citations                : 85
Invalid citations              : 0

Citation validation rate       : 100.00%
```

This measures whether the citations returned by the pipeline correspond to valid retrieved policy evidence.

It should not be interpreted as a complete measure of semantic retrieval quality; future evaluation can add metrics such as evidence recall@k using manually annotated relevant policy chunks.

---

# Representative Financial Results

## PUB-001

```text
Total Claimed  : ₹163,200
Deductions     : ₹10,000
Payable Amount : ₹153,200
```

The deduction is caused by the applicable room-rent limit.

## PUB-007

```text
Total Claimed  : ₹906,500
Deductions     : ₹190,000
Payable Amount : ₹716,500
```

The deductions include category-specific limits for:

- Room
- Doctor fees
- Medicines and diagnostics

---

# Example End-to-End Flow

Example claim:

```text
Diagnosis:
Acute appendicitis

Procedure:
Appendectomy

Treatment:
Inpatient

Hospitalization:
96 hours

Sum Insured:
₹500,000

Total Claim:
₹163,200
```

Processing:

```text
Claim Input
    ↓
Claim Validation
    ↓
Hybrid Retrieval
    ↓
BM25 + Dense Retrieval
    ↓
Cross-Encoder Reranking
    ↓
Coverage Agent
    ↓
Exclusion Agent
    ↓
Evidence Agent
    ↓
Deterministic Policy Rules
    ↓
Financial Limit Calculation
    ↓
Citation Validation
    ↓
Decision Engine
    ↓
APPROVE
```

Financial result:

```text
Total Claimed  : ₹163,200
Deduction      : ₹10,000
Payable        : ₹153,200
```

---

# Development Failure Cases and Improvements

The development process included several failure cases that were used to improve the implementation.

## Failure Case 1 — Exact 72-Hour Boundary

### Problem

An initial policy rule treated:

```text
admission_hours <= 72
```

as the exclusion/review boundary.

This incorrectly affected a case with exactly 72 hours of hospitalization.

### Root Cause

The boundary condition did not match the intended policy interpretation used by the evaluation case.

### Improvement

The rule was changed to:

```text
admission_hours < 72
```

This distinguishes exactly 72 hours from durations below 72 hours.

The additional test case `ADD-001` subsequently passed.

---

## Failure Case 2 — Insufficient Claim-Level Evidence

### Problem

`ADD-004` was initially returned as:

```text
APPROVE
```

when the expected result was:

```text
NEEDS_REVIEW
```

### Root Cause

The original Evidence Agent validated policy citation metadata but did not sufficiently inspect claim-level evidence.

### Improvement

The Evidence Agent was extended to check:

- Hospital/provider status
- Medical necessity information
- Clinical supporting documents

Missing evidence is now converted into an explicit review finding.

`ADD-004` subsequently returned:

```text
NEEDS_REVIEW
```

---

## Failure Case 3 — Citation Evaluation Mismatch

### Problem

The initial evaluation reported:

```text
0 / 85
```

valid citations even though citations were being returned and the citation validator was reporting them as valid.

### Root Cause

The evaluation script expected a `validation_status` field inside every individual citation, while the implementation stored validation results in the separate `citation_validation` object.

### Improvement

The evaluator was updated to use:

```text
result.citation_validation
```

and count validated citations from the validator result.

The final evaluation became:

```text
85 / 85
100% citation validation
```

---

# Design Decisions and Trade-offs

## Why Hybrid Retrieval?

BM25 is strong for exact policy terminology, while dense retrieval is useful for semantic similarity.

Using both provides better coverage than relying on only one retrieval method.

### Trade-off

The implementation is more complex than a simple vector search pipeline and requires maintaining both retrieval mechanisms.

---

## Why Cross-Encoder Reranking?

Initial retrieval can return several relevant-looking chunks.

Cross-encoder reranking provides a second-stage relevance assessment before evidence reaches the agents.

### Trade-off

Reranking increases inference time compared with direct retrieval.

---

## Why Deterministic Rules?

Financial calculations and explicit policy thresholds should be reproducible.

Deterministic rules make calculations such as:

```text
Room limit
Doctor fee limit
Medicines limit
Waiting periods
```

consistent across repeated runs.

### Trade-off

Rules require manual implementation and may need updates when the policy changes.

---

## Why Specialized Agents?

Separating:

```text
Coverage
Exclusions
Evidence
```

makes the architecture modular and easier to test.

### Trade-off

Multiple agents increase pipeline complexity compared with a single analysis function.

---

## Why Abstention?

A claim system should not infer missing evidence.

Returning `NEEDS_REVIEW` provides a safer path when the available information is insufficient.

### Trade-off

Some cases cannot receive an automatic final decision and require human review.

---

# Known Limitations

The current implementation is a prototype designed for the supplied policy and synthetic evaluation cases.

Known limitations include:

- Policy rules are manually encoded for the supplied policy.
- The current implementation uses local JSON storage rather than a production vector database.
- Claim documents are represented primarily through structured claim fields and document names.
- OCR and scanned medical-document extraction are not implemented.
- There is no production authentication or authorization layer.
- API logging and monitoring are limited.
- The current confidence field is a categorical application-level indicator rather than a calibrated statistical probability.
- The retrieval evaluation currently emphasizes citation validation rather than a manually annotated retrieval recall benchmark.
- Policy version management is not automated.
- Production deployment requires environment-specific API configuration.

---

# Security and Reliability Considerations

The system is designed to avoid making unsupported policy claims.

Important reliability principles include:

- Policy evidence is retrieved from the supplied source.
- Citations preserve page and chunk metadata.
- Deterministic rules handle important policy thresholds.
- Financial calculations are explicit.
- Missing claim evidence can trigger abstention.
- API errors are returned as HTTP errors rather than silently ignored.
- Secrets should be supplied through environment variables in deployment environments.

The system should be treated as a decision-support prototype rather than an autonomous production insurance adjudication system.

---

# Installation

## 1. Create a Virtual Environment

```powershell
python -m venv venv
```

## 2. Activate the Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

## 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

# Running the Application

## Terminal 1 — FastAPI

```powershell
uvicorn main:app --reload
```

The API will run on:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

---

## Terminal 2 — Streamlit

```powershell
streamlit run app.py
```

The frontend will normally run on:

```text
http://localhost:8501
```

The Streamlit frontend sends claim requests to the FastAPI backend.

---

# Running Evaluation

Run the complete evaluation from the project root:

```powershell
python tests\run_evaluation.py
```

Run only the public cases:

```powershell
python tests\run_public_cases.py
```

The evaluation output is stored in:

```text
data/evaluation_results.json
```

---

# Reproducibility

The repository contains:

- Source code
- Policy PDF
- Processed policy chunks
- Public test cases
- Additional test cases
- Evaluation script
- Evaluation results
- Dependency list

A new environment can therefore be created using:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

followed by the evaluation or application startup commands.

---

# Deployment

The application is structured for separate frontend and backend deployment.

```text
Public Streamlit Frontend
          ↓
Public FastAPI Backend
          ↓
Claim Analyzer
          ↓
RAG + Agents + Rules
```

For deployment, the frontend API endpoint should be supplied through an environment variable rather than relying on:

```text
127.0.0.1
```

The production deployment URLs should be added here after deployment:

```text
Frontend URL:
[To be added]

API URL:
[To be added]

API Health:
[To be added]
```

---

# Future Improvements

Potential future improvements include:

- Persistent vector database
- Production document storage
- OCR for scanned medical documents
- Automated claim-document extraction
- Human reviewer workflow for `NEEDS_REVIEW`
- Authentication and authorization
- API monitoring and observability
- Automated policy version management
- More extensive unit and integration tests
- Docker deployment
- Cloud deployment
- Retrieval recall@k benchmark with manually annotated evidence
- Calibrated confidence scoring
- Policy-specific rule configuration rather than hard-coded rules

---

# Conclusion

This project demonstrates a complete policy-aware insurance claim analysis pipeline combining:

**Hybrid RAG + BM25 + Dense Retrieval + Cross-Encoder Reranking + Multi-Agent Analysis + Deterministic Policy Rules + Financial Calculations + Evidence Checking + Citation Validation + FastAPI + Streamlit.**

The final evaluation achieved:

```text
Public Cases:
12 / 12 successful

Additional Cases:
5 / 5 successful

Overall:
17 / 17 successful
100.00% case success rate

Citation Validation:
85 / 85
100.00%
```

The system also demonstrates evidence-aware abstention through `NEEDS_REVIEW`, allowing unresolved claims to be routed for additional verification rather than making unsupported decisions.
