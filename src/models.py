from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CandidateProfile:
    # LOCAL-ONLY / sensitive
    full_name: str = ""
    email: str = ""
    phone: str = ""
    current_employer: str = ""
    current_salary: float = 0.0
    desired_salary: float = 0.0
    currency: str = "GTQ"

    # Allowed to be considered for cloud after deterministic sanitization
    current_role_generic: str = ""
    target_role: str = ""
    target_company: str = ""
    years_experience: int = 0
    skills: str = ""
    achievements: str = ""
    motivation: str = ""
    job_posting: str = ""
    tone: str = "professional and warm"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
