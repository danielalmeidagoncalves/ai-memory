from __future__ import annotations

import re
import unicodedata
import uuid


def generate_slug(content: str, max_length: int = 40) -> str:
    text = content.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = text.split()
    if not words:
        return uuid.uuid4().hex[:8]

    meaningful = [w for w in words if len(w) > 2][:4]
    if not meaningful:
        meaningful = words[:4]

    slug = "_".join(meaningful)
    slug = slug[:max_length]
    slug = slug.rstrip("_")
    return slug


def deduplicate_slug(slug: str, existing_ids: set[str]) -> str:
    if slug not in existing_ids:
        return slug
    counter = 2
    while f"{slug}_{counter}" in existing_ids:
        counter += 1
    return f"{slug}_{counter}"


def generate_id(content: str, existing_ids: set[str]) -> str:
    slug = generate_slug(content)
    if len(slug) < 3:
        return uuid.uuid4().hex[:8]
    return deduplicate_slug(slug, existing_ids)
