# Renewal After Expiry

## Selection

- Runtime target: the existing deterministic subscription-backed workspace.
- Architecture: a new bounded entitlement period in the same event history.

## Contract

A successful payment after expiry opens a new entitlement beginning at the new
paid period. It does not reopen or mutate the expired interval. Access is
restricted at the old exclusive boundary and allowed inside the new period.

## Deterministic test plan

- access is restricted at the old period boundary;
- renewal creates a second entitlement fact with a new start;
- the old interval remains expired;
- a post-renewal entry is accepted;
- renewal is rejected while the current period is still active.

## Done criteria

The runtime scenario demonstrates expiry followed by a new paid period, with an
invariant proving the new start boundary.

## Out of scope

Proration, partial periods, plan changes, credits, retries across providers,
and grace periods.
