# Subscription Ownership

## Selection

- Runtime target: subscription request and account/payer relationship.
- Architecture: one subscription owned by the first-version user and payer.

## Contract

The subscription request fact identifies its Waymark subscription, user, and
payer. The payer is the same person as the user in the first version, but the
relationship is explicit for billing boundaries and replay.

## Done criteria

Subscription ownership is inspectable from durable facts without provider
identifiers replacing Waymark identities.

## Out of scope

Delegated payers, organization-funded subscriptions, and subscription transfer.
