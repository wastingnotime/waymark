# Waymark Subscription Status Slice Build

Date: 2026-08-09

## Built behavior

- Derived subscription statuses cover request, active, past-due, cancellation,
  expiry, and no-subscription states.
- Operator inspection includes status and access explanation.
- Status is calculated at an instant and is not stored as an independent flag.

## Evidence

```text
pytest -q
40 passed

SimulationRunner
run_id: waymark-first-slice
observations: 86
operator inspection:
  subscription_status: past_due
invariants:
  operator_inspection_is_complete: passed
  event_replay_matches_live_state: passed
```

## Handoff

Commercial status is now explainable from existing facts. Provider-specific
statuses and grace periods remain outside scope.
