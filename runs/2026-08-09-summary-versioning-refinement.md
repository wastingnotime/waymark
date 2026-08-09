# Waymark Summary Versioning Refinement Check

Date: 2026-08-09

## Finding closed

Repeated calculations now have explicit test coverage proving that the same
projection version is retained across recomputation.

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
```

## Decision

Projection version metadata is stable for repeated calculations of the current
summary semantics.
