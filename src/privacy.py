"""Deterministic privacy boundary.

No model decides what leaves the device. The outbound payload is constructed from
an explicit allowlist and then sanitized with deterministic rules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import CandidateProfile


# Explicit allowlist: if a field is not here, it cannot be serialized to cloud.
CLOUD_ALLOWLIST = (
    "current_role_generic",
    "target_role",
    "target_company",
    "years_experience",
    "skills",
    "achievements",
    "motivation",
    "job_posting",
    "tone",
)

LOCAL_ONLY_FIELDS = (
    "full_name",
    "email",
    "phone",
    "current_employer",
    "current_salary",
    "desired_salary",
    "currency",
)

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")

# Conservative money redaction. It intentionally removes any obvious monetary
# amount from cloud-bound free text, even if it came from the job posting.
MONEY_PATTERNS = [
    re.compile(r"(?i)(?:Q|GTQ|US\$|USD|\$)\s*\d[\d,]*(?:\.\d{1,2})?"),
    re.compile(r"(?i)\b\d[\d,]*(?:\.\d{1,2})?\s*(?:quetzales?|d[oó]lares?|USD|GTQ)\b"),
    re.compile(
        r"(?i)\b(?:salario|sueldo|salary|compensation|pay)\b[^\n]{0,30}?\d[\d,]*(?:\.\d{1,2})?"
    ),
]


@dataclass(frozen=True)
class PrivacyAudit:
    redactions: int
    redacted_categories: tuple[str, ...]


def _replace_exact_secret(text: str, secret: str) -> tuple[str, int]:
    if not secret or len(secret.strip()) < 2:
        return text, 0
    pattern = re.compile(re.escape(secret.strip()), re.I)
    return pattern.subn("[REDACTED]", text)


def sanitize_text(text: str, profile: CandidateProfile) -> tuple[str, PrivacyAudit]:
    if not text:
        return "", PrivacyAudit(0, ())

    out = str(text)
    count = 0
    categories: set[str] = set()

    # Exact secrets planted in structured local-only fields.
    for category, secret in (
        ("candidate_name", profile.full_name),
        ("current_employer", profile.current_employer),
        ("email", profile.email),
        ("phone", profile.phone),
    ):
        out, n = _replace_exact_secret(out, secret)
        if n:
            count += n
            categories.add(category)

    out, n = EMAIL_RE.subn("[REDACTED_EMAIL]", out)
    if n:
        count += n
        categories.add("email")

    out, n = PHONE_RE.subn("[REDACTED_PHONE]", out)
    if n:
        count += n
        categories.add("phone")

    for pattern in MONEY_PATTERNS:
        out, n = pattern.subn("[REDACTED_MONEY]", out)
        if n:
            count += n
            categories.add("money")

    # Also remove the exact numeric salary values if they were pasted into prose
    # without a currency marker. Only values >= 100 are used to avoid destroying
    # years or small achievement counts.
    for salary in (profile.current_salary, profile.desired_salary):
        if salary and abs(salary) >= 100:
            variants = {
                f"{salary:g}",
                f"{salary:,.0f}",
                f"{salary:,.2f}",
            }
            for v in variants:
                out, n = re.subn(rf"(?<!\d){re.escape(v)}(?!\d)", "[REDACTED_MONEY]", out)
                if n:
                    count += n
                    categories.add("money")

    return out, PrivacyAudit(count, tuple(sorted(categories)))


def build_cloud_payload(profile: CandidateProfile) -> tuple[dict[str, Any], PrivacyAudit]:
    """Build the ONLY object permitted to leave the device.

    This is intentionally explicit and testable. There is no dynamic field
    selection and no model in this decision path.
    """
    raw = profile.to_dict()
    payload: dict[str, Any] = {}
    total_redactions = 0
    categories: set[str] = set()

    for field in CLOUD_ALLOWLIST:
        value = raw[field]
        if isinstance(value, str):
            value, audit = sanitize_text(value, profile)
            total_redactions += audit.redactions
            categories.update(audit.redacted_categories)
        payload[field] = value

    return payload, PrivacyAudit(total_redactions, tuple(sorted(categories)))


def assert_no_local_only_keys(payload: dict[str, Any]) -> None:
    leaked_keys = set(payload).intersection(LOCAL_ONLY_FIELDS)
    if leaked_keys:
        raise AssertionError(f"Local-only fields in cloud payload: {sorted(leaked_keys)}")
