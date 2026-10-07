from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

from .models import CandidateProfile
from .privacy import build_cloud_payload
from .prompts import CLOUD_INSTRUCTIONS, LOCAL_INSTRUCTIONS


@dataclass
class GenerationResult:
    letter: str
    source: str
    detail: str = ""
    cloud_payload: dict | None = None


def _compact_facts(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def add_local_signature(letter: str, full_name: str) -> str:
    clean = letter.strip()
    if not full_name.strip():
        return clean
    # Candidate name is deliberately added after cloud generation.
    return f"{clean}\n{full_name.strip()}"


def generate_cloud(profile: CandidateProfile) -> GenerationResult:
    payload, audit = build_cloud_payload(profile)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(timeout=float(os.getenv("CLOUD_TIMEOUT_SECONDS", "25")))
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    response = client.responses.create(
        model=model,
        instructions=CLOUD_INSTRUCTIONS,
        input=(
            "Create a cover letter from this sanitized JSON. "
            "Never infer redacted values.\n\n" + _compact_facts(payload)
        ),
        max_output_tokens=700,
    )
    text = (response.output_text or "").strip()
    if not text:
        raise RuntimeError("Cloud model returned empty text")
    return GenerationResult(
        letter=add_local_signature(text, profile.full_name),
        source=f"cloud:{model}",
        detail=f"privacy redactions before cloud: {audit.redactions}",
        cloud_payload=payload,
    )


def generate_ollama(profile: CandidateProfile) -> GenerationResult:
    payload, audit = build_cloud_payload(profile)
    # For the cover letter fallback we still use the sanitized representation,
    # even though Ollama is local. This keeps behavior comparable in validation.
    model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    timeout = float(os.getenv("LOCAL_TIMEOUT_SECONDS", "90"))

    response = requests.post(
        url,
        json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": LOCAL_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": "Write the letter using this JSON:\n" + _compact_facts(payload),
                },
            ],
            "options": {"temperature": 0.4},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError("Ollama returned empty text")
    return GenerationResult(
        letter=add_local_signature(text, profile.full_name),
        source=f"local-model:{model}",
        detail=f"privacy redactions before local model: {audit.redactions}",
        cloud_payload=payload,
    )


def _drop_redacted_fragments(text: str) -> str:
    """Remove sentence-like fragments containing redaction markers for clean fallback prose."""
    parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
    safe = [p for p in parts if "[REDACTED" not in p]
    return ". ".join(safe).strip() + ("." if safe else "")


def generate_template(profile: CandidateProfile) -> GenerationResult:
    payload, audit = build_cloud_payload(profile)
    role = str(payload.get("target_role", "")).strip() or "the position"
    company = str(payload.get("target_company", "")).strip() or "your organization"
    greeting = "Dear Hiring Team,"

    intro_parts = [f"I am writing to express my interest in {role} at {company}."]
    current_role = str(payload.get("current_role_generic", "")).strip()
    if current_role:
        intro_parts.append(
            f"My background in {current_role} has prepared me to contribute with a practical, organized approach."
        )

    body = []
    skills = _drop_redacted_fragments(str(payload.get("skills", "")))
    achievements = _drop_redacted_fragments(str(payload.get("achievements", "")))
    motivation = _drop_redacted_fragments(str(payload.get("motivation", "")))
    if skills:
        body.append(f"Relevant strengths I would bring include {skills}")
    if achievements:
        body.append(f"One example of my experience is {achievements}")
    if motivation:
        body.append(f"I am especially interested in this opportunity because {motivation}")
    if str(payload.get("job_posting", "")).strip():
        body.append(
            "I would welcome the opportunity to discuss how my experience can support the priorities described in the role."
        )

    if not body:
        body.append(
            "I would welcome the opportunity to explain how my experience, adaptability, and commitment to learning can support the team."
        )

    letter = "\n\n".join(
        [
            greeting,
            " ".join(intro_parts),
            " ".join(body),
            "Thank you for your time and consideration. I would be glad to discuss the role further.",
            "Sincerely,",
        ]
    )
    return GenerationResult(
        letter=add_local_signature(letter, profile.full_name),
        source="local-template",
        detail=f"deterministic offline fallback; no network/model; privacy redactions: {audit.redactions}",
        cloud_payload=None,
    )


def generate_with_fallback(profile: CandidateProfile, prefer_cloud: bool = True) -> GenerationResult:
    errors: list[str] = []
    if prefer_cloud:
        try:
            return generate_cloud(profile)
        except Exception as exc:  # intentionally catches API/network/auth failures
            errors.append(f"cloud={type(exc).__name__}: {exc}")

    try:
        result = generate_ollama(profile)
        if errors:
            result.detail += " | fallback reason: " + " | ".join(errors)
        return result
    except Exception as exc:
        errors.append(f"ollama={type(exc).__name__}: {exc}")

    result = generate_template(profile)
    result.detail += " | " + " | ".join(errors)
    return result
