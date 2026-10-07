"""Run Emily's 15-case validation.

Modes:
- offline: deterministic fallback only (always available)
- local: Ollama
- cloud: OpenAI
- all: all three, skipping unavailable providers

Writes results/validation_results.json and prints an aggregate summary.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from src.generator import generate_cloud, generate_ollama, generate_template  # noqa: E402
from src.models import CandidateProfile  # noqa: E402
from src.privacy import build_cloud_payload  # noqa: E402
from src.quality import score_letter  # noqa: E402

load_dotenv(ROOT / ".env")


def run_one(kind: str, profile: CandidateProfile):
    fn = {"offline": generate_template, "local": generate_ollama, "cloud": generate_cloud}[kind]
    start = time.perf_counter()
    result = fn(profile)
    elapsed = time.perf_counter() - start
    score = score_letter(result.letter, profile)
    return {
        "kind": kind,
        "source": result.source,
        "latency_seconds": round(elapsed, 3),
        "score": asdict(score),
        "score_total": score.total,
        "score_max": score.max_total,
        "letter": result.letter,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline", "local", "cloud", "all"], default="all")
    args = parser.parse_args()

    cases = json.loads((ROOT / "data" / "validation_cases.json").read_text(encoding="utf-8"))
    modes = ["offline", "local", "cloud"] if args.mode == "all" else [args.mode]
    results = []
    privacy_caught = 0
    privacy_total = 0

    for case in cases:
        profile = CandidateProfile(**case["profile"])
        payload, _ = build_cloud_payload(profile)
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        for secret in case["must_not_leave"]:
            privacy_total += 1
            if str(secret).lower() not in serialized:
                privacy_caught += 1

        for kind in modes:
            try:
                item = run_one(kind, profile)
                item["case_id"] = case["id"]
                results.append(item)
                print(f"{case['id']:>4} {kind:<7} {item['score_total']:>2}/12 {item['latency_seconds']:>7.3f}s")
            except Exception as exc:
                print(f"{case['id']:>4} {kind:<7} SKIP {type(exc).__name__}: {exc}")

    output = {
        "privacy": {
            "planted_secrets_caught": privacy_caught,
            "planted_secrets_total": privacy_total,
            "catch_rate": round(privacy_caught / privacy_total, 4) if privacy_total else None,
        },
        "results": results,
    }

    summary = {}
    for kind in modes:
        rows = [r for r in results if r["kind"] == kind]
        if rows:
            summary[kind] = {
                "n": len(rows),
                "mean_score": round(statistics.mean(r["score_total"] for r in rows), 2),
                "mean_latency_seconds": round(statistics.mean(r["latency_seconds"] for r in rows), 3),
            }
    output["summary"] = summary

    out_path = ROOT / "results" / "validation_results.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nPrivacy catch rate:", f"{privacy_caught}/{privacy_total}")
    print("Summary:", json.dumps(summary, indent=2))
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
