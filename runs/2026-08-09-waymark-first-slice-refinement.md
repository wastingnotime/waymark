# Waymark First Slice Refinement Check

Date: 2026-08-09

## Scope

Compared the subscription-backed workspace slice contract with the shared
deterministic simulation and its WNT MRL Runtime adapter.

## Changes made

- Added a recomputable daily-entry summary projection.
- Added runtime evidence for the summary projection.
- Added an explicit cancellation-boundary invariant: cancellation preserves
  access before the paid period ends and expiry restricts it at the boundary.
- Added unit coverage for summary reproducibility and cancellation behavior.

## Evidence

```text
pytest -q
10 passed

SimulationRunner
run_id: waymark-first-slice
observations: 31
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
```

## Decision

The slice is coherent enough to continue refining in the same simulation
environment. It is not a model release: payment-provider behavior, operator
inspection, timezone semantics, and grace-period policy remain open discovery
work.
