from gateway.src.request_policy import validate_headers


def test_get_requires_tenant() -> None:
    validate_headers("GET", {"X-Tenant-Id": "tenant-a"})
