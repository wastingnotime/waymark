# Waymark Subscription Ownership Slice Build

Date: 2026-08-09

## Built behavior

- `SubscriptionRequested` facts carry subscription, user, and payer identity.
- The first-version payer/user relationship remains explicit.
- Replay and runtime invariants preserve the ownership linkage.

## Evidence

```text
pytest -q
39 passed

SimulationRunner
run_id: waymark-first-slice
observations: 86
invariants:
  subscription_request_is_unique: passed
  subscription_ownership_is_explicit: passed
  payer_identity_is_explicit: passed
  event_replay_matches_live_state: passed
```

## Handoff

Subscription ownership is now durable and inspectable. Delegated and
organization-funded billing remain outside scope.
