"""Order aggregate states and transitions."""

ORDER_STATES = ("draft", "confirmed", "allocated", "shipped", "cancelled")
TERMINAL_STATES = ("shipped", "cancelled")
