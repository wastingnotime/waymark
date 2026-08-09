# Waymark Billing Period Overlap Slice Build

Date: 2026-08-09

## Built behavior

- Activation periods must have positive duration.
- Overlapping activation against the current entitlement is rejected.
- Renewal after expiry remains the explicit new-period path.

## Evidence

```text
pytest -q
38 passed

SimulationRunner
run_id: waymark-first-slice
observations: 84
invariants:
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
```

## Handoff

Entitlement intervals cannot silently overlap. Proration and plan changes remain
outside scope.
