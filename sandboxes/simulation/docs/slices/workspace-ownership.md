# Workspace Ownership

## Selection

- Runtime target: the existing private workspace and Recording boundary.
- Architecture: one owner identity; no collaboration or role system.

## Contract

Only the workspace owner may access or record entries. A request identified as a
different user is rejected with `unauthorized_user`, regardless of subscription
state. The rejection does not mutate durable facts.

## Deterministic test plan

- owner can record while entitled;
- another user cannot record;
- unauthorized access emits an explanatory decision;
- unauthorized attempts do not append entries or domain facts.

## Done criteria

Private workspace ownership is explicit in the simulation boundary.

## Out of scope

Invitations, shared workspaces, organization roles, delegation, and impersonation.
