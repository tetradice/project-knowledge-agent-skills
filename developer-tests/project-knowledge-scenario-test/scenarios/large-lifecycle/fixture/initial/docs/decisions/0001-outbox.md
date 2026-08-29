# ADR 0001: Transactional outbox

Status: accepted

Order events are written to an outbox table in the same PostgreSQL transaction. Direct broker publication from request handlers was rejected because it can diverge from committed state.
