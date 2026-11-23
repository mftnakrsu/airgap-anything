"""File size limits, splitting and the volume plan (design spec section 8.5)."""
from __future__ import annotations

from .constants import FAT32_MAX_FILE_BYTES, FILE_LIMIT_CHANNELS, MEDIUM_CHANNELS, PART_SUFFIX, VOLUME_RESERVE, size_bytes
from .hashing import part_count

MAX_PARTS = 999  # PART_SUFFIX has three digits


def max_file_bytes(channel: str, answers: dict) -> int | None:
    """The largest single file the channel takes; None when it has no limit."""
    if channel in MEDIUM_CHANNELS and answers.get("medium.filesystem") == "fat32":
        return FAT32_MAX_FILE_BYTES
    if channel in FILE_LIMIT_CHANNELS:
        return size_bytes(answers.get("channel.max_file_gb"))
    return None


def volume_capacity(channel: str, answers: dict) -> int | None:
    """Bytes of data one volume holds: the medium minus the reserve; None for one volume."""
    capacity = size_bytes(answers.get("medium.capacity_gb")) if channel in MEDIUM_CHANNELS else None
    if capacity is None:
        return None
    return capacity * (100 - round(VOLUME_RESERVE * 100)) // 100


def part_size(channel: str, answers: dict) -> int | None:
    """Files larger than this are split; None when nothing needs splitting."""
    limits = [value for value in (max_file_bytes(channel, answers), volume_capacity(channel, answers)) if value]
    return min(limits) if limits else None


def part_name(path: str, index: int) -> str:
    """The name of part `index` (from 1) of the file at `path`."""
    return path + PART_SUFFIX.format(index)


def units_of(files: list[dict], size_limit: int | None) -> list[dict]:
    """What goes onto volumes: whole files, and the parts of files larger than `size_limit`.

    `files` holds {path, size, parts}, where `parts` are the SHA-256 of each part.
    Each unit is {path, size, sha256, of}: `of` is the original path for a part, else None.
    Raises ValueError when a file would need more than MAX_PARTS parts.
    """
    units = []
    for entry in files:
        count = part_count(entry["size"], size_limit)
        if count > MAX_PARTS:
            raise ValueError(f"{entry['path']}: would be cut into {count} parts; at most {MAX_PARTS} are possible")
        if not count:
            units.append({"path": entry["path"], "size": entry["size"], "sha256": entry["sha256"], "of": None})
            continue
        for index in range(1, count + 1):
            size = min(size_limit, entry["size"] - (index - 1) * size_limit)
            units.append(
                {"path": part_name(entry["path"], index), "size": size, "sha256": entry["parts"][index - 1], "of": entry["path"]}
            )
    return units


def assign_volumes(units: list[dict], capacity: int | None) -> list[list[dict]]:
    """First fit, largest first. One volume when `capacity` is None."""
    ordered = sorted(units, key=lambda unit: (-unit["size"], unit["path"]))
    if capacity is None:
        return [ordered]
    volumes: list[list[dict]] = []
    free: list[int] = []
    for unit in ordered:
        for index, room in enumerate(free):
            if unit["size"] <= room:
                volumes[index].append(unit)
                free[index] -= unit["size"]
                break
        else:
            volumes.append([unit])
            free.append(capacity - unit["size"])
    return volumes
