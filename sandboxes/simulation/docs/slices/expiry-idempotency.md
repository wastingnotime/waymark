# Expiry Job Idempotency

## Selection

- Runtime target: the period-end access transition.
- Architecture: one expiry transition for each current entitlement interval.

## Contract

Repeated period-end processing does not append another `EntitlementExpired`
fact. The duplicate scheduler attempt is observable and access state remains
restricted.

## Done criteria

Expiry can be safely retried by a scheduler or replayed delivery.

## Out of scope

Grace periods, scheduler ownership, provider settlement, and manual date
overrides.
