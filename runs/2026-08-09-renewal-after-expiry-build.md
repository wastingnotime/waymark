# Waymark Renewal After Expiry Slice Build

Date: 2026-08-09

## Built behavior

- Expiry restricts access at the old entitlement boundary.
- A successful renewal after expiry creates a new bounded entitlement.
- The old interval remains expired and is never reopened.
- New entries are accepted inside the renewed period.
- Renewal while an entitlement is active is rejected.

## Evidence

```text
pytest -q
19 passed

SimulationRunner
run_id: waymark-first-slice
observations: 43
invariants:
  durable_entries_survive_payment_failure: passed
  cancellation_respects_paid_boundary: passed
  operator_intervention_is_audited: passed
  summary_timezone_is_recorded: passed
  renewal_opens_new_period: passed
```

## Handoff

The core first-slice lifecycle is now represented through activation, failure,
recovery, cancellation, expiry, intervention, summary projection, and renewal.
Grace periods, provider-specific retries, and plan changes remain out of scope.
