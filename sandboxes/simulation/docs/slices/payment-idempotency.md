# Payment Delivery Idempotency

## Selection

- Runtime target: the existing fake payment provider and access environment.
- Architecture: provider correlation at the simulation boundary; no provider
  implementation leaks into domain language.

## Contract

Repeated delivery of the same payment failure correlation ID produces one
`PaymentFailed` fact and one access transition. A duplicate delivery emits an
informational observation and does not mutate entitlement state.

## Deterministic test plan

- first failure suspends access;
- duplicate failure preserves one failure fact;
- duplicate delivery is observable;
- replay preserves processed payment correlations.

## Done criteria

Provider retries cannot duplicate payment-failure facts in the shared
simulation environment.

## Out of scope

Provider webhook signatures, ordering across different payments, refunds,
chargebacks, and provider-specific retry schedules.
