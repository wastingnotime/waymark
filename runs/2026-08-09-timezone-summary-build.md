# Waymark Timezone Summary Slice Build

Date: 2026-08-09

## Built behavior

- Daily summaries accept an absolute instant range and IANA timezone name.
- Recorded instants are grouped by local calendar date in the requested zone.
- Projection observations include the timezone used.
- Unknown timezone names fail explicitly; durable entry facts remain unchanged.

## Evidence

```text
pytest -q
16 passed

SimulationRunner
run_id: waymark-first-slice
observations: 35
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
```

## Handoff

The timezone summary slice is built. Refinement should next compare the
projection's explicit instant-range semantics with the intended user workflow.
