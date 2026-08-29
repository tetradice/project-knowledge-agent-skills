"""Order persistence contract."""

TABLE = "orders"
UNIQUE_KEYS = ("tenant_id", "idempotency_key")
