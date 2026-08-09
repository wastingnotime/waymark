# Waymark Expiry Idempotency Slice Build

Date: 2026-08-09

## Built behavior

- First period-end processing records one `EntitlementExpired` fact.
- Repeated expiry processing emits `duplicate_expiry_ignored`.
- Duplicate jobs append no event and leave access restricted.
- Runtime scenario exercises duplicate period-end processing.

## Evidence

```text
pytest -q
36 passed

SimulationRunner
run_id: waymark-first-slice
observations: 81
invariants:
  expiry_job_is_unique: passed
  expired_interval_remains_closed: passed
  renewal_opens_new_period: passed
  event_replay_matches_live_state: passed
```

## Handoff

Expiry is safe to retry for the current entitlement interval. Grace periods and
manual date overrides remain outside scope.
