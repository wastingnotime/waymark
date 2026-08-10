# Cancellation Access Boundary

## Selection

- Runtime target: the shared subscription-backed workspace environment.
- Architecture: a scheduled cancellation boundary interpreted by the access
  read model; no mutable entitlement flag is introduced.

## Contract

Cancellation defaults to the paid period's exclusive end. The simulation may
also represent an explicit boundary inside the current paid period. Access is
allowed before that instant and restricted at or after it with reason
`cancelled`.

## Deterministic test plan

- the default cancellation boundary remains the period end;
- an explicit boundary preserves access before the instant;
- access at the explicit boundary is denied and explains cancellation;
- retroactive or out-of-period boundaries are rejected;
- replay preserves the cancellation boundary.

## Done criteria

The cancellation edge is explicit in the shared simulation graph and remains
observable through the access decision read model.

## Out of scope

Plan changes, grace periods, cancellation reversal, and post-cancellation
renewal.
