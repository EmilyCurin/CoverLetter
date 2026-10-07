import json
from pathlib import Path

import pytest

from src.models import CandidateProfile
from src.privacy import CLOUD_ALLOWLIST, LOCAL_ONLY_FIELDS, build_cloud_payload


@pytest.fixture
def planted_profile():
    return CandidateProfile(
        full_name="Emily Secret",
        email="emily.secret@example.com",
        phone="+502 5555 1234",
        current_employer="Private Robotics SA",
        current_salary=15000,
        desired_salary=22000,
        currency="GTQ",
        current_role_generic="Mechatronics engineer",
        target_role="Program Manager",
        target_company="Future Learning",
        years_experience=5,
        skills="coordination, STEM education",
        achievements=(
            "At Private Robotics SA I earned Q15,000 and can be reached at emily.secret@example.com. "
            "I coordinated 8 events."
        ),
        motivation="I want broader community impact.",
        job_posting="Salary USD 3,000. Call +502 5555 1234.",
    )


def test_cloud_payload_uses_explicit_allowlist(planted_profile):
    payload, _ = build_cloud_payload(planted_profile)
    assert tuple(payload.keys()) == CLOUD_ALLOWLIST
    assert not set(payload).intersection(LOCAL_ONLY_FIELDS)


def test_salary_and_identity_never_leave(planted_profile):
    payload, audit = build_cloud_payload(planted_profile)
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    forbidden = [
        "15000",
        "15,000",
        "22000",
        "22,000",
        "private robotics sa",
        "emily secret",
        "emily.secret@example.com",
        "+502 5555 1234",
    ]
    for secret in forbidden:
        assert secret.lower() not in serialized
    assert audit.redactions >= 3


def test_all_15_planted_cases_keep_salary_out():
    cases_path = Path(__file__).parents[1] / "data" / "validation_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    assert len(cases) >= 15
    for case in cases:
        profile = CandidateProfile(**case["profile"])
        payload, _ = build_cloud_payload(profile)
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        for secret in case["must_not_leave"]:
            assert str(secret).lower() not in serialized, f"Leak in case {case['id']}: {secret}"
