# Waymark Entry Identity Slice Build

Date: 2026-08-09

## Built behavior

- Notes and logs receive immutable entry IDs.
- Same-ID retries with the same content do not append duplicate facts.
- Same-ID conflicting content is rejected.
- IDs and entry data survive event replay.
- The runtime scenario exercises a repeated note write and checks ID
  uniqueness.

## Evidence

```text
pytest -q
28 passed

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

## Handoff

Recording is now identity-safe for retried writes. Editing and deletion remain
outside the current model.
