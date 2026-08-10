# Subscription Status Read Model

## Selection

- Runtime target: derived billing status and operator inspection.
- Architecture: projection over subscription, payment, entitlement, and
  cancellation facts.

## Contract

The derived status is one of `none`, `requested`, `active`, `past_due`,
`cancellation_scheduled`, or `expired`. It is calculated at an instant and is
not stored as an independent flag.

## Done criteria

Operator inspection explains both access reason and commercial status.

## Out of scope

Provider-specific statuses, invoices, grace periods, and multi-plan status.
