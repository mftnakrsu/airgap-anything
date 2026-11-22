"""The evidence policy shared by rules, GPU rows and component entries."""
from __future__ import annotations

from .constants import EVIDENCE_LEVELS


def _has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evidence_problems(level, sources, verified_by, notes) -> list[str]:
    """Problems with one evidence record; empty when it follows the policy."""
    if level not in EVIDENCE_LEVELS:
        return ["evidence level must be one of " + ", ".join(EVIDENCE_LEVELS)]
    if level == "docs":
        urls_ok = (
            isinstance(sources, list)
            and bool(sources)
            and all(
                isinstance(url, str) and url.startswith(("http://", "https://"))
                for url in sources
            )
        )
        return [] if urls_ok else ["evidence 'docs' needs at least one URL in sources"]
    if level == "field":
        problems = []
        if not _has_text(verified_by):
            problems.append("evidence 'field' needs verified_by")
        if not _has_text(notes):
            problems.append("evidence 'field' needs notes with hardware and context")
        return problems
    if not _has_text(notes):
        return ["evidence 'estimate' needs notes stating the basis"]
    return []
