from inventory.src.reservations import reservation_key


def test_key_is_tenant_scoped() -> None:
    assert reservation_key("a", "sku-1") == "a:sku-1"
