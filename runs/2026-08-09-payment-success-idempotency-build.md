# Waymark Payment Success Idempotency Slice Build

Date: 2026-08-09

## Built behavior

- Activation and renewal success facts carry payment correlation IDs.
- Duplicate success delivery emits `duplicate_payment_success_ignored`.
- Duplicate success delivery does not append payment or entitlement facts.
- Replay preserves processed success IDs.
- Runtime exercises duplicate activation success.

## Evidence

```text
pytest -q
33 passed

SimulationRunner
run_id: waymark-first-slice
observations: 72
invariants:
  duplicate_success_is_observed: passed
  duplicate_failure_is_observed: passed
  subscription_request_is_unique: passed
  event_replay_matches_live_state: passed
```

## Handoff

Both payment outcomes are now idempotent at the simulation boundary. Refunds and
reconciliation remain outside scope.
