# Operator Intervention Idempotency

## Selection

- Runtime target: entitlement restoration through the Operations boundary.
- Architecture: one attributed intervention for a suspended entitlement.

## Contract

Repeating the same restore after the entitlement is already restored does not
append another intervention or restoration fact. The duplicate is observable
as an operator notice.

## Done criteria

Operator retries are safe after an uncertain response.

## Out of scope

Approval workflows, role checks, bulk interventions, and support-ticket links.
