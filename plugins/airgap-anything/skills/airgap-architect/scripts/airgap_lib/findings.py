"""Lint findings and how they are printed."""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

# Report order. Only errors make lint fail.
SEVERITIES = ("error", "warning", "note")


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    @property
    def severity(self) -> str:
        return {"W": "warning", "N": "note"}.get(self.code[:1], "error")


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


def format_text(findings: list[Finding]) -> str:
    if not findings:
        return "OK: no findings"
    lines = [f"{f.code} {f.severity}: {f.message}" for f in findings]
    counts = {
        severity: sum(1 for f in findings if f.severity == severity)
        for severity in SEVERITIES
    }
    lines.append(
        f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)"
    )
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    return json.dumps(
        [
            {"code": f.code, "severity": f.severity, "message": f.message}
            for f in findings
        ],
        indent=2,
    )
