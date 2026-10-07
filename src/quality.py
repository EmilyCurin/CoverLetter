from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from .models import CandidateProfile


@dataclass
class QualityScore:
    role_specificity: int
    evidence_use: int
    motivation_use: int
    professionalism: int
    length_fit: int
    privacy: int

    @property
    def total(self) -> int:
        return sum(asdict(self).values())

    @property
    def max_total(self) -> int:
        return 12


def _contains_any(haystack: str, needles: list[str]) -> bool:
    h = haystack.lower()
    return any(n.strip().lower() in h for n in needles if n and n.strip())


def score_letter(letter: str, profile: CandidateProfile) -> QualityScore:
    """Simple reproducible rubric: each criterion is 0, 1, or 2."""
    text = letter or ""
    words = re.findall(r"\b\w+\b", text)
    n = len(words)

    role_specificity = 2 if _contains_any(text, [profile.target_role, profile.target_company]) else 0
    if role_specificity == 2 and not profile.target_company:
        role_specificity = 1

    skills = [s.strip() for s in re.split(r"[,;\n]", profile.skills) if s.strip()]
    evidence_use = 2 if _contains_any(text, skills[:5]) and bool(profile.achievements.strip()) else 1 if _contains_any(text, skills[:5]) else 0
    motivation_use = 2 if profile.motivation.strip() and _contains_any(text, [profile.motivation[:45]]) else 1 if "interest" in text.lower() else 0
    professionalism = 2 if ("dear" in text.lower() and ("sincerely" in text.lower() or "regards" in text.lower())) else 1
    length_fit = 2 if 180 <= n <= 380 else 1 if 100 <= n <= 500 else 0

    sensitive_values = [
        profile.current_employer,
        profile.email,
        profile.phone,
        f"{profile.current_salary:g}" if profile.current_salary else "",
        f"{profile.desired_salary:g}" if profile.desired_salary else "",
    ]
    leaked = [s for s in sensitive_values if s and s.lower() in text.lower()]
    # Candidate name is allowed in final locally assembled output, so it is not counted here.
    privacy = 0 if leaked else 2

    return QualityScore(
        role_specificity=role_specificity,
        evidence_use=evidence_use,
        motivation_use=motivation_use,
        professionalism=professionalism,
        length_fit=length_fit,
        privacy=privacy,
    )
