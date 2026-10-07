from src.generator import generate_template
from src.models import CandidateProfile
from src.negotiation import build_private_negotiation_note


def test_deterministic_fallback_is_useful_without_network():
    p = CandidateProfile(
        full_name="Test Person",
        current_salary=10000,
        desired_salary=13000,
        currency="GTQ",
        current_role_generic="Mechatronics engineer",
        target_role="Program Coordinator",
        target_company="Example Foundation",
        skills="project coordination, communication",
        achievements="coordinated community STEM events",
        motivation="the role combines education and community work",
    )
    result = generate_template(p)
    assert "Program Coordinator" in result.letter
    assert "Example Foundation" in result.letter
    assert "10000" not in result.letter
    assert "13000" not in result.letter
    assert result.source == "local-template"


def test_negotiation_note_contains_salary_and_is_local_function_only():
    p = CandidateProfile(current_salary=10000, desired_salary=12500, currency="GTQ")
    note = build_private_negotiation_note(p)
    assert "25.0%" in note.note
    assert note.uplift_pct == 25.0
