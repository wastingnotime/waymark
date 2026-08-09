# Subscription Request

## Selection

- Runtime target: the commercial flow between account creation and payment.
- Architecture: one current subscription for the one user.

## Contract

The user requests the single subscription before payment activation. Repeating
the request with the same subscription identity is idempotent; requesting a
different current subscription is rejected.

## Deterministic test plan

- account can request one subscription;
- duplicate request produces one fact and one notice;
- subscription identity survives replay;
- activation follows the request in the runtime scenario.

## Done criteria

The first scenario visibly follows account creation → subscription request →
payment success → entitlement grant.

## Out of scope

Multiple plans, trials, upgrades, downgrades, and subscription transfers.
