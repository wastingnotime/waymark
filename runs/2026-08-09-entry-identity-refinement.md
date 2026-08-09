# Waymark Entry Identity Refinement Check

Date: 2026-08-09

## Findings closed

- Replay advances the deterministic ID source beyond existing user, workspace,
  and entry identifiers.
- A conflicting same-ID retry emits a `conflicting_entry_retry` rejection
  observation instead of silently returning false.

## Evidence

```text
pytest -q
29 passed

SimulationRunner
run_id: waymark-first-slice
observations: 55
invariants:
  durable_entries_survive_payment_failure: passed
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

## Decision

Entry identity remains stable across replay and retried writes. Editing and
deletion remain outside the model.
