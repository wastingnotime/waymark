# Operator Inspection Read Model

## Selection

- Runtime target: the existing Operations observation boundary.
- Architecture: a read-only projection of current subscription and entitlement
  facts.

## Contract

Inspection includes access reason, user/workspace identity, entry count,
entitlement period boundaries, payment-failure state, expiry state,
cancellation boundary, and event count. It does not mutate facts.

## Deterministic test plan

- inspection includes all lifecycle fields;
- payment failure is visible as an access reason and state;
- cancellation boundary is visible after scheduling;
- inspection remains read-only.

## Done criteria

An operator can understand why access is allowed or restricted from one
structured observation.

## Out of scope

Operator dashboards, search, roles, approvals, and support-ticket integration.
