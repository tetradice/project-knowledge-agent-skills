"""Asynchronous notification delivery."""

RETRY_SECONDS = (5, 30, 120)
DEAD_LETTER_AFTER = 3


def supported_channels() -> tuple[str, ...]:
    """Return channels owned by this module."""
    return ("email", "webhook")
