# Waymark Account Bootstrap Slice Build

Date: 2026-08-09

## Built behavior

- First bootstrap creates one account and one private workspace.
- Duplicate bootstrap emits `duplicate_account_creation_ignored`.
- Duplicate requests do not append account or workspace facts.
- Runtime scenario exercises and verifies the cardinality boundary.

## Evidence

```text
pytest -q
31 passed

SimulationRunner
run_id: waymark-first-slice
observations: 64
invariants:
  account_bootstrap_is_unique: passed
  private_workspace_is_owner_only: passed
  event_replay_matches_live_state: passed
  entry_ids_are_unique: passed
```

## Handoff

The first-version account/workspace cardinality is enforced. Account deletion,
merging, and multiple users remain outside scope.
