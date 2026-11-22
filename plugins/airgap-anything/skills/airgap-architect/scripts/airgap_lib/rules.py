"""rules.toml: thresholds, escalators, sizing defaults and answer defaults."""
from __future__ import annotations

import tomllib
from pathlib import Path

from .constants import ESCALATOR_REQUIREMENTS, LAYERS, SCHEMA_VERSION, TIERS
from .evidence import evidence_problems
from .findings import Finding

REQUIRED_CONSTANTS = (
    "tiers.t1_max_users",
    "tiers.t2_max_users",
    "tiers.t1_max_departments",
    "tiers.t2_max_departments",
    "sizing.chat.active",
    "sizing.chat.duty_low",
    "sizing.chat.duty_high",
    "sizing.rag.active",
    "sizing.rag.duty_low",
    "sizing.rag.duty_high",
    "sizing.code_assistant.active",
    "sizing.code_assistant.duty_low",
    "sizing.code_assistant.duty_high",
    "sizing.gpu_memory_utilization",
    "sizing.overhead",
    "sizing.gpu_group_sizes",
    "sizing.default_precision",
    "sizing.default_context_tokens",
    "sizing.default_output_tokens",
    "sizing.default_kv_dtype",
    "sizing.size_class.S",
    "sizing.size_class.M",
    "sizing.size_class.L",
    "sizing.size_class.XL",
    "sizing.gpus_per_server",
    "sizing.power_system_factor",
    "sizing.ha_min_replicas",
    "lint.freshness_days",
)
BYTES_PREFIX = "sizing.bytes_per_param."
_RESERVED_TOP_LEVEL = ("schema_version", "escalators")


class Rules:
    """Read access to rules.toml. A constant's ID is its table path."""

    def __init__(self, data: dict):
        self.data = data
        self._constants: dict[str, dict] = {}
        self._collect("", data)

    def _collect(self, prefix: str, table: dict) -> None:
        for key, value in table.items():
            if not prefix and key in _RESERVED_TOP_LEVEL:
                continue
            if not isinstance(value, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if "value" in value:
                self._constants[path] = value
            else:
                self._collect(path, value)

    def has(self, key: str) -> bool:
        return key in self._constants

    def constant_keys(self) -> list[str]:
        return sorted(self._constants)

    def entry(self, key: str) -> dict:
        return self._constants[key]

    def value(self, key: str):
        return self._constants[key]["value"]

    def use(self, key: str, sink: list[dict] | None = None):
        """Return a constant's value and record it once in `sink`."""
        entry = self._constants[key]
        if sink is not None and not any(item["id"] == key for item in sink):
            sink.append(
                {
                    "id": key,
                    "value": entry["value"],
                    "evidence": entry.get("evidence", "estimate"),
                    "note": entry.get("notes", ""),
                }
            )
        return entry["value"]

    def precisions(self) -> tuple[str, ...]:
        return tuple(
            key[len(BYTES_PREFIX):]
            for key in self.constant_keys()
            if key.startswith(BYTES_PREFIX)
        )

    @property
    def escalators(self) -> list[dict]:
        return list(self.data.get("escalators", []))

    def default_answer(self, question_id: str) -> dict | None:
        """The default entry for an answer given as 'unknown', or None."""
        return self._constants.get(f"defaults.{question_id}")


def load_rules(path: Path) -> Rules:
    with Path(path).open("rb") as handle:
        return Rules(tomllib.load(handle))


_POSITIVE_INTS = (
    "tiers.t1_max_users",
    "tiers.t2_max_users",
    "tiers.t1_max_departments",
    "tiers.t2_max_departments",
    "sizing.default_context_tokens",
    "sizing.default_output_tokens",
    "sizing.gpus_per_server",
    "sizing.ha_min_replicas",
    "lint.freshness_days",
)
_USAGE_FIELDS = ("active", "duty_low", "duty_high")
_SIZE_CLASS_PREFIX = "sizing.size_class."


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _usage_types(rules: Rules) -> list[str]:
    """Usage types that define a sizing.<usage>.<field> constant."""
    names = set()
    for key in rules.constant_keys():
        parts = key.split(".")
        if len(parts) == 3 and parts[0] == "sizing" and parts[2] in _USAGE_FIELDS:
            names.add(parts[1])
    return sorted(names)


def _value_findings(rules: Rules) -> list[Finding]:
    """C1 findings for constant values of the wrong type or outside their range."""
    findings: list[Finding] = []
    bad: set[str] = set()

    def reject(key: str, expected: str) -> None:
        bad.add(key)
        findings.append(Finding("C1", f"rules.toml: {key}: value must be {expected}"))

    def check(key: str, accepts, expected: str) -> None:
        if rules.has(key) and not accepts(rules.value(key)):
            reject(key, expected)

    def positive_int(value) -> bool:
        return _is_int(value) and value >= 1

    def share(value) -> bool:
        return _is_number(value) and 0 < value <= 1

    def positive(value) -> bool:
        return _is_number(value) and value > 0

    for key in _POSITIVE_INTS:
        check(key, positive_int, "an integer of at least 1")
    usages = _usage_types(rules)
    for usage in usages:
        for field in _USAGE_FIELDS:
            check(f"sizing.{usage}.{field}", share, "a number above 0 and at most 1")
    check("sizing.gpu_memory_utilization", share, "a number above 0 and at most 1")
    check("sizing.overhead", lambda v: _is_number(v) and v >= 0, "a number of at least 0")
    for key in rules.constant_keys():
        if key.startswith(BYTES_PREFIX) or key.startswith(_SIZE_CLASS_PREFIX):
            check(key, positive, "a number above 0")
    check("sizing.power_system_factor", positive, "a number above 0")

    key = "sizing.gpu_group_sizes"
    if rules.has(key):
        sizes = rules.value(key)
        if not (
            isinstance(sizes, list)
            and sizes
            and all(_is_int(size) and size >= 1 for size in sizes)
            and all(a < b for a, b in zip(sizes, sizes[1:]))
        ):
            reject(key, "a non-empty list of integers of at least 1 in strictly ascending order")

    def ordered(low: str, high: str, relation: str, ok) -> None:
        if rules.has(low) and rules.has(high) and low not in bad and high not in bad:
            if not ok(rules.value(low), rules.value(high)):
                findings.append(
                    Finding("C1", f"rules.toml: {low}: must be {relation} {high}")
                )

    ordered("tiers.t1_max_users", "tiers.t2_max_users", "below", lambda a, b: a < b)
    ordered(
        "tiers.t1_max_departments",
        "tiers.t2_max_departments",
        "below",
        lambda a, b: a < b,
    )
    for usage in usages:
        ordered(
            f"sizing.{usage}.duty_low",
            f"sizing.{usage}.duty_high",
            "at most",
            lambda a, b: a <= b,
        )
    return findings


def validate_rules(rules: Rules) -> list[Finding]:
    findings: list[Finding] = []
    if rules.data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding("C1", f"rules.toml: schema_version must be {SCHEMA_VERSION}")
        )
    for key in REQUIRED_CONSTANTS:
        if not rules.has(key):
            findings.append(Finding("C1", f"rules.toml: missing constant '{key}'"))
    precisions = rules.precisions()
    if not precisions:
        findings.append(
            Finding("C1", f"rules.toml: no '{BYTES_PREFIX}<precision>' constants")
        )
    for key in ("sizing.default_precision", "sizing.default_kv_dtype"):
        if rules.has(key) and rules.value(key) not in precisions:
            findings.append(
                Finding("C1", f"rules.toml: {key} must name a known precision")
            )
    findings.extend(_value_findings(rules))
    for key in rules.constant_keys():
        entry = rules.entry(key)
        for problem in evidence_problems(
            entry.get("evidence"),
            entry.get("sources"),
            entry.get("verified_by"),
            entry.get("notes"),
        ):
            findings.append(Finding("C4", f"rules.toml: {key}: {problem}"))
    seen_ids: set[str] = set()
    for index, escalator in enumerate(rules.escalators):
        where = f"rules.toml: escalators[{index}]"
        if not isinstance(escalator, dict):
            findings.append(Finding("C1", f"{where}: must be a table"))
            continue
        escalator_id = escalator.get("id")
        if not isinstance(escalator_id, str) or not escalator_id:
            findings.append(Finding("C1", f"{where}: needs a non-empty string 'id'"))
        elif escalator_id in seen_ids:
            findings.append(Finding("C1", f"{where}: duplicate id '{escalator_id}'"))
        else:
            seen_ids.add(escalator_id)
        if not isinstance(escalator.get("answer"), str) or "equals" not in escalator:
            findings.append(Finding("C1", f"{where}: needs 'answer' and 'equals'"))
        if not isinstance(escalator.get("reason"), str) or not escalator["reason"]:
            findings.append(Finding("C1", f"{where}: needs a 'reason'"))
        floors = escalator.get("floors", {})
        if not isinstance(floors, dict) or any(
            layer not in LAYERS or tier not in TIERS for layer, tier in floors.items()
        ):
            findings.append(
                Finding("C1", f"{where}: floors must map known layers to T1, T2 or T3")
            )
        requires = escalator.get("requires", [])
        if not isinstance(requires, list) or any(
            name not in ESCALATOR_REQUIREMENTS for name in requires
        ):
            findings.append(
                Finding(
                    "C1",
                    f"{where}: requires must be a list drawn from "
                    + ", ".join(ESCALATOR_REQUIREMENTS),
                )
            )
        for problem in evidence_problems(
            escalator.get("evidence"),
            escalator.get("sources"),
            escalator.get("verified_by"),
            escalator.get("notes"),
        ):
            findings.append(Finding("C4", f"{where}: {problem}"))
    return findings
