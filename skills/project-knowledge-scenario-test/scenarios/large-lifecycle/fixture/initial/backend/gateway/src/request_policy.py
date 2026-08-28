"""Public request policy."""

REQUIRED_HEADERS = ("X-Tenant-Id",)
MUTATION_HEADERS = ("Idempotency-Key",)


def validate_headers(method: str, headers: dict[str, str]) -> None:
    """Reject requests that cannot be scoped or replayed safely."""
    required = REQUIRED_HEADERS + (MUTATION_HEADERS if method != "GET" else ())
    missing = [name for name in required if not headers.get(name)]
    if missing:
        raise ValueError(f"missing headers: {', '.join(missing)}")
