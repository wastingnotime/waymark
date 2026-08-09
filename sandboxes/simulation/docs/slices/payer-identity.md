# Payer Identity

## Selection

- Runtime target: account bootstrap and billing facts.
- Architecture: one payer identity represented separately from the user role,
  with the same underlying person in the first version.

## Contract

Account creation records both user and payer identity. They are equal in the
single-user model, while remaining separate concepts for future billing
boundaries. Replay and operator inspection preserve the relationship.

## Done criteria

Payment and subscription facts can refer to an explicit payer identity without
introducing organization accounts or a second person.

## Out of scope

Delegated payers, organization billing, invoices, tax identities, and transfer.
