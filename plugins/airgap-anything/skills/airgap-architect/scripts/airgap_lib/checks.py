"""Blueprint lint: errors E1-E11, warnings W1-W3 and note N1 of the design spec."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .answers import QUESTIONS, resolve_answers
from .blueprint import (
    chosen_components,
    decision_for,
    decisions_of,
    has_override,
    inputs_digest,
    load_blueprint,
    validate_schema,
)
from .catalog import Catalog, is_stale
from .constants import (
    AGENT_BLOCK_END,
    AGENT_BLOCK_START,
    ISOLATION_MARKER,
    LAYERS,
    SECTION_MARKERS,
    UNKNOWN,
    section_marker,
    weakest,
)
from .findings import SEVERITIES, Finding
from .sizing import SizingInputError, compute_sizing
from .tiering import compute_tier
from .transfer import MANIFEST_FILENAME, read_manifest_digest


def split_sections(text: str) -> tuple[dict[str, str], list[str]]:
    """Map each section marker to the text that follows it; also return problems."""
    problems: list[str] = []
    positions: list[tuple[int, str]] = []
    for name in SECTION_MARKERS:
        position = text.find(section_marker(name))
        if position < 0:
            problems.append(f"section marker '{section_marker(name)}' is missing")
        else:
            positions.append((position, name))
    if [name for _, name in sorted(positions)] != [name for _, name in positions]:
        problems.append("section markers are out of order")
    ordered = sorted(positions)
    sections: dict[str, str] = {}
    for index, (position, name) in enumerate(ordered):
        end = ordered[index + 1][0] if index + 1 < len(ordered) else len(text)
        sections[name] = text[position:end]
    return sections, problems


def _names_token(text: str, token: str) -> bool:
    """True when `token` appears as a whole word: not inside "suite" or "open-webui"."""
    return re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text) is not None


def _names_version(text: str, version: str) -> bool:
    """True when `version` appears exactly as written and not as part of a longer version.

    For a pin of 1.2.3, "11.2.3" and "0.1.2.3" do not count (a digit or a dot before
    it), nor do "1.2.30", "1.2.3rc1", "1.2.3-rc1" and "1.2.3+build" (a letter, digit or
    underscore after it, or a dot, hyphen, plus or tilde followed by one); for 18.7,
    "18.7.1" does not count. A space, other punctuation or the end of the text after
    it does, as in "1.2.3, " or "1.2.3." at the end of a sentence.
    """
    pattern = rf"(?<![0-9.]){re.escape(version)}(?!\w|[.+~-]\w)"
    return re.search(pattern, text) is not None


def _report_order(finding: Finding) -> tuple[int, int]:
    """Errors, then warnings, then notes, each in numeric order; the sort is stable."""
    return (SEVERITIES.index(finding.severity), int(finding.code[1:]))


def _effective_evidence(decision: dict, catalog: Catalog) -> str:
    labels = [decision.get("evidence")]
    for component_id in decision.get("components") or []:
        entry = catalog.components.get(component_id)
        if entry:
            labels.append(entry.get("evidence", {}).get("level"))
    if decision.get("custom"):
        labels.append("estimate")
    return weakest(label for label in labels if isinstance(label, str))


def lint_blueprint(
    *,
    blueprint: dict,
    catalog: Catalog,
    blueprint_text: str | None,
    manifest_text: str | None,
    agents_text: str | None,
    today: date,
) -> list[Finding]:
    return _lint(
        blueprint=blueprint,
        catalog=catalog,
        blueprint_text=blueprint_text,
        manifest_text=manifest_text,
        agents_text=agents_text,
        today=today,
        unreadable={},
    )


def _lint(
    *,
    blueprint: dict,
    catalog: Catalog,
    blueprint_text: str | None,
    manifest_text: str | None,
    agents_text: str | None,
    today: date,
    unreadable: dict[str, str],
) -> list[Finding]:
    """The lint run. `unreadable` maps "blueprint", "manifest" or "agents" to the reason
    that file could not be read; such a file is reported instead of "not found"."""
    findings: list[Finding] = []
    rules = catalog.rules

    # E1: structure and answers.
    schema_problems = validate_schema(blueprint)
    findings += [Finding("E1", problem) for problem in schema_problems]
    if schema_problems:
        return findings
    answers = blueprint["answers"]
    resolved, _, answer_problems = resolve_answers(answers, rules)
    findings += [Finding("E1", problem) for problem in answer_problems]

    decisions = decisions_of(blueprint)

    # E2: components exist and belong to the decision's layer. A benchmark component
    # only has to exist.
    for decision in decisions:
        for component_id in decision.get("benchmark", []):
            if component_id not in catalog.components:
                findings.append(
                    Finding("E2", f"{decision['layer']}: unknown component '{component_id}'")
                )
        for component_id in decision["components"]:
            entry = catalog.components.get(component_id)
            if entry is None:
                findings.append(
                    Finding("E2", f"{decision['layer']}: unknown component '{component_id}'")
                )
            elif entry.get("layer") != decision["layer"]:
                findings.append(
                    Finding(
                        "E2",
                        f"{decision['layer']}: '{component_id}' belongs to layer "
                        f"'{entry.get('layer')}'",
                    )
                )

    # E6: stored tier and sizing are fresh. Later checks use the fresh values.
    tier = sizing = None
    if not answer_problems:
        tier = compute_tier(resolved, rules)
        if blueprint["tier"] != tier:
            findings.append(Finding("E6", "tier is stale; run tier.py again"))
        try:
            sizing, _ = compute_sizing(resolved, rules, catalog.gpu)
        except SizingInputError as error:
            findings += [Finding("E1", problem) for problem in error.problems]
        else:
            if blueprint["sizing"] != sizing:
                findings.append(Finding("E6", "sizing is stale; run size.py again"))

    # E3: components allow the layer's floor tier.
    if tier:
        for decision in decisions:
            floor = tier["floors"].get(decision["layer"])
            for component_id in decision["components"]:
                entry = catalog.components.get(component_id)
                if entry and floor not in entry.get("tiers", []) and not has_override(decision):
                    findings.append(
                        Finding(
                            "E3",
                            f"{decision['layer']}: '{component_id}' does not allow floor {floor}; "
                            "choose another component or record an override",
                        )
                    )

    # E4: every layer has a decision with a rationale.
    for layer in LAYERS:
        decision = decision_for(blueprint, layer)
        if decision is None:
            findings.append(Finding("E4", f"{layer}: no decision"))
        elif not decision["rationale"].strip():
            findings.append(Finding("E4", f"{layer}: the decision has no rationale"))

    # E5: escalator requirements.
    if tier:
        requirements = tier["requirements"]
        gateway = decision_for(blueprint, "llm-gateway")
        if requirements["gateway_non_empty"] and gateway is not None:
            empty = not (gateway["components"] or gateway["existing"] or gateway["custom"])
            if empty and not has_override(gateway):
                findings.append(
                    Finding("E5", "llm-gateway: a gateway is required but the decision is empty")
                )
        if requirements["two_engine_replicas"] and sizing:
            minimum = rules.value("sizing.ha_min_replicas")
            # A malformed stored sizing is reported by E6; skip what is not well formed.
            models = blueprint["sizing"].get("models", [])
            for model in models if isinstance(models, list) else []:
                replicas = model.get("replicas") if isinstance(model, dict) else None
                if isinstance(replicas, int) and not isinstance(replicas, bool) and replicas < minimum:
                    findings.append(
                        Finding(
                            "E5",
                            f"llm-serving: model '{model.get('name', '')}' has fewer than "
                            f"{minimum} replicas",
                        )
                    )

    # E7 and E9 read the blueprint file.
    sections: dict[str, str] = {}
    if "blueprint" in unreadable:
        findings.append(
            Finding(
                "E7",
                f"blueprint file at '{blueprint['blueprint_path']}' cannot be read: "
                f"{unreadable['blueprint']}",
            )
        )
    elif blueprint_text is None:
        findings.append(
            Finding("E7", f"blueprint file not found at '{blueprint['blueprint_path']}'")
        )
    else:
        sections, marker_problems = split_sections(blueprint_text)
        findings += [Finding("E7", problem) for problem in marker_problems]
        decision_lines = sections.get("decisions", "").splitlines()
        for component_id in chosen_components(blueprint):
            entry = catalog.components.get(component_id)
            if entry is None:
                continue
            if not any(
                component_id in line and _names_version(line, entry["version"])
                for line in decision_lines
            ):
                findings.append(
                    Finding(
                        "E7",
                        f"the decisions section needs a line naming '{component_id}' with "
                        f"version {entry['version']}",
                    )
                )
        if (
            tier
            and tier["requirements"]["isolation_design_section"]
            and section_marker(ISOLATION_MARKER) not in blueprint_text
        ):
            findings.append(
                Finding("E7", f"marker '{section_marker(ISOLATION_MARKER)}' is missing")
            )

    # E8: transfer manifest exists and matches the decisions.
    if "manifest" in unreadable:
        findings.append(
            Finding("E8", f"{MANIFEST_FILENAME} cannot be read: {unreadable['manifest']}")
        )
    elif manifest_text is None:
        findings.append(Finding("E8", f"{MANIFEST_FILENAME} not found; run manifest.py"))
    elif read_manifest_digest(manifest_text) != inputs_digest(blueprint):
        findings.append(Finding("E8", f"{MANIFEST_FILENAME} is stale; run manifest.py again"))

    # E9: estimate-backed decisions are listed for verification.
    verification_text = sections.get("verification")
    for decision in decisions:
        effective = _effective_evidence(decision, catalog)
        if decision.get("evidence") != effective:
            findings.append(
                Finding(
                    "E9",
                    f"{decision['layer']}: evidence must be '{effective}', the weakest label "
                    "among the decision's inputs",
                )
            )
        if (
            effective == "estimate"
            and verification_text is not None
            and not _names_token(verification_text, decision["layer"])
        ):
            findings.append(
                Finding(
                    "E9",
                    f"{decision['layer']}: the decision rests on an estimate and must be "
                    "listed in the verification section",
                )
            )
    for decision in decisions:
        for component_id in decision.get("benchmark", []):
            if verification_text is not None and not _names_token(verification_text, component_id):
                findings.append(
                    Finding(
                        "E9",
                        f"{decision['layer']}: the benchmark component '{component_id}' must "
                        "be named in the verification section",
                    )
                )
    if (
        tier
        and tier["requirements"]["kubernetes_risk_note"]
        and verification_text is not None
        and "org.kubernetes_experience" not in verification_text
    ):
        findings.append(
            Finding(
                "E9",
                "the verification section must list org.kubernetes_experience as a risk",
            )
        )

    # E10: the hardware covers the sizing.
    if blueprint["sizing"].get("fits") is not True:
        engine = decision_for(blueprint, "llm-serving")
        if engine is None or not has_override(engine):
            findings.append(
                Finding(
                    "E10",
                    "sizing.fits is not true; resolve it or record an override on the "
                    "llm-serving decision",
                )
            )

    # E11: required components are present.
    chosen = set(chosen_components(blueprint))
    existing_text = " ".join(
        name.lower() for decision in decisions for name in decision["existing"]
    )
    for component_id in sorted(chosen):
        entry = catalog.components.get(component_id)
        for required in (entry or {}).get("requires", []):
            if required not in chosen and required.lower() not in existing_text:
                findings.append(
                    Finding(
                        "E11",
                        f"'{component_id}' requires '{required}', which is neither chosen "
                        "nor named in existing",
                    )
                )

    # W1: stale catalog entries in use.
    limit = rules.value("lint.freshness_days")
    for component_id in sorted(chosen):
        entry = catalog.components.get(component_id)
        if entry and is_stale(entry.get("last_verified"), today, limit):
            findings.append(
                Finding(
                    "W1",
                    f"{component_id}: last verified {entry['last_verified']}, "
                    f"more than {limit} days ago",
                )
            )

    # W2: required answers given as "unknown".
    for question in QUESTIONS:
        if question.required and answers.get(question.id) == UNKNOWN:
            findings.append(Finding("W2", f"{question.id}: unknown; a default was used"))

    # W3: agent instruction block.
    if "agents" in unreadable:
        findings.append(Finding("W3", f"AGENTS.md cannot be read: {unreadable['agents']}"))
    elif (
        agents_text is None
        or AGENT_BLOCK_START not in agents_text
        or AGENT_BLOCK_END not in agents_text
    ):
        findings.append(Finding("W3", "the agent instruction block is missing from AGENTS.md"))

    # N1: every override in effect is reported.
    for decision in decisions:
        if has_override(decision):
            reason = decision["override"]["reason"].strip()
            findings.append(
                Finding("N1", f"{decision['layer']}: override in effect: {reason}")
            )

    return sorted(findings, key=_report_order)


def _read(path: Path) -> tuple[str | None, str | None]:
    """Return (text, None), (None, None) for a missing file or (None, reason) when unreadable."""
    try:
        return path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, None
    except UnicodeDecodeError:
        return None, "it is not valid UTF-8"
    except (OSError, ValueError) as error:
        return None, str(error)


def lint_project(
    blueprint_path: Path, catalog: Catalog, project_root: Path, today: date
) -> list[Finding]:
    """Read the project's files from disk and lint them."""
    blueprint_path = Path(blueprint_path)
    project_root = Path(project_root)
    blueprint = load_blueprint(blueprint_path)
    relative = blueprint.get("blueprint_path")
    unreadable: dict[str, str] = {}
    texts: dict[str, str | None] = {"blueprint": None}
    sources = {
        "manifest": blueprint_path.parent / MANIFEST_FILENAME,
        "agents": project_root / "AGENTS.md",
    }
    if isinstance(relative, str) and relative.strip():
        sources["blueprint"] = project_root / relative
    for name, source in sources.items():
        texts[name], reason = _read(source)
        if reason is not None:
            unreadable[name] = reason
    return _lint(
        blueprint=blueprint,
        catalog=catalog,
        blueprint_text=texts["blueprint"],
        manifest_text=texts["manifest"],
        agents_text=texts["agents"],
        today=today,
        unreadable=unreadable,
    )
