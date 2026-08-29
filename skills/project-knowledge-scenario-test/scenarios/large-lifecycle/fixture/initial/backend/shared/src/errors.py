"""Cross-service error envelope."""


def envelope(code: str, message: str, trace_id: str) -> dict[str, str]:
    """Return the public error shape without internal stack data."""
    return {"code": code, "message": message, "trace_id": trace_id}
