# Waymark Workspace Ownership Slice Build

Date: 2026-08-09

## Built behavior

- Entry commands accept an actor identity at the simulation boundary.
- The workspace owner can record while entitled.
- Another user is rejected with `unauthorized_user`.
- Unauthorized attempts do not append entries or domain facts.
- Runtime scenario exercises the private boundary and checks the invariant.

## Evidence

```text
pytest -q
30 passed

SimulationRunner
run_id: waymark-first-slice
observations: 61
invariants:
  private_workspace_is_owner_only: passed
  durable_entries_survive_payment_failure: passed
  event_replay_matches_live_state: passed
  entry_ids_are_unique: passed
```

## Handoff

Private ownership is explicit for the single-user model. Shared workspaces and
delegated access remain outside scope.
