# Payment Success Idempotency

## Selection

- Runtime target: activation and renewal payment boundaries.
- Architecture: payment correlation IDs on the shared fact history.

## Contract

Repeated delivery of the same successful payment ID does not append a second
`PaymentSucceeded` or entitlement fact. The duplicate is observable and leaves
the current period unchanged.

## Done criteria

Activation and renewal success notifications are idempotent for a fixed payment
correlation ID and replay preserves those IDs.

## Out of scope

Refunds, chargebacks, provider ordering, and payment reconciliation.
