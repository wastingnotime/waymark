# Waymark Log Timestamp Slice Build

Date: 2026-08-09

## Built behavior

- Runtime records a log for an earlier activity time.
- Waymark preserves the later controlled recording time separately.
- Replay and the runtime invariant preserve the distinction.
- Daily summaries continue grouping by recording time.

## Evidence

```text
pytest -q
26 passed

SimulationRunner
run_id: waymark-first-slice
observations: 49
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
  expired_interval_remains_closed: passed
  event_replay_matches_live_state: passed
  duplicate_failure_is_observed: passed
  log_timestamps_are_distinct: passed
```

## Handoff

Activity-time analytics remain intentionally outside the current slice.
