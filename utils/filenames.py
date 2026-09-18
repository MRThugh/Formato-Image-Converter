import os
from pathlib import Path
from typing import Set, Optional


def get_unique_output_path(
    output_dir: Path,
    stem: str,
    extension: str,
    prefix: str = "",
    suffix: str = "",
    index_hint: Optional[int] = None,
    reserved_paths: Optional[Set[Path]] = None
) -> Path:
    """
    Generates a unique, non-colliding file path in output_dir.
    Handles existing disk files and tracks reserved paths for concurrent batch execution.
    Preserves Unicode, Persian, Arabic, and special characters.
    """
    ext = extension.lstrip(".").lower()
    if ext == "jpeg":
        ext = "jpg"

    pref_part = f"{prefix}_" if prefix else ""
    suff_part = f"_{suffix}" if suffix else ""

    if index_hint is not None and (prefix or suffix):
        base_name = f"{pref_part}{stem}_{index_hint:03d}{suff_part}"
    else:
        base_name = f"{pref_part}{stem}{suff_part}"

    candidate = output_dir / f"{base_name}.{ext}"

    if reserved_paths is None:
        reserved_paths = set()

    counter = 1
    while candidate.exists() or candidate in reserved_paths:
        candidate = output_dir / f"{base_name}_{counter}.{ext}"
        counter += 1

    reserved_paths.add(candidate)
    return candidate


def get_temp_output_path(target_path: Path) -> Path:
    """
    Returns a temporary file path adjacent to the target path for atomic writes.
    """
    return target_path.parent / f".{target_path.name}.{os.getpid()}.tmp"
