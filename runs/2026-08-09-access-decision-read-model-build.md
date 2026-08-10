# Waymark Access Decision Read Model Build

Date: 2026-08-09

## Built

Access checks now emit an explainable decision containing the boolean outcome,
restriction reason, and derived subscription status. The existing boolean API
delegates to the same read model.

## Evidence

```text
pytest -q
41 passed

SimulationRunner
run_id: waymark-first-slice
observations: 86
invariants:
  operator_inspection_is_complete: passed
  cancellation_respects_paid_boundary: passed
  expired_interval_remains_closed: passed
```

## Decision

Access projections can explain a denial without reimplementing subscription
status derivation.
