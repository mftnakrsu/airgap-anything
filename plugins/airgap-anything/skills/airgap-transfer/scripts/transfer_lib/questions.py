"""The transfer questions (design spec section 8.3): which apply, and whether answers fit."""
from __future__ import annotations

import re
from pathlib import Path

from .constants import FILE_LIMIT_CHANNELS, FILESYSTEMS, MAX_SIZE_GB, MEDIUM_CHANNELS, size_bytes

QUESTION_IDS = (
    "bundle.path",
    "models",
    "medium.capacity_gb",
    "medium.filesystem",
    "channel.max_file_gb",
    "include_benchmark",
)
_REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*")
_COMMIT = re.compile(r"[0-9a-f]{40}")
NONE = "none"


def has_benchmark_rows(manifest: dict) -> bool:
    rows = list(manifest.get("images", [])) + list(manifest.get("packages", []))
    return any(isinstance(row, dict) and row.get("benchmark") for row in rows)


def needed_questions(channel: str, manifest: dict, answers: dict | None = None) -> list[str]:
    """The questions to ask for this channel and manifest, in order."""
    answers = answers or {}
    needed = ["bundle.path"]
    if manifest.get("models"):
        needed.append("models")
    if channel in MEDIUM_CHANNELS:
        needed.append("medium.capacity_gb")
        if not (channel == "other" and answers.get("medium.capacity_gb") == NONE):
            needed.append("medium.filesystem")
    if channel in FILE_LIMIT_CHANNELS:
        needed.append("channel.max_file_gb")
    if has_benchmark_rows(manifest):
        needed.append("include_benchmark")
    return needed


def inside_git_repository(path: Path) -> bool:
    """True when `path`, or the nearest folder above it that exists, is in a git work tree."""
    for folder in [Path(path), *Path(path).parents]:
        if (folder / ".git").exists():
            return True
    return False


def _bundle_path_problems(value, project_root: Path) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return ["must be a path"]
    path = Path(value)
    if not path.is_absolute():
        return ["must be an absolute path"]
    root = Path(project_root).resolve()
    resolved = path.resolve()
    if resolved == root or root in resolved.parents or inside_git_repository(resolved):
        return ["must be outside the git repository: a bundle can be hundreds of gigabytes"]
    if resolved.exists() and not resolved.is_dir():
        return ["exists and is not a folder"]
    return []


def _model_problems(value, manifest: dict) -> list[str]:
    names = [model.get("name") for model in manifest.get("models", []) if isinstance(model, dict)]
    if not isinstance(value, dict):
        return ["must be an object with one entry per model: " + ", ".join(names)]
    problems = []
    for name in names:
        source = value.get(name)
        where = f"'{name}'"
        if not isinstance(source, dict):
            problems.append(f"{where}: missing; give its source")
            continue
        if "allow_pickle" in source and not isinstance(source["allow_pickle"], bool):
            problems.append(f"{where}: allow_pickle must be true or false")
        if source.get("source") == "huggingface":
            if not isinstance(source.get("repo"), str) or not _REPO.fullmatch(source["repo"]):
                problems.append(f"{where}: repo must be <organization>/<name>")
            if not isinstance(source.get("revision"), str) or not _COMMIT.fullmatch(source["revision"]):
                problems.append(
                    f"{where}: revision must be the full 40-character commit hash; a tag or "
                    "branch cannot be recorded as what was fetched"
                )
        elif source.get("source") == "local":
            path = source.get("path")
            if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).is_dir():
                problems.append(f"{where}: path must be an absolute path to an existing folder")
        else:
            problems.append(f"{where}: source must be huggingface or local")
    for extra in sorted(set(value) - set(names)):
        problems.append(f"'{extra}': not a model of the manifest")
    return problems


def answer_problems(answers: dict, channel: str, manifest: dict, project_root: Path) -> list[str]:
    """'question id: reason' for every needed answer that is missing or does not fit."""
    problems = []
    for question_id in needed_questions(channel, manifest, answers):
        value = answers.get(question_id)
        if value is None:
            if question_id != "include_benchmark":
                problems.append(f"{question_id}: missing")
            continue
        if question_id == "bundle.path":
            reasons = _bundle_path_problems(value, project_root)
        elif question_id == "models":
            reasons = _model_problems(value, manifest)
        elif question_id == "medium.capacity_gb":
            allowed_none = channel == "other" and value == NONE
            reasons = [] if allowed_none or size_bytes(value) is not None else [
                f"must be a number of gigabytes above 0 and at most {MAX_SIZE_GB}" + (", or 'none'" if channel == "other" else "")
            ]
        elif question_id == "medium.filesystem":
            reasons = [] if value in FILESYSTEMS else ["must be one of " + ", ".join(FILESYSTEMS)]
        elif question_id == "channel.max_file_gb":
            reasons = [] if value == NONE or size_bytes(value) is not None else [
                f"must be a number of gigabytes above 0 and at most {MAX_SIZE_GB}, or 'none'"
            ]
        else:
            reasons = [] if isinstance(value, bool) else ["must be true or false"]
        problems += [f"{question_id}: {reason}" for reason in reasons]
    return problems


def include_benchmark(answers: dict) -> bool:
    return answers.get("include_benchmark", True) is not False
