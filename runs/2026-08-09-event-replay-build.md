# Waymark Event Replay Slice Build

Date: 2026-08-09

## Built behavior

- Typed append-only facts can rehydrate a fresh simulation environment.
- Replay preserves identities, entries, timestamps, payment state, expiry, and
  entitlement boundaries.
- Replay does not emit or append new facts.
- The runtime scenario checks replay equivalence continuously through the full
  lifecycle.

## Evidence

```text
pytest -q
21 passed

SimulationRunner
run_id: waymark-first-slice
observations: 45
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
```

## Handoff

The simulation now has a replayable event history suitable for the next
refinement check. Cross-version migrations, serialization, and snapshots remain
outside this slice.
