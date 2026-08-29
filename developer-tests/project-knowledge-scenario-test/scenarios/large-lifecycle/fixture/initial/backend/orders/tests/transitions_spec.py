from orders.src.models import TERMINAL_STATES


def test_terminal_states_are_closed() -> None:
    assert TERMINAL_STATES == ("shipped", "cancelled")
