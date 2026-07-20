"""
Authentication: password hashing plus the Sign Up / Sign In use cases.

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib ``hashlib``) and a random
per-user salt — no extra dependency, and well beyond what a study workspace
needs. Raw passwords and hashes never leave this module; callers only ever
see the public user dict returned by ``sign_up``/``sign_in``.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from typing import Any, Dict, Optional, Tuple

from database.db import Database

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ITERATIONS = 260_000
_MIN_PASSWORD_LENGTH = 8


def hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    """Return ``(hash_hex, salt_hex)``, generating a salt if one isn't given."""
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return digest.hex(), salt.hex()


def verify_password(password: str, password_hash: str, password_salt: str) -> bool:
    candidate, _ = hash_password(password, password_salt)
    return hmac.compare_digest(candidate, password_hash)


def _public_user(row: Dict[str, Any]) -> Dict[str, Any]:
    """Strip credential columns before a user record enters session state."""
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "avatar": row["avatar"],
        "semester": row["semester"],
    }


def sign_up(
    db: Database,
    name: str,
    email: str,
    password: str,
    confirm_password: str,
    semester: str = "Semester 5",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Create a new account. Returns ``(user, None)`` on success, else ``(None, error)``."""
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if not clean_name:
        return None, "Enter your name."
    if not _EMAIL_RE.match(clean_email):
        return None, "Enter a valid email address."
    if len(password) < _MIN_PASSWORD_LENGTH:
        return None, f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
    if password != confirm_password:
        return None, "Passwords do not match."
    if db.get_user_by_email(clean_email):
        return None, "An account with this email already exists. Try signing in."

    password_hash, password_salt = hash_password(password)
    row = db.create_user(clean_name, clean_email, password_hash, password_salt, semester)
    return _public_user(row), None


def sign_in(
    db: Database, email: str, password: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Verify credentials. Returns ``(user, None)`` on success, else ``(None, error)``."""
    clean_email = email.strip().lower()
    if not clean_email or not password:
        return None, "Enter your email and password."

    row = db.get_user_by_email(clean_email)
    if row is None or not verify_password(password, row["password_hash"], row["password_salt"]):
        return None, "Incorrect email or password."
    return _public_user(row), None
