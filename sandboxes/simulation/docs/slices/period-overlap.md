# Billing Period Overlap

## Selection

- Runtime target: subscription activation and entitlement periods.
- Architecture: one non-overlapping current entitlement interval.

## Contract

An activation request whose period overlaps the current entitlement is rejected.
Periods must have a positive duration. Renewal after expiry remains the
explicit path to a new period.

## Done criteria

The simulation cannot silently replace an active period with an overlapping
activation.

## Out of scope

Proration, backdated billing, plan changes, and multiple concurrent plans.
