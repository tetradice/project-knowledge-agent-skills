"""Order application service."""


def confirm(order: dict[str, object]) -> dict[str, object]:
    """Confirm a draft after inventory accepts a reservation."""
    if order["state"] != "draft":
        raise ValueError("only draft orders can be confirmed")
    return {**order, "state": "confirmed"}
