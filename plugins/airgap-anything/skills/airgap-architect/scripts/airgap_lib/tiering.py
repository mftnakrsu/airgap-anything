"""Base tier, per-layer floors and the requirements escalators switch on."""
from __future__ import annotations

from .constants import LAYERS, REQUIREMENTS, max_tier
from .rules import Rules

# Answers tier.py needs. Everything else may still be unanswered.
TIER_ANSWERS = (
    "org.users_total",
    "org.departments",
    "org.isolation",
    "org.audit_required",
    "org.downtime_tolerance",
    "org.kubernetes_experience",
)


def base_tier(users: int, departments: int, rules: Rules) -> str:
    """The higher of the tier implied by users and by departments."""

    def implied(value: int, t1_key: str, t2_key: str) -> str:
        if value <= rules.value(t1_key):
            return "T1"
        if value <= rules.value(t2_key):
            return "T2"
        return "T3"

    return max_tier(
        implied(users, "tiers.t1_max_users", "tiers.t2_max_users"),
        implied(departments, "tiers.t1_max_departments", "tiers.t2_max_departments"),
    )


def compute_tier(answers: dict, rules: Rules) -> dict:
    """`answers` must be resolved and contain every ID in TIER_ANSWERS."""
    base = base_tier(answers["org.users_total"], answers["org.departments"], rules)
    floors = {layer: base for layer in LAYERS}
    requirements = {name: False for name in REQUIREMENTS}
    reasons: list[str] = []
    for escalator in rules.escalators:
        answer = answers.get(escalator["answer"])
        expected = escalator["equals"]
        if type(answer) is not type(expected) or answer != expected:
            continue
        for layer, tier in escalator.get("floors", {}).items():
            floors[layer] = max_tier(floors[layer], tier)
        for name in escalator.get("requires", []):
            requirements[name] = True
        reasons.append(escalator["reason"])
    if floors["orchestration"] == "T3" and answers.get("org.kubernetes_experience") is False:
        requirements["kubernetes_risk_note"] = True
        reasons.append(
            "the orchestration floor is T3 but org.kubernetes_experience is false"
        )
    return {
        "base": base,
        "floors": floors,
        "requirements": requirements,
        "reasons": reasons,
    }
