"""Inventory reservation policy."""

RESERVATION_TTL_SECONDS = 900


def reservation_key(tenant_id: str, sku: str) -> str:
    """Build the tenant-scoped reservation key."""
    return f"{tenant_id}:{sku}"
