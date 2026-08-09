# Waymark Pre-Entitlement Access Slice Build

Date: 2026-08-09

## Built behavior

- Account creation without an entitlement yields restricted access.
- The access decision reason is `no_entitlement`.
- Runtime scenario observes the restricted state before subscription activation.
- Direct tests cover the same boundary.

## Evidence

```text
pytest -q
37 passed

SimulationRunner
run_id: waymark-first-slice
observations: 84
invariants:
  pre_entitlement_is_restricted: passed
  subscription_request_is_unique: passed
  account_bootstrap_is_unique: passed
  event_replay_matches_live_state: passed
```

## Handoff

Access now has explicit pre-entitlement behavior. Trials, previews, and free
plans remain outside scope.
