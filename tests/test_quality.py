from src.generator import generate_template
from src.models import CandidateProfile
from src.quality import score_letter


def test_quality_rubric_runs():
    p = CandidateProfile(
        full_name="A Person",
        current_employer="Secret Co",
        current_salary=9000,
        desired_salary=12000,
        target_role="Program Coordinator",
        target_company="Learning Lab",
        skills="coordination, communication",
        achievements="coordinated 12 workshops",
        motivation="I want to support student success",
    )
    letter = generate_template(p).letter
    score = score_letter(letter, p)
    assert 0 <= score.total <= score.max_total
    assert score.privacy == 2
