from src.policy_rules import PolicyRuleEngine


engine = PolicyRuleEngine()


claim = {
    "claim_id": "PUB-002",

    "continuous_coverage_months": 0,

    "prior_insurer_continuous_years": 0,

    "treatment": {
        "type": "inpatient",
        "admission_hours": 96,
        "diagnosis": "Viral Fever",
        "procedure": "Medical Treatment",
        "pre_existing": False,
        "experimental": False
    },

    "hospital": {
        "network_provider": True
    }
}


findings = engine.evaluate(claim)


print("\nPUB-002 RESULTS")
print("=" * 50)

for finding in findings:
    print(f"\nRule       : {finding['rule']}")
    print(f"Status     : {finding['status']}")
    print(f"Effect     : {finding['effect']}")
    print(f"Reason     : {finding['reason']}")
    print(f"Citation   : {finding['citation']}")

    # ============================================================
# PUB-003 - PRE-EXISTING DISEASE
# ============================================================

claim_003 = {
    "claim_id": "PUB-003",
    "continuous_coverage_months": 27,
    "prior_insurer_continuous_years": 0,
    "treatment": {
        "type": "inpatient",
        "admission_hours": 96,
        "diagnosis": "Pre-existing thyroid disorder with complications",
        "procedure": "Medical Treatment",
        "pre_existing": True,
        "experimental": False
    },
    "hospital": {
        "network_provider": True
    }
}

findings_003 = engine.evaluate(claim_003)

print("\n\nPUB-003 RESULTS")
print("=" * 50)

for finding in findings_003:
    print(f"\nRule       : {finding['rule']}")
    print(f"Status     : {finding['status']}")
    print(f"Effect     : {finding['effect']}")
    print(f"Reason     : {finding['reason']}")
    print(f"Citation   : {finding['citation']}")

    # ============================================================
# PUB-004 - DOMICILIARY TREATMENT
# ============================================================

claim_004 = {
    "claim_id": "PUB-004",
    "continuous_coverage_months": 28,
    "treatment": {
        "type": "domiciliary",
        "admission_hours": None,
        "diagnosis": "Medical condition",
        "procedure": "Home treatment",
        "pre_existing": False,
        "experimental": False,
        "hospital_room_unavailable": True,
        "patient_cannot_be_moved": False
    },
    "hospital": {
        "network_provider": True
    }
}

findings_004 = engine.evaluate(claim_004)

print("\n\nPUB-004 RESULTS")
print("=" * 50)

for finding in findings_004:
    print(f"\nRule       : {finding['rule']}")
    print(f"Status     : {finding['status']}")
    print(f"Effect     : {finding['effect']}")
    print(f"Reason     : {finding['reason']}")
    print(f"Citation   : {finding['citation']}")

    # ============================================================
# PUB-005 - DAY CARE TREATMENT
# ============================================================

claim_005 = {
    "claim_id": "PUB-005",
    "continuous_coverage_months": 12,
    "treatment": {
        "type": "day_care",
        "admission_hours": 8,
        "diagnosis": "Cataract",
        "procedure": "Eye Surgery",
        "pre_existing": False,
        "experimental": False
    },
    "hospital": {
        "network_provider": True
    }
}

findings_005 = engine.evaluate(claim_005)

print("\n\nPUB-005 RESULTS")
print("=" * 50)

for finding in findings_005:
    print(f"\nRule       : {finding['rule']}")
    print(f"Status     : {finding['status']}")
    print(f"Effect     : {finding['effect']}")
    print(f"Reason     : {finding['reason']}")
    print(f"Citation   : {finding['citation']}")

    # ============================================================
# PUB-006 - INSUFFICIENT EVIDENCE
# ============================================================

claim_006 = {
    "claim_id": "PUB-006",
    "continuous_coverage_months": 30,
    "treatment": {
        "type": "inpatient",
        "admission_hours": 96,
        "diagnosis": "Acute infection",
        "procedure": "Medical Treatment",
        "pre_existing": False,
        "experimental": False
    },
    "hospital": {
        "network_provider": True
    },
    "documents": [
        "claim_form",
        "discharge_summary"
    ],
    "evidence_context": {
        "hospital_registered": None,
        "medical_necessity_confirmed": None
    }
}

findings_006 = engine.evaluate(claim_006)

print("\n\nPUB-006 RESULTS")
print("=" * 50)

for finding in findings_006:
    print(f"\nRule       : {finding['rule']}")
    print(f"Status     : {finding['status']}")
    print(f"Effect     : {finding['effect']}")
    print(f"Reason     : {finding['reason']}")
    print(f"Citation   : {finding['citation']}")

    import json


with open(
    "data/cases/public_test_cases.json",
    "r",
    encoding="utf-8"
) as f:
    public_cases = json.load(f)


pub_007 = next(
    case
    for case in public_cases
    if case["case_id"] == "PUB-007"
)

engine = PolicyRuleEngine()

results = engine.evaluate(pub_007)

print("\nPUB-007 RESULTS")
print("=" * 50)

for result in results:
    print(
        f"\nRule       : {result['rule']}"
    )
    print(
        f"Status     : {result['status']}"
    )
    print(
        f"Effect     : {result['effect']}"
    )
    print(
        f"Reason     : {result['reason']}"
    )
    print(
        f"Citation   : {result['citation']}"
    )
    # ==================================================
# PUB-008
# COSMETIC TREATMENT
# ==================================================

pub_008 = next(
    case
    for case in public_cases
    if case["case_id"] == "PUB-008"
)

results = engine.evaluate(pub_008)

print("\nPUB-008 RESULTS")
print("=" * 50)

for result in results:
    print(
        f"\nRule       : {result['rule']}"
    )
    print(
        f"Status     : {result['status']}"
    )
    print(
        f"Effect     : {result['effect']}"
    )
    print(
        f"Reason     : {result['reason']}"
    )
    print(
        f"Citation   : {result['citation']}"
    )
    # ==================================================
# PUB-009
# PRE/POST HOSPITALIZATION WINDOWS
# ==================================================

pub_009 = next(
    case
    for case in public_cases
    if case["case_id"] == "PUB-009"
)

results = engine.evaluate(pub_009)

print("\nPUB-009 RESULTS")
print("=" * 50)

for result in results:
    print(
        f"\nRule       : {result['rule']}"
    )
    print(
        f"Status     : {result['status']}"
    )
    print(
        f"Effect     : {result['effect']}"
    )
    print(
        f"Reason     : {result['reason']}"
    )
    print(
        f"Citation   : {result['citation']}"
    )