# Waymark Summary Versioning Slice Build

Date: 2026-08-09

## Built behavior

- Daily summary observations include `daily-entry-counts-v1`.
- Version metadata identifies projection semantics without entering durable
  entry facts.
- Runtime and unit checks verify the version is present and stable.

## Evidence

```text
pytest -q
29 passed

SimulationRunner
run_id: waymark-first-slice
observations: 57
invariants:
  summary_timezone_is_recorded: passed
  summary_version_is_recorded: passed
  event_replay_matches_live_state: passed
  entry_ids_are_unique: passed
```

## Handoff

Derived summary semantics are now explicitly identifiable for future
recomputation and comparison.
