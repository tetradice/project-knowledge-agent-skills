# Deployment

Production deploys use a 10% canary for ten minutes, followed by 50% and 100%. Error rate above 1% or p95 latency above 800 ms aborts promotion.

Database migrations must remain backward compatible with the previous application version. Rollback deploys the previous image; destructive schema cleanup happens only in a later release.
