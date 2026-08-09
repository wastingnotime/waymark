# Waymark Expiry Idempotency Refinement Check

Date: 2026-08-09

## Finding closed

The expiry invariant now verifies both one expiry fact and continued restricted
access after duplicate period-end processing.

## Evidence

```text
pytest -q
36 passed

SimulationRunner
run_id: waymark-first-slice
observations: 81
invariant:
  expiry_job_is_unique: passed
```

## Decision

Repeated expiry processing is non-mutating and preserves restricted access.
