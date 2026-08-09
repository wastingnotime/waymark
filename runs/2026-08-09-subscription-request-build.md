# Waymark Subscription Request Slice Build

Date: 2026-08-09

## Built behavior

- Account creation is followed by an explicit subscription request.
- Duplicate same-identity requests emit a notice without duplicate facts.
- Subscription identity survives replay.
- Runtime scenario exercises the request before payment activation.

## Evidence

```text
pytest -q
32 passed

SimulationRunner
run_id: waymark-first-slice
observations: 69
invariants:
  subscription_request_is_unique: passed
  account_bootstrap_is_unique: passed
  event_replay_matches_live_state: passed
  private_workspace_is_owner_only: passed
```

## Handoff

The commercial flow now includes an explicit idempotent subscription request.
Multiple plans and subscription changes remain outside scope.
