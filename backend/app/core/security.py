from __future__ import annotations

import hashlib
import hmac


def hash_token(token: str) -> str:
    """Utility kept for future non-auth token workflows, not used for route auth."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_admin_token(password: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_admin_password(candidate: str, expected: str) -> bool:
    return hmac.compare_digest(candidate, expected)


def verify_admin_token(token: str, password: str, secret: str) -> bool:
    expected = create_admin_token(password, secret)
    return hmac.compare_digest(token, expected)
