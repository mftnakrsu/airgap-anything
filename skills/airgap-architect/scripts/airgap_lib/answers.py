"""The interview's question table: validation and 'unknown' handling."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .constants import (
    GPU_VENDORS,
    INTERACTIVE_USAGE,
    MODEL_ROLES,
    SIZE_CLASSES,
    UNKNOWN,
    USAGE_TYPES,
)
from .findings import Finding
from .rules import Rules


@dataclass(frozen=True)
class Question:
    id: str
    kind: str
    required: bool
    choices: tuple[str, ...] = ()


QUESTIONS = (
    Question("org.users_total", "count", True),
    Question("org.departments", "count", True),
    Question("org.isolation", "enum", True, ("none", "per_department", "multi_level")),
    Question("org.audit_required", "bool", True),
    Question("org.downtime_tolerance", "enum", True, ("accepted", "planned_only", "none")),
    Question("org.ops_capacity", "enum", True, ("part_time_one", "small_team", "platform_team")),
    Question("org.kubernetes_experience", "bool", True),
    Question("workload.usage", "usage", True),
    Question("workload.models", "models", True),
    Question("workload.context_tokens", "contexts", False),
    Question("hardware.gpus", "gpus", True),
    Question("hardware.ram_gb", "number", False),
    Question("hardware.power_budget_kw", "number", False),
    Question("existing.identity", "enum", True, ("none", "ad_ldap", "oidc")),
    Question("existing.api_gateway", "enum", True, ("none", "kong", "other")),
    Question("existing.kubernetes", "enum", True, ("none", "kubernetes", "openshift")),
    Question("existing.registry", "enum", False, ("none", "harbor", "nexus", "artifactory", "other")),
    Question("transfer.channel", "enum", True, ("removable_media", "data_diode", "staging_host", "other")),
    Question("transfer.cadence", "enum", False, ("ad_hoc", "monthly", "quarterly")),
)
QUESTION_IDS = tuple(question.id for question in QUESTIONS)
REQUIRED_IDS = tuple(question.id for question in QUESTIONS if question.required)
NO_DEFAULT_IDS = ("org.users_total", "org.departments", "workload.models", "hardware.gpus")
_QUESTIONS_BY_ID = {question.id: question for question in QUESTIONS}
_DEFAULTS_PREFIX = "defaults."


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_usage(value) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["must be a non-empty map of usage type to share"]
    errors = []
    for usage_type, share in value.items():
        if usage_type not in USAGE_TYPES:
            errors.append(f"unknown usage type '{usage_type}'")
        elif not _is_number(share) or share < 0:
            errors.append(f"share for '{usage_type}' must be a number of 0 or more")
    if not errors and abs(sum(value.values()) - 1.0) > 1e-6:
        errors.append("shares must sum to 1")
    return errors


def _check_contexts(value) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["must be a non-empty map of usage type to tokens"]
    errors = []
    for usage_type, tokens in value.items():
        if usage_type == "batch":
            errors.append("batch has no interactive context; give chat, code_assistant or rag")
        elif usage_type not in INTERACTIVE_USAGE:
            errors.append(f"unknown usage type '{usage_type}'")
        elif not _is_int(tokens) or tokens <= 0:
            errors.append(f"tokens for '{usage_type}' must be a whole number above 0")
    return errors


def _check_models(value, rules: Rules) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["must be a non-empty list of models"]
    precisions = rules.precisions()
    errors = []
    for index, model in enumerate(value):
        where = f"item {index}"
        if not isinstance(model, dict):
            errors.append(f"{where}: must be an object")
            continue
        if model.get("role") not in MODEL_ROLES:
            errors.append(f"{where}: role must be one of " + ", ".join(MODEL_ROLES))
        given = [key for key in ("weights_gb", "params_b", "size_class") if model.get(key) is not None]
        if len(given) != 1:
            errors.append(f"{where}: give exactly one of weights_gb, params_b, size_class")
        elif given[0] == "size_class":
            if model["size_class"] not in SIZE_CLASSES:
                errors.append(f"{where}: size_class must be one of " + ", ".join(SIZE_CLASSES))
        elif not _is_number(model[given[0]]) or model[given[0]] <= 0:
            errors.append(f"{where}: {given[0]} must be a number above 0")
        precision = model.get("precision")
        if given == ["params_b"] and precision not in precisions:
            errors.append(f"{where}: precision must be one of " + ", ".join(precisions))
        elif precision is not None and precision not in precisions:
            errors.append(f"{where}: precision must be one of " + ", ".join(precisions))
        context = model.get("context_tokens")
        if context is not None and (not _is_int(context) or context <= 0):
            errors.append(f"{where}: context_tokens must be a whole number above 0")
        arch = model.get("arch")
        if arch is None:
            continue
        if not isinstance(arch, dict):
            errors.append(f"{where}: arch must be an object")
            continue
        for key in ("layers", "kv_heads", "head_dim"):
            if not _is_int(arch.get(key)) or arch[key] <= 0:
                errors.append(f"{where}: arch.{key} must be a whole number above 0")
        if arch.get("kv_dtype") is not None and arch["kv_dtype"] not in precisions:
            errors.append(f"{where}: arch.kv_dtype must be one of " + ", ".join(precisions))
    return errors


def _check_gpus(value) -> list[str]:
    if not isinstance(value, list):
        return ["must be a list (empty when there is no GPU)"]
    errors = []
    for index, gpu in enumerate(value):
        where = f"item {index}"
        if not isinstance(gpu, dict):
            errors.append(f"{where}: must be an object")
            continue
        if not isinstance(gpu.get("model"), str) or not gpu["model"].strip():
            errors.append(f"{where}: model must be a non-empty string")
        if not _is_int(gpu.get("count")) or gpu["count"] < 1:
            errors.append(f"{where}: count must be a whole number of 1 or more")
        if gpu.get("vendor") is not None and gpu["vendor"] not in GPU_VENDORS:
            errors.append(f"{where}: vendor must be one of " + ", ".join(GPU_VENDORS))
        for key in ("vram_gb", "tdp_w"):
            if gpu.get(key) is not None and (not _is_number(gpu[key]) or gpu[key] <= 0):
                errors.append(f"{where}: {key} must be a number above 0")
    return errors


def _check(question: Question, value, rules: Rules) -> list[str]:
    if question.kind == "count":
        return [] if _is_int(value) and value >= 1 else ["must be a whole number of 1 or more"]
    if question.kind == "bool":
        return [] if isinstance(value, bool) else ["must be true or false"]
    if question.kind == "enum":
        return [] if value in question.choices else ["must be one of " + ", ".join(question.choices)]
    if question.kind == "number":
        return [] if _is_number(value) and value > 0 else ["must be a number above 0"]
    if question.kind == "usage":
        return _check_usage(value)
    if question.kind == "models":
        return _check_models(value, rules)
    if question.kind == "contexts":
        return _check_contexts(value)
    return _check_gpus(value)


def validate_defaults(rules: Rules) -> list[Finding]:
    """C1 findings for answer defaults in rules.toml that do not fit their question."""
    findings: list[Finding] = []
    for key in rules.constant_keys():
        if not key.startswith(_DEFAULTS_PREFIX):
            continue
        question_id = key[len(_DEFAULTS_PREFIX):]
        question = _QUESTIONS_BY_ID.get(question_id)
        if question is None:
            reason = "not a question of the interview"
        elif question_id in NO_DEFAULT_IDS:
            reason = "this question must be answered and cannot have a default"
        else:
            reason = "; ".join(_check(question, rules.value(key), rules))
        if reason:
            findings.append(Finding("C1", f"rules.toml: {key}: {reason}"))
    return findings


def resolve_answers(
    answers: dict, rules: Rules, needed: Iterable[str] | None = None
) -> tuple[dict, list[dict], list[str]]:
    """Validate answers and replace 'unknown' with documented defaults.

    Returns (resolved, assumptions, problems).
    - resolved: a copy of `answers` with every defaultable 'unknown' replaced.
    - assumptions: one record per default that was applied (all questions).
    - problems: "question.id: reason" for missing or invalid answers.
      With `needed=None` every question is checked; otherwise only `needed`.
    """
    check_ids = set(QUESTION_IDS if needed is None else needed)
    resolved = dict(answers)
    assumptions: list[dict] = []
    problems: list[str] = []
    for question in QUESTIONS:
        checked = question.id in check_ids
        value = answers.get(question.id)
        if isinstance(value, str) and value == UNKNOWN:
            default = rules.default_answer(question.id)
            if default is not None:
                reasons = _check(question, default["value"], rules)
                if reasons:
                    if checked:
                        problems.append(
                            f"{question.id}: default in rules.toml is invalid: " + "; ".join(reasons)
                        )
                    continue
                resolved[question.id] = default["value"]
                assumptions.append(
                    {
                        "id": f"answers.{question.id}",
                        "value": default["value"],
                        "evidence": default.get("evidence", "estimate"),
                        "note": "answer was 'unknown'; default applied",
                    }
                )
            elif question.required:
                if checked:
                    problems.append(f"{question.id}: must be answered; 'unknown' has no default")
            else:
                resolved.pop(question.id, None)
            continue
        if value is None:
            if checked and question.required:
                problems.append(f"{question.id}: missing")
            continue
        if checked:
            problems += [f"{question.id}: {error}" for error in _check(question, value, rules)]
    if (
        "hardware.ram_gb" in check_ids
        and resolved.get("hardware.gpus") == []
        and resolved.get("hardware.ram_gb") is None
    ):
        problems.append("hardware.ram_gb: missing (required when hardware.gpus is empty)")
    return resolved, assumptions, problems
