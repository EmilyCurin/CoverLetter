from __future__ import annotations

from dataclasses import dataclass

from .models import CandidateProfile


@dataclass
class NegotiationResult:
    note: str
    uplift_pct: float | None


def build_private_negotiation_note(profile: CandidateProfile) -> NegotiationResult:
    """Entirely local, deterministic, and intentionally not market advice."""
    current = float(profile.current_salary or 0)
    desired = float(profile.desired_salary or 0)
    currency = profile.currency or "currency units"

    if current <= 0 or desired <= 0:
        return NegotiationResult(
            note=(
                "Private note: add both your current and desired compensation to compare them locally. "
                "These values are never included in the cloud payload."
            ),
            uplift_pct=None,
        )

    uplift = ((desired / current) - 1) * 100
    ratio = desired / current
    if ratio <= 1.10:
        band = "a relatively small increase over your current compensation"
    elif ratio <= 1.30:
        band = "a moderate increase over your current compensation"
    elif ratio <= 1.60:
        band = "a substantial increase over your current compensation"
    else:
        band = "a large jump over your current compensation"

    note = (
        f"Private negotiation note (local only): your target is {uplift:.1f}% above your current pay "
        f"({current:,.2f} → {desired:,.2f} {currency}), which is {band}. "
        "This comparison does not claim what the market rate is; that requires separate market data. "
        "A practical default is not to put compensation in the cover letter. If the employer asks early, "
        "state the target or a range and connect it to role scope; otherwise, discuss it after the role and "
        "responsibilities are clear."
    )
    return NegotiationResult(note=note, uplift_pct=uplift)
