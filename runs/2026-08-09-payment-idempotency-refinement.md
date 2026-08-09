# Waymark Payment Idempotency Refinement Check

Date: 2026-08-09

## Findings closed

- The runtime now asserts that duplicate failure delivery produced an
  informational observation.
- The fake provider rejects conflicting outcomes for the same payment ID,
  preventing a success/failure overwrite.

## Evidence

```text
pytest -q
24 passed

SimulationRunner
run_id: waymark-first-slice
observations: 48
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
  duplicate_failure_is_observed: passed
```

## Decision

Payment failure delivery is deterministic and auditable for the current slice.
Provider ordering and refund behavior remain outside scope.
