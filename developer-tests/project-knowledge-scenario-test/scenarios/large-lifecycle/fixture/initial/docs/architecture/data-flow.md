# Data flow

1. Gateway validates tenant and idempotency headers.
2. Orders persists a draft and outbox event.
3. Inventory reserves stock using tenant plus SKU keys.
4. Orders confirms or rejects the draft.
5. Notifications delivers committed events asynchronously.

No synchronous notification call is allowed in the order transaction.
