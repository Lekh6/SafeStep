from __future__ import annotations

import os


def resolve_login_input(value: str) -> str:
    """Resolve admin login input.

    If a user types an environment variable key (e.g. SAFESTEP_ADMIN_USER),
    resolve it to that variable's value. Otherwise return input as-is.
    """

    normalized = value.strip()
    if normalized in os.environ:
        return os.environ[normalized]
    return normalized


def authenticate_admin(
    username_input: str,
    password_input: str,
    expected_username: str,
    expected_password: str,
) -> bool:
    return (
        resolve_login_input(username_input) == expected_username
        and resolve_login_input(password_input) == expected_password
    )
