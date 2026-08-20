import hashlib
import os
import time


MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 30

_attempts = 0
_locked_until = 0.0


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(
        pin.strip().encode("utf-8")
    ).hexdigest()


def verify_shutdown_pin(pin: str) -> bool:
    global _attempts
    global _locked_until

    now = time.monotonic()

    if now < _locked_until:
        return False

    expected = os.getenv(
        "SUNDAY_SHUTDOWN_PIN_HASH",
        "",
    ).strip()

    if not expected:
        return False

    if _hash_pin(pin) == expected:
        _attempts = 0
        return True

    _attempts += 1

    if _attempts >= MAX_ATTEMPTS:
        _attempts = 0
        _locked_until = (
            now + LOCKOUT_SECONDS
        )

    return False


