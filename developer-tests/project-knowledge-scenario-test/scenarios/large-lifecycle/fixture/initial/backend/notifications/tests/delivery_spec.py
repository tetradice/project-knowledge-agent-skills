from notifications.src.delivery import supported_channels


def test_channels() -> None:
    assert supported_channels() == ("email", "webhook")
