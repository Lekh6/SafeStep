import os

from safestep.admin_auth import authenticate_admin, resolve_login_input


def test_resolve_login_input_returns_plain_value() -> None:
    assert resolve_login_input("admin") == "admin"


def test_resolve_login_input_can_resolve_env_var_name(monkeypatch) -> None:
    monkeypatch.setenv("SAFESTEP_ADMIN_USER", "real-admin")
    assert resolve_login_input("SAFESTEP_ADMIN_USER") == "real-admin"


def test_authenticate_admin_accepts_direct_credentials() -> None:
    assert authenticate_admin("admin", "admin123", "admin", "admin123") is True


def test_authenticate_admin_accepts_env_keys_when_set(monkeypatch) -> None:
    monkeypatch.setenv("SAFESTEP_ADMIN_USER", "admin")
    monkeypatch.setenv("SAFESTEP_ADMIN_PASSWORD", "admin123")
    assert authenticate_admin(
        "SAFESTEP_ADMIN_USER",
        "SAFESTEP_ADMIN_PASSWORD",
        "admin",
        "admin123",
    ) is True


def test_authenticate_admin_rejects_wrong_credentials() -> None:
    assert authenticate_admin("wrong", "wrong", "admin", "admin123") is False
