# Waymark Renewal After Expiry Refinement Check

Date: 2026-08-09

## Findings closed

- Added a runtime invariant proving the expired interval remains closed after a
  later entitlement is granted.
- Renewal now rejects zero-length and reverse-ordered periods.

## Evidence

```text
pytest -q
20 passed

SimulationRunner
run_id: waymark-first-slice
observations: 44
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
```

## Decision

Renewal semantics are sufficiently explicit for continued discovery. Proration,
plan changes, and grace periods remain outside the model.
