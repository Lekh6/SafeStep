from __future__ import annotations


class SafetySupervisor:
    """Tracks persistent errors and requests fail-safe mode."""

    def __init__(self, max_persistent_errors: int = 3) -> None:
        self.max_persistent_errors = max_persistent_errors
        self._error_count = 0

    def report_error(self) -> None:
        self._error_count += 1

    def clear_error(self) -> None:
        self._error_count = 0

    def should_enter_failsafe(self) -> bool:
        return self._error_count >= self.max_persistent_errors
