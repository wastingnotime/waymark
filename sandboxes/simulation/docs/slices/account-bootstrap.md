# Account Bootstrap Idempotency

## Selection

- Runtime target: account and private-workspace creation.
- Architecture: one account bootstrap in the shared environment.

## Contract

Repeated account bootstrap does not append duplicate `AccountCreated` or
`WorkspaceCreated` facts. The duplicate request is observable and leaves the
original owner and workspace unchanged.

## Deterministic test plan

- first bootstrap creates one account and workspace;
- duplicate bootstrap produces one informational observation;
- fact counts remain one each;
- replay preserves the single bootstrap.

## Done criteria

The one-user/one-workspace cardinality invariant is enforced at the simulation
boundary.

## Out of scope

Account deletion, account merging, multiple users, invitations, and migration
between workspaces.
