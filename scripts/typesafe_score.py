#!/usr/bin/env python3
"""TypeSafe (System One / Jev) lead scorer for the revenue-engine skill.

Turns the dimensions in references/icp-scoring.md into typed judgments instead of
a subagent reasoning them out freehand: vertical match, signal strength,
geography fit, stage/budget fit, and offer fit. The calling subagent still owns
exclude.md, dedupe, and the High/Medium/Low banding weights in preferences.md -
this script only answers the underlying per-dimension judgments, in parallel, in
one request.

Uses curl for HTTPS (avoids the macOS python-ssl/certifi gap, same as
hunter_lookup.py). Reads the API key from $TYPESAFE_API_KEY or
~/.revenue-engine-imparatta/.secrets/typesafe.env (never in this repo).

Usage:
  python3 typesafe_score.py score --record lead.json
  python3 typesafe_score.py score < lead.json   # or via stdin

Input record (JSON):
  {
    "company": "Acme Inc",
    "vertical": "logistics software",
    "country": "United States",
    "signal": "posted a 'VP of Product' role 4 months ago, still unfilled",
    "source_url": "https://...",
    "icp_verticals": ["logistics", "vertical SaaS", "climate tech"],
    "icp_geographies": ["United States", "Canada", "remote-first"],
    "icp_stage": "seed to Series B, 10-150 employees",
    "offers": [
      {"name": "stalled-to-shipped", "what": "get a stalled product into production"},
      {"name": "ai-demo-to-prod", "what": "take an AI demo to a real production system"},
      {"name": "fractional-leadership", "what": "fractional product/delivery leadership"}
    ]
  }

Output: the raw TypeSafe response JSON, with one answer block per dimension
(vertical_match, signal_strength, geography_fit, stage_budget_fit, offer_fit)
plus usage. The caller composes these into a High/Medium/Low band using the
weights in ~/.revenue-engine-imparatta/preferences.md - this script has no
opinion on banding.
"""
import argparse, json, os, subprocess, sys

API_URL = "https://api.typesafe.ai/v1/systemone"


def load_key():
    k = os.environ.get("TYPESAFE_API_KEY")
    if k:
        return k.strip()
    env = os.path.expanduser("~/.revenue-engine-imparatta/.secrets/typesafe.env")
    if os.path.exists(env):
        for line in open(env):
            if line.startswith("TYPESAFE_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("No TYPESAFE_API_KEY in env or ~/.revenue-engine-imparatta/.secrets/typesafe.env")


def build_state(rec):
    return {
        "company": rec["company"],
        "vertical": rec.get("vertical", ""),
        "country": rec.get("country", ""),
        "signal": rec.get("signal", ""),
        "source_url": rec.get("source_url", ""),
        "icp_verticals": rec.get("icp_verticals", []),
        "icp_geographies": rec.get("icp_geographies", []),
        "icp_stage": rec.get("icp_stage", ""),
        "offers": rec.get("offers", []),
    }


def build_questions(rec):
    offer_criteria = {o["name"]: o.get("what", "") for o in rec.get("offers", [])}
    offer_criteria["no_fit"] = "None of the offers cleanly solve the evidenced need - a forced fit"
    return {
        "vertical_match": {
            "type": "choice",
            "instructions": (
                "Compare `company`'s `vertical` against `icp_verticals`. Does the "
                "company sit in a target vertical, an adjacent one, or neither?"
            ),
            "criteria": {
                "in_vertical": "The company's vertical is one of icp_verticals, or a clear synonym of one",
                "adjacent": "Related to a target vertical but not a direct match",
                "unrelated": "No meaningful overlap with any icp_vertical",
            },
        },
        "signal_strength": {
            "type": "noul",
            "instructions": (
                "Is `signal` a fresh, specific buying signal (a recent raise, an open "
                "role that IS the pain, hard evidence of the problem) rather than a "
                "generic or stale one (boilerplate posting, vague, old)?"
            ),
        },
        "geography_fit": {
            "type": "choice",
            "instructions": "Compare `country` against `icp_geographies`.",
            "criteria": {
                "in_geo": "country is in icp_geographies, or remote-first/no geo constraint applies",
                "near_miss": "Close to a target geography but not listed - could still qualify if the signal is strong",
                "hard_avoid": "Clearly outside every target geography with no remote/near-miss case",
            },
        },
        "stage_budget_fit": {
            "type": "score",
            "instructions": (
                "Given `icp_stage` and what `signal` implies about company size/stage, "
                "how plausible is it this company can pay for and needs the offer?"
            ),
            "criteria": [
                "Too early (no budget yet), or so large it plausibly solves this in-house with no visible gap",
                "Plausible - roughly matches icp_stage, some uncertainty",
                "Strong fit - matches icp_stage with a clear, current gap",
            ],
        },
        "offer_fit": {
            "type": "choice",
            "instructions": (
                "Which offer in `offers` most cleanly solves the need evidenced by "
                "`signal`? Pick no_fit if none genuinely fit - a forced fit is worse than no fit."
            ),
            "criteria": offer_criteria,
        },
    }


def call_system_one(state, questions):
    body = json.dumps({"model": "jev-latest", "state": state, "questions": questions})
    proc = subprocess.run(
        ["curl", "-sS", "-X", "POST", API_URL,
         "-H", f"Authorization: Bearer {load_key()}",
         "-H", "Content-Type: application/json",
         "-d", body],
        capture_output=True, text=True,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": (proc.stdout or proc.stderr)[:500]}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("--record", help="path to the lead JSON record (default: stdin)")
    a = ap.parse_args()

    raw = open(a.record).read() if a.record else sys.stdin.read()
    rec = json.loads(raw)

    result = call_system_one(build_state(rec), build_questions(rec))
    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
