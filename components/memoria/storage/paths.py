from __future__ import annotations

from pathlib import Path


def resolve_storage_path(storage_path: str | None = None) -> Path:
    if storage_path is not None:
        return Path(storage_path)
    return Path.home() / ".memoria"


def daily_dir(storage_path: Path) -> Path:
    p = storage_path / "daily"
    p.mkdir(parents=True, exist_ok=True)
    return p


def archived_dir(storage_path: Path) -> Path:
    p = storage_path / "archived"
    p.mkdir(parents=True, exist_ok=True)
    return p
