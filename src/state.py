from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    age: Optional[int] = None


class HospitalInfo(BaseModel):
    name: Optional[str] = None
    network_provider: Optional[bool] = None


class TreatmentInfo(BaseModel):
    type: Optional[str] = None
    admission_hours: Optional[int] = None
    diagnosis: Optional[str] = None
    procedure: Optional[str] = None
    pre_existing: Optional[bool] = None
    experimental: Optional[bool] = None


class ExpensesInfo(BaseModel):
    room: float = 0
    doctor_fees: float = 0
    medicines_diagnostics: float = 0
    pre_hospitalization: float = 0
    post_hospitalization: float = 0
    ambulance: float = 0


class ClaimState(BaseModel):

    # ---------------------------------------------
    # Basic claim information
    # ---------------------------------------------

    claim_id: str

    policy_id: Optional[str] = None

    policy_start_date: Optional[str] = None

    claim_date: Optional[str] = None

    sum_insured_inr: Optional[float] = None

    continuous_coverage_months: Optional[int] = None

    prior_insurer_continuous_years: Optional[int] = None

    # ---------------------------------------------
    # Claim details
    # ---------------------------------------------

    patient: PatientInfo = Field(
        default_factory=PatientInfo
    )

    hospital: HospitalInfo = Field(
        default_factory=HospitalInfo
    )

    treatment: TreatmentInfo = Field(
        default_factory=TreatmentInfo
    )

    expenses_inr: ExpensesInfo = Field(
        default_factory=ExpensesInfo
    )

    documents: List[str] = Field(
        default_factory=list
    )

    task: Optional[str] = None

    # ---------------------------------------------
    # RAG information
    # ---------------------------------------------

    retrieved_chunks: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    # ---------------------------------------------
    # Agent results
    # ---------------------------------------------

    coverage_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    exclusion_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    evidence_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    citation_validation: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ---------------------------------------------
    # Final decision
    # ---------------------------------------------

    final_decision: Optional[str] = None

    final_reason: Optional[str] = None

    # Complete decision and financial result
    decision_result: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ---------------------------------------------
    # Citations
    # ---------------------------------------------

    citations: List[Dict[str, Any]] = Field(
        default_factory=list
    )