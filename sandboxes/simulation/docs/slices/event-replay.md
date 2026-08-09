# Event Replay

## Selection

- Runtime target: the shared Waymark simulation environment.
- Architecture: rehydrate projections from ordered `SimFact` history.

## Contract

Given the same append-only facts, replay produces the same access state,
entitlement boundaries, and durable entries as the live simulation. Replay is
read-only and emits no new facts.

## Deterministic test plan

- replay preserves account and workspace identity;
- replay preserves entries and timestamps;
- replay preserves payment failure, expiry, cancellation, and period state;
- replay does not append facts;
- runtime invariant compares replayed and live state.

## Done criteria

The first slice can be inspected and rehydrated from its fact history before
model EGD.

## Out of scope

Cross-version migration, external event-store serialization, snapshots, and
schema compatibility policy.
