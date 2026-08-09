# Waymark Timezone Summary Refinement Check

Date: 2026-08-09

## Finding closed

The runtime scenario previously exercised only the UTC summary default. It now
requests `America/Sao_Paulo`, and an invariant verifies that the projection
observation preserves the requested timezone. A unit check also confirms that
projection calculation does not append domain events.

## Evidence

```text
pytest -q
17 passed

SimulationRunner
run_id: waymark-first-slice
observations: 36
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
```

## Decision

Timezone-aware summaries are coherent for the current slice. User preference
persistence and timezone migration remain discovery work, not model release
scope.
