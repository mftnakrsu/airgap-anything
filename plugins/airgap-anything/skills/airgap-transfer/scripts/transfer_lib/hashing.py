"""SHA-256 of files and of the parts a split file is cut into, in one read."""
from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK = 1024 * 1024


def hash_file(path: Path, part_size: int | None = None) -> tuple[str, list[str]]:
    """(SHA-256 of the whole file, SHA-256 of each part of `part_size` bytes).

    The list of parts is empty when `part_size` is None or the file is not larger.
    """
    whole = hashlib.sha256()
    parts: list[str] = []
    size = Path(path).stat().st_size
    split = part_size is not None and size > part_size
    part = hashlib.sha256()
    left = part_size if split else None
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            whole.update(chunk)
            while split and chunk:
                take = chunk[:left]
                part.update(take)
                chunk = chunk[len(take):]
                left -= len(take)
                if left == 0:
                    parts.append(part.hexdigest())
                    part, left = hashlib.sha256(), part_size
    if split and left != part_size:
        parts.append(part.hexdigest())
    return whole.hexdigest(), parts


def part_count(size: int, part_size: int | None) -> int:
    """How many parts a file of `size` bytes is cut into; 0 when it is not split."""
    if part_size is None or size <= part_size:
        return 0
    return -(-size // part_size)
