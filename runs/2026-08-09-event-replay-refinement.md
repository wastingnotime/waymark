# Waymark Event Replay Refinement Check

Date: 2026-08-09

## Finding closed

Replay previously restored period and access state but did not explicitly clear
the prior cancellation schedule when a new entitlement was granted. Rehydration
now resets that old schedule, and the runtime equivalence invariant compares
both cancellation fields.

## Evidence

```text
pytest -q
22 passed

SimulationRunner
run_id: waymark-first-slice
observations: 45
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
```

## Decision

Replay semantics are aligned with the current lifecycle model. Cross-version
event migration remains outside this slice.
