from __future__ import annotations

import hashlib


def hash_token(token: str) -> str:
    """Utility kept for future non-auth token workflows, not used for route auth."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

