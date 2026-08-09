# Waymark First Slice Refinement Check 2

Date: 2026-08-09

## Findings closed

- Entry commands now reject empty bodies and emit a semantic rejection reason.
- Cancellation preserves its effective paid-period boundary in state, facts,
  and runtime observations.

## Evidence

```text
pytest -q
12 passed

SimulationRunner
run_id: waymark-first-slice
observations: 31
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
```

## Decision

The first slice remains coherent and deterministic. Continue discovery before
model EGD; operator inspection, timezone behavior, grace-period policy, and
provider lifecycle detail remain outside this refinement.
