# Waymark Payment Idempotency Slice Build

Date: 2026-08-09

## Built behavior

- Payment failure facts carry an optional provider correlation ID.
- Repeated delivery of the same failure ID is ignored after an informational
  observation.
- Processed payment IDs are included in replayed state.
- The runtime scenario exercises duplicate failure delivery.

## Evidence

```text
pytest -q
23 passed

SimulationRunner
run_id: waymark-first-slice
observations: 47
duplicate observation:
  duplicate_payment_failure_ignored
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
```

## Handoff

Payment delivery idempotency is built for failure notifications. Different
payment ordering and provider-specific retry schedules remain out of scope.
