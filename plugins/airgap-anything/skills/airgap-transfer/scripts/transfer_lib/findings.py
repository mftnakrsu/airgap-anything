"""Bundle check findings: B codes are errors, BW codes are warnings."""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    @property
    def severity(self) -> str:
        return "warning" if self.code.startswith("BW") else "error"


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


def format_text(findings: list[Finding]) -> str:
    if not findings:
        return "OK: no findings"
    lines = [f"{f.code} {f.severity}: {f.message}" for f in findings]
    errors = sum(1 for f in findings if f.severity == "error")
    lines.append(f"{errors} error(s), {len(findings) - errors} warning(s)")
    return "\n".join(lines)


def format_json(findings: list[Finding]) -> str:
    return json.dumps(
        [{"code": f.code, "severity": f.severity, "message": f.message} for f in findings],
        indent=2,
    )
