# Waymark Operator Inspection Read Model Build

Date: 2026-08-09

## Built behavior

- Operator inspection includes access reason and lifecycle state.
- Entitlement period and cancellation boundaries are visible.
- Payment failure, expiry, entry count, and event count are included.
- Inspection remains read-only and is checked by a runtime invariant.

## Evidence

```text
pytest -q
29 passed

SimulationRunner
run_id: waymark-first-slice
observations: 56
invariants:
  durable_entries_survive_payment_failure: passed
  operator_inspection_is_complete: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
  duplicate_failure_is_observed: passed
  log_timestamps_are_distinct: passed
  entry_ids_are_unique: passed
```

## Handoff

The operator read model is sufficient for the current lifecycle. Dashboards,
roles, and approvals remain outside scope.
